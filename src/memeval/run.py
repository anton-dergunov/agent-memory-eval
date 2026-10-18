"""Run arms over a split, then score them.

    python -m memeval.run build --split pilot --arms full-context retrieval
    python -m memeval.run score --split pilot
    python -m memeval.run report --split pilot

`build` writes one file per question and arm under `results/<split>/<arm>/`,
holding what the system returned, its answer and its store. It skips files
that already exist, so an interrupted run continues where it stopped, and the
model-call cache makes a repeated call free. `score` adds the judge's verdict
and the probes to those files. Arms run in separate processes, one per arm,
so their costs can be told apart and a slow arm does not hold up the others.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

from . import config, data, llm


def result_path(split: str, arm: str, qid: str) -> Path:
    return config.RESULTS_DIR / split / arm / f"{qid}.json"


def build(split: str, arm_name: str, limit: int | None = None, reverse: bool = False,
          shard: str | None = None) -> None:
    from .arms import build as build_arm

    ids = data.split(split)[:limit]
    if shard:
        # "i/n": every n-th question from the i-th, so n processes split the work.
        i, n = (int(x) for x in shard.split("/"))
        ids = ids[i - 1::n]
    if reverse:
        # A second process for a slow arm works from the other end of the list.
        ids = ids[::-1]
    full = split == "full"
    arm = build_arm(arm_name)
    try:
        for n, qid in enumerate(ids, 1):
            names = getattr(arm, "variants", [arm.name])
            if all(result_path(split, name, qid).exists() for name in names):
                continue
            q = data.question(qid, full_history=full)
            started = time.time()
            print(f"[{arm_name}] {n}/{len(ids)} {qid}: {len(q.sessions)} sessions", flush=True)
            try:
                _build_one(split, arm, arm_name, q, started)
            except llm.BudgetExceeded:
                raise
            except Exception:  # noqa: BLE001 - retried on the next run
                traceback.print_exc()
                print(f"[{arm_name}] {qid} FAILED; it will be retried on the next run", flush=True)
    finally:
        arm.close()


def _build_one(split: str, arm, arm_name: str, q, started: float) -> None:
    qid = q.qid
    with llm.tagged(split=split, arm=arm_name, qid=qid):
        with llm.tagged(phase="write"):
            arm.reset(q)
            for session in q.sessions:
                arm.ingest(session)
            arm.finish()
        written = time.time()
        with llm.tagged(phase="read"):
            reads = arm.reads(q)
        dump = arm.dump()
        for name, read in reads.items():
            with llm.tagged(arm=name, phase="answer"):
                answer = read.answer if read.answer is not None else arm.answer(q, read.context)
            out = {"qid": qid, "arm": name, "split": split, "question": q.question,
                   "reference": q.answer, "question_date": f"{q.date:%Y-%m-%d %H:%M}",
                   "sessions": [{"id": s.id, "date": f"{s.date:%Y-%m-%d %H:%M}",
                                 "evidence": s.evidence} for s in q.sessions],
                   "context": read.context, "answer": answer, "dump": dump,
                   "extra": read.extra, "settings": arm.settings(),
                   "seconds": {"write": round(written - started, 1),
                               "total": round(time.time() - started, 1)}}
            path = result_path(split, name, qid)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"[{arm_name}] {qid} done in {time.time() - started:.0f}s; "
          f"spent so far ${llm.spent():.2f}", flush=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="memeval.run")
    ap.add_argument("command", choices=["build", "score", "report"])
    ap.add_argument("--split", required=True, choices=["pilot", "main", "full"])
    ap.add_argument("--arms", nargs="*", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--reverse", action="store_true",
                    help="work through the questions from the last one backwards")
    ap.add_argument("--shard", default=None,
                    help="i/n: build only every n-th question starting at the i-th (1-based)")
    args = ap.parse_args(argv)
    config.ensure_credentials()

    if args.command == "build":
        failed = []
        for arm in args.arms or []:
            try:
                build(args.split, arm, args.limit, args.reverse, args.shard)
            except llm.BudgetExceeded as exc:
                print(f"STOPPED: {exc}")
                return 2
            except Exception:  # noqa: BLE001 - one arm failing should not hide the others
                traceback.print_exc()
                failed.append(arm)
        return 1 if failed else 0
    if args.command == "score":
        from .score import score_split
        score_split(args.split, args.arms)
        return 0
    from .report import report
    print(report(args.split))
    return 0


if __name__ == "__main__":
    sys.exit(main())
