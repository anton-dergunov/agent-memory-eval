"""Draw the README's results chart from the generated tables.

    python3 scripts/plot_results.py       # writes docs/figures/results.svg

Reads the main-run table in docs/findings/tables.md, the same numbers the
README's table shows, so the two cannot drift apart: after
`python -m memeval.findings`, run this again. Plain SVG from the standard
library, so it needs nothing installed.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TABLES = REPO / "docs" / "findings" / "tables.md"
OUT = REPO / "docs" / "figures" / "results.svg"

# The README's rows, in its order: arm, system, variant, and whether it is a
# first run that fed the conversation in a way the system was not built for.
ROWS = [
    ("full-context", "Full context", "", False),
    ("retrieval", "Retrieval", "BM25 over raw turns", False),
    ("textual", "Textual memory", "", False),
    ("mem0", "Mem0", "", False),
    ("honcho-chat", "Honcho", "dialectic chat", False),
    ("honcho-repr", "Honcho", "representation", False),
    ("graphiti-chunk", "Graphiti", "sessions cut into 8,000-character episodes", True),
    ("graphiti", "Graphiti", "one episode per message", False),
    ("letta-batch", "Letta", "each session in one request", True),
    ("letta", "Letta", "one agent step per user message", False),
    ("letta-persona", "Letta", "the same, with a persona that keeps facts current", False),
]

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
SERIES = "#2a78d6"

LABELS = 300  # the label column
ACC_X, ACC_W = LABELS + 16, 270
COST_X, COST_W = ACC_X + ACC_W + 64, 170
WIDTH = COST_X + COST_W + 28
TOP = 92  # first row's centre
ROW = 38
COST_MIN, COST_MAX = 0.001, 1.0


def read_main_table() -> dict[str, tuple[float, float, float, float]]:
    """arm -> (accuracy, low, high, USD per question), from the first table."""
    text = TABLES.read_text()
    section = text.split("## Accuracy, cost and time (main)", 1)[1].split("\n## ", 1)[0]
    out = {}
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 5 or not cells[2].endswith("%"):
            continue
        arm, _n, acc, interval, cost = cells[:5]
        low, high = re.fullmatch(r"(\d+)%–(\d+)%", interval).groups()
        out[arm] = (float(acc[:-1]), float(low), float(high), float(cost))
    return out


def acc_x(percent: float) -> float:
    return ACC_X + ACC_W * percent / 100


def cost_x(usd: float) -> float:
    span = math.log10(COST_MAX) - math.log10(COST_MIN)
    return COST_X + COST_W * (math.log10(usd) - math.log10(COST_MIN)) / span


def text(x: float, y: float, s: str, *, size: int = 13, fill: str = INK, anchor: str = "start",
         weight: int = 400) -> str:
    s = s.replace("&", "&amp;").replace("<", "&lt;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}">{s}</text>')


def dot(x: float, y: float, hollow: bool) -> str:
    # A 2px ring in the surface colour lifts the dot off its interval line.
    if hollow:
        return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{SURFACE}"/>'
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="{SURFACE}" stroke="{SERIES}" stroke-width="2"/>')
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="{SERIES}" stroke="{SURFACE}" stroke-width="2"/>'


def draw(data: dict[str, tuple[float, float, float, float]]) -> str:
    bottom = TOP + ROW * (len(ROWS) - 1) + ROW / 2
    height = bottom + 34
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height:.0f}" '
        f'viewBox="0 0 {WIDTH} {height:.0f}" font-family="-apple-system, BlinkMacSystemFont, '
        f"'Segoe UI', Helvetica, Arial, sans-serif\" role=\"img\" "
        f'aria-label="Accuracy with 95% intervals and cost per question for each arm of the LongMemEval experiment">',
        f'<rect width="100%" height="100%" fill="{SURFACE}"/>',
        text(ACC_X, 24, "Accuracy, with 95% interval", weight=600),
        text(COST_X, 24, "Cost per question (log scale)", weight=600),
    ]
    # The key for the one secondary encoding.
    parts += [dot(16 + 6, 50, True),
              text(16 + 18, 54.5, "first run: the conversation was not fed the way the system was built for",
                   size=12, fill=INK_2)]

    axis_top = TOP - ROW / 2
    for percent in (0, 25, 50, 75, 100):
        x = acc_x(percent)
        parts.append(f'<line x1="{x:.1f}" y1="{axis_top:.1f}" x2="{x:.1f}" y2="{bottom:.1f}" stroke="{GRID}"/>')
        parts.append(text(x, bottom + 18, f"{percent}%", size=12, fill=INK_2, anchor="middle"))
    for usd, label in ((0.001, "$0.001"), (0.01, "$0.01"), (0.1, "$0.10"), (1.0, "$1")):
        x = cost_x(usd)
        parts.append(f'<line x1="{x:.1f}" y1="{axis_top:.1f}" x2="{x:.1f}" y2="{bottom:.1f}" stroke="{GRID}"/>')
        parts.append(text(x, bottom + 18, label, size=12, fill=INK_2, anchor="middle"))

    for i, (arm, system, variant, first) in enumerate(ROWS):
        acc, low, high, cost = data[arm]
        y = TOP + ROW * i
        if variant:
            parts.append(text(LABELS, y - 2, system, anchor="end"))
            parts.append(text(LABELS, y + 13, variant, size=11.5, fill=INK_2, anchor="end"))
        else:
            parts.append(text(LABELS, y + 4.5, system, anchor="end"))
        parts.append(f'<line x1="{acc_x(low):.1f}" y1="{y:.1f}" x2="{acc_x(high):.1f}" y2="{y:.1f}" '
                     f'stroke="{SERIES}" stroke-width="2" stroke-linecap="round"/>')
        parts.append(dot(acc_x(acc), y, first))
        parts.append(dot(cost_x(cost), y, first))

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> None:
    data = read_main_table()
    missing = [arm for arm, *_ in ROWS if arm not in data]
    if missing:
        raise SystemExit(f"not in {TABLES.relative_to(REPO)}: {', '.join(missing)}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(draw(data))
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
