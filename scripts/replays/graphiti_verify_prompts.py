"""Check every prompt block quoted in the part 5 draft against graphiti-core 0.31.1, ignoring line breaks.

Each ```text block that contains a known prompt anchor is normalised (whitespace collapsed,
[…] cuts allowed, {slot} placeholders matched against the rendered slot markers) and must be a
sequence of pieces that each appear, in order, in the library's prompt text.
"""
import re, sys
from graphiti_core.prompts import dedupe_edges, dedupe_nodes, extract_edges, extract_nodes

def render(fn, ctx):
    return "\n".join(m.content for m in fn(ctx))

M = lambda n: f"⟦{n}⟧"
sources = {
    "nodes": render(extract_nodes.extract_message, {"entity_types": M("entity_types"),
        "previous_episodes": [], "episode_content": M("episode_content"),
        "custom_extraction_instructions": M("custom_extraction_instructions")}).replace("[]", M("previous_episodes"), 1),
    "dedupe_nodes": render(dedupe_nodes.nodes, {"previous_episodes": M("previous_episodes"),
        "episode_content": M("episode_content"), "extracted_nodes": M("extracted_nodes"), "existing_nodes": M("existing_nodes")}),
    "edges": render(extract_edges.edge, {"previous_episodes": M("previous_episodes"), "episode_content": M("episode_content"),
        "nodes": M("nodes"), "reference_time": M("reference_time"), "edge_types": [],
        "custom_extraction_instructions": M("custom_extraction_instructions")}),
    "dedupe_edges": render(dedupe_edges.resolve_edge, {"existing_edges": M("existing_edges"),
        "edge_invalidation_candidates": M("edge_invalidation_candidates"), "new_edge": M("new_edge")}),
}
norm = lambda t: re.sub(r"\s+", " ", t.replace('"', '"')).strip()
for k in sources:
    src = norm(sources[k]).replace('"⟦', "⟦").replace('⟧"', "⟧")
    src = re.sub(r"ENTITIES contains \d+ entities with IDs 0 through \d+\.", "ENTITIES contains {n} entities with IDs 0 through {n-1}.", src)
    src = re.sub(r"Your response MUST include EXACTLY \d+ resolutions with IDs 0 through \d+\.", "Your response MUST include EXACTLY {n} resolutions with IDs 0 through {n-1}.", src)
    sources[k] = src

post = open(sys.argv[1]).read()
blocks = re.findall(r"```text\n(.*?)```", post, flags=re.S)
anchors = {"NEVER extract any of the following": "nodes", "You are an entity extraction specialist": "nodes",
           "Each of the above ENTITIES": "dedupe_nodes", "You are an entity deduplication assistant": "dedupe_nodes",
           "# EXTRACTION RULES": "edges", "You are an expert fact extractor": "edges",
           "DUPLICATE DETECTION": "dedupe_edges", "You are a fact deduplication assistant": "dedupe_edges"}
checked = 0
for b in blocks:
    key = next((v for a, v in anchors.items() if a in b), None)
    if not key:
        continue
    text = norm(b)
    text = re.sub(r"\{(\w+)\}", lambda m: f"⟦{m.group(1)}⟧" if m.group(1) not in ("n", "n-1") else m.group(0), text)
    pieces = [p.strip() for p in text.split("[…]") if p.strip()]
    pos, src = 0, sources[key]
    for piece in pieces:
        i = src.find(piece, pos)
        if i < 0:
            # find the first word where it diverges
            for n in range(len(piece), 0, -20):
                if src.find(piece[:n], pos) >= 0:
                    j = src.find(piece[:n], pos)
                    print(f"MISMATCH in {key}: after …{piece[max(0,n-60):n]}… post has «{piece[n:n+80]}» source has «{src[j+n:j+n+80]}»")
                    break
            else:
                print(f"MISMATCH in {key}: piece not found: {piece[:100]}")
            break
        pos = i + len(piece)
    else:
        print(f"ok: {key} ({len(text)} chars)")
    checked += 1
print("blocks checked:", checked)
