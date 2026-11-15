"""Honcho: the levels of a conclusion, who writes each one, and the links between them.

Levels and writers are Honcho 3.3.0's (the deriver, src/dreamer/specialists.py, the tools in
src/utils/agent_tools.py). The conclusions are from the first real-server run of the series'
example (scripts/replays/honcho_server_runs/run1.json); the ids are short labels for this figure,
in the order the rows were stored (the server's own ids are 21-character random strings).
"""

from __future__ import annotations

from ..kit import BOLD, ITALIC, MONO, SANS, Box, Canvas, W, M, chip, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line
from .honcho_parts import conclusion, legend

NAME = "honcho-levels"
TITLE = "Levels and links"
ALT = ("Four levels, top to bottom. Contradiction: two statements that cannot both be true; no "
       "component of Honcho 3.3.0 writes it. Inductive, a pattern, written by the dream's induction "
       "agent: 'Anton is highly attentive to dietary restrictions, both his own and those of others', "
       "drawn from E5, E19, E10 and E16. Deductive, what follows and updates, written by the dream's "
       "deduction agent: the update 'Anton transitioned from a vegetarian diet to a pescatarian diet "
       "in June 2026', drawn from E2, E17 and E13, and 'Anton requires a peanut-free restaurant', "
       "drawn from E5. Explicit, what was said, written by the deriver as messages arrive: the "
       "vegetarian fact E2 (deleted in dream 2), the peanut allergy E5 and again E19, starting to eat "
       "fish E17, pescatarian E13, Lena's shellfish E10 and Jonas's coeliac disease E16. Abduction, "
       "which Honcho's documentation describes, has no level in the code.")

BANDS = [
    ("contradiction", "two statements that cannot both be true", "no writer in 3.3.0", "stale", []),
    ("inductive", "a pattern across conclusions", "dream: induction agent", "llm", [
        ("I23", "Anton is highly attentive to dietary restrictions, both his own and those of others in "
                "his social circle.", "live", "from E5, E19, E10, E16 · medium")]),
    ("deductive", "what follows; an update when a fact changes", "dream: deduction agent", "llm", [
        ("D20", "Anton transitioned from a vegetarian diet to a pescatarian diet in June 2026.", "update",
         "from E2, E17, E13"),
        ("D8", "Anton requires a peanut-free restaurant for his dinner in Berlin.", "live", "from E5")]),
    ("explicit", "what the peer said", "deriver, as messages arrive", "llm", [
        ("E2", "Anton has followed a strict vegetarian diet for eight years.", "deleted", "14 March"),
        ("E5", "Anton has a severe, anaphylactic peanut allergy.", "live", "14 March"),
        ("E17", "Anton started eating fish in June 2026.", "live", "20 July"),
        ("E13", "Anton identifies as a pescatarian as of July 2026.", "live", "20 July"),
        ("E19", "Anton has a peanut allergy.", "live", "20 July"),
        ("E10", "Anton's sister Lena is unable to eat shellfish.", "live", "20 July"),
        ("E16", "Anton's sister's partner Jonas is coeliac.", "live", "20 July")]),
]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Each derived conclusion keeps the ids of the conclusions it was drawn "
                       "from. The labels E2, D20, … are this figure's; the links are the server's.",
                       W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 26
    legend(c, M, y, ["live", "update", "deleted"])
    y += 22
    label_w = 190
    area_x = M + label_w
    area_w = W - M - area_x
    for level, meaning, writer, role, cards in BANDS:
        cols = 4 if len(cards) > 2 else max(1, len(cards))
        gap = 8
        cw = (area_w - 16 - gap * (cols - 1)) / cols if cards else area_w
        # lay out the cards in rows of `cols`
        rows, row, heights = [], [], []
        for card in cards:
            row.append(card)
            if len(row) == cols:
                rows.append(row)
                row = []
        if row:
            rows.append(row)
        top = y + 12
        band_h = 74
        if cards:
            # draw cards to measure; a first pass at a hidden position is not available, so estimate
            est = []
            for r in rows:
                est.append(max(_card_height(text, note, cw) for _, text, _, note in r))
            band_h = max(band_h, 24 + sum(est) + gap * (len(rows) - 1))
        band = Box(M, y, W - 2 * M, band_h)
        if cards:
            c.rect(band, fill=t.surface, r=12)
        else:
            c.rect(band, fill=t.paper, stroke=t["stale"].accent, r=12, dash="5 4", width=1.1)
        c.text(M + 14, y + 26, level, SMALL, MONO, t["store"].accent if cards else t["stale"].accent)
        for i, line in enumerate(wrap(meaning, TINY, label_w - 28, ITALIC)):
            c.text(M + 14, y + 46 + i * TINY * 1.3, line, TINY, ITALIC, t.muted)
        if cards:
            chip(c, M + 14, y + band_h - 30, writer, role, size=TINY - 1, icon="sparkles")
        else:
            box = chip(c, area_x + 12, y + 14, writer, "stale", icon="x", size=TINY - 0.5)
            c.text(area_x + 12, box.bottom + 20, "The deduction prompt asks for it; its only tool for "
                   "writing stores every row as deductive.", TINY, SANS, t.muted)
        ry = top
        for r, h in zip(rows, est if cards else []):
            for j, (cid, text, state, note) in enumerate(r):
                conclusion(c, area_x + 8 + j * (cw + gap), ry, cw, level, text, state, tag=cid, note=note)
            ry += h + gap
        y += band_h + 10
    y += 4
    c.paragraph(M, y, "Abduction, “inferring the simplest explanations for observed behavior”, is described in "
                "Honcho's documentation and has no level or component in the code. Nothing checks that a "
                "conclusion cites only lower levels: in the same run, a pattern cited another pattern.",
                W - 2 * M, TINY, SANS, t.muted)
    source_line(c, y + 52, "From the first run of a Honcho 3.3.0 server on the example")
    return c


def _card_height(text, note, w, size=TINY):
    lines = wrap(text, size, w - 16)
    note_lines = wrap(note, size - 0.5, w - 16, ITALIC) if note else []
    return 8 + 13 + len(lines) * size * 1.35 + (len(note_lines) * (size - 0.5) * 1.3 + 3 if note_lines else 0) + 6
