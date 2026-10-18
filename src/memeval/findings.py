"""The tables behind the write-up, rebuilt from the committed result files.

    python -m memeval.findings            # writes docs/findings/*.md

Every number in docs/experiment-results.md comes from one of these tables, and
every table is computed from `results/<split>/<arm>/<qid>.json` and the saved
call ledgers (`results/<split>/ledger.jsonl`), so the write-up can be checked
and re-cut without re-running anything.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from . import config
from .report import ORDER, ledger, outcome, wilson

OUT = config.REPO / "docs" / "findings"

# Which value each question asks for, labelled by hand from the question text.
# The probes take the reference answer as "the new value", so for the
# questions that ask for an earlier value their "update stored" columns mean
# "the value asked for was stored".
PREVIOUS = {"07741c44", "0ddfec37", "10e09553", "50635ada", "89941a94", "9bbe84a2",
            "dfde3500", "e66b632c"}
BOTH = {"031748ae", "c4ea545c", "f685340e"}

MEMORY_ARMS = {"textual", "mem0", "honcho-chat", "honcho-repr", "graphiti", "graphiti-chunk",
               "letta", "letta-batch", "letta-persona"}
SERVERS = {"full-context": "none", "retrieval": "none", "textual": "none",
           "mem0": "none (local Qdrant files)", "honcho-chat": "Honcho API + deriver, Postgres, Redis",
           "honcho-repr": "Honcho API + deriver, Postgres, Redis", "graphiti": "Neo4j",
           "graphiti-chunk": "Neo4j", "letta": "Letta server, Postgres", "letta-batch": "Letta server, Postgres",
           "letta-persona": "Letta server, Postgres"}
# Variants of an arm, each kept as its own row but left out of the cross-arm
# count of who missed which question.
VARIANTS = ("graphiti-chunk", "letta-batch", "letta-persona")


def load(split: str) -> dict[str, dict[str, dict]]:
    root = config.RESULTS_DIR / split
    out = {}
    for d in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("_")):
        rows = {p.stem: json.loads(p.read_text()) for p in sorted(d.glob("*.json"))}
        out[d.name] = {q: r for q, r in rows.items() if "judge" in r}
    return dict(sorted(out.items(), key=lambda kv: ORDER.index(kv[0]) if kv[0] in ORDER else 99))


def costs(split: str) -> dict[str, dict[str, dict]]:
    """Per arm and question: system USD (write + read + answer), and model calls
    and input tokens at write. Judging and probes are left out."""
    per = defaultdict(lambda: defaultdict(lambda: {"usd": 0.0, "calls": 0, "tokens": 0}))
    for c in ledger(split):
        arm, phase = c.get("arm"), c.get("phase")
        if not arm or phase not in ("write", "read", "answer"):
            continue
        targets = [arm]
        if arm == "honcho":  # one store, two read paths: charge the write to both
            targets = ["honcho-chat", "honcho-repr"] if phase == "write" else []
        for t in targets:
            q = per[t][c.get("qid")]
            q["usd"] += c["usd"]
            if phase == "write" and c["kind"] == "chat":
                q["calls"] += 1
                q["tokens"] += c["input_tokens"]
    return per


def per_q(cost, arm: str, qids, key: str = "usd") -> float:
    """Mean of one cost figure over the given questions."""
    by_q = cost.get(arm) or {}
    return _mean(by_q[q][key] if q in by_q else 0 for q in qids)


def _pct(k: int, n: int) -> str:
    return f"{k / n:.0%}" if n else "–"


def _mean(xs) -> float:
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def overview(split: str, res, cost) -> list[str]:
    lines = [f"## Accuracy, cost and time ({split})", "",
             "| Arm | n | Accuracy | 95% interval | USD per question (system) | model calls to write | "
             "seconds to write | servers needed |",
             "|---|--:|--:|---|--:|--:|--:|---|"]
    for arm, rows in res.items():
        n = len(rows)
        k = sum(r["judge"]["correct"] for r in rows.values())
        lo, hi = wilson(k, n)
        usd, calls = per_q(cost, arm, rows), per_q(cost, arm, rows, "calls")
        secs = _mean((r.get("seconds") or {}).get("write", 0) for r in rows.values())
        lines.append(f"| {arm} | {n} | {_pct(k, n)} | {lo:.0%}–{hi:.0%} | {usd:.4f} | "
                     f"{calls:.0f} | {secs:.0f} | {SERVERS.get(arm, '')} |")
    return lines + [""]


def connecting(res, cost) -> list[str]:
    """Point 1: the same system, fed two ways."""
    lines = ["## 1. How a system is fed decides whether it remembers", "",
             "| Arm | how it was fed | accuracy | update never stored | model calls to write | "
             "input tokens to write | USD per question | what the store holds |",
             "|---|---|--:|--:|--:|--:|--:|---|"]
    fed = {"graphiti-chunk": "sessions cut into episodes of up to 8,000 characters",
           "graphiti": "one episode per message (Graphiti's own examples)",
           "letta-batch": "each session in one request, ending on an assistant message",
           "letta": "one agent step per user message",
           "letta-persona": "one agent step per user message; persona asks it to keep facts current"}
    for arm in ("graphiti-chunk", "graphiti", "letta-batch", "letta", "letta-persona"):
        rows = res.get(arm)
        if not rows:
            continue
        n = len(rows)
        k = sum(r["judge"]["correct"] for r in rows.values())
        lost = sum(outcome(r) == "update never stored" for r in rows.values())
        usd = per_q(cost, arm, rows)
        if arm.startswith("graphiti"):
            e = lambda key: _mean((r.get("extra") or {}).get(key, 0) for r in rows.values())  # noqa: E731
            holds = (f"{e('episodes'):.0f} episodes, {e('edges'):.0f} edges, "
                     f"{e('invalidated'):.1f} closed as superseded")
        else:
            empty = sum("<human>\n\n</human>" in (r.get("dump") or "") or "<human>\n</human>" in (r.get("dump") or "")
                        for r in rows.values())
            edits = _mean(sum(1 for t in (r.get("extra") or {}).get("write_tool_calls", [])
                              if t.startswith(("memory_", "core_memory"))) for r in rows.values())
            holds = f"human block empty in {empty}/{n}" + (f"; {edits:.1f} memory edits while reading the history"
                                                           if arm != "letta-batch" else "")
        lines.append(f"| {arm} | {fed[arm]} | {_pct(k, n)} | {lost} | {per_q(cost, arm, rows, 'calls'):.0f} | "
                     f"{per_q(cost, arm, rows, 'tokens'):,.0f} | {usd:.3f} | {holds} |")
    return lines + [""]


def after_update(res) -> list[str]:
    """Point 2: the state of memory once the update has been read."""
    lines = ["## 2. What memory looks like after an update", "",
             "Share of questions. *Stored* columns read the whole memory; *delivered* columns read what the "
             "answering model was given. Questions that ask for an earlier value count the asked value as "
             "\"new\" (see point 3).", "",
             "| Arm | new value stored | old value still stored | old value still presented as current | "
             "new value delivered | old value delivered | both delivered | correct when both delivered | "
             "context given to the answer (tokens) |",
             "|---|--:|--:|--:|--:|--:|--:|--:|--:|"]
    for arm, rows in res.items():
        n = len(rows)
        p = [r.get("probe") or {} for r in rows.values()]
        st = [x.get("stored") or {} for x in p]
        de = [x.get("delivered") or {} for x in p]
        both = [r for r, d in zip(rows.values(), de) if d.get("new_present") and d.get("old_present")]
        stored_cols = (" | ".join(_pct(sum(bool(s.get(k)) for s in st), n)
                                  for k in ("new_present", "old_present", "old_as_current"))
                       if arm in MEMORY_ARMS else "n/a | n/a | n/a")
        ctx = _mean(len(r["context"]) for r in rows.values()) / 4
        lines.append(f"| {arm} | {stored_cols} | {_pct(sum(bool(d.get('new_present')) for d in de), n)} | "
                     f"{_pct(sum(bool(d.get('old_present')) for d in de), n)} | {len(both)} | "
                     f"{sum(r['judge']['correct'] for r in both)}/{len(both)} | {ctx:,.0f} |")
    return lines + [""]


def by_intent(res) -> list[str]:
    """Point 3: questions about the current value against questions about an earlier one."""
    lines = ["## 3. Asking for the current value or an earlier one", "",
             f"Hand-labelled from the question text: {len(PREVIOUS)} questions ask for an earlier value "
             f"({', '.join(sorted(PREVIOUS))}), {len(BOTH)} ask for both ({', '.join(sorted(BOTH))}), the rest "
             "for the current value.", "",
             "| Arm | current value | earlier value | both |", "|---|--:|--:|--:|"]
    for arm, rows in res.items():
        cells = []
        for group in ("current", "previous", "both"):
            sel = [r for q, r in rows.items()
                   if (q in PREVIOUS if group == "previous" else q in BOTH if group == "both"
                       else q not in PREVIOUS and q not in BOTH)]
            cells.append(f"{sum(r['judge']['correct'] for r in sel)}/{len(sel)}")
        lines.append(f"| {arm} | " + " | ".join(cells) + " |")
    return lines + [""]


def failures(res, facts_dir: Path) -> list[str]:
    """Point 4: every wrong answer, grouped by how many arms missed the question."""
    arms = [a for a in res if a not in VARIANTS]
    qids = sorted({q for a in arms for q in res[a]})
    wrong = {q: [a for a in arms if q in res[a] and not res[a][q]["judge"]["correct"]] for q in qids}
    lines = ["## 4. Every wrong answer", "",
             f"Arms counted: {', '.join(arms)}. A question most arms miss points at the question or its answer "
             "key as much as at the systems; a question one arm misses points at that arm.", "",
             "| Question | reference | old value (probe) | arms wrong |", "|---|---|---|---|"]
    for q in sorted(qids, key=lambda q: -len(wrong[q])):
        if not wrong[q]:
            continue
        any_row = next(res[a][q] for a in arms if q in res[a])
        fp = facts_dir / f"{q}.json"
        old = json.loads(fp.read_text()).get("old_value") if fp.exists() else None
        lines.append(f"| `{q}` {any_row['question']} | {str(any_row['reference'])[:80]} | {old} | "
                     f"{len(wrong[q])}: {', '.join(wrong[q])} |")
    lines += ["", "### The wrong answers, by arm", ""]
    for a in arms:
        bad = [r for r in res[a].values() if not r["judge"]["correct"]]
        lines += [f"#### {a} ({len(bad)} wrong)", ""]
        for r in bad:
            tail = " ".join(r["answer"].split())[-300:]
            lines.append(f"- `{r['qid']}` *{r['question']}* Reference: {str(r['reference'])[:100]}. "
                         f"Lost: {outcome(r)}. Shared with {len(wrong[r['qid']]) - 1} other arm(s). "
                         f"Answer ends: \"…{tail}\"")
        lines.append("")
    return lines


def history_length(main, full, cost_main, cost_full) -> list[str]:
    """What trimming hid: the same questions with 10 sessions and with all of them."""
    lines = ["## Full history against the trimmed history (same questions)", "",
             "| Arm | n | accuracy, 10 sessions | accuracy, full history | context tokens, 10 | "
             "context tokens, full | USD per question, 10 | USD per question, full |",
             "|---|--:|--:|--:|--:|--:|--:|--:|"]
    for arm, frows in full.items():
        mrows = {q: r for q, r in main.get(arm, {}).items() if q in frows}
        n = len(frows)
        if not n:
            continue
        def usd(cost, rows):
            return per_q(cost, arm, rows)
        lines.append(f"| {arm} | {n} | {_pct(sum(r['judge']['correct'] for r in mrows.values()), len(mrows))} | "
                     f"{_pct(sum(r['judge']['correct'] for r in frows.values()), n)} | "
                     f"{_mean(len(r['context']) for r in mrows.values()) / 4:,.0f} | "
                     f"{_mean(len(r['context']) for r in frows.values()) / 4:,.0f} | "
                     f"{usd(cost_main, mrows):.4f} | {usd(cost_full, frows):.4f} |")
    return lines + [""]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    res, cost = load("main"), costs("main")
    head = ["<!-- Generated by `python -m memeval.findings` from results/; do not edit by hand. -->", ""]
    tables = head + ["# Findings: the tables", "",
                     "Main run: 67 knowledge-update questions, 10 sessions each. Generated from the result "
                     "files; the interpretation is in [../experiment-results.md](../experiment-results.md).", ""]
    tables += overview("main", res, cost) + connecting(res, cost) + after_update(res) + by_intent(res)
    full_dir = config.RESULTS_DIR / "full"
    if full_dir.exists():
        full, cost_full = load("full"), costs("full")
        tables += overview("full", full, cost_full) + history_length(res, full, cost, cost_full)
    (OUT / "tables.md").write_text("\n".join(tables))
    (OUT / "failures.md").write_text("\n".join(head + ["# Findings: every wrong answer", ""]
                                               + failures(res, config.RESULTS_DIR / "main" / "_facts")))
    print(f"wrote {OUT / 'tables.md'} and {OUT / 'failures.md'}")


if __name__ == "__main__":
    main()
