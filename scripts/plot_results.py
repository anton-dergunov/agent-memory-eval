# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib==3.11.2"]
# ///
"""Draw the README's results chart from the committed result files.

    uv run scripts/plot_results.py

writes docs/figures/results.svg and results-dark.svg (the README shows the one
matching the reader's GitHub theme) and results.png (for the blog). The numbers
come from the same functions that write docs/findings/tables.md, at full
precision, so they round exactly as the README's table does. `uv run` installs
matplotlib for this script alone; the project does not depend on it.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
from memeval.findings import costs, load, per_q  # noqa: E402
from memeval.report import wilson  # noqa: E402

FIGURES = REPO / "docs" / "figures"

# The README's rows, in its order, in two groups: arm, system, and the variant
# shown under the system's name.
GROUPS = [
    ("Without memory", [
        ("full-context", "Full context", ""),
        ("retrieval", "Retrieval", "BM25 over raw turns"),
    ]),
    ("Memory systems", [
        ("textual", "Textual memory", ""),
        ("mem0", "Mem0", ""),
        ("honcho-chat", "Honcho", "dialectic chat"),
        ("honcho-repr", "Honcho", "representation"),
        ("graphiti", "Graphiti", ""),
        ("letta", "Letta", ""),
        ("letta-persona", "Letta", "persona that keeps facts current"),
    ]),
]

THEMES = {
    "light": {
        "surface": "#ffffff", "ink": "#1f1f1e", "ink_2": "#5f5e5a", "ink_3": "#8d8c87",
        "grid": "#e6e5e0", "accuracy": "#2a78d6", "cost": "#eb6834", "band": "#eef4fc",
    },
    # GitHub's dark page colour, so the picture sits on the page without a frame.
    "dark": {
        "surface": "#0d1117", "ink": "#e6edf3", "ink_2": "#9198a1", "ink_3": "#6e7681",
        "grid": "#262c36", "accuracy": "#3987e5", "cost": "#d95926", "band": "#132238",
    },
}

Data = dict[str, tuple[float, float, float, float]]


def read_main_run() -> Data:
    """arm -> (accuracy, low, high, USD per question), accuracy in percent."""
    results, cost = load("main"), costs("main")
    out = {}
    for arm, rows in results.items():
        n = len(rows)
        k = sum(r["judge"]["correct"] for r in rows.values())
        low, high = wilson(k, n)
        out[arm] = (100 * k / n, 100 * low, 100 * high, per_q(cost, arm, rows))
    return out


def layout() -> tuple[list[tuple[float, str, str, str]], list[tuple[float, str]]]:
    """Each row's y (top row highest), arm, system and variant, and each group heading's y."""
    rows, headings, y = [], [], 0.0
    for heading, members in GROUPS:
        headings.append((y, heading))
        y -= 0.85
        for arm, system, variant in members:
            rows.append((y, arm, system, variant))
            y -= 1.0
        y -= 0.35
    return rows, headings


def bare(ax, c: dict, top: float, bottom: float) -> None:
    ax.set_ylim(bottom, top)
    ax.set_facecolor("none")
    for side in ax.spines.values():
        side.set_visible(False)
    ax.tick_params(left=False, labelleft=False, bottom=False, colors=c["ink_2"], labelsize=9.5)


def draw_labels(ax, c: dict, rows, headings) -> None:
    ax.set_xticks([])
    ax.set_xlim(0, 1)
    for y, heading in headings:
        ax.text(0.97, y, heading.upper(), ha="right", va="center", fontsize=8.5, color=c["ink_3"],
                fontweight="bold")
    for y, _arm, system, variant in rows:
        if not variant:
            ax.text(0.97, y, system, ha="right", va="center", fontsize=11, color=c["ink"],
                    fontweight="bold")
            continue
        ax.text(0.97, y + 0.15, system, ha="right", va="center", fontsize=11, color=c["ink"],
                fontweight="bold")
        ax.text(0.97, y - 0.21, variant, ha="right", va="center", fontsize=9.5, color=c["ink_2"])


def draw_accuracy(ax, c: dict, data: Data, rows, top: float) -> None:
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
    ax.grid(axis="x", color=c["grid"], linewidth=1)
    ax.set_axisbelow(True)
    # Full context's interval as a band the other arms are read against: reading
    # the whole history is what a memory system has to beat.
    _acc, low, high, _cost = data["full-context"]
    ax.axvspan(low, high, color=c["band"], zorder=0, linewidth=0)
    ax.text((low + high) / 2, top - 0.1, "full context's\ninterval", ha="center", va="top",
            fontsize=8, color=c["ink_3"], linespacing=1.1)
    for y, arm, _system, _variant in rows:
        acc, low, high, _cost = data[arm]
        ax.plot([low, high], [y, y], color=c["accuracy"], linewidth=2.4, solid_capstyle="round",
                alpha=0.45, zorder=2)
        ax.plot(acc, y, "o", markersize=9, color=c["accuracy"], markeredgecolor=c["surface"],
                markeredgewidth=1.8, zorder=3)
        ax.text(acc, y + 0.27, f"{acc:.0f}%", ha="center", va="bottom", fontsize=9.5, color=c["ink"],
                fontweight="bold")


def draw_cost(ax, c: dict, data: Data, rows) -> None:
    # A bar from zero, so a bar twice as long costs twice as much.
    most = max(data[row[1]][3] for row in rows)
    ax.set_xlim(0, most * 1.3)
    ticks = [0, 0.2, 0.4, 0.6]
    ax.set_xticks(ticks, ["$0" if t == 0 else f"${t:.2f}" for t in ticks])
    ax.grid(axis="x", color=c["grid"], linewidth=1)
    ax.set_axisbelow(True)
    for y, arm, _system, _variant in rows:
        cost = data[arm][3]
        ax.barh(y, cost, height=0.52, color=c["cost"], edgecolor="none")
        ax.text(cost + most * 0.025, y, f"${cost:.3f}", ha="left", va="center", fontsize=9.5,
                color=c["ink"], fontweight="bold")
    # How many times full context's cost the most expensive arm spends.
    y, arm, _system, _variant = max(rows, key=lambda row: data[row[1]][3])
    times = data[arm][3] / data["full-context"][3]
    ax.text(most * 1.025, y - 0.36, f"{times:.0f}× full context", ha="left", va="center",
            fontsize=8.5, color=c["ink_2"])


def draw(data: Data, theme: str) -> plt.Figure:
    c = THEMES[theme]
    plt.rcParams.update({
        "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "svg.fonttype": "path",
        # No hinting: snapping glyphs to the pixel grid squashes small letters
        # such as "a" in the PNG. Unhinted, it matches how the SVG is drawn.
        "text.hinting": "none",
        "text.hinting_factor": 1,
    })
    rows, headings = layout()
    # Room above the first heading for the band's caption.
    top, bottom = headings[0][0] + 0.95, rows[-1][0] - 0.6

    fig = plt.figure(figsize=(10, 6.7), facecolor=c["surface"])
    left, right = 0.035, 0.955
    # Label column, accuracy, a gutter, cost.
    grid = fig.add_gridspec(1, 4, width_ratios=[2.5, 3.0, 0.75, 2.9], left=left, right=right,
                            top=0.79, bottom=0.075, wspace=0)
    names, acc_ax, cost_ax = fig.add_subplot(grid[0]), fig.add_subplot(grid[1]), fig.add_subplot(grid[3])
    for ax in (names, acc_ax, cost_ax):
        bare(ax, c, top, bottom)

    draw_labels(names, c, rows, headings)
    draw_accuracy(acc_ax, c, data, rows, top)
    draw_cost(cost_ax, c, data, rows)

    # A hairline between the groups, across the whole chart.
    rule = headings[1][0] + 0.55
    rule_y = fig.transFigure.inverted().transform(names.transData.transform((0, rule)))[1]
    fig.add_artist(plt.Line2D([left, right], [rule_y, rule_y], color=c["grid"], linewidth=1))

    # Titles: the finding, then what each panel measures.
    fig.text(left, 0.955, "Accuracy is close. Cost is not.", fontsize=18, fontweight="bold",
             color=c["ink"], ha="left", va="center")
    fig.text(left, 0.912, "LongMemEval: 67 knowledge-update questions, 10 sessions of history each, "
             "every arm on gemini-3.1-flash-lite", fontsize=10.5, color=c["ink_2"], ha="left", va="center")
    for ax, title, note in (
        (acc_ax, "Accuracy", "questions answered correctly, with 95% interval"),
        (cost_ax, "Cost per question", "USD: building the memory, reading it, answering"),
    ):
        ax.text(0, 1.07, title, transform=ax.transAxes, fontsize=12.5, fontweight="bold", color=c["ink"],
                ha="left", va="bottom")
        ax.text(0, 1.03, note, transform=ax.transAxes, fontsize=9.5, color=c["ink_2"], ha="left",
                va="bottom")
    return fig


def main() -> None:
    data = read_main_run()
    missing = [arm for _h, members in GROUPS for arm, *_ in members if arm not in data]
    if missing:
        raise SystemExit(f"no results for {', '.join(missing)}")
    FIGURES.mkdir(parents=True, exist_ok=True)
    light, dark = draw(data, "light"), draw(data, "dark")
    light.savefig(FIGURES / "results.svg", metadata={"Date": None})
    light.savefig(FIGURES / "results.png", dpi=200)
    dark.savefig(FIGURES / "results-dark.svg", metadata={"Date": None})
    print("wrote docs/figures/results.svg, results-dark.svg and results.png")


if __name__ == "__main__":
    main()
