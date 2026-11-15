"""The running example: one conversation in three sessions, and the six things a correct answer needs.

No memory system appears here: this is the test that every notebook runs. The quotes are from the
conversation in notebooks/00-introduction.ipynb (the same in every notebook), shortened.
"""

from __future__ import annotations

from ..kit import (BOLD, ITALIC, MEDIUM, SANS, Box, Canvas, W, M, arrow, bubble, chip, heading, measure,
                   wrap)
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme

NAME = "conversation"
TITLE = "One conversation, three sessions"
ALT = ("The running example. On 14 March the user says they have been strictly vegetarian for "
       "eight years, have a severe peanut allergy, and like Indian food. Four months later, on 20 "
       "July, they say they are pescatarian now, have moved to Kreuzberg, and that their sister "
       "Lena (who can't eat shellfish) is coming with her partner Jonas (coeliac). Six weeks after "
       "that, in a new conversation, they ask for dinner for 'my sister and her partner'. A correct "
       "answer needs six things: the new diet and not the old one (a fact that changes), no "
       "peanuts (a hard constraint), no shellfish and no gluten (people the question does not "
       "name, reached through two links), Indian food and somewhere near Kreuzberg.")

SESSIONS = [
    ("14 March · session 1",
     "“I'm planning a dinner for my sister's visit to Berlin next week … I've been strictly "
     "vegetarian for eight years, and I have a severe peanut allergy — anaphylactic, not a "
     "preference … Indian, usually. Paneer dishes especially … not more than about 40 euros a "
     "head.”", False),
    ("20 July · session 2",
     "“I started eating fish about a month ago. So I'm pescatarian now, not vegetarian … I moved "
     "to Kreuzberg in May … my sister Lena is coming back in the autumn, and she's bringing her "
     "partner, Jonas … Lena can't eat shellfish, and Jonas is coeliac.”", False),
    ("1 September · session 3",
     "“My sister and her partner are in town tonight. Book the three of us somewhere for dinner — "
     "you know what we can and can't eat.”", True),
]
GAPS = ["four months", "six weeks"]

# What a correct answer needs, grouped by what each group tests. Each card: its title, the short
# names of its needs (the same names as the scorecards in the system figures), rows of (when,
# what was said, struck out), whether the rows form a chain of links, and a note.
CARDS = [
    ("A fact that changes", ["diet"],
     [("March", "“strictly vegetarian for eight years”", True),
      ("July", "“pescatarian now, not vegetarian”", False)], False,
     "The newer value must win: the answer needs pescatarian, not vegetarian."),
    ("A hard constraint", ["peanuts"],
     [("March", "“a severe peanut allergy — anaphylactic, not a preference”", False),
      ("July", "“the peanut situation obviously hasn't changed”", False)], False,
     "An attribute of the user, not a named thing, and not a matter of taste."),
    ("People the question does not name", ["shellfish", "gluten"],
     [("September", "“my sister and her partner”", False),
      ("July", "sister Lena, her partner Jonas", False),
      ("July", "“Lena can't eat shellfish, and Jonas is coeliac”", False)], True,
     "The question never says Lena, Jonas, shellfish or gluten. Coeliac is two links away."),
    ("Preferences", ["cuisine", "area"],
     [("March", "“Indian, usually. Paneer dishes especially.”", False),
      ("July", "“I moved to Kreuzberg in May … anything walkable from there”", False)], False,
     "Not strict, but a good answer uses both."),
]

