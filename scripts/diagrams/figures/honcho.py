"""Honcho: conclusions at levels, extracted on arrival and reasoned over later, in the background;
read through Honcho's own agent (dialectic) or as the conclusions themselves (representation).

Every example below is from the first run of a Honcho 3.3.0 server on the series' example
(scripts/replays/honcho_server_runs/run1.json), shortened to fit: what the deriver stored, what the
two dreams added and deleted, the dialectic's prefetch and its reply. Counts are that run's.
"""

from __future__ import annotations

from ..kit import (BOLD, ITALIC, MEDIUM, MONO, SANS, Box, Canvas, W, answer_card, arrow, bubble, column,
                   footer, frame, heading, measure, node, panel, prompt_card, segment, wrap)
from ..theme import TINY, Theme

NAME = "honcho"
TITLE = "Honcho"
ALT = ("Honcho's architecture, with the running example. Writing: when messages arrive, a deriver "
       "makes one LLM call per batch that extracts what was said as explicit conclusions; later, "
       "a dream runs two agents with tools that add deductive and inductive conclusions, delete "
       "outdated ones and keep a peer card. Memory: conclusions at levels, each derived one citing "
       "the conclusions it was drawn from; the contradiction level has no writer in this release. "
       "In the run shown, the vegetarian fact was deleted, but a deduction and a pattern that rest "
       "on it stayed live. Reading: either Honcho's dialectic agent writes an answer from the "
       "conclusions (an LLM call), or the representation returns the conclusions themselves, with "
       "their times (no LLM call). The dialectic's prefetch held both the update and the stale "
       "conclusions; its answer said pescatarian and kept all four constraints.")

SESSION_1 = ("“I've been strictly vegetarian for eight years, and I have a severe peanut "
             "allergy … Indian, usually.”")
SESSION_2 = ("“So I'm pescatarian now, not vegetarian … I moved to Kreuzberg in May … Lena "
             "can't eat shellfish, and Jonas is coeliac.”")
QUESTION = ("“My sister and her partner are in town tonight. Book the three of us somewhere for "
            "dinner — you know what we can and can't eat.”")

# The levels, top to bottom: name, what it means, live count, and example conclusions as
# (id, text, state); state is live, deleted, or stale (live, but resting on a deleted row).
LEVELS = [
    ("contradiction", "two that cannot both hold", None, []),
    ("inductive", "a pattern", "2", [
        ("i", "Attentive to dietary restrictions, his own and others'", "live"),
        ("i", "Consistent preference for vegetarian cuisine", "stale")]),
    ("deductive", "what follows", "4", [
        ("d20", "Transitioned from vegetarian to pescatarian, June 2026", "live"),
        ("d", "Likely to order vegetarian Indian food", "stale")]),
    ("explicit", "what was said", "15", [
        ("e17", "Started eating fish in June 2026", "live"),
        ("e", "Sister's partner Jonas is coeliac", "live"),
        ("e2", "Strict vegetarian diet for eight years", "deleted")]),
]
CITES = ("d20", ["e17", "e2"])   # the update's premises, drawn as links

# The dialectic's prefetch (the 25 + 25 conclusions closest to the question), a few of 21.
PACKET = [
    ("explicit ", "Anton is pescatarian", None), ("explicit ", "Jonas is coeliac", None),
    ("explicit ", "Lena: no shellfish", None), ("deductive", "Transitioned to pescatarian", None),
    ("deductive", "Likely orders vegetarian", "stale"), ("inductive", "Prefers vegetarian cuisine", "stale"),
]

ANSWER = ("Pescatarian, severe peanut allergy; Lena, no shellfish; Jonas, coeliac. An Indian "
          "restaurant in Kreuzberg with gluten-free options.")
