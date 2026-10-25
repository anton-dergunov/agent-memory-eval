"""A small kit for drawing the architecture diagrams as self-contained SVG.

Text is measured with the real fonts (HarfBuzz shaping, so kerning is counted), which lets
boxes fit their text exactly. The fonts are subset to the characters a figure uses and
embedded in it, so the SVG looks the same in a notebook, on the blog, on GitHub and in the
PNG rendered from it.

Everything is placed on explicit coordinates. A figure module draws top to bottom and uses
the boxes each primitive returns to attach arrows.
"""

from __future__ import annotations

import base64
import hashlib
import io
import re
from collections import defaultdict
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from xml.sax.saxutils import escape

import uharfbuzz as hb
from fontTools import subset
from fontTools.ttLib import TTFont

from .theme import BODY, HEAD, SMALL, SUBTITLE, TINY, TITLE, Theme

HERE = Path(__file__).parent

# ---- Fonts ----

FACES = {
    ("sans", 400, False): "IBMPlexSans-Regular.woff2",
    ("sans", 400, True): "IBMPlexSans-Italic.woff2",
    ("sans", 500, False): "IBMPlexSans-Medium.woff2",
    ("sans", 600, False): "IBMPlexSans-SemiBold.woff2",
    ("mono", 400, False): "IBMPlexMono-Regular.woff2",
    ("mono", 500, False): "IBMPlexMono-Medium.woff2",
}
# Names of our own, so a copy of Plex installed on the reader's machine is never used instead.
FAMILY = {"sans": "Diagram Plex Sans", "mono": "Diagram Plex Mono"}

Face = tuple[str, int, bool]
SANS: Face = ("sans", 400, False)
ITALIC: Face = ("sans", 400, True)
MEDIUM: Face = ("sans", 500, False)
BOLD: Face = ("sans", 600, False)
MONO: Face = ("mono", 400, False)


@cache
def _font(face: Face) -> tuple[hb.Font, int]:
    font = TTFont(HERE / "fonts" / FACES[face])
    font.flavor = None   # HarfBuzz reads plain sfnt, not woff2
    ttf = io.BytesIO()
    font.save(ttf)
    hb_face = hb.Face(ttf.getvalue())
    return hb.Font(hb_face), hb_face.upem


@cache
def measure(text: str, size: float, face: Face = SANS, spacing: float = 0.0) -> float:
    """The advance width of one line of text, in px, as a browser will lay it out."""
    font, upem = _font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True})
    return sum(p.x_advance for p in buf.glyph_positions) * size / upem + spacing * len(text)


def wrap(text: str, size: float, width: float, face: Face = SANS) -> list[str]:
    """Greedy word wrap to `width`. An explicit newline always breaks."""
    lines = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split(" "):
            trial = f"{line} {word}" if line else word
            if line and measure(trial, size, face) > width:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
    return lines


def _embedded_font(face: Face, chars: set[str]) -> str:
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["kern", "liga", "calt"]
    options.name_IDs = []
    options.notdef_outline = True
    font = TTFont(HERE / "fonts" / FACES[face])
    subsetter = subset.Subsetter(options)
    subsetter.populate(text="".join(sorted(chars)) + " ")
    subsetter.subset(font)
    out = io.BytesIO()
    font.flavor = "woff2"
    font.save(out)
    data = base64.b64encode(out.getvalue()).decode()
    family, weight, italic = face
    return (f"@font-face{{font-family:'{FAMILY[family]}';font-weight:{weight};"
            f"font-style:{'italic' if italic else 'normal'};"
            f"src:url(data:font/woff2;base64,{data}) format('woff2');}}")


# ---- Icons (Lucide, ISC licence: icons/LICENSE) ----

@cache
def _icon_body(name: str) -> str:
    svg = (HERE / "icons" / f"{name}.svg").read_text()
    body = svg[svg.index(">", svg.index("<svg")) + 1: svg.rindex("</svg>")]
    return re.sub(r"\s+", " ", body).strip()


# ---- Geometry ----

@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2


def _attr(**attrs) -> str:
    out = []
    for key, value in attrs.items():
        if value is None:
            continue
        if isinstance(value, float):
            value = f"{value:.2f}".rstrip("0").rstrip(".")
        out.append(f'{key.rstrip("_").replace("_", "-")}="{escape(str(value), {chr(34): "&quot;"})}"')
    return " ".join(out)


# ---- The canvas ----

