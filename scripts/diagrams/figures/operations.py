"""The write path and the read path of a text memory, with the six operations placed on them.

The operations and their grouping are those of Du et al., Rethinking Memory in LLM based Agents
(2025), §2.4, p. 6–7: encoding (consolidation, indexing), evolving (updating, forgetting) and
adapting (retrieval, condensation). Where each runs, and the example of a user who moved from
Munich to Berlin, are the series' own.
"""

from __future__ import annotations

from ..kit import (BOLD, ITALIC, MEDIUM, MONO, SANS, Box, Canvas, W, M, arrow, bubble, column, frame,
                   node, panel, wrap)
from ..theme import SMALL, TINY, Theme
from .graphiti_graph import source_line

NAME = "operations"
TITLE = "The write path and the read path"
ALT = ("How a text memory works, as two paths around a store. The write path runs after or during a "
       "conversation and can run in the background: consolidation turns the conversation into candidate "
       "memories (\"I moved to Berlin in May\" becomes \"lives in Berlin, since May 2026\"); updating "
       "reconciles each one with what is stored (it replaces \"lives in Munich\"); indexing builds what a "
       "read will use, such as an embedding or a keyword index. Forgetting drops or decays entries in the "
       "store. The read path runs on every request while the user waits: retrieval finds what the request "
       "needs (\"any good bakeries near me?\" finds \"lives in Berlin\"), and condensation shortens it to "
       "fit the prompt. The answering model gets the instructions, what memory returned, and the request. "
       "Each operation is tagged with the survey's group: encoding, evolving or adapting.")

GROUP = {"encoding": "encoding", "evolving": "evolving", "adapting": "adapting"}


def _tag(group: str) -> list[dict]:
    return [{"text": group, "size": TINY - 1}]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    s, p = t["store"], t["prompt"]
    y = frame(c, TITLE, "Six operations, as one survey names them, placed on the two paths of a text "
              "memory. The example is a user who moved from Munich to Berlin.",
              {"write": "After or during a conversation. It can run in the background.",
               "store": "What is kept between conversations.",
               "read": "On every request, while the user waits."})
    wx, ww = column("write")
    sx, sw = column("store")
    rx, rw = column("read")

    # inputs
    b1 = bubble(c, wx, y, ww, "a conversation", "… I moved to Berlin in May …")
    b2 = bubble(c, rx, y, rw, "a later request", "Any good bakeries near me?")
    y = max(b1.bottom, b2.bottom) + 26

    # the write path
    n1 = node(c, wx, y, ww, "code", "pencil", "Consolidation",
              "Turns the conversation into candidate memories: lives in Berlin, since May 2026.",
              tags=_tag("encoding"), badge=False)
    n2 = node(c, wx, n1.bottom + 22, ww, "code", "history", "Updating",
              "Reconciles each one with what is stored: add, merge, replace, or ignore. Here it replaces "
              "lives in Munich.", tags=_tag("evolving"), badge=False)
    n3 = node(c, wx, n2.bottom + 22, ww, "code", "list", "Indexing",
              "Builds what a read will use: an embedding, a keyword index, a link to Berlin.",
              tags=_tag("encoding"), badge=False)
    arrow(c, [(wx + 24, b1.bottom + 4), (wx + 24, n1.y - 4)], t.ink)
    arrow(c, [(wx + 24, n1.bottom + 2), (wx + 24, n2.y - 4)], t.ink)
    arrow(c, [(wx + 24, n2.bottom + 2), (wx + 24, n3.y - 4)], t.ink)

    # the store, and forgetting
    store = panel(c, sx, y, sw, 178, "database", "Memory")
    rows = [("lives in Berlin (since May 2026)", "store"), ("lives in Munich", "stale"),
            ("works as a nurse", None), ("prefers short answers", None)]
    for i, (text, role) in enumerate(rows):
        ry = store.y + 46 + i * 30
        c.rect(Box(sx + 10, ry, sw - 20, 24), fill=t.card, r=6)
        colour = t[role].accent if role else t.ink
        c.text(sx + 18, ry + 16, text, TINY, MONO if role != "stale" else MONO, colour)
        if role == "stale":
            c.line(sx + 18, ry + 12, sx + 18 + 118, ry + 12, colour, 1.2)
    forget = node(c, sx, store.bottom + 22, sw, "code", "x", "Forgetting",
                  "Drops or decays entries: what is old, unused, or asked to be deleted. Often run in batches.",
                  tags=_tag("evolving"), badge=False)
    arrow(c, [(sx + sw / 2, forget.y - 4), (sx + sw / 2, store.bottom + 4)], t.ink)
    arrow(c, [(n1.right + 4, store.cy), (sx - 4, store.cy)], t.ink, label="writes")

    # the read path
    r1 = node(c, rx, y, rw, "code", "search", "Retrieval",
              "Finds what the request needs: by similarity, keywords, a graph walk, or a search the model "
              "asks for. Here: lives in Berlin.", tags=_tag("adapting"), badge=False)
    r2 = node(c, rx, r1.bottom + 22, rw, "code", "layers", "Condensation",
              "Shortens what was found to fit the prompt: drops repeats, summarises, keeps a budget.",
              tags=_tag("adapting"), badge=False)
    arrow(c, [(rx + 24, b2.bottom + 4), (rx + 24, r1.y - 4)], t.ink)
    arrow(c, [(rx + 24, r1.bottom + 2), (rx + 24, r2.y - 4)], t.ink)
    arrow(c, [(store.right + 4, r1.cy), (rx - 4, r1.cy)], t.ink, dashed=True, label="reads")

    # the prompt the answering model gets
    py = max(forget.bottom, r2.bottom) + 34
    pb = Box(sx, py, W - M - sx, 112)
    c.rect(pb, fill=p.wash, r=12)
    c.icon("scroll-text", sx + 12, py + 10, 15, p.accent)
    c.text(sx + 34, py + 22, "The prompt of the answering model", SMALL, BOLD, p.ink)
    c.text(sx + 14, py + 46, "Instructions.", SMALL * 0.93, MONO, p.ink)
    mem = Box(sx + 8, py + 54, pb.w - 16, 30)
    c.rect(mem, fill=t.card, stroke=s.accent, r=8, width=1.2)
    c.text(mem.x + 10, mem.y + 20, "What memory returned: lives in Berlin (since May 2026)", SMALL, SANS, t.ink)
    c.text(sx + 14, py + 102, "Any good bakeries near me?", SMALL, ITALIC, t["person"].ink)
    arrow(c, [(rx + rw - 24, r2.bottom + 2), (rx + rw - 24, py - 4)], t.ink, dashed=True)
    note_y = n3.bottom + 18
    used = c.paragraph(wx, note_y, "Nothing else from earlier conversations reaches the model: what the read path "
                "does not return, the model does not know.", ww, TINY, ITALIC, t.muted)

    # the key and the source
    ky = max(pb.bottom, note_y + used) + 26
    c.line(wx, ky, wx + 26, ky, t.ink, 1.5)
    x = wx + 32 + c.text(wx + 32, ky + 4, "writes memory", TINY, SANS, t.muted) + 16
    c.line(x, ky, x + 26, ky, t.ink, 1.5, dash="5 4")
    x += 32 + c.text(x + 32, ky + 4, "reads memory", TINY, SANS, t.muted) + 16
    c.text(x, ky + 4, "Tags: the survey's three groups of operations", TINY, SANS, t.muted)
    source_line(c, ky + 18, "Operations as named in Du et al., Rethinking Memory in LLM based Agents (2025), p. 6–7")
    return c
