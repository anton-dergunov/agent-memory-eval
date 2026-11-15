"""Zep / Graphiti: what it costs to store the example's two sessions, next to two simpler designs.

Tokens read and calls to store the same two sessions, from the committed notebook runs:
notebooks/01-textual.ipynb (two rewrites, 357 + 559 tokens), notebooks/02-mem0.ipynb (two
extraction calls, 16,857 tokens), notebooks/03-zep-graphiti.ipynb section 7 (by step, and the
calls per message). Answering calls are not counted.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, SANS, Box, Canvas, W, M, heading, measure
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "graphiti-cost"
TITLE = "What it costs to store two sessions"
ALT = ("Tokens read to store the example's two sessions. Textual memory: 916 tokens in 2 LLM calls. "
       "Mem0: 16,857 tokens in 2 LLM calls and 4 embedding calls. Zep / Graphiti: 60,374 tokens in "
       "38 LLM calls and 25 embedding calls, split by step: finding entities 24,118 tokens in 10 "
       "calls, matching them 7,194 in 7, extracting facts 19,166 in 10, comparing with stored facts "
       "9,896 in 11. Below, Graphiti's LLM calls for each of the ten messages: 2, 3, 6 in session 1 "
       "and 5, 4, 4, 2, 5, 2, 5 in session 2; the assistant's four messages took 11 of the 38 calls "
       "and produced one fact.")

SYSTEMS = [("Textual memory", 916, "2 LLM calls", None),
           ("Mem0", 16857, "2 LLM calls, 4 embeddings", None),
           ("Zep / Graphiti", 60374, "38 LLM calls, 25 embeddings",
            [("find entities", 24118, 10), ("match", 7194, 7), ("extract facts", 19166, 10),
             ("compare", 9896, 11)])]
MESSAGES = [("s1.1", "user", 2), ("s1.2", "assistant", 3), ("s1.3", "user", 6), ("s2.1", "user", 5),
            ("s2.2", "assistant", 4), ("s2.3", "user", 4), ("s2.4", "assistant", 2), ("s2.5", "user", 5),
            ("s2.6", "assistant", 2), ("s2.7", "user", 5)]
SHADES = ("llm", "prompt", "store", "code")


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Tokens the model read to store the same two sessions, ten short "
                       "messages. Graphiti makes several calls per message, each with a long fixed "
                       "prompt, and one more call for every new fact.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 34
    label_w = 196
    bar_w = W - 2 * M - label_w - 10
    top = max(v for _, v, _, _ in SYSTEMS)
    for name, tokens, calls, steps in SYSTEMS:
        c.text(M, y + 16, name, SMALL, BOLD)
        c.text(M, y + 33, calls, TINY, SANS, t.muted)
        x = M + label_w
        if steps:
            for (step, v, n), role in zip(steps, SHADES):
                w = bar_w * v / top
                c.rect(Box(x, y, w - 2, 26), fill=t[role].wash, stroke=t[role].accent, r=4, width=0.8)
                text = f"{step}: {v:,}"
                if measure(text, TINY - 1, MEDIUM) < w - 10:
                    c.text(x + 6, y + 17, text, TINY - 1, MEDIUM, t[role].ink)
                    c.text(x + 6, y + 42, f"{n} calls", TINY - 1, SANS, t.muted)
                else:   # too narrow: name and count under the bar
                    c.text(x + 2, y + 42, f"{step}: {v:,}", TINY - 1, MEDIUM, t[role].ink)
                    c.text(x + 2, y + 57, f"{n} calls", TINY - 1, SANS, t.muted)
                x += w
            c.text(M + label_w + bar_w, y - 6, f"{tokens:,} tokens", SMALL, BOLD, anchor="end")
        else:
            w = max(3, bar_w * tokens / top)
            c.rect(Box(x, y, w, 26), fill=t["llm"].wash, stroke=t["llm"].accent, r=4, width=0.8)
            c.text(x + w + 8, y + 17, f"{tokens:,} tokens", SMALL, BOLD)
        y += 66
    y += 30

    heading(c, M, y, W - 2 * M, "GRAPHITI'S LLM CALLS, MESSAGE BY MESSAGE")
    y += 26
    col = (W - 2 * M) / len(MESSAGES)
    unit = 14
    base = y + 6 * unit + 8
    for i, (label, who, n) in enumerate(MESSAGES):
        x = M + i * col + 10
        role = "person" if who == "user" else "code"
        for k in range(n):
            c.rect(Box(x, base - (k + 1) * unit, col - 20, unit - 3), fill=t[role].wash,
                   stroke=t[role].accent, r=3, width=0.8)
        c.text(x + (col - 20) / 2, base - n * unit - 6, str(n), TINY, BOLD, t[role].ink, anchor="middle")
        c.text(x + (col - 20) / 2, base + 16, label, TINY, MEDIUM, t.muted, anchor="middle")
        c.text(x + (col - 20) / 2, base + 31, who, TINY - 1, SANS, t.faint, anchor="middle")
    y = base + 50
    used = c.paragraph(M, y, "The assistant's four messages took 11 of the 38 calls and produced one "
                       "fact: that the assistant acknowledged fish was now included. The entity prompt, "
                       "read for every message, is about 2,400 tokens each time.", W - 2 * M, TINY,
                       SANS, t.muted)
    source_line(c, y + used + 18, "From notebooks 01, 02 and 03 (section 7); answering calls not counted")
    return c
