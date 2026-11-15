"""Zep / Graphiti: how a name in a new message is matched to a stored entity.

The two names are from the committed run of notebooks/03-zep-graphiti.ipynb: "Anton's sister
Lena" in message s2.5 and "Lena" in s2.7. The scores are the cosine similarities of the name's
embedding to each stored entity's (section 5 prints those for "Lena"; the ones for "Anton's
sister Lena" come from the same run's cached embeddings). Only entities stored before the
message are shown.
"""

from __future__ import annotations

from ..kit import BOLD, ITALIC, SANS, Box, Canvas, W, M, chip, heading
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_floor import score_bars
from .graphiti_graph import source_line

NAME = "graphiti-matching"
TITLE = "Matching a name to a stored entity"
ALT = ("How Graphiti decides whether a name in a new message is an entity it already has. Names "
       "that are not stored exactly are compared by the cosine similarity of their embeddings, "
       "and only stored entities scoring at least 0.6 are shown to the model. Left, 'Anton's "
       "sister Lena' in July: Anton's sister scores 0.882 and Anton 0.756, both are shown, and the "
       "model says it is Anton's sister. Right, plain 'Lena' two messages later: Lena's partner "
       "Jonas 0.787 and Anton 0.608 are shown; Assistant 0.5997 and Anton's sister 0.5949 fall "
       "just under the floor. The model rightly says Lena is neither Jonas nor Anton, so a new, "
       "second node for Lena is made, and 'Lena cannot eat shellfish' is stored on it.")

CASES = [
    ("“my sister Lena is coming back in the autumn”", "Anton's sister Lena",
     [("Anton's sister", .882), ("Anton", .756), ("Assistant", .569), ("Berlin", .557),
      ("vegetarian", .531), ("Kreuzberg", .529)],
     "The model is shown the two over the floor and picks Anton's sister.",
     ("same node: Anton's sister", "store", "check")),
    ("“Lena can't eat shellfish, and Jonas is coeliac”", "Lena",
     [("Lena's partner Jonas", .7867), ("Anton", .6081), ("Assistant", .5997),
      ("Anton's sister", .5949), ("Berlin", .594), ("Kreuzberg", .574)],
     "The model is shown Jonas and Anton, and rightly says Lena is neither. Anton's sister was "
     "never shown.",
     ("a second node for Lena", "stale", "x")),
]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "A name that is not stored exactly is compared with every stored "
                       "entity's name by embedding. Only those scoring at least 0.6 are shown to the "
                       "model, which decides if one of them is the same thing. The rest are never "
                       "considered.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30
    gap = 30
    cw = (W - 2 * M - gap) / 2
    bottoms = []
    for i, (said, name, rows, verdict, (result, role, icon)) in enumerate(CASES):
        x = M + i * (cw + gap)
        yy = y
        c.text(x, yy, "20 July, message " + ("5" if i == 0 else "7"), TINY, BOLD, t["person"].accent)
        yy += 6 + c.paragraph(x, yy + 4, said, cw, SMALL, ITALIC, t["person"].ink)
        c.text(x, yy + 18, "the name found:", TINY, SANS, t.muted)
        chip(c, x + 104, yy + 5, name, "person", face=BOLD)
        yy += 64
        bars = [(n, s, s >= 0.6, s < 0.6, None) for n, s in rows]
        yy += score_bars(c, x, yy, cw, bars, 0.5, 0.9, 0.6, 128, digits=3 if i == 0 else 4, row_h=26)
        yy += 6
        yy += c.paragraph(x, yy, verdict, cw, TINY, SANS, t.muted) + 8
        chip(c, x, yy, result, role, icon=icon, face=BOLD)
        bottoms.append(yy + 30)
    y = max(bottoms) + 20
    heading(c, M, y, W - 2 * M, "WHY “LENA” MISSED")
    y += 10
    used = c.paragraph(M, y, "A first name alone carries little meaning for an embedding: “Lena” "
                       "is about as close to “Berlin” as to “Anton's sister”. The stored node kept "
                       "its old name, “Anton's sister”, when it was matched to “Anton's sister Lena” "
                       "(0.779 against “Lena”), so the name that would have matched was never "
                       "stored.", W - 2 * M, TINY, SANS, t.muted)
    source_line(c, y + used + 20, "From notebooks/03-zep-graphiti.ipynb, sections 3 and 5")
    return c
