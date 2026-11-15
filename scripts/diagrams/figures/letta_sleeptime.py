"""Letta: the sleep-time set-up, two agents sharing the same blocks.

Letta 0.16.8: with `enable_sleeptime`, the primary agent keeps its search tools and loses the
tools that edit blocks (BASE_SLEEPTIME_CHAT_TOOLS); the sleep-time agent has memory_insert,
memory_replace, memory_rethink and memory_finish_edits (BASE_SLEEPTIME_TOOLS) and runs in the
background after every fifth turn of the primary (`sleeptime_agent_frequency=5`, server.py), on the
messages since its last run. The timeline is a schematic of that default.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, MONO, SANS, Box, Canvas, W, M, arrow, heading, kind_badge
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "letta-sleeptime"
TITLE = "Two agents, one set of blocks"
ALT = ("The sleep-time set-up of Letta, as a timeline of ten turns. Top lane: the primary agent "
       "answers each user message; it reads the memory blocks, can search past messages, and "
       "has no tool to edit the blocks. Bottom lane: the sleep-time agent runs in the "
       "background after turns 5 and 10, by default, reads the messages since its last run, "
       "and edits the shared blocks with memory_insert, memory_replace or memory_rethink, then "
       "memory_finish_edits. A fact the user states in turn 2 reaches the blocks only when the "
       "sleep-time agent runs after turn 5; until then it is only in the conversation.")

TURNS = 10
PAD = 12


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "With a sleep-time agent, the agent that answers cannot write, and "
                       "a second agent edits the shared blocks in the background, every few "
                       "turns. The user never waits for it.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30
    label_w = 150
    x0 = M + label_w
    span = W - M - x0
    col = span / TURNS

    heading(c, M, y, W - 2 * M, "A TIMELINE OF TEN TURNS", "Letta's default: the sleep-time agent runs every fifth turn")
    y += 30
    # lane 1: the primary agent
    c.text(M, y + 18, "Primary agent", SMALL, BOLD)
    c.text(M, y + 34, "answers; can search", TINY, SANS, t.muted)
    for i in range(TURNS):
        b = Box(x0 + i * col + 3, y, col - 6, 40)
        c.rect(b, fill=t["llm"].wash, stroke=t["llm"].accent, r=6, width=0.9)
        c.text(b.cx, b.y + 25, f"turn {i + 1}", TINY, MEDIUM, t["llm"].ink, anchor="middle")
    lane1 = y
    # the fact stated in turn 2
    fx = x0 + 1 * col + col / 2
    c.text(fx, y - 8, "a new fact", TINY, BOLD, t["person"].accent, anchor="middle")
    y += 70

    # lane 2: the blocks
    c.text(M, y + 18, "Memory blocks", SMALL, BOLD, t["store"].ink)
    c.text(M, y + 34, "in both prompts", TINY, SANS, t.muted)
    blocks = Box(x0, y, span, 40)
    c.rect(blocks, fill=t["store"].wash, stroke=t["store"].accent, r=6)
    # lag: from turn 2 to the first run
    run1 = x0 + 5 * col
    c.rect(Box(fx, y + 6, run1 - fx, 28), fill=t["stale"].wash, r=4)
    c.text((fx + run1) / 2, y + 25, "not in the blocks yet", TINY, MEDIUM, t["stale"].ink, anchor="middle")
    c.text(run1 + 10, y + 25, "now in the blocks", TINY, MEDIUM, t["store"].ink)
    arrow(c, [(fx, lane1 + 42), (fx, y + 6)], t["person"].accent, dashed=True)
    # reads: blocks are in every primary call
    lane2 = y
    y += 80

    # lane 3: the sleep-time agent
    c.text(M, y + 18, "Sleep-time agent", SMALL, BOLD)
    c.text(M, y + 34, "background; edits", TINY, SANS, t.muted)
    for k in (5, 10):
        rx = min(x0 + k * col, W - M - col * 0.75)
        b = Box(rx - col * 0.75, y, col * 1.5, 40)
        c.rect(b, fill=t.card, stroke=t["llm"].accent, r=6, dash="5 4")
        c.text(b.cx, b.y + 18, "reads turns", TINY, MEDIUM, t["llm"].ink, anchor="middle")
        c.text(b.cx, b.y + 33, f"{k - 4}–{k}, edits", TINY, MEDIUM, t["llm"].ink, anchor="middle")
        arrow(c, [(rx, y - 2), (rx, lane2 + 42)], t["llm"].accent)
    y += 76

    # the two tool sets
    half = (W - 2 * M - 20) / 2
    for i, (title, tools) in enumerate((
            ("The primary agent's tools", "send_message · conversation_search · archival_memory_search"),
            ("The sleep-time agent's tools", "memory_insert · memory_replace · memory_rethink · memory_finish_edits"))):
        x = M + i * (half + 20)
        c.rect(Box(x, y, half, 62), fill=t.card, stroke=t.line, r=8)
        c.text(x + PAD, y + 22, title, TINY, BOLD)
        c.paragraph(x + PAD, y + 28, tools, half - 2 * PAD, TINY - 0.5, MONO, t.muted)
    y += 80
    used = c.paragraph(M, y, "The sleep-time agent has its own prompt, which asks for specific "
                       "dates in place of “today” or “recently”. The notebook runs it once after "
                       "each session, the simplest set-up that shows the same mechanism.",
                       W - 2 * M, TINY, SANS, t.muted)
    source_line(c, y + used + 16, "Letta 0.16.8: constants.py, server.py, groups/sleeptime_multi_agent_v4.py")
    return c
