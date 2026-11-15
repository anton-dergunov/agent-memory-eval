"""Honcho: when a dream runs, and what its two agents did, round by round.

The trigger is DREAM settings and check_and_schedule_dream in Honcho 3.3.0. The rounds are dream 2
of the first real-server run of the series' example (scripts/replays/honcho_server_runs/run1.json):
each round's tool call, what it returned, and the round's input tokens.
"""

from __future__ import annotations

from ..kit import BOLD, ITALIC, MEDIUM, MONO, SANS, Box, Canvas, W, M, chip, heading, icon_tile, measure, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "honcho-dream"
TITLE = "Inside a dream"
ALT = ("Top: a dream starts when a peer has at least 50 new explicit conclusions, at least 8 hours "
       "after the last dream, and then 60 minutes pass with no new messages; or when an application "
       "schedules one. Below, dream 2 of the first server run. The deduction agent, at most 12 "
       "rounds: round 1 asks for the 20 newest conclusions and gets the whole store, 19 rows; round "
       "2 writes two deductions, the update and 'resides in Kreuzberg'; round 3 deletes one row, "
       "the vegetarian fact; round 4 rewrites the peer card with 'Diet: Pescatarian'; round 5 "
       "answers DONE. Its rounds read 2,551 to 4,069 tokens. The induction agent, at most 10 "
       "rounds: round 1 asks for the 20 newest; round 2 writes two patterns, one of which is "
       "rejected because its ids do not resolve; round 3 sends that pattern again with correct "
       "ids; round 4 answers DONE.")

GATES = ["≥ 50 new explicit conclusions", "≥ 8 hours since the last dream", "then 60 minutes with no new message"]
LANES = [
    ("Deduction agent", "at most 12 rounds", ["get_recent_observations", "search_memory", "search_messages",
                                             "create_observations_deductive", "delete_observations", "update_peer_card"], [
        ("get_recent_observations", "limit 20: got the whole store, 19 rows, old and new diet", 2551, None),
        ("create_observations_deductive", "the update, “transitioned … to a pescatarian diet in June 2026”, and “resides in … Kreuzberg”", 3727, "store"),
        ("delete_observations", "one row: the vegetarian fact", 3969, "stale"),
        ("update_peer_card", "“Diet: Vegetarian” becomes “Diet: Pescatarian”; Kreuzberg added", 4005, None),
        ("DONE", "", 4069, None),
    ]),
    ("Induction agent", "at most 10 rounds", ["get_recent_observations", "search_memory", "search_messages",
                                             "create_observations_inductive"], [
        ("get_recent_observations", "limit 20: the 20 newest rows, the old pattern among them", 1028, None),
        ("create_observations_inductive", "two patterns: a new one on the diet, built on the old pattern; the other rejected, its ids did not resolve", 2362, "stale"),
        ("create_observations_inductive", "the rejected pattern again, with its ids fixed", 2690, None),
        ("DONE", "", 2861, None),
    ]),
]


def split_name(name, size, width):
    """A tool name on as many lines as it needs, broken after underscores."""
    lines, current = [], ""
    for part in name.replace("_", "_ ").split(" "):
        if current and measure(current + part, size, MONO) > width:
            lines.append(current)
            current = part
        else:
            current += part
    return lines + [current]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Two agents run one after the other. Each sees only what its tools "
                       "return, and stops when it answers DONE.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30
    heading(c, M, y, W - 2 * M, "WHEN A DREAM RUNS")
    y += 22
    x = M
    for i, gate in enumerate(GATES):
        box = chip(c, x, y, gate, "code", icon="check", size=SMALL)
        x = box.right + 8
        if i < len(GATES) - 1:
            x += 4 + c.text(x, y + 16, "and", TINY, ITALIC, t.muted) + 8
    y += 40
    box = chip(c, M, y, "or: scheduled by the application, which skips the first two", "code",
               icon="history", size=SMALL, outline=True)
    c.text(box.right + 12, y + 16, "(as in this post's runs and in the experiment)", TINY, ITALIC, t.muted)
    y += 52
    heading(c, M, y, W - 2 * M, "DREAM 2 OF THE FIRST SERVER RUN", "each round: the tool it called, what came back, tokens read")
    y += 24
    cols = 5
    gap = 10
    cw = (W - 2 * M - gap * (cols - 1)) / cols
    for name, limit, tools, rounds in LANES:
        icon_tile(c, M, y, "llm", "sparkles", 24)
        c.text(M + 32, y + 17, name, SMALL, BOLD, t["llm"].ink)
        c.text(M + 32 + 140, y + 17, limit, TINY, SANS, t.muted)
        y += 34
        tool_line = "tools: " + ", ".join(tools)
        for i, line in enumerate(wrap(tool_line, TINY - 0.5, W - 2 * M, MONO)):
            c.text(M, y + i * 15, line, TINY - 0.5, MONO, t.muted)
        y += 15 * len(wrap(tool_line, TINY - 0.5, W - 2 * M, MONO)) + 8
        heights = []
        layouts = []
        for tool, result, tokens, role in rounds:
            tool_lines = split_name(tool, TINY - 1, cw - 16)
            res_lines = wrap(result, TINY, cw - 16) if result else []
            h = 40 + len(tool_lines) * 14 + len(res_lines) * TINY * 1.35 + 30
            heights.append(h)
            layouts.append((tool_lines, res_lines))
        h = max(heights)
        for i, ((tool, result, tokens, role), (tool_lines, res_lines)) in enumerate(zip(rounds, layouts)):
            bx = M + i * (cw + gap)
            box = Box(bx, y, cw, h)
            if role:
                c.rect(box, fill=t[role].wash, stroke=t[role].accent, r=9, width=1.2)
            else:
                c.rect(box, fill=t.card, stroke=t.line, r=9)
            c.circle(bx + 16, y + 15, 9, fill=t["llm"].wash)
            c.text(bx + 16, y + 19.5, str(i + 1), TINY, BOLD, t["llm"].ink, anchor="middle")
            for j, line in enumerate(tool_lines):
                c.text(bx + 8, y + 40 + j * 14, line, TINY - 1, MONO, t["llm"].accent)
            ry = y + 40 + len(tool_lines) * 14 - 2
            ink = t[role].ink if role else t.ink
            for j, line in enumerate(res_lines):
                c.text(bx + 8, ry + TINY + j * TINY * 1.35, line, TINY, SANS, ink)
            c.text(bx + cw - 8, y + h - 9, f"{tokens:,} tokens in", TINY - 1, MEDIUM, t.muted, anchor="end")
            if i < len(rounds) - 1:
                c.path(f"M{bx + cw + 1} {y + 15} l{gap - 3} 0", stroke=t.faint, width=1.2)
        y += h + 26
    used = c.paragraph(M, y - 8, "Each round sends the agent's instructions and tool descriptions again, plus "
                       "every tool result so far: that is why later rounds read more. No round reads "
                       "the whole store unless the store is small, as here.", W - 2 * M, TINY, SANS, t.muted)
    source_line(c, y + used + 4, "From the first run of a Honcho 3.3.0 server on the example")
    return c
