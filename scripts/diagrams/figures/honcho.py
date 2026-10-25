"""Honcho: conclusions at four levels of certainty, derived on arrival and in the background;
read through Honcho's own agent (dialectic) or as the conclusions themselves (representation).

Every example below is from the committed run of notebooks/05-honcho.ipynb, shortened to fit: the
live store and what was retired (section 4), the induction (section 5), the dialectic call and
its answer (section 7), the cost (section 8). The two read paths are Honcho's API, described in
section 0 and in the experiment's findings; the notebook re-implements the dialectic one.
"""

from __future__ import annotations

from ..kit import (BOLD, ITALIC, MEDIUM, MONO, SANS, Box, Canvas, W, answer_card, arrow, bubble, column,
                   footer, frame, heading, measure, node, panel, prompt_card, segment, wrap)
from ..theme import TINY, Theme

NAME = "honcho"
TITLE = "Honcho"
ALT = ("Honcho's architecture, with the running example. Writing: when messages arrive, a "
       "deriver makes one LLM call that extracts what was said as explicit conclusions; later, "
       "in the background, a dreamer reasons over the store and adds deductive and inductive "
       "conclusions, retiring outdated ones. Memory: conclusions at four levels of certainty "
       "(explicit, deductive, inductive, and abductive, which Honcho announced but has not "
       "implemented), each citing its premises; the vegetarian fact and a deduction drawn from "
       "it were retired. Reading: either Honcho's dialectic agent writes an answer from the "
       "conclusions (an LLM call), or the representation endpoint returns the conclusions "
       "themselves (no LLM call). All six constraints reached the prompt.")

SESSION_1 = ("“I've been strictly vegetarian for eight years, and I have a severe peanut "
             "allergy … Indian, usually.”")
SESSION_2 = ("“So I'm pescatarian now, not vegetarian … I moved to Kreuzberg in May … Lena "
             "can't eat shellfish, and Jonas is coeliac.”")
QUESTION = ("“My sister and her partner are in town tonight. Book the three of us somewhere for "
            "dinner — you know what we can and can't eat.”")

# The levels, top to bottom: name, what it means, live count, and example conclusions as
# (id, text, retired). Ids are the notebook's.
LEVELS = [
    ("ABDUCTIVE", "a guess about why", None, []),
    ("INDUCTIVE", "a pattern", "2", [
        ("i26", "Needs strict dietary accommodations for himself and his guests", False)]),
    ("DEDUCTIVE", "what follows", "7", [
        ("d21", "No longer strictly vegetarian, as of June 2026", False),
        ("d7", "Must avoid peanuts in Indian dishes", False),
        ("d6", "Does not consume meat or fish", True)]),
    ("EXPLICIT", "what was said", "14", [
        ("e11", "Started eating fish in June 2026", False),
        ("e20", "Sister's partner Jonas is coeliac", False),
        ("e1", "Strictly vegetarian since March 2018", True)]),
]
CITES = ("d21", ["e11", "e1"])   # d21's premises, drawn as links

# The answering call's input: every live conclusion with its level (section 7), a few of 23.
PACKET = [
    ("EXPLICIT ", "Anton is pescatarian", None), ("EXPLICIT ", "Jonas is coeliac", None),
    ("EXPLICIT ", "Lena: no shellfish", None), ("DEDUCTIVE", "No longer vegetarian", None),
    ("DEDUCTIVE", "Allergy is anaphylactic", None), ("INDUCTIVE", "Needs strict accommodations", None),
]

ANSWER = ("Will book Indian in or near Kreuzberg, about 40 € a head, with paneer: no peanuts, "
          "no shellfish for Lena, gluten-free for Jonas.")
