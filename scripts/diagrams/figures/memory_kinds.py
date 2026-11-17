"""Working, episodic, semantic and procedural memory, as CoALA defines them for language agents.

From Sumers et al., Cognitive Architectures for Language Agents (2023), §4.1, p. 9–10: working
memory is the information for the current decision cycle, from which each LLM input is built;
episodic memory stores experience from earlier cycles; semantic memory stores knowledge about the
world and the agent itself (retrieval-augmented generation reads a fixed, read-only one);
procedural memory is the LLM's weights and the agent's code. Long-term memories are read into
working memory by retrieval and written by learning. The mechanisms named under each label are
the series' own mapping.
"""

from __future__ import annotations

from ..kit import BOLD, ITALIC, MEDIUM, SANS, Box, Canvas, W, M, arrow, icon_tile, label_pill, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "memory-kinds"
TITLE = "Working, episodic, semantic and procedural memory"
ALT = ("The four kinds of memory in the CoALA framework, each with the mechanism it corresponds to. "
       "At the bottom, working memory: the prompt of the current call, with the instructions, what was "
       "retrieved and the conversation so far. Above it, three long-term memories. Episodic: records of "
       "past sessions, such as the raw turns or summaries of them. Semantic: facts and knowledge, such as "
       "a profile of the user, extracted facts, or a document collection that retrieval-augmented "
       "generation reads but never writes. Procedural: how to act, kept in the model's weights, the "
       "agent's code, and instructions or skill files. Retrieval brings long-term memory into the prompt; "
       "learning writes from the prompt into long-term memory. Memory about a user, the subject of this "
       "series, is episodic and semantic; procedural memory is left out.")

KINDS = [
    ("Episodic", "message-square", "what happened",
     "Records of past sessions: the raw turns, or summaries of them, with their dates.",
     "the two baselines; Letta's message log"),
    ("Semantic", "book-open", "what is known",
     "Facts and knowledge: a profile of the user, extracted facts, a graph. RAG reads a document "
     "collection that it never writes.",
     "Mem0, Zep, textual memory, Honcho"),
    ("Procedural", "wrench", "how to act",
     "The model's weights, the agent's code, and instructions or skill files the agent can read.",
     None),
]
GAP = 14


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    s, p = t["store"], t["prompt"]
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Labels from cognitive science, as CoALA applies them to language agents, "
                       "with what each one is in a running system.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y0 = 62 + used + 24
    c.text(M, y0, "LONG-TERM MEMORY", TINY, BOLD, t.muted, spacing=1.6)
    y0 += 12
    cw = (W - 2 * M - 2 * GAP) / 3
    heights = []
    for name, icon, gist, body, here in KINDS:
        lines = wrap(body, SMALL, cw - 28)
        heights.append(62 + len(lines) * SMALL * 1.4 + (44 if here else 44))
    h = max(heights)
    boxes = []
    for i, (name, icon, gist, body, here) in enumerate(KINDS):
        x = M + i * (cw + GAP)
        box = Box(x, y0, cw, h)
        boxes.append(box)
        out = here is None
        if out:
            c.rect(box, fill=t.paper, stroke=s.accent, r=12, dash="5 4", width=1.2)
        else:
            c.rect(box, fill=s.wash, r=12)
        icon_tile(c, x + 14, y0 + 14, "store", icon, 30)
        c.text(x + 54, y0 + 28, name, SMALL + 1.5, BOLD, s.ink)
        c.text(x + 54, y0 + 44, gist, TINY, ITALIC, s.ink)
        for k, line in enumerate(wrap(body, SMALL, cw - 28)):
            c.text(x + 14, y0 + 74 + k * SMALL * 1.4, line, SMALL, SANS, t.ink)
        if here:
            c.text(x + 14, box.bottom - 30, "In this series", TINY, BOLD, s.accent)
            c.text(x + 14, box.bottom - 13, here, TINY, SANS, s.ink)
        else:
            c.text(x + 14, box.bottom - 13, "Not covered in this series", TINY, BOLD, t.muted)

    # working memory: the prompt of the current call
    wy = y0 + h + 92
    wb = Box(M, wy, W - 2 * M, 96)
    c.rect(wb, fill=p.wash, r=12)
    icon_tile(c, M + 14, wy + 14, "prompt", "scroll-text", 30)
    c.text(M + 54, wy + 28, "Working memory", SMALL + 1.5, BOLD, p.ink)
    c.text(M + 54, wy + 44, "what the model is working with now", TINY, ITALIC, p.ink)
    c.paragraph(M + 14, wy + 54, "The prompt of the current call: the instructions, what was retrieved "
                "from long-term memory, and the conversation so far. It is gone when the call ends, unless "
                "something writes it to long-term memory.", W - 2 * M - 28, SMALL, SANS, t.ink)

    # retrieval down, learning up, between each long-term memory and the prompt
    for box in boxes:
        xr, xl = box.cx - 34, box.cx + 34
        arrow(c, [(xr, box.bottom + 6), (xr, wy - 6)], s.accent, dashed=True)
        arrow(c, [(xl, wy - 6), (xl, box.bottom + 6)], t.ink)
    mid = boxes[0].bottom + (wy - boxes[0].bottom) / 2
    label_pill(c, boxes[0].cx - 34, mid, "retrieval", s.accent)
    label_pill(c, boxes[0].cx + 34, mid, "learning", t.ink)

    source_line(c, wb.bottom + 28, "After Sumers et al., Cognitive Architectures for Language Agents (2023), p. 9–10")
    return c
