# Historical note: the original project idea (G91)

> **Status: historical.** This is the idea note this project grew out of, kept
> unchanged below for reference. It was written before any of the work was done.
> The current plan is [docs/tasks/blog-post-plan.md](../tasks/blog-post-plan.md),
> which supersedes it. The assessment that follows says which parts of the note
> still hold and which do not.

## How the note reads today

**Right, and worth keeping**

- Separate what the memory layer returned from what the model answered. In
  practice this needs one more split than the note has: *stored* versus
  *delivered*. A fact can be written correctly and still never reach the prompt.
- Report a stale-answer rate explicitly.
- Treat a rolling summary as the baseline that is hard to beat. PersonaMem-v3
  later showed exactly this: its plain "Textual Memory" beats Mem0 on tracking
  preference changes.
- Run no-memory and full-context arms from the first day.

**Still ahead of the current plan**

- Accuracy by memory age and by revision status.
- Degradation as the history grows 10×. LongMemEval's history length is
  configurable, so this is cheap for the inexpensive arms.
- Small implementations behind one interface, which isolate the architecture from
  vendor engineering.
- A decision guide as the ending ("summary until X, vectors until Y, graph when
  Z").

**Wrong or dated**

- It treats memory as fact recall. The larger problem is how a retrieved fact is
  *used*: over-personalisation, privacy leaks and telegraphing ("since you like
  X") all rise when memory is added, and perfect memory content does not fix
  them. The note has no metric for any of this.
- LoCoMo is a poor benchmark choice: its conversations fit in a context window, an
  independent audit found 6.4% of its answer key wrong, and it has few real
  revisions. The "revised in between" stress the note wants is LongMemEval's
  knowledge-update slice.
- "Controlled comparisons are rare" is no longer true. Comparisons are everywhere;
  call-by-call tracing of the mechanism is what is rare.
- "The graph should shine at revision" did not survive contact: the Graphiti
  notebook shows superseded facts that are silently left open, at many times the
  model calls of Mem0.
- Full context is not an oracle. It degrades with length.
- The taxonomy has no agent-edited memory (MemGPT is cited but is not an arm) and
  no background derivation (Honcho). Consolidation is treated as an optional
  add-on, when in Mem0 and Graphiti it is the write path itself.
- "Match effort across arms" is not fairness for vendor systems. An untuned
  configuration measures the setup, not the system.
- The scope (three implementations, three task suites, a synthetic-life generator
  and TextWorld in 3–5 part-time weeks) is several times too large. The generator
  alone is a benchmark project.

---

## The original note, unchanged

# G91 — Agent memory systems comparison 🧪📄

**One-liner:** Implement three memory architectures for LLM agents —
scratchpad/summary, episodic vector store, knowledge-graph memory — and
compare them on long-horizon tasks where memory actually decides the outcome.

**Why / gap:** Memory is the least-solved layer of the agent stack and a
constant architecture debate; implementations are plentiful, controlled
comparisons rare. Your retrieval depth makes the episodic arm strong and the
comparison credible — retrieval-vs-structure is a question you're unusually
qualified to referee.

**Effort:** 3–5 weeks part-time. **Compute:** API/local model budget;
embedding infra you already have.

## Goals

1. **Three memories, one interface** (`remember(event)`, `recall(query,
   state)`, `consolidate()`):
   (a) *rolling summary/scratchpad* — recursive summarisation into a bounded
   working document (the cheap baseline that's embarrassingly hard to beat);
   (b) *episodic vector memory* — chunked event store, hybrid retrieval,
   recency/importance-weighted scoring (generative-agents style);
   (c) *knowledge-graph memory* — entity/relation extraction into a typed
   graph with temporal edges (facts can change — invalidation matters),
   recall = subgraph retrieval + verbalisation.
2. **Task suites where memory is load-bearing:**
   - long-conversation QA (LoCoMo-style: facts dropped in session 3, asked
     in session 30, some *revised* in between — the update/invalidations
     stress);
   - a longitudinal assistant simulation: 100 simulated "days" of your
     org-mode/task life (generate from your actual patterns) with queries
     mixing recent, old, and superseded facts;
   - an episodic-recall game (TextWorld exploration revisited later —
     bridges F79).
3. **The measurements:** answer accuracy by memory age & revision status
   (the killer breakdown), recall precision of the memory layer itself
   (retrieved context contains the needed fact? — separates memory failure
   from reasoning failure), token cost per interaction, latency, and
   degradation curve as history grows 10×.

## Plan

1. **Week 1 — interface + baselines:** full-context (oracle, until it
   overflows) and no-memory (floor); the evaluation harness with per-fact
   provenance tracking (each Q labelled with which event answers it —
   design the data so failure attribution is mechanical).
2. **Week 2 — the three implementations** (time-boxed: resist making each
   perfect; match effort across arms — fairness is the methodology).
3. **Week 3 — task suites + main runs;** the age × revision breakdown.
4. **Week 4 — consolidation experiments:** does periodic consolidation
   (summarise/merge/forget) help each architecture? (The sleep metaphor,
   tested.)
5. **Week 5 — write-up 📄** + decision guidance ("scratchpad until X,
   vectors until Y, graphs when Z").

## Data / environment

- LoCoMo benchmark (long conversations); your synthetic assistant-life
  generator (release it — the reusable contribution); TextWorld.
- Embeddings/retrieval from your existing stack; small LLM for extraction.

## Techniques to try

- Fact-revision handling per architecture (the graph should shine here —
  verify); measure *stale-answer rate* explicitly.
- Importance scoring at write-time (generative-agents' trick) vs uniform —
  ablate.
- Memory-content audits: sample recalls, judge relevance (H-group hygiene)
  — memory precision as a first-class metric.
- Hybrid arm (episodic + graph for entities) if the pure arms show
  complementary failures.

## Evaluation / definition of done

- The accuracy-by-age-and-revision figure across architectures; the
  cost/latency table; degradation curves at 10× history.
- Memory-layer recall separated from end-to-end accuracy in all reporting.
- Decision-guide post; generator released; qa/ card ("design agent memory"
  — a rising system-design interview question).

## Literature

- Park et al., *Generative Agents* (2023) — episodic memory + importance.
- Packer et al., *MemGPT* (2023) — paging/self-managed memory.
- Maharana et al., *LoCoMo: Evaluating Very Long-Term Conversational Memory*
  (2024) — the benchmark.
- Zep/Graphiti's temporal-KG memory write-ups (2024–25) — the graph arm's
  prior art.
- Anthropic/OpenAI context-management engineering posts (compaction,
  memory tools) — current practice.

## Deliverables

Memory library (three backends, one interface), synthetic-life generator,
comparison study 📄, decision-guide post, reuse in G83/G87/E69.

## Stretch

- Plug the winning memory into your real org-mode assistant (O191/G-group)
  — the dogfooding leg with actual longitudinal data (your life).
- Learned memory controller: small model decides store/skip/consolidate
  (bandit-flavoured — D-group crossover).
