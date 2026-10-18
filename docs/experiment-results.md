# The LongMemEval experiment: results

What the experiment found, with one worked example per system. How it was run
is in [experiment.md](experiment.md); the generated tables are in
[results/main/report.md](../results/main/report.md) and
[results/full/report.md](../results/full/report.md), and every number below can
be traced to a file under `results/`.

Runs: 17 October 2026. 67 knowledge-update questions (the 72 without
abstention, minus 5 pilot questions used for checking), history trimmed to both
evidence sessions plus 8 distractors, about 28,000 tokens. One model,
`gemini-3.1-flash-lite`, in every seat; `gemini-3.1-pro-preview` as judge.

**These numbers are not comparable to published LongMemEval results.** The
history is trimmed, there is one question type, and the models differ.

## Accuracy

| Arm | Accuracy (n = 67) | 95% interval | Cost per question |
|---|--:|---|--:|
| full-context | 90% | 80%–95% | $0.007 |
| retrieval (BM25, top 10 rounds) | 97% | 90%–99% | $0.002 |
| textual memory | 93% | 84%–97% | $0.022 |
| Mem0 | 84% | 73%–91% | $0.040 |
| Honcho, dialectic chat | 87% | 76%–93% | $0.030 |
| Honcho, representation | 93% | 84%–97% | $0.028 |
| Graphiti | 18% | 11%–29% | $0.238 |
| Letta | 58% | 46%–69% | $0.029 |

Cost per question is what the system spent on writing, reading and answering,
measured from the call ledger; judging and probes are extra and the same for
every arm.

With 67 questions only large gaps mean anything. Six arms sit between 84% and
97% with overlapping intervals; the ordering among them is not a result. Two
arms are clearly apart: Graphiti and Letta.

The judges agree: `gemini-3.1-pro-preview` and `gemini-3.8-flash` gave the same
verdict on 95 of 96 answers judged by both.

## In this regime, memory can only lose

At 28,000 tokens the whole history fits in the answering model's context, so
full context is close to its ceiling. Every memory system here is doing a job
the model did not need done, and the question is how much each one loses.

Plain retrieval over raw turns lost nothing: 65 of 67, above full context, with
a fifth of the tokens. Full context's seven errors are answer-model errors. In
five of them the new value was in the prompt and the model answered with the old
one, for example quoting a $350,000 mortgage pre-approval and adding "in a later
conversation on November 30, 2023, you mentioned $400,000". A shorter context
made that mistake rarer, not more common.

