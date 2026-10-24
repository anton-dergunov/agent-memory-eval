# The LongMemEval experiment: results

What the experiment found. How it was run is in [experiment.md](experiment.md).
The numbers come from three generated or hand-written companions:

- [findings/tables.md](findings/tables.md): every table below, rebuilt from the
  result files by `python -m memeval.findings`;
- [findings/failures.md](findings/failures.md): every wrong answer, with the
  answer text and the arms that share it;
- [findings/failure-analysis.md](findings/failure-analysis.md): every wrong
  answer read and sorted by cause;
- one account per system, following each wrong answer through the model calls
  and saying how the right ones were reached:
  [Letta](findings/letta.md), [Graphiti](findings/graphiti.md),
  [Mem0](findings/mem0.md), [Honcho](findings/honcho.md),
  [textual memory](findings/textual.md),
  [full context](findings/full-context.md) and
  [retrieval](findings/retrieval.md).

Every number can be traced to `results/<split>/<arm>/<qid>.json` and the call
ledgers saved next to them. The raw model calls (requests and replies) are
kept, but not published with the repository.

Runs: 17–18 October 2026. 67 knowledge-update questions (the 72 without
abstention, minus 5 pilot questions used for checking), each history trimmed
to both evidence sessions plus 8 distractors, about 28,000 tokens; then 25 of
them again with the whole history, about 124,000 tokens. One model,
`gemini-3.1-flash-lite`, in every seat; `gemini-3.1-pro-preview` as judge.

**These numbers are not comparable to published LongMemEval results.** The
history is trimmed, there is one question type, and the models differ.

## Accuracy, cost and time

| Arm | Accuracy (n = 67) | 95% interval | USD per question | model calls to write | seconds to write | servers |
|---|--:|---|--:|--:|--:|---|
| full context | 90% | 80%–95% | 0.007 | 0 | 0 | none |
| retrieval (BM25, top 10 rounds) | 97% | 90%–99% | 0.002 | 0 | 0 | none |
| textual memory | 93% | 84%–97% | 0.022 | 10 | 27 | none |
| Mem0 | 84% | 73%–91% | 0.039 | 10 | 38 | none |
| Honcho, dialectic chat | 87% | 76%–93% | 0.029 | 38 | 115 | API, deriver, Postgres, Redis |
| Honcho, representation | 93% | 84%–97% | 0.028 | 38 | 115 | (the same) |
| Graphiti | 82% | 71%–89% | 0.640 | 720 | 839 | Neo4j |
| Letta | 69% | 57%–78% | 0.132 | 81 | 379 | Letta server, Postgres |
| Letta, persona that keeps facts current | 90% | 80%–95% | 0.152 | 88 | 265 | (the same) |

Cost is what the system spent writing, reading and answering, from the call
ledger; judging and probes are extra and the same for every arm. The judges
agree: `gemini-3.1-pro-preview` and `gemini-3.8-flash` gave the same verdict on
130 of 132 answers judged by both.