class Canvas:
    def __init__(self, width: int, theme: Theme, title: str, desc: str):
        self.width, self.height = width, 0
        self.theme = theme
        self.title, self.desc = title, desc
        self.parts: list[str] = []
        self.chars: dict[Face, set[str]] = defaultdict(set)

    def add(self, svg: str) -> None:
        self.parts.append(svg)

    def text(self, x: float, y: float, s: str, size: float = BODY, face: Face = SANS,
             fill: str | None = None, anchor: str = "start", spacing: float = 0.0) -> float:
        """One line of text with its baseline at y. Returns its width."""
        self.chars[face].update(s)
        family, weight, italic = face
        self.add(f"<text {_attr(x=float(x), y=float(y), font_family=FAMILY[family], font_size=size, font_weight=weight, font_style='italic' if italic else None, fill=fill or self.theme.ink, text_anchor=None if anchor == 'start' else anchor, letter_spacing=spacing or None)}>{escape(s)}</text>")
        return measure(s, size, face, spacing)

    def runs(self, x: float, y: float, runs: list[tuple[str, Face, str | None]], size: float = BODY) -> float:
        """Text on one line in several faces or colours, each run placed by measurement."""
        start = x
        for s, face, fill in runs:
            # a monospace run is drawn slightly smaller, so it does not look louder than the text
            run_size = size * 0.93 if face[0] == "mono" else size
            x += self.text(x, y, s, run_size, face, fill)
        return x - start

    def paragraph(self, x: float, y: float, s: str, width: float, size: float = BODY,
                  face: Face = SANS, fill: str | None = None, leading: float = 1.38) -> float:
        """Wrapped text whose first baseline is at y + size. Returns the height used."""
        lines = wrap(s, size, width, face)
        for i, line in enumerate(lines):
            self.text(x, y + size + i * size * leading, line, size, face, fill)
        return len(lines) * size * leading

    def rect(self, box: Box, fill: str | None = None, stroke: str | None = None, r: float = 10,
             width: float = 1.0, dash: str | None = None, opacity: float | None = None) -> None:
        self.add(f"<rect {_attr(x=float(box.x), y=float(box.y), width=float(box.w), height=float(box.h), rx=float(r), fill=fill or 'none', stroke=stroke, stroke_width=width if stroke else None, stroke_dasharray=dash, opacity=opacity)}/>")

    def line(self, x1, y1, x2, y2, stroke, width=1.0, dash=None, cap="round") -> None:
        self.add(f"<line {_attr(x1=float(x1), y1=float(y1), x2=float(x2), y2=float(y2), stroke=stroke, stroke_width=width, stroke_dasharray=dash, stroke_linecap=cap)}/>")

    def circle(self, cx, cy, r, fill=None, stroke=None, width=1.0, dash=None) -> None:
        self.add(f"<circle {_attr(cx=float(cx), cy=float(cy), r=float(r), fill=fill or 'none', stroke=stroke, stroke_width=width if stroke else None, stroke_dasharray=dash)}/>")

    def path(self, d: str, fill=None, stroke=None, width=1.0, dash=None) -> None:
        self.add(f"<path {_attr(d=d, fill=fill or 'none', stroke=stroke, stroke_width=width if stroke else None, stroke_dasharray=dash, stroke_linecap='round', stroke_linejoin='round')}/>")

    def icon(self, name: str, x: float, y: float, size: float, colour: str, stroke: float = 1.6) -> None:
        """A Lucide icon with its top-left corner at (x, y), `stroke` px wide at this size."""
        scale = size / 24
        self.add(f'<g transform="translate({x:.2f} {y:.2f}) scale({scale:.4f})" fill="none" '
                 f'stroke="{colour}" stroke-width="{stroke / scale:.2f}" stroke-linecap="round" '
                 f'stroke-linejoin="round">{_icon_body(name)}</g>')

    def svg(self) -> str:
        fonts = "".join(_embedded_font(face, chars) for face, chars in sorted(self.chars.items()))
        w, h = self.width, self.height
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
                f'viewBox="0 0 {w} {h}" role="img" aria-labelledby="t d" text-rendering="geometricPrecision">'
                f'<title id="t">{escape(self.title)}</title><desc id="d">{escape(self.desc)}</desc>'
                f"<style>{fonts}</style>"
                f'<rect width="{w}" height="{h}" rx="14" fill="{self.theme.paper}" stroke="{self.theme.line}"/>'
                + "".join(self.parts) + "</svg>\n")


