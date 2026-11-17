"""When the cost of a memory is paid: once per conversation on the write path, or on every request on the read path.

Schematic: the bar heights are made up and show only the shape. Full context writes nothing and
reads the whole, growing history on every request. A write-heavy design (an extraction pipeline,
a graph) spends model calls after each conversation and puts a short, steady selection into each
prompt. A rewritten profile spends one call per conversation and inserts a profile that stays
about the same size.
"""

from __future__ import annotations

from ..kit import BOLD, ITALIC, MEDIUM, SANS, Box, Canvas, W, M
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "cost-timing"
TITLE = "When the cost is paid"
ALT = ("A schematic of cost over eight conversations, for three designs. Full context writes nothing; on "
       "every request it reads the whole history, so the cost of each request grows with every "
       "conversation. A write-heavy memory, such as an extraction pipeline or a graph, pays for several "
       "model calls after each conversation, in the background, and puts a short selection of about the "
       "same size into every prompt. A rewritten profile pays for one call after each conversation and "
       "inserts a profile that stays about the same size. Write costs are paid once and can wait; read "
       "costs are paid on every request while the user waits.")

N = 8
LANES = [
    ("Full context", "nothing is written; the whole history is read",
     [0] * N, [0.12 * (i + 1) for i in range(N)]),
    ("A write-heavy memory", "extraction or a graph; a short selection is read",
     [0.62, 0.7, 0.58, 0.66, 0.6, 0.72, 0.64, 0.68], [0.14] * N),
    ("A rewritten profile", "one call per conversation; the profile is inserted",
     [0.22] * N, [0.18, 0.2, 0.21, 0.22, 0.22, 0.23, 0.23, 0.23]),
]
X0 = M + 210
LANE_H = 112


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    wr, rd = t["llm"], t["prompt"]
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Work on the write path is paid once per conversation and can run in the "
                       "background. Work on the read path is paid on every request, while the user waits.",
                       W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30
    slot = (W - M - X0) / N
    for i in range(N):
        c.text(X0 + i * slot + slot / 2, y, str(i + 1), TINY, MEDIUM, t.muted, anchor="middle")
    c.text(X0 - 12, y, "conversation", TINY, SANS, t.muted, anchor="end")
    y += 12
    for name, how, writes, reads in LANES:
        c.rect(Box(M, y, W - 2 * M, LANE_H), fill=t.surface, r=10)
        c.text(M + 12, y + 26, name, SMALL, BOLD, t.ink)
        for k, line in enumerate((how[:how.index(";") + 1], how[how.index(";") + 2:])):
            c.text(M + 12, y + 46 + k * 17, line, TINY, SANS, t.muted)
        base = y + LANE_H - 14
        top = y + 12
        c.line(X0, base, W - M - 8, base, t.line, 1.2)
        for i in range(N):
            x = X0 + i * slot + slot / 2
            hw = (base - top) * writes[i]
            hr = (base - top) * reads[i]
            if hw:
                c.rect(Box(x - 15, base - hw, 13, hw), fill=wr.accent, r=2, opacity=0.85)
            c.rect(Box(x + 2, base - hr, 13, hr), fill=rd.accent, r=2)
        y += LANE_H + 12
    y += 10
    c.rect(Box(M, y - 11, 14, 14), fill=wr.accent, r=2, opacity=0.85)
    x = M + 20 + c.text(M + 20, y, "write: after the conversation, in the background", TINY, SANS, t.muted) + 22
    c.rect(Box(x, y - 11, 14, 14), fill=rd.accent, r=2)
    c.text(x + 20, y, "read: on the request, while the user waits", TINY, SANS, t.muted)
    source_line(c, y + 16, "Schematic; heights show the shape only")
    return c
