"""R2 on the committed notebook 04 (after the 2026-11-15 rerun): does the agent write on the first message?

Run from agent-memory-eval:
    PYTHONPATH=notebooks .venv/bin/python <this file> letta_dump.json

The request is the in-line agent's first call of session 1, rebuilt from the dump of the notebook
(letta_dump_run.py), sent 10 times at Letta's temperature of 1.0 (the notebook runs at 0):
  a. as in the notebook;
  b. with the experiment's three persona lines (letta-persona) added to the persona block, and the
     message prefixed with its date, as the experiment's wrapper does.
Counts the replies whose first step edits memory. Live calls, no reply cache.
"""
import json
import sys

from config import generate

REPEATS = 10
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

call = json.load(open(sys.argv[1]))["calls"][0]
assert "chars_current=0" in call["system"] and "s1" in call["system"]
text = call["contents"][0]["parts"][0]["text"]
variants = {
    "a. as in the notebook": (call["system"], call["contents"]),
    "b. persona lines + dated message": (
        call["system"].replace(STARTER_END, STARTER_END + PERSONA_LINES),
        [{"role": "user", "parts": [{"text": "[2026-03-14 19:00] " + text}]}]),
}
for label, (system, contents) in variants.items():
    first_steps = []
    for _ in range(REPEATS):
        reply = generate(contents, system=system, tools=call["tools"], temperature=1.0)
        parts = (reply.candidates[0].content.parts or []) if reply.candidates[0].content else []
        calls = [p.function_call for p in parts if p.function_call]
        first_steps.append([f"{c.name}({json.dumps(dict(c.args or {}), ensure_ascii=False)[:160]})" for c in calls]
                           or ["no tool call"])
    edits = sum(any(s.startswith("memory_") for s in step) for step in first_steps)
    print(f"{label}: memory edited in {edits} of {REPEATS}")
    for step in first_steps:
        print("    ", "; ".join(step))
