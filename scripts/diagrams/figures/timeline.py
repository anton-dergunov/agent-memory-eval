"""Memory papers for LLM agents, 2023 to 2026: systems, benchmarks and surveys, by the month of the first arXiv version.

The dates are the `published` field of each paper in the library (~/papers/library/llm/memory/ and
CoALA in llm/agents/), which is the date of the first arXiv version. The selection is the papers
part 2 of the series mentions.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, SANS, Box, Canvas, W, M, measure
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "timeline"
TITLE = "Memory for LLM agents, 2023 to 2026"
ALT = ("A timeline of papers from 2023 to 2026 in four rows. Systems: Generative Agents (April 2023), "
       "MemoryBank (May 2023), MemGPT (October 2023), Zep (January 2025), A-MEM (February 2025), Mem0 "
       "(April 2025), MemOS and MIRIX (July 2025), LightMem (October 2025). Learned write policies: "
       "Memory-R1 (August 2025) and Mem-α (September 2025). Benchmarks: LoCoMo (February 2024), LongMemEval "
       "(October 2024), MemoryAgentBench (July 2025), HaluMem (November 2025), EvoMemBench (May 2026), "
       "ForgetEval (June 2026). Surveys: CoALA (September 2023), Rethinking Memory (May "
       "2025), Memory in the Age of AI Agents (December 2025), Memory for Autonomous LLM Agents (March "
       "2026). The systems cluster in 2023 and 2025; the independent benchmarks that re-run them cluster "
       "in late 2025 and 2026.")

START, END = (2023, 1), (2027, 1)
GROUPS = [
    ("Systems", "store", [(2023, 4, "Generative Agents"), (2023, 5, "MemoryBank"), (2023, 10, "MemGPT"),
                          (2025, 1, "Zep"), (2025, 2, "A-MEM"), (2025, 4, "Mem0"), (2025, 7, "MemOS"),
                          (2025, 7, "MIRIX"), (2025, 10, "LightMem")]),
    ("Learned writing", "llm", [(2025, 8, "Memory-R1"), (2025, 9, "Mem-α")]),
    ("Benchmarks", "prompt", [(2024, 2, "LoCoMo"), (2024, 10, "LongMemEval"), (2025, 7, "MemoryAgentBench"),
                              (2025, 11, "HaluMem"), (2026, 5, "EvoMemBench"), (2026, 6, "ForgetEval")]),
    ("Surveys", "code", [(2023, 9, "CoALA"), (2025, 5, "Rethinking Memory"),
                         (2025, 12, "Memory in the Age of AI Agents"), (2026, 3, "Memory for Autonomous Agents")]),
]
X0 = M + 128
X1 = W - M - 10
BAND = 70
GAP = 10
PILL = TINY + 9


def _x(year: int, month: int, day: float = 0.5) -> float:
    total = (END[0] - START[0]) * 12
    k = (year - START[0]) * 12 + (month - 1) + day
    return X0 + (X1 - X0) * k / total


def _pill(c: Canvas, x: float, top: float, label: str, role: str) -> float:
    t = c.theme
    r = t[role]
    w = measure(label, TINY, SANS) + 14
    c.rect(Box(x, top, w, PILL), fill=r.wash, stroke=r.accent, r=PILL / 2, width=0.7)
    c.text(x + 7, top + PILL / 2 + TINY * 0.36, label, TINY, SANS, r.ink)
    return x + w


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Papers mentioned in this part, by the month of their first version. The "
                       "systems come in two waves; the benchmarks that re-run them come after.",
                       W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 34
    c.line(X0, y + 22, X1, y + 22, t.faint, 1.2)
    for year in (2023, 2024, 2025, 2026):
        c.text((_x(year, 1, 0) + _x(year, 12, 1)) / 2, y + 2, str(year), SMALL, BOLD, t.ink, anchor="middle")
        for month, name in ((1, "Jan"), (4, "Apr"), (7, "Jul"), (10, "Oct")):
            x = _x(year, month, 0)
            c.line(x, y + 17, x, y + 27, t.faint, 1.2 if month == 1 else 0.8)
            c.text(x + 3, y + 40, name, TINY - 2, SANS, t.faint)
    y += 56
    for name, role, events in GROUPS:
        r = t[role]
        # two rows of labels above and two below the line, each label where it has to move least
        lanes = {"a1": -1e9, "b1": -1e9, "a2": -1e9, "b2": -1e9}
        placed = []
        for year, month, label in events:
            x = _x(year, month)
            w = measure(label, TINY, SANS) + 14
            want = min(x - 8, X1 - w)
            lane = min(lanes, key=lambda k: (max(0.0, lanes[k] + 6 - want), k[1]))
            px = max(want, lanes[lane] + 6)
            lanes[lane] = px + w
            placed.append((x, px, lane, label))
        na = max([int(l[1]) for _, _, l, _ in placed if l[0] == "a"], default=0)
        nb = max([int(l[1]) for _, _, l, _ in placed if l[0] == "b"], default=0)
        up, down = 12 + na * (PILL + 6), 12 + nb * (PILL + 6)
        pad = max(0.0, (BAND - up - down) / 2)
        h = up + down + 2 * pad
        c.rect(Box(M, y, W - 2 * M, h), fill=t.surface, r=10)
        mid = y + pad + up
        c.text(M + 12, mid + 5, name, SMALL, MEDIUM, t.ink)
        c.line(X0, mid, X1, mid, t.line, 1.4)
        tops = []
        for x, px, lane, label in placed:   # the stems first, so a pill covers any stem behind it
            above = lane[0] == "a"
            level = int(lane[1])
            ptop = (mid - 7 - level * PILL - (level - 1) * 6) if above else (mid + 7 + (level - 1) * (PILL + 6))
            ymid = ptop + PILL / 2
            if px > x - 4:
                c.path(f"M {x:.1f} {mid:.1f} L {x:.1f} {ymid:.1f} L {px:.1f} {ymid:.1f}", stroke=r.accent, width=1.0)
            else:
                c.line(x, mid, x, ptop + (PILL if above else 0), r.accent, 1.0)
            tops.append(ptop)
        for (x, px, lane, label), ptop in zip(placed, tops):
            _pill(c, px, ptop, label, role)
        for x, _, _, _ in placed:
            c.circle(x, mid, 5, fill=r.accent, stroke=t.surface, width=2)
        y += h + GAP
    source_line(c, y + 8, "Dates: the first arXiv version of each paper")
    return c
