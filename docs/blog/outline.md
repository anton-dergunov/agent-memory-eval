# Blog post: outline and collected material

A skeleton for the post, with the material gathered so far placed under the
section where it will be used. Nothing here is final prose. The experiment and
its plan are in [../tasks/blog-post-plan.md](../tasks/blog-post-plan.md).

Items marked **[verify]** come from third-party write-ups or from memory and
must be checked against a primary source before they go into the post.

Two kinds of numbers were added on 7 October 2026:

- **From the notebooks.** Copied from the executed outputs of the four notebooks
  in [notebooks/](../../notebooks/). They are one run of one small model
  (`gemini-3.1-flash-lite`) on one hand-written conversation. Re-running a
  notebook can change them.
- **Published figures.** Taken from the author's reading notes on the papers,
  each with the paper, page and table. Open the paper and confirm each one
  before it goes into the post. They are marked **[paper]**.

## Working thesis

Agent memory systems differ on two choices: **who writes the memory**, and
**whether the read path inserts everything or selects**. Most of what a system
does well or badly, and most of what it costs, follows from those two choices.
Running one conversation through each system, with every model call visible,
shows this more clearly than a benchmark table does.

## Structure

### 1. Opening: a failure

Open with one concrete, surprising result, before any architecture.

- Candidate: the user changes their mind, and the temporal graph closes the old
  fact correctly. Then its default search returns the closed fact and not the one
  that replaced it, having spent eighteen times the model calls of the simpler
  system (36 against 2 in the notebooks).
- Alternate: the user states a life-threatening peanut allergy, and the graph
  system stores nothing about it, because its entity prompt asks for things that
  "could have their own Wikipedia article" and a fact needs two entities to
  exist (Zep/Graphiti notebook, section 1).
- Alternate: an agent with no tool for writing memory tells the user "I have
  updated my records", then gives no reply at all on the next three turns while
  it searches for its own memory block (Letta notebook, section 5).
- Alternate: one hypothesis from the background reasoner says the user started
  eating fish in order to make a dinner with his sister easier to book. Nobody
  said that (Honcho notebook, section 6).
- Then the question the post answers: what does each system actually do with a
  conversation, and what does that cost?

### 2. The running example

- Three hand-written sessions: a preference is stated, reversed, then asked
  about. The third session can only be answered correctly from the updated
  preference.
- Why this example and not `add("I like pizza")` then `search("food")`: the
  vendor demo shows the API and none of the mechanism.
- The conversation as the notebooks now have it. Session 1 (March): planning a
  dinner for a sister's visit; strictly vegetarian for eight years; a severe
  peanut allergy; likes Indian food and paneer; about 40 euros a head. Session 2
  (July): pescatarian now, not vegetarian; moved to Kreuzberg in May; the sister
  is Lena and she is bringing her partner Jonas; Lena can't eat shellfish and
  Jonas is coeliac. Question (September): "My sister and her partner are in town
  tonight. Book the three of us somewhere for dinner — you know what we can and
  can't eat."
- A correct answer needs six things: pescatarian and no longer vegetarian, no
  peanuts, no shellfish for Lena, no gluten for Jonas, a liking for Indian food,
  somewhere near Kreuzberg.
- Why the sister and her partner were added. The question says "my sister and
  her partner" and never says Lena, Jonas, shellfish or gluten. That gives one
  fact (Jonas is coeliac) that shares no words with the question and can only be
  reached through two links. Without it nothing in the example needs a graph.
- The reversal tests updating. The two guests test retrieval. Keep them apart
  when explaining results.

### 3. The map: two axes

The organising table for the whole post.

| Who writes | Read path: insert everything | Read path: select |
|---|---|---|
| Nobody | Full context | Plain retrieval over raw turns; search tools over past chats |
| An extraction pipeline | | Mem0; Zep/Graphiti |
| The answering agent | Letta's core blocks; ChatGPT saved memories | Letta's archival store; Claude's memory tool |
| A background process | Textual memory; Mastra; ChatGPT's chat-history summary | Honcho |

Points to make:

- All of these are one broad family: text is extracted at write time, stored
  outside the model, and put into the prompt at read time.
- "Text file" does not always mean "no retrieval". The defining choice is
  whether the read path inserts everything or selects.
- What is left out, and why: memory in the model's weights (per-user
  fine-tuning) is research-stage, and procedural memory (learned skills, prompt
  optimisation) is a different topic.

### 4. One section per system

