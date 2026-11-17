"""Who writes the memory, and when: four writers on the timeline of two conversations.

Schematic. Nobody: the raw messages are kept as they are. A pipeline: an extraction call after
each message or each session (Mem0, Graphiti). The answering agent: a tool call inside its own turn,
while the user waits (Letta, ChatGPT's saved memories in 2024). A background process: a job that
runs later, between conversations (textual memory, Honcho's dreams, ChatGPT's dreaming). How each
loses facts is the series' summary of parts 3–8.
"""

from __future__ import annotations

from ..kit import BOLD, ITALIC, MEDIUM, SANS, Box, Canvas, W, M, icon_tile, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "writers"
TITLE = "Who writes the memory, and when"
ALT = ("A timeline of two conversations with a gap between them, and four rows, one per kind of writer. "
       "Nobody: the raw messages are kept as they arrive, and nothing is lost or cleaned up, so old and new "
       "values both stay. A pipeline: an extraction call runs after each message or at the end of the "
       "session; it loses what its prompt does not ask for. The answering agent: it writes with a tool call "
       "inside its own turn, while the user waits; it loses what it does not decide to write. A background "
       "process: it runs later, between the conversations; it can rewrite or drop what it should keep, and "
       "its result is not ready until it has run.")

X0 = M + 196          # where the timeline starts
X1 = W - M - 8
S1 = (X0, X0 + 330)   # the first conversation
S2 = (X1 - 150, X1)   # the next one
TURNS = [S1[0] + 20, S1[0] + 120, S1[0] + 220]   # the user's messages in the first conversation
ROW = 64

LANES = [
    ("Nobody", "the raw messages are the memory", "code",
     "Loses nothing, cleans nothing: old and new values both stay."),
    ("A pipeline", "after each message or session", "llm",
     "Loses what its prompt does not ask for."),
    ("The answering agent", "a tool call inside its turn", "llm",
     "Loses what it does not decide to write."),
    ("A background process", "later, between conversations", "llm",
     "Can rewrite or drop what it should keep; is late."),
]


def _turn(c: Canvas, x: float, y: float) -> tuple[float, float]:
    """A user message and the reply after it; returns the reply's x range."""
    t = c.theme
    c.rect(Box(x, y, 34, 14), fill=t["person"].accent, r=4)
    c.rect(Box(x + 38, y, 52, 14), fill=t["prompt"].accent, r=4, opacity=0.8)
    return x + 38, x + 90


def _mark(c: Canvas, x: float, y: float, role: str) -> None:
    icon = "sparkles" if role == "llm" else "database"
    icon_tile(c, x - 11, y - 11, role if role == "llm" else "store", icon, 22)


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Four kinds of writer, placed on the timeline of two conversations. Each runs "
                       "at a different moment, and each loses facts in its own way.", W - 2 * M, SUBTITLE,
                       SANS, t.muted)
    y = 62 + used + 30

    # the conversations
    for (a, b), label in ((S1, "a conversation"), (S2, "the next conversation")):
        c.text(a, y, label.upper(), TINY - 1, BOLD, t.muted, spacing=1.2)
    gap_mid = (S1[1] + S2[0]) / 2
    c.text(gap_mid, y, "hours or days later", TINY - 1, ITALIC, t.muted, anchor="middle")
    ty = y + 14
    replies = [_turn(c, x, ty) for x in TURNS]
    _turn(c, S2[0] + 20, ty)
    c.line(S1[1] + 16, ty + 7, S2[0] - 16, ty + 7, t.faint, 1.2, dash="2 4")
    # the key for the turns
    kx = M
    c.rect(Box(kx, ty, 14, 14), fill=t["person"].accent, r=4)
    kx += 20 + c.text(kx + 20, ty + 11, "user", TINY, SANS, t.muted) + 12
    c.rect(Box(kx, ty, 14, 14), fill=t["prompt"].accent, r=4, opacity=0.8)
    c.text(kx + 20, ty + 11, "reply", TINY, SANS, t.muted)

    y = ty + 34
    for i, (who, when, role, loses) in enumerate(LANES):
        top = y + i * (ROW + 30)
        c.rect(Box(M, top, W - 2 * M, ROW), fill=t.surface, r=10)
        c.text(M + 12, top + 24, who, SMALL, BOLD, t.ink)
        c.text(M + 12, top + 42, when, TINY, SANS, t.muted)
        mid = top + ROW / 2
        c.line(X0, mid, X1, mid, t.line, 1.4)
        # the turns, faint, so the marks can be read against them
        for x in TURNS + [S2[0] + 20]:
            c.rect(Box(x, mid - 3, 90, 6), fill=t.line, r=3)
        if who == "Nobody":
            for x in TURNS:
                _mark(c, x + 17, mid, "code")
                _mark(c, x + 64, mid, "code")
        elif who == "A pipeline":
            for (a, b) in replies:
                _mark(c, b + 14, mid, "llm")
        elif who == "The answering agent":
            a, b = replies[1]
            _mark(c, (a + b) / 2, mid, "llm")
            c.text((a + b) / 2, top + 12, "while the user waits", TINY - 1.5, ITALIC, t["llm"].accent, anchor="middle")
        else:
            _mark(c, gap_mid, mid, "llm")
        # how it loses facts, under the row
        c.text(X0, top + ROW + 16, loses, TINY, ITALIC, t["stale"].accent)

    bottom = y + len(LANES) * (ROW + 30) + 8
    kx = M
    icon_tile(c, kx, bottom, "llm", "sparkles", 18)
    kx += 24 + c.text(kx + 24, bottom + 13, "a model call that writes", TINY, SANS, t.muted) + 14
    icon_tile(c, kx, bottom, "store", "database", 18)
    kx += 24 + c.text(kx + 24, bottom + 13, "a message stored as it is", TINY, SANS, t.muted) + 14
    c.text(kx, bottom + 13, "In red: how each one loses facts", TINY, SANS, t["stale"].accent)
    source_line(c, bottom + 30, "Schematic; the four writers as described in this series")
    return c
