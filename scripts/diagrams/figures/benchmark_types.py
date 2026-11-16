"""LongMemEval's seven question types: the paper's Figure 1, with the type this experiment uses marked.

The image is Figure 1 of Wu et al. (ICLR 2025), CC BY 4.0, embedded unchanged
(images/longmemeval-fig1.png, see images/README.md). The highlight around the knowledge-update
panel is ours. The image keeps its white background in the dark theme too, on a card, because
it is a picture of a page.
"""

from __future__ import annotations

import base64

from ..kit import BOLD, HERE, SANS, Box, Canvas, W, M
from ..theme import SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "benchmark-types"
TITLE = "The seven question types of LongMemEval"
ALT = ("The paper's Figure 1: one example for each of LongMemEval's seven question types, each with "
       "the user's statements on the left and the question and answer on the right. "
       "Single-session-user: a 45-minute commute. Single-session-assistant: the restaurant the "
       "assistant recommended. Single-session-preference: Sony camera accessories. Temporal "
       "reasoning: months since a museum visit. Multi-session: how many instruments the user owns. "
       "Abstention: a 30-gallon tank never mentioned. Knowledge update, outlined: a family trip to "
       "Hawaii, then a later trip to Paris; the most recent family trip is Paris. Only "
       "knowledge-update questions are used in this experiment.")

IMAGE = HERE / "images" / "longmemeval-fig1.png"
SOURCE_W, SOURCE_H = 4278, 2830          # the size the panel's coordinates refer to
PANEL = (0, 1385, 2085, 2165)            # the knowledge-update panel: x0, y0, x1, y1


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "One example of each type, from the paper. This experiment uses only "
                       "the knowledge-update questions (outlined): a fact the user states and "
                       "later changes.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 22
    pad = 12
    width = W - 2 * M - 2 * pad
    scale = width / SOURCE_W
    height = SOURCE_H * scale
    c.rect(Box(M, y, W - 2 * M, height + 2 * pad), fill="#FFFFFF", stroke=t.line, r=10)
    data = base64.b64encode(IMAGE.read_bytes()).decode()
    c.add(f'<image x="{M + pad:.2f}" y="{y + pad:.2f}" width="{width:.2f}" height="{height:.2f}" '
          f'href="data:image/png;base64,{data}"/>')
    x0, y0, x1, y1 = PANEL
    hl = Box(M + pad + x0 * scale - 4, y + pad + y0 * scale - 4, (x1 - x0) * scale + 8, (y1 - y0) * scale + 8)
    colour = theme["prompt"].accent if theme.name == "light" else "#2F5D7C"
    c.rect(hl, stroke=colour, r=8, width=3)
    y += height + 2 * pad + 18
    c.text(M, y, "The outline is added; the figure is otherwise as published.", TINY, SANS, t.muted)
    source_line(c, y + 18, "Figure 1 of Wu et al., LongMemEval (ICLR 2025), CC BY 4.0")
    return c
