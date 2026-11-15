"""Mem0: what happens to a new fact in the paper's design and in the release.

Left, the two phases of the Mem0 paper (arXiv 2504.19413, pp. 3-4). Right, the write path of
mem0ai 2.2.1 as read from `mem0/memory/main.py` (`_add_to_vector_store`). The two rows at the
bottom are from the committed run of notebooks/02-mem0.ipynb (section 2).
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, MONO, SANS, Box, Canvas, W, M, arrow, chip, heading, kind_badge, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme

NAME = "mem0-update"
TITLE = "What happens to a new fact"
ALT = ("Two write paths side by side. The Mem0 paper: an LLM call extracts candidate facts from "
       "each pair of messages; code fetches the ten most similar stored facts for each candidate; "
       "a second LLM call chooses one of four operations, ADD, UPDATE, DELETE or NOOP, so a "
       "contradicted fact can be deleted. The release, mem0ai 2.2.1: code fetches the ten stored "
       "facts most similar to the whole session; one LLM call extracts new facts with those ten "
       "in view and can only add; code drops exact duplicates by hash and stores the rest. The "
       "model's links from a new fact to related stored facts are not stored. In the example, "
       "the old fact 'strict vegetarian for eight years' stays in the store next to the new fact "
       "'transitioned from a strict vegetarian diet to a pescatarian diet'.")

PAPER = [
    ("llm", "Extract candidate facts", "From each new pair of messages, with a summary of the "
     "conversation and the last ten messages as context."),
    ("code", "Find similar stored facts", "For each candidate fact, the ten most similar facts "
     "in the store."),
    ("llm", "Choose an operation", "For each candidate fact, the model picks one, through a "
     "tool call:"),
]
RELEASE = [
    ("code", "Find similar stored facts", "Once per add(): the ten stored facts most similar to "
     "the whole new session."),
    ("llm", "Extract new facts", "One call per add(), with those ten facts in view. The prompt: "
     "“Your sole operation is ADD”."),
    ("code", "Store", "Drop a fact whose text is identical to a stored one (a hash). Embed and "
     "insert the rest."),
]
OPS = [("ADD", "store"), ("UPDATE", "both"), ("DELETE", "stale"), ("NOOP", None)]
GAP = 28
PAD = 14


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The Mem0 paper compares each new fact with the stored facts and "
                       "can update or delete one. The open-source release, since version 2.0, "
                       "only adds.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30
    cw = (W - 2 * M - GAP) / 2
    lx, rx = M, M + cw + GAP
    heading(c, lx, y, cw, "THE PAPER", "two LLM steps")
    heading(c, rx, y, cw, "THE RELEASE", "mem0ai 2.2.1 · one LLM step")
    top = y + 22

    ends = []
    for x, steps, paper in ((lx, PAPER, True), (rx, RELEASE, False)):
        yy = top
        for i, (role, title, text) in enumerate(steps):
            h = _step(c, x, yy, cw, i + 1, role, title, text, ops=paper and i == 2)
            if i < len(steps) - 1:
                arrow(c, [(x + cw / 2, yy + h + 2), (x + cw / 2, yy + h + 20)], t.faint, width=1.4)
            yy += h + 22
        ends.append(yy)
    y = max(ends) - 4

    # the outcome of each path
    for x, role, title, text in (
            (lx, "store", "One value per fact",
             "A fact that the new one contradicts can be deleted, or updated in place. The check "
             "covers only the ten most similar facts."),
            (rx, "stale", "Both values stay",
             "Nothing is updated, deleted or marked as replaced. The model's links from a new "
             "fact to related stored facts are not stored either.")):
        r = t[role]
        height = 30 + len(_wrap(text, cw - 2 * PAD)) * TINY * 1.38 + 8
        c.rect(Box(x, y, cw, height), fill=r.wash, r=8)
        c.text(x + PAD, y + 20, title, SMALL, BOLD, r.ink)
        c.paragraph(x + PAD, y + 26, text, cw - 2 * PAD, TINY, SANS, r.ink)
        ends.append(y + height)
    y = max(ends[2:]) + 30

    heading(c, M, y, W - 2 * M, "IN THE EXAMPLE", "the store after the second session, in the release")
    y += 20
    rows = [("stale", "stored after session 1", "User has been a strict vegetarian for eight years.",
             "still stored, still searchable"),
            ("store", "added after session 2", "User transitioned from a strict vegetarian diet to a "
             "pescatarian diet in September 2026, meaning they now eat fish but no other meat.",
             "added; the new fact names the old value in its own sentence")]
    for role, when, text, note in rows:
        r = t[role]
        lines = _wrap(text, W - 2 * M - 2 * PAD - 170, MONO)
        h = max(len(lines) * TINY * 1.4 + 16, 40)
        c.rect(Box(M, y, W - 2 * M, h), fill=r.wash, r=8)
        c.text(M + PAD, y + 18, when, TINY, BOLD, r.ink)
        for i, line in enumerate(lines):
            c.text(M + PAD + 170, y + 18 + i * TINY * 1.4, line, TINY, MONO, r.ink)
        y += h + 4
        c.text(M + PAD + 170, y + 12, note, TINY, SANS, t.muted)
        y += 26

    c.line(M, y, W - M, y, t.line)
    y += 20
    x = M
    for role, label in (("llm", "an LLM call"), ("code", "plain code, no LLM")):
        b = kind_badge(c, x + 62, y - 14, role)
        x = b.right + 8 + c.text(b.right + 8, y, label, TINY, SANS, t.muted) + 18
    c.text(W - M, y, "Left: the Mem0 paper, pp. 3–4. Right: mem0/memory/main.py, version 2.2.1",
           TINY, SANS, t.muted, anchor="end")
    c.height = int(y + 20)
    return c


def _wrap(text: str, width: float, face=SANS) -> list[str]:
    return wrap(text, TINY, width, face)


def _step(c: Canvas, x: float, y: float, w: float, n: int, role: str, title: str, text: str,
          ops: bool = False) -> float:
    """One numbered step with its badge. Returns the height used."""
    t = c.theme
    r = t[role]
    lines = _wrap(text, w - 2 * PAD)
    h = 34 + len(lines) * TINY * 1.38 + (36 if ops else 8)
    c.rect(Box(x, y, w, h), fill=t.card, stroke=r.accent if role == "llm" else t.line, r=8)
    c.text(x + PAD, y + 22, f"{n}", SMALL, BOLD, r.accent)
    c.text(x + PAD + 16, y + 22, title, SMALL, BOLD)
    kind_badge(c, x + w - 10, y + 8, role)
    c.paragraph(x + PAD, y + 28, text, w - 2 * PAD, TINY, SANS, t.muted)
    if ops:
        cx = x + PAD
        cy = y + 28 + len(lines) * TINY * 1.38 + 10
        for label, op_role in OPS:
            b = chip(c, cx, cy, label, op_role, face=MEDIUM, outline=op_role is None)
            cx = b.right + 6
    return h
