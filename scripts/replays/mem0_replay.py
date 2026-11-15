"""Replays for blog part 4 (Mem0). Run with the repository's environment:
  From the top of agent-memory-eval: .venv/bin/python <this file> A   (5 Gemini chat calls)
  From the top of agent-memory-eval: .venv/bin/python <this file> B   (embedding calls only)
A: the example's second extraction call, 5 times, raw replies.
B: the same nine facts stored with the nlp extras on; search with explain=True."""
import json, os, sys, shutil, time, logging
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "notebooks"))
from config import CHAT_MODEL, EMBED_MODEL, gemini_api_key
os.environ["MEM0_TELEMETRY"] = "False"
for noisy in ("google_genai", "httpx"): logging.getLogger(noisy).setLevel(logging.ERROR)
from mem0 import Memory
from mem0.configs.prompts import ADDITIVE_EXTRACTION_PROMPT

import tempfile
SP = Path(tempfile.mkdtemp())  # scratch stores, outside the repository
nb = json.load(open(REPO / "notebooks/02-mem0.ipynb"))
out = lambda i: "".join(nb["cells"][i]["outputs"][0]["text"])
looked = out(25).split("--- USER, the part Mem0 looked up ---\n", 1)[1]
given = out(27).split("--- USER, the part to extract from ---\n", 1)[1]
user2 = (looked.rstrip("\n") + "\n\n" + given).rstrip("\n")
reply1 = out(18).split("--- RESPONSE ---\n", 1)[1]
facts2 = [
 "User transitioned from a strict vegetarian diet to a pescatarian diet in September 2026, meaning they now eat fish but no other meat.",
 "User relocated to the Kreuzberg neighborhood in May 2026 and prefers restaurant options within walking distance.",
 "User's sister, Lena, is visiting in the autumn of 2026 and has a shellfish allergy.",
 "User's sister Lena is traveling with her partner, Jonas, who has coeliac disease and requires a gluten-free diet."]
reply2 = json.dumps({"memory": [{"id": str(i), "text": t, "attributed_to": "user"} for i, t in enumerate(facts2)]})

def make(name):
    store = SP / name
    shutil.rmtree(store, ignore_errors=True); store.mkdir()
    key = gemini_api_key()
    return Memory.from_config({
        "llm": {"provider": "gemini", "config": {"model": CHAT_MODEL, "api_key": key, "temperature": 0.0}},
        "embedder": {"provider": "gemini", "config": {"model": f"models/{EMBED_MODEL}", "api_key": key, "embedding_dims": 768}},
        "vector_store": {"provider": "qdrant", "config": {"path": str(store / "qdrant"), "collection_name": "replay", "embedding_model_dims": 768}},
        "history_db_path": str(store / "history.db")})

which = sys.argv[1]
if which == "A":
    m = make("store-a")
    print("USER PROMPT SENT:\n" + user2 + "\n" + "=" * 60)
    for i in range(5):
        r = m.llm.generate_response(messages=[{"role": "system", "content": ADDITIVE_EXTRACTION_PROMPT},
                                              {"role": "user", "content": user2}], response_format={"type": "json_object"})
        print(f"--- reply {i+1} ---\n{r}")
        time.sleep(5)
else:
    m = make("store-b")
    replies = iter([reply1, reply2])
    calls = []
    m.llm.generate_response = lambda *a, **k: next(replies)
    for attr in ("embed", "embed_batch"):
        orig = getattr(m.embedding_model, attr)
        def wrap(*a, _o=orig, _n=attr, **k):
            calls.append((_n, a[0] if isinstance(a[0], str) else list(a[0]))); return _o(*a, **k)
        setattr(m.embedding_model, attr, wrap)
    S1 = [c["source"] for c in nb["cells"] if c["cell_type"] == "code" and "SESSION_1 = [" in "".join(c["source"])][0]
    ns = {}; exec("".join(S1).split("def show_session")[0], ns)
    m.add(ns["SESSION_1"], user_id="anton"); m.add(ns["SESSION_2"], user_id="anton")
    print("embedding calls during the two add() calls:")
    for n, a in calls: print("  ", n, (a[:60] if isinstance(a, str) else a))
    for q in [ns["QUESTION"], "any good places nearby?", "what should I cook tonight?", "allergies?"]:
        hits = m.search(q, filters={"user_id": "anton"}, explain=True)["results"]
        print(f"\n{q!r}  ({len(hits)} results)")
        for h in hits:
            d = h.get("score_details", {})
            print(f"  {h['score']:.3f}  sem {d.get('semantic_score',0):.3f}  bm25 {d.get('bm25_score',0):.3f}  ent {d.get('entity_boost',0):.3f}  /{d.get('max_possible_score')}  {h['memory'][:70]}")
    hits = m.search(ns["QUESTION"], filters={"user_id": "anton"}, limit=6)["results"]; print("\nlimit=6 ->", len(hits))
    hits = m.search(ns["QUESTION"], filters={"user_id": "anton"}, top_k=6)["results"]; print("top_k=6 ->", len(hits)); [print("  ", round(h["score"],3), h["memory"][:70]) for h in hits]
