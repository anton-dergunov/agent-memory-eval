"""Where the old and new values sat in each benchmark store, against what a dream agent saw.

For each of the 67 questions of the experiment's Honcho arm: the explicit conclusions in the
order they were stored (the store dump is sorted by creation time; the dream's own rows come
last and are left out), and the newest 20, which is what `get_recent_observations` returned with
the limit the dream agents mostly used. The old and new values come from results/main/_facts; a
value is located by case-insensitive substring match on its text (word boundaries for numbers),
so a question counts only when the match is found.

    python3 honcho_dream_window.py
"""
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WINDOW = 20


def find(rows, value):
    value = value.strip().lower()
    pattern = re.compile(rf"(?<![\d.]){re.escape(value)}(?![\d.])" if re.fullmatch(r"[\d.,:$%]+", value)
                         else re.escape(value))
    return [i for i, row in enumerate(rows) if pattern.search(row.lower())]


found = both_in = old_in = new_in = neither_in = 0
positions = []
for path in sorted((REPO / "results/main/honcho-repr").glob("*.json")):
    run = json.loads(path.read_text())
    facts = json.loads((REPO / "results/main/_facts" / path.name).read_text())
    rows = [r for r in run["dump"].splitlines() if r.startswith("- [explicit]")]
    if not facts.get("old_value") or not facts.get("new_value"):
        continue
    old, new = find(rows, facts["old_value"]), find(rows, facts["new_value"])
    if not old or not new:
        continue
    found += 1
    n = len(rows)
    old_rank, new_rank = n - max(old), n - max(new)       # 1 = the newest row
    positions.append((run["qid"], n, old_rank, new_rank))
    o, w = old_rank <= WINDOW, new_rank <= WINDOW
    both_in += o and w
    old_in += o
    new_in += w
    neither_in += not o and not w

print(f"questions with both values located: {found} of 67")
print(f"newest {WINDOW} explicit rows contained: both values {both_in}, the old value {old_in}, "
      f"the new value {new_in}, neither {neither_in}")
print("median store size:", sorted(p[1] for p in positions)[len(positions) // 2])
for qid, n, o, w in positions[:10]:
    print(f"  {qid}: {n} rows; old value {o}th from the newest, new value {w}th")
