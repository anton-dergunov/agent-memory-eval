"""How a system is fed: Graphiti's and Letta's first runs against the runs that fed them as
they were built to be fed.

Numbers from results/main/report.md and docs/experiment-results.md (point 1); the traced
example (the painting classes) from docs/findings/graphiti.md.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, SANS, Box, Canvas, W, M, wrap
from ..theme import SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "feeding"
TITLE = "The same system, fed two ways"
ALT = ("Two panels. Graphiti: in the first run each session was cut into episodes of up to 8,000 "
       "characters, many messages in one episode; it answered 18% of the questions, the update was "
       "never stored in 45 of 67, at $0.24 per question. Fed one message per episode, as its own "
       "examples do, it answered 82%, the update was never stored in 5, at $0.64. Letta: in the "
       "first run each session was sent in one request ending on an assistant message, and the "
       "agent mostly took no step; 58%, 22 updates never stored, $0.03. With one agent step per "
       "user message it edited its memory about nine times per history; 69%, 15, $0.13.")

# (system, [(how it was fed, groups of messages, result line, note)])
PANELS = [
    ("Graphiti", [
        ("First run: each session cut into episodes of up to 8,000 characters",
         [["u", "a", "u", "a", "u", "a"], ["u", "a", "u", "a"]], "episode",
         ("18%", "45", "$0.24"),
         "Each extraction prompt carried 60,000–80,000 characters, mostly the assistant's answers. "
         "The model returned two or three entities per episode."),
        ("Second run: one episode per message, as Graphiti's own examples do",
         [["u"], ["a"], ["u"], ["a"], ["u"], ["a"], ["u"], ["a"], ["u"], ["a"]], "episode",
         ("82%", "5", "$0.64"),
         "The same revision now became a fact: “The user has completed their 5th project since "
         "they began attending painting classes”."),
    ]),
    ("Letta", [
        ("First run: a whole session in one request, ending on an assistant message",
         [["u", "a", "u", "a", "u", "a", "u", "a", "u", "a"]], "request",
         ("58%", "22", "$0.03"),
         "With nothing to reply to, the agent mostly took no step. Its block about the user was "
         "empty after 43 of 67 histories."),
        ("Second run: one agent step per user message",
         [["u"], ["u"], ["u"], ["u"], ["u"]], "step",
         ("69%", "15", "$0.13"),
         "The agent replied to each user message itself (the recorded replies were not sent) and "
         "edited its memory about nine times per history."),
    ]),
]


def _messages(c: Canvas, x: float, y: float, groups: list[list[str]], unit: str, theme: Theme) -> float:
    t = theme
    mw, gap = 13, 3
    for group in groups:
        w = len(group) * (mw + gap) + 7
        c.rect(Box(x, y, w, 30), stroke=t["llm"].accent, r=6, width=1.2, dash="4 3")
        for i, who in enumerate(group):
            role = "person" if who == "u" else "code"
            c.rect(Box(x + 5 + i * (mw + gap), y + 6, mw, 18), fill=t[role].wash, stroke=t[role].accent,
                   r=3, width=0.7)
        x += w + 6
    return x


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The first runs of two systems scored far lower than the others. Neither "
                       "reported an error. Feeding them the conversation the way each was built for "
                       "changed the result; no setting was changed.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 26
    x = M
    for label, role in [("a user message", "person"), ("an assistant message", "code")]:
        c.rect(Box(x, y - 12, 12, 15), fill=t[role].wash, stroke=t[role].accent, r=3, width=0.7)
        x += 18 + c.text(x + 18, y, label, TINY, SANS, t.muted) + 16
    c.rect(Box(x, y - 13, 22, 17), stroke=t["llm"].accent, r=4, width=1.2, dash="4 3")
    c.text(x + 28, y, "what one call to the system receives", TINY, SANS, t.muted)
    y += 22
    col_gap = 28
    col_w = (W - 2 * M - col_gap) / 2
    bottom = y
    for p, (system, cards) in enumerate(PANELS):
        x = M + p * (col_w + col_gap)
        yy = y + 8
        c.text(x, yy + 14, system, 17, BOLD, t.ink)
        yy += 30
        for k, (how, groups, unit, (acc, lost, usd), note) in enumerate(cards):
            pad = 12
            how_lines = wrap(how, TINY, col_w - 2 * pad, MEDIUM)
            note_lines = wrap(note, TINY, col_w - 2 * pad, SANS)
            h = pad + len(how_lines) * TINY * 1.35 + 8 + 30 + 12 + 20 + 6 + len(note_lines) * TINY * 1.38 + pad + 4
            box = Box(x, yy, col_w, h)
            c.rect(box, fill=t.card, stroke=t.line if k == 1 else t["stale"].accent, r=10,
                   width=1.0 if k == 1 else 1.3)
            ty = yy + pad
            for i, line in enumerate(how_lines):
                c.text(x + pad, ty + TINY + i * TINY * 1.35, line, TINY, MEDIUM, t.ink)
            ty += len(how_lines) * TINY * 1.35 + 8
            _messages(c, x + pad, ty, groups, unit, t)
            ty += 30 + 12
            colour = t["stale"].ink if k == 0 else t["store"].ink
            c.runs(x + pad, ty + 14, [(acc + " correct   ", BOLD, colour), ("·   ", SANS, t.muted),
                                      (lost + " updates never stored   ", MEDIUM, t.ink),
                                      ("·   ", SANS, t.muted), (usd + " per question", MEDIUM, t.ink)], TINY)
            ty += 20 + 6
            c.paragraph(x + pad, ty, note, col_w - 2 * pad, TINY, SANS, t.muted)
            yy += h + 12
        bottom = max(bottom, yy)
    source_line(c, bottom + 10, "agent-memory-eval: results/main, 67 questions per run")
    return c
