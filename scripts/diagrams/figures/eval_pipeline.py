"""How one question runs through the experiment, and where the three probes read.

The same steps for every arm (src/memeval/run.py, score.py): the sessions go in one at a
time with their dates, the system writes, the read path picks what the answering model sees,
LongMemEval's answer prompt and judge prompt do the rest. The probes (src/memeval/prompts.py)
read the whole memory, the context given to the answer, and the answer.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, SANS, Box, Canvas, W, M, arrow, icon_tile, wrap
from ..theme import SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "eval-pipeline"
TITLE = "How one question is run and scored"
ALT = ("Six steps from left to right. History: the trimmed history, ten sessions fed one at a time "
       "with their dates. Write: the memory system turns each session into memory; the two baselines "
       "skip this step. Memory: what the system keeps. Read: at the question's date, the system "
       "picks what the answering model sees. Answer: the same model and LongMemEval's answer prompt "
       "for every system. Judge: LongMemEval's knowledge-update judge prompt answers yes or no. "
       "Three probes, each a model call, read the memory (is the new value stored, is the old one "
       "still there and still current), the context given to the answer (did the new value and "
       "the old one reach it), and the answer (did it give the old value).")

STEPS = [
    ("History", "person", "history", "10 sessions, fed one at a time, each with its date"),
    ("Write", "llm", "sparkles", "the system turns each session into memory (the baselines skip this)"),
    ("Memory", "store", "database", "what the system keeps: a profile, facts, a graph, blocks or conclusions"),
    ("Read", "code", "search", "at the question's date, a search or a model call picks what the answering model sees"),
    ("Answer", "llm", "sparkles", "the same model and LongMemEval's answer prompt for every system"),
    ("Judge", "llm", "check", "LongMemEval's knowledge-update prompt: is the answer correct, yes or no"),
]
PROBES = {
    2: ("Probe 1: stored", "Is the new value in the memory? Is the old one, and is it still "
        "presented as current?"),
    3: ("Probe 2: delivered", "Did the new value, and the old one, reach the answering model?"),
    4: ("Probe 3: answered", "Did the answer give the old value?"),
}


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The same six steps for every system. The judge gives the score; three "
                       "probes say where a wrong answer was lost.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 28
    gap = 18
    w = (W - 2 * M - gap * (len(STEPS) - 1)) / len(STEPS)
    pad = 10
    body_h = max(len(wrap(body, TINY, w - 2 * pad, SANS)) for *_, body in STEPS) * TINY * 1.38
    h = pad + 30 + 10 + body_h + pad
    boxes = []
    for i, (title, role, icon, body) in enumerate(STEPS):
        x = M + i * (w + gap)
        box = Box(x, y, w, h)
        c.rect(box, fill=t.card, stroke=t[role].accent, r=10, width=1.6 if role == "llm" else 1.0)
        icon_tile(c, x + pad, y + pad, role, icon, 26)
        c.text(x + pad + 34, y + pad + 18, title, 14, BOLD, t.ink)
        c.paragraph(x + pad, y + pad + 34, body, w - 2 * pad, TINY, SANS, t.muted)
        boxes.append(box)
    for a, b in zip(boxes, boxes[1:]):
        arrow(c, [(a.right + 2, a.cy), (b.x - 2, b.cy)], t.ink, width=1.3)

    # the probes, in three slots under the steps they read
    py = y + h + 60
    colour = t["both"]
    slot_gap = 24
    slot_w = (W - 2 * M - 2 * slot_gap) / 3
    probe_h = max(30 + len(wrap(text, TINY, slot_w - 2 * pad, SANS)) * TINY * 1.38 + pad
                  for _, text in PROBES.values())
    for slot, (i, (head, text)) in enumerate(PROBES.items()):
        target = boxes[i]
        anchor_x = (boxes[3].right + boxes[4].x) / 2 if i == 3 else target.cx
        start = target.cy if i == 3 else target.bottom + 4
        bx = M + slot * (slot_w + slot_gap)
        pbox = Box(bx, py, slot_w, probe_h)
        mid = y + h + 22 + slot * 8
        c.path(f"M {anchor_x:.1f} {start:.1f} L {anchor_x:.1f} {mid:.1f} L {pbox.cx:.1f} {mid:.1f} "
               f"L {pbox.cx:.1f} {py - 2:.1f}", stroke=colour.accent, width=1.2, dash="3 3")
        c.circle(anchor_x, start, 3.5, fill=colour.accent)
        c.rect(pbox, fill=colour.wash, stroke=colour.accent, r=8, width=1.0, dash="5 4")
        c.text(bx + pad, py + 20, head, TINY, BOLD, colour.ink)
        c.paragraph(bx + pad, py + 25, text, slot_w - 2 * pad, TINY, SANS, colour.ink)
    note_y = py + probe_h + 22
    c.paragraph(M, note_y, "Each probe is a model call that reads text: the whole memory, the context "
                "given to the answer, or the answer. The old value is read once per question from the "
                "first evidence session. For the baselines nothing is written, so only probes 2 and 3 apply.",
                W - 2 * M, TINY, SANS, t.muted)
    source_line(c, note_y + 50, "agent-memory-eval: src/memeval/run.py, score.py, prompts.py")
    return c
