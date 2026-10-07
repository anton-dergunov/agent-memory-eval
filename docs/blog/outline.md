# Blog post: outline and collected material

A skeleton for the post, with the material gathered so far placed under the
section where it will be used. Nothing here is final prose. The experiment and
its plan are in [../tasks/blog-post-plan.md](../tasks/blog-post-plan.md).

Items marked **[verify]** come from third-party write-ups or from memory and
must be checked against a primary source before they go into the post.

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
- Then the question the post answers: what does each system actually do with a
  conversation, and what does that cost?

### 2. The running example

- Three hand-written sessions: a preference is stated, reversed, then asked
  about. The third session can only be answered correctly from the updated
  preference.
- Why this example and not `add("I like pizza")` then `search("food")`: the
  vendor demo shows the API and none of the mechanism.

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
history, one question type, about 50 questions, one model, and no comparison
with published LongMemEval results.

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
