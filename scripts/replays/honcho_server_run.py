"""Run the series' example through the real Honcho v3.3.0 server, as the experiment ran it.

Server: `infra/honcho/up.sh` in agent-memory-eval (commit 608aec8, every model role on
gemini-3.1-flash-lite through memeval.proxy on port 8100, which logs every request in full).
Start it with COMPOSE_PROJECT_NAME=memeval-honcho so that it does not touch other Honcho
containers on the machine.

What this run does, step by step, each step tagged in the proxy's call log:
  s1      add session 1 (14 March 2026, messages a minute apart), wait for the deriver
  dream1  schedule a dream for (Anton, Anton), wait for it
  s2      add session 2 (20 July 2026), wait for the deriver
  dream2  schedule a second dream, wait for it
  chat    peer.chat(QUESTION)                    (the dialectic agent)
  repr    peer.representation(search_query=QUESTION)   (no model call)

The experiment scheduled one dream after the whole history. Here a dream follows each session:
in real use many other conversations would fall between March and July, enough to pass Honcho's
own trigger (50 new explicit conclusions, 8 hours since the last dream, 60 idle minutes).

Every run gets its own reply cache, so runs 2 and 3 make real calls instead of replaying run 1.
The stored state (every conclusion, soft-deleted ones included, the premise links, the peer card)
is read from the server's Postgres with SELECT statements only.

    GOOGLE_CLOUD_PROJECT=<project> .venv/bin/python -I scripts/replays/honcho_server_run.py --run 1
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "honcho_server_runs"
SCRATCH = Path(os.environ.get("HONCHO_RUN_SCRATCH", "/tmp/honcho-runs"))
DB = "memeval-honcho-database-1"

PEER, ASSISTANT = "Anton", "assistant"
SESSION_1 = [
    ("user", "I'm planning a dinner for my sister's visit to Berlin next week. Worth saying up "
             "front: I've been strictly vegetarian for eight years, and I have a severe peanut "
             "allergy — anaphylactic, not a preference."),
    ("assistant", "Understood — no meat, and peanuts are a hard exclusion. Any cuisine you lean "
                  "towards?"),
    ("user", "Indian, usually. Paneer dishes especially. And I'd rather not spend more than about "
             "40 euros a head."),
]
SESSION_2 = [
    ("user", "Small update on the food thing — I started eating fish about a month ago. So I'm "
             "pescatarian now, not vegetarian. Still no meat, and the peanut situation obviously "
             "hasn't changed."),
    ("assistant", "Noted, fish is in. Anything else shifted?"),
    ("user", "I moved to Kreuzberg in May, so anything walkable from there is a plus."),
    ("assistant", "Kreuzberg, noted. Anything else for next time?"),
    ("user", "Yes — my sister Lena is coming back in the autumn, and she's bringing her partner, "
             "Jonas."),
    ("assistant", "Lovely. Anything I should know about what they eat?"),
    ("user", "Lena can't eat shellfish, and Jonas is coeliac."),
]
QUESTION = ("My sister and her partner are in town tonight. Book the three of us somewhere for "
            "dinner — you know what we can and can't eat.")
DATES = {"s1": datetime(2026, 3, 14, 12, 0, tzinfo=timezone.utc),
         "s2": datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)}


def setup(run: int) -> Path:
    """Point the experiment's cache, call log and ledger at fresh directories for this run."""
    base = SCRATCH / f"run{run}"
    for name, env in (("llm", "MEMEVAL_CACHE_DIR"), ("calls", "MEMEVAL_CALLS_DIR"),
                      ("ledger", "MEMEVAL_LEDGER_DIR")):
        (base / name).mkdir(parents=True, exist_ok=True)
        os.environ[env] = str(base / name)
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        raise SystemExit("set GOOGLE_CLOUD_PROJECT to the Vertex project to bill")
    sys.path.insert(0, str(REPO / "src"))
    return base


def gcloud_token():
    """A Vertex token from the gcloud CLI's active account, renewed every 30 minutes.

    The machine's Application Default Credentials belong to another account; the blog project
    is billed through the account that gcloud is logged in as.
    """
    cached = {"at": 0.0, "token": ""}

    def token() -> str:
        if time.time() - cached["at"] > 1800:
            cached["token"] = subprocess.run(["gcloud", "auth", "print-access-token"], check=True,
                                             capture_output=True, text=True).stdout.strip()
            cached["at"] = time.time()
        return cached["token"]

    return token


