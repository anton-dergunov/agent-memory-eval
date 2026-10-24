#!/usr/bin/env bash
# Start a local Honcho server at the pinned release, wired to memeval.proxy.
#
#   infra/honcho/up.sh           # start (idempotent)
#   infra/honcho/up.sh --reset   # discard every workspace first
#   infra/honcho/down.sh         # stop
#
# Postgres (pgvector) and Redis run in Docker from Honcho's own compose file.
# The API and the deriver run natively from Honcho's frozen lockfile with uv.
# (Honcho's Dockerfile copies uv from ghcr.io, which some networks block; the
# native run is the same code and the same dependency versions.)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
dir="$repo/vendor/honcho"
commit=608aec8a928da13c540262ed980c569448fb53ab   # v3.3.0, 9 October 2026
proxy="${MEMEVAL_HONCHO_PROXY:-http://127.0.0.1:8100/v1}"
model="${MEMEVAL_CHAT_MODEL:-gemini-3.1-flash-lite}"
# Honcho's compose file names floating tags (pgvector/pgvector:pg15, redis:8.2);
# these are the images they pointed to when the experiment ran (17-18 Oct 2026).
pg_image=pgvector/pgvector:0.8.7-pg15@sha256:47af0b65960b14f1c6945aa4ccae37836c632e9a6fe0eea9160936e616e5b2e9
redis_image=redis:8.2.9@sha256:66b7f4c2f3c6ef1b298bbd7b13c806bc6f71e61f1136a4f58710daf2cb053b21

if [ ! -d "$dir/.git" ]; then
  git clone -q https://github.com/plastic-labs/honcho.git "$dir"
fi
git -C "$dir" fetch -q --tags origin || true
git -C "$dir" checkout -q "$commit"
sed -e "s#image: pgvector/pgvector:pg15\$#image: $pg_image#" -e "s#image: redis:8.2\$#image: $redis_image#" \
  "$dir/docker-compose.yml.example" > "$dir/docker-compose.yml"
sed -e "s#@PROXY@#$proxy#g" -e "s#@MODEL@#$model#g" "$here/honcho.env.template" > "$dir/.env"

cd "$dir"
"$here/down.sh" >/dev/null 2>&1 || true
if [ "${1:-}" = "--reset" ]; then docker compose down -v database redis; fi
docker compose up -d --wait database redis
UV_PYTHON="${UV_PYTHON:-python3.13}" uv sync -q --frozen --no-group dev

# Honcho counts tokens with tiktoken, whose download host some networks block;
# the cache is rebuilt from Hugging Face and checked against tiktoken's hashes.
export TIKTOKEN_CACHE_DIR="$repo/.cache/tiktoken"
python3 "$repo/infra/tiktoken_cache.py" "$TIKTOKEN_CACHE_DIR" >/dev/null

export DB_CONNECTION_URI=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/postgres
export CACHE_URL='redis://127.0.0.1:6379/0?suppress=true' CACHE_ENABLED=true
mkdir -p logs
.venv/bin/python scripts/provision_db.py > logs/provision.log 2>&1
nohup .venv/bin/fastapi run --host 127.0.0.1 --port 8000 src/main.py > logs/api.log 2>&1 &
echo $! > logs/api.pid
for _ in $(seq 60); do
  if curl -sf http://127.0.0.1:8000/health >/dev/null; then
    nohup .venv/bin/python -m src.deriver > logs/deriver.log 2>&1 &
    echo $! > logs/deriver.pid
    echo "Honcho is up on :8000 (logs in $dir/logs)"
    exit 0
  fi
  sleep 2
done
echo "Honcho did not become healthy; see $dir/logs/api.log" >&2
exit 1
