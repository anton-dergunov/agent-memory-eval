# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib==3.11.2"]
# ///
"""Draw the README's two results charts from the committed result files.

    uv run scripts/plot_results.py

writes, in docs/figures/:

- results: accuracy, and the cost of building the memory and answering;
- answering: what each answer reads and costs once the memory is built;

each as .svg, -dark.svg (the README shows the one matching the reader's GitHub
theme) and .png (for the blog). The numbers come from the result files and the
call ledger with the same functions that write docs/findings/tables.md, at full
precision, so they round exactly as the README's table does. `uv run` installs
matplotlib for this script alone; the project does not depend on it.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
from memeval.findings import costs, load, per_q  # noqa: E402
from memeval.report import ledger, wilson  # noqa: E402

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
ARMS = [arm for _heading, members in GROUPS for arm, *_ in members]

THEMES = {
    "light": {
        "surface": "#ffffff", "ink": "#1f1f1e", "ink_2": "#5f5e5a", "ink_3": "#8d8c87",
        "grid": "#e6e5e0", "accuracy": "#2a78d6", "cost": "#eb6834", "tokens": "#6250d6",
        "band": "#eef4fc",
    },
    # GitHub's dark page colour, so the picture sits on the page without a frame.
    "dark": {
        "surface": "#0d1117", "ink": "#e6edf3", "ink_2": "#9198a1", "ink_3": "#6e7681",
        "grid": "#262c36", "accuracy": "#3987e5", "cost": "#d95926", "tokens": "#9085e9",
        "band": "#132238",
    },
}

Row = tuple[float, str, str, str]


# ---- Data ----

def accuracy_and_cost() -> dict[str, tuple[float, float, float, float]]:
    """arm -> (accuracy, low, high, USD per question to build and answer), in percent."""
    results, cost = load("main"), costs("main")
    out = {}
    for arm in ARMS:
        rows = results[arm]
        n = len(rows)
        k = sum(r["judge"]["correct"] for r in rows.values())
        low, high = wilson(k, n)
        out[arm] = (100 * k / n, 100 * low, 100 * high, per_q(cost, arm, rows))
    return out


def answering() -> dict[str, tuple[float, float]]:
    """arm -> (input tokens the models read, USD) per question, once the memory is built.

    Everything after writing: the read path (searches, Honcho's dialectic call,
    Letta's agent steps) and the answer itself. Tokens are the chat models' input."""
    questions = {arm: set(rows) for arm, rows in load("main").items()}
    tokens, usd = defaultdict(float), defaultdict(float)
    for c in ledger("main"):
        arm = c.get("arm")
        if arm in ARMS and c.get("phase") in ("read", "answer") and c.get("qid") in questions[arm]:
            usd[arm] += c["usd"]
            if c["kind"] == "chat":
                tokens[arm] += c["input_tokens"]
    return {arm: (tokens[arm] / len(questions[arm]), usd[arm] / len(questions[arm])) for arm in ARMS}


# ---- Drawing ----

def layout() -> tuple[list[Row], list[tuple[float, str]]]:
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


def draw_labels(ax, c: dict, rows: list[Row], headings) -> None:
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


def draw_accuracy(ax, c: dict, data, rows: list[Row], top: float) -> None:
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


def draw_bars(ax, c: dict, values: dict[str, float], colour: str, rows: list[Row],
              ticks: list[float], tick_label, value_label) -> None:
    """Bars from zero, so a bar twice as long is twice as much, each with its value."""
    most = max(values[arm] for _y, arm, *_ in rows)
    ax.set_xlim(0, most * 1.3)
    ax.set_xticks(ticks, [tick_label(t) for t in ticks])
    ax.grid(axis="x", color=c["grid"], linewidth=1)
    ax.set_axisbelow(True)
    for y, arm, *_ in rows:
        ax.barh(y, values[arm], height=0.52, color=c[colour], edgecolor="none")
        ax.text(values[arm] + most * 0.025, y, value_label(values[arm]), ha="left", va="center",
                fontsize=9.5, color=c["ink"], fontweight="bold")


def note_under(ax, c: dict, values: dict[str, float], arm: str, rows: list[Row], text: str) -> None:
    """A short grey note under one bar's value."""
    most = max(values[a] for _y, a, *_ in rows)
    y = next(y for y, a, *_ in rows if a == arm)
    ax.text(values[arm] + most * 0.025, y - 0.36, text, ha="left", va="center", fontsize=8.5,
            color=c["ink_2"])


def note_inside(ax, c: dict, values: dict[str, float], arm: str, rows: list[Row], text: str) -> None:
    """A short note inside one long bar, in the page colour."""
    most = max(values[a] for _y, a, *_ in rows)
    y = next(y for y, a, *_ in rows if a == arm)
    ax.text(most * 0.03, y, text, ha="left", va="center", fontsize=9, color=c["surface"])


def figure(c: dict, title: str, subtitle: str, panels: list[tuple[str, str]]):
    """A titled figure with the label column and two panels; returns the axes and layout."""
    plt.rcParams.update({
        "font.family": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "svg.fonttype": "path",
        # No hinting: snapping glyphs to the pixel grid squashes small letters
        # such as "a" in the PNG. Unhinted, it matches how the SVG is drawn.
        "text.hinting": "none",
        "text.hinting_factor": 1,
    })
    rows, headings = layout()
    # Room above the first heading for a caption at the top of a panel.
    top, bottom = headings[0][0] + 0.95, rows[-1][0] - 0.6

    fig = plt.figure(figsize=(10, 6.7), facecolor=c["surface"])
    left, right = 0.035, 0.955
    # Label column, first panel, a gutter, second panel.
    grid = fig.add_gridspec(1, 4, width_ratios=[2.5, 3.0, 0.75, 2.9], left=left, right=right,
                            top=0.79, bottom=0.075, wspace=0)
    names, first, second = fig.add_subplot(grid[0]), fig.add_subplot(grid[1]), fig.add_subplot(grid[3])
    for ax in (names, first, second):
        bare(ax, c, top, bottom)
    draw_labels(names, c, rows, headings)

    # A hairline between the groups, across the whole chart.
    rule = headings[1][0] + 0.55
    rule_y = fig.transFigure.inverted().transform(names.transData.transform((0, rule)))[1]
    fig.add_artist(plt.Line2D([left, right], [rule_y, rule_y], color=c["grid"], linewidth=1))

    fig.text(left, 0.955, title, fontsize=18, fontweight="bold", color=c["ink"], ha="left", va="center")
    fig.text(left, 0.912, subtitle, fontsize=10.5, color=c["ink_2"], ha="left", va="center")
    for ax, (heading, note) in zip((first, second), panels):
        ax.text(0, 1.07, heading, transform=ax.transAxes, fontsize=12.5, fontweight="bold",
                color=c["ink"], ha="left", va="bottom")
        ax.text(0, 1.03, note, transform=ax.transAxes, fontsize=9.5, color=c["ink_2"], ha="left",
                va="bottom")
    return fig, first, second, rows, top


def dollars(t: float) -> str:
    return "$0" if t == 0 else f"${t:.2f}"


def draw_results(data, theme: str) -> plt.Figure:
    c = THEMES[theme]
    fig, acc_ax, cost_ax, rows, top = figure(
        c, "Accuracy is close. Cost is not.",
        "LongMemEval: 67 knowledge-update questions, 10 sessions of history each, "
        "every arm on gemini-3.1-flash-lite",
        [("Accuracy", "questions answered correctly, with 95% interval"),
         ("Cost to build and answer", "USD per question, building its memory included")])
    draw_accuracy(acc_ax, c, data, rows, top)
    cost = {arm: data[arm][3] for arm in ARMS}
    draw_bars(cost_ax, c, cost, "cost", rows, [0, 0.2, 0.4, 0.6], dollars, lambda v: f"${v:.3f}")
    most = max(cost, key=cost.get)
    note_under(cost_ax, c, cost, most, rows, f"{cost[most] / cost['full-context']:.0f}× full context")
    return fig


def draw_answering(data, theme: str) -> plt.Figure:
    c = THEMES[theme]
    fig, tok_ax, cost_ax, rows, _top = figure(
        c, "Pay once, or pay every question.",
        "Once the memory is built, what each answer reads and costs",
        [("Tokens read per answer", "model input: searching the memory and answering"),
         ("Cost to answer", "USD per question, memory already built")])
    tokens = {arm: data[arm][0] for arm in ARMS}
    draw_bars(tok_ax, c, tokens, "tokens", rows, [0, 10_000, 20_000],
              lambda t: "0" if t == 0 else f"{t / 1000:.0f}k", lambda v: f"{v:,.0f}")
    note_inside(tok_ax, c, tokens, "full-context", rows, "the whole history, every question")
    cost = {arm: data[arm][1] for arm in ARMS}
    draw_bars(cost_ax, c, cost, "cost", rows, [0, 0.002, 0.004, 0.006],
              lambda t: "$0" if t == 0 else f"${t:.3f}", lambda v: f"${v:.4f}")
    return fig


def save(fig_for, name: str) -> None:
    light, dark = fig_for("light"), fig_for("dark")
    light.savefig(FIGURES / f"{name}.svg", metadata={"Date": None})
    light.savefig(FIGURES / f"{name}.png", dpi=200)
    dark.savefig(FIGURES / f"{name}-dark.svg", metadata={"Date": None})
    plt.close("all")


def main() -> None:
    missing = [arm for arm in ARMS if arm not in load("main")]
    if missing:
        raise SystemExit(f"no results for {', '.join(missing)}")
    FIGURES.mkdir(parents=True, exist_ok=True)
    results, answers = accuracy_and_cost(), answering()
    save(lambda theme: draw_results(results, theme), "results")
    save(lambda theme: draw_answering(answers, theme), "answering")
    print("wrote results and answering (.svg, -dark.svg, .png) in docs/figures/")


if __name__ == "__main__":
    main()
