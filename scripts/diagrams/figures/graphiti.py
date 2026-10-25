"""Zep / Graphiti: four LLM steps turn each message into dated facts in a graph; a hybrid search reads them.

Every example below is from the committed run of notebooks/03-zep-graphiti.ipynb, shortened to fit:
the graph after session 2 (section 3, the facts table), the calls per step (section 7), the
default search and its answer (sections 4 and 6).
"""

from __future__ import annotations

from ..kit import (BOLD, MEDIUM, SANS, Box, Canvas, W, answer_card, arrow, bubble, column, footer, frame,
                   heading, measure, node, panel, prompt_card, segment)
from ..theme import TINY, Theme

NAME = "graphiti"
TITLE = "Zep / Graphiti"
ALT = ("Zep and Graphiti's architecture, with the running example. Writing: every message goes "
       "through four LLM steps (find entities, match them to stored ones, extract facts, compare "
       "with stored facts), 36 calls for ten messages. Memory: a graph of entities whose edges "
       "are facts with dates; the vegetarian edge was closed on 20 June 2026 and a pescatarian "
       "edge opened. Reading: a hybrid search with a 0.6 similarity floor returned nine facts, "
       "including the closed one; the pescatarian fact, Jonas's coeliac disease and Kreuzberg "
       "fell below the floor, so the answer missed the diet, gluten and the area.")

SESSION_1 = ("“I've been strictly vegetarian for eight years, and I have a severe peanut "
             "allergy … Indian, usually.”")
SESSION_2 = ("“So I'm pescatarian now, not vegetarian … I moved to Kreuzberg in May … Lena "
             "can't eat shellfish, and Jonas is coeliac.”")
QUESTION = ("“My sister and her partner are in town tonight. Book the three of us somewhere for "
            "dinner — you know what we can and can't eat.”")

# Model calls per step, over the ten messages of both sessions (section 7).
STEPS = [("Find entities", "×10"), ("Match to stored ones", "×7"),
         ("Extract dated facts", "×8"), ("Compare; close old facts", "×11")]

# Part of the graph after session 2 (section 3): entity, its centre, and its role when special.
ENTITIES = {
    "Anton": ((136, 150), "person"),
    "vegetarian": ((70, 28), "stale"),
    "pescatarian diet": ((200, 28), None),
    "Indian cuisine": ((54, 150), None),
    "peanut allergy": ((216, 150), None),
    "Kreuzberg": ((60, 222), None),
    "Anton's sister": ((196, 222), None),
    "Jonas": ((196, 274), None),
    "coeliac": ((100, 274), None),
}
# Edges drawn: (from, to, label on the edge, closed)
EDGES = [
    ("Anton", "vegetarian", "until 20 Jun", True),
    ("Anton", "pescatarian diet", "from 20 Jun", False),
    ("Anton", "Indian cuisine", None, False),
    ("Anton", "peanut allergy", None, False),
    ("Anton", "Kreuzberg", None, False),
    ("Anton", "Anton's sister", None, False),
    ("Anton's sister", "Jonas", None, False),
    ("Jonas", "coeliac", None, False),
]

# The default search, best first (section 4), and what fell below its floor.
HITS = [
    ("", "sister visiting Berlin", None), ("", "Lena: no shellfish", None),
    ("", "Indian cuisine", None), ("", "sister named Lena", None),
    ("", "40 € a head", None), ("", "assistant: fish is in", None),
    ("", "paneer dishes", None), ("", "vegetarian, ended", "stale"),
    ("", "peanut allergy", None),
]
FLOOR = ("The search drops facts that score under 0.6. The closed vegetarian fact passed, at "
         "0.608; the three below did not.", "stale")
MISSED = ["pescatarian 0.599", "Jonas: coeliac 0.596", "Kreuzberg 0.542"]

ANSWER = ("Will book a table for three: Indian with paneer, €40 a head, noting Anton's peanut "
          "allergy and that Lena eats no shellfish.")
