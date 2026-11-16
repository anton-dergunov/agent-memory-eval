"""Codex's memory pipeline: extraction per conversation, consolidation by an agent, a summary loaded.

From openai/codex at commit 3257e1b3eb04a43a8721ad0e59470327807eb844: codex-rs/memories/README.md,
the templates in codex-rs/memories/write/templates/memories/ and
codex-rs/ext/memories/templates/memories/, the defaults in codex-rs/config/src/types.rs and
the 2,500-token limit in codex-rs/ext/memories/src/lib.rs. Version 2, the default for a new profile.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, MONO, SANS, Box, Canvas, W, M, arrow, node
from ..theme import SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "codex-memory"
TITLE = "Codex: a pipeline that writes, a summary that is loaded"
ALT = ("Codex's memory, version 2. When a session starts, a background job picks recent past "
       "conversations that have been idle for at least 6 hours and are at most 10 days old. Phase 1 "
       "sends each one to a model, in parallel, which writes a summary of that conversation or "
       "nothing, kept in a local database. Phase 2 writes those summaries out as files and runs one "
       "consolidation agent, with no network and no approvals, which reads what changed and "
       "rewrites memory_summary.md, a file under 10,000 bytes. A new session gets "
       "that summary in its instructions, cut at 2,500 tokens; the per-conversation summaries stay "
       "on disk and the model reads one when it needs it. The model in a session writes memory only "
       "when the user asks, as a small note that the next consolidation applies.")


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The default for a new profile (version 2). Memories are off until the "
                       "user turns them on.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 34
    w = 252
    x1, x2, x3 = M, M + w + 32, M + 2 * (w + 32)
    a = node(c, x1, y, w, "person", "scroll-text", "Past conversations",
             body="Idle for 6 hours or more, at most 10 days old, not sub-agents; two per start.")
    b = node(c, x2, y, w, "llm", "sparkles", "Phase 1: per conversation",
             body="One model call each, in parallel: a summary of that conversation, or nothing.")
    d = node(c, x3, y, w, "llm", "bot", "Phase 2: consolidation",
             body="One agent, no network, no approvals; reads the diff since the last run.")
    arrow(c, [(a.right, a.y + 40), (b.x, b.y + 40)], t.muted)
    arrow(c, [(b.right, b.y + 40), (d.x, d.y + 40)], t.muted)

    y2 = max(a.bottom, b.bottom, d.bottom) + 70
    s1 = node(c, x2, y2, w, "store", "file-text", "rollout_summaries/",
              body="One file per conversation, kept on disk.")
    s2 = node(c, x3, y2, w, "store", "file-text", "memory_summary.md",
              body="The user, their preferences, pointers to past work; under 10,000 bytes.")
    # Phase 1 writes to Codex's state database; Phase 2 syncs both kinds of file
    c.text(b.x + 14, b.bottom + 20, "results kept in a local database", TINY, SANS, t.muted)
    arrow(c, [(d.cx - 40, d.bottom), (d.cx - 40, d.bottom + 38), (s1.cx, d.bottom + 38), (s1.cx, s1.y)],
          t["store"].accent)
    arrow(c, [(d.cx, d.bottom), (s2.cx, s2.y)], t["store"].accent)

    y3 = max(s1.bottom, s2.bottom) + 46
    n = node(c, x1, y3, W - 2 * M, "prompt", "layers", "A new session",
             body="The summary goes into its instructions, cut at 2,500 tokens. A summary of one past "
                  "conversation is read only when the model decides it needs it. The model writes memory "
                  "only when the user asks: a small note, applied by the next consolidation.")
    arrow(c, [(s2.cx, s2.bottom), (s2.cx, n.y)], t["prompt"].accent, label="loaded", at=0)
    arrow(c, [(s1.cx, s1.bottom), (s1.cx, n.y)], t["prompt"].accent, dashed=True, label="read on demand", at=0)
    c.text(M, a.bottom + 26, "at the start of a session,", TINY, SANS, t.muted)
    c.text(M, a.bottom + 42, "in the background", TINY, SANS, t.muted)
    source_line(c, n.bottom + 26, "openai/codex, commit 3257e1b, codex-rs/memories [C]")
    return c