Each section has the same four parts: write, revise, read, cost. Each ends with
one thing the system does well and one failure, with the real prompt or stored
record shown.

| System | The idea it represents | Why it is included |
|---|---|---|
| Mem0 | A pipeline extracts short facts into a vector store and updates them on conflict | The simplest complete design, and the easiest to reproduce |
| Zep/Graphiti | A pipeline writes facts as dated edges in a graph and closes superseded ones | The only one that models time explicitly |
| Letta (MemGPT lineage) | The answering agent edits its own always-in-context memory through tool calls | The agent-managed design; also shows moving the write to a background agent |
| Honcho | A background reasoner derives typed conclusions; a query agent reads them back | The only one that stores inferences, not just statements |
| Textual memory | A separate call rewrites one text profile under a token cap | The baseline to beat, and what consumer products mostly ship |
| Full context, plain retrieval | Nothing is written | The floor and the reference for every cost |

Notes for these sections:

- **Honcho, Letta and Zep/Graphiti are re-implementations.** The notebooks drive the vendors'
  published prompts and tool definitions from local code. Say so plainly, or run
  the real servers.
- **Textual memory versus Letta.** Same family, different writer. In Letta the
  answering agent edits blocks during the turn. In textual memory a separate call
  rewrites the whole file between sessions. PersonaMem-v3's version is one
  profile under four headings, rewritten once per day of history, capped at 4,096
  tokens. In that paper it beats Mem0 on tracking preference changes, 79.9%
  against 56.9%.
- **Why not more systems.** Cognee sits in the same quadrant as Graphiti and
  targets document knowledge. A seventh or eighth vendor would make this a list.
- **Ancestors, one paragraph at most [verify]:** Generative Agents (retrieval
  scored by recency, importance and relevance, plus reflection) and MemGPT. The
  background reflection in Honcho and in Letta's sleep-time agent descends from
  the first.

#### Material from the notebook runs

**Which needed facts reached the final answer**

| System, as run | Peanuts | Shellfish (Lena) | Gluten (Jonas) | Diet | Kreuzberg |
|---|---|---|---|---|---|
| Mem0, all nine stored facts handed over | yes | yes | yes | not stated; the stale line was not acted on | yes |
| Zep/Graphiti, default search | yes | yes | no | no | no |
| Zep/Graphiti, tuned read | yes | yes | yes | "fish is included", from the wrong fact | no |
| Letta, in-line | yes | yes | yes | in the block, not stated in the answer | yes |
| Letta, sleep-time | yes | yes | yes | yes | yes |
| Honcho-style | yes | yes | yes | not stated | yes |

