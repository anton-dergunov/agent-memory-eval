"""Letta (MemGPT): the answering agent edits memory blocks that sit in its own prompt.

Every example below is from the committed run of notebooks/04-letta.ipynb: the `human` block after
session 2 (section 2, verbatim), the tool calls and their cost (sections 1, 2 and 4), the
September turn (section 3).
"""

from __future__ import annotations

from ..kit import (BOLD, ITALIC, MONO, SANS, Box, Canvas, W, answer_card, arrow, bubble, chip, column,
                   footer, frame, heading, node, panel, prompt_card, segment, wrap)
from ..theme import SMALL, TINY, Theme

NAME = "letta"
TITLE = "Letta (MemGPT)"
ALT = ("Letta's architecture, with the running example. Writing: the answering agent itself "
       "decides mid-turn what to remember and edits its human memory block with a tool call "
       "(memory_replace); a sleep-time agent can do this in the background instead. Memory: "
       "small text blocks that are in the agent's prompt on every call, plus a history of "
       "every message. In July the vegetarian line was replaced in place, with no history "
       "kept. Reading: no search is needed for the blocks; the agent may search the message "
       "history (recall) with a tool. All six constraints were in the prompt.")

SESSION_1 = ("“I've been strictly vegetarian for eight years, and I have a severe peanut "
             "allergy … Indian, usually.”")
SESSION_2 = ("“So I'm pescatarian now, not vegetarian … I moved to Kreuzberg in May … Lena "
             "can't eat shellfish, and Jonas is coeliac.”")
QUESTION = ("“My sister and her partner are in town tonight. Book the three of us somewhere for "
            "dinner — you know what we can and can't eat.”")

# The `human` block after session 2, verbatim (section 2), and the line its first edit replaced.
REPLACED = "The user is a vegetarian (8 years) and has a severe, anaphylactic peanut allergy."
HUMAN = [
    "The user is a pescatarian (started eating fish one month ago) and has a severe, "
    "anaphylactic peanut allergy.",
    "They enjoy Indian cuisine, specifically paneer dishes.",
    "Budget: ~40 euros per person.",
    "Location: Berlin (Kreuzberg).",
    "Family: Sister (Lena) and her partner (Jonas) are visiting in the autumn. Lena has a "
    "shellfish allergy, and Jonas is coeliac.",
]

ANSWER = ("Suggests Chutnify near Kreuzberg, South Indian and naturally gluten-free, and says to "
          "call ahead about the peanut, coeliac and shellfish needs.")
NEEDS = [("diet", "yes"), ("peanuts", "yes"), ("shellfish", "yes"), ("gluten", "yes"),
         ("cuisine", "yes"), ("area", "yes")]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, "Letta: an agent that edits its own memory", ALT)
    t = theme
    top = frame(
        c, "Letta (MemGPT)",
        "The memory is a few small text blocks inside the agent's own prompt. The answering "
        "agent edits them itself, with tool calls, in the middle of a conversation.",
        captions={
            "write": "Turns a conversation into memory. Here the answering agent does it, "
                     "mid-turn, while the user waits.",
            "read": "Finds what a new question needs. The blocks are already in the prompt; "
                    "the agent may also search."})

    wx, ww = column("write")
    b1 = bubble(c, wx, top, ww, "March · session 1", SESSION_1)
    b2 = bubble(c, wx, b1.bottom + 14, ww, "July · session 2", SESSION_2)
    rx, rw = column("read")
    q = bubble(c, rx, top, rw, "September · session 3", QUESTION, target=True)

    row = max(b2.bottom, q.bottom) + 34
    writer = node(
        c, wx, row, ww, "llm", "bot", "The agent", api="memory_replace()",
        body="While it answers, it decides what is worth keeping and edits the human block "
             "with a tool call.",
        tags=[{"text": "+1 LLM call per edit", "role": "llm", "icon": "sparkles"}])
    sleeper = node(
        c, wx, writer.bottom + 16, ww, "llm", "moon", "Sleep-time agent", dashed=True,
        body="Letta's alternative: a second agent edits the blocks between turns, in the "
             "background, so the user does not wait.")
    reader = node(
        c, rx, row, rw, "llm", "bot", "The same agent", api="conversation_search()",
        body="Its blocks are already in its prompt. It may also search past messages with a tool.",
        tags=[{"text": "+1 LLM call per search", "role": "llm", "icon": "sparkles"}])
    arrow(c, [(wx + 30, b2.bottom + 4), (wx + 30, writer.y)], t["person"].accent)
    arrow(c, [(rx + 30, q.bottom + 4), (rx + 30, reader.y)], t["person"].accent)

    sx, sw = column("store")
    # the history sits below the reading agent, so the search arrow can turn up into it
    blocks, recall = _memory(c, sx, top, sw, history_top=reader.bottom + 14)

    y_write = writer.y + 34
    arrow(c, [(writer.right, y_write), (sx, y_write)], t.ink, label="edits")
    arrow(c, [(sleeper.right, sleeper.y + 34), (sx - 18, sleeper.y + 34), (sx - 18, blocks.bottom - 22),
              (sx, blocks.bottom - 22)], t.muted, label="edits", at=0, offset=(-4, 0))
    y_read = reader.y + 34
    arrow(c, [(blocks.right, y_read), (reader.x, y_read)], t.muted, dashed=True, label="in the\nprompt")
    arrow(c, [(recall.right, recall.cy), (reader.x + 28, recall.cy), (reader.x + 28, reader.bottom)],
          t.muted, dashed=True, label="searched", at=0)

    band = max(sleeper.bottom, reader.bottom, recall.bottom) + 30
    heading(c, wx, band, W - 2 * wx, "USE", "what the answering model is given, and what it replies")
    px = sx
    prompt = prompt_card(
        c, px, band + 22, W - wx - px, "Letta's base prompt, then the persona block.",
        [segment("the human block, always in the prompt", " ".join(HUMAN), icon="layers"),
         segment("what conversation_search() returned",
                 "Searched for “restaurant recommendations Berlin Kreuzberg paneer shellfish "
                 "coeliac peanut allergy”: up to 10 past messages sharing those words, with "
                 "their dates.", outlined=True, icon="history")],
        QUESTION)
    arrow(c, [(reader.cx, reader.bottom), (reader.cx, prompt.y)], t.muted, dashed=True)
    answer = answer_card(c, wx, band + 22, ww, ANSWER, NEEDS)
    arrow(c, [(prompt.x, band + 22 + 13), (answer.right + 4, band + 22 + 13)], t["prompt"].accent)

    footer(c, max(prompt.bottom, answer.bottom) + 24, "Example from notebooks/04-letta.ipynb")
    return c


