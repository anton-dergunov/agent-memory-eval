"""Mastra's Observational Memory: the Observer and the Reflector, and what the prompt held in one run.

The mechanism and thresholds are Mastra's defaults (@mastra/memory 1.41.1,
packages/memory/src/processors/observational-memory/constants.ts, and the documentation). The
two bars are from scripts/mastra/om_summary_output.txt: question 6a1eabeb with its whole
history, gemini-3.1-flash-lite, in Mastra's own token estimates.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, SANS, Box, Canvas, W, M, arrow, measure, node
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "observer-reflector"
TITLE = "Observational Memory: two agents keep the prompt small"
ALT = ("The conversation grows as raw messages in the prompt. In the background, about every 6,000 "
       "tokens, the Observer turns the newest messages into dated observations, held ready. When "
       "the raw messages pass 30,000 tokens, the prepared observations replace the messages they "
       "came from, which leave the prompt, and about 6,000 tokens of recent messages stay. When the "
       "observation log passes 40,000 tokens, the Reflector rewrites the whole log into a smaller "
       "one. Below, the answer prompt in one run on a benchmark history of about 108,000 tokens: "
       "an observation log of 2,652 tokens and 28,703 tokens of recent messages not yet observed, "
       "which held the changed fact; the answer used the old value. With the recent messages "
       "observed first, the prompt held a log of 3,154 tokens and 132 tokens of messages, and the "
       "answer used the new value.")


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Mastra's defaults. The Observer replaces old messages with dated notes; "
                       "the Reflector rewrites the notes when they grow. Nothing is searched: the "
                       "notes sit at the start of the prompt.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 34
    w = 252
    x1, x2, x3 = M, M + w + 32, M + 2 * (w + 32)
    msgs = node(c, x1, y, w, "person", "scroll-text", "Raw messages",
                body="The conversation, in the prompt as it happens.")
    obs = node(c, x2, y, w, "llm", "sparkles", "Observer",
               body="About every 6,000 tokens, in the background: the newest messages become dated "
                    "observations, held ready.")
    log = node(c, x3, y, w, "store", "file-text", "Observation log",
               body="Dated lines with priorities, at the start of the prompt.")
    arrow(c, [(msgs.right, msgs.y + 44), (obs.x, obs.y + 44)], t.muted)
    arrow(c, [(obs.right, obs.y + 44), (log.x, log.y + 44)], t["store"].accent)
    refl = node(c, x3, max(msgs.bottom, obs.bottom, log.bottom) + 40, w, "llm", "sparkles", "Reflector",
                body="When the log passes 40,000 tokens: rewrites the whole log, smaller.")
    arrow(c, [(log.cx - 30, log.bottom), (log.cx - 30, refl.y)], t["llm"].accent)
    arrow(c, [(log.cx + 30, refl.y), (log.cx + 30, log.bottom)], t["store"].accent)
    note = ("At 30,000 tokens the observed messages leave the prompt and their observations take "
            "their place; about 6,000 tokens of recent messages stay. Past 36,000 the agent waits "
            "for the Observer.")
    c.paragraph(x1, refl.y + 4, note, x2 + w - x1, TINY, SANS, t.muted)

    # the run: what the answer prompt held
    y = refl.bottom + 44
    c.text(M, y, "ONE RUN: THE ANSWER PROMPT, ON A HISTORY OF ABOUT 108,000 TOKENS", TINY, BOLD, t.muted, spacing=1.2)
    y += 16
    scale = (W - 2 * M - 230) / 32000
    rows = [("Asked as the history ended", 2652, 28703, "answer: 27:12, the old value", "stale"),
            ("Recent messages observed first", 3154, 132, "answer: 25:50, the new value", "store")]
    for label, log_tokens, raw_tokens, outcome, role in rows:
        c.text(M, y + 18, label, TINY, MEDIUM, t.ink)
        bx = M + 230
        lw_ = log_tokens * scale
        c.rect(Box(bx, y + 4, lw_, 20), fill=t["store"].accent, r=3)
        c.rect(Box(bx + lw_ + 2, y + 4, max(2, raw_tokens * scale), 20), fill=t["person"].wash,
               stroke=t["person"].accent, r=3, width=0.8)
        c.text(bx, y + 42, f"log {log_tokens:,} + messages {raw_tokens:,} tokens; {outcome}", TINY, MEDIUM,
               t[role].accent)
        y += 56
    c.rect(Box(M + 230, y + 2, 14, 12), fill=t["store"].accent, r=2)
    x = M + 250 + c.text(M + 250, y + 12, "observation log", TINY, SANS, t.muted)
    c.rect(Box(x + 18, y + 2, 14, 12), fill=t["person"].wash, stroke=t["person"].accent, r=2, width=0.8)
    c.text(x + 38, y + 12, "recent messages, not yet observed (Mastra's token estimates)", TINY, SANS, t.muted)
    source_line(c, y + 26, "Mastra @mastra/memory 1.41.1 defaults [C]; run: agent-memory-eval scripts/mastra, question 6a1eabeb")
    return c
