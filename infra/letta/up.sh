#!/usr/bin/env bash
# Start Letta's Python server 0.16.8 (its last release) on :8283, wired to
# memeval.proxy on :8101, with its own Postgres (pgvector) on :5433.
#
#   infra/letta/up.sh           # start (idempotent)
#   infra/letta/up.sh --reset   # discard every agent first
#
# The server's dependencies are resolved as of its release date
# (--exclude-newer), because later releases of its unpinned dependencies no
# longer import. Its database migrations ship in the repository, not the wheel,
# so the tagged source is cloned for them.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
dir="$repo/vendor/letta"
proxy="${MEMEVAL_LETTA_PROXY:-http://127.0.0.1:8101/v1}"
pg=postgresql://postgres:postgres@127.0.0.1:5433/letta
# pgvector 0.8.7 on Postgres 15, what the pg15 tag pointed to on 17-18 Oct 2026.
pg_image=pgvector/pgvector:0.8.7-pg15@sha256:47af0b65960b14f1c6945aa4ccae37836c632e9a6fe0eea9160936e616e5b2e9
mkdir -p "$dir/logs" "$dir/home"

if [ "${1:-}" = "--reset" ]; then docker rm -f memeval-letta-db >/dev/null 2>&1 || true; docker volume rm -f memeval-letta-db >/dev/null; fi
if ! docker ps --format '{{.Names}}' | grep -qx memeval-letta-db; then
  docker rm -f memeval-letta-db >/dev/null 2>&1 || true
  docker run -d --name memeval-letta-db -p 127.0.0.1:5433:5432 \
    -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=letta \
    -v memeval-letta-db:/var/lib/postgresql/data "$pg_image" >/dev/null
fi
for _ in $(seq 30); do docker exec memeval-letta-db pg_isready -U postgres >/dev/null 2>&1 && break; sleep 2; done
docker exec memeval-letta-db psql -U postgres -d letta -qc "CREATE EXTENSION IF NOT EXISTS vector" >/dev/null

if [ ! -x "$dir/.venv/bin/letta" ]; then
  uv venv -q --python 3.12 "$dir/.venv"
  uv pip install -q --python "$dir/.venv/bin/python" --exclude-newer 2026-05-15 \
    "letta[server]==0.16.8" "asyncpg>=0.30.0" "pgvector>=0.2.3" psycopg2-binary pg8000
fi
if [ ! -d "$dir/src/.git" ]; then
  git clone -q --depth 1 --branch 0.16.8 https://github.com/letta-ai/letta.git "$dir/src"
fi
(cd "$dir/src" && HOME="$dir/home" LETTA_PG_URI="$pg" "$dir/.venv/bin/alembic" upgrade head > "$dir/logs/migrate.log" 2>&1)

if [ -f "$dir/logs/server.pid" ]; then kill "$(cat "$dir/logs/server.pid")" 2>/dev/null || true; sleep 2; fi
HOME="$dir/home" LETTA_PG_URI="$pg" OPENAI_API_KEY=proxy OPENAI_BASE_URL="$proxy" \
  nohup "$dir/.venv/bin/letta" server --host 127.0.0.1 --port 8283 > "$dir/logs/server.log" 2>&1 &
echo $! > "$dir/logs/server.pid"
for _ in $(seq 60); do
  curl -sf http://127.0.0.1:8283/v1/health/ >/dev/null && { echo "Letta is up on :8283"; exit 0; }
  sleep 2
done
echo "Letta did not start; see $dir/logs/server.log" >&2
exit 1
