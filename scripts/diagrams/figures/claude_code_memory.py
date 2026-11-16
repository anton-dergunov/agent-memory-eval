"""Claude Code's two kinds of memory: what loads at the start of a session, and what is read on demand.

From Anthropic's documentation, "How Claude remembers your project"
(https://code.claude.com/docs/en/memory), as of November 2026: CLAUDE.md files written by the
user and loaded whole; auto memory written by Claude, a MEMORY.md index of which the first 200
lines or 25 KB load at start, and topic files read with the file tools when needed; a `modified`
time stamp written into each memory file's frontmatter by Claude Code. The file names are the
documentation's examples; the frontmatter is an illustration.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, MONO, SANS, Box, Canvas, W, M, arrow, icon_tile, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "claude-code-memory"
TITLE = "Claude Code: an index loaded, topics read on demand"
ALT = ("At the start of a session Claude Code loads two things into the prompt: the CLAUDE.md files, "
       "which the user writes, and the first 200 lines or 25 KB of MEMORY.md, an index that Claude "
       "writes, one line per memory. The topic files the index points to, such as user_role.md and "
       "feedback_testing.md, are not loaded; Claude reads one with its file tools when it needs it. "
       "When Claude writes a memory it writes a topic file and a one-line pointer in the index, and "
       "Claude Code stamps the file with the time it was written, so a fact read months later shows "
       "how current it is.")

INDEX = ["- [User role](user_role.md) — their work",
         "- [Testing](feedback_testing.md) — tests first",
         "- …"]
TOPIC = ["---",
         "name: testing",
         "description: run the integration tests first",
         "type: feedback",
         "modified: 2026-11-16T14:02:11Z",
         "---",
         "Run the integration tests before committing.",
         "Why: …"]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "What goes into every session, and what Claude reads only when it needs "
                       "it. Each memory file carries the time it was written.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 28

    # left: the prompt at the start of a session
    lw = 400
    p = t["prompt"]
    c.text(M, y, "LOADED AT THE START OF EVERY SESSION", TINY, BOLD, t.muted, spacing=1.4)
    b1 = Box(M, y + 12, lw, 66)
    c.rect(b1, fill=p.wash, r=10)
    icon_tile(c, b1.x + 12, b1.y + 12, "person", "user", 26)
    c.text(b1.x + 48, b1.y + 24, "CLAUDE.md files", SMALL + 0.5, BOLD, p.ink)
    c.text(b1.x + 48, b1.y + 42, "written by you: instructions, loaded whole", TINY, SANS, p.ink)
    b2 = Box(M, b1.bottom + 10, lw, 132)
    c.rect(b2, fill=p.wash, r=10)
    icon_tile(c, b2.x + 12, b2.y + 12, "store", "list", 26)
    c.text(b2.x + 48, b2.y + 24, "MEMORY.md, the index", SMALL + 0.5, BOLD, p.ink)
    c.text(b2.x + 48, b2.y + 42, "written by Claude; first 200 lines or 25 KB", TINY, SANS, p.ink)
    for i, line in enumerate(INDEX):
        c.text(b2.x + 16, b2.y + 70 + i * 18, line, TINY - 1, MONO, p.ink)

    # right: the memory directory
    rx = M + lw + 70
    rw = W - M - rx
    s = t["store"]
    c.text(rx, y, "READ ON DEMAND, WITH THE FILE TOOLS", TINY, BOLD, t.muted, spacing=1.4)
    d = Box(rx, y + 12, rw, b2.bottom - y - 12)
    c.rect(d, fill=s.wash, r=10)
    c.text(d.x + 14, d.y + 24, "feedback_testing.md", SMALL, MONO, s.ink)
    for i, line in enumerate(TOPIC):
        colour = s.accent if line.startswith("modified") else s.ink
        face = BOLD if line.startswith("modified") else MONO
        c.text(d.x + 14, d.y + 50 + i * 17, line, TINY - 1.5, MONO if face == MONO else BOLD, colour)
    c.text(d.x + 14, d.bottom - 12, "user_role.md, …", TINY - 1, MONO, t.muted)

    # the arrows: the index points to topic files; Claude reads one when it needs it
    ay = b2.y + 82
    arrow(c, [(b2.right + 6, ay), (d.x - 6, ay)], t.muted)
    mid = (b2.right + d.x) / 2
    c.text(mid, ay + 20, "read when", TINY - 1, MEDIUM, t.muted, anchor="middle")
    c.text(mid, ay + 35, "needed", TINY - 1, MEDIUM, t.muted, anchor="middle")
    by = b2.bottom + 40
    c.text(M, by, "Claude writes a memory as a topic file plus one line in the index; Claude Code stamps "
           "the file with the time of the write.", TINY, MEDIUM, t.ink)
    c.text(M, by + 20, "Near the size limit Claude Code tells Claude to shorten the index; past it, the "
           "write returns an error.", TINY, SANS, t.muted)
    source_line(c, by + 34, "Anthropic, Claude Code documentation, November 2026 [V]; file contents illustrative")
    return c
