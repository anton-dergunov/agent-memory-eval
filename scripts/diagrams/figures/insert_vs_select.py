"""The two read paths: insert the whole memory into the prompt, or let a search select part of it.

Schematic. The design that does both is Claude Code's auto memory as its documentation describes it
(an index loaded at the start of every session, topic files read on demand); part 9 has the source.
"""

from __future__ import annotations

from ..kit import BOLD, ITALIC, MEDIUM, MONO, SANS, Box, Canvas, W, M, arrow, icon_tile, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "insert-vs-select"
TITLE = "Insert the whole memory, or select part of it"
ALT = ("Two read paths side by side. Insert: the whole memory, here eight short entries, goes into the "
       "prompt with the request; no stored fact can be missed, but the prompt grows with the memory and "
       "stops at the context window, and the model must find the relevant lines among the rest. Select: a "
       "search compares the request (a trip for next weekend) with the stored entries and puts the three "
       "best matches into the prompt (lives in Berlin, runs on weekends, sister in Hamburg); the "
       "prompt stays small however much is stored, but the entry the answer needed (has a dog), which the "
       "request does not mention, ranks fourth and is left out. Under both, a design that does both: an index that is always in the "
       "prompt, and topic files read only when the index points to them, as in Claude Code.")

ENTRIES = ["lives in Berlin", "works as a nurse", "prefers short answers", "plays the piano",
           "has a dog", "learning Spanish", "runs on weekends", "sister in Hamburg"]
PICKED = {0, 6, 7}          # what the search returned
NEEDED = 4                  # what the request needed, ranked fourth
REQUEST = "Suggest a trip for next weekend."
GAP = 26


def _entry(c: Canvas, x: float, y: float, w: float, text: str, style: str | None = None) -> Box:
    t = c.theme
    box = Box(x, y, w, 20)
    if style == "missed":
        c.rect(box, fill=t.paper, stroke=t["stale"].accent, r=5, dash="3 2.5")
        c.text(x + 8, y + 14, text, TINY - 1.5, MONO, t["stale"].accent)
    elif style == "picked":
        c.rect(box, fill=t.card, stroke=t["store"].accent, r=5, width=1.4)
        c.text(x + 8, y + 14, text, TINY - 1.5, MONO, t["store"].ink)
    else:
        c.rect(box, fill=t.card, r=5)
        c.text(x + 8, y + 14, text, TINY - 1.5, MONO, t.ink)
    return box


def _pros(c: Canvas, x: float, y: float, w: float, items: list[tuple[bool, str]]) -> float:
    t = c.theme
    for good, text in items:
        role, icon = ("store", "check") if good else ("stale", "x")
        icon_tile(c, x, y, role, icon, 18)
        lines = wrap(text, TINY, w - 28)
        for k, line in enumerate(lines):
            c.text(x + 26, y + 13 + k * TINY * 1.35, line, TINY, SANS, t.ink)
        y += max(24, len(lines) * TINY * 1.35 + 10)
    return y


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    s, p = t["store"], t["prompt"]
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The same memory and the same request, read in the two ways. A good answer to this "
                       "request takes the dog into account, which the request does not mention.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y0 = 62 + used + 28
    cw = (W - 2 * M - GAP) / 2
    ew = 150

    for side in ("insert", "select"):
        x = M if side == "insert" else M + cw + GAP
        icon_tile(c, x, y0 - 4, "prompt", "layers" if side == "insert" else "search", 26)
        c.text(x + 34, y0 + 9, "Insert" if side == "insert" else "Select", SMALL + 1, BOLD, p.ink)
        c.text(x + 34, y0 + 25, "the whole memory goes into the prompt" if side == "insert"
               else "a search picks the best matches", TINY, SANS, t.muted)
        top = y0 + 44
        # the memory
        mem = Box(x, top, ew + 16, 24 + len(ENTRIES) * 24)
        c.rect(mem, fill=s.wash, r=10)
        c.text(x + 10, top + 16, "Memory", TINY, BOLD, s.ink)
        for i, e in enumerate(ENTRIES):
            style = None
            if side == "select":
                style = "picked" if i in PICKED else None
            _entry(c, x + 8, top + 24 + i * 24, ew, e, style)
        # the prompt
        px = mem.right + 36
        pw = x + cw - px
        if side == "insert":
            ph = 46 + len(ENTRIES) * 24 + 26
        else:
            ph = 46 + len(PICKED) * 24 + 26 + 44
        pb = Box(px, top, pw, ph)
        c.rect(pb, fill=p.wash, r=10)
        c.text(px + 10, top + 16, "The prompt", TINY, BOLD, p.ink)
        c.text(px + 10, top + 34, "Instructions.", TINY - 1, MONO, p.ink)
        shown = list(range(len(ENTRIES))) if side == "insert" else sorted(PICKED)
        for k, i in enumerate(shown):
            _entry(c, px + 6, top + 42 + k * 24, pw - 12, ENTRIES[i], "picked" if side == "select" else None)
        qy = top + 42 + len(shown) * 24 + 16
        c.text(px + 10, qy, REQUEST, TINY - 0.5, ITALIC, t["person"].ink)
        if side == "select":
            c.text(px + 10, qy + 26, "Not returned:", TINY - 1, BOLD, t["stale"].accent)
            _entry(c, px + 6, qy + 32, pw - 12, ENTRIES[NEEDED], "missed")
            c.text(px + pw - 8, qy + 26, "rank 4 of a top 3", TINY - 1.5, ITALIC, t["stale"].accent, anchor="end")
        arrow(c, [(mem.right + 4, top + 60), (px - 4, top + 60)], t.ink, dashed=True,
              label="all" if side == "insert" else "top 3")
        bottom = max(mem.bottom, pb.bottom) + 18
        items = ([(True, "No stored fact can be missed."),
                  (False, "The prompt grows with the memory, and stops at the context window."),
                  (False, "The model must find the few lines that matter among the rest.")]
                 if side == "insert" else
                 [(True, "The prompt stays small, however much is stored."),
                  (False, "The fact the request needed can rank just below the cut."),
                  (False, "A search and a rule for how many to take must be designed and tuned.")])
        end = _pros(c, x, bottom, cw, items)
        if side == "insert":
            ins_end = end
        else:
            sel_end = end

    # both in one design
    y = max(ins_end, sel_end) + 16
    band = Box(M, y, W - 2 * M, 62)
    c.rect(band, fill=t.surface, r=10)
    c.text(M + 14, y + 22, "Both in one design", SMALL, BOLD, t.ink)
    c.paragraph(M + 14, y + 28, "An index that is always in the prompt, one line per memory, and topic files "
                "read only when the index points to them. Claude Code's memory works this way.",
                W - 2 * M - 28, TINY, SANS, t.muted)
    source_line(c, band.bottom + 22, "Schematic; the entries are made up")
    return c
