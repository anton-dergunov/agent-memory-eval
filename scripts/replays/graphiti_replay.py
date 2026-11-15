"""Replays for part 5 (Zep/Graphiti), against graphiti-core 0.31.1 and gemini-3.1-flash-lite.

Run from agent-memory-eval:  PYTHONPATH=notebooks .venv/bin/python <this file>

A. The step-4 comparison of the committed notebook run (graphiti-core 0.30), sent with the
   0.31.1 prompt, three times: does the stricter contradiction rule still close the old fact?
B. Step 3 for the first message with the three entities that the default entity prompt found,
   three times: does the fact step name an endpoint that is not in the list?
D. Name similarities behind the second node for the same person.
"""
import json
from datetime import datetime, timezone

import numpy as np
from config import embed, generate
from graphiti_core.prompts import dedupe_edges, extract_edges

REPEATS = 3


def call(messages, schema):
    reply = generate(messages[1].content, system=messages[0].content, schema=schema)
    return json.loads(reply.text)


print("A. the 0.30 run's comparison under the 0.31.1 prompt")
candidates = [
    "Anton has been strictly vegetarian for eight years.",
    "Anton has a sister who is visiting Berlin.",
    "Anton prefers Indian cuisine for his dinner plans.",
    "Anton has a severe anaphylactic peanut allergy.",
    "Anton specifically prefers paneer dishes when eating Indian cuisine.",
    "Anton has a budget of 40 euros a head for his dinner.",
]
for new_fact in ("Anton started following a pescatarian diet about a month ago.",):
    for i in range(REPEATS):
        print(" ", call(dedupe_edges.resolve_edge({
            "existing_edges": [],
            "edge_invalidation_candidates": [{"idx": j, "fact": f} for j, f in enumerate(candidates)],
            "new_edge": new_fact,
        }), dedupe_edges.EdgeDuplicate))

print("\nB. step 3 for s1.1 with the default entities")
message = ("Anton: I'm planning a dinner for my sister's visit to Berlin next week. Worth saying up front: "
           "I've been strictly vegetarian for eight years, and I have a severe peanut allergy — anaphylactic, "
           "not a preference.")
names = ["Anton", "Anton's sister", "Berlin"]
for i in range(REPEATS):
    reply = call(extract_edges.edge({
        "episode_content": message,
        "nodes": [{"name": n, "entity_types": ["Entity"]} for n in names],
        "previous_episodes": [],
        "reference_time": datetime(2026, 3, 14, 19, 0, tzinfo=timezone.utc),
        "edge_types": [],
        "custom_extraction_instructions": "",
    }), extract_edges.ExtractedEdges)
    for edge in reply["edges"]:
        outside = [n for n in (edge["source_entity_name"], edge["target_entity_name"]) if n not in names]
        print(f"  run {i + 1}: {edge['source_entity_name']} -[{edge['relation_type']}]-> {edge['target_entity_name']}"
              f" | {edge['fact']} | valid_at {edge.get('valid_at')}" + (f" | NOT IN LIST: {outside}" if outside else ""))

print("\nD. name similarities")
texts = ["Lena", "Anton's sister", "Anton's sister Lena", "Lena's partner Jonas"]
vectors = np.array(embed(texts))
vectors /= np.linalg.norm(vectors, axis=1, keepdims=True)
for text, vector in zip(texts[1:], vectors[1:]):
    print(f"  Lena ~ {text}: {float(vectors[0] @ vector):.3f}")
