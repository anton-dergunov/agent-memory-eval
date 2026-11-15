"""Letta: what conversation_search does on a self-hosted server, and the notebook's five queries.

The rule is Letta 0.16.8 without Turbopuffer (`search_messages_async` in
letta/services/message_manager.py and `conversation_search` in the tool executor). The queries
and what they returned are the question turn (session 3) of the in-line agent in the committed run
of notebooks/04-letta.ipynb.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, MONO, SANS, Box, Canvas, W, M, arrow, chip, heading, kind_badge, measure, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "letta-search"
TITLE = "How conversation_search finds messages"
ALT = ("Top, the rule of a self-hosted Letta server, four steps of plain code: keep the messages "
       "of every conversation that contain the whole query as one piece of text, ignoring case; "
       "order them newest first; keep the first five; drop tool messages, after the cut. The "
       "description the model reads promises a hybrid text and semantic search, which needs a "
       "hosted vector service. Bottom, the five queries the agent made before answering the "
       "question in the notebook: three long ones found nothing; 'restaurant recommendations' "
       "found one of the agent's own earlier replies; 'Kreuzberg' found four messages, three of "
       "them the agent's replies and one the user's message about the move. None returned "
       "anything that was not already in the memory block.")

RULE = [("Keep", "messages that contain the whole query, as one piece of text, ignoring case"),
        ("Order", "newest first, across all conversations"),
        ("Cut", "keep the first five"),
        ("Drop", "tool messages, after the cut")]
QUERIES = [  # (query, [(who, n)])
    ("Berlin Kreuzberg Indian restaurant paneer peanut allergy shellfish allergy coeliac", []),
    ("Indian restaurant Kreuzberg", []),
    ("dinner Berlin Kreuzberg", []),
    ("restaurant recommendations", [("agent", 1)]),
    ("Kreuzberg", [("agent", 3), ("user", 1)]),
]
PAD = 12


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The tool's description promises “hybrid search (text + semantic "
                       "similarity)”. A self-hosted server, without a hosted vector database, "
                       "runs four steps of plain code instead.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30
    heading(c, M, y, W - 2 * M, "THE RULE", "Letta 0.16.8, self-hosted: plain code, no model call")
    y += 22
    n = len(RULE)
    gap = 26
    bw = (W - 2 * M - gap * (n - 1)) / n
    h = 86
    for i, (title, text) in enumerate(RULE):
        x = M + i * (bw + gap)
        c.rect(Box(x, y, bw, h), fill=t.card, stroke=t.line, r=8)
        c.text(x + PAD, y + 22, f"{i + 1}. {title}", SMALL, BOLD)
        c.paragraph(x + PAD, y + 30, text, bw - 2 * PAD, TINY, SANS, t.muted)
        if i < n - 1:
            arrow(c, [(x + bw + 3, y + h / 2), (x + bw + gap - 3, y + h / 2)], t.faint, width=1.3)
    y += h + 18
    used = c.paragraph(M, y, "So a list of keywords matches almost nothing, and a short query "
                       "returns the newest messages that mention it: often the question itself and "
                       "the agent's own long replies. In the experiment, the results of the "
                       "agent's memory edits, each a copy of the whole block, also took places "
                       "among the five before they were dropped.", W - 2 * M, TINY, SANS, t.muted)
    y += used + 34

    heading(c, M, y, W - 2 * M, "THE FIVE SEARCHES BEFORE THE ANSWER", "session 3, in the notebook")
    y += 26
    qx = M + 26
    rx = M + 450
    for i, (query, found) in enumerate(QUERIES):
        c.text(M, y + 16, f"{i + 1}", SMALL, BOLD, t.muted)
        lines = wrap(query, TINY, rx - qx - 20, MONO)
        box_h = 12 + len(lines) * 16
        c.rect(Box(qx, y, rx - qx - 20, box_h), fill=t["llm"].wash, r=6)
        for k, line in enumerate(lines):
            c.text(qx + 10, y + 18 + k * 16, line, TINY, MONO, t["llm"].ink)
        if not found:
            c.text(rx, y + 18, "No results found.", TINY, MEDIUM, t.muted)
        else:
            cx = rx
            for who, k in found:
                role = "code" if who == "agent" else "person"
                label = f"{k} × the agent's own reply" if who == "agent" else f"{k} × the user's message"
                b = chip(c, cx, y + 4, label, role, face=MEDIUM)
                cx = b.right + 6
        y += box_h + 10
    y += 4
    used = c.paragraph(M, y, "Everything the answer needed was already in the memory block. "
                       "The searches added five model calls and nothing new.",
                       W - 2 * M, TINY, SANS, t.muted)
    source_line(c, y + used + 16, "Rule: Letta 0.16.8. Queries: notebooks/04-letta.ipynb, section 3")
    return c
