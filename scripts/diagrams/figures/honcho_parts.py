"""Pieces shared by the Honcho figures: one stored conclusion drawn as a card, in its state.

Not a figure itself (no NAME). The states mean the same thing in every Honcho figure:

- live: an ordinary live conclusion;
- deleted: soft-deleted, struck through;
- stale: live, but it rests on a deleted conclusion and still carries the old value;
- update: the conclusion that records the change.
"""

from __future__ import annotations

from ..kit import ITALIC, MEDIUM, MONO, SANS, Box, Canvas, measure, wrap
from ..theme import TINY

LEVEL_LABEL = {"explicit": "explicit", "deductive": "deductive", "inductive": "inductive",
               "contradiction": "contradiction"}


def conclusion(c: Canvas, x: float, y: float, w: float, level: str, text: str, state: str = "live",
               tag: str | None = None, note: str | None = None, size: float = TINY) -> Box:
    """A conclusion as a small card: its level in mono, an optional tag on the right, its text."""
    t = c.theme
    pad = 8
    lines = wrap(text, size, w - 2 * pad)
    note_lines = wrap(note, size - 0.5, w - 2 * pad, ITALIC) if note else []
    h = pad + 13 + len(lines) * size * 1.35 + (len(note_lines) * (size - 0.5) * 1.3 + 3 if note_lines else 0) + pad - 2
    box = Box(x, y, w, h)
    stale, store = t["stale"], t["store"]
    if state == "deleted":
        c.rect(box, fill=t.paper, stroke=stale.accent, r=7, dash="4 3", width=1.1)
    elif state == "stale":
        c.rect(box, fill=stale.wash, stroke=stale.accent, r=7, width=1.1)
    elif state == "update":
        c.rect(box, fill=store.wash, stroke=store.accent, r=7, width=1.3)
    else:
        c.rect(box, fill=t.card, stroke=t.line, r=7)
    label_colour = stale.accent if state in ("deleted", "stale") else store.accent
    c.text(x + pad, y + pad + 9, LEVEL_LABEL.get(level, level), size - 1.5, MONO, label_colour)
    if tag:
        c.text(box.right - pad, y + pad + 9, tag, size - 1.5, MEDIUM, label_colour, anchor="end")
    ty = y + pad + 13
    ink = stale.ink if state == "stale" else (t.muted if state == "deleted" else t.ink)
    for i, line in enumerate(lines):
        base = ty + size + i * size * 1.35
        c.text(x + pad, base, line, size, SANS, ink)
        if state == "deleted":
            c.line(x + pad, base - size * 0.32, x + pad + measure(line, size), base - size * 0.32,
                   stale.accent, 1.1)
    ny = ty + len(lines) * size * 1.35 + 3
    for i, line in enumerate(note_lines):
        c.text(x + pad, ny + (size - 0.5) + i * (size - 0.5) * 1.3, line, size - 0.5, ITALIC,
               stale.accent if state in ("deleted", "stale") else t.muted)
    return box


def legend(c: Canvas, x: float, y: float, states: list[str]) -> float:
    """A row of small swatches naming the states used. Returns the width."""
    t = c.theme
    names = {"live": "live", "deleted": "deleted (soft)", "stale": "live, but rests on a deleted row",
             "update": "records the change"}
    start = x
    for state in states:
        box = Box(x, y - 10, 22, 13)
        if state == "deleted":
            c.rect(box, fill=t.paper, stroke=t["stale"].accent, r=3, dash="3 2", width=1)
        elif state == "stale":
            c.rect(box, fill=t["stale"].wash, stroke=t["stale"].accent, r=3, width=1)
        elif state == "update":
            c.rect(box, fill=t["store"].wash, stroke=t["store"].accent, r=3, width=1.2)
        else:
            c.rect(box, fill=t.card, stroke=t.line, r=3)
        x += 28 + c.text(x + 28, y, names[state], TINY, SANS, t.muted) + 18
    return x - start