NEEDS = [("diet", "yes"), ("peanuts", "yes"), ("shellfish", "yes"), ("gluten", "yes"),
         ("cuisine", "yes"), ("area", "yes")]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, "Honcho: a reasoner that works in the background", ALT)
    t = theme
    top = frame(
        c, "Honcho",
        "Memory as reasoning about a person: conclusions at four levels of certainty, each "
        "citing the conclusions it was drawn from. Most of the reasoning runs in the background.",
        captions={"write": "Turns a conversation into memory. What was said, on arrival; the "
                           "reasoning, later, in the background."})

    wx, ww = column("write")
    b1 = bubble(c, wx, top, ww, "March · session 1", SESSION_1)
    b2 = bubble(c, wx, b1.bottom + 14, ww, "July · session 2", SESSION_2)
    rx, rw = column("read")
    q = bubble(c, rx, top, rw, "September · session 3", QUESTION, target=True)

    row = max(b2.bottom, q.bottom) + 34
    deriver = node(
        c, wx, row, ww, "llm", "sparkles", "Deriver",
        body="As messages arrive: extracts what was said, as EXPLICIT conclusions only.",
        tags=[{"text": "1 LLM call per session", "role": "llm", "icon": "sparkles"}])
    dreamer = node(
        c, wx, deriver.bottom + 16, ww, "llm", "moon", "Dreamer",
        body="Later, in the background: deduces what follows, finds patterns, and retires "
             "what is outdated.",
        tags=[{"text": "4 LLM calls in this run", "role": "llm", "icon": "sparkles"}])
    arrow(c, [(wx + 30, b2.bottom + 4), (wx + 30, deriver.y)], t["person"].accent)

    # read: one of two paths, in a group
    group_top = row
    c.text(rx + 42, group_top + 19, "one of two read paths", TINY, BOLD, t.muted)
    chat = node(
        c, rx + 8, group_top + 40, rw - 16, "llm", "bot", "Dialectic", api="peer.chat(question)",
        body="Honcho's agent searches the conclusions and writes a short answer.",
        tags=[{"text": "the path this run takes", "role": "llm"}], pad=12)
    c.text(rx + rw / 2, chat.bottom + 22, "or", TINY, ITALIC, t.muted, anchor="middle")
    rep = node(
        c, rx + 8, chat.bottom + 40, rw - 16, "code", "list", "Representation",
        api="peer.representation()",
        body="Returns the matching conclusions themselves, with their dates.", pad=12)
    group = Box(rx, group_top, rw, rep.bottom + 10 - group_top)
    c.rect(group, stroke=t.line, r=14, dash="4 3")
    arrow(c, [(rx + 30, q.bottom + 4), (rx + 30, group.y)], t["person"].accent)

    sx, sw = column("store")
    store = _ladder(c, sx, top, sw)

    arrow(c, [(deriver.right, deriver.y + 34), (sx, deriver.y + 34)], t.ink, label="explicit")
    # the dreamer reads the store and writes back to it; the store ends above it, so the
    # arrows turn up into the store's bottom edge
    arrow(c, [(dreamer.right, dreamer.y + 34), (sx + 40, dreamer.y + 34), (sx + 40, store.bottom)],
          t.ink, label="new levels", at=0, offset=(4, 0))
    arrow(c, [(sx + 90, store.bottom), (sx + 90, dreamer.y + 80), (dreamer.right, dreamer.y + 80)],
          t.muted, dashed=True, label="what is stored", at=1, offset=(10, 0))
    # one arrow into the group: whichever path is used reads the same conclusions
    y_read = min(group.y + 60, store.bottom - 30)
    arrow(c, [(store.right, y_read), (group.x, y_read)], t.muted, dashed=True, label="conclusions")

    band = max(dreamer.bottom, group.bottom, store.bottom) + 30
    heading(c, wx, band, W - 2 * wx, "USE", "what the answering model is given, and what it replies")
    px = sx
    prompt = prompt_card(
        c, px, band + 22, W - wx - px,
        "Act on EXPLICIT and DEDUCTIVE. Treat INDUCTIVE as a soft preference. Never assert "
        "an ABDUCTIVE claim.",
        [segment("every live conclusion, tagged with its level", PACKET, columns=2,
                 note=("6 of the 23 lines. The two retired conclusions are not among them.", None))],
        QUESTION)
    arrow(c, [(group.cx, group.bottom), (group.cx, prompt.y)], t.muted, dashed=True)
    answer = answer_card(c, wx, band + 22, ww, ANSWER, NEEDS)
    arrow(c, [(prompt.x, band + 22 + 13), (answer.right + 4, band + 22 + 13)], t["prompt"].accent)

    footer(c, max(prompt.bottom, answer.bottom) + 24,
           "Example from notebooks/05-honcho.ipynb, a re-implementation, shortened")
    return c


def _ladder(c: Canvas, x: float, y: float, w: float) -> Box:
    """The four levels as bands, the least certain on top; retired conclusions struck through;
    the links from one deduction down to the explicit conclusions it cites."""
    t = c.theme
    s, stale = t["store"], t["stale"]
    text_w = w - 12 - 30 - 16
    # measure the bands
    layout, h = [], 48
    for name, meaning, count, items in LEVELS:
        band_h = 28
        rows = []
        for oid, text, retired in items:
            lines = wrap(text, TINY, text_w)
            rows.append((oid, lines, retired, band_h))
            band_h += len(lines) * 15 + 6
        if not items:
            band_h += 18
        layout.append((name, meaning, count, rows, h, band_h + 4))
        h += band_h + 4 + 8
    box = panel(c, x, y, w, h + 22, "layers", "Conclusions", "24 live, 2 retired")
    c.text(x + 12, box.bottom - 10, "struck through: retired in July", TINY, ITALIC, stale.accent)
    rows_at = {}
    for name, meaning, count, rows, by, band_h in layout:
        band = Box(x + 6, y + by, w - 12, band_h)
        if not rows:
            c.rect(band, fill=t.paper, stroke=s.accent, r=8, dash="4 3")
        else:
            c.rect(band, fill=t.card, r=8)
        c.text(band.x + 10, band.y + 18, name, TINY - 1, MONO, s.accent)
        c.text(band.x + 10 + measure(name, TINY - 1, MONO) + 8, band.y + 18, meaning, TINY, ITALIC, t.muted)
        if count:
            c.text(band.right - 10, band.y + 18, count, TINY, BOLD, s.ink, anchor="end")
        if not rows:
            c.text(band.x + 10, band.y + 38, "Announced, not in Honcho's code yet", TINY, SANS, t.muted)
        for oid, lines, retired, ry in rows:
            ty = band.y + ry
            colour = stale.accent if retired else t.ink
            for i, line in enumerate(lines):
                c.text(band.x + 10, ty + 12 + i * 15, line, TINY, SANS, colour)
                if retired:
                    c.line(band.x + 10, ty + 7.5 + i * 15, band.x + 10 + measure(line, TINY), ty + 7.5 + i * 15,
                           stale.accent, 1.1)
            rows_at[oid] = (ty + 8, ty + len(lines) * 15)
    # the premise links, on the right edge: from the deduction down to what it cites
    start, ends = CITES
    sx = x + w - 14
    top_y = rows_at[start][0]
    for oid in ends:
        end_y = rows_at[oid][0]
        c.path(f"M{sx - 8} {top_y} H{sx} V{end_y} H{sx - 8}", stroke=s.accent, width=1.2)
        c.circle(sx - 9, end_y, 2.2, fill=s.accent)
    c.circle(sx - 9, top_y, 2.2, fill=s.accent)
    c.text(sx - 4, (top_y + rows_at[ends[0]][0]) / 2 + 4, "cites", TINY - 1, BOLD, s.accent, anchor="end")
    return box
