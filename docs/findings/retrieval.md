# Retrieval: why the simplest arm scores highest

Hand-written, from the replayed model calls of the retrieval arm and the result
files in `results/main/retrieval/` and `results/full/retrieval/`.

## Summary

Plain retrieval answers 65 of 67 (97%, 95% interval 90–99%), at $0.002 per
question and no model calls to write: BM25 over rounds (a user message and the
assistant reply after it), the top 10 rounds by the question's words, each with
its session date and time, put back in date order. Its two wrong answers are
both flawed questions.

| Cause | answers | questions |
|---|--:|---|
| The question or its key is flawed | 2 | `618f13b2`, `852ce960` |

## Why it works on this benchmark

- **Nothing is lost at write time.** There is no write step, so a revision
  mentioned in passing is still there, word for word, in its round. The failure
  every write-time system shares (an aside that was never turned into a memory)
  cannot happen.
- **The question's words find both values.** A knowledge-update question names
  the thing that changed ("Instagram followers", "Crash Course videos"), and the
  user's two statements use the same words. Both values were among the ten
  rounds in 54 of the 58 questions with an old value.
- **Dates come with the text.** Each round carries "[Session date: 2023-05-25
  09:28]", to the minute, so same-day revisions are ordered. With both values
  delivered, it answered 52 of 54 correctly.
- **The answer reads the user's own sentence**, not a paraphrase of it, so none
  of the reframing failures of the extraction systems ("in the past few weeks"
  turned into a running total, a routine against a one-off plan) occur.

The context is about 5,800 tokens, a fifth of full context, and the accuracy is
higher: the ten rounds hold the two statements and little else to reason back
from.

## The two wrong answers

- **`618f13b2`** (key: six). Both rounds retrieved; "At 17:45, the user stated
  they had worn them **six** times. At 22:16, the user stated they had worn them
  **four** times… the most recent statement provided in the chat history is that
  they have worn them **four** times." The key holds the earlier value.
- **`852ce960`** (key: $400,000). Both rounds retrieved; the answer judged the
  later "remember when I got pre-approved for $400,000" to be "a misremembered
  figure by the user" and answered $350,000. The question's "when I got my
  mortgage" points at the first figure.

## The full history

With all ~48 sessions, accuracy is 96% (from 100% on the same 25 questions),
cost unchanged: BM25 still returns ten rounds. The one error, `4d6b87c8`: "Your
count increased from 20 to 25 titles… you explicitly stated you were adding two
more films… 25 + 2 = 27", the same arithmetic Graphiti and Mem0 made.

## Limits

This benchmark favours retrieval: every question names its topic, each fact is
stated twice in similar words, and the trimmed history is small. A question
whose answer must be inferred from many scattered mentions, or phrased in words
the user never used, is where a memory that summarises would earn its cost.
