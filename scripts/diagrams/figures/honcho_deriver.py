"""Honcho: the deriver's one call for a batch of messages, and the rules for saving what it returns.

The message tags and the rules are Honcho 3.3.0's (src/deriver/prompts.py, create_documents in
src/crud/document.py). The batch and the six rows are session 1 of the first real-server run of the
series' example (scripts/replays/honcho_server_runs/run1.json).
"""

from __future__ import annotations

from ..kit import BOLD, ITALIC, MEDIUM, MONO, SANS, Box, Canvas, W, M, arrow, heading, node, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line
from .honcho_parts import conclusion

NAME = "honcho-deriver"
TITLE = "The deriver: one call per batch"
ALT = ("Top: session 1 as the deriver sees it, three messages, each in a tag with its index, its "
       "peer, whether that peer is the one being modelled, and its time. One model call, 923 tokens "
       "in, returns six explicit conclusions, each with Anton as the subject and the time of the "
       "batch's last message: planning a dinner in Berlin for the week of March 21, 2026; a strict "
       "vegetarian diet for eight years; a severe, anaphylactic peanut allergy; Indian cuisine; "
       "paneer dishes; a budget of about 40 euros per person. Bottom: the three rules for saving. An "
       "exact duplicate (same text, level and, for explicit rows, session) is dropped and the existing "
       "row counted again. A near duplicate (cosine distance 0.05 or less, same level and, for "
       "explicit rows, same session) is merged, and the richer text wins. Otherwise the row is stored. "
       "So the peanut allergy said in March and again in July is stored twice.")

MESSAGES = [
    ('<message idx="0" peer="Anton" target="true" time="2026-03-14 12:00:00">', "I'm planning a dinner for my "
     "sister's visit to Berlin next week. Worth saying up front: I've been strictly vegetarian for eight "
     "years, and I have a severe peanut allergy — anaphylactic, not a preference."),
    ('<message idx="1" peer="assistant" target="false" time="2026-03-14 12:01:00">', "Understood — no meat, "
     "and peanuts are a hard exclusion. Any cuisine you lean towards?"),
    ('<message idx="2" peer="Anton" target="true" time="2026-03-14 12:02:00">', "Indian, usually. Paneer "
     "dishes especially. And I'd rather not spend more than about 40 euros a head."),
]
ROWS = ["Anton is planning a dinner in Berlin for the week of March 21, 2026.",
        "Anton has followed a strict vegetarian diet for eight years.",
        "Anton has a severe, anaphylactic peanut allergy.", "Anton prefers Indian cuisine.",
        "Anton prefers dishes containing paneer.",
        "Anton has a budget of approximately 40 euros per person for the dinner."]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The deriver sees the new messages and nothing else: no stored conclusions, "
                       "no earlier session. Saving then drops or merges near-identical rows.",
                       W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30
    heading(c, M, y, W - 2 * M, "THE BATCH", "session 1, as it appears in the prompt")
    y += 18
    for tag, text in MESSAGES:
        target = 'target="true"' in tag
        colour = t["person"].accent if target else t.muted
        c.text(M, y + 14, tag, TINY - 1.5, MONO, colour)
        lines = wrap(text, TINY, W - 2 * M - 20, SANS)
        for i, line in enumerate(lines):
            c.text(M + 16, y + 30 + i * TINY * 1.35, line, TINY, SANS, t["person"].ink if target else t.muted)
        y += 30 + len(lines) * TINY * 1.35 + 4
    y += 8
    call = node(c, M + 220, y + 16, W - 2 * M - 440, "llm", "sparkles", "Deriver", api="1 call · 923 tokens in",
                body="Explicit facts about the target peer, one each, with absolute dates.")
    arrow(c, [(W / 2, y - 2), (W / 2, call.y)], t["person"].accent)
    y = call.bottom + 26
    arrow(c, [(W / 2, call.bottom), (W / 2, y - 2)], t.ink)
    heading(c, M, y + 10, W - 2 * M, "WHAT IT RETURNED", "six explicit rows, each stamped 2026-03-14 12:02, "
            "the time of the batch's last message")
    y += 26
    cols, gap = 3, 8
    cw = (W - 2 * M - gap * (cols - 1)) / cols
    notes = {0: "“next week”, said on Saturday 14 March", 1: "“eight years”: still relative"}
    for start in range(0, len(ROWS), cols):
        bottom = y
        for col, text in enumerate(ROWS[start:start + cols]):
            box = conclusion(c, M + col * (cw + gap), y, cw, "explicit", text, "live",
                             note=notes.get(start + col))
            bottom = max(bottom, box.bottom)
        y = bottom + gap
    y += 18
    heading(c, M, y, W - 2 * M, "SAVING", "create_documents, for each new row")
    y += 18
    rules = node(c, M, y, W - 2 * M, "code", "database", "Three rules, in order",
                 steps=[("an exact duplicate (same text, level, and for explicit rows session) is dropped; "
                         "the stored row is counted again", "drop"),
                        ("a near duplicate (cosine distance ≤ 0.05, same level, and for explicit rows same "
                         "session) is merged: the richer text wins", "merge"),
                        ("otherwise the row is stored", "store")],
                 tags=[{"text": "March: “a severe, anaphylactic peanut allergy” · July: “a peanut allergy” · "
                                "different sessions, so both stored", "role": "both"}])
    source_line(c, rules.bottom + 24, "From the first run of a Honcho 3.3.0 server on the example")
    return c