WHEN_W = 74       # the column of dates inside a card
ROW_GAP = 8
CHAIN_GAP = 18    # room for the arrow between the links of a chain


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The test that every system in this series runs. The user changes a "
                       "fact, keeps a hard constraint, and introduces two people; the last session "
                       "asks for something only right if all of it was kept.",
                       W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30

    # the sessions on a line of time, with the gaps between them
    gap = 16
    bw = (W - 2 * M - 2 * gap) / 3
    xs = [M + i * (bw + gap) for i in range(3)]
    p = t["person"]
    c.line(xs[0] + 7.5, y, xs[2] + 7.5, y, p.accent, 1.2)
    for x in xs:
        c.circle(x + 7.5, y, 4, fill=p.accent)
    for i, label in enumerate(GAPS):
        mid = (xs[i] + xs[i + 1]) / 2 + 7.5
        c.text(mid, y - 8, label, TINY, ITALIC, p.accent, anchor="middle")
    y += 16
    bottoms = [bubble(c, x, y, bw, when, text, target=target).bottom
               for x, (when, text, target) in zip(xs, SESSIONS)]
    y = max(bottoms) + 34

    heading(c, M, y, W - 2 * M, "WHAT A CORRECT ANSWER NEEDS", "six things, grouped by what they test")
    y += 22
    cw = (W - 2 * M - gap) / 2
    for row in (CARDS[:2], CARDS[2:]):
        heights = [_card_height(card, cw) for card in row]
        h = max(heights)
        for i, card in enumerate(row):
            _card(c, M + i * (cw + gap), y, cw, h, card)
        y += h + gap

    y += 6
    c.line(M, y, W - M, y, t.line)
    c.text(M, y + 22, "From notebooks/00-introduction.ipynb, shortened. The same conversation runs "
           "through every notebook.", TINY, SANS, t.muted)
    c.height = int(y + 40)
    return c


def _row_lines(text: str, w: float) -> list[str]:
    return wrap(text, TINY, w - 28 - WHEN_W)


def _chips_below(card, w: float) -> bool:
    """Whether the needs' chips go under the title, because they do not fit beside it."""
    title, needs = card[0], card[1]
    chips_w = sum(measure(need, TINY, MEDIUM) + 16 + 6 for need in needs)
    return measure(title, SMALL, BOLD) + 20 + chips_w > w - 26


def _card_height(card, w: float) -> float:
    _, _, rows, chain, note = card
    h = 44 + (26 if _chips_below(card, w) else 0)
    for i, (_, text, _) in enumerate(rows):
        h += len(_row_lines(text, w)) * TINY * 1.35 + (CHAIN_GAP if chain and i < len(rows) - 1 else ROW_GAP)
    h += 6 + len(wrap(note, TINY, w - 28, ITALIC)) * TINY * 1.35 + 12
    return h


def _card(c: Canvas, x: float, y: float, w: float, h: float, card) -> None:
    t = c.theme
    title, needs, rows, chain, note = card
    c.rect(Box(x, y, w, h), fill=t.card, stroke=t.line, r=10)
    c.text(x + 14, y + 25, title, SMALL, BOLD)
    yy = y + 44
    if _chips_below(card, w):
        cx = x + 14
        for need in needs:
            cx = chip(c, cx, y + 36, need).right + 6
        yy += 26
    else:
        right = x + w - 12
        for need in reversed(needs):
            right = chip(c, right, y + 11, need, anchor="end").x - 6
    for i, (when, text, struck) in enumerate(rows):
        lines = _row_lines(text, w)
        c.text(x + 14, yy + TINY, when, TINY, MEDIUM, t["person"].accent)
        tx = x + 14 + WHEN_W
        colour = t["stale"].accent if struck else t.ink
        for j, line in enumerate(lines):
            base = yy + TINY + j * TINY * 1.35
            c.text(tx, base, line, TINY, SANS, colour)
            if struck:
                c.line(tx, base - TINY * 0.32, tx + measure(line, TINY), base - TINY * 0.32, colour, 1.1)
        yy += len(lines) * TINY * 1.35
        if chain and i < len(rows) - 1:
            arrow(c, [(tx + 6, yy + 1), (tx + 6, yy + CHAIN_GAP - 3)], t.muted, width=1.2)
            yy += CHAIN_GAP
        else:
            yy += ROW_GAP
    c.paragraph(x + 14, yy - 2, note, w - 28, TINY, ITALIC, t.muted, 1.35)
