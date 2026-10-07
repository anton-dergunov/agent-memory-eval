# agent-memory-eval

How LLM agent memory systems actually work, traced call by call, and what that
costs them on a real benchmark.

Most comparisons of agent memory systems are either feature tables or vendor
benchmark results. This repository takes a third route. It runs the same short
conversation, in which a user changes their mind, through each system with every
model call shown, so you can see what was extracted, what was overwritten, what
was retrieved, and how many calls it took. It then checks the same behaviour at
a larger scale on the knowledge-update questions of
[LongMemEval](https://arxiv.org/abs/2410.10813).

**Status: work in progress.** The notebooks run today. The benchmark experiment
and the write-up are planned in
[docs/tasks/blog-post-plan.md](docs/tasks/blog-post-plan.md).

## Systems covered

The systems are grouped by one question: who decides what gets written to
memory?

| Who writes | System | Notebook | What is run |
|---|---|---|---|
| An extraction pipeline | Mem0 | [mem0](notebooks/mem0.ipynb) | the real library |
| A pipeline, into a dated graph | Zep / Graphiti | [zep-graphiti](notebooks/zep-graphiti.ipynb) | Graphiti's prompts, driven by local code |
| The agent itself | Letta (MemGPT) | [letta](notebooks/letta.ipynb) | Letta's prompts and tool descriptions, driven by local code |
| A background reasoner | Honcho | [honcho](notebooks/honcho.ipynb) | our prompts, written from Honcho's published definitions |
| A background rewriter of one text file | Textual memory | planned | |
| Nobody | Full context; plain retrieval over raw turns | planned | |

Three of the four are re-implementations made so that every step can be read.
Each notebook says at the top what it takes from the original system and what it
leaves out.

## What each notebook shows

Every notebook starts with one screen that explains the idea, with a diagram,
and then uses the same hand-written conversation: two sessions four months
apart and a question in a third. The user states a diet in the first session,
reverses it in the second, and introduces two other people with constraints of
their own. The closing question can only be answered correctly from the updated
facts.

1. **Write.** What the system keeps from a conversation and what it drops.
2. **Revise.** What happens to the old fact when a new one contradicts it.
3. **Read.** What a new session gets back, and whether the answer changes.
4. **Cost.** Model calls and tokens for the same two sessions.

## Running the notebooks

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e .
.venv/bin/python -m ipykernel install --user --name agent-memory-eval --display-name agent-memory-eval
```

Put `GEMINI_API_KEY` in a `.env` file at the top of the repository, open a
notebook in VS Code or JupyterLab, and pick the **agent-memory-eval** kernel.
The Zep/Graphiti notebook draws its graphs with Graphviz, which has to be
installed separately (`brew install graphviz`).

The models are set in one place, [notebooks/config.py](notebooks/config.py):
`gemini-3.1-flash-lite` for chat and `gemini-embedding-001` for embeddings. The
free tier of the Gemini API is enough. It allows 15 chat requests a minute, and
the notebooks wait between calls to stay under that, so the longest one takes
about five minutes.

## How the notebooks are stored

The `.ipynb` is the version in git, with its outputs, because the outputs are
the point: the prose, the code and the results together are what make a notebook
worth reading, and they can be read without an API key.

Each notebook is also paired by [jupytext](https://jupytext.readthedocs.io/)
with a script, `<name>.nb.py`: the same content as plain Python, which is far
easier to diff, to search, and to hand to a coding assistant. That file is
generated and gitignored. The pairing is declared in `jupytext.toml`, so any
clone can recreate it:

```bash
jupytext --sync notebooks/mem0.ipynb
```

VS Code users get both directions as tasks (`.vscode/tasks.json`), each guarded
so that a sync fails loudly instead of overwriting the side that has newer work
in it.

When a script is synced back into a notebook, jupytext keeps the outputs already
there, including on cells whose code changed. Re-run those cells before
committing, or the notebook will show results its code did not produce.

## Reading on a tablet

[lectern](https://github.com/anton-dergunov/lectern) serves the notebooks as
pages laid out for a tablet:

```bash
lectern serve
```

run at the top of the repository, then open the address it prints (for example
`http://<your-mac>.local:8642/`) on the tablet. For the rare time a cell has to
be run from the tablet, `lectern lab notebooks` starts JupyterLab behind its
password.

Every push to `main` also renders the notebooks with lectern and publishes them
to GitHub Pages (`.github/workflows/pages.yml`). Nothing is executed during that
build. To preview it locally:

```bash
lectern build . -o _site --clean && open _site/index.html
```

## Layout

| Path | Contents |
|---|---|
| [notebooks/](notebooks/) | One notebook per system, `config.py` for the models, `letta_source.py` for fetching Letta's prompts |
| `src/` | The LongMemEval experiment, as plain Python (planned) |
| [docs/tasks/](docs/tasks/) | The plan from these notebooks to the finished post |
| [docs/blog/](docs/blog/) | The outline of the post, with the material collected for it |
| [docs/history/](docs/history/) | The original project idea, with notes on how it aged |
