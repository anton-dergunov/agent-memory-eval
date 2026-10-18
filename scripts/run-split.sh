#!/usr/bin/env bash
# Build every arm on a split, one process per arm in parallel, then score.
#
#   scripts/run-split.sh pilot
#   scripts/run-split.sh main
#   ARMS="full-context retrieval mem0 textual" scripts/run-split.sh full
#
# Needs the servers from infra/*/up.sh. Resumable: re-running skips finished
# questions, and cached model calls cost nothing.
set -uo pipefail
cd "$(dirname "$0")/.."
split="$1"
arms="${ARMS:-full-context retrieval textual mem0 honcho graphiti letta}"
mkdir -p "results/$split/_logs"
pids=()
for arm in $arms; do
  .venv/bin/python -m memeval.run build --split "$split" --arms "$arm" \
    > "results/$split/_logs/$arm.log" 2>&1 &
  pids+=($!)
done
status=0
for pid in "${pids[@]}"; do wait "$pid" || status=1; done
.venv/bin/python -m memeval.run score --split "$split" > "results/$split/_logs/score.log" 2>&1 || status=1
.venv/bin/python -m memeval.run report --split "$split" > "results/$split/report.md" || status=1
cat "results/$split/report.md"
exit $status
