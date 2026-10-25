# /// script
# requires-python = ">=3.11"
# dependencies = ["fonttools[woff]==4.67.0", "uharfbuzz==0.57.0", "playwright==1.64.1"]
# ///
"""Draw the architecture diagrams that open each notebook and each part of the blog series.

    uv run scripts/draw_diagrams.py              # every figure
    uv run scripts/draw_diagrams.py mem0 letta   # some
    uv run scripts/draw_diagrams.py --copy-to DIR

writes, in docs/figures/architecture/, for each figure:

- <name>.svg and <name>-dark.svg, with the fonts embedded, so they look the same anywhere;
- <name>.png, the light one at twice the size, for places that take no SVG (Medium).

It also writes a contact sheet of every figure in both themes, and at the width of a blog
column, and prints where. `--copy-to` copies the files to another directory as well, such as
a blog's image folder.

The figures are drawn by the modules in scripts/diagrams/figures/, one per figure, with the
examples copied from the committed notebook runs. The PNGs are rendered by Chromium through
Playwright; the first run needs `uv run --with playwright==1.64.1 playwright install chromium`.
"""

from __future__ import annotations

import argparse
import html
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "figures" / "architecture"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from diagrams.figures import FIGURES  # noqa: E402
from diagrams.theme import THEMES, check  # noqa: E402


def draw(names: list[str]) -> dict[str, dict[str, Path]]:
    OUT.mkdir(parents=True, exist_ok=True)
    written = {}
    for name in names:
        figure = FIGURES[name]
        written[name] = {}
        for theme in THEMES.values():
            path = OUT / (f"{name}.svg" if theme.name == "light" else f"{name}-{theme.name}.svg")
            path.write_text(figure.draw(theme).svg(), encoding="utf-8")
            written[name][theme.name] = path
    return written


def render_pngs(written: dict[str, dict[str, Path]]) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright is not installed: no PNGs")
        return
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=2)
        for name, paths in written.items():
            svg = paths["light"].read_text(encoding="utf-8")
            page.set_content(f"<!doctype html><body style='margin:0;background:transparent'>{svg}</body>")
            page.wait_for_function("document.fonts.status === 'loaded'")
            page.locator("svg").first.screenshot(path=str(OUT / f"{name}.png"), omit_background=True)
        browser.close()


def contact_sheet(written: dict[str, dict[str, Path]]) -> Path:
    sheet = Path(tempfile.gettempdir()) / "architecture-diagrams.html"
    rows = []
    for name, paths in written.items():
        light, dark = (html.escape(paths[k].as_uri()) for k in ("light", "dark"))
        rows.append(
            f"<h2>{name}</h2><div class=row>"
            f"<div><p>light, 700 px</p><img width=700 src='{light}'></div>"
            f"<div class=dark><p>dark, 700 px</p><img width=700 src='{dark}'></div></div>"
            f"<p>light, natural size</p><img src='{light}'>")
    sheet.write_text(
        "<!doctype html><meta charset=utf-8><title>Architecture diagrams</title><style>"
        "body{font:14px system-ui;margin:24px;background:#FBFAF6;color:#22241F}"
        ".row{display:flex;gap:24px;flex-wrap:wrap}.dark{background:#161814;color:#E7E5DB;padding:0 12px 12px}"
        "</style>" + "".join(rows), encoding="utf-8")
    return sheet


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("names", nargs="*", choices=[[], *FIGURES], help="figures to draw (default: all)")
    parser.add_argument("--copy-to", type=Path, help="also copy every file written to this directory")
    parser.add_argument("--no-png", action="store_true", help="skip the PNGs")
    args = parser.parse_args()

    problems = [p for theme in THEMES.values() for p in check(theme)]
    if problems:
        sys.exit("contrast below WCAG AA:\n  " + "\n  ".join(problems))

    written = draw(args.names or list(FIGURES))
    if not args.no_png:
        render_pngs(written)
    for name, paths in written.items():
        files = [*paths.values(), OUT / f"{name}.png"]
        print(f"{name}: " + ", ".join(f.name for f in files if f.exists()))
        if args.copy_to:
            args.copy_to.mkdir(parents=True, exist_ok=True)
            for f in files:
                if f.exists():
                    shutil.copy2(f, args.copy_to / f.name)
    print(f"contact sheet: {contact_sheet(written)}")


if __name__ == "__main__":
    main()
