"""Zep / Graphiti: the four dates on a fact, on two timelines, and how the old fact closes.

The dates are the committed run of notebooks/03-zep-graphiti.ipynb (section 3, the table of
fourteen facts with all four dates).
"""

from __future__ import annotations

from datetime import date

from ..kit import BOLD, ITALIC, MEDIUM, MONO, SANS, Box, Canvas, W, M, arrow, heading
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "graphiti-dates"
TITLE = "Two timelines on every fact"
ALT = ("Three stored facts on a timeline from March to September 2026, each with two bars: when "
       "it was true in the world (valid_at to invalid_at) and when the graph held it (created_at "
       "to expired_at). 'Strictly vegetarian for eight years' is true from 14 March, the day it "
       "was said, until 20 July, and held over the same days. 'Started following a pescatarian "
       "diet about a month ago' is true from 20 July and held from 20 July; the user meant about "
       "20 June, but the model dated it by the message. When it arrived, code ended the "
       "vegetarian fact where the new one starts. 'Moved to Kreuzberg in May' is true from 1 May "
       "but held only from 20 July, when it was said. A line at 15 April crosses only the "
       "vegetarian fact; a line at 1 September crosses the pescatarian fact and Kreuzberg.")

START, END = date(2026, 3, 1), date(2026, 9, 8)
FACTS = [
    ("Strictly vegetarian for eight years", "stale",
     (date(2026, 3, 14), date(2026, 7, 20)), (date(2026, 3, 14), date(2026, 7, 20)),
     "said: “for eight years”, so since about 2018"),
    ("Started a pescatarian diet about a month ago", "store",
     (date(2026, 7, 20), None), (date(2026, 7, 20), None),
     "said: “about a month ago”, so about 20 June"),
    ("Moved to Kreuzberg in May 2026", "store",
     (date(2026, 5, 1), None), (date(2026, 7, 20), None),
     "true from 1 May; known from 20 July"),
]
LABEL_W = 214


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Every fact carries two date ranges: when it was true in the world, "
                       "and when the graph held it. A contradicted fact is not deleted; it gets an "
                       "end date, so a question about any day becomes a filter.", W - 2 * M,
                       SUBTITLE, SANS, t.muted)
    y = 62 + used + 40
    x0, x1 = M + LABEL_W, W - M - 10
    xd = lambda d: x0 + (x1 - x0) * (d - START).days / (END - START).days

    top = y
    for m in range(3, 10):
        d = date(2026, m, 1)
        c.text(xd(d), top, d.strftime("%b"), TINY, MEDIUM, t.faint, anchor="middle")
    y += 18
    rows_top = y
    bars = {}
    for name, role, world, held, note in FACTS:
        r = t[role]
        c.text(M, y + 15, name, SMALL, BOLD, r.ink if role == "stale" else t.ink)
        for k, ((a, b), lane) in enumerate(((world, "true in the world"), (held, "held by the graph"))):
            yy = y + 26 + k * 24
            c.text(M + 12, yy + 13, lane, TINY, SANS, t.muted)
            right = xd(b) if b else x1
            box = Box(xd(a), yy + 2, right - xd(a), 16)
            if role == "stale":
                c.rect(box, fill=r.wash, stroke=r.accent, r=4, dash="3 2.5")
            else:
                c.rect(box, fill=r.wash if k else r.accent, stroke=r.accent, r=4)
            c.text(xd(a) - 4, yy + 14, a.strftime("%-d %b"), TINY - 1, MEDIUM, t.muted, anchor="end")
            if b:
                c.text(right + 4, yy + 14, b.strftime("%-d %b"), TINY - 1, MEDIUM, r.accent)
            elif k == 0:
                c.text(x1 + 4, yy + 14, "…", TINY, BOLD, r.accent)
            bars[(name, k)] = box
        c.text(M + 12, y + 92, note, TINY, ITALIC, t.muted)
        y += 116
    rows_bottom = y - 12

    # where the user meant the new diet to start
    meant = xd(date(2026, 6, 20))
    pes = bars[(FACTS[1][0], 0)]
    c.line(meant, pes.y - 2, meant, pes.bottom + 2, t["person"].accent, 1.4, dash="2 2.5")
    c.text(meant, pes.y - 6, "meant: about 20 Jun", TINY - 1, MEDIUM, t["person"].accent, anchor="middle")

    # the closing: the old fact ends where the new one starts
    veg = bars[(FACTS[0][0], 0)]
    held = bars[(FACTS[0][0], 1)]
    arrow(c, [(pes.x, pes.y - 2), (pes.x, held.bottom + 4)], t["stale"].accent)
    c.text(pes.x - 8, held.bottom + 22, "the old fact ends", TINY, BOLD, t["stale"].accent, anchor="end")
    c.text(pes.x - 8, held.bottom + 38, "where the new one starts", TINY, BOLD, t["stale"].accent, anchor="end")

    # two questions about a day
    for d, label, anchor in ((date(2026, 4, 15), "15 April", "middle"), (date(2026, 9, 1), "1 September", "end")):
        x = xd(d)
        c.line(x, rows_top - 4, x, rows_bottom, t["prompt"].accent, 1.4, dash="5 4")
        c.text(x + (14 if anchor == "end" else 0), rows_bottom + 16, f"true on {label}?", TINY, BOLD,
               t["prompt"].accent, anchor=anchor)
    y = rows_bottom + 40

    heading(c, M, y, W - 2 * M, "WHO SETS EACH DATE")
    y += 22
    for field, what, who in (
            ("valid_at", "when it became true", "the model, in step 3, from the message and its date"),
            ("invalid_at", "when it stopped being true", "code, when a newer fact contradicts it"),
            ("created_at", "when the graph learned it", "code, when the message is stored"),
            ("expired_at", "when the graph stopped holding it", "code, when the fact is closed")):
        c.text(M, y + 4, field, SMALL, MONO, t["llm"].accent if field == "valid_at" else t["code"].accent)
        c.text(M + 110, y + 4, what, SMALL, MEDIUM)
        c.text(M + 380, y + 4, who, TINY, SANS, t.muted)
        y += 24
    y += 4
    used = c.paragraph(M, y, "Here created_at and expired_at are set to the time of each message, as if "
                       "every session were stored on the day it happened; in a live system they are "
                       "the clock time of storing.", W - 2 * M, TINY, SANS, t.muted)
    source_line(c, y + used + 18, "From notebooks/03-zep-graphiti.ipynb, section 3")
    return c
