"""Mem0: an LLM extracts short facts into a vector store; a similarity search reads them.

Every example below is from the committed run of notebooks/mem0.ipynb, shortened to fit:
the stored facts from section 1 and 2 (the `add()` results and the store dump), the scores
from section 3, the answer from "Does it change the answer?".
"""

from __future__ import annotations

from ..kit import (BOLD, SANS, Box, Canvas, W, answer_card, arrow, bubble, chip, column, footer, frame,
                   heading, node, prompt_card, vector_strip)
from ..theme import SMALL, TINY, Theme

NAME = "mem0"
TITLE = "Mem0"
ALT = ("Mem0's architecture, with the running example. Writing: after each session, an LLM "
       "call extracts short standalone facts, seeing the related facts already stored, and "
       "only adds. Memory: a vector store of nine facts; the old and the new diet are both "
       "kept. Reading: a similarity search embeds the question and returns all nine facts, "
       "which go into the prompt; the answer covers every constraint.")

SESSION_1 = ("“I've been strictly vegetarian for eight years, and I have a severe peanut "
             "allergy … Indian, usually.”")
SESSION_2 = ("“So I'm pescatarian now, not vegetarian … I moved to Kreuzberg in May … Lena "
             "can't eat shellfish, and Jonas is coeliac.”")
QUESTION = ("“My sister and her partner are in town tonight. Book the three of us somewhere for "
            "dinner — you know what we can and can't eat.”")

# The store after both sessions, in the order the facts were added (section 2, the dump),
# each cut to a line, grouped by the session that added them. The two facts about the diet
# are tagged: both are still live.
FACTS = [
    ("added in March · session 1", [
        ("Dinner for their sister's visit", None),
        ("Strict vegetarian, eight years", "old, still live"),
        ("Severe peanut allergy", None),
        ("Likes Indian, paneer dishes", None),
        ("Budget about 40 € a head", None),
    ]),
    ("added in July · session 2", [
        ("Now pescatarian", "new"),
        ("Moved to Kreuzberg in May", None),
        ("Sister Lena: no shellfish", None),
        ("Her partner Jonas: coeliac", None),
    ]),
]

# What search() returned for the question, best first (section 3).
HITS = [
    ("0.74", "Lena: shellfish", None), ("0.73", "Jonas: coeliac", None),
    ("0.73", "dinner plan", None), ("0.66", "40 € a head", None),
    ("0.62", "Kreuzberg", None), ("0.62", "Indian, paneer", None),
    ("0.61", "peanut allergy", None), ("0.59", "vegetarian", "both"),
    ("0.59", "pescatarian", "both"),
]

ANSWER = ("Booked Chutnify in Kreuzberg: Indian, within 40 € a head, with the peanut and "
          "shellfish allergies and gluten-free passed on.")
NEEDS = [("diet", "both"), ("peanuts", "yes"), ("shellfish", "yes"), ("gluten", "yes"),
         ("cuisine", "yes"), ("area", "yes")]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, "Mem0: facts in a vector store", ALT)
    t = theme
    top = frame(
        c, "Mem0",
        "A conversation becomes a list of short standalone facts in a vector store. An LLM "
        "extracts them; a similarity search finds them again.")

    # ---- write: the two sessions, then the extractor
    wx, ww = column("write")
    b1 = bubble(c, wx, top, ww, "March · session 1", SESSION_1)
    b2 = bubble(c, wx, b1.bottom + 14, ww, "July · session 2", SESSION_2)

    # ---- read: the question, then the search
    rx, rw = column("read")
    q = bubble(c, rx, top, rw, "September · session 3", QUESTION, target=True)

    row = max(b2.bottom, q.bottom) + 34
    extractor = node(
        c, wx, row, ww, "llm", "sparkles", "Extractor", api="add(messages)",
        body="Distils the session into short standalone facts. It only adds: nothing stored "
             "is ever updated or deleted.",
        tags=[{"text": "1 LLM call per session", "role": "llm", "icon": "sparkles"}])
    search = node(
        c, rx, row, rw, "code", "search", "Similarity search", api="search(question)",
        body="Embeds the question and ranks the facts by how close their embeddings are.",
        tags=[{"text": "1 embedding per question", "role": "code", "icon": "chart-scatter"}])
    arrow(c, [(wx + 30, b2.bottom + 4), (wx + 30, extractor.y)], t["person"].accent)
    arrow(c, [(rx + 30, q.bottom + 4), (rx + 30, search.y)], t["person"].accent)

    # ---- memory: the vector store
    sx, sw = column("store")
    store = _store(c, sx, top, sw)

    # extractor -> store, and the related facts it is shown
    y_write = extractor.y + 34
    arrow(c, [(extractor.right, y_write), (store.x, y_write)], t.ink, label="new\nfacts")
    y_back = extractor.y + 92
    arrow(c, [(store.x, y_back), (extractor.right, y_back)], t.muted, dashed=True, label="related\nfacts")
    # store -> search
    y_read = search.y + 34
    arrow(c, [(store.right, y_read), (search.x, y_read)], t.muted, dashed=True, label="all 9\nfacts")

    # ---- use: the prompt under the memory and the read side, the answer back on the left
    band = max(extractor.bottom, search.bottom, store.bottom) + 30
    heading(c, wx, band, W - 2 * wx, "USE", "what the answering model is given, and what it replies")
    px = sx
    prompt = prompt_card(
        c, px, band + 22, W - wx - px, "You are a booking assistant. Be brief and concrete.",
        "what search() returned, closest first", HITS, QUESTION, columns=3)
    arrow(c, [(search.cx, search.bottom), (search.cx, prompt.y)], t.muted, dashed=True)
    answer = answer_card(c, wx, band + 22, ww, ANSWER, NEEDS)
    arrow(c, [(prompt.x, band + 22 + 13), (answer.right + 4, band + 22 + 13)], t["prompt"].accent)

    footer(c, max(prompt.bottom, answer.bottom) + 24, "Example from notebooks/mem0.ipynb, shortened")
    return c


def _store(c: Canvas, x: float, y: float, w: float) -> Box:
    """The vector store: each fact as one row with its embedding, under the session that added it."""
    t = c.theme
    s, both = t["store"], t["both"]
    pad = 12
    text_x = 44
    rows, h = [], 48
    for when, facts in FACTS:
        rows.append((when, None, h, 0))
        h += 22
        for text, tag in facts:
            row_h = 30 + (24 if tag else 0)
            rows.append((text, tag, h, row_h))
            h += row_h + 5
    box = Box(x, y, w, h + 3)
    c.rect(box, fill=s.wash, r=14)
    c.icon("database", x + pad, y + 13, 18, s.accent, stroke=1.7)
    c.text(x + pad + 26, y + 27, "Vector store", 15, BOLD, s.ink)
    count = sum(len(facts) for _, facts in FACTS)
    c.text(x + w - pad, y + 27, f"{count} facts", TINY, SANS, s.ink, anchor="end")
    for text, tag, ry, row_h in rows:
        if not row_h:   # a session's heading
            c.text(x + pad, y + ry + 13, text, TINY, SANS, s.ink)
            continue
        card = Box(x + 6, y + ry, w - 12, row_h)
        c.rect(card, fill=t.card, stroke=both.accent if tag else None, r=8, width=1.3)
        vector_strip(c, card.x + 8, card.y + 9, text, both.accent if tag else s.accent)
        c.text(card.x + text_x, card.y + 20, text, SMALL, SANS, t.ink)
        if tag:
            chip(c, card.x + text_x, card.bottom - 27, tag, "both", icon="history")
    return box
