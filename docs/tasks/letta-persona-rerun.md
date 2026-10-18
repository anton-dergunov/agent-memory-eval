# Task: re-run Letta with a persona that keeps facts current

## Why

[findings/letta.md](../findings/letta.md) traces Letta's 21 wrong answers to a
chain of three failures:

1. At the message that carries a revision, the agent recorded the new value in
   only 31 of 64 questions. In 18 more it named the new value in its own reply
   and still did not write it down.
2. Its memory lines carry no dates, so "recently hit 500 followers" reads the
   same months later.
3. It searches past messages with paraphrases, but the self-hosted server's
   `conversation_search` is a literal substring match returning the five
   newest hits. Most of its searches came back empty.

The agent was told nothing about any of this. Its persona was Letta's blank
starter text. Textual memory's prompt, by contrast, has an explicit rule for
keeping the earlier value. The persona block is the part of Letta its users
are expected to write, so this run changes only that block.

## What changes

A new arm, `letta-persona` (`LettaPersonaArm` in `src/memeval/arms/letta.py`).
It is the `letta` arm with `PERSONA_INSTRUCTED` as the persona: the starter
text plus three lines, one per failure above. These are:

- write the message's date on every fact saved;
- when a value changes, even in passing, update the line with `memory_replace`
  and keep the earlier value and its date;
- search with one or two distinctive words, because the search matches word
  for word.

Everything else is identical: the model (`gemini-3.1-flash-lite`), the
temperature (Letta's default, 1.0), the server version and one agent step per
user message. Results go to `results/main/letta-persona/`, a row of their own;
`letta` stays as it is.

**What to judge it by.** Accuracy on 67 questions has an interval of about
±10 points, and at temperature 1.0 two runs of the same agent churn (the last
re-run gained 16 answers and lost 9). The sharper measure is in the logged
calls: how often the agent writes the new value at the revision message, which
was 31 of 64 before.

## Cost and time

| | questions | USD (estimate) | wall time |
|---|--:|--:|---|
| pilot | 3 | ~0.45 | ~20 min |
| the rest | 64 | ~9 | ~2.5 h in 3 shards (~7 h in one process) |

Nothing from the previous Letta run can be replayed from the cache. Every
request carries the agent id, the conversation id and a timestamp, so every
call is new. The estimate is the last run's cost ($8.70 to write, $0.17 to
read, $0.40 to probe and judge, for 67 questions). The persona may make the
agent edit more often, which costs somewhat more. The pilot is not extra:
`build` skips questions whose result file exists, so the full run builds only
the remaining 64.

The budget stop counts everything in `.cache/ledger`, about $99 so far. Set
`MEMEVAL_BUDGET_USD` to that plus a margin: 101 for the pilot, 115 for the
full run. A stopped run loses nothing; raise the budget and rerun the same
command.

## What it needs on a laptop

- **Docker Desktop, running.** The Letta server's Postgres (with pgvector)
  runs in a container.
- **The experiment's Python packages**, as in [experiment.md](../experiment.md):
  `uv pip install -e ".[experiment]"`. The Letta client (`letta-client==1.11.0`)
  is the one the run cannot do without.
- **Vertex credentials:** `gcloud auth application-default login`, and
  `export GOOGLE_CLOUD_PROJECT=<the project billed for the earlier runs>`.
- **The Letta server.** `infra/letta/up.sh` installs it into `vendor/letta` on
  the first run (a Python 3.12 venv and a shallow clone of the 0.16.8 source,
  about 1–2 GB, a few minutes), then starts it on :8283.

Load is light: the run waits on the model API almost all the time. Memory is
the one thing to watch on a 16 GB machine. Each build process loads the
277 MB dataset (about 1 GB in Python), the Letta server takes about 1 GB, and
Docker's VM takes its own allocation. With three shards that is roughly
6–7 GB, which fits. Use two shards if the machine is also busy with other
work. Disk: the call log for one Letta run is about 110 MB. The machine must
stay awake and online, so run under `caffeinate -i`, plugged in, lid open.

## Commands

From the repository root, in one terminal:

```bash
export GOOGLE_CLOUD_PROJECT=<project>
infra/letta/up.sh                          # "Letta is up on :8283"
mkdir -p results/main/_logs
```

### 1. Pilot: three revisions the agent noticed but did not write

`06db6396` (painting projects, 4 → 5), `1cea1afa` (Instagram followers,
500 → 600), `cc5ded98` (daily coding, one hour → two hours):

