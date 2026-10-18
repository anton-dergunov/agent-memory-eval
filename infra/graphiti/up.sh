#!/usr/bin/env bash
# Start Neo4j for the Graphiti arm (bolt://127.0.0.1:7687, neo4j / memeval-local).
#   infra/graphiti/up.sh           # start (idempotent)
#   infra/graphiti/up.sh --reset   # discard every graph first
set -euo pipefail
name=memeval-neo4j
if [ "${1:-}" = "--reset" ]; then docker rm -f "$name" >/dev/null 2>&1 || true; docker volume rm -f memeval-neo4j-data >/dev/null; fi
if ! docker ps --format '{{.Names}}' | grep -qx "$name"; then
  docker rm -f "$name" >/dev/null 2>&1 || true
  docker run -d --name "$name" \
    -p 127.0.0.1:7474:7474 -p 127.0.0.1:7687:7687 \
    -e NEO4J_AUTH=neo4j/memeval-local \
    -e NEO4J_server_memory_heap_max__size=2G -e NEO4J_server_memory_pagecache_size=1G \
    -v memeval-neo4j-data:/data neo4j:5.26 >/dev/null
fi
for _ in $(seq 60); do
  docker exec "$name" cypher-shell -u neo4j -p memeval-local "RETURN 1" >/dev/null 2>&1 \
    && { echo "Neo4j is up on bolt://127.0.0.1:7687"; exit 0; }
  sleep 2
done
echo "Neo4j did not start; see: docker logs $name" >&2
exit 1