# ---- Primitives ----

def icon_tile(c: Canvas, x: float, y: float, role: str, icon: str, size: float = 30) -> Box:
    """A rounded square in the role's wash with the role's icon: the mark of a step's kind."""
    r = c.theme[role]
    box = Box(x, y, size, size)
    c.rect(box, fill=r.wash, r=size * 0.27)
    inner = size * 0.6
    c.icon(icon, x + (size - inner) / 2, y + (size - inner) / 2, inner, r.accent, stroke=1.7)
    return box


def chip(c: Canvas, x: float, y: float, text: str, role: str | None = None, icon: str | None = None,
         size: float = TINY, face: Face = MEDIUM, outline: bool = False, anchor: str = "start") -> Box:
    """A small pill. Filled with the role's wash, or only outlined."""
    t = c.theme
    accent = t[role].accent if role else t.muted
    fill = t[role].wash if role else t.surface
    ink = t[role].ink if role else t.muted
    h = size + 10
    ic = size + 1 if icon else 0
    w = measure(text, size, face) + 16 + (ic + 4 if icon else 0)
    if anchor == "end":
        x -= w
    elif anchor == "middle":
        x -= w / 2
    box = Box(x, y, w, h)
    if outline:
        c.rect(box, fill=t.paper, stroke=accent, r=h / 2, dash="3 2.5")
    else:
        c.rect(box, fill=fill, r=h / 2)
    tx = x + 8
    if icon:
        c.icon(icon, tx, y + (h - ic) / 2, ic, accent, stroke=1.6)
        tx += ic + 4
    c.text(tx, y + h / 2 + size * 0.36, text, size, face, accent if outline else ink)
    return box


def chips(c: Canvas, x: float, y: float, specs: list[dict], gap: float = 6, width: float | None = None) -> float:
    """A row of chips, wrapping to the next row past `width`. Returns the height used."""
    cx, cy, h = x, y, 0.0
    for spec in specs:
        size = spec.get("size", TINY)
        w = measure(spec["text"], size, spec.get("face", MEDIUM)) + 16 + (size + 5 if spec.get("icon") else 0)
        if width and cx > x and cx + w > x + width:
            cx, cy = x, cy + h + gap
        box = chip(c, cx, cy, **spec)
        cx, h = box.right + gap, max(h, box.h)
    return cy + h - y


def node(c: Canvas, x: float, y: float, w: float, role: str, icon: str, title: str,
         body: str | None = None, api: str | None = None, tags: list[dict] | None = None,
         dashed: bool = False, pad: float = 14) -> Box:
    """A step: icon tile and title, an optional API name, a description, then chips."""
    t = c.theme
    inner = w - 2 * pad
    # lay the content out once to know the height, then draw the card under it
    title_lines = wrap(title, HEAD, inner - 40, BOLD)
    body_lines = wrap(body, SMALL, inner) if body else []
    h = pad + max(30, len(title_lines) * HEAD * 1.25 + (16 if api else 0)) + 8
    h += len(body_lines) * SMALL * 1.4 + (6 if body_lines else 0)
    tag_h = _chips_height(tags or [], inner)
    h += tag_h + (8 if tags else 0) + pad - 8
    box = Box(x, y, w, h)
    c.rect(box, fill=t.paper if dashed else t.card, stroke=t[role].accent if dashed else t.line,
           r=12, dash="5 4" if dashed else None, width=1.2 if dashed else 1.0)
    icon_tile(c, x + pad, y + pad, role, icon)
    ty = y + pad + HEAD * 0.95 + (2 if len(title_lines) == 1 and not api else 0)
    if len(title_lines) == 1 and not api:
        ty = y + pad + 15 + HEAD * 0.36
    for i, line in enumerate(title_lines):
        c.text(x + pad + 40, ty + i * HEAD * 1.25, line, HEAD, BOLD)
    if api:
        c.text(x + pad + 40, ty + len(title_lines) * HEAD * 1.25 - 2, api, SMALL * 0.95, MONO, t[role].accent)
    by = y + pad + max(30, len(title_lines) * HEAD * 1.25 + (16 if api else 0)) + 8
    for i, line in enumerate(body_lines):
        c.text(x + pad, by + SMALL + i * SMALL * 1.4, line, SMALL, SANS, t.muted)
    if tags:
        chips(c, x + pad, box.bottom - pad - tag_h, tags, width=inner)
    return box