```bash
MEMEVAL_BUDGET_USD=101 caffeinate -i .venv/bin/python -m memeval.run build \
  --split main --arms letta-persona --qids 06db6396 1cea1afa cc5ded98 \
  2>&1 | tee results/main/_logs/letta-persona-pilot.log
MEMEVAL_BUDGET_USD=101 .venv/bin/python -m memeval.run score --split main --arms letta-persona
```

Compare with the previous run:

```bash
.venv/bin/python - <<'EOF'
import json
for q in ["06db6396", "1cea1afa", "cc5ded98"]:
    old, new = (json.load(open(f"results/main/{a}/{q}.json")) for a in ("letta", "letta-persona"))
    print(f"== {q}  {old['reference']!r}  letta: {old['judge']['correct']}  letta-persona: {new['judge']['correct']}")
    print(new["dump"].split("<human>")[-1][:1500], "\n-> ", new["answer"][:300], "\n")
EOF
```

Go on if the `human` block now has the new value with dates, and the dates are
the history's (2023), not the server's (the day of the run): every tool result
Letta returns carries the server's time, and the first pilot's agent dated one
whole history with it. That pilot, before the persona named the bracketed
date, is kept in `results/main/_letta-persona-pilot-v1/`. If the new value is missing,
the persona is not being followed and the full run is not worth $9: stop
there, and bring the pilot back for a look.

### 2. The full run, in three shards

Each shard needs its own proxy port. All three share the one Letta server.

```bash
for i in 1 2 3; do
  MEMEVAL_BUDGET_USD=115 MEMEVAL_LETTA_PROXY_PORT=$((8110 + i)) \
    nohup caffeinate -i .venv/bin/python -m memeval.run build --split main \
    --arms letta-persona --shard $i/3 > results/main/_logs/letta-persona-$i.log 2>&1 &
  sleep 30   # stagger: each process loads the dataset
done
```

**Watch:** `tail -f results/main/_logs/letta-persona-*.log` (one line per
question, with the spend so far), and `ls results/main/letta-persona | wc -l`
for the count, out of 67.

**Resume or restart** (after a crash, a reboot or the budget stop): start the
server again with `infra/letta/up.sh` if it is down, then rerun the same loop.
Finished questions are skipped. A question that fails is retried on the next
run.

**`184da446`** will most likely fail every time: in the previous run, Vertex's
content filter stopped the build at the same message four times. After one
retry, record it the way the previous run did, as a wrong answer with no reply:

```bash
.venv/bin/python - <<'EOF'
import json
r = json.load(open("results/main/letta/184da446.json"))
r["arm"] = "letta-persona"
json.dump(r, open("results/main/letta-persona/184da446.json", "w"), indent=1, ensure_ascii=False)
EOF
```

### 3. Score and rebuild the tables

```bash
MEMEVAL_BUDGET_USD=115 .venv/bin/python -m memeval.run score --split main --arms letta-persona
.venv/bin/python -m memeval.findings     # docs/findings/tables.md and failures.md
infra/letta/up.sh --reset                # optional: discard the agents afterwards
```

`memeval.findings` rewrites `results/main/ledger.jsonl` from `.cache/ledger`,
which holds every call of the experiment, so the cost columns stay complete.

## Afterwards (in a new Claude Code session)

Keep `.cache/calls/` (gitignored): it holds every request and reply of this
run, and the analysis needs it. Point the session at this file and
[findings/letta.md](../findings/letta.md), and ask it to:

1. Classify what the agent did at each revision message, as in letta.md's
   write-side table, and compare it with 31 of 64.
2. List the answers that changed against `letta`, and say for each whether
   the persona explains the change.
3. Add a section on `letta-persona` to letta.md, the row to the results'
   tables, and a line on it to experiment-results.md.

## Running it in Claude Code in the cloud instead

This is possible (the original runs were done that way), but it needs more
setup than running it locally:

- The cloud environment needs `GCP_ADC_JSON` (the credentials JSON, read by
  `memeval.config.ensure_credentials`) and `GOOGLE_CLOUD_PROJECT` as
  secrets, Docker (`dockerd`), and the dataset downloaded as in
  experiment.md.
- `.cache/` is not in the repository, so the cloud ledger starts empty. Set
  `MEMEVAL_BUDGET_USD=15`.
- **Do not run `memeval.findings` or `memeval.run report` there.** With an
  empty ledger they would overwrite `results/main/ledger.jsonl` with this
  run's calls only. Score there if you like. Then bring back
  `results/main/letta-persona/`, `.cache/ledger/calls-*.jsonl` and
  `.cache/calls/calls-*.jsonl`, copy the two ledger folders into the local
  `.cache/`, and run `memeval.findings` locally.