NEEDS = [("diet", "both"), ("peanuts", "yes"), ("shellfish", "yes"), ("gluten", "yes"),
         ("cuisine", "yes"), ("area", "yes")]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, "Honcho: a reasoner that works in the background", ALT)
    t = theme
    top = frame(
        c, "Honcho",
        "Memory as reasoning about a person: conclusions at levels, each derived one citing the "
        "conclusions it was drawn from. Extracted on arrival; reasoned over later, in a dream.",
        captions={"write": "Turns a conversation into memory. What was said, on arrival; the "
                           "reasoning, later, in a background dream."})

    wx, ww = column("write")
    b1 = bubble(c, wx, top, ww, "March · session 1", SESSION_1)
    b2 = bubble(c, wx, b1.bottom + 14, ww, "July · session 2", SESSION_2)
    rx, rw = column("read")
    q = bubble(c, rx, top, rw, "September · session 3", QUESTION, target=True)

    row = max(b2.bottom, q.bottom) + 34
    deriver = node(
        c, wx, row, ww, "llm", "sparkles", "Deriver",
        body="As messages arrive: extracts what was said, as explicit conclusions only.",
        tags=[{"text": "1 LLM call per batch", "role": "llm", "icon": "sparkles"}])
    dreamer = node(
        c, wx, deriver.bottom + 16, ww, "llm", "moon", "Dream",
        body="Later, in the background: two agents with tools add deductions and patterns, "
             "delete outdated rows, keep a peer card.",
        tags=[{"text": "16 LLM calls in two dreams", "role": "llm", "icon": "sparkles"}])
    arrow(c, [(wx + 30, b2.bottom + 4), (wx + 30, deriver.y)], t["person"].accent)

    # read: one of two paths, in a group
    group_top = row
    c.text(rx + 42, group_top + 19, "one of two read paths", TINY, BOLD, t.muted)
    chat = node(
        c, rx + 8, group_top + 40, rw - 16, "llm", "bot", "Dialectic", api="peer.chat(question)",
        body="Honcho's agent searches the conclusions and writes a short answer.",
        tags=[{"text": "the path shown below", "role": "llm"}], pad=12)
    c.text(rx + rw / 2, chat.bottom + 22, "or", TINY, ITALIC, t.muted, anchor="middle")
    rep = node(
        c, rx + 8, chat.bottom + 40, rw - 16, "code", "list", "Representation",
        api="peer.representation()",
        body="Returns the conclusions themselves, with their times; no LLM call.", pad=12)
    group = Box(rx, group_top, rw, rep.bottom + 10 - group_top)
    c.rect(group, stroke=t.line, r=14, dash="4 3")
    arrow(c, [(rx + 30, q.bottom + 4), (rx + 30, group.y)], t["person"].accent)

    sx, sw = column("store")
    store = _ladder(c, sx, top, sw)

    arrow(c, [(deriver.right, deriver.y + 34), (sx, deriver.y + 34)], t.ink, label="explicit")
    # the dreamer reads the store and writes back to it; the store ends above it, so the
    # arrows turn up into the store's bottom edge
    arrow(c, [(dreamer.right, dreamer.y + 34), (sx + 40, dreamer.y + 34), (sx + 40, store.bottom)],
          t.ink, label="add, delete", at=0, offset=(4, 0))
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
        "You are Honcho's dialectic … The MORE RECENT statement supersedes the older one … "
        "Ask the user which statement is correct …",
        [segment("prefetched: the conclusions closest to the question", PACKET, columns=2,
                 note=("6 of 21. Red: rests on the deleted fact.", "stale"))],
        QUESTION)
    arrow(c, [(group.cx, group.bottom), (group.cx, prompt.y)], t.muted, dashed=True)
    answer = answer_card(c, wx, band + 22, ww, ANSWER, NEEDS)
    arrow(c, [(prompt.x, band + 22 + 13), (answer.right + 4, band + 22 + 13)], t["prompt"].accent)

    footer(c, max(prompt.bottom, answer.bottom) + 24,
           "Example from the first run of a Honcho 3.3.0 server, shortened")
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
    box = panel(c, x, y, w, h + 22, "layers", "Conclusions", "21 live, 2 deleted")
    c.text(x + 12, box.bottom - 10, "struck: deleted · red: rests on it", TINY, ITALIC, stale.accent)
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
            c.text(band.x + 10, band.y + 38, "No writer in this release", TINY, SANS, t.muted)
        for oid, lines, state, ry in rows:
            ty = band.y + ry
            colour = stale.accent if state != "live" else t.ink
            for i, line in enumerate(lines):
                c.text(band.x + 10, ty + 12 + i * 15, line, TINY, SANS, colour)
                if state == "deleted":
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