With 67 questions only large gaps mean anything. Seven arms sit between 82%
and 97%. Their intervals overlap except at the two ends (Graphiti's 71%–89%
against retrieval's 90%–99%). Tested pair by pair on the same questions
(McNemar's test, one test for each of the 21 pairs), even the clearest gap,
retrieval over Mem0, does not hold up: 9 questions only retrieval got right and
none only Mem0 got right gives p = 0.004 on its own, short of the 0.05 / 21 ≈
0.0024 that a Bonferroni correction asks of 21 tests. The order among them is
not a result.
Letta at its defaults is the one arm clearly below. With three lines added to
its persona block, the part of Letta its users are meant to write, it scores
90% and joins the others (point 4 and [findings/letta.md](findings/letta.md)). Between the arms that work, the
differences that are large are cost and weight: Graphiti spends about 30
times what textual memory spends and over 300 times what plain retrieval
spends, for no gain in accuracy here.

## 1. How a system is fed decides whether it remembers

The first runs of Graphiti and Letta scored 18% and 58%. Neither number was
about the systems; both were about how the conversation was handed to them.

| Arm | how it was fed | accuracy | update never stored | calls to write | USD per question |
|---|---|--:|--:|--:|--:|
| Graphiti | sessions cut into episodes of up to 8,000 characters | 18% | 45 | 121 | 0.24 |
| Graphiti | one episode per message, as Graphiti's own examples do | 82% | 5 | 720 | 0.64 |
| Letta | each session in one request, ending on an assistant message | 58% | 22 | 11 | 0.03 |
| Letta | one agent step per user message | 69% | 15 | 81 | 0.13 |
| Letta | the same, with a persona that asks it to keep facts current | 90% | 3 | 88 | 0.15 |

**Graphiti** extracts entities and facts from each episode with prompts written
for one message from a named speaker ("Jordan: we just moved to Denver…"),
which tell the model to skip generic activities and, "when in doubt, do not
extract". It also adds the previous ten episodes as context. With
8,000-character episodes every extraction prompt carried 60,000–80,000
characters, mostly the assistant's long answers, and the model returned two
or three entities. In a traced example the update "I just finished my 5th
project since starting painting classes" was in the prompt; the model
extracted `assistant` and `bold colors`, so no fact about projects existed to
update. With one message per episode the same sentence produced the entities
`user`, `painting project` and `painting classes` and the edge "The user has
completed their 5th project since they began attending painting classes".

**Letta**'s agent decides what to remember during its own turn. Sent a whole
session at once, ending on an assistant message, it had nothing to answer and
in most sessions took no step at all: in a trace, 6 of 10 sessions produced
nothing and only the first produced a memory edit, and the `human` block stayed empty after 43 of 67
histories. One step per user message gives it a turn after every message; it
then edits its memory about ten times per history.

Neither fix changes a setting of either system; both make the input look like
the input each system was built for. The contract is not written down in
either API, nothing fails when it is broken, and the price of keeping it is
real: Graphiti's correct run costs 2.7 times the broken one, Letta's 4.6
times.

## 2. What memory looks like after an update

The probes read the whole memory and the context given to the answer, for
every question:

| Arm | new value stored | old value still stored | old value still current | both values delivered | correct when both delivered | context given to the answer (tokens) |
|---|--:|--:|--:|--:|--:|--:|
| full context | n/a | n/a | n/a | 58 | 52/58 | 27,890 |
| retrieval | n/a | n/a | n/a | 54 | 52/54 | 5,761 |
| textual memory | 85% | 64% | 7% | 39 | 37/39 | 1,513 |
| Mem0 | 78% | 81% | 37% | 45 | 41/45 | 930 |
| Honcho chat | 82% | 81% | 64% | 39 | 33/39 | 77 |
| Honcho repr | 82% | 81% | 64% | 53 | 51/53 | 935 |
| Graphiti | 78% | 70% | 21% | 39 | 37/39 | 284 |
| Letta | 42% | 33% | 24% | 15 | 12/15 | 884 |
| Letta, persona | 79% | 66% | 9% | 43 | 42/43 | 1,288 |

Three readings:

- **Almost nobody resolves the conflict at write time, and with dates it
  mostly does not matter.** Mem0 keeps the old value as a current fact in a
  third of the questions, Honcho in two thirds; Graphiti, the system built to
  close superseded facts, still presents the old one as current in a fifth.
  When both values reach the answering model with their dates, it picks the
  newer one about nine times in ten (51 of 53 for Honcho's representation).
- **The systems that overwrite keep less, not better.** Textual memory
  rewrites its profile and keeps the old value as current in only 7% of
  questions, at the cost of occasionally dropping a detail. Letta's memory
  holds the new value in only 42% of questions. Its agent writes about ten
  times per history, but at the message carrying the revision it recorded the
  new value in only 31 of 64 questions, and when the value is missing its
  search rarely finds the message again
  ([findings/letta.md](findings/letta.md)). Asked in its persona to update
  the line and keep the earlier value with its date, it writes 57 of 64
  revisions and holds the new value in 79% of questions. It also keeps the old
  value in the line more often (66%) while presenting it as current less
  often (9%).
- **The amount delivered differs by a factor of 360** between Honcho's
  dialectic summary (77 tokens) and full context (27,890), with accuracy
  within the same interval.

## 3. Asking for the current value or an earlier one

Eight questions ask for an earlier value ("What was my *previous* frequent
flyer status?"), three for both. The expectation was that systems which
overwrite would lose the earlier value:

| Arm | current value (56) | earlier value (8) | both (3) |
|---|--:|--:|--:|
| full context | 50 | 7 | 3 |
| retrieval | 54 | 8 | 3 |
| textual memory | 52 | 7 | 3 |
| Mem0 | 48 | 6 | 2 |
| Honcho chat | 48 | 7 | 3 |
| Honcho repr | 52 | 7 | 3 |
| Graphiti | 46 | 8 | 1 |
| Letta | 39 | 6 | 1 |
| Letta, persona | 50 | 8 | 2 |

It does not show here. Textual memory, which rewrites its profile, answers 7
of the 8, and its rewrites often keep the history in the line itself ("15 …
as of 2023-09-30; previously 12 as of 2023-08-11"). Eight questions are too
few to measure a difference of this kind; the table is reported because the
question was asked, not because it separates the systems.

## 4. Why the answers were wrong

Reading every wrong answer (overview in
[findings/failure-analysis.md](findings/failure-analysis.md), one file per
system next to it):

- **Three questions are flawed.** They account for 12 of the 39 wrong answers
  among full context, retrieval, textual memory, Mem0 and Honcho. In one
  (`618f13b2`) two sessions on the same day say six and then four, and the key
  says six; every one of those arms answers four.
- **Losing the update at write time** is the common failure of the systems
  with a write step: 4 of Mem0's 11 wrong answers, 6 of Graphiti's 12, 14 of
  Letta's 21. Typically the revision was mentioned in passing ("By the way, I
  just finished my 5th project since starting painting classes").
- **Honcho's dialectic agent refuses to choose.** Five of its nine wrong
  answers decline to pick between two dated values ("there is conflicting
  information… clarification is required"). Given the same conclusions
  directly, the representation path answers; this is most of the six-point gap
  between the two.
- **Mem0 adds instead of replacing.** "Attended three sessions" and "attended
  five sessions" come back as two facts, and the answer is 3 + 5 = 8.
- **Textual memory invites subtraction.** Its profile records running counts
  with their history ("The user has 25 postcards in their collection as of
  2023-11-30 (up from 17 items reported on 2023-08-11)"), and the answer to
  "how many new postcards have I added" becomes 25 − 17 = 8 (the key: 25).
- **Graphiti's dates can close the wrong fact.** It dates a fact by when it
  became true, not when it was said. "The user visited Paris with their family
  last month", said in May, became valid from April 1; "a recent family trip to Hawaii"
  became valid from the day it was mentioned, May 26. Graphiti closed Paris as
  superseded by Hawaii, and the answer followed the graph. Every other system
  answered Paris.
- **Letta's agent notices the revision and does not write it down.** "By the
  way, I just checked and I'm now at 600 followers" drew "Congratulations on
  hitting 600 followers!" and no memory edit; 18 revisions went that way.
  Inserting the new value worked as well as replacing the old one (11 of 12
  correct, against 16 of 19), so the loss is not appending instead of
  replacing; it is not writing at all. The fallback cannot recover it: the
  self-hosted server's `conversation_search` is a phrase match that returns the
  five newest matches, and 97 of the agent's 146 searches at answer time
  returned nothing. In six wrong answers the block still held the first value
  ("has completed 4 projects so far") and the agent answered from it after its
  searches came back empty.
- **Telling Letta's agent fixes most of it.** The persona had been Letta's
  blank starter text. Three lines added to it (write the message's date on
  every fact, update the line when a value changes and keep the earlier one,
  search with one or two words) raised the revisions written at the message
  from 31 to 57 of 64 and the score from 69% to 90%. Fourteen of the 17
  answers it gained can be traced to those lines. Of its seven wrong answers
  one is a lost update. Two had the right dated lines and reasoned wrongly at
  answer time ("you switched to more water… you are now using less water"),
  and one is a plan counted as a fact: "I'm definitely going to add" two
  films turned 25 titles into 27. The persona was written after reading
  these failures on the same questions, so 90% is not a held-out score.
- **One Letta question could not be built.** In four builds Vertex returned
  `finish_reason=content_filter` with no message while the agent read a
  history about a named book, and Letta stops on such a reply. It is counted
  as wrong.

## 5. What trimming hid: the full history

The same 25 questions with all ~48 sessions, for the four arms cheap enough
to run on 124,000-token histories:

| Arm | accuracy, 10 sessions | accuracy, full history | context tokens | USD per question, 10 → full |
|---|--:|--:|---|---|
| full context | 92% | 84% | 27,677 → 123,631 | 0.007 → 0.028 |
| retrieval | 100% | 96% | 5,825 → 5,881 | 0.002 → 0.002 |
| textual memory | 96% | 92% | 1,515 → 5,567 | 0.022 → 0.277 |
| Mem0 | 84% | 84% | 919 → 910 | 0.040 → 0.181 |

- **Full context slips, it does not collapse.** All four of its errors on the
  full history are the new value in the prompt and the old one in the answer
  (for example 27:12 instead of the later 25:50). On 25 questions the drop
  from 92% to 84% is two answers and inside the interval; the paper's GPT-4o
  fell from 0.87 to 0.61 on the same histories. A model that reads 124,000
  tokens well removes most of the capacity argument for memory on this
  benchmark.
- **The cost of memory grows with the history at write time.** Textual memory
  costs 13 times more per question on the full history (one rewrite per
  session, of a growing profile), Mem0 4.5 times; retrieval costs the same,
  because it does nothing until asked. Read-time context stays flat for every
  memory system.

## Limits

- Trimmed history for the main run, one question type, 67 questions, one
  model in every seat. In Graphiti's extraction and Letta's agent the model's
  judgement is the memory policy; a stronger model would change those two
  rows most. For Letta the persona moved the row further than feeding it
  correctly did (69% → 90%, against 58% → 69%).
- Each fact is stated once and revised once. A system whose value is inferring
  patterns from repetition (Honcho's claim) has nothing to work on here.
- Every system runs at its library defaults, with the exceptions listed at the
  top of each arm's module in `src/memeval/arms/` and in each result's
  `settings`. Graphiti and Letta were re-run once with their ingestion fixed;
  the first runs are kept as `graphiti-chunk` and `letta-batch`. Letta was
  run a third time with an instructed persona (`letta-persona`), as its own
  row; no other arm was re-run with a changed prompt.
- Letta is its last Python server release, 0.16.8, self-hosted: its
  `conversation_search` is a literal SQL substring match unless Turbopuffer, a
  hosted service, is configured.
- The probes take the reference answer as "the new value"; for the 11 questions
  that ask for an earlier value or both, "new value stored" means "the value
  asked for was stored".
- One run per arm at temperature 0 (Letta's agent at its own default). Repeated
  model calls are served from the cache: replaying full context, retrieval and
  textual memory from the cache reproduces all 201 answers byte for byte.
- No vendor took part, and none was asked to tune its system.

## Reproducing it

Total Vertex spend for the whole experiment, smoke tests and every Graphiti
and Letta run included: about $110 (main run $93, of which the Letta persona
run $10.68; full-history run $13; pilot $2.63; traces and checks the rest). Rebuilding every table from the committed
results costs nothing (`python -m memeval.findings`, no model calls). The reply
cache (`.cache/llm`) is not published, so re-running the systems themselves
costs about that much again; see [experiment.md](experiment.md) for the
commands.
