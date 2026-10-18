#!/usr/bin/env bash
# Stop the Honcho API and deriver started by up.sh. The databases keep running.
dir="$(cd "$(dirname "$0")/../.." && pwd)/vendor/honcho"
for name in deriver api; do
  pid_file="$dir/logs/$name.pid"
  [ -f "$pid_file" ] && kill "$(cat "$pid_file")" 2>/dev/null && rm -f "$pid_file"
done
exit 0
