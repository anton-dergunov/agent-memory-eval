"""Where each configuration's answers were lost: the probes' breakdown of all 67 answers.

Counts from results/main/report.md ("Where answers were lost"), the same as
scripts/replays/experiment_numbers_output.txt. "Unclassified" is a wrong answer the probes
could not place: most are the 9 questions for which the probe model found no earlier value,
so no probe ran; one Letta question could not be built (the provider's content filter).
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, SANS, Box, Canvas, W, M
from ..theme import SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "answer-loss"
TITLE = "Where the answers were lost"
ALT = ("Stacked bars, one per configuration, of all 67 answers. Correct answers: full context 60, "
       "retrieval 65, textual memory 62, Mem0 56, Graphiti 55, Graphiti with 8,000-character "
       "episodes 12, Letta 46, Letta with whole sessions 39, Letta with the persona 60, Honcho chat "
       "58, Honcho representation 62. Update never stored: 0, 0, 1, 6, 5, 45, 15, 22, 3, 1, 2. "
       "Stored but not delivered: 2 for Graphiti and 1 for Honcho chat. Delivered and answered with "
       "the old value: 5, 2, 1, 2, 1, 0, 0, 0, 0, 3, 1. Delivered, other error: 1, 0, 3, 2, 3, 1, 2, "
       "0, 2, 4, 1. Unclassified: 1, 0, 0, 1, 1, 9, 4, 6, 2, 0, 1.")

# label, variant, counts in the order of PARTS
ROWS = [
    ("Full context", "", (60, 0, 0, 5, 1, 1)),
    ("Retrieval", "BM25 over raw rounds", (65, 0, 0, 2, 0, 0)),
    None,
    ("Textual memory", "", (62, 1, 0, 1, 3, 0)),
    ("Mem0", "", (56, 6, 0, 2, 2, 1)),
    ("Graphiti", "one episode per message", (55, 5, 2, 1, 3, 1)),
    ("Graphiti", "8,000-character episodes", (12, 45, 0, 0, 1, 9)),
    ("Letta", "one step per user message", (46, 15, 0, 0, 2, 4)),
    ("Letta", "a whole session per request", (39, 22, 0, 0, 0, 6)),
    ("Letta", "persona that keeps facts current", (60, 3, 0, 0, 2, 2)),
    ("Honcho", "dialectic chat", (58, 1, 1, 3, 4, 0)),
    ("Honcho", "representation", (62, 2, 0, 1, 1, 1)),
]
PARTS = [("correct", "store"), ("update never stored", "stale"), ("stored, not delivered", "prompt"),
         ("delivered, answered with the old value", "both"), ("delivered, other error", "llm"),
         ("wrong, not classified", None)]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "All 67 answers of each configuration, sorted by the probes. Where a "
                       "memory system lost answers, it was mostly at write time: the update was "
                       "never stored.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 28
    x = M
    for label, role in PARTS:
        fill, stroke = (t[role].wash, t[role].accent) if role else (t.surface, t.faint)
        if role == "store":
            fill = t[role].accent
        box_w = c.text(x + 20, y, label, TINY, SANS, t.muted)
        c.rect(Box(x, y - 11, 14, 14), fill=fill, stroke=stroke, r=3, width=0.8)
        x += 20 + box_w + 16
        if x > W - M - 200 and label != PARTS[-1][0]:
            x, y = M, y + 22
    y += 26
    label_w = 230
    bar_x = M + label_w
    bar_w = W - M - bar_x - 10
    row_h = 30
    for v in (0, 20, 40, 60):
        xx = bar_x + bar_w * v / 67
        c.text(xx, y + 4, str(v), TINY - 1, SANS, t.faint, anchor="middle")
    y += 14
    for row in ROWS:
        if row is None:
            c.line(M, y + 6, W - M, y + 6, t.line)
            y += 14
            continue
        label, variant, counts = row
        c.text(bar_x - 12, y + (13 if variant else 19), label, 14, BOLD, t.ink, anchor="end")
        if variant:
            c.text(bar_x - 12, y + 27, variant, TINY - 1, SANS, t.muted, anchor="end")
        xx = bar_x
        for n, (name, role) in zip(counts, PARTS):
            if not n:
                continue
            w = bar_w * n / 67
            fill, stroke = (t[role].wash, t[role].accent) if role else (t.surface, t.faint)
            if role == "store":
                fill = t[role].accent
            c.rect(Box(xx, y + 4, w, row_h - 8), fill=fill, stroke=stroke, r=2, width=0.7)
            ink = t.paper if role == "store" else (t[role].ink if role else t.muted)
            if w > 16:
                c.text(xx + w / 2, y + row_h / 2 + 5, str(n), TINY - 1, MEDIUM, ink, anchor="middle")
            xx += w
        y += row_h + 4
    y += 10
    used = c.paragraph(M, y, "The probes need the value before the update; in 9 questions the probe model "
                       "found none (six of them ask for the earlier value), so a wrong answer there is not classified. "
                       "Graphiti and Letta were first run with the conversation fed to them another way "
                       "(8,000-character episodes; a whole session per request).", W - 2 * M, TINY, SANS, t.muted)
    source_line(c, y + used + 16, "agent-memory-eval: results/main, 67 questions per configuration")
    return c
