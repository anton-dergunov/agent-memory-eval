"""Honcho: the two read paths, side by side, with what each returned in the first server run.

The rules are Honcho 3.3.0's: get_working_representation (src/crud/representation.py) and the
dialectic agent (src/dialectic/core.py, prompts.py) at its default reasoning level. The outputs are
excerpts from scripts/replays/honcho_server_runs/run1.json.
"""

from __future__ import annotations

from ..kit import BOLD, ITALIC, MEDIUM, MONO, SANS, Box, Canvas, W, M, arrow, chip, heading, node, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "honcho-read"
TITLE = "Two ways to read the memory"
ALT = ("Left, the representation: plain code, no model call. It takes the 33 conclusions closest to "
       "the question by embedding, fills up to 100 with the newest, sorts each level by when it was "
       "said, and prints them with their times; patterns are printed without a time. In the first "
       "server run it returned the pescatarian row dated 20 July, a stale deduction about "
       "vegetarian food dated 14 March, and a stale pattern marked 'high' with no date. Right, the "
       "dialectic: an agent. Before its first call the code fetches the 25 closest explicit "
       "conclusions and the 25 closest derived ones; at the default level it may use tools for up "
       "to 5 rounds; it writes an answer. Its prompt has two rules for two values of one fact: ask "
       "the user which is correct, and the more recent one supersedes. In the first run it made one "
       "call and answered: pescatarian, the peanut allergy, no shellfish for Lena, coeliac Jonas. "
       "Either output goes to the answering prompt.")

REPR_LINES = [("## Explicit Observations", None), ("[2026-07-20 12:06:00] Anton identifies as a", None),
              ("  pescatarian as of July 2026.", None), ("## Deductive Observations", None),
              ("[2026-03-14 12:02:00] Anton is likely to order", "stale"),
              ("  vegetarian Indian food featuring paneer …", "stale"),
              ("## Inductive Observations", None), (" **Pattern** [high]: Anton has a consistent", "stale"),
              ("  preference for vegetarian cuisine …", "stale")]
CHAT = ("“Anton (You): Pescatarian, severe anaphylactic peanut allergy. Lena (Sister): No shellfish. "
        "Jonas (Partner): Coeliac …”")


def _output(c: Canvas, x: float, y: float, w: float, title: str, draw_body) -> Box:
    t = c.theme
    c.text(x, y + 14, title, TINY, BOLD, t.muted)
    h = draw_body(y + 24)
    return Box(x, y, w, h + 24)


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "On the same store: a rule that returns conclusions with their times, "
                       "or an agent that reads them and answers.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30
    half = (W - 2 * M - 30) / 2
    lx, rx = M, M + half + 30
    heading(c, lx, y, half, "REPRESENTATION")
    heading(c, rx, y, half, "DIALECTIC")
    y += 24
    left = node(c, lx, y, half, "code", "list", "A list of conclusions", api="peer.representation(search_query=q)",
                body="No model call.",
                steps=[("the conclusions closest to the question, by embedding", "≤ 33"),
                       ("then the newest, until there are 100", "≤ 67"),
                       ("each level sorted by when it was said", "by time")])
    right = node(c, rx, y, half, "llm", "bot", "An agent that answers", api="peer.chat(q)",
                 body="Honcho's dialectic, at the default level, low.",
                 steps=[("prefetch: the closest explicit conclusions", "≤ 25"),
                        ("and the closest derived ones", "≤ 25"),
                        ("tools: search conclusions or messages", "≤ 5 rounds"),
                        ("writes an answer in prose", "1 reply")])
    y = max(left.bottom, right.bottom) + 16
    # the dialectic's two rules
    c.text(rx, y + 14, "Its prompt, for two values of one fact:", TINY, BOLD, t.muted)
    b1 = chip(c, rx, y + 24, "CONTRADICTORY: “Ask the user which statement is correct”", "stale", size=TINY - 0.5)
    b2 = chip(c, rx, b1.bottom + 6, "UPDATED: “The MORE RECENT statement supersedes”", "store", size=TINY - 0.5)
    c.text(lx, y + 14, "Patterns are printed without a time.", TINY, ITALIC, t["stale"].accent)
    y = b2.bottom + 22
    heading(c, M, y, W - 2 * M, "WHAT EACH RETURNED IN THE FIRST SERVER RUN", "excerpts; red: rests on the deleted fact")
    y += 22
    ly = y
    for line, role in REPR_LINES:
        ly += 16
        c.text(lx, ly, line, TINY - 1, MONO, t[role].accent if role else t.ink)
    out_l = Box(lx, y, half, ly - y + 8)
    lines = wrap(CHAT, SMALL, half, ITALIC)
    for i, line in enumerate(lines):
        c.text(rx, y + SMALL + 4 + i * SMALL * 1.4, line, SMALL, ITALIC, t["llm"].ink)
    note = wrap("One call, no tools: it answered from the prefetch.", TINY, half, SANS)
    ny = y + SMALL + 4 + len(lines) * SMALL * 1.4 + 6
    for i, line in enumerate(note):
        c.text(rx, ny + i * TINY * 1.35, line, TINY, SANS, t.muted)
    out_r = Box(rx, y, half, ny + len(note) * TINY * 1.35 - y)
    y = max(out_l.bottom, out_r.bottom) + 24
    box = Box(M + 120, y + 18, W - 2 * M - 240, 46)
    c.rect(box, fill=t["prompt"].wash, r=10)
    c.icon("scroll-text", box.x + 12, box.y + 15, 16, t["prompt"].accent)
    c.text(box.x + 36, box.y + 28, "The answering prompt: either output, as the memory", SMALL, BOLD, t["prompt"].ink)
    arrow(c, [(lx + half / 2, out_l.bottom + 4), (lx + half / 2, box.y)], t.muted, dashed=True)
    arrow(c, [(rx + half / 2, out_r.bottom + 4), (rx + half / 2, box.y)], t.muted, dashed=True)
    source_line(c, box.bottom + 24, "Rules of Honcho 3.3.0; outputs from the first run of its server on the example")
    return c