def _chips_height(specs: list[dict], width: float, gap: float = 6) -> float:
    if not specs:
        return 0
    cx, rows = 0.0, 1
    for spec in specs:
        size = spec.get("size", TINY)
        w = measure(spec["text"], size, spec.get("face", MEDIUM)) + 16 + (size + 5 if spec.get("icon") else 0)
        if cx and cx + w > width:
            cx, rows = 0, rows + 1
        cx += w + gap
    return rows * (TINY + 10) + (rows - 1) * gap


def bubble(c: Canvas, x: float, y: float, w: float, when: str, text: str, side: str = "left") -> Box:
    """What the user said: a speech bubble with the date above it."""
    t = c.theme
    r = t["person"]
    c.icon("user", x, y, 15, r.accent, stroke=1.7)
    c.text(x + 20, y + 12, when, TINY, MEDIUM, r.accent)
    top = y + 22
    lines = wrap(text, SMALL, w - 24, ITALIC)
    h = len(lines) * SMALL * 1.4 + 18
    box = Box(x, top, w, h)
    # the tail points up at the person icon
    tail = x + 8
    c.path(f"M{tail} {top + 1} L{tail + 3} {top - 6} L{tail + 13} {top + 1} Z", fill=r.wash)
    c.rect(box, fill=r.wash, r=12)
    for i, line in enumerate(lines):
        c.text(x + 12, top + 9 + SMALL + i * SMALL * 1.4, line, SMALL, ITALIC, r.ink)
    return Box(x, y, w, box.bottom - y)


def arrow(c: Canvas, points: list[tuple[float, float]], colour: str, dashed: bool = False,
          label: str | None = None, at: int = 0, label_face: Face = MEDIUM, offset: tuple[float, float] = (0, 0),
          radius: float = 10, width: float = 1.5, head: bool = True, above: bool = True) -> None:
    """A polyline through `points` with rounded corners and an arrowhead at the end.

    `label` goes on segment `at`: just above it when the segment is horizontal and `above`,
    otherwise as a pill sitting on the line. `offset` nudges it.
    """
    (x0, y0), *rest = points
    # stop the line short of the tip so the arrowhead's point lands exactly on the target
    if head:
        (xa, ya), (xb, yb) = points[-2], points[-1]
        length = max(1e-6, ((xb - xa) ** 2 + (yb - ya) ** 2) ** 0.5)
        ux, uy = (xb - xa) / length, (yb - ya) / length
        tip = (xb, yb)
        points = points[:-1] + [(xb - ux * 6, yb - uy * 6)]
    d = f"M{x0:.1f} {y0:.1f}"
    for i in range(1, len(points) - 1):
        (px, py), (qx, qy), (nx, ny) = points[i - 1], points[i], points[i + 1]
        r_in = min(radius, abs(qx - px) / 2 + abs(qy - py) / 2)
        r_out = min(radius, abs(nx - qx) / 2 + abs(ny - qy) / 2)
        r = min(r_in, r_out)
        ax, ay = qx - _sign(qx - px) * r, qy - _sign(qy - py) * r
        bx, by = qx + _sign(nx - qx) * r, qy + _sign(ny - qy) * r
        d += f" L{ax:.1f} {ay:.1f} Q{qx:.1f} {qy:.1f} {bx:.1f} {by:.1f}"
    d += f" L{points[-1][0]:.1f} {points[-1][1]:.1f}"
    c.path(d, stroke=colour, width=width, dash="5 4" if dashed else None)
    if head:
        _head(c, tip, (ux, uy), colour)
    if label:
        (sx, sy), (ex, ey) = points[at], points[at + 1]
        mx, my = (sx + ex) / 2 + offset[0], (sy + ey) / 2 + offset[1]
        if above and abs(ey - sy) < 1:
            lines = label.split("\n")
            for i, line in enumerate(reversed(lines)):
                c.text(mx, my - 6 - i * TINY * 1.25, line, TINY, label_face, colour, anchor="middle")
        else:
            label_pill(c, mx, my, label, colour, label_face)


def _sign(v: float) -> float:
    return (v > 0) - (v < 0)


