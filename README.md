# agent-memory-eval

How LLM agent memory systems actually work, traced call by call, and what that
costs them on a real benchmark.

Most comparisons of agent memory systems are either feature tables or vendor
benchmark results. This repository takes a third route. It runs the same short
conversation, in which a user changes their mind, through each system with every
model call intercepted, so you can see what was extracted, what was overwritten,
what was retrieved, and how many calls it took. It then checks the same
behaviour at a larger scale on the knowledge-update questions of
[LongMemEval](https://arxiv.org/abs/2410.10813).

**Status: work in progress.** The intuition notebooks run today. The benchmark
experiment and the write-up are planned in
[docs/tasks/blog-post-plan.md](docs/tasks/blog-post-plan.md).

## Systems covered

The systems are grouped by one question: who decides what gets written to
memory?

| Who writes | System | Notebook |
|---|---|---|
| An extraction pipeline | Mem0 | [mem0-intuition](notebooks/mem0-intuition.py) |
| A pipeline, into a dated graph | Zep / Graphiti | [zep-graphiti-intuition](notebooks/zep-graphiti-intuition.py) |
| The agent itself | Letta (MemGPT lineage) | [letta-intuition](notebooks/letta-intuition.py) |
| A background reasoner | Honcho | [neuromancer-intuition](notebooks/neuromancer-intuition.py) |
| A background rewriter of one text file | Textual memory | planned |
| Nobody | Full context; plain retrieval over raw turns | planned |

Two of the notebooks drive the vendor's published prompts and tool definitions
from local code. They do not run the vendor's server: `letta-intuition` and
`neuromancer-intuition` (Honcho). Each notebook says so at the top.

## What each notebook shows

Every notebook uses the same three hand-written sessions. The user states a
preference in the first, reverses it in the second, and asks a question in the
third that only the updated preference answers correctly.

1. **Write.** What the system keeps from a conversation and what it drops.
2. **Revise.** What happens to the old fact when a new one contradicts it.
3. **Read.** What a fresh session gets back, and whether the answer changes.
4. **Cost.** Model calls and tokens for the same two sessions.

## Running the notebooks

```bash
cd notebooks
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e .
.venv/bin/jupyter lab
```

Put `GEMINI_API_KEY` and `OPENAI_API_KEY` in a `.env` file at the repository
root. Each notebook costs a few cents to run. See
[notebooks/README.md](notebooks/README.md) for how the `.py` and `.ipynb` files
are paired.

### Reading on a tablet

The notebooks are saved with their outputs, so they can be read without running
anything. [lectern](https://github.com/anton-dergunov/lectern) serves them as
pages laid out for a tablet:

```bash
lectern serve
```

run in the repository root, then open the address it prints (for example
`http://<your-mac>.local:8642/`) on the tablet. For the rare time a cell has to
be run from the tablet, `lectern lab notebooks` starts JupyterLab behind its
password.

## Layout

| Path | Contents |
|---|---|
| [notebooks/](notebooks/) | One intuition notebook per system |
| `experiments/` | The LongMemEval experiment, as plain Python (planned) |
| [docs/tasks/](docs/tasks/) | The plan from these notebooks to the finished post |
| [docs/blog/](docs/blog/) | The outline of the post, with the material collected for it |
| [docs/history/](docs/history/) | The original project idea, with notes on how it aged |
