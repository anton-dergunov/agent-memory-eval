"""Appended to an exported copy of notebooks/03-zep-graphiti (jupytext --to py:percent), this
    dumps every model call, entity, fact and score of the run to JSON, for the post and its figures.

Run the copy from agent-memory-eval/notebooks:
    MEMORY_NOTEBOOKS_CACHE=1 DUMP=run03.json PYTHONPATH=$PWD ../.venv/bin/python run03.py
With the cache on, every request the notebook already made replays, so no new calls are made.
"""
import json
# ---- dump for the blog figures ----
def _d(x): return x.isoformat() if x else None
def _f(f): return {"source": f.source, "target": f.target, "relation": f.relation, "text": f.text,
                   "valid_at": _d(f.valid_at), "invalid_at": _d(f.invalid_at), "created_at": _d(f.created_at),
                   "expired_at": _d(f.expired_at), "said_in": f.said_in,
                   "q_cosine": float(f.vector @ question_vector)}
ents = list(graph.entities.values())
dump = {
  "calls": [{k: v for k, v in c.items()} for c in CALLS],
  "embeds": EMBEDS,
  "entities": [{"name": e.name, "kind": e.kind} for e in ents],
  "name_sim": {a.name: {b.name: float(a.vector @ b.vector) for b in ents} for a in ents},
  "facts": [_f(f) for f in graph.facts],
  "log": {k: {"found": [e.name for e in v["found"]], "same_as": v["same_as"],
              "records": [{"new": r["new fact"], "same_pair": [f.text for f in r["same pair"]],
                           "candidates": [f.text for f in r["candidates"]],
                           "duplicate_of": r["duplicate of"].text if r["duplicate of"] else None,
                           "contradicts": [f.text for f in r["contradicts"]],
                           "closed": [f.text for f in r["closed"]]} for r in v["records"]]}
          for k, v in LOG.items()},
  "returned": [f.text for f in returned], "current": [f.text for f in current],
  "text_hits": [f.text for f in text_hits], "text_and_walk": [f.text for f in text_and_walk],
  "chain": [f.text for f in chain], "tuned": [f.text for f in tuned_ranking],
}
json.dump(dump, open(__import__("os").environ["DUMP"], "w"), indent=1, default=str)
print("dumped")