The [full-history run](#what-trimming-hid) is what moves the experiment out of
this regime.

## Where answers were lost

The probes (`gemini-3.8-flash`) check, for every question, whether the new value
is in the store, whether it reached the answering model, and whether the
answer gave the old value. Every wrong answer is put in the first category that
explains it:

| Arm | correct | update never stored | stored, not delivered | delivered, answered old value | delivered, other error | wrong, unclassified |
|---|--:|--:|--:|--:|--:|--:|
| full-context | 60 | n/a | n/a | 5 | 1 | 1 |
| retrieval | 65 | n/a | 0 | 2 | 0 | 0 |
| textual | 62 | 1 | 0 | 1 | 3 | 0 |
| Mem0 | 56 | 6 | 0 | 2 | 2 | 1 |
| Honcho chat | 58 | 1 | 1 | 2 | 4 | 0 |
| Honcho repr | 62 | 2 | 0 | 1 | 1 | 1 |
| Graphiti | 12 | **45** | 0 | 0 | 1 | 9 |
| Letta | 39 | **22** | 0 | 0 | 0 | 6 |

Three things stand out.

1. **Loss is at write time.** Every arm that loses more than a handful of
   answers loses them because the update never made it into memory. "Stored but
   not delivered" is almost empty: on a 10-session history every read path finds
   what was written. (This is what trimming was expected to do; see below.)
2. **Nobody resolves the conflict at write time, and it mostly does not
   matter.** The old value was still stored, and still presented as current,
   in 25 of Mem0's 67 stores and 42 of Honcho's. When both values reached the
   answering model with their dates, the answer picked the newer one 51 times
   out of 53 for Honcho's representation, 41 of 45 for Mem0 and 37 of 39 for
   textual memory. Dates on every stored item are what make this work, which is
   why the experiment passes the session dates into every system.
3. **The two systems that let a model decide what is worth keeping lose the
   most.** Graphiti's extraction and Letta's agent both run on
   `gemini-3.1-flash-lite` here. In both designs the model's judgement is the
   memory policy, so a stronger model would change these two rows the most.

## One example per system

**Full context: the answer model ignores the update.** *"How many followers do
I have on Instagram now?"* (reference: 1,300.) The whole history is in the
prompt. The model reads "nearing 1300 followers" from the later session and
answers that, as of May 25 the user "was nearing 1300 followers", which the
judge marks wrong. The data is there; the reading is cautious.

**Retrieval: one of two misses.** *"What was the amount I was pre-approved for
when I got my mortgage from Wells Fargo?"* (reference: $400,000.) Both sessions
are retrieved; the model takes "pre-approved for" to mean the first figure and
answers $350,000. Full context gives the same answer. This is the question's
wording as much as the system.

**Textual memory: the update is an aside, and the rewrite drops it.** *"Where
do I initially keep my old sneakers?"* (reference: under my bed.) The profile is
rewritten in full after every session and keeps "The user owns a collection of
footwear, including sneakers, dress shoes, and boots", but not where they are
kept. The same rewrite gets the Instagram question right: the profile says
"The user maintains an Instagram account with approximately 1,300 followers, as
of 2023-05-25".

**Mem0: both facts kept, both delivered, added up.** *"How many sessions of the
bereavement support group did I attend?"* (reference: five.) Mem0 stores "User
attended three sessions of a bereavement support group (from a chat on
2023-05-11)" and "User attended five sessions … last year (from a chat on
2023-10-30)". Its update step treated the second as a new fact rather than a
replacement, both come back from `search()`, and the answering model adds them:
"3 + 5 = 8".

**Honcho: the dialectic agent hedges where the raw conclusions do not.**
*"How many Instagram followers do I currently have?"* (reference: 600.)
Honcho's deriver stored both "user reached 500 followers on Instagram during the
week of May 20, 2023" and "user has 600 followers on Instagram as of
2023-05-28" as explicit, dated conclusions. Given those conclusions directly
(`honcho-repr`), the answer is 600. The dialectic agent (`honcho-chat`) also
finds 600, but phrases it as "you had 600 followers as of May 28 … I cannot
provide your current follower count", and the answer built on it is marked
wrong. Over the run the agent's summary costs a little more than the raw
conclusions and scores a little lower (87% against 93%); the difference is
inside the interval.

**Graphiti: the update is never extracted.** *"How many projects have I
completed since starting painting classes?"* (reference: 5.) The graph holds
"The user has completed 4 painting projects since they began taking painting
classes (valid since 2023-08-16)". The later session's mention of a fifth
project never became an edge, so nothing was invalidated and the answer is 4.
This is the typical Graphiti failure here: about 57 edges per question from 20
episodes, 0.2 edges closed as superseded per question, and the new value absent
from the graph in 45 of 67 questions. It is also the most expensive arm by far,
121 model calls and 900,000 input tokens per question, eight times the next
system.

**Letta: an empty memory block and a substring search.** *"How many engineers
do I lead when I just started my new role as Senior Software Engineer? How many
engineers do I lead now?"* (reference: 4, then 5.) After ten sessions the
agent's `human` block is still empty; it was empty after 43 of the 67 histories.
To answer, the agent calls `conversation_search` fifty times ("lead engineers",
"Senior Software Engineer role", "engineer team" …) and gets "No results found"
for most of them, then gives no reply. In the self-hosted server
`conversation_search` is a SQL `ILIKE` match on the literal query unless
Turbopuffer (a hosted service) is configured, so a query has to appear verbatim
in a message to find it. Letta's correct answers come from searches that happen
to match: it scores the same with an empty `human` block (25 of 43) as with a
filled one (14 of 24).

## Cost

Mean per question, from the ledger (USD):

| Arm | write | read | answer | total | model calls at write | input tokens at write |
|---|--:|--:|--:|--:|--:|--:|
| full-context | – | – | 0.0065 | 0.0065 | 0 | 0 |
| retrieval | – | – | 0.0017 | 0.0017 | 0 | 0 |
| textual | 0.0212 | – | 0.0007 | 0.0219 | 10 | 34,269 |
| Mem0 | 0.0389 | – | 0.0006 | 0.0395 | 10 | 116,073 |
| Honcho chat | 0.0278 | 0.0014 | 0.0003 | 0.0296 | 39 | 71,732 |
| Honcho repr | 0.0274 | – | 0.0007 | 0.0281 | 38 | 70,661 |
| Graphiti | 0.2375 | – | 0.0004 | 0.2380 | 121 | 897,212 |
| Letta | 0.0249 | 0.0039 | – | 0.0288 | 11 | 51,712 |

Letta's answer is its own reply, so its answering cost is counted as read.

Total spend on Vertex for the whole experiment, smoke tests included: see
[the last section](#reproducing-it).

## What trimming hid

FULL_HISTORY_PLACEHOLDER

## Limits

- Trimmed history, one question type, 67 questions, one model in every seat.
- Each fact is stated once and revised once. A system whose value is inferring
  patterns from repetition (Honcho's claim) has nothing to work on here.
- Every system runs at its library defaults, with the exceptions listed at the
  top of each arm's module in `src/memeval/arms/` and in each result's
  `settings`.
- Letta is its last Python server release, 0.16.8, self-hosted, so its
  conversation search is the SQL fallback described above.
- One run per arm at temperature 0. Repeated model calls are served from the
  cache, so a re-run reproduces these numbers exactly; a fresh run without the
  cache may differ by a few answers.
- No vendor took part, and none was asked to tune its system.

## Reproducing it

REPRO_PLACEHOLDER