def sql(query: str) -> list[dict]:
    """One read-only query on the server's Postgres, rows as dicts."""
    wrapped = f"SELECT coalesce(json_agg(t), '[]'::json) FROM ({query}) t"
    out = subprocess.run(["docker", "exec", DB, "psql", "-U", "postgres", "-At", "-c", wrapped],
                         check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=int, required=True)
    args = parser.parse_args()
    base = setup(args.run)

    from honcho import Honcho
    from honcho.api_types import MessageCreateParams, PeerConfig
    from memeval import llm, proxy

    from google import genai
    from google.oauth2.credentials import Credentials
    from memeval import config

    token = gcloud_token()
    proxy._token = token                     # chat calls
    llm._client = genai.Client(vertexai=True, project=config.project(), location=config.LOCATION,
                               credentials=Credentials(token()))   # embedding calls
    proxy.start(8100)
    workspace = f"example-run{args.run}-{uuid.uuid4().hex[:6]}"
    honcho = Honcho(api_key="local", base_url="http://127.0.0.1:8000", workspace_id=workspace,
                    timeout=900)
    user = honcho.peer(PEER)
    assistant = honcho.peer(ASSISTANT, configuration=PeerConfig(observe_me=False))
    steps: list[dict] = []

    def drain(confirmations: int = 2) -> None:
        empty, deadline = 0, time.monotonic() + 1800
        while time.monotonic() < deadline:
            status = honcho.queue_status()
            if status.pending_work_units or status.in_progress_work_units:
                empty = 0
            else:
                empty += 1
                if empty >= confirmations:
                    return
            time.sleep(3)
        raise RuntimeError("queue did not drain")

    def step(name: str, action) -> object:
        llm.TAGS.clear()
        llm.TAGS.update(arm="honcho-example", qid=f"run{args.run}", phase=name)
        started = datetime.now(timezone.utc).isoformat()
        result = action()
        steps.append({"step": name, "started": started,
                      "ended": datetime.now(timezone.utc).isoformat()})
        return result

    def add_session(key: str, turns) -> None:
        chat = honcho.session(key, peers=[user, assistant])
        chat.add_messages([MessageCreateParams(peer_id=PEER if role == "user" else ASSISTANT,
                                               content=text,
                                               created_at=DATES[key] + timedelta(minutes=i))
                           for i, (role, text) in enumerate(turns)])
        drain()

    def dream() -> None:
        honcho.schedule_dream(observer=user, observed=user)
        drain()

    step("s1", lambda: add_session("s1", SESSION_1))
    step("dream1", dream)
    step("s2", lambda: add_session("s2", SESSION_2))
    step("dream2", dream)
    reply = step("chat", lambda: user.chat(QUESTION))
    representation = step("repr", lambda: user.representation(search_query=QUESTION))
    llm.TAGS.clear()

    documents = sql(f"""
        SELECT id, level, content, session_name, observer, observed, times_derived,
               created_at, deleted_at, internal_metadata
        FROM documents WHERE workspace_name = '{workspace}' ORDER BY created_at, id""")
    links = sql(f"""
        SELECT derived_id, source_id, position FROM document_sources
        WHERE workspace_name = '{workspace}' ORDER BY derived_id, position""")
    peers = sql(f"SELECT name, internal_metadata FROM peers WHERE workspace_name = '{workspace}'")

    calls = []
    for path in sorted((base / "calls").glob("calls-*.jsonl")):
        calls += [json.loads(line) for line in path.read_text().splitlines()]
    ledger = []
    for path in sorted((base / "ledger").glob("*.jsonl")):
        ledger += [json.loads(line) for line in path.read_text().splitlines()]

    text = reply if isinstance(reply, str) else getattr(reply, "content", None) or str(reply)
    OUT.mkdir(exist_ok=True)
    result = {"run": args.run, "workspace": workspace, "server": "honcho v3.3.0 (608aec8)",
              "model": "gemini-3.1-flash-lite (every role)", "steps": steps,
              "question": QUESTION, "chat": text, "representation": representation,
              "documents": documents, "links": links, "peers": peers,
              "calls": calls, "ledger": ledger}
    path = OUT / f"run{args.run}.json"
    path.write_text(json.dumps(result, indent=1, ensure_ascii=False, default=str))
    print(f"{path}: {len(documents)} documents, {len(links)} links, {len(calls)} calls")


if __name__ == "__main__":
    main()
