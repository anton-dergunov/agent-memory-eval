"""The check on trimming: the same 25 questions with 10 sessions and with the whole history.

Accuracy and USD per question for the four arms of the full-history run, from
scripts/replays/experiment_numbers_output.txt ("Full history against trimmed, same 25
questions"), which reads results/main and results/full.
"""

from __future__ import annotations

import math

from ..kit import BOLD, MEDIUM, SANS, Box, Canvas, W, M
from ..theme import SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "trimming-check"
TITLE = "Trimmed history and full history, on the same 25 questions"
ALT = ("Two slope charts for four systems, from the trimmed history of 10 sessions to the whole "
       "history of about 48. Accuracy: retrieval 100% to 96%, textual memory 96% to 92%, full "
       "context 92% to 84%, Mem0 84% to 84%; the order is the same in both runs. Cost per question: "
       "retrieval stays at $0.0016; full context goes from $0.0065 to $0.028; Mem0 from $0.040 to "
       "$0.18; textual memory from $0.022 to $0.28. One answer is 4 points.")

# arm, label, role, (accuracy 10, accuracy full), (usd 10, usd full)
ARMS = [
    ("retrieval", "Retrieval", "code", (100, 96), (0.0016, 0.0016)),
    ("textual", "Textual memory", "store", (96, 92), (0.0218, 0.2773)),
    ("full-context", "Full context", "prompt", (92, 84), (0.0065, 0.0275)),
    ("mem0", "Mem0", "llm", (84, 84), (0.0396, 0.1806)),
]


def _usd(v: float) -> str:
    return f"${v:.4f}" if v < 0.01 else f"${v:.3f}" if v < 0.1 else f"${v:.2f}"


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Four systems, run again with the whole history (about 48 sessions "
                       "instead of 10). Accuracy drops a little and keeps its order; the cost of "
                       "writing memory grows with the history.", W - 2 * M, SUBTITLE, SANS, t.muted)
    top = 62 + used + 40
    ph = 300
    panel_w = (W - 2 * M - 60) / 2
    panels = [("Accuracy", "questions answered correctly, of 25", M),
              ("Cost per question", "USD to write, read and answer, log scale", M + panel_w + 60)]
    for head, note, x in panels:
        c.text(x, top - 18, head, 15, BOLD, t.ink)
        c.text(x, top, note, TINY, SANS, t.muted)
    y0, y1 = top + 30, top + 30 + ph
    xl, xr = 70, panel_w - 150

    def acc_y(v):
        return y1 - (v - 70) / 30 * ph

    def usd_y(v):
        lo, hi = math.log10(0.001), math.log10(0.5)
        return y1 - (math.log10(v) - lo) / (hi - lo) * ph

    for (head, note, x), scale, ticks, fmt in [
            (panels[0], acc_y, [70, 80, 90, 100], lambda v: f"{v}%"),
            (panels[1], usd_y, [0.001, 0.01, 0.1], lambda v: f"${v:g}")]:
        for v in ticks:
            yy = scale(v)
            c.line(x + xl - 10, yy, x + xr + 10, yy, t.line, 0.8)
            c.text(x + xl - 16, yy + 4, fmt(v), TINY - 1, SANS, t.faint, anchor="end")
        c.text(x + xl, y1 + 22, "10 sessions", TINY, MEDIUM, t.muted, anchor="middle")
        c.text(x + xr, y1 + 22, "whole history", TINY, MEDIUM, t.muted, anchor="middle")
    # labels at the right end, nudged apart where values meet
    for panel, index, scale, fmt in [(panels[0], 3, acc_y, lambda v: f"{v}%"), (panels[1], 4, usd_y, _usd)]:
        x = panel[2]
        ends = []
        for arm, label, role, acc, usd in ARMS:
            a, b = acc if index == 3 else usd
            colour = t[role].accent
            ya, yb = scale(a), scale(b)
            c.line(x + xl, ya, x + xr, yb, colour, 2.2)
            c.circle(x + xl, ya, 4.5, fill=colour)
            c.circle(x + xr, yb, 4.5, fill=colour)
            ends.append([yb, label, fmt(a), fmt(b), colour])
        ends.sort()
        for i in range(1, len(ends)):
            ends[i][0] = max(ends[i][0], ends[i - 1][0] + 32)
        for yy, label, a, b, colour in ends:
            c.text(x + xr + 12, yy + 1, label, TINY - 1, MEDIUM, colour)
            c.text(x + xr + 12, yy + 15, f"{a} → {b}", TINY - 1.5, SANS, t.muted)
    y = y1 + 50
    used = c.paragraph(M, y, "On 25 questions one answer is 4 points, so every drop here is one or two "
                       "answers. All four of full context's errors on the whole history gave the old "
                       "value, which was in its prompt next to the new one.", W - 2 * M, TINY, SANS, t.muted)
    source_line(c, y + used + 16, "agent-memory-eval: results/main and results/full, the same 25 questions")
    return c
