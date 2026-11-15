"""Check for blog part 4 (Mem0): which stored fact the model linked in failure 1 (`f9e8c073`).

From the top of agent-memory-eval, in the environment with the experiment's extras:
  GOOGLE_CLOUD_PROJECT=<project> .venv/bin/python scripts/replays/mem0_fact0_from_cache.py
  (no chat calls; about 60 embedding calls on Vertex, because the main run's embeddings
  were not cached)

The `mem0` arm's main run did not log its prompts. This script builds the same store again.
Every extraction must come from the reply cache (`.cache/llm/`): a chat call that misses is
an error. A hit means that the prompt is identical, byte for byte, to the one the main run
sent, so the replay is the run. The proxy logs each request in full, cache hits included,
so the prompt of the extraction that stored "five sessions" can be read. The call log and
the ledger go to a temporary folder, not to the experiment's own."""
import json, os, re, subprocess, sys, tempfile
from pathlib import Path

QID = "f9e8c073"
REPO = Path(__file__).resolve().parents[2]
scratch = Path(tempfile.mkdtemp())
os.environ.update(MEMEVAL_CALLS_DIR=str(scratch / "calls"), MEMEVAL_LEDGER_DIR=str(scratch / "ledger"))
if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
    raise SystemExit("set GOOGLE_CLOUD_PROJECT to the Vertex project to bill")
sys.path.insert(0, str(REPO / "src"))
import google.oauth2.credentials
from google import genai
from memeval import config, data, llm, proxy
from memeval.arms.mem0 import Mem0Arm


def no_live_chat(handler, payload):
    raise RuntimeError("an extraction missed the cache, so this replay differs from the main run")


proxy.Handler._forward = no_live_chat
# The embeddings are billed to the gcloud CLI's active account, not to the machine's default
# credentials, which may be another account.
token = subprocess.run(["gcloud", "auth", "print-access-token"], check=True, capture_output=True,
                       text=True).stdout.strip()
llm._client = genai.Client(vertexai=True, project=config.project(), location=config.LOCATION,
                           credentials=google.oauth2.credentials.Credentials(token))

q = data.question(QID)
arm = Mem0Arm()
arm.reset(q)
for session in q.sessions:
    arm.ingest(session)
dump = arm.dump()
arm.close()

stored = json.load(open(REPO / "results/main/mem0" / f"{QID}.json"))["dump"]
same = sorted(dump.splitlines()) == sorted(stored.splitlines())
print(f"store rebuilt from the cache: {len(dump.splitlines())} facts; the same as the main run's: {same}")

calls = [json.loads(line) for f in (scratch / "calls").glob("*.jsonl") for line in f.read_text().splitlines()]
print(f"chat calls: {len(calls)}, all from the cache: {all(c['cache_hit'] for c in calls)}")
for call in calls:
    user = call["request"]["messages"][1]["content"]
    new_messages = user.split("## New Messages", 1)[1].split("## Observation Date", 1)[0]
    if "five sessions" not in new_messages:
        continue
    existing = json.loads(re.search(r"## Existing Memories\n(\[.*?\])\n", user, re.S).group(1))
    reply = json.loads(call["reply"]["choices"][0]["message"]["content"])
    print(f"\nObservation Date: {user.split('## Observation Date', 1)[1].split()[0]}")
    print("Existing Memories shown to the model:")
    for m in existing:
        print(f"  {m['id']}: {m['text']}")
    print("Reply: new facts and their links")
    for m in reply["memory"]:
        print(f"  {m.get('linked_memory_ids', [])}  {m['text']}")
