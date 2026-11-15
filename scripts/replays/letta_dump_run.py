"""Rebuild notebook 04's run from the reply cache and dump every request and reply.

Run from agent-memory-eval:
    MEMORY_NOTEBOOKS_CACHE=1 PYTHONPATH=notebooks .venv/bin/python <this file> [NOTEBOOK] [OUT.json]

It executes the notebook's code cells in order. A cache miss stops the run instead of calling
the model, so it reproduces the committed outputs exactly or fails. The dump holds, for each
model call, the system prompt, the conversation sent, the tools offered and the reply; plus the
agents' blocks and recall at the end. Part 6 quotes prompts and blocks from it.
"""
import json
import sys
from pathlib import Path

import config

NOTEBOOK = Path(sys.argv[1] if len(sys.argv) > 1 else "notebooks/04-letta.ipynb")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/letta_dump.json")


def no_live_calls():
    raise RuntimeError("cache miss: this run would call the model")


config.gemini = no_live_calls
RECORD = []
_generate = config.generate


def recording_generate(contents, **kwargs):
    reply = _generate(contents, **kwargs)
    RECORD.append({"system": kwargs.get("system"), "contents": json.loads(json.dumps(contents, default=str)),
                   "tools": kwargs.get("tools"), "temperature": kwargs.get("temperature", 0.0),
                   "reply": json.loads(reply.model_dump_json(exclude_none=True))})
    return reply


config.generate = recording_generate
cells = [c for c in json.loads(NOTEBOOK.read_text())["cells"] if c["cell_type"] == "code"]
scope = {"display": lambda *a, **k: None, "__name__": "__main__"}
for cell in cells:
    exec("".join(cell["source"]), scope)

agents = {name: scope[name] for name in ("agent", "primary", "sleeper") if name in scope}
OUT.write_text(json.dumps({
    "calls": RECORD,
    "call_table": scope["CALLS"],
    "blocks": {name: {label: b.value for label, b in a.blocks.items()} for name, a in agents.items()},
    "recall": {name: [dict(m, time=m["time"].isoformat()) for m in a.recall] for name, a in agents.items()},
}, indent=1, ensure_ascii=False, default=str))
print(f"{len(RECORD)} calls, all from the cache; dump in {OUT}")
