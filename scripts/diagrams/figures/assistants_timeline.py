"""When memory arrived in the assistants and coding agents, by product, 2024 to 2026.

Each date and its source are in the blog's _drafts/agent-memory/9-assistants.sources.md:
V the vendor's own page, C code the vendor published, T a third party. ChatGPT's dates are
from OpenAI's release notes and its posts of February 2024 and June 2026.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, SANS, Box, Canvas, W, M, measure
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "assistants-timeline"
TITLE = "When memory arrived"
ALT = ("A timeline from 2024 to 2026 with one row per product, grouped by vendor. ChatGPT: saved "
       "memories in April 2024, references to past chats in April 2025, a search over past chats "
       "in January 2026, dreaming in June 2026. Codex: a memory pipeline in its code from February "
       "2026, version 2 in September 2026. Claude app: search over past chats in August 2025, a "
       "memory summary in September 2025, free users in March 2026, topics written as you chat in "
       "July 2026. Claude Code: auto memory in February 2026. Claude API: the memory tool in "
       "September 2025. Gemini app: recalls past chats in February 2025, on by default in August "
       "2025, Personal Intelligence in January 2026, renamed memory with an import in March 2026. "
       "Gemini CLI: a save_memory tool in June 2025, plain files in four tiers and Auto Memory in "
       "April 2026. Meta AI: January 2025. Grok: April 2025. Le Chat: September 2025. Perplexity: November 2025. A marker "
       "shows November 2026, the date of this description.")

START, END = (2024, 1), (2027, 1)  # the axis runs from January 2024 to the end of 2026
NOW = (2026, 11)
# (vendor, [(product, role, [(year, month, label, mark)])])
GROUPS = [
    ("OpenAI", [
        ("ChatGPT", "prompt", [(2024, 4, "saved memories", "V"), (2025, 4, "references past chats", "V"),
                               (2026, 1, "searches past chats", "V"), (2026, 6, "dreaming", "V")]),
        ("Codex", "code", [(2026, 2, "memory pipeline", "C"), (2026, 9, "v2", "C")]),
    ]),
    ("Anthropic", [
        ("Claude app", "prompt", [(2025, 8, "searches past chats", "V"), (2025, 9, "memory summary", "V"),
                                  (2026, 3, "free users", "V"), (2026, 7, "topics, as you chat", "V")]),
        ("Claude Code", "code", [(2026, 2, "auto memory", "V")]),
        ("Claude API", "code", [(2025, 9, "memory tool", "V")]),
    ]),
    ("Google", [
        ("Gemini app", "prompt", [(2025, 2, "recalls past chats", "V"), (2025, 8, "on by default", "V"),
                                  (2026, 1, "Personal Intelligence", "V"), (2026, 3, "renamed memory", "V")]),
        ("Gemini CLI", "code", [(2025, 6, "save_memory tool", "C"), (2026, 4, "files in four tiers", "C")]),
    ]),
    ("Others", [
        ("Meta AI", "prompt", [(2025, 1, "memory", "T")]),
        ("Grok", "prompt", [(2025, 4, "memory (beta)", "T")]),
        ("Le Chat", "prompt", [(2025, 9, "Memories (beta)", "V")]),
        ("Perplexity", "prompt", [(2025, 11, "memory", "V")]),
    ]),
]
X0 = M + 128           # where the time axis starts
X1 = W - M - 10        # where it ends
BAND = 62              # the height of one product's band
GAP = 6                # between bands
GROUP_GAP = 34         # above each vendor's name
PILL = TINY + 9        # the height of a label pill


def _x(year: int, month: int, day: float = 0.5) -> float:
    total = (END[0] - START[0]) * 12
    k = (year - START[0]) * 12 + (month - 1) + day
    return X0 + (X1 - X0) * k / total


def _pill_width(label: str, mark: str) -> float:
    return measure(label, TINY, SANS) + 8 + measure(mark, TINY - 1.5, BOLD) + 16


def _pill(c: Canvas, x: float, top: float, label: str, mark: str, role: str) -> float:
    """A label in the product's colour, with its source letter; returns its right edge."""
    t = c.theme
    r = t[role]
    w = _pill_width(label, mark)
    c.rect(Box(x, top, w, PILL), fill=r.wash, stroke=r.accent, r=PILL / 2, width=0.7)
    tx = x + 8 + c.text(x + 8, top + PILL / 2 + TINY * 0.36, label, TINY, SANS, r.ink)
    c.text(tx + 6, top + PILL / 2 + TINY * 0.36, mark, TINY - 1.5, BOLD, t.muted)
    return x + w


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Memory in the chat apps and the coding agents, by the month it shipped. "
                       "The letter says where the date comes from.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 34

    # the axis: years above, a tick at every quarter
    c.line(X0, y + 22, X1, y + 22, t.faint, 1.2)
    for year in (2024, 2025, 2026):
        c.text((_x(year, 1, 0) + _x(year, 12, 1)) / 2, y + 2, str(year), SMALL, BOLD, t.ink, anchor="middle")
        for month, name in ((1, "Jan"), (4, "Apr"), (7, "Jul"), (10, "Oct")):
            x = _x(year, month, 0)
            c.line(x, y + 17, x, y + 27, t.faint, 1.2 if month == 1 else 0.8)
            c.text(x + 3, y + 40, name, TINY - 2, SANS, t.faint)
    top = y + 50

    # the date of this description, under the bands' contents
    xn = _x(*NOW)
    c.text(xn, top + 2, "Nov 2026", TINY - 2, BOLD, t["stale"].accent, anchor="middle")

    # the bands
    y = top
    for vendor, products in GROUPS:
        y += GROUP_GAP
        c.text(M, y - 10, vendor.upper(), TINY - 1, BOLD, t.muted, spacing=1.4)
        for product, role, events in products:
            r = t[role]
            c.rect(Box(M, y, W - 2 * M, BAND), fill=t.surface, r=10)
            c.line(xn, y - GROUP_GAP + 10 if product == products[0][0] else y - GAP, xn, y + BAND,
                   t["stale"].accent, 1.0, dash="3 3")
            mid = y + BAND / 2
            c.text(M + 12, mid + 5, product, SMALL, MEDIUM, t.ink)
            c.line(X0, mid, X1, mid, t.line, 1.4)
            # each label goes above its dot or below it, on the side where it has to move least to
            # clear the label before it; a label moved right gets a bent stem
            last = {"above": -1e9, "below": -1e9}
            for year, month, label, mark in events:
                x = _x(year, month)
                want = min(x - 10, X1 - _pill_width(label, mark))
                side = min(("above", "below"), key=lambda k: max(0.0, last[k] + 6 - want))
                px = max(want, last[side] + 6)
                ptop = mid - 7 - PILL if side == "above" else mid + 7
                edge = ptop + (PILL if side == "above" else 0)
                if px > x - 4:   # moved right: up (or down) to the pill's middle, then across
                    ymid = ptop + PILL / 2
                    c.path(f"M {x:.1f} {mid:.1f} L {x:.1f} {ymid:.1f} L {px:.1f} {ymid:.1f}", stroke=r.accent, width=1.0)
                else:
                    c.line(x, mid, x, edge, r.accent, 1.0)
                last[side] = _pill(c, px, ptop, label, mark, role)
                c.circle(x, mid, 5.5, fill=r.accent, stroke=t.surface, width=2)
            y += BAND + GAP
    bottom = y - GAP

    # the key
    y = bottom + 30
    x = M
    for role, meaning in (("prompt", "chat app"), ("code", "coding agent or API")):
        c.circle(x + 5, y - 4, 5, fill=t[role].accent)
        x += 16 + c.text(x + 16, y, meaning, TINY, SANS, t.muted) + 20
    for mark, meaning in (("V", "the vendor's own page"), ("C", "the vendor's published code"),
                          ("T", "a third party (press)")):
        x += c.text(x, y, mark, TINY, BOLD, t.muted) + 6
        x += c.text(x, y, meaning, TINY, SANS, t.muted) + 16
    source_line(c, y + 16, "Dates and sources: part 9 of the series, as of November 2026")
    return c
