"""Honcho on the benchmark: what a dream agent looked at, against where the two values were.

Top: the store of question 4d6b87c8 ("How many titles are currently on my to-watch list?") from
results/main/honcho-repr, its 114 explicit conclusions in the order they were stored. The dream's
agents opened with get_recent_observations, mostly with a limit of 20 (the experiment's reply
cache: 13 such calls, 10 with 20; no search_memory call at all), so the newest twenty are marked.
The old value ("20 titles") is row 48 and the new one ("25 titles") row 88 of 114.

Bottom: the same count for every store where both values could be located by their text (41 of
67; scripts/replays/honcho_dream_window.py), and what the 67 stores held by level.
"""

from __future__ import annotations

from ..kit import BOLD, ITALIC, MEDIUM, MONO, SANS, Box, Canvas, W, M, heading
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "honcho-window"
TITLE = "What the dream looked at"
ALT = ("Top: one benchmark store, 114 explicit conclusions from oldest to newest. The dream's "
       "agents asked for the newest twenty. The old value of the question, '20 titles', is row 48; "
       "the new value, '25 titles', is row 88: both outside the twenty. The dream wrote three "
       "deductions and two patterns, about sleep, glaciology and journalism, the topics of the "
       "newest rows. Bottom: in the 41 stores where both values could be located, the newest twenty "
       "rows held both values in none, the new value only in 21, the old value only in 3, and "
       "neither in 17. Across all 67 stores: 7,434 explicit conclusions, 158 deductive, none of "
       "which records a change, 146 inductive, and no contradictions.")

ROWS, WINDOW, OLD, NEW = 114, 20, 48, 88       # 1-based positions, oldest first
COUNTS = [("both values", 0, "store"), ("the new value only", 21, "both"),
          ("the old value only", 3, "stale"), ("neither", 17, "code")]
LEVELS = [("explicit", "7,434", "about 111 per store"),
          ("deductive", "158", "none records a change of value"),
          ("inductive", "146", "about 2 per store"),
          ("contradiction", "0", "no component writes this level")]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "A dream agent sees what its tools return. On the benchmark it asked "
                       "for the newest twenty conclusions and never searched, so it rarely saw a fact "
                       "and its change together.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30
    heading(c, M, y, W - 2 * M, "ONE STORE", "“How many titles are currently on my to-watch list?”")
    y += 34
    cell = (W - 2 * M) / ROWS
    strip = Box(M, y + 30, W - 2 * M, 30)
    c.text(M, strip.bottom + 22, "oldest", TINY, SANS, t.muted)
    c.text(W - M, strip.bottom + 22, "newest", TINY, SANS, t.muted, anchor="end")
    for i in range(1, ROWS + 1):
        x = M + (i - 1) * cell
        role = "stale" if i == OLD else "both" if i == NEW else None
        if role:
            c.rect(Box(x + 0.6, strip.y - 6, cell - 1.2, strip.h + 12), fill=t[role].accent, r=1.5)
        else:
            inside = i > ROWS - WINDOW
            c.rect(Box(x + 0.6, strip.y, cell - 1.2, strip.h),
                   fill=t["prompt"].accent if inside else t.line, r=1, opacity=0.9 if inside else 1)
    # the window
    wx = M + (ROWS - WINDOW) * cell
    c.rect(Box(wx - 3, strip.y - 10, WINDOW * cell + 6, strip.h + 20), stroke=t["prompt"].accent, r=6, width=1.4)
    label_w = c.text(W - M, strip.y - 18, "what the agents asked for", TINY, SANS, t["prompt"].accent, anchor="end")
    c.text(W - M - label_w - 6, strip.y - 18, "the newest 20:", TINY, BOLD, t["prompt"].accent, anchor="end")
    for pos, role, label, when in ((OLD, "stale", "old value: “20 titles”", "row 48, said 20 May"),
                                   (NEW, "both", "new value: “25 titles”", "row 88, said 22 May")):
        x = M + (pos - 0.5) * cell
        c.line(x, strip.bottom + 6, x, strip.bottom + 20, t[role].accent, 1.2)
        c.text(x, strip.bottom + 34, label, TINY, BOLD, t[role].accent, anchor="middle")
        c.text(x, strip.bottom + 49, when, TINY, SANS, t[role].accent, anchor="middle")
    y = strip.bottom + 74
    c.paragraph(M, y, "What the dream wrote for this store: three deductions and two patterns, about "
                "sleep hygiene, Antarctic glaciology and long-form journalism, the topics of its "
                "newest rows. Nothing about the list.", W - 2 * M, SMALL, ITALIC, t.ink)
    y += 62
    heading(c, M, y, W - 2 * M, "ALL STORES", "the newest twenty explicit rows of each store held")
    y += 26
    total = sum(n for _, n, _ in COUNTS)
    bar_w = W - 2 * M
    x = M
    for label, n, role in COUNTS:
        w = bar_w * n / total
        if n:
            c.rect(Box(x, y, w - 2, 28), fill=t[role].wash, stroke=t[role].accent, r=4, width=1)
            c.text(x + 8, y + 19, f"{n}", SMALL, BOLD, t[role].ink)
        x += w
    lx = M
    for label, n, role in COUNTS:
        c.rect(Box(lx, y + 42, 12, 12), fill=t[role].wash, stroke=t[role].accent, r=2, width=0.8)
        lx += 18 + c.text(lx + 18, y + 52, f"{label}: {n}", TINY, SANS, t.muted) + 22
    c.text(M, y + 76, "in the 41 of 67 stores where both values could be found by their text",
           TINY, ITALIC, t.muted)
    y += 108
    heading(c, M, y, W - 2 * M, "WHAT THE 67 STORES HELD", "conclusions by level")
    y += 28
    for i, (level, count, note) in enumerate(LEVELS):
        ry = y + i * 24
        c.text(M, ry, level, SMALL, MONO, t["store"].accent)
        c.text(M + 200, ry, count, SMALL, BOLD, t.ink, anchor="end")
        c.text(M + 220, ry, note, SMALL, SANS, t.muted)
    y += len(LEVELS) * 24 + 4
    source_line(c, y, "From the experiment's Honcho stores (results/main/honcho-repr) and reply cache")
    return c
