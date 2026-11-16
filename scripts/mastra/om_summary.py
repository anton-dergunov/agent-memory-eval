"""Print what part 9 of the blog series quotes from the Observational Memory runs.

No model calls: it reads runs/<name>/calls.jsonl and result.json, written by om_run.ts.

    python3 scripts/mastra/om_summary.py > scripts/mastra/om_summary_output.txt
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).parent
RUNS = [
    ("2026-11-16-6a1eabeb", "question asked with the newest sessions still unobserved (the default flow)"),
    ("2026-11-16-6a1eabeb-observed-tail", "the unobserved tail observed before the question"),
]
VALUES = ("27:12", "25:50")


def tokens(usage, side):
    v = usage.get(f"{side}Tokens")
    return v["total"] if isinstance(v, dict) else v


def main():
    for name, label in RUNS:
        run = HERE / "runs" / name
        calls = [json.loads(l) for l in (run / "calls.jsonl").open()]
        result = json.loads((run / "result.json").read_text())
        print(f"=== {name}: {label}")
        print(f"question: {result['question']}  (asked {result['question_date']})")
        print(f"expected: {result['expected']}")
        print(f"answer:   {result['answer'].strip()}")
        print(f"model: {result['model']}; packages: {result['packages']}")
        print(f"sessions fed: {len(result['sessions'])}; turns: {sum(s['turns'] for s in result['sessions'])}")
        print()

        print("calls:")
        by_phase = {}
        for c in calls:
            phase = c["phase"].split(":")[0]
            agent = "Observer" if c["prompt"][0]["text"].startswith("You are the memory consciousness of an AI assistant. Your observations") else (
                "Reflector" if "observation reflector" in c["prompt"][0]["text"] else "answering agent")
            text = " ".join(m["text"] for m in c["prompt"])
            dates = re.findall(r"([A-Z][a-z]{2} \d{1,2} 2023):", text)
            span = f"{dates[0]} to {dates[-1]}" if dates else ""
            seen = [v for v in VALUES if v in text]
            wrote = [v for v in VALUES if v in c["reply"]]
            tin, tout = tokens(c["usage"], "input"), tokens(c["usage"], "output")
            by_phase.setdefault(agent, [0, 0, 0])
            by_phase[agent][0] += 1
            by_phase[agent][1] += tin
            by_phase[agent][2] += tout
            print(f"  {c['index']:2} {agent:15} {c['phase']:28} in {tin:6} out {tout:5}  {span:24} saw {seen} wrote {wrote}")
        print("totals by agent (calls, tokens in, tokens out):")
        for agent, (n, tin, tout) in by_phase.items():
            print(f"  {agent:15} {n:2} {tin:7} {tout:6}")
        print()

        for when in ("afterAnswer", "afterReflect"):
            snap = result.get(when)
            if not snap:
                continue
            rec = snap["record"]
            print(f"{when}: log {rec['observationTokenCount']} tokens, {len(rec['activeObservations'])} characters, "
                  f"generation {rec['generationCount']}, unobserved {snap['status']['pendingTokens']} tokens")
            for line in rec["activeObservations"].splitlines():
                if any(v in line for v in VALUES) or "5K" in line:
                    print(f"  {line.strip()}")
        print()

        answer = next(c for c in calls if c["phase"] == "answer" and c["kind"] == "generate")
        system = [m for m in answer["prompt"] if m["role"] == "system"]
        rest = [m for m in answer["prompt"] if m["role"] != "system"]
        print(f"answer prompt: {len(system)} system messages ({sum(len(m['text']) for m in system)} chars), "
              f"{len(rest)} raw messages ({sum(len(m['text']) for m in rest)} chars), "
              f"{tokens(answer['usage'], 'input')} tokens in")
        for m in rest:
            if "25:50" in m["text"]:
                print(f"  raw message with the new value ({m['role']}): {m['text'][:200]}")
                break
        print()


if __name__ == "__main__":
    main()
