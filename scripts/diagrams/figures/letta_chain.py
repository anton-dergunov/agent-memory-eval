"""Letta in the experiment: where a changed value was lost, with and without the persona lines.

Counts from docs/findings/letta.md (results/main/letta and results/main/letta-persona, LongMemEval,
67 questions): what the agent did at the user message carrying the new value (64 questions have
such a message), the searches at question time, and what the answer had to work with. Counts of
questions only; the accuracies belong to part 8.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, SANS, Box, Canvas, W, M, arrow, heading, measure, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "letta-chain"
TITLE = "Where a changed value was lost"
ALT = ("Three stages for the questions of the experiment, each with two rows: Letta as shipped and "
       "Letta with three persona lines. Stage 1, at the user message that carried the new value "
       "(64 questions): as shipped, the agent wrote the new value in 31 and did not in 33, of "
       "which 18 times its own reply named the new value; with the persona lines, it wrote it in "
       "57 and did not in 7. Stage 2, searches at question time: as shipped, 97 of 146 returned "
       "nothing; with the persona lines, 71 of 151. Stage 3, what the answer had to work with (67 "
       "questions): as shipped, the block held the value in 36, a search returned it in 17, "
       "neither in 13, and one history has no memory; with the persona lines, 59, 4, 3 and 1.")

STAGES = [
    ("1", "At the message that carried the new value", "64 questions",
     [("as shipped", [("wrote it", 31, "store"), ("did not; named it in its reply", 18, "stale"),
                      ("did not write it", 15, "both")]),
      ("with persona lines", [("wrote it", 57, "store"), ("named it, did not write", 2, "stale"),
                              ("did not", 5, "both")])],
     "Failure 1: noticed and not written"),
    ("2", "Searches at question time", "all searches",
     [("as shipped", [("returned something", 49, "store"), ("“No results found.”", 97, "stale")]),
      ("with persona lines", [("returned something", 80, "store"), ("“No results found.”", 71, "stale")])],
     "Failure 2: a phrase match, five newest"),
    ("3", "What the answer had to work with", "67 questions",
     [("as shipped", [("the block held it", 36, "store"), ("a search returned it", 17, "prompt"),
                      ("neither", 13, "stale"), ("no memory", 1, "code")]),
      ("with persona lines", [("the block held it", 59, "store"), ("a search returned it", 4, "prompt"),
                              ("neither", 3, "stale"), ("no memory", 1, "code")])],
     "Failure 3: a stale block is trusted"),
]
PAD = 12


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The real Letta server on LongMemEval, one agent step per user "
                       "message: as shipped, and with three lines added to its persona. Each stage "
                       "could have caught what the one before it missed.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 26
    label_w = 150
    bar_x = M + label_w
    bar_w = W - M - bar_x
    for num, title, unit, rows, failure in STAGES:
        heading(c, M, y, W - 2 * M, f"{num}. {title.upper()}", unit)
        c.text(W - M, y - 2, failure, TINY, BOLD, t["stale"].accent, anchor="end")
        y += 22
        for row, segments in rows:
            total = sum(n for _, n, _ in segments)
            c.text(M, y + 20, row, TINY, BOLD)
            x = bar_x
            for label, n, role in segments:
                w = bar_w * n / total
                c.rect(Box(x, y, w - 2, 30), fill=t[role].wash, stroke=t[role].accent, r=3, width=0.8)
                if measure(str(n), TINY, MEDIUM) + 8 < w:
                    c.text(x + 6, y + 20, str(n), TINY, MEDIUM, t[role].ink)
                x += w
            y += 38
        # the legend of this stage, from the first row's labels
        x = bar_x
        y += 6
        for label, _, role in rows[0][1]:
            text = {"did not; named it in its reply": "did not write it, but named it in its reply"}.get(label, label)
            c.rect(Box(x, y - 11, 14, 14), fill=t[role].wash, stroke=t[role].accent, r=3, width=0.8)
            x += 20 + c.text(x + 20, y, text, TINY, SANS, t.muted) + 18
        y += 40
    used = c.paragraph(M, y, "The persona lines were written after reading the first run's "
                       "failures, on the same questions. Stage 1 comes from reading the edit at "
                       "each message; in stage 3, one history has no memory at all (the model "
                       "provider's content filter stopped it).", W - 2 * M, TINY, SANS, t.muted)
    source_line(c, y + used + 16, "From docs/findings/letta.md (results/main/letta, letta-persona)")
    return c
