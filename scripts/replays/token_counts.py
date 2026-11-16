"""Token counts of the texts the experiment reports, with the answering model's own tokenizer.

    uv run --isolated --no-project --python 3.12 \
        --with 'google-genai[local-tokenizer-transformers]' --with sentencepiece --with 'protobuf>=7' \
        python scripts/replays/token_counts.py > scripts/replays/token_counts_output.txt

The repository's tables used to estimate a text's tokens as characters / 4. This counts them
with google-genai's local tokenizer for gemini-3.1-flash-lite: no model call, nothing sent
anywhere. The run is isolated from the project because the tokenizer needs a newer protobuf.

It first checks the tokenizer against the model: it rebuilds every answering prompt of the
arms that use the shared answer prompt and compares its count with the input tokens that
Vertex reported for that call (results/<split>/ledger.jsonl). Then it counts what the tables
report: the context each read path handed to the answering model, and the histories.
The counts are saved to results/<split>/_context_tokens.json ({arm: {qid: tokens}}), which
memeval.report and memeval.findings read, so the tables need no tokenizer.
"""

from __future__ import annotations

import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

from google.genai.local_tokenizer import LocalTokenizer

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from memeval import prompts  # noqa: E402  (plain strings, no dependencies)

TOKENIZER = LocalTokenizer(model_name="gemini-3.1-flash-lite")
HISTORY_ARMS = {"full-context", "retrieval"}
SHARED_PROMPT = {"full-context", "retrieval", "textual", "mem0", "graphiti", "graphiti-chunk",
                 "honcho-chat", "honcho-repr"}


def count(text: str) -> int:
    return TOKENIZER.count_tokens(text).total_tokens


def results(split: str) -> dict[str, dict[str, dict]]:
    out = {}
    for d in sorted(p for p in (REPO / "results" / split).iterdir() if p.is_dir() and not p.name.startswith("_")):
        rows = {p.stem: json.loads(p.read_text()) for p in sorted(d.glob("*.json"))}
        out[d.name] = {q: r for q, r in rows.items() if "judge" in r}
    return out


def answer_calls(split: str) -> dict[tuple[str, str], list[int]]:
    calls = defaultdict(list)
    for line in (REPO / "results" / split / "ledger.jsonl").read_text().splitlines():
        c = json.loads(line)
        if c.get("phase") == "answer" and c["kind"] == "chat":
            calls[(c["arm"], c["qid"])].append(c["input_tokens"])
    return calls


def prompt_for(arm: str, r: dict) -> str:
    template = prompts.ANSWER_FROM_HISTORY if arm in HISTORY_ARMS else prompts.ANSWER_FROM_MEMORY
    date = r["question_date"].replace("-", "/")
    return template.format(context=r["context"] or "(nothing)", date=date, question=r["question"])


def main() -> None:
    for split in ("main", "full"):
        res, calls = results(split), answer_calls(split)
        print(f"\n## {split}\n")
        print("Check: rebuilt answer prompt (local count) against the model's reported input tokens")
        for arm, rows in res.items():
            if arm not in SHARED_PROMPT:
                continue
            diffs = []
            for q, r in rows.items():
                reported = calls.get((arm, q))
                if reported:
                    local = count(prompt_for(arm, r))
                    diffs.append(min(abs(local - x) for x in reported))
            if diffs:
                print(f"  {arm:15s} n={len(diffs)}  exact {sum(d == 0 for d in diffs)}  "
                      f"mean |diff| {st.mean(diffs):.1f}  max {max(diffs)}")
        print("\nContext handed to the answering model, tokens (mean; chars/4 for comparison)")
        saved = {arm: {q: count(r["context"] or "") for q, r in rows.items()} for arm, rows in res.items()}
        (REPO / "results" / split / "_context_tokens.json").write_text(json.dumps(saved, indent=1, sort_keys=True) + "\n")
        for arm, rows in res.items():
            ctx = list(saved[arm].values())
            est = [len(r["context"] or "") / 4 for r in rows.values()]
            print(f"  {arm:15s} {st.mean(ctx):9,.0f}   (min {min(ctx):,}, max {max(ctx):,})   chars/4 {st.mean(est):9,.0f}")
        if "6a1eabeb" in res.get("full-context", {}):
            print(f"\nQuestion 6a1eabeb, full-context history: "
                  f"{count(res['full-context']['6a1eabeb']['context']):,} tokens")
    main_res, full_res = results("main"), results("full")
    print("\n## Same 25 questions, trimmed and whole (context tokens, mean)\n")
    for arm, frows in full_res.items():
        m = [count(main_res[arm][q]["context"] or "") for q in frows]
        f = [count(r["context"] or "") for r in frows.values()]
        print(f"  {arm:15s} {st.mean(m):9,.0f} -> {st.mean(f):9,.0f}")


if __name__ == "__main__":
    main()
