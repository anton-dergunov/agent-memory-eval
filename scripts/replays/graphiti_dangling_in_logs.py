"""Check C for part 5: in the experiment's logged Graphiti calls (graphiti-core 0.31.1), how many
extracted facts name an endpoint that is not in the ENTITIES list of their own prompt?
0.31.1 keeps such a fact and creates the missing node; 0.30 dropped it. No model calls.

Run from agent-memory-eval:  .venv/bin/python <this file> <logged calls .jsonl> [...]
"""
import json
import re
import sys

seen, calls, edges, outside, examples = set(), 0, 0, 0, []
for path in sys.argv[1:]:
    for line in open(path):
        try:
            row = json.loads(line)
        except ValueError:
            continue
        text = json.dumps(row.get("request", row), ensure_ascii=False)
        if "<ENTITIES>" not in text or "# EXTRACTION RULES" not in text:
            continue
        reply = row.get("reply") or row.get("response") or ""
        key = hash((text, str(reply)))
        if key in seen:
            continue
        seen.add(key)
        match = re.search(r"<ENTITIES>\\n(.*?)\\n</ENTITIES>", text, flags=re.S)
        try:
            names = {n["name"].strip().lower() for n in json.loads(json.loads('"' + match.group(1) + '"'))}
            reply_edges = (json.loads(reply) if isinstance(reply, str) else reply)["edges"]
        except Exception:
            continue
        calls += 1
        for edge in reply_edges:
            edges += 1
            missing = [edge[k] for k in ("source_entity_name", "target_entity_name")
                       if edge[k].strip().lower() not in names]
            if missing:
                outside += 1
                if len(examples) < 8:
                    examples.append((missing, edge["fact"]))
print(f"fact-extraction calls: {calls}; facts: {edges}; with an endpoint outside the list: {outside}"
      f" ({outside / max(edges, 1):.1%})")
for missing, fact in examples:
    print("  ", missing, "|", fact)
