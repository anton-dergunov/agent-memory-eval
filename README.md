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

## Systems covered

What sets the systems apart is one question: who decides what gets written to
memory?

| System | Who writes | What is run |
|---|---|---|
| [Mem0](https://anton-dergunov.github.io/agent-memory-eval/notebooks/mem0.html) | An extraction pipeline | the real library |
| [Zep / Graphiti](https://anton-dergunov.github.io/agent-memory-eval/notebooks/zep-graphiti.html) | A pipeline, into a dated graph | Graphiti's prompts, driven by local code |
| [Letta (MemGPT)](https://anton-dergunov.github.io/agent-memory-eval/notebooks/letta.html) | The agent itself | Letta's prompts and tool descriptions, driven by local code |
| [Honcho](https://anton-dergunov.github.io/agent-memory-eval/notebooks/honcho.html) | A background reasoner | our prompts, written from Honcho's published definitions |
| [Textual memory](https://anton-dergunov.github.io/agent-memory-eval/notebooks/textual.html) | A background rewriter of one text file | our code, about 50 lines; the same prompt as the experiment |
| Full context; plain retrieval over raw turns | Nobody | our code, in the experiment only |

Three of the five notebooks are re-implementations made so that every step can
be read. Each notebook says at the top what it takes from the original system
and what it leaves out. The experiment runs the real systems: Mem0 2.2.1,
Graphiti 0.31.1 on Neo4j, Honcho v3.3.0 and Letta 0.16.8, all on the same
model.

The notebooks are in [notebooks/](notebooks/). The system names above link to
their rendered pages, which read better on a tablet or phone than GitHub's
notebook view.

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
tokens), `gemini-3.1-flash-lite` for every model call the systems and the
answerer make, `gemini-3.1-pro-preview` as judge. Not comparable to published
LongMemEval results: each history is cut from about 48 sessions to 10, only
one of the benchmark's question types is used (67 of its 500 questions), and
the answering and judging models differ from the paper's.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/figures/results-dark.svg">
  <img alt="Accuracy with its 95% interval, and the cost of building the memory and answering, for each arm: accuracy sits between 82% and 97% for all but Letta at its defaults, while cost ranges from $0.002 to $0.640 per question" src="docs/figures/results.svg">
</picture>

| Arm | Accuracy | 95% interval | Cost to build and answer | Model calls to write |
|---|--:|---|--:|--:|
| Full context | 90% | 80%–95% | $0.007 | 0 |
| Retrieval (BM25 over raw turns) | 97% | 90%–99% | $0.002 | 0 |
| Textual memory | 93% | 84%–97% | $0.022 | 10 |
| Mem0 | 84% | 73%–91% | $0.039 | 10 |
| Honcho, dialectic chat | 87% | 76%–93% | $0.029 | 38 |
| Honcho, representation | 93% | 84%–97% | $0.028 | 38 |
| Graphiti | 82% | 71%–89% | $0.640 | 720 |
| Letta | 69% | 57%–78% | $0.132 | 81 |
| Letta, persona that keeps facts current | 90% | 80%–95% | $0.152 | 88 |

On a history this short most memory systems lose little against reading the
whole thing, and what separates them is cost: Graphiti spends 30 times what
textual memory spends. At its defaults Letta trails, because its agent often
notices a revision without writing it down and its search rarely finds the
message again. Three lines in its persona block, asking it to date facts,
update them and search with short words, bring it to 90%.

Why keep a memory at all, then? Because the two pay at different times. A
memory system pays once, to build its memory, and then each answer reads far
less than the whole history. Full context pays for the whole history on every
question, and a history only grows.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/figures/answering-dark.svg">
  <img alt="Once the memory is built, the tokens each answer reads and what it costs: full context reads about 25,000 tokens for $0.0065 per question, most memory systems read 500 to 1,500 tokens for under $0.001" src="docs/figures/answering.svg">
</picture>

The analysis, the failure breakdown and the
full-history run are in [docs/experiment-results.md](docs/experiment-results.md),
with the tables in [docs/findings/](docs/findings/); how to run it is in
[docs/experiment.md](docs/experiment.md).

## Running the notebooks

```bash
uv sync --python 3.12
uv run python -m ipykernel install --user --name agent-memory-eval --display-name agent-memory-eval
```

`uv sync` creates `.venv` with the versions pinned in `uv.lock`; add
`--extra experiment` if the same environment should also run the experiment,
since a plain `uv sync` removes the experiment's packages.

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
`http://<your-mac>.local:8642/`) on the tablet.

## Layout

| Path | Contents |
|---|---|
| [notebooks/](notebooks/) | One notebook per system, `config.py` for the models, `letta_source.py` for fetching Letta's prompts |
| [src/memeval/](src/memeval/) | The LongMemEval experiment: data, model calls, one module per arm, judge, report |
| [infra/](infra/) | Scripts that start the Honcho, Neo4j and Letta servers |
| [results/](results/) | Every result of the pilot, main and full-history runs, with the call ledgers |
| [docs/](docs/) | [experiment.md](docs/experiment.md) (how it runs), [experiment-results.md](docs/experiment-results.md) (what it found) |
