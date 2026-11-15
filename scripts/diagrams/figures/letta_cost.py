"""Letta: what each model call of the in-line agent read, split into its parts.

From the committed run of notebooks/04-letta.ipynb (section 4): the input tokens of each of the 17
calls. The base instructions, the blocks and the metadata of each call were counted with the
model's token counter; the tool descriptions are 1,594 tokens on every call (the remainder of the
first call, the same on all of them); the conversation (messages, tool calls and results) is the
rest.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, SANS, Box, Canvas, W, M, heading, measure
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "letta-cost"
TITLE = "What each call read"
ALT = ("Seventeen bars, one per model call of the in-line agent, grouped by user turn, each split "
       "into tool descriptions (1,594 tokens on every call), base instructions and metadata (about "
       "430), memory blocks (225 to 337) and the conversation with tool calls and results (31 to "
       "1,369). Session 1: one call for the first message, two for the second. Session 2: two "
       "calls for each of four messages, each pair an edit and a reply, growing from 2,348 to "
       "3,727 tokens. Session 3: six calls for the question, five searches and the answer, from "
       "2,390 to 3,526 tokens. In all, 47,677 tokens.")

# (turn, step, tool, base+meta, blocks, conversation); tool descriptions 1,594 on every call
CALLS = [
    ("s1.1", 1, None, 427, 225, 48), ("s1.2", 1, "insert", 427, 225, 363), ("s1.2", 2, None, 427, 284, 517),
    ("s2.1", 1, "replace", 427, 284, 43), ("s2.1", 2, None, 427, 287, 266),
    ("s2.2", 1, "insert", 427, 287, 411), ("s2.2", 2, None, 427, 305, 547),
    ("s2.3", 1, "insert", 427, 305, 646), ("s2.3", 2, None, 427, 325, 804),
    ("s2.4", 1, "replace", 427, 325, 1005), ("s2.4", 2, None, 427, 337, 1369),
    ("s3.1", 1, "search", 428, 337, 31), ("s3.1", 2, "search", 428, 337, 82),
    ("s3.1", 3, "search", 428, 337, 124), ("s3.1", 4, "search", 428, 337, 166),
    ("s3.1", 5, "search", 428, 337, 514), ("s3.1", 6, None, 428, 337, 1167),
]
TOOLS = 1594
PARTS = [("tool descriptions", "code"), ("instructions and metadata", "prompt"),
         ("memory blocks", "store"), ("conversation, tool calls and results", "person")]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The in-line agent's 17 model calls for seven user turns. Every call "
                       "reads the fixed prompt again; a turn with an edit or a search adds calls.",
                       W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30
    x = M
    for label, role in PARTS:
        c.rect(Box(x, y - 11, 14, 14), fill=t[role].wash, stroke=t[role].accent, r=3, width=0.8)
        x += 20 + c.text(x + 20, y, label, TINY, SANS, t.muted) + 20
    y += 24
    chart_h = 300
    base = y + chart_h
    top = 4000
    axis_x = M + 44
    span = W - M - axis_x
    # gaps between turns
    turns = []
    for call in CALLS:
        if not turns or turns[-1][0] != call[0]:
            turns.append([call[0], []])
        turns[-1][1].append(call)
    gap = 14
    bar = (span - gap * (len(turns) - 1)) / len(CALLS)
    for v in (0, 1000, 2000, 3000, 4000):
        yy = base - chart_h * v / top
        c.line(axis_x, yy, W - M, yy, t.line, 0.8)
        c.text(axis_x - 6, yy + 4, f"{v:,}", TINY - 1, SANS, t.faint, anchor="end")
    x = axis_x
    for name, calls in turns:
        start = x
        for turn, step, tool, instr, blocks, conv in calls:
            yy = base
            for v, role in ((TOOLS, "code"), (instr, "prompt"), (blocks, "store"), (conv, "person")):
                h = chart_h * v / top
                c.rect(Box(x + 2, yy - h, bar - 4, h), fill=t[role].wash, stroke=t[role].accent, r=1.5, width=0.6)
                yy -= h
            total = TOOLS + instr + blocks + conv
            c.text(x + bar / 2, yy - 6, f"{total / 1000:.1f}k", TINY - 2, MEDIUM, t.muted, anchor="middle")
            if tool:
                c.text(x + bar / 2, base + 14, tool[:3], TINY - 2, SANS, t["llm"].accent, anchor="middle")
            x += bar
        mid = (start + x) / 2
        c.text(mid, base + 32, _turn_label(name), TINY - 1, BOLD, t.ink, anchor="middle")
        x += gap
    y = base + 52
    used = c.paragraph(M, y, "Small labels under a bar: the tool that call made (ins = memory_insert, "
                       "rep = memory_replace, sea = conversation_search). In all, 47,677 tokens; "
                       "the tool descriptions alone are 27,098 of them.", W - 2 * M, TINY, SANS, t.muted)
    source_line(c, y + used + 16, "From notebooks/04-letta.ipynb, section 4; parts counted with the model's token counter")
    return c


def _turn_label(name):
    session, message = name[1], name[3]
    return f"S{session}·{message}"
