"""Textual memory: what the second rewrite changed in the profile.

The profile after session 1 and after session 2, side by side under their four headings, from the
committed run of notebooks/01-textual.ipynb (section 2), each line without its bold label and
some shortened. The diet line changed as the prompt asks; the numbered marks are the changes the
rewriter made on its own.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, SANS, Box, Canvas, W, M, arrow, heading, measure, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme

NAME = "profile-diff"
TITLE = "What the second rewrite changed"
ALT = ("The textual-memory profile after session 1 (91 words) and after session 2 (153 words), "
       "under the same four headings. The diet line was replaced, as the prompt asks: pescatarian "
       "since June 2026, previously strictly vegetarian since 2018, and the change is recorded "
       "again under 'Changes over time' as 2026-06-20. The allergy, cuisine and budget lines "
       "survived word for word. Lena, Jonas and their needs, Kreuzberg and the walking distance "
       "were added. Four changes nobody asked for are marked: 1, 'moved in May' became 'since "
       "2026-05-01'; 2, 'can't eat shellfish' became 'has a shellfish allergy'; 3, the guess from "
       "session 1, 'based in or planning for Berlin', is kept as what the user said before; 4, the "
       "March dinner was dropped.")

# Each line: (text, style, marks). Styles: None for a line that survived word for word,
# "changed" for the line the prompt's rule replaced, "added" for a line from session 2,
# "dropped" for a line that is gone. Marks are the numbered notes below.
BEFORE = [
    ("Personal facts", [
        ("Strictly vegetarian (since 2018).", "dropped", []),
        ("Severe, anaphylactic peanut allergy.", None, []),
        ("Has a sister who is visiting Berlin.", "dropped", []),
        ("Currently based in or planning for Berlin.", "dropped", [3]),
    ]),
    ("Preferences and habits", [
        ("Indian food, specifically paneer dishes.", None, []),
        ("Prefers to spend no more than 40 euros per person for dining.", None, []),
    ]),
    ("Ongoing situations and plans", [
        ("Planning a dinner for a sister's visit to Berlin, scheduled for the week of March 16, "
         "2026.", "dropped", [4]),
    ]),
    ("Changes over time", [
        ("None.", "dropped", []),
    ]),
]
AFTER = [
    ("Personal facts", [
        ("Pescatarian (since June 2026; previously strictly vegetarian since 2018).", "changed", []),
        ("Severe, anaphylactic peanut allergy.", None, []),
        ("Sister named Lena; her partner is named Jonas.", "added", []),
        ("Residing in Kreuzberg, Berlin (since May 2026).", "added", []),
    ]),
    ("Preferences and habits", [
        ("Indian food, specifically paneer dishes.", None, []),
        ("Prefers to spend no more than 40 euros per person for dining.", None, []),
        ("Prefers restaurants within walking distance of Kreuzberg.", "added", []),
        ("Sister (Lena) has a shellfish allergy; partner (Jonas) has coeliac disease (must be "
         "gluten-free).", "added", [2]),
    ]),
    ("Ongoing situations and plans", [
        ("Planning a dinner for a visit from sister Lena and her partner, Jonas, in the autumn of "
         "2026.", "added", []),
    ]),
    ("Changes over time", [
        ("Now pescatarian (since 2026-06-20; previously strictly vegetarian since 2018).", "changed", []),
        ("Moved to Kreuzberg, Berlin (since 2026-05-01; previously based in or planning for "
         "Berlin generally).", "added", [1, 3]),
    ]),
]

NOTES = [
    (1, "Added precision", "“I moved to Kreuzberg in May” became “since 2026-05-01”: a guessed "
        "day, written down as a date."),
    (2, "Reworded a constraint", "“Lena can't eat shellfish” became “has a shellfish allergy”. "
        "For a booking it makes no difference; for a question about why, it does."),
    (3, "Kept its own guess as history", "“Based in or planning for Berlin” was the rewriter's "
        "hedge in March. In July it is recorded as what the user said before."),
    (4, "Dropped a plan", "The March dinner is gone, replaced by the autumn visit. Here that is "
        "right, but nothing outside the model checked it."),
]

STYLE = {None: None, "changed": "both", "added": "store", "dropped": "stale"}
GAP = 40           # between the two pages, room for the arrow
LEAD = TINY * 1.35
MARK_R = 8


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The textual-memory profile after session 1, and after one LLM call "
                       "rewrote all of it with session 2. The diet changed as the prompt's rule "
                       "asks; the four numbered changes are the rewriter's own.",
                       W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30

    pw = (W - 2 * M - GAP) / 2
    lx, rx = M, M + pw + GAP
    for x, name, when in ((lx, "After session 1", "14 March · 91 words"),
                          (rx, "After session 2", "20 July · 153 words")):
        width = c.text(x, y, name, SMALL, BOLD, t["store"].ink)
        c.text(x + width + 8, y, when, TINY, SANS, t.muted)
    top = y + 12

    # lay out both pages section by section, so that each heading sits level on both
    layout, h = [], 16.0
    for (head, before), (_, after) in zip(BEFORE, AFTER):
        layout.append((head, h))
        h += 22
        hb = sum(_line_height(text, marks, pw) for text, _, marks in before)
        ha = sum(_line_height(text, marks, pw) for text, _, marks in after)
        layout.append(((before, after), h))
        h += max(hb, ha) + 10
    page_h = h + 6
    for x, side in ((lx, 0), (rx, 1)):
        c.rect(Box(x, top, pw, page_h), fill=t.card, stroke=t.line, r=8)
        for item, ry in layout:
            if isinstance(item, str):
                c.text(x + 14, top + ry + 12, item, TINY, BOLD, t["store"].ink)
                continue
            yy = top + ry
            for text, style, marks in item[side]:
                yy += _line(c, x, yy, pw, text, style, marks)
    my = top + 60
    arrow(c, [(lx + pw + 8, my), (rx - 8, my)], t["llm"].accent, width=1.6)

    y = top + page_h + 30
    heading(c, M, y, W - 2 * M, "CHANGES NOBODY ASKED FOR")
    y += 20
    nw = (W - 2 * M - 16) / 2
    for row in (NOTES[:2], NOTES[2:]):
        heights = []
        for i, (n, title, text) in enumerate(row):
            x = M + i * (nw + 16)
            _mark(c, x + MARK_R, y + MARK_R + 1, n)
            c.text(x + 2 * MARK_R + 8, y + 13, title, SMALL, BOLD)
            heights.append(18 + c.paragraph(x + 2 * MARK_R + 8, y + 18, text, nw - 2 * MARK_R - 8,
                                            TINY, SANS, t.ink, 1.35))
        y += max(heights) + 14

    y += 4
    c.line(M, y, W - M, y, t.line)
    x = M
    y += 22
    for style, label in (("changed", "replaced, with the old value as history"),
                         ("added", "added from session 2"), ("dropped", "gone"),
                         (None, "plain: kept word for word")):
        if style:
            r = t[STYLE[style]]
            c.rect(Box(x, y - 11, 22, 15), fill=r.wash, r=3)
        else:
            c.rect(Box(x, y - 11, 22, 15), fill=t.card, stroke=t.line, r=3)
        x += 30 + c.text(x + 30, y, label, TINY, SANS, t.muted) + 18
    source = "From notebooks/01-textual.ipynb; each line without its bold label"
    if x + measure(source, TINY) > W - M:
        y += 22
    c.text(W - M, y, source, TINY, SANS, t.muted, anchor="end")
    c.height = int(y + 20)
    return c


def _text_width(marks: list[int], pw: float) -> float:
    return pw - 40 - len(marks) * (2 * MARK_R + 4)


def _line_height(text: str, marks: list[int], pw: float) -> float:
    return len(wrap(text, TINY, _text_width(marks, pw))) * LEAD + 6


def _line(c: Canvas, x: float, y: float, pw: float, text: str, style: str | None, marks: list[int]) -> float:
    """One line of the profile, tinted by what happened to it. Returns the height used."""
    t = c.theme
    lines = wrap(text, TINY, _text_width(marks, pw))
    h = len(lines) * LEAD + 6
    role = STYLE[style]
    if role:
        c.rect(Box(x + 7, y, pw - 14, h - 2), fill=t[role].wash, r=4)
    ink = t[role].ink if role else t.ink
    c.text(x + 16, y + 3 + TINY, "·", TINY, BOLD, t.muted)
    for i, line in enumerate(lines):
        base = y + 3 + TINY + i * LEAD
        c.text(x + 24, base, line, TINY, MEDIUM if style == "changed" else SANS, ink)
        if style == "dropped":
            c.line(x + 24, base - TINY * 0.32, x + 24 + measure(line, TINY), base - TINY * 0.32,
                   t["stale"].accent, 1.0)
    mx = x + pw - 14 - MARK_R
    for n in reversed(marks):
        _mark(c, mx, y + 3 + TINY * 0.6, n)
        mx -= 2 * MARK_R + 4
    return h


def _mark(c: Canvas, cx: float, cy: float, n: int) -> None:
    r = c.theme["llm"]
    c.circle(cx, cy, MARK_R, fill=r.accent)
    c.text(cx, cy + 4, str(n), TINY - 1, BOLD, c.theme.paper, anchor="middle")
