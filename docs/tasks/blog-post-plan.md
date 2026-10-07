# Plan: from the intuition notebooks to a published post

This is the working plan for the project. It records what the post should claim,
which experiment backs it, what that experiment costs, and the decisions already
made along with their reasons. Read it before starting any stage.

## The goal

One blog post about how LLM agent memory systems work, backed by this
repository.

The post has two halves:

1. **Mechanism.** One short conversation, in which a user changes their mind, run
   through each system with every model call shown. The four notebooks already
   do this.
2. **Evidence.** A small experiment on a public benchmark that checks whether what
   the notebooks show on one short conversation also holds on real data.

The post is written by hand from these materials. The notebooks stay separate as
intuition material and are not converted into the post. The experiment is plain
Python under `src/`, not a notebook.

## Why this post is worth writing

The field is crowded, so the angle matters.

- **Saturated:** "best memory frameworks" lists and vendor benchmark results, where
  each vendor's benchmark shows that vendor winning.
- **Exists, and good:** comparisons made by reading the source code. The closest is
  CodePointer's post on Letta, Mem0, Graphiti and Cognee (May 2026). It does not
  run the systems.
- **Not found:** the same conversation through every system, every call
  intercepted and counted, with the silent failures shown. That is the angle.

Reference points to read before writing, and to cite:

