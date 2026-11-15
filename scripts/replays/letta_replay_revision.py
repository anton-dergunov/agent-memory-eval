"""R2b on the committed notebook 04: what the agent writes at the message that carries the change.

Run from agent-memory-eval:
    PYTHONPATH=notebooks .venv/bin/python <this file> letta_dump.json

The request is the in-line agent's first call of session 2 (the message with the changed fact),
rebuilt from the dump of the notebook, sent 10 times at Letta's temperature of 1.0:
  a. as in the notebook;
  b. with the experiment's three persona lines in the persona block, and every user message of the
     notebook prefixed with its date, as the experiment's wrapper does. The block from session 1 is
     the notebook's own (written without the persona), so this tests only the revision.
For each reply: the tool called, whether the new text keeps the earlier value ("vegetarian"), and
whether it carries a date.
"""
import json
import re
import sys

from config import generate

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

REPEATS = 10
call = json.load(open(sys.argv[1]))["calls"][3]
assert "Small update on the food thing" in json.dumps(call["contents"])
dated = json.loads(json.dumps(call["contents"]))
dated[0]["parts"][0]["text"] = "[2026-07-20 19:00] " + dated[0]["parts"][0]["text"]
variants = {
    "a. as in the notebook": (call["system"], call["contents"]),
    "b. persona lines + dated message": (call["system"].replace(STARTER_END, STARTER_END + PERSONA_LINES), dated),
}
DATE = re.compile(r"20\d\d-\d\d(-\d\d)?|(January|February|March|April|May|June|July|August|September)\s+20\d\d")
for label, (system, contents) in variants.items():
    print(label)
    for _ in range(REPEATS):
        reply = generate(contents, system=system, tools=call["tools"], temperature=1.0)
        parts = (reply.candidates[0].content.parts or []) if reply.candidates[0].content else []
        calls = [p.function_call for p in parts if p.function_call]
        if not calls:
            print("     no tool call")
            continue
        for c in calls:
            args = dict(c.args or {})
            new = args.get("new_string", "")
            old = args.get("old_string", "")
            print(f"     {c.name}: keeps earlier value={'vegetarian' in new.lower()}, dated={bool(DATE.search(new))}, "
                  f"old_string {len(old)} chars | {new[:150]!r}")