def _memory(c: Canvas, x: float, y: float, w: float, history_top: float) -> tuple[Box, Box]:
    """The blocks, in the prompt on every call, with the July edit; then the message history,
    outside the prompt, which Letta calls recall."""
    t = c.theme
    s, stale, both = t["store"], t["stale"], t["both"]
    inner = w - 12 - 20
    old_lines = wrap(REPLACED, TINY, inner, MONO)
    human_lines = [wrap(line, TINY, inner, MONO) for line in HUMAN]
    human_h = 30 + len(old_lines) * 15 + 6 + sum(len(lines) * 15 + 4 for lines in human_lines) + 34
    blocks_h = 48 + 50 + human_h + 10
    blocks = panel(c, x, y, w, blocks_h, "layers", "Memory blocks", "in every prompt")

    # persona: Letta's starter text, not ours to show
    persona = Box(x + 6, y + 46, w - 12, 42)
    c.rect(persona, fill=t.card, r=8)
    c.text(persona.x + 10, persona.y + 17, "persona", TINY, BOLD, s.ink)
    c.text(persona.x + 10, persona.y + 33, "who the agent is: Letta's starter text", TINY, SANS, t.muted)

    human = Box(x + 6, persona.bottom + 8, w - 12, human_h)
    c.rect(human, fill=t.card, stroke=s.accent, r=8, width=1.3)
    c.text(human.x + 10, human.y + 18, "human", TINY, BOLD, s.ink)
    c.text(human.right - 10, human.y + 18, "349 of 20,000 characters", TINY, SANS, t.muted, anchor="end")
    yy = human.y + 30
    for line in old_lines:   # the line memory_replace overwrote in July
        c.text(human.x + 10, yy + 11, line, TINY, MONO, stale.accent)
        c.line(human.x + 10, yy + 6.5, human.x + 10 + _w(line), yy + 6.5, stale.accent, 1.1)
        yy += 15
    yy += 6
    for i, lines in enumerate(human_lines):
        if i == 0:
            c.rect(Box(human.x + 5, yy - 1, human.w - 10, len(lines) * 15 + 3), fill=both.wash, r=3)
        for line in lines:
            c.text(human.x + 10, yy + 11, line, TINY, MONO, both.ink if i == 0 else t.ink)
            yy += 15
        yy += 4
    chip(c, human.x + 10, human.bottom - 30, "replaced in place, no history", "stale", icon="x")

    recall = panel(c, x, max(blocks.bottom + 16, history_top), w, 70, "history", "Message history",
                   outlined=True)
    c.text(x + 12, recall.y + 46, "Every past message, outside the prompt.", TINY, SANS, s.ink)
    c.text(x + 12, recall.y + 61, "Letta calls it recall.", TINY, ITALIC, t.muted)
    return blocks, recall


def _w(line: str) -> float:
    from ..kit import measure
    return measure(line, TINY, MONO)
