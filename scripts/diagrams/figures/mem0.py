"""Mem0: an extractor writes short facts to a vector store; a similarity search reads them.

Every example below is from the committed run of notebooks/mem0.ipynb, shortened to fit:
the stored facts from section 1 and 2 (the `add()` results and the store dump), the scores
from section 3, the answer from "Does it change the answer?".
"""

from __future__ import annotations

from ..kit import (BOLD, SANS, Box, Canvas, W, answer_card, arrow, bubble, chip, column, footer, frame,
                   heading, node, prompt_card, vector_strip, wrap)
from ..theme import SMALL, TINY, Theme

NAME = "mem0"
TITLE = "Mem0"
ALT = ("Mem0's architecture, with the running example. Writing: each session goes to an "
       "extractor, one model call per add(), which sees related stored facts and returns new "
       "facts to add. Memory: a vector store of nine short facts; the old and the new diet are "
       "both kept. Reading: the question is embedded and every fact is scored; all nine go "
       "into the prompt, and the answer covers every constraint.")

SESSION_1 = ("“I've been strictly vegetarian for eight years, and I have a severe peanut "
             "allergy … Indian, usually.”")
SESSION_2 = ("“So I'm pescatarian now, not vegetarian … I moved to Kreuzberg in May … Lena "
             "can't eat shellfish, and Jonas is coeliac.”")
QUESTION = ("“My sister and her partner are in town tonight. Book the three of us somewhere for "
            "dinner — you know what we can and can't eat.”")

# The store after both sessions, in the order the facts were added (section 2, the dump).
# The two facts about the diet are tagged: both are still live.
FACTS = [
    ("session 1", [
        ("Planning a dinner in Berlin for their sister's visit", None),
        ("Strict vegetarian for eight years", "old, still live"),
        ("Severe, anaphylactic peanut allergy", None),
        ("Prefers Indian cuisine, paneer dishes", None),
        ("Budget about 40 euros per person", None),
    ]),
    ("session 2", [
        ("Now pescatarian: eats fish, no other meat", "new"),
        ("Moved to Kreuzberg in May; likes walkable places", None),
        ("Sister Lena has a shellfish allergy", None),
        ("Lena's partner Jonas is coeliac", None),
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
        "A conversation becomes a list of short standalone facts in a vector store. Writing "
        "is one model call per add(); reading is a similarity search.",
        write=[{"text": "a pipeline", "icon": "list"}, {"text": "on every add()", "icon": "clock"}],
        store=[{"text": "a flat list of facts, embedded", "icon": "chart-scatter"}],
        read=[{"text": "selects by similarity", "icon": "search"},
              {"text": "while the user waits", "icon": "clock"}],
    )

    # ---- write: the two sessions, then the extractor
    wx, ww = column("write")
    b1 = bubble(c, wx, top, ww, "14 March · session 1", SESSION_1)
    b2 = bubble(c, wx, b1.bottom + 14, ww, "20 July · session 2", SESSION_2)

    # ---- read: the question, then the search
    rx, rw = column("read")
    q = bubble(c, rx, top, rw, "September · session 3", QUESTION)

    row = max(b2.bottom, q.bottom) + 34
    extractor = node(
        c, wx, row, ww, "llm", "sparkles", "Extractor", api="add(messages)",
        body="Reads the new messages and the stored facts that look related. Returns new "
             "facts to add; it never updates or deletes one.",
        tags=[{"text": "1 model call per add()", "role": "llm", "icon": "sparkles"},
              {"text": "2 embeddings", "role": "code", "icon": "chart-scatter"}])
    search = node(
        c, rx, row, rw, "code", "search", "Similarity search", api="search(question)",
        body="Embeds the question and scores every fact by cosine. Asked for 6, it returned "
             "all 9: limit is not a cap.",
        tags=[{"text": "1 embedding", "role": "code", "icon": "chart-scatter"},
              {"text": "no model call", "role": "code", "icon": "code-xml"}])
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
    arrow(c, [(store.right, y_read), (search.x, y_read)], t.muted, dashed=True, label="all 9,\nscored")

    # ---- use: the prompt under the memory and the read side, the answer back on the left
    band = max(extractor.bottom, search.bottom, store.bottom) + 30
    heading(c, wx, band, W - 2 * wx, "USE", "what the answering model is given, and what it replies")
    px = sx
    prompt = prompt_card(
        c, px, band + 22, W - wx - px, "You are a booking assistant. Be brief and concrete.",
        "what search() returned, best first", HITS, QUESTION, columns=3)
    arrow(c, [(search.cx, search.bottom), (search.cx, prompt.y)], t.muted, dashed=True)
    answer = answer_card(c, wx, band + 22, ww, ANSWER, NEEDS)
    arrow(c, [(prompt.x, band + 22 + 13), (answer.right + 4, band + 22 + 13)], t["prompt"].accent)

    footer(c, max(prompt.bottom, answer.bottom) + 24, "Example from notebooks/mem0.ipynb, shortened")
    return c


def _store(c: Canvas, x: float, y: float, w: float) -> Box:
    """The vector store: each fact as one row with its embedding, grouped by the session that added it."""
    t = c.theme
    s, both = t["store"], t["both"]
    pad = 12
    text_x, text_w = 44, w - 12 - 44 - 10
    # lay the rows out first, to know how tall the store is
    layout, h = [], 46
    for session, facts in FACTS:
        h += 22
        for text, tag in facts:
            lines = wrap(text, SMALL, text_w)
            row_h = 12 + len(lines) * SMALL * 1.32 + (22 if tag else 0)
            layout.append((session, text, tag, lines, h, row_h))
            h += row_h + 5
    box = Box(x, y, w, h + 2)
    c.rect(box, fill=s.wash, r=14)
    c.icon("database", x + pad, y + 13, 18, s.accent, stroke=1.7)
    c.text(x + pad + 26, y + 27, "Vector store", 15, BOLD, s.ink)
    c.text(x + w - pad, y + 27, "9 facts", TINY, SANS, s.ink, anchor="end")
    seen = set()
    for session, text, tag, lines, ry, row_h in layout:
        if session not in seen:
            seen.add(session)
            c.text(x + pad, y + ry - 10, f"added in {session}", TINY, SANS, s.ink)
        card = Box(x + 6, y + ry, w - 12, row_h)
        c.rect(card, fill=t.card, stroke=both.accent if tag else None, r=8, width=1.3)
        vector_strip(c, card.x + 8, card.y + 9, text, both.accent if tag else s.accent)
        for i, line in enumerate(lines):
            c.text(card.x + text_x, card.y + 6 + SMALL + i * SMALL * 1.32, line, SMALL, SANS, t.ink)
        if tag:
            chip(c, card.x + text_x, card.bottom - 26, tag, "both", icon="history")
    return box
