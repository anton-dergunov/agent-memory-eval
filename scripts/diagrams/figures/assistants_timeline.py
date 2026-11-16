"""When memory arrived in the assistants and coding agents, by product, 2024 to 2026.

Each date and its source are in the blog's _drafts/agent-memory/9-assistants.sources.md:
V the vendor's own page, C code the vendor published, T a third party. ChatGPT's dates are
OpenAI's own history in its June 2026 post on dreaming.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, SANS, Box, Canvas, W, M, measure
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "assistants-timeline"
TITLE = "When memory arrived"
ALT = ("A timeline from 2024 to 2026 with one lane per product. ChatGPT: saved memories in April "
       "2024, references to past chats in April 2025, dreaming in June 2026. Codex: a memory "
       "pipeline in its code from February 2026, version 2 in September 2026. Claude app: search "
       "over past chats in August 2025, a memory summary in September 2025, free users in March "
       "2026, topics written as you chat in July 2026. Claude Code: auto memory in February 2026. "
       "Claude API: the memory tool in September 2025. Gemini app: recalls past chats in February "
       "2025, on by default in August 2025, Personal Intelligence in January 2026, renamed memory "
       "with an import in March 2026. Gemini CLI: a save_memory tool in June 2025, plain files in "
       "four tiers and Auto Memory in April 2026. Grok: April 2025. Le Chat: September 2025. "
       "Perplexity: November 2025.")

START, END = (2024, 1), (2027, 1)  # the axis runs from January 2024 to the end of 2026
# (vendor, product, role, [(year, month, label, mark)])
LANES = [
    ("OpenAI", "ChatGPT", "prompt", [(2024, 4, "saved memories", "V"), (2025, 4, "references past chats", "V"),
                                     (2026, 6, "dreaming", "V")]),
    ("OpenAI", "Codex", "code", [(2026, 2, "memory pipeline", "C"), (2026, 9, "v2", "C")]),
    ("Anthropic", "Claude app", "prompt", [(2025, 8, "searches past chats", "V"), (2025, 9, "memory summary", "V"),
                                          (2026, 3, "free users", "V"), (2026, 7, "topics, as you chat", "V")]),
    ("Anthropic", "Claude Code", "code", [(2026, 2, "auto memory", "V")]),
    ("Anthropic", "Claude API", "code", [(2025, 9, "memory tool", "V")]),
    ("Google", "Gemini app", "prompt", [(2025, 2, "recalls past chats", "V"), (2025, 8, "on by default", "V"),
                                        (2026, 1, "Personal Intelligence", "V"), (2026, 3, "renamed memory", "V")]),
    ("Google", "Gemini CLI", "code", [(2025, 6, "save_memory tool", "C"), (2026, 4, "files in four tiers", "C")]),
    ("Others", "Grok", "prompt", [(2025, 4, "memory (beta)", "T")]),
    ("Others", "Le Chat", "prompt", [(2025, 9, "Memories (beta)", "V")]),
    ("Others", "Perplexity", "prompt", [(2025, 11, "memory", "V")]),
]
X0 = M + 150
LANE = 56


def _x(year: int, month: int) -> float:
    total = (END[0] - START[0]) * 12
    k = (year - START[0]) * 12 + (month - 1) + 0.5
    return X0 + (W - M - X0) * k / total


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Memory in the chat apps and the coding agents, by the month it shipped. "
                       "The letter says where the date comes from.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30

    # the years
    for year in (2024, 2025, 2026):
        x = _x(year, 1) - (W - M - X0) / 72
        c.line(x, y - 4, x, y + 14 + LANE * len(LANES), t.line)
        c.text(x + 6, y + 8, str(year), TINY, BOLD, t.muted)
    y += 22

    vendor = None
    for vendor_name, product, role, events in LANES:
        r = t[role]
        if vendor_name != vendor:
            c.line(M, y, W - M, y, t.line)
            c.text(M, y + 16, vendor_name.upper(), TINY - 1.5, BOLD, t.faint, spacing=1.4)
            vendor = vendor_name
        mid = y + LANE / 2 + 6
        c.text(M, mid + 4, product, SMALL, MEDIUM, t.ink)
        c.line(X0, mid, W - M, mid, t.line, 1.0, dash="2 4")
        # each label goes above its dot, else below, else higher above, so that none runs into another
        last_end = {"above": -1e9, "below": -1e9, "high": -1e9}
        for year, month, label, mark in events:
            x = _x(year, month)
            c.circle(x, mid, 5, fill=r.accent)
            text = f"{label} "
            width = measure(text, TINY, SANS) + measure(mark, TINY - 1, BOLD)
            lx = min(x - 4, W - M - width)
            side = next((k for k in ("above", "below", "high") if lx > last_end[k] + 10), "high")
            ty = {"above": mid - 10, "below": mid + 20, "high": mid - 27}[side]
            c.text(lx, ty, text, TINY, SANS, t.ink)
            c.text(lx + measure(text, TINY, SANS), ty, mark, TINY - 1, BOLD, t.muted)
            last_end[side] = lx + width
        y += LANE
    c.line(M, y, W - M, y, t.line)

    # the key
    y += 24
    x = M
    for role, meaning in (("prompt", "chat app"), ("code", "coding agent or API")):
        c.circle(x + 5, y - 4, 5, fill=t[role].accent)
        x += 16 + c.text(x + 16, y, meaning, TINY, SANS, t.muted) + 22
    for mark, meaning in (("V", "the vendor's own page"), ("C", "the vendor's published code"),
                          ("T", "a third party (press)")):
        x += c.text(x, y, mark, TINY, BOLD, t.muted) + 6
        x += c.text(x, y, meaning, TINY, SANS, t.muted) + 18
    source_line(c, y + 16, "Dates and sources: part 9 of the series, as of November 2026")
    return c
