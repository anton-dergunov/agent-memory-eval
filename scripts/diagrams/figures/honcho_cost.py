"""Honcho: what each model call read, in the first real-server run of the series' example.

Input tokens of all 19 calls, as the server's provider reported them (the blog's
replays/honcho_server_runs/run1.json). For a dream agent, the first round's input is what every
round sends again (instructions, tool descriptions, the opening message); the rest of a later
round is what the agent has read and called since. The deriver and the dialectic make one call
each, drawn whole.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, SANS, Box, Canvas, W, M
from ..theme import SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "honcho-cost"
TITLE = "What each call read"
ALT = ("Nineteen bars, one per model call of the first server run, grouped by step. The deriver "
       "read 923 tokens for session 1 and 1,115 for session 2. Dream 1: the deduction agent's four "
       "rounds read 2,460 to 3,069 tokens, the induction agent's three 1,028 to 1,705. Dream 2: "
       "the deduction agent's five rounds read 2,551 to 4,069, the induction agent's four 1,028 to "
       "2,861. In every round of an agent, the part equal to its first round is sent again; the "
       "rest is what it has read since. The dialectic's one call read 4,598 tokens. In all, "
       "49,585 tokens, 44,987 of them for writing.")

# (step, input tokens of each call), from run 1
STEPS = [
    ("deriver\nsession 1", "single", [923]),
    ("dream 1\ndeduction", "agent", [2460, 2841, 3015, 3069]),
    ("dream 1\ninduction", "agent", [1028, 1569, 1705]),
    ("deriver\nsession 2", "single", [1115]),
    ("dream 2\ndeduction", "agent", [2551, 3727, 3969, 4005, 4069]),
    ("dream 2\ninduction", "agent", [1028, 2362, 2690, 2861]),
    ("dialectic\nanswer", "single", [4598]),
]
PARTS = [("sent again every round (as in round 1)", "prompt"), ("read and called since round 1", "store"),
         ("a single call", "llm")]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The 19 model calls of the first server run. The dream agents make "
                       "most of them, and each round sends the agent's instructions again.",
                       W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30
    x = M
    for label, role in PARTS:
        c.rect(Box(x, y - 11, 14, 14), fill=t[role].wash, stroke=t[role].accent, r=3, width=0.8)
        x += 20 + c.text(x + 20, y, label, TINY, SANS, t.muted) + 20
    y += 24
    chart_h, top = 280, 5000
    base = y + chart_h
    axis_x = M + 44
    gap = 16
    n = sum(len(calls) for _, _, calls in STEPS)
    bar = (W - M - axis_x - gap * (len(STEPS) - 1)) / n
    for v in range(0, top + 1, 1000):
        yy = base - chart_h * v / top
        c.line(axis_x, yy, W - M, yy, t.line, 0.8)
        c.text(axis_x - 6, yy + 4, f"{v:,}", TINY - 1, SANS, t.faint, anchor="end")
    x = axis_x
    for label, kind, calls in STEPS:
        start = x
        first = calls[0]
        for value in calls:
            if kind == "single":
                parts = [(value, "llm")]
            else:
                parts = [(first, "prompt"), (value - first, "store")]
            yy = base
            for v, role in parts:
                h = chart_h * v / top
                if h > 0:
                    c.rect(Box(x + 2, yy - h, bar - 4, h), fill=t[role].wash, stroke=t[role].accent,
                           r=1.5, width=0.6)
                yy -= h
            c.text(x + bar / 2, yy - 6, f"{value / 1000:.1f}k", TINY - 2, MEDIUM, t.muted, anchor="middle")
            x += bar
        mid = (start + x) / 2
        for i, line in enumerate(label.split("\n")):
            c.text(mid, base + 18 + i * 15, line, TINY - 1, BOLD if i == 0 else SANS, t.ink, anchor="middle")
        x += gap
    y = base + 56
    used = c.paragraph(M, y, "Writing the two sessions took 18 calls and 44,987 tokens; the "
                       "dialectic's call that gave the answer its context, 4,598 more. The second "
                       "dream cost more than the first because its tool results were longer: both "
                       "asked for the newest twenty conclusions.", W - 2 * M, TINY, SANS, t.muted)
    source_line(c, y + used + 16, "From the first run of a Honcho 3.3.0 server on the example; tokens as reported by the model's provider")
    return c
