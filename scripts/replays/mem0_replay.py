"""Replay for blog part 4 (Mem0): the notebook's nine facts, scored with the optional packages on.

From the top of agent-memory-eval, in the environment with the experiment's extras
(`uv sync --extra experiment`, which installs spaCy and fastembed):
  .venv/bin/python scripts/replays/mem0_replay.py [notebook]   (embedding calls only)

The model is replaced by the two extraction replies that the notebook printed, so the
real library stores the same nine facts with no chat call. Every search then runs with
explain=True, which returns the three parts of each score: similarity, keyword (BM25)
and entity boost. The notebook itself runs without the extras, so its scores are the
similarity alone."""
import json, logging, os, shutil, sys, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "notebooks"))
from config import CHAT_MODEL, EMBED_MODEL, gemini_api_key
os.environ["MEM0_TELEMETRY"] = "False"
for noisy in ("google_genai", "httpx"):
    logging.getLogger(noisy).setLevel(logging.ERROR)
from mem0 import Memory

nb = json.load(open(sys.argv[1] if len(sys.argv) > 1 else REPO / "notebooks/02-mem0.ipynb"))
texts = ["".join(o.get("text", "")) for c in nb["cells"] if c["cell_type"] == "code" for o in c.get("outputs", [])]
replies = [t.split("--- RESPONSE ---\n", 1)[1] for t in texts if t.startswith("--- RESPONSE ---\n")]
assert len(replies) == 2, "expected the replies of the two add() calls"
source = next("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code" and "SESSION_1 = [" in "".join(c["source"]))
ns = {}
exec(source.split("def show_session")[0], ns)

store = Path(tempfile.mkdtemp())  # outside the repository
key = gemini_api_key()
m = Memory.from_config({
    "llm": {"provider": "gemini", "config": {"model": CHAT_MODEL, "api_key": key, "temperature": 0.0}},
    "embedder": {"provider": "gemini", "config": {"model": f"models/{EMBED_MODEL}", "api_key": key, "embedding_dims": 768}},
    "vector_store": {"provider": "qdrant", "config": {"path": str(store / "qdrant"), "collection_name": "replay", "embedding_model_dims": 768}},
    "history_db_path": str(store / "history.db")})
answers = iter(replies)
m.llm.generate_response = lambda *a, **k: next(answers)

m.add(ns["SESSION_1"], user_id="anton")
m.add(ns["SESSION_2"], user_id="anton")
for q in [ns["QUESTION"], "what should I cook tonight?"]:
    hits = m.search(q, filters={"user_id": "anton"}, explain=True)["results"]
    print(f"\n{q!r}  ({len(hits)} results)")
    for rank, h in enumerate(hits, 1):
        d = h.get("score_details", {})
        print(f"  {rank}  {h['score']:.3f}  sem {d.get('semantic_score', 0):.3f}  bm25 {d.get('bm25_score', 0):.3f}"
              f"  ent {d.get('entity_boost', 0):.3f}  /{d.get('max_possible_score')}  {h['memory']}")
shutil.rmtree(store, ignore_errors=True)