def _head(c: Canvas, tip, direction, colour, size: float = 8) -> None:
    (tx, ty), (ux, uy) = tip, direction
    bx, by = tx - ux * size, ty - uy * size
    px, py = -uy * size * 0.55, ux * size * 0.55
    c.path(f"M{tx:.1f} {ty:.1f} L{bx + px:.1f} {by + py:.1f} L{bx - px:.1f} {by - py:.1f} Z", fill=colour)


def label_pill(c: Canvas, cx: float, cy: float, text: str, colour: str, face: Face = MEDIUM,
               size: float = TINY) -> Box:
    """A label that sits on a line, masking it, in the line's colour."""
    lines = text.split("\n")
    w = max(measure(line, size, face) for line in lines) + 12
    h = len(lines) * size * 1.3 + 6
    box = Box(cx - w / 2, cy - h / 2, w, h)
    c.rect(box, fill=c.theme.paper, r=6)
    for i, line in enumerate(lines):
        c.text(cx, box.y + 3 + size * 1.02 + i * size * 1.3, line, size, face, colour, anchor="middle")
    return box


def vector_strip(c: Canvas, x: float, y: float, seed: str, colour: str, bars: int = 9) -> float:
    """A few bars of made-up heights: the mark of a stored embedding. Returns the width."""
    digest = hashlib.sha256(seed.encode()).digest()
    for i in range(bars):
        h = 3 + digest[i] % 9
        c.rect(Box(x + i * 3.4, y + 12 - h, 2.2, h), fill=colour, r=1, opacity=0.75)
    return bars * 3.4


# ---- The shared frame ----
#
# Write on the left, the memory between, read on the right; under them, the prompt the read
# feeds and the answer it produces. Read clockwise, it is the loop of Part 2: a conversation
# is written to memory, a later question reads it, and the answer becomes conversation again.

W = 880
M = 30
GAP = 64
COLUMNS = {"write": (M, 210), "store": (M + 210 + GAP, 272), "read": (M + 210 + GAP + 272 + GAP, 210)}


def column(name: str) -> tuple[float, float]:
    return COLUMNS[name]


def heading(c: Canvas, x: float, y: float, w: float, label: str, caption: str | None = None) -> None:
    t = c.theme
    width = c.text(x, y, label, TINY, BOLD, t.muted, spacing=1.6)
    if caption:
        c.text(x + width + 8, y, caption, TINY, SANS, t.muted)
    c.line(x, y + 7, x + w, y + 7, t.line)


