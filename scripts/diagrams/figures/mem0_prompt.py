"""Mem0: what one extraction call reads, to scale.

The token counts are from the committed run of notebooks/02-mem0.ipynb (section 4): a system
prompt of 8,131 tokens on every add(), and user prompts of 161 and 439 tokens. The split of the
system prompt is by characters of `ADDITIVE_EXTRACTION_PROMPT` in mem0ai 2.2.1
(`mem0/configs/prompts.py`), 33,653 characters between its top-level headings.
"""

from __future__ import annotations

from ..kit import BOLD, SANS, Box, Canvas, W, M, heading, measure
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme

NAME = "mem0-prompt"
TITLE = "What one extraction call reads"
ALT = ("Two bars drawn to the same scale, one for each of the two extraction calls in the example. "
       "Each call reads the same system prompt of 8,131 tokens. By characters, the system prompt "
       "is 2.5% role, 11.6% a description of the inputs, 40.1% guidelines on what to extract and "
       "how to write a memory, 38.5% eleven worked examples, 3.5% a final checklist and 3.7% the "
       "output format. Next to it, the user prompt with the conversation is a thin slice: 161 "
       "tokens for the first session and 439 tokens for the second, which also carries the five "
       "stored facts and the earlier messages.")

SYSTEM = 8131
# (label, share of the system prompt's characters, what it holds)
SECTIONS = [
    ("Role", 2.5, "“Your sole operation is ADD”"),
    ("Inputs", 11.6, "the seven slots of the user prompt, and the rule for dates"),
    ("Guidelines", 40.1, "what to extract, how to write a memory, what never to do, linking"),
    ("Examples", 38.5, "eleven worked examples (numbered 1 to 12, with no number 4)"),
    ("Checklist", 3.5, "re-read every message before answering"),
    ("Output", 3.7, "the JSON format"),
]
CALLS = [("Session 1", 161, "3 messages"),
         ("Session 2", 439, "7 messages, the 5 stored facts and the 3 earlier messages")]
SHADES = ("llm", "code", "llm", "code", "llm", "code")
BAR_H = 34


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Each add() sends the same instructions, then the conversation. "
                       "The bars are to scale: for a short session, the conversation is a thin "
                       "slice at the right end.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 34
    full = W - 2 * M
    scale = full / (SYSTEM + max(n for _, n, _ in CALLS))

    for name, user, what in CALLS:
        c.text(M, y, name, SMALL, BOLD)
        c.text(M + measure(name, SMALL, BOLD) + 8, y,
               f"{SYSTEM:,} + {user} = {SYSTEM + user:,} tokens read", TINY, SANS, t.muted)
        y += 10
        x = M
        for (label, share, _), role in zip(SECTIONS, SHADES):
            w = SYSTEM * scale * share / 100
            c.rect(Box(x, y, w - 1.5, BAR_H), fill=t[role].wash, r=3)
            if measure(label, TINY, BOLD) + 10 < w:
                c.text(x + 6, y + BAR_H / 2 + 4, label, TINY, BOLD, t[role].ink)
            x += w
        uw = user * scale
        c.rect(Box(x, y, uw, BAR_H), fill=t["person"].accent, r=3)
        c.text(x + uw, y + BAR_H + 15, f"the conversation: {user} tokens", TINY, BOLD,
               t["person"].accent, anchor="end")
        c.text(M, y + BAR_H + 15, f"the system prompt: {SYSTEM:,} tokens, the same on every call",
               TINY, SANS, t.muted)
        c.text(x + uw, y + BAR_H + 31, what, TINY, SANS, t.muted, anchor="end")
        y += BAR_H + 62

    heading(c, M, y, full, "INSIDE THE SYSTEM PROMPT", "shares of its 33,653 characters")
    y += 24
    for (label, share, what), role in zip(SECTIONS, SHADES):
        c.rect(Box(M, y - 11, 14, 14), fill=t[role].wash, stroke=t[role].accent, r=3)
        c.text(M + 22, y, label, TINY, BOLD)
        c.text(M + 150, y, f"{share:.1f}%", TINY, BOLD, anchor="end")
        c.text(M + 164, y, what, TINY, SANS, t.muted)
        y += 20

    y += 6
    c.line(M, y, W - M, y, t.line)
    y += 20
    c.text(W - M, y, "Token counts from notebooks/02-mem0.ipynb; the prompt is "
           "mem0/configs/prompts.py, version 2.2.1", TINY, SANS, t.muted, anchor="end")
    c.height = int(y + 20)
    return c
