"""The map: who writes the memory, against whether the read path inserts it all or selects.

The placements are the series' own (part 2's table): the systems run in the notebooks and the
experiment as cards, other systems and products as text.
"""

from __future__ import annotations

from ..kit import BOLD, ITALIC, M, MEDIUM, SANS, Box, Canvas, W, icon_tile, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme

NAME = "map"
TITLE = "A map of memory systems"
ALT = ("A map of memory systems on two axes: who writes the memory (nobody, a pipeline, the "
       "answering agent, a background process) and whether the read path inserts everything or "
       "selects. Nobody writes: full context inserts everything; plain retrieval, and Claude's "
       "and ChatGPT's search over past chats, select. A pipeline writes: Mem0 and Zep/Graphiti "
       "select. The answering agent writes: Letta's core memory blocks and ChatGPT's saved "
       "memories are inserted; Letta's archival store and Claude's API memory tool select. A "
       "background process writes: textual memory, Mastra's Observational Memory and ChatGPT's "
       "dreaming summary are inserted; Honcho selects.")

COLUMNS = [("layers", "Insert everything", "the whole memory goes into the prompt"),
           ("search", "Select", "a search picks part of it")]
# (who writes, what it means, [insert cell], [select cell]); a cell is
# ([(icon, system run in the series, how)], [other systems and products])
ROWS = [
    ("Nobody", "the raw history is the memory",
     ([("scroll-text", "Full context", "the whole history")], []),
     ([("search", "Plain retrieval", "BM25 over raw turns")],
      ["Claude's and ChatGPT's search over past chats"])),
    ("A pipeline", "extracts after each message or session",
     ([], []),
     ([("chart-scatter", "Mem0", "facts in a vector store"),
       ("network", "Zep / Graphiti", "dated facts in a graph")], [])),
    ("The answering agent", "edits memory with tool calls, mid-turn",
     ([("layers", "Letta", "core memory blocks")], ["ChatGPT's saved memories (2024)"]),
     ([], ["Letta's archival store", "Claude's API memory tool"])),
    ("A background process", "rewrites or reasons between conversations",
     ([("file-text", "Textual memory", "one profile, rewritten")],
      ["Mastra's Observational Memory", "ChatGPT's “dreaming” summary"]),
     ([("list", "Honcho", "conclusions at levels")], [])),
]

X_ROW, W_ROW = M, 178
GAP = 12
W_CELL = (W - M - (X_ROW + W_ROW + GAP) - GAP) / 2


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    s = t["store"]
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Two choices place every system: who writes the memory, and whether "
                       "the read path puts all of it into the prompt or selects part of it.",
                       W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30

    # the two axes, named once
    c.text(X_ROW, y + 12, "WHO WRITES", TINY, BOLD, t.muted, spacing=1.6)
    x0 = X_ROW + W_ROW + GAP
    c.text(x0, y - 4, "THE READ PATH", TINY, BOLD, t.muted, spacing=1.6)
    for i, (icon, name, meaning) in enumerate(COLUMNS):
        x = x0 + i * (W_CELL + GAP)
        icon_tile(c, x, y + 6, "prompt", icon, 26)
        c.text(x + 34, y + 19, name, SMALL + 1, BOLD, t["prompt"].ink)
        c.text(x + 34, y + 35, meaning, TINY, SANS, t.muted)
    y += 50

    for who, meaning, *cells in ROWS:
        layouts = [_cell_height(cell) for cell in cells]
        h = max(64, *layouts)
        c.line(X_ROW, y, W - M, y, t.line)
        c.text(X_ROW, y + 24, who, SMALL + 0.5, BOLD, t.ink)
        for i, line in enumerate(wrap(meaning, TINY, W_ROW - 10)):
            c.text(X_ROW, y + 42 + i * TINY * 1.35, line, TINY, SANS, t.muted)
        for i, cell in enumerate(cells):
            box = Box(x0 + i * (W_CELL + GAP), y + 8, W_CELL, h - 16)
            _cell(c, box, cell)
        y += h
    c.line(X_ROW, y, W - M, y, t.line)

    # the key
    y += 22
    icon_tile(c, M, y - 13, "store", "database", 18)
    x = M + 24 + c.text(M + 24, y, "run in this series, in the notebooks or the experiment", TINY, SANS, t.muted)
    c.text(x + 22, y, "Other systems and products, as described in the series", TINY, ITALIC, t.muted)
    c.height = int(y + 22)
    return c


def _cell_height(cell) -> float:
    systems, others = cell
    return 16 + len(systems) * 46 + sum(len(wrap(o, TINY, W_CELL - 24, ITALIC)) * TINY * 1.4 + 4
                                         for o in others) + (8 if others else 0) + 8


def _cell(c: Canvas, box: Box, cell) -> None:
    t = c.theme
    s = t["store"]
    systems, others = cell
    if not systems and not others:
        c.rect(box, fill=t.paper, stroke=t.line, r=10, dash="4 3")
        c.text(box.cx, box.cy + 4, "nothing here in the series", TINY, ITALIC, t.faint, anchor="middle")
        return
    c.rect(box, fill=s.wash if systems else t.surface, r=10)
    y = box.y + 8
    for icon, name, how in systems:
        card = Box(box.x + 6, y, box.w - 12, 40)
        c.rect(card, fill=t.card, r=8)
        icon_tile(c, card.x + 7, card.y + 7, "store", icon, 26)
        width = c.text(card.x + 42, card.y + 25, name, SMALL, BOLD, t.ink)
        c.text(card.x + 42 + width + 8, card.y + 25, how, TINY, SANS, t.muted)
        y += 46
    if others:
        y += 6
        for other in others:
            for line in wrap(other, TINY, box.w - 24, ITALIC):
                c.text(box.x + 12, y + TINY, line, TINY, ITALIC, t.muted)
                y += TINY * 1.4
            y += 4
