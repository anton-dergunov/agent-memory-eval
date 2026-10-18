"""Tables from scored results: accuracy, where answers were lost, and cost.

Baselines come first in every table. Intervals are 95% Wilson intervals; with
a few dozen yes/no questions only large gaps mean anything.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict

from . import config

ORDER = ["full-context", "retrieval", "textual", "mem0", "honcho-chat", "honcho-repr",
         "graphiti", "graphiti-chunk", "letta", "letta-batch", "letta-persona"]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (centre - half, centre + half)


def load(split: str) -> dict[str, list[dict]]:
    root = config.RESULTS_DIR / split
    out = {}
    for arm_dir in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("_")):
        rows = [json.loads(p.read_text()) for p in sorted(arm_dir.glob("*.json"))]
        out[arm_dir.name] = [r for r in rows if "judge" in r]
    return dict(sorted(out.items(), key=lambda kv: ORDER.index(kv[0]) if kv[0] in ORDER else 99))


def ledger(split: str) -> list[dict]:
    """This split's model calls. Read from the live ledger and saved next to
    the results, so the cost tables can be rebuilt from the committed files."""
    saved = config.RESULTS_DIR / split / "ledger.jsonl"
    rows = []
    for path in sorted(config.LEDGER_DIR.glob("calls-*.jsonl")):
        for raw in path.read_text().splitlines():
            row = json.loads(raw)
            if row.get("split") == split:
                rows.append(row)
    if rows:
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_text("".join(json.dumps(r) + "\n" for r in sorted(rows, key=lambda r: r["at"])))
    elif saved.exists():
        rows = [json.loads(raw) for raw in saved.read_text().splitlines()]
    return rows


def outcome(r: dict) -> str:
    """Where a wrong answer was lost, from the probes."""
    if r["judge"]["correct"]:
        return "correct"
    p = r.get("probe", {})
    if "skipped" in p or not p:
        return "wrong, unclassified"
    if "stored" in p and not p["stored"].get("new_present"):
        return "update never stored"
    if not p["delivered"].get("new_present"):
        return "stored, not delivered"
    if p["stale"].get("gave_old"):
        return "delivered, answered old value"
    return "delivered, other error"


def system_stats(arm: str, rows: list[dict]) -> dict:
    """A few numbers that say what the system did, from each result's `extra`
    and `dump`."""
    n = max(1, len(rows))
    mean = lambda key: sum((r.get("extra") or {}).get(key, 0) for r in rows) / n  # noqa: E731
    out = {}
    if arm == "mem0":
        out = {"facts stored": f"{mean('stored'):.0f}", "facts returned": f"{mean('retrieved'):.0f}",
               "unparsed extraction replies": f"{mean('parse_failures'):.2f}"}
    elif arm.startswith("graphiti"):
        out = {"edges": f"{mean('edges'):.0f}", "edges closed (superseded)": f"{mean('invalidated'):.1f}",
               "episodes": f"{mean('episodes'):.0f}", "failed episodes": f"{mean('episode_failures'):.2f}",
               "facts returned": f"{mean('retrieved'):.0f}"}
    elif arm.startswith("honcho"):
        levels = defaultdict(int)
        for r in rows:
            for line in (r.get("dump") or "").splitlines():
                if line.startswith("- ["):
                    levels[line[3:line.index("]")]] += 1
        out = {f"{level} conclusions": f"{count / n:.0f}" for level, count in sorted(levels.items())}
        out["context tokens"] = f"{sum(len(r['context']) for r in rows) / n / 4:.0f}"
    elif arm.startswith("letta"):
        empty = sum(1 for r in rows if "<human>\n\n</human>" in (r.get("dump") or "")
                    or "<human>\n</human>" in (r.get("dump") or ""))
        out = {"human block chars": f"{sum(_human_chars(r.get('dump') or '') for r in rows) / n:.0f}",
               "questions with an empty human block": f"{empty}/{len(rows)}",
               "tool calls while answering": f"{sum(len((r.get('extra') or {}).get('tool_calls', [])) for r in rows) / n:.1f}",
               "no reply": f"{sum(1 for r in rows if r['answer'] == '(no reply)')}/{len(rows)}"}
    elif arm == "textual":
        out = {"profile tokens": f"{sum(len(r['context']) for r in rows) / n / 4:.0f}"}
    elif arm in ("retrieval", "full-context"):
        out = {"context tokens": f"{sum(len(r['context']) for r in rows) / n / 4:,.0f}"}
    return out


def _human_chars(dump: str) -> int:
    start, end = dump.find("<human>"), dump.find("</human>")
    return max(0, end - start - len("<human>") - 2) if start >= 0 and end > start else 0


def report(split: str) -> str:
    results = load(split)
    calls = ledger(split)
    lines = [f"## Results: {split}", ""]

    lines += ["| Arm | n | Accuracy | 95% interval |", "|---|--:|--:|---|"]
    for arm, rows in results.items():
        k = sum(r["judge"]["correct"] for r in rows)
        lo, hi = wilson(k, len(rows))
        lines.append(f"| {arm} | {len(rows)} | {k / max(1, len(rows)):.0%} | {lo:.0%}–{hi:.0%} |")

    kinds = ["correct", "update never stored", "stored, not delivered",
             "delivered, answered old value", "delivered, other error", "wrong, unclassified"]
    lines += ["", "### Where answers were lost", "",
              "| Arm | " + " | ".join(kinds) + " | old value stored as current | old value delivered |",
              "|---|" + "--:|" * (len(kinds) + 2)]
    for arm, rows in results.items():
        counts = defaultdict(int)
        for r in rows:
            counts[outcome(r)] += 1
        probed = [r.get("probe", {}) for r in rows]
        old_current = sum(1 for p in probed if p.get("stored", {}).get("old_as_current"))
        old_delivered = sum(1 for p in probed if p.get("delivered", {}).get("old_present"))
        stored_col = str(old_current) if any("stored" in p for p in probed) else "n/a"
        lines.append(f"| {arm} | " + " | ".join(str(counts[k]) for k in kinds)
                     + f" | {stored_col} | {old_delivered} |")

    lines += ["", "### Cost per question (USD, mean)", "",
              "| Arm | write | read | answer | total system | model calls (write) | input tokens (write) |",
              "|---|--:|--:|--:|--:|--:|--:|"]
    for arm, rows in results.items():
        n = max(1, len(rows))
        source = arm.split("-")[0] if arm.startswith("honcho") else arm
        by_phase = defaultdict(float)
        write_calls = write_tokens = 0
        for c in calls:
            if c.get("arm") not in (arm, source) or c.get("phase") in ("judge", "probe"):
                continue
            # Honcho's two reads share one write; charge the write to both.
            if c.get("arm") == source and source != arm and c.get("phase") != "write":
                continue
            by_phase[c["phase"]] += c["usd"]
            if c["phase"] == "write" and c["kind"] == "chat":
                write_calls += 1
                write_tokens += c["input_tokens"]
        total = by_phase["write"] + by_phase["read"] + by_phase["answer"]
        lines.append(f"| {arm} | {by_phase['write'] / n:.4f} | {by_phase['read'] / n:.4f} | "
                     f"{by_phase['answer'] / n:.4f} | {total / n:.4f} | {write_calls / n:.1f} | "
                     f"{write_tokens / n:,.0f} |")

    lines += ["", "### What each system stored and returned (mean per question)", ""]
    for arm, rows in results.items():
        stats = system_stats(arm, rows)
        if stats:
            lines.append(f"- **{arm}**: " + "; ".join(f"{k} {v}" for k, v in stats.items()))

    pairs = [(r["judge"]["correct"], r["judge_check"]["correct"])
             for rows in results.values() for r in rows if "judge_check" in r]
    if pairs:
        agree = sum(a == b for a, b in pairs)
        lines += ["", f"Judge agreement ({config.JUDGE_MODEL} vs {config.PROBE_MODEL}): "
                      f"{agree}/{len(pairs)} ({agree / len(pairs):.0%})."]
    spend = sum(c["usd"] for c in calls)
    scoring = sum(c["usd"] for c in calls if c.get("phase") in ("judge", "probe"))
    lines += ["", f"Spent on this split: ${spend:.2f} (of which judging and probes ${scoring:.2f})."]
    return "\n".join(lines)
