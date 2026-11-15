"""Zep / Graphiti: the fourteen stored facts scored against the question, and the 0.6 floor.

The scores, the facts that share a word with the question and the final ranks are the committed
run of notebooks/03-zep-graphiti.ipynb, section 4 (the score table). graphiti_matching.py draws
entity names against the same kind of floor with `score_bars`.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, SANS, Box, Canvas, W, M, chip, heading
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "graphiti-floor"
TITLE = "What the search returned, and why"
ALT = ("The fourteen stored facts, sorted by the cosine similarity of their sentence to the "
       "question, between 0.54 and 0.74, with a line at the 0.6 floor. The search returns ten: "
       "facts that share a word with the question, and facts above the floor, merged. Returned: "
       "the dinner plan, stored twice (0.739), Indian cuisine (0.665), the budget (0.658), the "
       "assistant's note that fish is in (0.658), the sister named Lena (0.653), Lena cannot eat "
       "shellfish (0.636), the closed vegetarian fact (0.608, tenth), paneer dishes (0.608), and "
       "Lena and Jonas as a couple (0.599, under the floor but returned for its shared words). Not "
       "returned: the peanut allergy (0.602, over the floor but eleventh), Jonas's coeliac disease "
       "(0.596), the pescatarian fact that replaced the vegetarian one (0.592) and the move to "
       "Kreuzberg (0.542).")

# (fact, cosine to the question, shares a word, final rank or None, role, needed)
ROWS = [
    ("dinner for the sister's visit", .739, True, 1, None, False),
    ("the same dinner sentence, second edge", .739, True, 3, None, False),
    ("prefers Indian cuisine", .665, True, 5, None, False),
    ("budget of 40 euros a head", .658, True, 7, None, False),
    ("the assistant: fish is now included", .658, False, 8, None, False),
    ("a sister named Lena", .653, True, 6, None, False),
    ("Lena cannot eat shellfish", .636, True, 4, None, True),
    ("strictly vegetarian (ended in July)", .608, False, 10, "stale", False),
    ("enjoys paneer dishes", .608, False, 9, None, False),
    ("severe peanut allergy", .602, False, None, None, True),
    ("Lena and Jonas are a couple", .599, True, 2, None, False),
    ("Jonas has coeliac disease", .596, False, None, None, True),
    ("pescatarian, replacing vegetarian", .592, False, None, None, True),
    ("moved to Kreuzberg in May", .542, False, None, None, False),
]
LO, HI, FLOOR = 0.50, 0.75, 0.6


def score_bars(c: Canvas, x: float, y: float, w: float, rows, lo: float, hi: float, floor: float,
               label_w: float, digits: int = 3, row_h: float = 28) -> float:
    """Rows of (label, score, bold, faded, role) as bars on a common scale, with a dashed line at
    `floor`. Returns the height used."""
    t = c.theme
    bar_x, bar_w = x + label_w, w - label_w - 64
    scale = lambda v: bar_x + bar_w * (v - lo) / (hi - lo)
    for i, (label, score, bold, faded, role) in enumerate(rows):
        yy = y + i * row_h
        ink = t[role].ink if role else (t.faint if faded else t.ink)
        c.text(x, yy + 17, label, TINY, BOLD if bold else SANS, ink)
        c.rect(Box(bar_x, yy + 5, bar_w, row_h - 10), fill=t.card, stroke=t.line, r=4)
        if faded:
            c.rect(Box(bar_x, yy + 5, scale(score) - bar_x, row_h - 10), fill=t.paper,
                   stroke=t["stale"].accent, r=4, dash="3 2.5")
        else:
            fill = t[role].wash if role else t["store"].wash
            c.rect(Box(bar_x, yy + 5, scale(score) - bar_x, row_h - 10), fill=fill,
                   stroke=t[role].accent if role else t["store"].accent, r=4, width=0.8)
        c.text(bar_x + bar_w + 8, yy + 17, f"{score:.{digits}f}", TINY, MEDIUM if bold else SANS, ink)
    fx = scale(floor)
    bottom = y + len(rows) * row_h
    c.line(fx, y - 6, fx, bottom + 2, t["stale"].accent, 1.6, dash="5 4")
    c.text(fx, y - 12, f"floor {floor}", TINY, BOLD, t["stale"].accent, anchor="middle")
    for v in (lo, (lo + hi) / 2, hi):
        c.text(scale(v), bottom + 16, f"{v:.3g}", TINY, SANS, t.faint, anchor="middle")
    return len(rows) * row_h + 20


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Every stored fact, scored by how close its sentence is in meaning to "
                       "the question. All fourteen fall in a narrow band, and the floor of 0.6 cuts "
                       "through it. The search keeps ten: facts that share a word with the question, "
                       "and facts over the floor, merged by rank.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 40
    right = 150   # the columns for shared words and the final rank
    c.text(W - M - right + 10, y - 12, "shares a word", TINY, BOLD, t.muted)
    c.text(W - M, y - 12, "returned", TINY, BOLD, t.muted, anchor="end")
    rows = [(label, s, needed, rank is None, role) for label, s, _, rank, role, needed in ROWS]
    h = score_bars(c, M, y, W - 2 * M - right, rows, LO, HI, FLOOR, 250)
    for i, (_, _, word, rank, role, _) in enumerate(ROWS):
        yy = y + i * 28
        if word:
            c.icon("check", W - M - right + 40, yy + 6, 15, t.muted, stroke=1.8)
        if rank:
            chip(c, W - M, yy + 3, f"{rank}", role or "store", face=BOLD, anchor="end")
        else:
            chip(c, W - M, yy + 3, "11th" if ROWS[i][0] == "severe peanut allergy" else "no", "stale",
                 icon="x", outline=True, anchor="end")
    y += h + 30

    heading(c, M, y, W - 2 * M, "WHAT TO NOTICE")
    y += 22
    for lead, text in (
            ("The floor decides at the third decimal.", "The closed fact is in at 0.608; the fact that "
             "replaced it is out at 0.592; Jonas's coeliac disease is out at 0.596."),
            ("A shared word gets a fact in anyway.", "“Lena and Jonas are a couple” is under the floor "
             "and comes second, for the words it shares with the question."),
            ("The limit decides the rest.", "The peanut allergy passes the floor and comes eleventh. "
             "The closed fact took the tenth place, and the dinner sentence stored twice took two."),
            ("Bold rows are the four facts the answer needs.", "One of them was returned.")):
        c.text(M, y, lead, TINY, BOLD, t.ink)
        used = c.paragraph(M, y + 3, text, W - 2 * M, TINY, SANS, t.muted)
        y += used + 22
    source_line(c, y + 10, "From notebooks/03-zep-graphiti.ipynb, section 4")
    return c
