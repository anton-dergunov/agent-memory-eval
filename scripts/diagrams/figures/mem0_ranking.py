"""Mem0: the order in which a search returns the example's nine facts.

Column 1 is the scored list from the committed run of notebooks/02-mem0.ipynb (section 3).
Columns 2 and 3 are from a replay that stored the same nine facts and searched them again
(the similarity scores came out the same to three decimals): column 2 with the library's
keyword scoring switched on (the `nlp` extra and fastembed), column 3 for another question,
whose first three rows are also in the notebook.
"""

from __future__ import annotations

from ..kit import BOLD, SANS, Box, Canvas, W, M, heading, measure, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme

NAME = "mem0-ranking"
TITLE = "The order the search returns"
ALT = ("Three ranked lists of the same nine stored facts, each with a line after the sixth row. "
       "First list, the example's question scored by embedding similarity only: Lena and "
       "shellfish 0.740, Jonas and coeliac 0.732, the dinner plan 0.725, the budget 0.663, "
       "Kreuzberg 0.623, Indian food 0.616, then below the line the peanut allergy 0.612, the "
       "replaced fact 'strict vegetarian' 0.589 and the fact that replaced it 0.588. Second "
       "list, the same question with keyword scores added: Jonas 0.553, the dinner plan 0.480, "
       "Lena 0.392, the budget 0.366, the fact that replaced the old one 0.357, Kreuzberg 0.312, "
       "then below the line Indian food 0.308, the peanut allergy 0.306 and the replaced fact "
       "0.295. Third list, the question 'what should I cook tonight?': Indian food 0.607, the "
       "budget 0.586, the dinner plan 0.564, Kreuzberg 0.564, Lena 0.550, the replaced fact "
       "0.545, then below the line the fact that replaced it 0.542, Jonas 0.524 and the peanut "
       "allergy 0.509, in last place.")

FACTS = {
    "lena": ("Lena … has a shellfish allergy", None),
    "jonas": ("Jonas … has coeliac disease", None),
    "dinner": ("planning a dinner in Berlin", None),
    "budget": ("about 40 euros per person", None),
    "kreuzberg": ("relocated to Kreuzberg", None),
    "indian": ("prefers Indian cuisine", None),
    "peanut": ("severe … peanut allergy", "both"),
    "old": ("strict vegetarian for eight years", "stale"),
    "new": ("transitioned … to pescatarian", "store"),
}
COLUMNS = [
    ("The example's question", "similarity only, as in the notebook",
     [("lena", .740), ("jonas", .732), ("dinner", .725), ("budget", .663), ("kreuzberg", .623),
      ("indian", .616), ("peanut", .612), ("old", .589), ("new", .588)]),
    ("The same question", "with keyword scores added",
     [("jonas", .553), ("dinner", .480), ("lena", .392), ("budget", .366), ("new", .357),
      ("kreuzberg", .312), ("indian", .308), ("peanut", .306), ("old", .295)]),
    ("“What should I cook tonight?”", "similarity only",
     [("indian", .607), ("budget", .586), ("dinner", .564), ("kreuzberg", .564), ("lena", .550),
      ("old", .545), ("new", .542), ("jonas", .524), ("peanut", .509)]),
]
GAP = 22
ROW = 30
CUT = 6


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The same nine stored facts, ranked three times. A caller that "
                       "keeps the first six gets a different six each time, and the hard "
                       "constraint is never among them.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 32
    cw = (W - 2 * M - 2 * GAP) / 3
    top = y
    for i, (name, how, rows) in enumerate(COLUMNS):
        x = M + i * (cw + GAP)
        yy = top
        for line in wrap(name, SMALL, cw, BOLD):
            c.text(x, yy, line, SMALL, BOLD)
            yy += SMALL * 1.3
        c.text(x, yy, how, TINY, SANS, t.muted)
        yy = top + SMALL * 1.3 + 30
        for rank, (key, score) in enumerate(rows, 1):
            label, role = FACTS[key]
            if rank == CUT + 1:
                c.line(x, yy + 1, x + cw, yy + 1, t["stale"].accent, 1.4, dash="5 4")
                c.text(x + cw, yy + 14, "a cut at six", TINY, BOLD, t["stale"].accent, anchor="end")
                yy += 22
            fill = t[role].wash if role else t.surface
            ink = t[role].ink if role else t.ink
            c.rect(Box(x, yy, cw, ROW - 5), fill=t.card, stroke=t.line, r=5)
            c.rect(Box(x, yy, cw * score, ROW - 5), fill=fill, r=5)
            c.text(x + 8, yy + 17, str(rank), TINY, BOLD, t.muted)
            c.text(x + 24, yy + 17, label, TINY, BOLD if role else SANS, ink)
            c.text(x + cw - 8, yy + 17, f"{score:.3f}", TINY, SANS, t.muted, anchor="end")
            yy += ROW
        bottom = yy
    y = bottom + 26

    heading(c, M, y, W - 2 * M, "THE THREE FACTS TO WATCH")
    y += 24
    for role, label, text in (
            ("both", "the hard constraint", "rank 7, 8 and 9: outside the first six every time"),
            ("stale", "the replaced fact", "still stored, and inside the first six for the third question"),
            ("store", "the fact that replaced it", "inside the first six only when keyword scores are added")):
        c.rect(Box(M, y - 11, 14, 14), fill=t[role].wash, stroke=t[role].accent, r=3)
        width = c.text(M + 22, y, label, TINY, BOLD, t[role].ink)
        c.text(M + 22 + width + 10, y, text, TINY, SANS, t.muted)
        y += 20

    y += 6
    c.line(M, y, W - M, y, t.line)
    y += 20
    source = "Column 1 from notebooks/02-mem0.ipynb; columns 2 and 3 from a replay with the same nine facts"
    c.text(W - M, y, source, TINY, SANS, t.muted, anchor="end")
    c.height = int(y + 20)
    return c
