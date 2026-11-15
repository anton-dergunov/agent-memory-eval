"""R3b: what searching at answer time cost in the experiment's Letta runs, from the ledger alone.

Run from agent-memory-eval:  python3 <this file>

Every model call of the experiment is in results/main/ledger.jsonl with its input tokens, arm,
question and phase. In Letta's answer turn ("read" phase) the first call reads the system prompt
(instructions and memory blocks) and the question; each later call follows a tool call and reads
the same prompt again, plus the tool calls and results so far. So:

- calls per answer      = 1 + the number of tool steps before the reply;
- extra results tokens  = sum(input) - n_calls * first_call_input   (what the results themselves add);
- total / first         = how many first-call prompts the whole answer turn read.
"""
import json
import statistics as st
from collections import defaultdict

rows = [json.loads(line) for line in open("results/main/ledger.jsonl")]
for arm in ("letta", "letta-persona"):
    turns = defaultdict(list)
    for r in rows:
        if r.get("arm") == arm and r["kind"] == "chat" and r["phase"] == "read":
            turns[r["qid"]].append(r)
    calls, first, total, results = [], [], [], []
    for rs in turns.values():
        tokens = [r["input_tokens"] for r in sorted(rs, key=lambda r: r["at"])]
        calls.append(len(tokens))
        first.append(tokens[0])
        total.append(sum(tokens))
        results.append(sum(tokens) - len(tokens) * tokens[0])
    print(f"{arm}: {len(turns)} answers; calls per answer: median {st.median(calls)}, mean {st.mean(calls):.2f}, "
          f"one call only in {sum(c == 1 for c in calls)}")
    print(f"   first call: median {st.median(first):,.0f} tokens; whole answer turn: median {st.median(total):,.0f}")
    print(f"   whole turn / first call: median {st.median(t / f for t, f in zip(total, first)):.1f}, "
          f"pooled {sum(total) / sum(first):.1f}")
    print(f"   tokens of tool calls and results: median {st.median(results):,.0f} per answer, "
          f"{sum(results) / sum(total):.0%} of all tokens read while answering")
