"""The frame every system figure fills in: write, memory, read, use, with nothing filled in.

The six operations are the ones named by the survey Rethinking Memory in LLM-based Agents
(consolidation, updating, indexing, forgetting, retrieval, condensation). The two questions
pinned to the write and read steps are the two axes of the series.
"""

from __future__ import annotations

from ..kit import (BOLD, ITALIC, SANS, Box, Canvas, W, answer_card, arrow, bubble, chips, column, footer,
                   frame, heading, icon_tile, node, panel, prompt_card, segment)
from ..theme import SMALL, TINY, Theme

NAME = "overview"
TITLE = "How a memory system works"
ALT = ("The loop every memory system in the series is built on. Write: a conversation is turned "
       "into memory (consolidation, updating), and the question is who writes: nobody, a "
       "pipeline, a background process or the answering agent. Memory: what is kept, in a shape "
       "that differs per system (a text profile, a list of facts, a dated graph, blocks in the "
       "prompt, conclusions at levels). Read: a new question gets what it needs (retrieval, "
       "condensation), and the question is whether everything is inserted or a search selects. "
       "Use: the answering model gets instructions, what memory returned, and the question.")

# Where the six operations are named (arXiv 2505.00675).
CITATION = [("Operations as named in Du et al., ", SANS),
            ("Rethinking Memory in LLM based Agents: Representations, Operations, and Emerging "
             "Topics", ITALIC), (", 2025", SANS)]

# The shape of the memory in each system of the series, in the order of the parts.
SHAPES = [
    ("file-text", "a text profile", "Textual memory"),
    ("chart-scatter", "a list of facts", "Mem0"),
    ("network", "a graph with dates", "Zep / Graphiti"),
    ("layers", "blocks in the prompt", "Letta"),
    ("list", "conclusions at levels", "Honcho"),
]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, "How a memory system works", ALT)
    t = theme
    top = frame(
        c, "How a memory system works",
        "Every system in this series is the same loop around a model that does not change: "
        "write, keep, read, use. They differ in what fills each slot.")

    wx, ww = column("write")
    b1 = bubble(c, wx, top, ww, "a session", "“… what the user says, and what the assistant "
                "replies …”")
    rx, rw = column("read")
    q = bubble(c, rx, top, rw, "a later session", "“A new question, with no transcript in "
               "front of the assistant.”", target=True)

    row = max(b1.bottom, q.bottom) + 34
    write = node(
        c, wx, row, ww, "code", "pencil", "Decide what to keep", badge=False,
        body="Consolidation turns the conversation into candidate memories. Updating adds, "
             "merges, replaces or ignores each one.")
    read = node(
        c, rx, row, rw, "code", "search", "Select and condense", badge=False,
        body="Retrieval finds what the question needs. Condensation makes it short enough for "
             "the prompt.")
    arrow(c, [(wx + 30, b1.bottom + 4), (wx + 30, write.y)], t["person"].accent)
    arrow(c, [(rx + 30, q.bottom + 4), (rx + 30, read.y)], t["person"].accent)
    w_q = _question(c, wx, write.bottom + 14, ww, "Who writes?",
                    "nobody · a pipeline · a background process · the answering agent")
    r_q = _question(c, rx, read.bottom + 14, rw, "Insert all, or select?",
                    "the whole memory goes in, or a search picks part of it")

    sx, sw = column("store")
    store = _shapes(c, sx, top, sw, max(w_q.bottom, r_q.bottom) - top)

    arrow(c, [(write.right, write.y + 34), (store.x, write.y + 34)], t.ink, label="writes")
    arrow(c, [(store.right, read.y + 34), (read.x, read.y + 34)], t.muted, dashed=True, label="reads")

    band = max(w_q.bottom, r_q.bottom, store.bottom) + 30
    heading(c, wx, band, W - 2 * wx, "USE", "what the answering model is given, and what it replies")
    px = sx
    prompt = prompt_card(
        c, px, band + 22, W - wx - px, "The instructions.",
        [segment("what memory returned",
                 "A profile, some facts, some conclusions: whatever the read step selected, and "
                 "nothing else from the past.")], "“The new question.”")
    arrow(c, [(r_q.cx, r_q.bottom), (r_q.cx, prompt.y)], t.muted, dashed=True)
    answer = answer_card(c, wx, band + 22, ww, "The reply, which becomes part of the next "
                         "conversation, and so of what is written next.")
    arrow(c, [(prompt.x, band + 22 + 13), (answer.right + 4, band + 22 + 13)], t["prompt"].accent)
    # the loop closes: the answer goes back into the conversation, up the left margin
    ay = band + 22 + 13
    arrow(c, [(wx - 4, ay + 26), (14, ay + 26), (14, b1.y + 50), (wx, b1.y + 50)],
          t["person"].accent, radius=8, width=1.2)
    footer(c, max(prompt.bottom, answer.bottom) + 24, CITATION)
    return c


def _question(c: Canvas, x: float, y: float, w: float, question: str, options: str) -> Box:
    """One of the two choices that separate the systems, pinned under the step it is about."""
    t = c.theme
    r = t["both"]
    lines = options
    from ..kit import wrap
    wrapped = wrap(lines, TINY, w - 24, ITALIC)
    box = Box(x, y, w, 34 + len(wrapped) * TINY * 1.35 + 8)
    c.rect(box, fill=r.wash, r=10)
    c.text(x + 12, y + 21, question, SMALL, BOLD, r.ink)
    for i, line in enumerate(wrapped):
        c.text(x + 12, y + 38 + i * TINY * 1.35, line, TINY, ITALIC, r.ink)
    return box


def _shapes(c: Canvas, x: float, y: float, w: float, h: float) -> Box:
    """The memory slot, with the shape it takes in each system of the series."""
    t = c.theme
    s = t["store"]
    box = panel(c, x, y, w, h, "database", "Memory", "a different shape in each")
    yy = y + 50
    for icon, shape, system in SHAPES:
        card = Box(x + 6, yy, w - 12, 44)
        c.rect(card, fill=t.card, r=8)
        icon_tile(c, card.x + 8, card.y + 8, "store", icon, 28)
        c.text(card.x + 46, card.y + 19, shape, SMALL, BOLD, t.ink)
        c.text(card.x + 46, card.y + 35, system, TINY, SANS, t.muted)
        yy += 50
    yy += 4
    c.text(x + 12, yy + 12, "Indexing builds what a read will use.", TINY, ITALIC, s.ink)
    c.text(x + 12, yy + 30, "Forgetting drops or decays entries.", TINY, ITALIC, s.ink)
    return Box(box.x, box.y, box.w, max(box.h, yy + 40 - y))
