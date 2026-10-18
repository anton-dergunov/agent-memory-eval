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
has run; its results are below and in
[docs/experiment-results.md](docs/experiment-results.md). The write-up is planned
in [docs/tasks/blog-post-plan.md](docs/tasks/blog-post-plan.md).

## Systems covered

The systems are grouped by one question: who decides what gets written to
memory?

| Who writes | System | Notebook | What is run |
|---|---|---|---|
| An extraction pipeline | Mem0 | [mem0](notebooks/mem0.ipynb) | the real library |
| A pipeline, into a dated graph | Zep / Graphiti | [zep-graphiti](notebooks/zep-graphiti.ipynb) | Graphiti's prompts, driven by local code |
| The agent itself | Letta (MemGPT) | [letta](notebooks/letta.ipynb) | Letta's prompts and tool descriptions, driven by local code |
| A background reasoner | Honcho | [honcho](notebooks/honcho.ipynb) | our prompts, written from Honcho's published definitions |
| A background rewriter of one text file | Textual memory | experiment only | our code, about 50 lines |
| Nobody | Full context; plain retrieval over raw turns | experiment only | our code |

Three of the four notebooks are re-implementations made so that every step can
be read. Each notebook says at the top what it takes from the original system
and what it leaves out. The experiment runs the real systems: Mem0 2.2.1,
Graphiti 0.31.1 on Neo4j, Honcho v3.3.0 and Letta 0.16.8, all on the same
model.

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

## Results on LongMemEval

67 knowledge-update questions, history trimmed to 10 sessions (about 28,000
tokens), `gemini-3.1-flash-lite` in every seat, `gemini-3.1-pro-preview` as
judge. Not comparable to published LongMemEval results.

| Arm | Accuracy | 95% interval | Cost per question | Where wrong answers were lost |
|---|--:|---|--:|---|
| Full context | 90% | 80%–95% | $0.007 | the model answered with the old value (5 of 7) |
| Retrieval (BM25 over raw turns) | 97% | 90%–99% | $0.002 | |
| Textual memory | 93% | 84%–97% | $0.022 | |
| Mem0 | 84% | 73%–91% | $0.040 | update never stored (6 of 11) |
| Honcho, dialectic chat | 87% | 76%–93% | $0.030 | |
| Honcho, representation | 93% | 84%–97% | $0.028 | |
| Graphiti | 18% | 11%–29% | $0.238 | update never stored (45 of 55) |
| Letta | 58% | 46%–69% | $0.029 | update never stored or never found (22 of 28) |

On a history this short every memory system can only lose to reading the whole
thing, and most lose little. The two that lose a lot lose at write time: the
update never makes it into memory. The analysis, one worked example per system
and the full-history run are in
[docs/experiment-results.md](docs/experiment-results.md); how to run it is in
[docs/experiment.md](docs/experiment.md).

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
| [src/memeval/](src/memeval/) | The LongMemEval experiment: data, model calls, one module per arm, judge, report |
| [infra/](infra/) | Scripts that start the Honcho, Neo4j and Letta servers |
| [results/](results/) | Every result of the pilot, main and full-history runs, with the call ledgers |
| [docs/](docs/) | [experiment.md](docs/experiment.md) (how it runs), [experiment-results.md](docs/experiment-results.md) (what it found) |
| [docs/tasks/](docs/tasks/) | The plan from these notebooks to the finished post |
| [docs/blog/](docs/blog/) | The outline of the post, with the material collected for it |
| [docs/history/](docs/history/) | The original project idea, with notes on how it aged |
