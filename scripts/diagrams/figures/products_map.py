"""The products on the two choices: who writes the memory, and how the read path uses it.

The placements and their sources are in the blog's _drafts/agent-memory/9-assistants.sources.md
(V the vendor's own page, C published code, R reverse engineering). As of November 2026.
"""

from __future__ import annotations

from ..kit import BOLD, ITALIC, M, MEDIUM, SANS, Box, Canvas, W, icon_tile, measure, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "products-map"
TITLE = "The products on the two choices"
ALT = ("A grid. Rows say who writes the memory: the user; the model, during its turn; a process "
       "after or between conversations; nobody. Columns say how it is read: all of it put into "
       "the prompt, a search that selects, or not documented. The user writes: CLAUDE.md files in "
       "Claude Code and saved info in Gemini are inserted. The model during its turn: ChatGPT's "
       "saved memories, Claude Code's MEMORY.md index and Gemini CLI's memory files are inserted; "
       "Claude Code's topic files, Gemini CLI's detail files and the API memory tool are read on "
       "demand, and Le Chat recalls its Memories when relevant; the Claude app's topics and Meta "
       "AI are not documented. A process writes: "
       "ChatGPT's dreaming summary, Codex's memory summary, Mastra's Observational Memory and the "
       "Claude app's earlier daily summary are inserted; Codex's rollout summaries are read on "
       "demand. Nobody writes: Claude's search over past chats, Grok's referenced chats and "
       "Gemini's Personal Intelligence search what is already there. Not documented who writes: "
       "Perplexity searches its memory store; Gemini's memory of past chats is not documented "
       "either way.")

COLUMNS = [("layers", "Put into the prompt", "all of it, every time"),
           ("search", "Searched", "a search or a tool picks part of it"),
           ("circle-dashed", "Not documented", "the vendor does not say")]
# (who writes, what it means, [insert], [select], [unknown]); an entry is (product, detail, mark)
ROWS = [
    ("The user", "writes or approves each entry",
     [("Claude Code", "CLAUDE.md", "V"), ("Gemini", "saved info", "V")],
     [],
     []),
    ("The model, during its turn", "a tool call or a file edit, mid-conversation",
     [("ChatGPT", "saved memories (2024)", "V"), ("Claude Code", "MEMORY.md index", "V"),
      ("Gemini CLI", "memory files", "C")],
     [("Claude Code", "topic files", "V"), ("Gemini CLI", "detail files", "C"),
      ("Claude API", "memory tool", "V"), ("Le Chat", "Memories", "V")],
     [("Claude app", "topics (2026)", "V"), ("Meta AI", "saved details", "V")]),
    ("A process, after or between conversations", "reads past chats, rewrites the memory",
     [("ChatGPT", "dreaming summary (2026)", "V"), ("ChatGPT", "chat-history summary (2025)", "R"),
      ("Codex", "memory_summary.md", "C"), ("Claude app", "daily summary (2025)", "V"),
      ("Mastra", "Observational Memory", "C")],
     [("Codex", "rollout summaries", "C")],
     []),
    ("Nobody", "the past chats themselves are searched",
     [],
     [("Claude", "search over past chats", "V"), ("Grok", "referenced chats", "C"),
      ("Gemini", "Personal Intelligence", "V")],
     []),
    ("Not documented", "the vendor does not say who writes",
     [],
     [("Perplexity", "memory store", "V")],
     [("Gemini app", "memory of past chats", "V")]),
]

X_ROW, W_ROW = M, 168
GAP = 10
W_CELL = (W - M - (X_ROW + W_ROW + GAP) - 2 * GAP) / 3
LINE = 19


def _entry_lines(entry) -> int:
    product, detail, mark = entry
    return len(_wrap_entry(product, detail, mark))


def _wrap_entry(product: str, detail: str, mark: str) -> list[str]:
    """The detail's lines: the first follows the product's name, the rest start at the margin."""
    room = W_CELL - 20
    first = room - measure(product + ": ", TINY, MEDIUM)
    words, lines, line = f"{detail} {mark}".split(), [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        limit = (first if not lines else room) + (14 if word == mark else 0)  # a mark may overhang
        if measure(trial, TINY, SANS) > limit and line:
            lines.append(line)
            line = word
        else:
            line = trial
    return lines + [line]


def _entry(c: Canvas, x: float, y: float, product: str, detail: str, mark: str) -> int:
    t = c.theme
    lines = _wrap_entry(product, detail, mark)
    for k, line in enumerate(lines):
        lx = x + (c.text(x, y, product + ": ", TINY, MEDIUM, t.ink) if k == 0 else 0)
        body = line[: -len(mark)].rstrip() if k == len(lines) - 1 else line
        w = c.text(lx, y + k * LINE, body, TINY, SANS, t.ink) if body else -5
        if k == len(lines) - 1:
            c.text(lx + w + 5, y + k * LINE, mark, TINY - 1, BOLD, t.muted)
    return len(lines)


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Who writes the memory, and whether all of it goes into the prompt or a "
                       "search picks part of it. One product can sit in several cells: Claude Code "
                       "loads its index and reads its topic files on demand.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30

    c.text(X_ROW, y + 12, "WHO WRITES", TINY, BOLD, t.muted, spacing=1.6)
    x0 = X_ROW + W_ROW + GAP
    c.text(x0, y - 4, "HOW IT IS READ", TINY, BOLD, t.muted, spacing=1.6)
    for i, (icon, name, meaning) in enumerate(COLUMNS):
        x = x0 + i * (W_CELL + GAP)
        icon_tile(c, x, y + 6, "prompt", icon, 24)
        c.text(x + 31, y + 18, name, SMALL, BOLD, t["prompt"].ink)
        for j, line in enumerate(wrap(meaning, TINY - 1, W_CELL - 34)):
            c.text(x + 31, y + 33 + j * 14, line, TINY - 1, SANS, t.muted)
    y += 58

    for who, meaning, *cells in ROWS:
        h = max(70, *(16 + sum(_entry_lines(e) for e in cell) * LINE + 8 for cell in cells))
        c.line(X_ROW, y, W - M, y, t.line)
        for i, line in enumerate(wrap(who, SMALL, W_ROW - 8, BOLD)):
            c.text(X_ROW, y + 22 + i * 17, line, SMALL, BOLD, t.ink)
        top = y + 22 + len(wrap(who, SMALL, W_ROW - 8, BOLD)) * 17
        for i, line in enumerate(wrap(meaning, TINY, W_ROW - 10)):
            c.text(X_ROW, top + i * TINY * 1.35, line, TINY, SANS, t.muted)
        for i, cell in enumerate(cells):
            box = Box(x0 + i * (W_CELL + GAP), y + 7, W_CELL, h - 14)
            if not cell:
                c.rect(box, fill=t.paper, stroke=t.line, r=10, dash="4 3")
                continue
            c.rect(box, fill=t["store"].wash if i < 2 else t.surface, r=10)
            ly = box.y + 8
            for product, detail, mark in cell:
                lines = _entry(c, box.x + 10, ly + TINY + 1, product, detail, mark)
                ly += lines * LINE
        y += h
    c.line(X_ROW, y, W - M, y, t.line)

    y += 24
    x = M
    for mark, meaning in (("V", "the vendor's own page"), ("C", "the vendor's published code or prompt"),
                          ("R", "reverse engineering")):
        x += c.text(x, y, mark, TINY, BOLD, t.muted) + 6
        x += c.text(x, y, meaning, TINY, SANS, t.muted) + 22
    source_line(c, y + 16, "Placements and sources: part 9 of the series, as of November 2026")
    return c
