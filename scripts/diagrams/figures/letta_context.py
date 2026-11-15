"""Letta: what the agent sees on every call, and what stays outside.

The parts of the prompt and their order are Letta 0.16.8's (`letta_v1` agent; the request logged
in the experiment, .cache/calls/). The token counts are the first call of session 1 in the
committed run of notebooks/04-letta.ipynb (2,294 tokens in), split by counting each part of the
system prompt with the model's token counter; the tool descriptions are the remainder, the same
1,594 tokens on every call.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, MONO, SANS, Box, Canvas, W, M, arrow, heading, measure, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "letta-context"
TITLE = "What a Letta agent sees"
ALT = ("Left, the prompt that the agent reads on every model call, in order: Letta's base "
       "instructions, the memory blocks (persona and human), the memory metadata, and the "
       "messages of the current conversation with any tool calls and results; the descriptions "
       "of the three tools are sent with it. The agent edits the blocks with memory_insert and "
       "memory_replace. Right, outside the prompt: recall, every message of every conversation, "
       "reached only by calling conversation_search, whose results come back into the "
       "conversation. Below, the first call of a session in the notebook, to scale: 2,294 tokens, "
       "of which the tool descriptions are 1,594, the base instructions 336, the blocks 225, the "
       "metadata 91 and the user's message 48.")

PARTS = [  # (role, title, note)
    ("code", "Base instructions", "the same for every agent of this type"),
    ("store", "Memory blocks", "persona and human: the agent's own memory, edited with tools"),
    ("code", "Memory metadata", "ids, a timestamp, how many messages are in recall"),
    ("person", "This conversation", "its messages, and the tool calls and results of this turn"),
]
TOKENS = [("tool descriptions", 1594, "code"), ("base instructions", 336, "code"),
          ("blocks", 225, "store"), ("metadata", 91, "code"), ("message", 48, "person")]
PAD = 12


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The prompt is the agent's main memory: the only thing the model "
                       "sees. Everything else is outside it, like a disk, and comes in only "
                       "through a tool call.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30
    rw = 230
    gutter = 160
    lw = W - 2 * M - gutter - rw
    rx = M + lw + gutter
    heading(c, M, y, lw, "IN THE PROMPT", "rebuilt and sent on every model call")
    heading(c, rx, y, rw, "OUTSIDE THE PROMPT")
    top = y + 22
    yy = top
    boxes = []
    for role, title, note in PARTS:
        r = t[role]
        lines = wrap(note, TINY, lw - 2 * PAD)
        h = 32 + len(lines) * TINY * 1.35
        b = Box(M, yy, lw, h)
        c.rect(b, fill=r.wash, stroke=r.accent if role == "store" else None, r=8,
               width=1.3 if role == "store" else 1.0)
        c.text(M + PAD, yy + 21, title, SMALL, BOLD, r.ink)
        for k, line in enumerate(lines):
            c.text(M + PAD, yy + 39 + k * TINY * 1.35, line, TINY, SANS, r.ink)
        boxes.append(b)
        yy += h + 6
    tools = Box(M, yy + 6, lw, 52)
    c.rect(tools, fill=t.card, stroke=t.line, r=8, dash="4 3")
    c.text(M + PAD, yy + 26, "Sent with it: the descriptions of three tools", TINY, BOLD, t.muted)
    c.text(M + PAD, yy + 44, "memory_insert · memory_replace · conversation_search", TINY, MONO, t.muted)

    blocks, conv = boxes[1], boxes[3]
    # outside: recall, level with the conversation
    rh = 96
    recall = Box(rx, conv.bottom - 40, rw, rh)
    c.rect(recall, fill=t.card, stroke=t["store"].accent, r=8, dash="5 4")
    c.text(rx + PAD, recall.y + 22, "Recall", SMALL, BOLD, t["store"].ink)
    c.paragraph(rx + PAD, recall.y + 28, "Every message of every conversation with this agent, "
                "tool calls and results included.", rw - 2 * PAD, TINY, SANS, t.muted)
    sy = conv.bottom - 18
    arrow(c, [(recall.x - 2, sy), (conv.right + 4, sy)], t["llm"].accent, dashed=True)
    c.text((conv.right + recall.x) / 2, sy - 8, "conversation_search", TINY, MONO, t["llm"].accent, anchor="middle")
    c.text((conv.right + recall.x) / 2, sy + 18, "results come back", TINY, SANS, t.muted, anchor="middle")
    c.text((conv.right + recall.x) / 2, sy + 32, "as a tool result", TINY, SANS, t.muted, anchor="middle")
    # the edit tools: from the conversation (the model's tool call) up into the blocks
    ex = conv.right + 26
    arrow(c, [(conv.right + 2, conv.y + 14), (ex, conv.y + 14), (ex, blocks.cy), (blocks.right + 4, blocks.cy)],
          t["llm"].accent)
    c.text(ex + 10, (blocks.cy + conv.y) / 2 - 2, "memory_insert,", TINY, MONO, t["llm"].accent)
    c.text(ex + 10, (blocks.cy + conv.y) / 2 + 13, "memory_replace", TINY, MONO, t["llm"].accent)
    bottom = max(tools.bottom, recall.bottom)

    # to scale: the first call of a session
    y = bottom + 44
    total = sum(v for _, v, _ in TOKENS)
    heading(c, M, y, W - 2 * M, "ONE CALL, TO SCALE", f"the first call of a session in the notebook: {total:,} tokens")
    y += 24
    x = M
    full = W - 2 * M
    for label, v, role in TOKENS:
        w = full * v / total
        c.rect(Box(x, y, w - 1.5, 30), fill=t[role].wash, stroke=t[role].accent, r=3, width=0.8)
        x += w
    y += 52
    x = M
    for label, v, role in TOKENS:
        c.rect(Box(x, y - 11, 14, 14), fill=t[role].wash, stroke=t[role].accent, r=3, width=0.8)
        text = f"{label} {v:,}"
        c.text(x + 20, y, text, TINY, MEDIUM, t[role].ink)
        x += 20 + measure(text, TINY, MEDIUM) + 22
    y += 14
    used = c.paragraph(M, y, "The tool descriptions are the largest part: the server copies each "
                       "tool's examples into its description. Everything but the message is sent "
                       "again on every call, including every call inside one turn.",
                       W - 2 * M, TINY, SANS, t.muted)
    source_line(c, y + used + 16, "Layout: Letta 0.16.8. Tokens: notebooks/04-letta.ipynb, session 1, first call")
    return c