The two systems that hand everything they hold to the model (Letta's block,
Honcho's tagged list) and the one that returned everything because the store was
small (Mem0) did best. The one system that really selected (Zep/Graphiti) did
worst. At this size, selection can only lose. Say so, and say that the picture
changes when the store no longer fits in the prompt.

**Cost for the same two sessions**

| System, as run | Model calls to store two sessions | Notes |
|---|--:|---|
| Mem0 | 2 | one per `add()`, plus 4 embedding calls |
| Zep/Graphiti | 36 | plus 24 embedding calls; about 51,000 tokens read to store 13 facts |
| Letta, in-line | 11 for six user turns | every memory write is a second call before the reply; 13 calls with the question |
| Letta, sleep-time | 34 that the user waits for, 4 in the background | the 34 are nearly all a search loop; a primary that answered in one call per turn would make 6 |
| Honcho-style | 6 | extraction twice, deduction twice, induction, abduction; 7 with the answer |

**Mem0** (real library)

- Stored five facts from session 1 and four from session 2, one model call each.
- The old fact: untouched. This release only adds ("Your sole operation is
  ADD"). The vegetarian line and the line that replaces it sit side by side.
- What saved it: the extractor was shown the old line and wrote the new fact as
  a transition ("transitioned from a strict vegetarian diet to a pescatarian
  diet"), so the model did not have to choose between two flat statements.
- Read: asked for 6 facts and got all 9. `limit` is not a cap in this release.
  The two diet lines ranked last (0.589, 0.588) and the peanut allergy seventh
  (0.612). A real cut at six would have dropped all three.
- Dates: the open-source library resolves "next week" and "a month ago" against
  the day of ingestion. `add(timestamp=...)` is rejected as a hosted-platform
  feature. A history loaded after the fact gets its relative dates wrong.
- Does well: the cheapest write path. Fails: nothing ever revisits a stored
  fact.

**Zep/Graphiti** (Graphiti's prompts, driven by local code, no database)

- With the default entity prompt, the first message yields three entities
  (Anton, Anton's sister, Berlin) and no diet or allergy. Four custom entity
  types (Person, Place, Preference, HealthCondition) fix it. Same message, same
  model, temperature 0.
- The old fact: closed correctly. The model says which stored fact is
  contradicted; ordinary code sets its end date from the new fact's start date.
  "Vegetarian since 2018-03-14" now ends 2026-06-20. Nothing is deleted, and
  "what was true in April?" is a filter.
- The repeated peanut allergy was caught as a duplicate by looking up the same
  pair of nodes. This is one of the two places the graph structure did real
  work.
- Read, default search: returned the closed vegetarian fact (cosine 0.608) and
  not the pescatarian fact that replaced it (0.599), because of a fixed 0.6
  floor. With this embedding model every fact scores between 0.54 and 0.67.
- Entity matching: "my sister Lena" was merged with "Anton's sister". Plain
  "Lena", two messages later, was not: name similarity 0.595 against the same
  kind of 0.6 floor. Her shellfish fact hangs on a second node.
- What the graph buys: "Jonas has coeliac disease" cannot be found by text
  search. A walk sister → Jonas → coeliac finds it in two steps. For facts about
  the user, all one step from the user's node, a table with dates does the same.
- Not used by default: the paper describes full-text, cosine and breadth-first
  search side by side; the library's `search()` uses the first two.
- Assistant turns are ingested too: 9 of the 36 calls, for one fact nobody
  needed.
- Four of the five failures in the run were settings (a prompt, two thresholds,
  a missing date filter), not flaws in the idea of dated edges.
- Does well: keeps history and makes the update explicit. Fails: everything
  exact rests on prompts and thresholds that have to be tuned for the
  application and the embedding model.

**Letta** (Letta's prompts and tool descriptions, driven by a local loop)

- In-line: nothing written after the message that states the allergy;
  everything written one turn later. The default prompt never says when to
  write.
- The old fact: overwritten in place. No search and no contradiction check are
  needed, because the whole block is always in the prompt. No history is kept.
- Stored as written: "started eating fish one month ago", "(8 years)". These
  stay wrong for as long as the line stays.
- To change one line the agent re-sent the whole block, which the tool's own
  description says not to do, and reworded "can't eat shellfish" as "has a
  shellfish allergy".
- Read: the block is in the prompt; there is no retrieval to miss. The agent
  searched recall anyway and doubled the prompt for that turn (about 1,500 to
  3,500 tokens).
- Sleep-time: the background agent wrote a better block (absolute dates) in 4
  calls, and invented a postponement ("originally March 2026, now updated to
  autumn 2026") from two separate visits.
- Sleep-time, primary agent: with its write tools removed it searched recall
  for "human block", "human block value" and so on, hit the step limit, and
  gave no reply on three of seven turns. This is the small model's failure, not
  the design's, and the post should say so.
- Does well: the constraints all fit in 350 to 450 characters that are always
  present, so the final answers were the best of the four. Fails: the write
  policy is whatever the model happens to decide.

**Honcho-style** (our prompts, written from Honcho's published level
definitions)

- Extraction is about the same as Mem0's. The difference is the level tag and
  the list of premises on each row.
- The old fact: marked as replaced by the deduction level, along with the
  conclusion that had been drawn from it ("does not consume meat or fish"). It
  leaves the prompt.
- Because every conclusion lists its premises, what depended on a withdrawn
  fact can be listed exactly.
- The level rule (a premise must rank below its conclusion) is eleven lines of
  code and rejects a certain conclusion drawn from a guess.
- Confidence labels: both patterns had four premises and came back "high",
  against a rule in the prompt that says three to four is "medium".
- Trivia: "Lena is a person" was stored as a deduction.
- The hypothesis level invented a motive (see the alternates in section 1).
- Honcho's own code: only `EXPLICIT` is produced when messages arrive; the
  other levels come from a background "dreamer"; abduction is announced and not
  in the repository **[verify]** against the current repository before
  publishing.
- Does well: the stale fact does not compete with its replacement, whatever
  the wording. Fails: every level reads the whole store, so input grows with
  the profile (the second deduction call read nearly twice the first), and
  nothing limits how much is derived.

**Threads that run across the systems**

- **Fixed thresholds decide outcomes by the third decimal.** 0.599 against
  0.608 for which diet fact is returned; 0.595 for whether two names are one
  person. The constants are tuned for some other embedding model. The Zep
  paper's experiments used BGE-m3 **[paper]** (Zep, experiments section).
- **Storing an update and delivering it are separate problems.** Graphiti
  stored the update correctly and its default search delivered the old fact.
  Mem0 stored it clumsily and delivered both.
- **Relative dates.** Graphiti and the Honcho-style extractor resolve them from
  the message's own date. Mem0's library uses the day of ingestion. Letta's
  default agent stores the phrase as said.
- **Assistant turns.** Graphiti ingests them as messages. Mem0's current prompt
  says it extracts from both sides. Letta's agent is the assistant.

**Published figures to set next to the notebook findings [paper]**

- Mem0's paper describes add, update, delete and do-nothing against the ten
  most similar stored facts (Mem0, p. 3–4). The release in the notebook only
  adds.
- Mem0 against full context in its own paper: 66.88 against 72.90 on LoCoMo,
  with p95 latency of 1.44 s against 17.12 s (Mem0, p. 11, Table 2). Memory
  buys cost, not accuracy, when the history fits.
- Zep on LongMemEval: 71.2% against 60.2% for full context, with 1.6K tokens in
  the prompt instead of 115K (Zep, p. 7, Table 2).
- After facts change, Zep scores 44.4, Cognee 37.8, long context 20.0, Letta
  17.8 and Mem0 15.6 ("Are We Ready For An Agent-Native Memory System?", p. 9,
  Table 2). This is the independent result closest to the notebooks' reversal.
- Against graphs as a default: Zep's temporal F1 on LoCoMo is 0.0295 (A-TMA,
  p. 11, Table 3); graph memory recovers almost none of LoCoMo's distant turns,
  Recall@5 at most 0.005 against 0.573 for a plain store of all turns
  (AgentMemBench, p. 10); Mem0's graph variant adds about 1.5 points over plain
  Mem0 (Mem0, p. 9–10, Table 1).
- Zep's graph holds more than 600K tokens per LoCoMo conversation and new
  memories take hours to become usable, as reported by Mem0's authors (Mem0,
  p. 14). A competitor's measurement; say so.
- Papers use a graph for three different reasons and often conflate them: Zep
  for time, HippoRAG for multi-hop retrieval, A-MEM for a store that
  reorganises itself. The notebook's finding fits this: the handling of time
  needed only the dates, and the graph earned its place on the multi-hop case.
- Extraction is where facts are lost: every system but one recalls under 60% of
  what it should have stored, and more than half of failed updates fail because
  the original fact was never extracted (HaluMem, p. 11, Table 3). The
  notebooks show one mechanism for this: Graphiti's default entity prompt.
- Two camps on what an update should do: mark the old fact as replaced and keep
  it (Zep, Mem0's graph variant, A-TMA) or remove it (Mem0's delete). No paper
  in the notes compares them on one task. The four notebooks cover both camps,
  plus "add only" and "overwrite in place".
- MemGPT's own benchmark is saturated: a full-conversation baseline scores
  94.4%, MemGPT 93.4%, Zep 94.8% (Zep, p. 6, Table 1).

### 5. What the products ship

A short section. None of these can be run as libraries, and what is known comes
from public reverse-engineering and third-party write-ups, not from the vendors.
Say that in the post.

**ChatGPT**

- **Saved memories.** The model calls a tool to store a short fact. All saved
  facts are inserted into every prompt. This is the pure "agent writes, insert
  everything" design.
- **Chat history.** Precomputed summaries of recent conversations and of the user
  are also inserted. Reverse-engineering posts report no vector search over past
  chats.
- **June 2026 [verify].** One write-up says OpenAI rebuilt how the summary is
  produced and named it "Dreaming", which is the background-rewriter design.

**Claude**

- **Chat app.** It can search past conversations through tool calls, which is
  retrieval on demand. Its memory was reported as a summary regenerated daily,
  then, from July 2026 **[verify]**, as individual categorised entries that Claude
  reads and updates during conversations.
- **Claude Code.** `CLAUDE.md` files are loaded whole. Auto memory is a directory
  with a `MEMORY.md` index that is always loaded and topic files that are read
  only when relevant: a small index always in context, with the detail fetched on
  demand.
- **API memory tool.** A file directory that the model views and edits through
  commands, read on demand.

**Mastra's Observational Memory** (open source, TypeScript)

- An Observer compresses messages into dated observations once they pass about
  30,000 tokens. A Reflector merges and prunes observations once they pass about
  40,000.
- No retrieval and no database. The log stays in the prompt, which keeps it
  cacheable.
- It is the most developed version of the textual-memory family. It shares the
  background agent with Honcho, but Honcho does more: it labels conclusions by
  how they were inferred, keeps what each was derived from, stores them for
  retrieval, and answers through a query agent.
- It is as much a context-compression device as a user memory, because its log
  replaces the raw message history.
- Mastra reports 94.87% on LongMemEval with gpt-5-mini. That is the vendor's own
  figure.

The point of the section: ChatGPT is at the "insert everything" end. Claude
combines an always-loaded part with tool-driven lookup. The products have mostly
converged on text, not on vector stores or graphs.

Sources:

- [Manthan Gupta: I Reverse Engineered ChatGPT's Memory System](https://manthanguptaa.in/posts/chatgpt_memory/)
- [Reverse Engineering ChatGPT's Updated Memory System](https://medium.com/@j0lian/reverse-engineering-chatgpts-updated-memory-system-3cb9e82e5d21)
- [OpenAI: Memory and new controls for ChatGPT](https://openai.com/index/memory-and-new-controls-for-chatgpt/)
- [Mem0: ChatGPT Started Dreaming](https://x.com/mem0ai/article/2071990201531118063)
- [Claude's New Memory Entries, Explained](https://www.memorylake.ai/en/blogs/claude-new-memory-entries)
- [Mem0: How Claude Code Memory Actually Works](https://mem0.ai/blog/how-memory-works-in-claude-code)
- [Claude vs ChatGPT vs Gemini Memory](https://blog.memoryplugin.com/claude-vs-chatgpt-vs-gemini-memory/)
- [Mastra: Observational Memory](https://mastra.ai/research/observational-memory)
- [Mastra: Announcing Observational Memory](https://mastra.ai/blog/observational-memory)

Several of these are secondary sources, and two are written by a memory vendor.
Prefer the vendors' own documentation where it exists.

### 6. The experiment

Does the intuition from one short conversation hold on real data?

- LongMemEval, the knowledge-update questions: the user states a fact and later
  revises it.
- Results table, with full context in the first row.
- The failure breakdown: update never stored; old value still stored as current;
  stored but not delivered; delivered but the model answered with the old value.
- The cost table: model calls and tokens per question, at write and at read.
- One worked example per system.
- What trimming the history changed, shown by the full-history run.

All numbers and the design are in the plan. The limits to state: trimmed
history, one question type, 67 questions, one model, and no comparison
with published LongMemEval results.

**Measured** (17 October 2026; tables, worked examples and the full-history run
in [experiment-results.md](../experiment-results.md)):

- Accuracy on 67 questions, 10-session history: full context 90%, retrieval
  97%, textual memory 93%, Mem0 84%, Honcho 87% (dialectic chat) and 93%
  (representation), Graphiti 18%, Letta 58%. Six arms overlap; only Graphiti
  and Letta are clearly apart. Judges agree on 95 of 96.
- The trimmed history is in the regime where full context wins: memory can only
  lose. Plain retrieval over raw turns lost nothing, at a fifth of the tokens.
  Full context's errors are the model answering with the old value although
  the new one is in the prompt.
- Most loss is at write time, as HaluMem would predict: "stored but not
  delivered" is almost empty for every arm; "update never stored" is 45 of
  Graphiti's 55 wrong answers and 22 of Letta's 28.
- Nobody resolves the conflict at write time, and with dates on every item it
  mostly does not matter: the old value is still stored as current in 25 of
  Mem0's stores and 42 of Honcho's, and when both values reach the model with
  dates it picks the newer one (51 of 53 for Honcho's representation).
- Graphiti: about 57 edges from 10 sessions, 0.2 closed as superseded per
  question; the update is an aside and never becomes an edge. 121 model calls
  per question, eight times the next system.
- Letta: the agent left its `human` block empty after 43 of 67 histories and
  answers by `conversation_search`, which on the self-hosted server is a
  literal SQL substring match. Its score is the same with or without a filled
  block.
- Cost per question (system only): full context $0.007, retrieval $0.002,
  textual $0.022, Mem0 $0.040, Honcho $0.030, Letta $0.029, Graphiti $0.238.
- Full history: FULL_HISTORY_SUMMARY

Published findings that bear on the design **[paper]**:

- **Full context is the baseline to beat.** On LongMemEval, histories are about
  115K tokens, and GPT-4o drops from 0.870 with only the relevant sessions to
  0.606 with all of them (LongMemEval, p. 6, Fig. 3). Memory systems beat full
  context there; on LoCoMo, which fits in context, they mostly do not. Trimming
  the history moves the experiment towards the regime where full context wins.
  Report it in the first row and say which regime the trimmed version is in.
- **Rankings do not transfer between papers.** The same Zep is 6 points below
  Mem0 in one paper and 17 above it in another (MemOS, p. 23, Table 3; MIRIX,
  p. 11, Table 2). Raising the number of retrieved items from 10 to 40 adds
  20.4 points on LongMemEval in one study (Memanto, p. 8). Fix the retrieved
  budget across arms and report it.
- **Most loss is at write time.** The failure breakdown in this section
  ("update never stored" first) matches what HaluMem measures. Keep that
  category separate from "stored but not delivered", which is what the Graphiti
  notebook showed.
- **Updating is where systems fail.** Consolidating conflicting facts across
  several hops scores at most 28% for every agent on MemoryAgentBench (p. 8,
  Table 3). The knowledge-update questions are the easy end of this.
- **The answer model is rarely at fault**: 2–7% of failures in DynamicMem
  (p. 12, Fig. 9). If "delivered but answered with the old value" turns out
  large here, check the prompt before blaming the model.
- **Judges vary.** A small judge model gave 85–98 to answers whose token F1 was
  5–15 (SAGE, p. 6, Table 1). Name the judge and spot-check it by hand.
- **Vendor evaluations.** Mem0, Zep, MemOS and MIRIX were each evaluated by the
  company that sells them. This experiment has no vendor, which is worth one
  sentence.

### 7. What memory does not fix

Short, and it is the part most posts omit. Memory benchmarks mostly measure
recall of facts. A second problem is how a recalled fact is used: adding memory
also raises over-personalisation, privacy leaks and telegraphing ("since you
like X"). PersonaMem-v3 measures this as an "over-personalisation tax". Cite the
paper's published numbers only.

### 8. Decision guide

End with something a reader can act on.

- When a text file is enough.
- When to add retrieval.
- When a graph earns its cost.
- When a background reasoner earns its cost.

Fill this in from the results. Do not name a winner.

### 9. Limits and reproduction

- Versions and commits pinned; date of the runs.
- What was re-implemented and what was run as shipped.
- A link to this repository and the cost of reproducing it.
- From the notebooks: Mem0 is the real library. Zep/Graphiti, Letta and Honcho
  are local code around the vendors' prompts (Honcho: prompts written from the
  vendor's definitions). The Graphiti version leaves out entity summaries,
  attributes, communities and the cross-encoder, and uses a small BM25 in place
  of the database's full-text index.
- One model in every seat, `gemini-3.1-flash-lite`, with `gemini-embedding-001`.
  In Letta's design and in Graphiti's entity step the model's judgement is the
  policy, so a stronger model would change those results most.
- One conversation, one run. Temperature 0 made the runs repeatable in
  practice, which is not a guarantee.
- Mem0's stored dates depend on the day the notebook was run.
- The free tier allows 15 requests a minute; the longest notebook takes about
  five minutes.

## Related writing, to read and cite

- Zep, [Is Mem0 Really SOTA in Agent Memory?](https://blog.getzep.com/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/)
- Penfield Labs, [We audited LoCoMo](https://penfieldlabs.substack.com/p/we-audited-locomo-64-of-the-answer)
- Continua, [The LoCoMo "Fair Fight"](https://blog.continua.ai/p/the-locomo-fair-fight)
- CodePointer, [Agent Memory Systems and Knowledge Graphs](https://codepointer.dev/p/agent-memory-systems-and-knowledge):
  the closest existing post. It reads the source code and does not run the
  systems.
- Mem0, [LoCoMo vs. LongMemEval vs. BEAM](https://mem0.ai/blog/ai-memory-benchmarks-in-2026)
- [LongMemEval paper](https://arxiv.org/abs/2410.10813)
- Letta's post on a filesystem agent as a memory baseline **[verify]**

## Writing notes

- One post. Cut most of the notebook material and link to the notebooks.
- Organise by the durable questions (who writes, how contradictions resolve, what
  the read path returns, what it costs), because prompts and versions will date
  within months.
- Show real prompts and real stored records, not diagrams of them.
- Put the baselines first in every table.
