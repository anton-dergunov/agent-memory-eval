"""Honcho on the benchmark: one store, two read paths, for a fact with two values.

Question 4d6b87c8 of the experiment ("How many titles are currently on my to-watch list?"):
the two stored conclusions, the dialectic's reply and both answers, quoted from
results/main/honcho-chat and honcho-repr and docs/findings/honcho.md. The two rules are sections of
the dialectic's system prompt in Honcho 3.3.0 (src/dialectic/prompts.py).
"""

from __future__ import annotations

from ..kit import BOLD, ITALIC, MEDIUM, MONO, SANS, Box, Canvas, W, M, arrow, chip, heading, icon_tile, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "honcho-conflict"
TITLE = "Two values, two read paths"
ALT = ("A benchmark question: 'How many titles are currently on my to-watch list?' The store holds "
       "two explicit conclusions: 20 titles, said on 20 May at 10:21, and 25 titles, said on 22 May "
       "at 03:29. Left, the representation hands both dated lines to the answering model, which "
       "answers: 'The most recent record… is from May 22, 2023, which states the list consists of 25 "
       "titles.' Correct. Right, the dialectic's prompt has two rules for this case: ask the user "
       "which statement is correct, and the more recent statement supersedes. Its reply lists both "
       "values and ends 'Which of these numbers is correct?'. The answering model, given that reply, "
       "answers that it is not possible to determine the number. Five of the dialectic path's nine "
       "wrong answers were of this kind. Honcho 3.5.0 later made the dialectic answer in a single "
       "turn.")


def card(c, x, y, w, lines_text, role, size=SMALL, face=SANS, title=None, icon=None):
    t = c.theme
    lines = wrap(lines_text, size, w - 24, face)
    top = 30 if title else 10
    h = top + len(lines) * size * 1.4 + 12
    box = Box(x, y, w, h)
    c.rect(box, fill=t[role].wash if role else t.card, stroke=t[role].accent if role else t.line, r=10,
           width=1.2 if role else 1)
    if title:
        if icon:
            c.icon(icon, x + 12, y + 9, 15, t[role].accent if role else t.muted)
        c.text(x + (34 if icon else 12), y + 21, title, TINY, BOLD, t[role].ink if role else t.muted)
    for i, line in enumerate(lines):
        c.text(x + 12, y + top + size + i * size * 1.4 - 2, line, size, face, t[role].ink if role else t.ink)
    return box


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "A question from the experiment. The store holds both values with their "
                       "times; the two read paths hand them over in different shapes.",
                       W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30
    heading(c, M, y, W - 2 * M, "THE STORE", "“How many titles are currently on my to-watch list?”")
    y += 18
    rows = [("[2023-05-20 10:21:00]", "user has a to-watch list consisting of 20 titles."),
            ("[2023-05-22 03:29:00]", "user has a to-watch list consisting of 25 titles.")]
    store = Box(M + 100, y, W - 2 * M - 200, 74)
    c.rect(store, fill=t["store"].wash, r=12)
    for i, (when, text) in enumerate(rows):
        ry = y + 28 + i * 26
        w = c.text(store.x + 16, ry, when, TINY, MONO, t["store"].accent)
        c.text(store.x + 22 + w, ry, text, SMALL, SANS, t["store"].ink)
    y = store.bottom + 40
    half = (W - 2 * M - 30) / 2
    lx, rx = M, M + half + 30
    heading(c, lx, y, half, "REPRESENTATION", "no model call")
    heading(c, rx, y, half, "DIALECTIC", "an agent")
    arrow(c, [(lx + half - 50, store.bottom), (lx + half - 50, y - 16)], t.muted, dashed=True)
    arrow(c, [(rx + half - 50, store.bottom), (rx + half - 50, y - 16)], t.muted, dashed=True)
    y += 22
    left_in = card(c, lx, y, half, "Both lines, each with its time, go to the answering model as they are.",
                   None, size=SMALL, title="What is handed over", icon="list")
    c.text(rx, y + 14, "Two sections of its prompt fit this case:", TINY, BOLD, t.muted)
    r1 = chip(c, rx, y + 24, "“Ask the user which statement is correct”", "stale", icon="target", size=TINY)
    r2 = chip(c, rx, r1.bottom + 6, "“The MORE RECENT statement supersedes”", "store", size=TINY, outline=True)
    reply = card(c, rx, r2.bottom + 12, half, "“… I do not have information confirming whether your list "
                 "was updated or if one of these figures was recorded in error. Which of these numbers is "
                 "correct?”", "llm", size=SMALL, face=ITALIC, title="Its reply, handed over", icon="bot")
    y = max(left_in.bottom, reply.bottom) + 16
    c.text(M, y + 12, "The answering model, given what each path handed over:", TINY, BOLD, t.muted)
    y += 22
    left = card(c, lx, y, half, "“The most recent record… is from May 22, 2023, which states the list "
                "consists of 25 titles.”", "store", face=ITALIC, title="Correct", icon="check")
    right = card(c, rx, y, half, "“It is not possible to determine the exact number of titles currently on "
                 "your to-watch list. The history contains conflicting information (20 titles on May 20 vs. "
                 "25 titles on May 22)…”", "stale", face=ITALIC, title="Wrong", icon="x")
    y = max(left.bottom, right.bottom) + 20
    used = c.paragraph(M, y, "Five of the dialectic path's nine wrong answers were of this kind. "
                       "Honcho 3.5.0 (released 30 October 2026, after the experiment) made the dialectic "
                       "answer in a single turn, without a question at the end.", W - 2 * M, TINY, SANS, t.muted)
    source_line(c, y + used + 14, "From the experiment, question 4d6b87c8, Honcho 3.3.0")
    return c