def frame(c: Canvas, name: str, tagline: str, write: list[dict], store: list[dict], read: list[dict]) -> float:
    """The title, and the three column headings with chips saying who and when.

    Returns the y where the columns' content starts.
    """
    t = c.theme
    c.text(M, 52, name, TITLE, BOLD)
    used = c.paragraph(M, 62, tagline, W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 26
    bottom = y
    for key, label, specs in (("write", "WRITE", write), ("store", "MEMORY", store), ("read", "READ", read)):
        x, w = COLUMNS[key]
        heading(c, x, y, w, label)
        bottom = max(bottom, y + 16 + chips(c, x, y + 16, specs, width=w))
    return bottom + 20


def prompt_card(c: Canvas, x: float, y: float, w: float, instructions: str, memory_label: str,
                memory: list[tuple[str, str, str | None]] | str, question: str, columns: int = 1) -> Box:
    """The prompt the answering model gets: instructions, the memory part, the question.

    `memory` is a paragraph, or rows of (lead, text, role): a short lead such as a score or a
    date in mono, then the text, tinted by role when given (e.g. "both" for a stale value).
    """
    t = c.theme
    p, s = t["prompt"], t["store"]
    pad = 12
    # measure every part first
    ins = wrap(instructions, SMALL * 0.93, w - 2 * pad, MONO)
    q = wrap(question, SMALL, w - 2 * pad, ITALIC)
    inner = w - 2 * pad - 8
    if isinstance(memory, str):
        mem_lines = wrap(memory, SMALL, inner)
        mem_h = len(mem_lines) * SMALL * 1.4
    else:
        col_w = (inner - (columns - 1) * 14) / columns
        rows = -(-len(memory) // columns)
        mem_h = rows * SMALL * 1.5
    h_ins = 22 + len(ins) * SMALL * 1.35 + 6
    h_mem = 30 + mem_h + 10
    h_q = len(q) * SMALL * 1.38 + 16
    box = Box(x, y, w, h_ins + h_mem + h_q + 6)
    c.rect(box, fill=p.wash, r=12)
    c.icon("scroll-text", x + pad, y + 9, 14, p.accent)
    c.text(x + pad + 20, y + 20, "the prompt", SMALL, BOLD, p.ink)
    for i, line in enumerate(ins):
        c.text(x + pad, y + 24 + SMALL + i * SMALL * 1.35, line, SMALL * 0.93, MONO, p.ink)
    my = y + h_ins
    mem = Box(x + 5, my, w - 10, h_mem)
    c.rect(mem, fill=t.card, stroke=s.accent, r=9, width=1.2)
    c.icon("database", x + pad + 1, my + 9, 14, s.accent)
    c.text(x + pad + 21, my + 20, memory_label, SMALL, BOLD, s.ink)
    top = my + 30
    if isinstance(memory, str):
        for i, line in enumerate(mem_lines):
            c.text(x + pad + 4, top + SMALL + i * SMALL * 1.4, line, SMALL, SANS, t.ink)
    else:
        for i, (lead, text, role) in enumerate(memory):
            col, row = divmod(i, rows)
            tx = x + pad + 4 + col * (col_w + 14)
            ty = top + SMALL + row * SMALL * 1.5
            lead_w = c.text(tx, ty, lead, SMALL * 0.9, MONO, t.muted) + 6 if lead else 0
            colour = t[role].accent if role else t.ink
            c.text(tx + lead_w, ty, text, SMALL, MEDIUM if role else SANS, colour)
    qy = my + h_mem + 4
    for i, line in enumerate(q):
        c.text(x + pad, qy + 6 + SMALL + i * SMALL * 1.38, line, SMALL, ITALIC, t["person"].ink)
    return box


def answer_card(c: Canvas, x: float, y: float, w: float, answer: str,
                needs: list[tuple[str, str]] | None = None) -> Box:
    """What the model replied, and which of the six things it needed reached the prompt."""
    t = c.theme
    icon_tile(c, x, y, "llm", "sparkles", 26)
    c.text(x + 34, y + 18, "the answer", SMALL, BOLD, t["llm"].ink)
    used = c.paragraph(x, y + 32, answer, w, SMALL, SANS, t.ink)
    bottom = y + 32 + used
    if needs:
        bottom += 14
        c.text(x, bottom + 11, "In the prompt, of the six things it needs:", TINY, SANS, t.muted)
        bottom += 20 + scorecard(c, x, bottom + 20, needs, w)
        states = {state for _, state in needs}
        key = [KEY[s] for s in ("yes", "both", "no") if s in states]
        if len(key) > 1:
            bottom += 8
            for line in wrap("; ".join(key) + ".", TINY, w):
                bottom += TINY * 1.35
                c.text(x, bottom, line, TINY, ITALIC, t.muted)
    return Box(x, y, w, bottom - y)


KEY = {"yes": "a tick: it reached the prompt", "both": "a clock: the old and the new value both did",
       "no": "a cross: it did not"}

NEED_STYLE = {
    "yes": ("store", "check", False),
    "both": ("both", "history", False),
    "no": ("stale", "x", True),
}


def scorecard(c: Canvas, x: float, y: float, needs: list[tuple[str, str]], width: float) -> float:
    specs = []
    for label, state in needs:
        role, icon, outline = NEED_STYLE[state]
        specs.append({"text": label, "role": role, "icon": icon, "outline": outline})
    return chips(c, x, y, specs, gap=5, width=width)


def footer(c: Canvas, y: float, source: str, extra: list[tuple[str, str, str]] = ()) -> None:
    """The legend, the same in every figure, and where the example came from."""
    t = c.theme
    c.line(M, y, W - M, y, t.line)
    x = M
    y += 14
    for role, icon, label in [("llm", "sparkles", "a model call"), ("code", "code-xml", "plain code"), *extra]:
        icon_tile(c, x, y, role, icon, 18)
        x += 24 + c.text(x + 24, y + 13, label, TINY, SANS, t.muted) + 14
    c.line(x, y + 9, x + 26, y + 9, t.ink, 1.5)
    x += 32 + c.text(x + 32, y + 13, "writes memory", TINY, SANS, t.muted) + 14
    c.line(x, y + 9, x + 26, y + 9, t.ink, 1.5, dash="5 4")
    x += 32 + c.text(x + 32, y + 13, "reads memory", TINY, SANS, t.muted) + 14
    c.text(W - M, y + 13, source, TINY, SANS, t.muted, anchor="end")
    c.height = int(y + 34)