NEEDS = [("diet", "old"), ("peanuts", "yes"), ("shellfish", "yes"), ("gluten", "no"),
         ("cuisine", "yes"), ("area", "no")]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, "Zep / Graphiti: facts with dates, in a graph", ALT)
    t = theme
    top = frame(
        c, "Zep / Graphiti",
        "Facts become edges between entities in a graph, each with the dates it was true. A "
        "contradicted fact is not deleted: it gets an end date.",
        captions={"write": "Turns a conversation into memory. Runs on every message, so it "
                            "can run in the background."})

    wx, ww = column("write")
    b1 = bubble(c, wx, top, ww, "March · session 1", SESSION_1)
    b2 = bubble(c, wx, b1.bottom + 14, ww, "July · session 2", SESSION_2)
    rx, rw = column("read")
    q = bubble(c, rx, top, rw, "September · session 3", QUESTION, target=True)

    row = max(b2.bottom, q.bottom) + 34
    ingest = node(
        c, wx, row, ww, "llm", "sparkles", "Ingest", api="add_episode()",
        body="Each message, one at a time, through four LLM steps:", steps=STEPS,
        tags=[{"text": "36 LLM calls, 10 messages", "role": "llm", "icon": "sparkles"}])
    search = node(
        c, rx, row, rw, "code", "search", "Hybrid search", api="search(question)",
        body="Ranks facts by shared words and by embedding, and drops those under a 0.6 "
             "similarity floor. A walk along the edges is optional.",
        tags=[{"text": "1 embedding per question", "role": "code", "icon": "chart-scatter"}])
    arrow(c, [(wx + 30, b2.bottom + 4), (wx + 30, ingest.y)], t["person"].accent)
    arrow(c, [(rx + 30, q.bottom + 4), (rx + 30, search.y)], t["person"].accent)

    sx, sw = column("store")
    store = _graph(c, sx, top, sw)

    y_write = ingest.y + 34
    arrow(c, [(ingest.right, y_write), (store.x, y_write)], t.ink, label="dated\nfacts")
    y_back = ingest.y + 110
    arrow(c, [(store.x, y_back), (ingest.right, y_back)], t.muted, dashed=True, label="stored\nones")
    y_read = search.y + 34
    arrow(c, [(store.right, y_read), (search.x, y_read)], t.muted, dashed=True, label="9 of 13\nfacts")

    band = max(ingest.bottom, search.bottom, store.bottom) + 30
    heading(c, wx, band, W - 2 * wx, "USE", "what the answering model is given, and what it replies")
    px = sx
    prompt = prompt_card(
        c, px, band + 22, W - wx - px,
        "Facts are valid between their valid_at and invalid_at dates.",
        [segment("what search() returned, each with its dates", HITS, columns=3, note=FLOOR,
                 missing=MISSED)], QUESTION)
    arrow(c, [(search.cx, search.bottom), (search.cx, prompt.y)], t.muted, dashed=True)
    answer = answer_card(c, wx, band + 22, ww, ANSWER, NEEDS)
    arrow(c, [(prompt.x, band + 22 + 13), (answer.right + 4, band + 22 + 13)], t["prompt"].accent)

    footer(c, max(prompt.bottom, answer.bottom) + 24,
           "Example from notebooks/03-zep-graphiti.ipynb, shortened")
    return c


def _graph(c: Canvas, x: float, y: float, w: float) -> Box:
    """A part of the graph: entities as pills, facts as edges, the diet edges with their dates;
    under it, the two diet facts on a line of time."""
    t = c.theme
    s, stale = t["store"], t["stale"]
    gy = y + 52
    graph_h = 316
    strip_h = 92
    box = panel(c, x, y, w, 52 + graph_h + strip_h, "network", "Temporal graph", "13 facts, 1 closed")

    def centre(name):
        (cx, cy), _ = ENTITIES[name]
        return x + cx, gy + cy

    # edges first, so the pills sit on top of them
    for a, b, label, closed in EDGES:
        (ax, ay), (bx, by) = centre(a), centre(b)
        colour = stale.accent if closed else s.accent
        c.line(ax, ay, bx, by, colour, 1.4, dash="4 3" if closed else None)
    for name, ((cx, cy), role) in ENTITIES.items():
        face = BOLD if role == "person" else MEDIUM
        tw = measure(name, TINY, face)
        pill = Box(x + cx - tw / 2 - 9, gy + cy - 11, tw + 18, 22)
        if role == "stale":
            c.rect(pill, fill=stale.wash, stroke=stale.accent, r=11, dash="3 2.5")
            ink = stale.ink
        elif role == "person":
            c.rect(pill, fill=t["person"].wash, stroke=t["person"].accent, r=11)
            ink = t["person"].ink
        else:
            c.rect(pill, fill=t.card, stroke=s.accent, r=11)
            ink = t.ink
        c.text(x + cx, gy + cy + 4.5, name, TINY, face, ink, anchor="middle")
        if role == "stale":
            c.line(pill.x + 7, gy + cy, pill.right - 7, gy + cy, stale.accent, 1.2)
    for a, b, label, closed in EDGES:
        if label:   # the dates go just under the entity the edge points to
            mx, my = centre(b)
            colour = stale.accent if closed else s.accent
            tw = measure(label, TINY, BOLD)
            c.rect(Box(mx - tw / 2 - 5, my + 14, tw + 10, 19), fill=s.wash, r=5)
            c.text(mx, my + 28, label, TINY, BOLD, colour, anchor="middle")
    c.text(x + 12, gy + graph_h - 4, "5 more facts not drawn", TINY, SANS, s.ink)

    # the two diet facts on a line of time
    ty = gy + graph_h + 6
    c.line(x + 12, ty, x + w - 12, ty, s.accent, 0.8)
    c.text(x + 12, ty + 20, "when each was true", TINY, BOLD, s.ink)
    left, right = x + 12, x + w - 12
    split = left + (right - left) * 0.6
    old = Box(left, ty + 30, split - left - 2, 20)
    new = Box(split + 2, ty + 30, right - split - 2, 20)
    c.rect(old, fill=stale.wash, stroke=stale.accent, r=5, dash="3 2.5")
    c.text(old.x + 8, old.y + 14, "vegetarian", TINY, MEDIUM, stale.ink)
    c.rect(new, fill=s.accent, r=5)
    c.text(new.x + 8, new.y + 14, "pescatarian", TINY, MEDIUM, t.paper)
    c.text(left, ty + 66, "2018", TINY, SANS, s.ink)
    c.text(split, ty + 66, "20 Jun 2026", TINY, SANS, s.ink, anchor="middle")
    c.text(right, ty + 66, "now", TINY, SANS, s.ink, anchor="end")
    return box
