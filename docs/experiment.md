# The LongMemEval experiment: how to run it

The notebooks run one hand-written conversation through each memory system.
This experiment checks the same behaviour on real data: LongMemEval's
knowledge-update questions, where the user states a fact and later revises it.
The code is in `src/memeval`; results are in `results/`. The design and the
decisions behind it are in [tasks/blog-post-plan.md](tasks/blog-post-plan.md).

## What is compared

| Arm | Who writes memory | What runs | Read path |
|---|---|---|---|
| `full-context` | nobody | the whole trimmed history in the prompt | everything |
| `retrieval` | nobody | BM25 over raw rounds (user turn + reply) | top 10 rounds |
| `textual` | a separate rewrite call after each session | our ~50 lines, after PersonaMem-v3's Textual Memory | the whole profile |
| `mem0` | an extraction pipeline | mem0ai 2.2.1 (real library) | `search()` defaults |
| `honcho-chat` | a background reasoner | Honcho v3.3.0 (real server) | the dialectic agent |
| `honcho-repr` | the same store | the same server | `representation()` retrieval, no model |
| `graphiti` | a pipeline into a dated graph, one episode per message | graphiti-core 0.31.1 on Neo4j 5.26.31 (real library) | `search()` defaults |
| `letta` | the answering agent, with tools, one step per user message | Letta 0.16.8 (real server, its last Python release) | the agent answers itself |
| `letta-persona` | the same agent, with three lines in its persona on keeping facts current | the same | the agent answers itself |

Every system runs on the same models, on Vertex AI:

- `gemini-3.1-flash-lite` for every model call inside every system and for the
  answers;
- `gemini-embedding-001` at 1536 dimensions for every embedding;
- `gemini-3.1-pro-preview` as the judge, with LongMemEval's own
  knowledge-update judge prompt;
- `gemini-3.8-flash` for the probes, and as a second judge on a subset so the
  agreement between judges can be reported.

Systems that call their models themselves (Mem0, Honcho, Letta) reach Vertex
through `memeval.proxy`, an OpenAI-compatible endpoint. Graphiti uses its own
Gemini client, wrapped. Either way every call goes through one disk cache, one
cost ledger and one budget stop, so every arm's cost is measured the same way.

Settings are each library's defaults unless the module says otherwise. Every
change from a default is explained at the top of that arm's module in
`src/memeval/arms/` and listed in each result file under `settings`.

## Data

`data/longmemeval_s_cleaned.json` from the Hugging Face dataset
`xiaowu0162/longmemeval-cleaned` (MIT licence), checked by SHA-256 on load.
The 78 knowledge-update questions minus 6 abstention questions leave 72. With
seed 0 they are split into 5 pilot questions (used for checking and tuning)
and 67 main questions (reported). Each history is trimmed to its two evidence
sessions plus 8 distractor sessions, in date order. The `full` split runs the
first 25 main questions again with all ~48 sessions.

## Running it

Needs Python 3.12+ with [uv](https://docs.astral.sh/uv/), Docker, a Google Cloud
project with Vertex AI, and Application Default Credentials.

```bash
uv sync --python 3.12 --extra experiment
mkdir -p data && curl -L -o data/longmemeval_s_cleaned.json \
  https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/resolve/main/longmemeval_s_cleaned.json
export GOOGLE_CLOUD_PROJECT=<your project>      # and gcloud auth application-default login

infra/honcho/up.sh       # Honcho API + deriver on :8000 (Postgres, Redis in Docker)
infra/graphiti/up.sh     # Neo4j on :7687
infra/letta/up.sh        # Letta server on :8283

uv run python infra/check_arm.py honcho        # smoke-test one arm (a few cents)
scripts/run-split.sh pilot                     # every arm on the pilot, then score and report
scripts/run-split.sh main
ARMS="full-context retrieval textual mem0" scripts/run-split.sh full
```

`MEMEVAL_BUDGET_USD` (default 45) stops every model call once the ledger shows
that much spent. Runs are resumable: finished questions are skipped, and a
repeated model call is served from `.cache/llm`.

- `--shard i/n` builds every n-th question of an arm, so several processes can
  share a slow arm (the Graphiti re-run used five; each Letta process needs its
  own proxy port, `MEMEVAL_LETTA_PROXY_PORT`).
- Every chat request and reply, cache hits included, is appended to
  `.cache/calls/`. `MEMEVAL_CACHE_ONLY=1` replays a finished run from the cache
  and fails on any miss instead of paying, which rebuilds those logs for free;
  `MEMEVAL_RESULTS_DIR` and `MEMEVAL_LEDGER_DIR` send a replay's results and
  ledger elsewhere.
- `python -m memeval.findings` rebuilds the tables behind the write-up
  (`docs/findings/`) from the result files.
- The first main run fed Graphiti 8,000-character episodes and Letta whole
  sessions in one request; both are kept in `results/main/graphiti-chunk` and
  `letta-batch` and can be reproduced with `MEMEVAL_GRAPHITI_EPISODES=chunk`
  and `MEMEVAL_LETTA_INGEST=batch`. `letta-persona` is an arm of its own
  (`LettaPersonaArm`); how it was run is in
  [tasks/letta-persona-rerun.md](tasks/letta-persona-rerun.md).

## What is measured

For every question and arm, `results/<split>/<arm>/<qid>.json` holds the
sessions used, what the system returned (`context`), the answer, everything
the system stored (`dump`), the judge's verdict and the probes:

- **stored**: does the memory hold the new value, the old one, and is the old
  one still presented as current?
- **delivered**: did the new value (and the old one) reach the answering model?
- **stale**: did the answer give the old value?

The old value is read once per question from the first evidence session. The
report turns these into a failure breakdown: update never stored, stored but
not delivered, delivered but answered with the old value, other errors.
Cost is split into write (building the memory), read and answer, from the
ledger in `.cache/ledger`.

The numbers are **not comparable to published LongMemEval results**: the
history is trimmed, there is one question type, and the models differ.
