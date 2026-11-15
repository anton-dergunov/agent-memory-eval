"""Replays for part 6 (Letta), with gemini-3.1-flash-lite, live (no reply cache).

Run from agent-memory-eval:
    PYTHONPATH=notebooks .venv/bin/python <this file> letta_dump.json

The requests are rebuilt from the dump of notebook 04 (letta_dump_run.py), so each one is the
request the notebook sent, with one thing changed.

R1. The tool descriptions. The notebook describes each tool by its docstring's summary only; the
    0.16.8 server adds the docstring's Examples section (copied here from a request the server sent
    in the experiment, .cache/calls/calls-33743.jsonl). Replay the in-line agent's first step of
    session 2 (the message with the changed fact) 5 times with each description, at temperature 0
    and at the server's 1.0. Count memory_replace calls whose old_string is the whole block.
R2. The first message of session 1, at the server's temperature 1.0, 10 times each:
    a. as in the notebook;
    b. with the server's tool descriptions;
    c. with the server's descriptions and the experiment's three persona lines (letta-persona),
       the message prefixed with its date as the experiment's wrapper does.
    Count the replies that edit memory in their first step.
"""
import json
import sys
from pathlib import Path

from config import generate

DUMP = json.load(open(sys.argv[1]))
REPO = Path(__file__).resolve().parent
SERVER_LOG = Path(".cache/calls/calls-33743.jsonl")

PERSONA_LINES = (  # src/memeval/arms/letta.py, PERSONA_INSTRUCTED minus the starter text
    "\n\nHow I keep my memory of the user:\n"
    "- Every user message starts with its date in square brackets, for example "
    "[2024-01-15 09:30]. I write that date on each fact I save about the user, never the "
    "server's time shown on tool results or in my system prompt.\n"
    "- When the user mentions a new value for something already in my memory (a count, a time, "
    "a place, a status), even in passing, I update that line at once with memory_replace and keep "
    "the earlier value with its date, for example \"has 4 herb plants on the balcony (2024-03-02; "
    "earlier 2, 2024-01-15)\".\n"
    "- When the user asks about themselves, I check my memory and also search past messages. "
    "The search matches my query word for word, so I search with one or two distinctive words, "
    "not a whole phrase.")
STARTER_END = "I am kind, thoughtful, and inquisitive."


def server_tools():
    request = next(json.loads(line)["request"] for line in SERVER_LOG.open()
                   if json.loads(line)["source"] == "proxy")
    return [{"function_declarations": [
        {"name": t["function"]["name"], "description": t["function"]["description"],
         "parameters_json_schema": t["function"]["parameters"]} for t in request["tools"]]}]


def first_step(call, *, tools=None, system=None, contents=None, temperature):
    reply = generate(contents or call["contents"], system=system or call["system"],
                     tools=tools or call["tools"], temperature=temperature)
    parts = (reply.candidates[0].content.parts or []) if reply.candidates[0].content else []
    return [p.function_call for p in parts if p.function_call]


def describe(calls, block):
    out = []
    for c in calls:
        args = dict(c.args or {})
        if c.name == "memory_replace":
            old = args.get("old_string", "")
            out.append(f"memory_replace(old_string {len(old)} chars"
                       f"{', the whole block' if old.strip() == block.strip() else ''})")
        else:
            out.append(c.name)
    return out or ["no tool call"]


calls = DUMP["calls"]
SERVER = server_tools()

print("R1. session 2, first message, first step of the in-line agent")
s21 = calls[3]
block = "\n".join(  # the human block after session 1, as the notebook printed it
    ["The user is a vegetarian (8 years) and has a severe, anaphylactic peanut allergy.",
     "They enjoy Indian cuisine, specifically paneer dishes.", "Budget: ~40 euros per person.",
     "Location: Berlin."])
assert block in s21["system"]
print("   the notebook's own call:", describe([type("C", (), {"name": "memory_replace", "args": a["function_call"]["args"]})
                                                for a in s21["reply"]["candidates"][0]["content"]["parts"]
                                                if "function_call" in a], block))
for label, tools in (("notebook descriptions", None), ("server descriptions", SERVER)):
    for temperature in (0.0, 1.0):
        results = [describe(first_step(s21, tools=tools, temperature=temperature), block) for _ in range(5)]
        print(f"   {label}, temperature {temperature}:")
        for r in results:
            print("     ", "; ".join(r))

print("\nR2. session 1, first message, first step, temperature 1.0")
s11 = calls[0]
assert "chars_current=0" in s11["system"]
persona_system = s11["system"].replace(STARTER_END, STARTER_END + PERSONA_LINES)
assert persona_system != s11["system"]
dated = [{"role": "user", "parts": [{"text": "[2026-03-14 19:00] " + s11["contents"][0]["parts"][0]["text"]}]}]
variants = {
    "a. as in the notebook": {},
    "b. server descriptions": {"tools": SERVER},
    "c. server descriptions + persona lines + dated message": {"tools": SERVER, "system": persona_system,
                                                               "contents": dated},
}
for label, change in variants.items():
    results = [describe(first_step(s11, temperature=1.0, **change), "") for _ in range(10)]
    edits = sum(any(r.startswith("memory_") for r in result) for result in results)
    print(f"   {label}: memory edited in {edits} of 10 -> {results}")
