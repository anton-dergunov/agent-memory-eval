"""Which memory design to start from, by situation, each with what this experiment showed.

The evidence lines restate results in docs/experiment-results.md and
scripts/replays/experiment_numbers_output.txt.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, SANS, Box, Canvas, W, M, wrap
from ..theme import SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "decision-guide"
TITLE = "Which design to start from"
ALT = ("Seven rows, each a situation, the design to start from, and what this experiment showed. "
       "The history fits in the prompt: no memory; the whole history, or a keyword search over the "
       "raw turns with their dates. A small profile that people can read and correct: textual memory, "
       "one rewrite per session. Too many facts for one profile: a fact store with search, with dates "
       "written and shown. Earlier values or links between people and things matter: a dated graph. "
       "The agent should decide what to keep: an agent that edits its memory, told when to write, how "
       "to date and what to do with the old value. Answers depend on what the user implies: a "
       "background reasoner, read as dated conclusions. In every case: read what the system stored.")

ROWS = [
    ("The history fits in the prompt", "No memory: the whole history, or a keyword search over the raw "
     "turns with their dates", "code",
     "Search over raw turns scored highest (97%) at the lowest cost ($0.002 per question); it writes "
     "nothing, so it cannot lose an update."),
    ("A person should be able to read and correct the memory", "Textual memory: one profile, rewritten "
     "after each session", "store",
     "93%. It kept the old value as current in only 9% of questions; its write cost grew 13 "
     "times on the whole history."),
    ("Too many facts for one profile", "A fact store with search (Mem0), with the conversation's dates "
     "written into the facts and shown at read time", "store",
     "84%. Old and new values were both kept; when both reached the answering model with their "
     "dates, it answered 41 of 45 correctly."),
    ("Earlier values, or links between people and things, matter", "A dated graph (Graphiti), fed one "
     "message at a time", "store",
     "Answered all 8 questions about an earlier value, at about 30 times the cost of textual memory "
     "and with a graph database to run."),
    ("The agent itself should decide what to keep", "An agent that edits its memory (Letta), told when "
     "to write, how to date and what to do with the old value", "llm",
     "69% as shipped; 90% with three lines in its persona that say exactly that."),
    ("Answers depend on what the user implies", "A background reasoner (Honcho), read as a list of "
     "dated conclusions", "llm",
     "93% as a dated list; 87% through its chat agent, which declined to choose between two dated "
     "values."),
]
LAST = ("In every case", "Read what the system stored, not only its score",
        "Two configurations scored 18% and 58% with no error anywhere, until the stored memory was read.")


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Defaults by situation, not a ranking. Each row says what this experiment "
                       "showed about the design.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 26
    c1, c2 = 210, 300
    c3 = W - 2 * M - c1 - c2 - 2 * 16
    for label, x in (("IF", M), ("START WITH", M + c1 + 16), ("IN THIS EXPERIMENT", M + c1 + c2 + 32)):
        c.text(x, y, label, TINY, BOLD, t.muted, spacing=1.6)
    y += 12
    for situation, design, role, evidence in ROWS + [(LAST[0], LAST[1], "both", LAST[2])]:
        pad = 10
        a = wrap(situation, TINY + 0.5, c1 - 2 * pad, MEDIUM)
        b = wrap(design, TINY + 0.5, c2 - 2 * pad, BOLD)
        e = wrap(evidence, TINY, c3, SANS)
        h = max(len(a), len(b), len(e)) * TINY * 1.4 + 2 * pad
        c.rect(Box(M, y, c1, h), fill=t.surface, r=8)
        c.rect(Box(M + c1 + 16, y, c2, h), fill=t[role].wash, stroke=t[role].accent, r=8, width=0.9)
        for i, line in enumerate(a):
            c.text(M + pad, y + pad + TINY + i * TINY * 1.4, line, TINY + 0.5, MEDIUM, t.ink)
        for i, line in enumerate(b):
            c.text(M + c1 + 16 + pad, y + pad + TINY + i * TINY * 1.4, line, TINY + 0.5, BOLD, t[role].ink)
        for i, line in enumerate(e):
            c.text(M + c1 + c2 + 32, y + pad + TINY + i * TINY * 1.4, line, TINY, SANS, t.muted)
        c.text(M + c1 + 3, y + h / 2 + 5, "→", 15, BOLD, t.faint)
        y += h + 10
    source_line(c, y + 10, "agent-memory-eval: LongMemEval knowledge-update questions, 67 per configuration")
    return c