- Zep, [Is Mem0 Really SOTA in Agent Memory?](https://blog.getzep.com/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/)
- Penfield Labs, [We audited LoCoMo](https://penfieldlabs.substack.com/p/we-audited-locomo-64-of-the-answer)
- Continua, [The LoCoMo "Fair Fight"](https://blog.continua.ai/p/the-locomo-fair-fight)
- CodePointer, [Agent Memory Systems and Knowledge Graphs](https://codepointer.dev/p/agent-memory-systems-and-knowledge)
- Mastra, [Observational Memory](https://mastra.ai/research/observational-memory)
- Letta's post on a filesystem agent as a memory baseline (not re-checked; find
  and verify before citing)

**Shelf life.** Prompts and versions will be out of date within months. The
questions will not be: what gets written, who resolves a contradiction, what the
read path returns, what it costs. Organise the post by those questions, pin every
library to a commit or version, and date the post.

## Systems

The systems are organised by who decides what is written to memory. Each row is a
distinct design, which is the reason it is included.

| Who writes | Arm | State |
|---|---|---|
| Nobody | Full context | to build (trivial) |
| Nobody | Plain retrieval over raw turns | to build (small) |
| An extraction pipeline | Mem0 | notebook exists |
| A pipeline, into a dated graph | Zep / Graphiti | notebook exists |
| The agent itself, inside the answer turn | Letta | notebook exists |
| A background rewriter of one text file | Textual memory | to build (about 50 lines) |
| A background reasoner | Honcho | notebook exists |

Decisions:

- **Add the textual-memory arm.** This is PersonaMem-v3's "Textual Memory": one
  plain-text profile, rewritten whole after each batch of history, held under a
  token cap. In that paper it beats Mem0 on tracking preference changes (79.9%
  against 56.9%). It is the baseline the vendors have to beat.
- **Textual memory is not the same thing as Letta.** Both keep memory as text that
  is always in the prompt. They differ in who writes and when. In Letta the
  answering agent edits structured blocks through tool calls during the turn, with
  an optional background agent. In textual memory a separate call rewrites the
  whole file between sessions and the answering model never writes. Keeping both
  shows what Letta's machinery adds over the simplest version of the same idea.
- **Skip Cognee.** It is in the same design quadrant as Graphiti and is aimed at
  knowledge from documents more than at a user's changing preferences.
- **Describe Mastra's Observational Memory, do not run it.** It is TypeScript. Its
  design: an Observer compresses messages into dated observations once they pass
  about 30k tokens, and a Reflector merges and prunes observations once they pass
  about 40k. There is no retrieval and no database; the log stays in the prompt,
  which keeps it cacheable. Mastra reports 94.87% on LongMemEval with gpt-5-mini.
  That figure is the vendor's own. It is the most developed version of the
  textual-memory family, so it belongs in the same section.
- **Describe ChatGPT's and Claude's built-in memory, do not run them.** They cannot
  be driven as libraries.
- **Do not add more vendors.** A seventh or eighth system turns the post into the
  kind of list it is meant to improve on.

## The experiment

### Dataset: LongMemEval, knowledge-update questions

LongMemEval has 500 questions. Each comes with its own chat history between one
user and an assistant, and each is labelled with the sessions that contain the
evidence. The 78 knowledge-update questions are the ones where the user states a
fact and later revises it, which is the scenario the notebooks are built on.

Measured on the S version (the `longmemeval_s_cleaned.json` file from the
`xiaowu0162/longmemeval-cleaned` dataset on Hugging Face):

| | Value |
|---|---|
| Questions | 500 in total, 78 knowledge-update |
| Sessions per question | 48 on average (38 to 62) |
| Turns per session | about 10 (median 12) |
| Tokens per session | about 2,600 |
| Tokens per question | about 122,000 |
| Share of tokens in user turns | 13% |
| Evidence sessions, knowledge-update | exactly 2 in all 78 questions |
| Days between the two evidence sessions | median 40 |

The other question types, for reference: multi-session 133, temporal-reasoning
133, single-session-user 70, single-session-assistant 56,
single-session-preference 30.

An example question: *"What was my personal best time in the charity 5K run?"*
The first evidence session says 27:12. The second says, in passing, *"By the way,
I'm hoping to beat my personal best time of 25:50 this time around."* The correct
answer is 25:50. Updates are often this incidental, which is what makes
extraction hard.

Scoring is a yes/no judgement from an LLM judge with a prompt per question type.
The paper validated it against human labels. It is a real accuracy, unlike the
rubric scores of personalisation benchmarks.

The paper says the data is released under the MIT licence. Confirm this on the
repository before publishing numbers.

**Why not LoCoMo.** It is cheaper per question, because one conversation serves
about 150 questions. But its conversations fit in a context window, an audit
found 6.4% of the answer key wrong, its judge accepted up to 63% of deliberately
wrong answers, and it has few real revisions.

**Why not PersonaMem-v3.** Its licence is non-commercial and it is kept out of
this project.

### The trimmed history, and what trimming costs

Running all 48 sessions per question through every system costs about $2 per
question, almost all of it Graphiti. So the main run uses a trimmed history: both
evidence sessions plus 8 distractor sessions sampled at random with a fixed seed,
kept in their original order with their original timestamps. That is 10 sessions
and about 26,000 tokens per question.

What trimming does **not** remove: the evidence. Both labelled sessions are always
kept. The other 46 or so are distractors by construction. Half are unrelated
public chats and half are simulated sessions about the same user's other
attributes.

What trimming **does** remove:

- **Retrieval difficulty.** Searching 10 sessions is much easier than 48, so
  scores rise for every system, and most for the ones with weak retrieval. The
  main run therefore tests the write path and conflict resolution, and mostly
  does not test the read path.
- **Interference at write time.** Fewer unrelated memories means fewer wrong
  merges and fewer entity collisions.
- **Headroom over the baseline.** At 26,000 tokens, reading the whole history is
  close to its ceiling. Memory systems can mostly only lose to it. This is a
  result to show, not to hide: it is the regime where memory is not needed for
  capacity, so any loss is the price of the memory layer.

A limit that comes from the dataset, not from trimming: each fact is stated once
and revised once. Nothing is repeated across many sessions. A system whose value
is inferring patterns from repetition, which is Honcho's claim, has nothing to
work on here, even with the full history. This slice tests supersession. Say so
in the post.

The numbers from the trimmed run are **not comparable** to published LongMemEval
results. State this next to every number.

### Design

| Run | Questions | History | Arms | Purpose |
|---|---|---|---|---|
| Pilot | 5 | 10 sessions | all | Replace the cost estimates with measured ones |
| Main | 50 (fixed seed) | 10 sessions | all | The comparison |
| Full history | 25 of the 50 | all 48 sessions | cheap arms only | Measure what trimming hid |

The full-history run is what turns the trimming from an assumption into a
measurement. The cheap arms are full context, plain retrieval, Mem0 and textual
memory.

With 50 yes/no questions the 95% interval is about ±14 points. Only large gaps
mean anything. The output is therefore a failure breakdown and a cost table, not
a ranking, and the post does not name a winner.

### Cost

Model: `gemini-3.1-flash-lite`, at $0.25 per million input tokens and $1.50 per
million output tokens (checked October 2026). These figures are extrapolated from
the call ledgers in the notebooks and could be wrong by a factor of two, which is
what the pilot is for.

| Arm | Per question, 10 sessions |
|---|---|
| Full context, plain retrieval, answers and judge | about $0.01 |
| Mem0 | about $0.02 |
| Textual memory | about $0.02 |
| Honcho-style | about $0.04 |
| Letta-style | about $0.06 |
| Graphiti | about $0.30 |
| **All arms** | **about $0.45** |

| Run | Estimated cost |
|---|---|
| Pilot, 5 questions | about $2 |
| Main, 50 questions | about $22 |
| Full history, 25 questions, cheap arms | about $5 |
| **Total** | **about $30** |

Ways to spend less: 30 questions in the main run brings it to about $13, and
there is a realistic floor of about $10. Graphiti is roughly three quarters of
the bill. Reduce the number of questions before changing how Graphiti ingests,
because altering its ingestion means measuring a different system.

Things that will change these numbers:

- Graphiti's cost grows with the size of the graph.
- All four notebooks run on Gemini (`gemini-3.1-flash-lite`), on a free tier
  that allows 15 requests a minute. The experiment will need a paid tier or a
  different route to the model.
- Cache every model call on disk, keyed on the full request, so a re-run after a
  bug fix costs nothing for the arms that did not change.

### What to measure

For every question and arm, record enough to say **why** an answer was wrong.

| Measure | What it tells you |
|---|---|
| Answer accuracy | The end result |
| New value stored? | Write-path loss: the update was never extracted |
| Old value still stored as current? | Conflict resolution failed |
| New value delivered to the prompt? | Read-path loss: stored but not retrieved |
| Old value delivered to the prompt? | Stale retrieval |
| Stale-answer rate | The model answered with the old value |
| Model calls and tokens, at write and at read | Cost |

The stored/delivered split matters most. A fact can be written correctly and
still never reach the answering model, and a single "recall" number hides which
of the two failed.

Two figures to add if budget allows, both taken from
[the original idea note](../history/g91-original-idea.md):

- accuracy by revision status (old value versus new value asked for);
- accuracy as the history grows from 10 to 48 sessions, for the cheap arms.

### Rules for the experiment

These come from mistakes already made once elsewhere.

- **Pass the session timestamps into every system.** A system that tracks what
  changed over time cannot do so if every message is stamped with the time it was
  ingested. Check after ingestion that stored dates are the conversation's dates.
- **Run a control row through the same scoring code.** A known result that comes
  back as zero, or several configurations that come back identical, means the
  pipeline is broken, not that the systems are.
- **Never let a truncated or empty model reply count as an answer.** Detect it and
  retry.
- **Tune on questions that are not in the reported set.** Use the pilot questions
  or a separate handful, and keep the 50 untouched.
- **Give each system a fair configuration.** Record every setting. Where a default
  was changed, say why.
- **Report the baselines first.** If full context wins, that is the finding.

## Stages

1. **Clean the copied notebooks.** Done. The notebooks stand alone, run on one
   model set in `notebooks/config.py`, and are committed as `.ipynb` with their
   outputs so a reader can follow along without an API key.
2. **Add the three missing arms as notebooks or small modules:** full context,
   plain retrieval, textual memory. Run each on the same three sessions.
3. **Make the labels honest.** The Honcho, Letta and Zep/Graphiti notebooks drive
   the vendors' prompts from local code and do not run the vendors' servers or
   libraries. Either run the real
   systems in the experiment or label the arms "Honcho-style" and "Letta-style"
   everywhere.
4. **Build the experiment under `src/`:** a loader for LongMemEval, the
   trimming with a fixed seed, one adapter per arm behind a common interface
   (ingest a session with its timestamp, answer a question at a date), the judge,
   the call cache and the cost ledger.
5. **Pilot** on 5 questions. Replace the cost table above with measured numbers
   and fix the size of the main run.
6. **Main run and full-history run.**
7. **Error analysis.** Read the failures and sort them into the measures above.
   Pick one worked example per system.
8. **Write the post.**
9. **Finish the repository:** README results section, committed result files,
   pinned versions.

Stages 1 to 3 need almost no API spend. Stages 5 and 6 are where the budget goes.

## The post

- One post, not one per system. Cut most of the notebook material; the notebooks
  stay in the repository for readers who want it.
- Open with a failure that surprises, not with architecture. A candidate: the
  temporal graph leaves a superseded fact open, at roughly ten times the model
  calls of the simpler system.
- Show real prompts and real stored records.
- Give each system one thing it does well and one failure.
- Put the full-context baseline in the first results table.
- End with a decision guide: when a text file is enough, when to add retrieval,
  when a graph earns its cost.
- State the limits: trimmed history, one question type, 50 questions, one model.
- Do not name a winner.

## Open decisions

- Whether to run the real Honcho, Letta and Graphiti in the experiment or keep
  the local re-implementations with honest labels.
- Whether to add the 30 single-session-preference questions. They are closer to
  personalisation, but they have one evidence session and no revision.
- The final repository name and whether it is public from the start.
