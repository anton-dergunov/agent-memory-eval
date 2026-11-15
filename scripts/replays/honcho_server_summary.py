"""Summarise the real-server runs of the example (honcho_server_runs/run*.json).

For each run: every model call by step (tool rounds of the dream agents included), every stored
conclusion with its level, premises and whether a dream deleted it, the peer card, and both read
paths. `--brief` prints only the comparison across runs.

    python3 honcho_server_summary.py [--brief] [run1.json ...]
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def calls_by_step(run: dict) -> list[dict]:
    """One row per model call, in order: step, which prompt, the tool calls or the reply."""
    rows = []
    for call in run["calls"]:
        messages = call["request"].get("messages", [])
        system = messages[0]["content"] if messages else ""
        kind = ("deriver" if system.startswith("Analyze messages") else
                "deduction" if "deductive reasoning agent" in system[:80] else
                "induction" if "inductive reasoning agent" in system[:80] else
                "dialectic" if "Honcho's dialectic" in system[:80] else "other")
        choice = (call["reply"].get("choices") or [{}])[0]
        message = choice.get("message") or {}
        tools = [(t["function"]["name"], t["function"]["arguments"])
                 for t in message.get("tool_calls") or []]
        usage = call["reply"].get("usage") or {}
        rows.append({"step": call.get("phase"), "kind": kind, "messages": len(messages),
                     "tools": tools, "content": message.get("content") or "",
                     "in": usage.get("prompt_tokens", 0), "out": usage.get("completion_tokens", 0)})
    return rows


def documents(run: dict) -> list[dict]:
    premises: dict[str, list[str]] = {}
    for link in run["links"]:
        premises.setdefault(link["derived_id"], []).append(link["source_id"])
    out = []
    for doc in run["documents"]:
        meta = doc.get("internal_metadata") or {}
        out.append({**doc, "premises": premises.get(doc["id"], []),
                    "said_at": meta.get("message_created_at"),
                    "confidence": meta.get("confidence"), "pattern_type": meta.get("pattern_type")})
    return out


def full(run: dict) -> None:
    print(f"\n######## run {run['run']}  ({run['workspace']})")
    for row in calls_by_step(run):
        what = "; ".join(f"{name}({args[:160]})" for name, args in row["tools"]) or row["content"][:300]
        print(f"[{row['step']:6} {row['kind']:9} {row['in']:>6}/{row['out']:<5}] {what}")
    docs = documents(run)
    short = {d["id"]: f"{d['level'][0].upper()}{i}" for i, d in enumerate(docs, 1)}
    print("\nconclusions (id: level, session, said at, premises, deleted):")
    for d in docs:
        flag = "  DELETED" if d["deleted_at"] else ""
        extra = f" [{d['confidence']}/{d['pattern_type']}]" if d["level"] == "inductive" else ""
        print(f"  {short[d['id']]:4} {d['level']:9} {d['session_name']}  {d['said_at']}  "
              f"<- {[short.get(p, p) for p in d['premises']]}{extra}{flag}\n        {d['content']}")
    for peer in run["peers"]:
        card = {k: v for k, v in (peer["internal_metadata"] or {}).items() if "card" in k}
        if card:
            print(f"\npeer card ({peer['name']}): {json.dumps(card, ensure_ascii=False, indent=1)}")
    print(f"\nCHAT:\n{run['chat']}\n\nREPRESENTATION:\n{run['representation']}")


def brief(runs: list[dict]) -> None:
    print("run | calls by kind | tokens in/out | conclusions by level | deleted")
    for run in runs:
        rows = calls_by_step(run)
        kinds = Counter(r["kind"] for r in rows)
        docs = documents(run)
        levels = Counter(d["level"] for d in docs if not d["deleted_at"])
        deleted = [d["content"] for d in docs if d["deleted_at"]]
        print(f"{run['run']} | {dict(kinds)} | {sum(r['in'] for r in rows)}/{sum(r['out'] for r in rows)}"
              f" | {dict(levels)} | {deleted}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    paths = [Path(a) for a in args] or sorted((HERE / "honcho_server_runs").glob("run*.json"))
    runs = [json.loads(p.read_text()) for p in paths]
    if "--brief" in sys.argv:
        brief(runs)
    else:
        for run in runs:
            full(run)
