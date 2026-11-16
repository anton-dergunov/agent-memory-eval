"""What ChatGPT's prompt held in December 2025, as Manthan Gupta reverse engineered it.

Source: Manthan Gupta, "I Reverse Engineered ChatGPT's Memory System, and Here's What I Found!"
(2025-12-09), https://manthanguptaa.in/posts/chatgpt_memory/ . He asked ChatGPT about its own
context; OpenAI has not confirmed it. The blocks and their contents are his.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, MONO, SANS, Box, Canvas, W, M, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "chatgpt-context"
TITLE = "What ChatGPT's prompt held, December 2025"
ALT = ("Seven blocks in the order ChatGPT received them with every message, as reverse engineered "
       "in December 2025: system instructions; developer instructions; session metadata such as "
       "device and rough location, for this session only; user memory, the saved facts, 33 in the "
       "author's case, inserted into every prompt; a summary of recent conversations, about 15 "
       "entries, each a time stamp, a chat title and snippets of the user's own messages; the "
       "messages of the current chat; and the latest message. No search over past conversations "
       "was found.")

BLOCKS = [
    ("[0]", "System instructions", "", None),
    ("[1]", "Developer instructions", "", None),
    ("[2]", "Session metadata", "device, browser, rough location, plan; for this session only", None),
    ("[3]", "User memory", "the saved facts (33 in his account), inserted into every prompt", "store"),
    ("[4]", "Recent conversations summary", "about 15 entries: a time stamp, the chat's title, and "
     "snippets of the user's own messages, not the assistant's", "store"),
    ("[5]", "Current session messages", "this chat, in full, up to a token limit he could not find", "prompt"),
    ("[6]", "Your latest message", "", "person"),
]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The blocks ChatGPT received with every message, in order, as one person "
                       "found by asking ChatGPT about its own context. The two memory blocks are "
                       "precomputed and inserted whole; he found no search over past chats.",
                       W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 26
    x, w = M + 40, W - 2 * M - 40
    for idx, name, detail, role in BLOCKS:
        lines = wrap(detail, SMALL, w - 300) if detail else []
        h = max(40, 18 + len(lines) * SMALL * 1.35)
        box = Box(x, y, w, h)
        if role:
            r = t[role]
            c.rect(box, fill=r.wash, stroke=r.accent if role == "store" else None, r=8, width=1.2)
            ink = r.ink
        else:
            c.rect(box, fill=t.surface, r=8)
            ink = t.muted
        c.text(M, y + h / 2 + 5, idx, SMALL, MONO, t.muted)
        c.text(x + 14, y + 25, name, SMALL + 0.5, BOLD, ink)
        for i, line in enumerate(lines):
            c.text(x + 290, y + 24 + i * SMALL * 1.35, line, SMALL, SANS, ink)
        y += h + 6
    y += 12
    c.text(M, y, "Memory blocks", TINY, MEDIUM, t["store"].accent)
    source_line(c, y + 10, "Reverse engineered by Manthan Gupta, December 2025 [R]; not confirmed by OpenAI")
    return c
