"""Zep / Graphiti: a walk along the graph from the entities the question names.

The graph is the one drawn by graphiti_graph.py, with only the facts still true in September
(the notebook's `current_graph`). The walk, its start and the positions in the table are the
committed run of notebooks/03-zep-graphiti.ipynb, section 5.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, SANS, Box, Canvas, W, M, chip, heading
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import draw_graph, source_line, type_key

NAME = "graphiti-walk"
TITLE = "A walk from the question's entities"
ALT = ("The graph after session 2, with only the facts still true in September. The question "
       "says 'my sister and her partner'; the entities whose names share a word with it are "
       "Anton's sister and Lena's partner Jonas, and both are ringed. Following edges from them "
       "for two steps reaches 'Lena is in a relationship with Jonas' and then 'Jonas has coeliac "
       "disease', drawn thick. The node Lena, which holds 'Lena cannot eat shellfish', is "
       "connected to nothing, so no walk reaches it. A table compares three ways of reading the "
       "same facts for the four facts the answer needs. Text search: the peanut allergy 10th, "
       "Lena's shellfish 4th, the new diet and Jonas's coeliac disease not returned. Text search "
       "then a walk from the entities those hits start at: the allergy 8th, shellfish 5th, the "
       "diet and coeliac not returned. A walk from the question's entities: only coeliac, 2nd.")

READINGS = [("Text search", "graphiti.search(): words and meaning"),
            ("Text search, then a walk", "from where the hits start, up to 3 steps"),
            ("A walk from the question's entities", "sister and partner, 2 steps")]
NEEDED = [("peanut allergy", ["10th", "8th", None]),
          ("the new diet (pescatarian)", [None, None, None]),
          ("Lena: no shellfish", ["4th", "5th", None]),
          ("Jonas: coeliac", [None, None, "2nd"])]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The question says “my sister and her partner”. Two stored entities "
                       "share a word with it. Two steps along the edges from them reach Jonas's "
                       "coeliac disease, a fact that shares no word with the question and scores "
                       "under the floor of the search.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30
    c.text(M, y, "The facts still true in September", SUBTITLE, BOLD)
    panel = draw_graph(c, M, y + 12, 2, drop_closed=True, faded=("vegetarian",),
                       starts=("Anton's sister", "Lena's partner Jonas"),
                       highlight=(("Anton's sister", "Lena's partner Jonas"),
                                  ("Lena's partner Jonas", "coeliac")))
    y = panel.bottom + 26
    t_ = t["prompt"]
    c.rect(Box(M, y - 11, 22, 14), stroke=t_.accent, r=5, width=1.6)
    x = M + 30 + c.text(M + 30, y, "where the walk starts", TINY, SANS, t.muted) + 18
    c.line(x, y - 4, x + 26, y - 4, t_.accent, 3.2)
    x += 34 + c.text(x + 34, y, "the facts it reaches", TINY, SANS, t.muted) + 18
    c.rect(Box(x, y - 11, 22, 14), fill=t.paper, stroke=t["stale"].accent, r=5, dash="3 2.5")
    c.text(x + 30, y, "an entity whose only fact has ended", TINY, SANS, t.muted)
    y += 22
    type_key(c, M, y)

    y += 40
    heading(c, M, y, W - 2 * M, "THREE WAYS TO READ THE SAME FACTS",
            "where each of the four facts the answer needs was placed")
    y += 30
    first = 220
    col = (W - 2 * M - first) / 3
    head_h = 0
    for i, (name, how) in enumerate(READINGS):
        x = M + first + i * col
        used = c.paragraph(x, y - SMALL, name, col - 14, SMALL, BOLD)
        used += c.paragraph(x, y - SMALL + used, how, col - 14, TINY, SANS, t.muted, 1.3)
        head_h = max(head_h, used)
    y += head_h - 4
    for fact, places in NEEDED:
        c.line(M, y, W - M, y, t.line)
        c.text(M, y + 23, fact, SMALL, MEDIUM)
        for i, place in enumerate(places):
            x = M + first + i * col
            if place:
                chip(c, x, y + 8, place, "store", icon="check", face=BOLD)
            else:
                chip(c, x, y + 8, "not returned", "stale", icon="x", outline=True)
        y += 36
    c.line(M, y, W - M, y, t.line)
    y += 8
    used = c.paragraph(M, y, "The shellfish fact is found only by text search, through the word "
                       "“eat”: it hangs on the second node for Lena, which no walk reaches. The new "
                       "diet is one step from Anton, but so are eight other facts still true, and it "
                       "is ranked behind them.", W - 2 * M, TINY, SANS, t.muted)
    source_line(c, y + used + 18, "From notebooks/03-zep-graphiti.ipynb, section 5")
    return c
