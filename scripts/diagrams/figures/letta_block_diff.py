"""Letta: how the in-line agent's block changed in session 2, and what each replace sent.

From the committed run of notebooks/04-letta.ipynb (sections 1 and 2): the five edits of sessions
1 and 2 with their arguments, and the block after session 2. For each memory_replace, the length of
old_string and how much of it actually changed (the span between the common prefix and suffix of
old_string and new_string).
"""

from __future__ import annotations

import re

from ..kit import BOLD, MEDIUM, MONO, SANS, Box, Canvas, W, M, chip, heading, measure, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "letta-block-diff"
TITLE = "How the block changed"
ALT = ("Top, the five memory edits of sessions 1 and 2. Session 1, second message: memory_insert, "
       "one paragraph. Session 2: memory_replace with an old_string of 253 characters, the whole "
       "block, of which 26 characters changed: 'strict vegetarian (8 years' became 'pescatarian "
       "(recently started eating fish'; two memory_insert calls of one line each; and "
       "memory_replace with an old_string of 438 characters, the whole block, of which nothing "
       "changed: one sentence of 52 characters was appended. Bottom, the block after session 2, "
       "with the replaced phrase, the two inserted lines and the appended sentence marked. Three "
       "notes: the earlier value is gone; 'about a month ago' became 'recently'; 'Lena can't eat "
       "shellfish' became 'Lena has a shellfish allergy'.")

EDITS = [  # (turn, tool, sent, changed, note)
    ("session 1 · message 2", "memory_insert", 0, 253, "one paragraph, everything from both messages"),
    ("session 2 · message 1", "memory_replace", 253, 26, "to change the diet"),
    ("session 2 · message 2", "memory_insert", 0, 93, "one line, the move to Kreuzberg"),
    ("session 2 · message 3", "memory_insert", 0, 75, "one line, Lena and Jonas"),
    ("session 2 · message 4", "memory_replace", 438, 0, "to append one sentence of 52 characters"),
]
# The block after session 2, as runs of (text, style): None, "replaced", "inserted", "appended".
BLOCK = [
    [("The user is a ", None), ("pescatarian (recently started eating fish", "replaced"),
     (") with a severe, anaphylactic peanut allergy. They are planning a dinner in Berlin for "
      "their sister's visit. They prefer Indian cuisine, specifically paneer dishes, and have a "
      "budget of around 40 euros per person.", None)],
    [("They recently moved to Kreuzberg (May), so restaurants within walking distance are "
      "preferred.", "inserted")],
    [("The user's sister, Lena, is visiting in the autumn with her partner, Jonas.", "inserted"),
     (" Lena has a shellfish allergy, and Jonas is coeliac.", "appended")],
]
STYLE = {"replaced": "both", "inserted": "store", "appended": "store"}
PAD = 12


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The agent's five edits in sessions 1 and 2. Both replaces sent the "
                       "whole block as the text to find, although each changed a small part of it, "
                       "or nothing.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30
    heading(c, M, y, W - 2 * M, "THE EDITS", "for each replace: the text sent, to scale, and the part that changed")
    y += 26
    label_w = 300
    bar_x = M + label_w
    bar_w = W - M - bar_x
    top = max(sent for _, _, sent, _, _ in EDITS)
    for turn, tool, sent, changed, note in EDITS:
        c.text(M, y + 12, turn, TINY, BOLD)
        c.text(M + 150, y + 12, tool, TINY, MONO, t["llm"].accent)
        if sent:
            w = bar_w * sent / top
            c.rect(Box(bar_x, y, w, 18), fill=t["stale"].wash, stroke=t["stale"].accent, r=3, width=0.8)
            if changed:
                cw = max(3, bar_w * changed / top)
                c.rect(Box(bar_x + 14 / 253 * w, y, cw, 18), fill=t["both"].accent, r=2)
            text = (f"old_string: {sent} characters, the whole block; {changed} changed"
                    if changed else f"old_string: {sent} characters, the whole block; none changed")
            c.text(bar_x, y + 34, text, TINY, MEDIUM, t["stale"].ink)
            c.text(bar_x, y + 50, note, TINY, SANS, t.muted)
            y += 64
        else:
            c.text(bar_x, y + 12, f"inserted {changed} characters: {note}", TINY, SANS, t.muted)
            y += 30
    y += 14

    heading(c, M, y, W - 2 * M, "THE BLOCK AFTER SESSION 2", "490 characters")
    y += 18
    inner = W - 2 * M - 2 * PAD
    rows = []
    for line in BLOCK:
        # wrap the line as one text, then colour the runs on each wrapped line
        rows.append(_layout(line, inner))
    h = sum(len(r) for r in rows) * 17 + (len(rows) - 1) * 8 + 2 * PAD
    c.rect(Box(M, y, W - 2 * M, h), fill=t.card, stroke=t["store"].accent, r=8)
    yy = y + PAD + 12
    for row in rows:
        for segments in row:
            x = M + PAD
            for text, style in segments:
                if not text:
                    continue
                lead = len(text) - len(text.lstrip())
                if lead:   # SVG drops a run's leading spaces: draw them as an offset
                    x += measure(" " * lead, TINY, MONO)
                    text = text.lstrip()
                w = measure(text, TINY, MONO)
                if style:
                    c.rect(Box(x - 1, yy - 12, w + 2, 16), fill=t[STYLE[style]].wash, r=2)
                c.text(x, yy, text, TINY, MONO, t[STYLE[style]].ink if style else t.ink)
                x += w
            yy += 17
        yy += 8
    y += h + 14
    x = M
    for style, label in (("replaced", "replaced in place"), ("inserted", "inserted, or appended by a replace")):
        c.rect(Box(x, y - 11, 14, 14), fill=t[STYLE[style]].wash, stroke=t[STYLE[style]].accent, r=3, width=0.8)
        x += 20 + c.text(x + 20, y, label, TINY, SANS, t.muted) + 22
    y += 26
    for text in ("The earlier value is gone: nothing says the user was vegetarian, or until when.",
                 "“About a month ago” became “recently”; “(8 years)” was dropped.",
                 "“Lena can't eat shellfish” became “Lena has a shellfish allergy”."):
        c.text(M, y, "•", TINY, BOLD, t["stale"].accent)
        c.text(M + 14, y, text, TINY, SANS, t.ink)
        y += 19
    source_line(c, y + 8, "From notebooks/04-letta.ipynb, sections 1 and 2")
    return c


def _layout(runs, width):
    """Wrap a list of (text, style) runs to `width`, keeping the styles. Returns lines of runs."""
    words = []
    for text, style in runs:
        for word in re.findall(r"\s*\S+\s*", text):   # keep the spaces with the words
            words.append((word, style))
    lines, line, used = [], [], 0.0
    for word, style in words:
        w = measure(word, TINY, MONO)
        if used + w > width and line:
            lines.append(line)
            word = word.lstrip()
            w = measure(word, TINY, MONO)
            line, used = [], 0.0
        if line and line[-1][1] == style:
            line[-1] = (line[-1][0] + word, style)
        else:
            line.append((word, style))
        used += w
    if line:
        lines.append(line)
    return lines
