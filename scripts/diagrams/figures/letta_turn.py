"""Letta: one turn of the agent, with a memory edit inside it.

The loop is LettaAgentV3 in Letta 0.16.8 (a reply without a tool call ends the turn). The token
counts are the turn with the changed fact (session 2, first message) in the committed run of
notebooks/04-letta.ipynb: 2,348 tokens in for the call that edits, 2,574 for the call that replies.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, MONO, SANS, Box, Canvas, W, M, arrow, heading, kind_badge, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "letta-turn"
TITLE = "One turn, with a memory edit"
ALT = ("The steps of one turn of a Letta agent. The user's message arrives. Model call 1 reads the "
       "whole prompt (in the notebook, 2,348 tokens) and returns a tool call, memory_replace, not a "
       "reply. Code runs the tool: it replaces the text in the block and returns the whole new "
       "block, which goes into the conversation; the system prompt is rebuilt with the new block. "
       "Model call 2 reads everything again plus the tool call and its result (2,574 tokens) and "
       "returns text with no tool call, which ends the turn and goes to the user. The user waits "
       "for both calls. A turn with no edit is one call; each search adds one more.")

STEPS = [  # (role, title, text, code line)
    ("person", "The user's message arrives", "It is appended to this conversation.", None),
    ("llm", "Model call 1 · reads 2,348 tokens",
     "Base instructions, blocks, metadata, three tool descriptions, the conversation. "
     "It returns a tool call, not a reply:",
     'memory_replace(label="human", old_string=…, new_string=…)'),
    ("code", "The tool runs",
     "The old text must appear exactly once. It is replaced, and the whole new block is returned "
     "as the tool's result. The system prompt is rebuilt with the new block.", None),
    ("llm", "Model call 2 · reads 2,574 tokens",
     "The same prompt, now with the new block, plus the tool call and its result. It returns "
     "text with no tool call, so the turn ends.", None),
    ("person", "The reply goes to the user",
     "In the notebook: “I've updated my notes […]”, a claim that, this time, was true.", None),
]
PAD = 14
GAP = 18


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The agent decides inside its turn whether to write. Each tool call "
                       "is one more model call before the reply, and each call reads the whole "
                       "prompt again.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30
    x = M + 120
    w = W - M - x
    heading(c, M, y, W - 2 * M, "THE TURN WITH THE CHANGED FACT", "session 2, first message, in the notebook")
    y += 24
    boxes = []
    for i, (role, title, text, code) in enumerate(STEPS):
        r = t[role]
        lines = wrap(text, TINY, w - 2 * PAD - 70)
        h = 34 + len(lines) * TINY * 1.38 + (24 if code else 6)
        b = Box(x, y, w, h)
        c.rect(b, fill=r.wash if role == "person" else t.card, stroke=r.accent, r=8,
               width=1.3 if role == "llm" else 1.0)
        c.text(x + PAD, y + 22, title, SMALL, BOLD, r.ink if role == "person" else t.ink)
        if role in ("llm", "code"):
            kind_badge(c, x + w - 10, y + 8, role)
        for k, line in enumerate(lines):
            c.text(x + PAD, y + 40 + k * TINY * 1.38, line, TINY, SANS, t.muted)
        if code:
            c.text(x + PAD, y + 40 + len(lines) * TINY * 1.38 + 6, code, TINY, MONO, t["llm"].accent)
        boxes.append(b)
        if i < len(STEPS) - 1:
            arrow(c, [(x + 40, y + h + 2), (x + 40, y + h + GAP - 2)], t.faint, width=1.3)
        y += h + GAP

    # the user waits from the message to the reply
    top, bottom = boxes[1].y, boxes[3].bottom
    bx = M + 70
    c.line(bx, top, bx, bottom, t["person"].accent, 1.6)
    c.line(bx, top, bx + 10, top, t["person"].accent, 1.6)
    c.line(bx, bottom, bx + 10, bottom, t["person"].accent, 1.6)
    c.text(bx - 10, (top + bottom) / 2 - 8, "the user", TINY, BOLD, t["person"].ink, anchor="end")
    c.text(bx - 10, (top + bottom) / 2 + 8, "waits", TINY, BOLD, t["person"].ink, anchor="end")

    y += 4
    used = c.paragraph(M, y, "A turn without an edit is one call. A search is one more call, and "
                       "its result is read by the next one: in the notebook, the question took "
                       "five searches and six calls.", W - 2 * M, TINY, SANS, t.muted)
    source_line(c, y + used + 16, "Loop: Letta 0.16.8 (LettaAgentV3). Tokens: notebooks/04-letta.ipynb")
    return c
