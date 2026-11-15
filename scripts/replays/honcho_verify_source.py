"""Check notebooks/honcho_source.py against the requests the real server sent (server run 1).

With the same inputs, every prompt and tool schema the notebook builds from Honcho's source
must equal what Honcho v3.3.0 itself sent to the model, as logged by the experiment's proxy.

    .venv/bin/python scripts/replays/honcho_verify_source.py
"""
import difflib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "notebooks"))
import honcho_source as hs  # noqa: E402

run = json.loads((Path(__file__).parent / "honcho_server_runs/run1.json").read_text())


def request(step, marker):
    return next(c["request"] for c in run["calls"]
                if c["phase"] == step and marker in c["request"]["messages"][0]["content"][:120])


def same(label, logged, mine):
    print(f"{'OK  ' if logged == mine else 'DIFF'} {label}")
    if logged != mine:
        print("\n".join(list(difflib.unified_diff(logged.splitlines(), mine.splitlines(), lineterm=""))[:30]))


S1 = [("Anton", "I'm planning a dinner for my sister's visit to Berlin next week. Worth saying up front: "
                "I've been strictly vegetarian for eight years, and I have a severe peanut allergy — "
                "anaphylactic, not a preference."),
      ("assistant", "Understood — no meat, and peanuts are a hard exclusion. Any cuisine you lean towards?"),
      ("Anton", "Indian, usually. Paneer dishes especially. And I'd rather not spend more than about 40 "
                "euros a head.")]
start = datetime(2026, 3, 14, 12, 0)
messages = "\n".join(hs.deriver_message(i, peer, "Anton", start + timedelta(minutes=i), text)
                     for i, (peer, text) in enumerate(S1))
same("deriver prompt, session 1", request("s1", "Analyze")["messages"][0]["content"],
     hs.deriver_prompt("Anton", messages))

d1, d2 = request("dream1", "deductive reasoning"), request("dream2", "deductive reasoning")
i1 = request("dream1", "inductive reasoning")
same("deduction system prompt", d1["messages"][0]["content"], hs.deduction_system_prompt())
same("deduction user prompt, no card", d1["messages"][1]["content"], hs.deduction_user_prompt("Anton", None))
card = [line[2:] for line in d2["messages"][1]["content"].splitlines() if line.startswith("- IDENTITY")
        or line.startswith("- ATTRIBUTE")]
same("deduction user prompt, with card", d2["messages"][1]["content"], hs.deduction_user_prompt("Anton", card))
same("induction system prompt", i1["messages"][0]["content"], hs.induction_system_prompt())
same("induction user prompt", i1["messages"][1]["content"], hs.induction_user_prompt("Anton"))
for req, name in ((d1, "DEDUCTION_SPECIALIST_TOOLS"), (i1, "INDUCTION_SPECIALIST_TOOLS")):
    logged = [{k: t["function"][k] for k in ("name", "description", "parameters")} for t in req["tools"]]
    mine = [{"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}
            for t in hs.tool_set(name)]
    same(name, json.dumps(logged, indent=1), json.dumps(mine, indent=1))

chat = next(c["request"] for c in run["calls"] if c["phase"] == "chat")
names = [t["function"]["name"] for t in chat["tools"]]
logged = [{k: t["function"][k] for k in ("name", "description", "parameters")} for t in chat["tools"]]
mine = [{"name": t["name"], "description": t["description"], "parameters": t["input_schema"]}
        for t in hs.tool_set("DIALECTIC_TOOLS")]
same("DIALECTIC_TOOLS", json.dumps(logged, indent=1), json.dumps(mine, indent=1))
peer_card = next(p for p in run["peers"] if p["name"] == "Anton")["internal_metadata"]["peer_card"]
same("dialectic system prompt", chat["messages"][0]["content"],
     hs.dialectic_system_prompt("Anton", peer_card, set(names)))
user = chat["messages"][1]["content"]
query, _, rest = user.partition("\n\n## Relevant Observations (prefetched)\n")
intro, _, prefetched = rest.partition("\n\n")
same("dialectic user message", user,
     hs.dialectic_user_message(query.removeprefix("Query: "), prefetched))
