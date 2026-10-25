"""The series in one picture: one conversation, five memory systems, side by side.

Each row is from that system's notebook run: what it did with the change in July, how many LLM
calls it made to write the two sessions (the answering call not counted; for Letta, the extra
calls its agent made to edit memory inside its turns), and which of the six things the answer
needs reached the prompt in September. The numbers are the ones the system figures show.
"""

from __future__ import annotations

from ..kit import (BOLD, ITALIC, MEDIUM, SANS, Box, Canvas, W, M, bubble, footer, icon_tile, measure, wrap)
from ..kit import NEED_STYLE
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme

NAME = "series"
TITLE = "One conversation, five memories"
ALT = ("The same three sessions run through five memory systems. In March the user states a diet, "
       "an allergy and a cuisine; in July they change the diet, move, and name two guests with "
       "their own needs; in September they ask for a booking. Textual memory rewrote its profile "
       "with the old diet as 'previously' (2 LLM calls to write; all six needs in the prompt). "
       "Mem0 added the new fact and kept the old one live (2 calls; both diets in the prompt). "
       "Graphiti closed the old fact and opened the new one (36 calls; its search returned only "
       "the old diet and missed gluten and the area). Letta's agent overwrote the line in place "
       "(5 extra calls inside its turns; all six). Honcho retired the old fact and a conclusion "
       "drawn from it (6 calls; all six).")

NEEDS = ["diet", "peanuts", "shellfish", "gluten", "cuisine", "area"]
ROWS = [
    ("file-text", "Textual memory", "An LLM rewrites one text profile after each session.",
     "Rewrote the line: pescatarian now, vegetarian as “previously”.", 2, "",
     ["yes"] * 6),
    ("chart-scatter", "Mem0", "An LLM extracts short facts; it only ever adds.",
     "Added the new fact. The old one stays live beside it.", 2, "",
     ["both", "yes", "yes", "yes", "yes", "yes"]),
    ("network", "Zep / Graphiti", "Four LLM steps per message, into a graph with dates.",
     "Closed the old fact on 20 June and opened the new one.", 36, "",
     ["old", "yes", "yes", "no", "yes", "no"]),
    ("layers", "Letta", "The answering agent edits its own memory block.",
     "Overwrote the line in place. No history kept.", 5, "mid-turn",
     ["yes"] * 6),
    ("list", "Honcho", "An LLM extracts; a background reasoner derives.",
     "Retired the old fact, and a conclusion drawn from it.", 6, "",
     ["yes"] * 6),
]

SESSIONS = [
    ("March · session 1", "“Strictly vegetarian for eight years … a severe peanut allergy … "
     "Indian, usually … about 40 euros a head.”", False),
    ("July · session 2", "“Pescatarian now, not vegetarian … moved to Kreuzberg in May … Lena "
     "can't eat shellfish, and Jonas is coeliac.”", False),
    ("September · session 3", "“Book the three of us somewhere for dinner — you know what we "
     "can and can't eat.”", True),
]

# columns: system, how it writes, what it did in July, LLM calls to write, the needs
X_SYS, X_HOW, X_CHANGE, X_CALLS, X_NEEDS = M, 190, 352, 540, 642
W_HOW, W_CHANGE = 146, 172
NEED_W = (W - M - X_NEEDS) / len(NEEDS)


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The same three sessions, run through five memory systems: what "
                       "each one did when the user changed their mind in July, what writing "
                       "cost, and what reached the prompt in September.",
                       W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 22

    # the three sessions, left to right, on a line of time
    gap = 16
    bw = (W - 2 * M - 2 * gap) / 3
    bottoms = []
    for i, (when, text, target) in enumerate(SESSIONS):
        bottoms.append(bubble(c, M + i * (bw + gap), y, bw, when, text, target=target).bottom)
    y = max(bottoms) + 30

    # the table's headings; the needs' names slanted over their columns
    head_y = y + 52
    for x, label in ((X_SYS, "system"), (X_HOW, "how it writes"), (X_CHANGE, "what it did in July"),
                     (X_CALLS, "LLM calls to write")):
        c.text(x, head_y, label, TINY, BOLD, t.muted)
    for i, need in enumerate(NEEDS):
        cx = X_NEEDS + (i + 0.5) * NEED_W
        c.add(f'<g transform="translate({cx - 4:.1f} {head_y:.1f}) rotate(-40)">')
        c.text(0, 0, need, TINY, MEDIUM, t.muted)
        c.add("</g>")
    c.text(X_NEEDS, y + 4, "in the prompt in September", TINY, BOLD, t.muted)
    c.line(M, head_y + 9, W - M, head_y + 9, t.line)

    # the rows
    yy = head_y + 9
    most = max(calls for *_, calls, _, _ in ROWS)
    for icon, name, how, change, calls, calls_note, needs in ROWS:
        how_lines = wrap(how, TINY, W_HOW)
        change_lines = wrap(change, SMALL, W_CHANGE)
        h = max(58, 16 + len(how_lines) * TINY * 1.35, 16 + len(change_lines) * SMALL * 1.35) + 6
        top = yy + 8
        icon_tile(c, X_SYS, top + 2, "store", icon, 28)
        c.text(X_SYS + 36, top + 21, name, SMALL, BOLD)
        for i, line in enumerate(how_lines):
            c.text(X_HOW, top + 14 + i * TINY * 1.35, line, TINY, SANS, t.muted)
        for i, line in enumerate(change_lines):
            c.text(X_CHANGE, top + 15 + i * SMALL * 1.35, line, SMALL, SANS, t.ink)
        # calls: a bar on a common scale, and the number
        bar = max(3.0, 58 * calls / most)
        c.rect(Box(X_CALLS, top + 8, bar, 12), fill=t["llm"].accent, r=3)
        c.text(X_CALLS + bar + 6, top + 18.5, str(calls), SMALL, BOLD, t["llm"].ink)
        if calls_note:
            c.text(X_CALLS, top + 36, calls_note, TINY, ITALIC, t.muted)
        for i, state in enumerate(needs):
            cx = X_NEEDS + (i + 0.5) * NEED_W
            role, icon_name, outline = NEED_STYLE[state]
            r = t[role]
            if outline:
                c.circle(cx, top + 14, 11, fill=t.paper, stroke=r.accent, width=1.2, dash="3 2.5")
            else:
                c.circle(cx, top + 14, 11, fill=r.wash)
            c.icon(icon_name, cx - 7, top + 7, 14, r.accent, stroke=1.9)
        yy += h
        c.line(M, yy, W - M, yy, t.line, 0.8)

    # the key to the matrix
    yy += 20
    x = M
    for state, label in (("yes", "reached the prompt"), ("both", "old and new value both did"),
                         ("old", "only the old value did"), ("no", "did not")):
        role, icon_name, outline = NEED_STYLE[state]
        r = t[role]
        if outline:
            c.circle(x + 9, yy, 9, fill=t.paper, stroke=r.accent, width=1.1, dash="3 2.5")
        else:
            c.circle(x + 9, yy, 9, fill=r.wash)
        c.icon(icon_name, x + 3.5, yy - 5.5, 11, r.accent, stroke=1.9)
        x += 24 + c.text(x + 24, yy + 4.5, label, TINY, SANS, t.muted) + 18
    footer_y = yy + 22
    c.line(M, footer_y, W - M, footer_y, t.line)
    c.text(M, footer_y + 22, "From the five notebooks. LLM calls to write the two sessions; for "
           "Letta, the extra calls its agent made to edit memory.", TINY, SANS, t.muted)
    c.height = int(footer_y + 40)
    return c
