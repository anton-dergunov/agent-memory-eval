"""The map of part 2: the systems run in this series on the two choices, without the products.

The same layout as `map`; the products are placed in part 9's own map (`products_map`).
"""

from __future__ import annotations

from ..kit import Canvas
from ..theme import Theme
from .map import draw_map

NAME = "map-systems"
TITLE = "The systems of this series on the two choices"
ALT = ("The five memory systems of this series and the two baselines, on two axes: who writes the "
       "memory (nobody, a pipeline, the answering agent, a background process) and whether the read "
       "path inserts everything or selects. Nobody writes: full context inserts the whole history; "
       "plain retrieval selects with BM25 over the raw turns. A pipeline writes: Mem0 and Zep/Graphiti "
       "select. The answering agent writes: Letta inserts its core memory blocks, and the agent "
       "searches its log of past messages. A background process writes: textual memory inserts one profile; Honcho "
       "selects among its conclusions.")

ROWS = [
    ("Nobody", "the raw history is the memory",
     ([("scroll-text", "Full context", "the whole history")], []),
     ([("search", "Plain retrieval", "BM25 over raw turns")], [])),
    ("A pipeline", "extracts after each message or session",
     ([], []),
     ([("chart-scatter", "Mem0", "facts in a vector store"),
       ("network", "Zep / Graphiti", "dated facts in a graph")], [])),
    ("The answering agent", "edits memory with tool calls, mid-turn",
     ([("layers", "Letta", "core memory blocks")], []),
     ([], ["Letta's log of past messages, which the agent searches"])),
    ("A background process", "rewrites or reasons between conversations",
     ([("file-text", "Textual memory", "one profile, rewritten")], []),
     ([("list", "Honcho", "conclusions at levels")], [])),
]


def draw(theme: Theme) -> Canvas:
    return draw_map(theme, TITLE, ALT, ROWS, "In italics: another part of the same system")
