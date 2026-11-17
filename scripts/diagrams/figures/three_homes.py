"""Where memory can be kept: as text outside the model, as internal state of the model, or in its weights.

The three forms are those of Hu et al., Memory in the Age of AI Agents (2025), p. 13, with the
trade-offs of its p. 30–31: token-level memory is readable and easy to edit and works with any
model; latent memory is compact but unreadable and needs the model's internals; parametric memory
costs no context but is slow to update and hard to inspect. Larimar (Das et al., 2024) is the one
in-model memory in the library that can delete a single fact. The examples are papers in the
series' reading list. The facts in the text panel are made up.
"""

from __future__ import annotations

from ..kit import BOLD, ITALIC, MEDIUM, MONO, SANS, Box, Canvas, W, M, arrow, icon_tile, vector_strip, wrap
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "three-homes"
TITLE = "Where memory can be kept"
ALT = ("Three places a memory can be kept, side by side. Text outside the model: notes, facts or a "
       "profile, pasted into the prompt; a person can read it, one fact can be corrected or deleted, "
       "and it works with any model, including a hosted one; reading it costs prompt tokens on every "
       "request. Internal state of the model: cached keys and values or memory vectors that the model "
       "attends to; nobody can read it, a single fact can rarely be deleted, and it needs access to the "
       "model's internals; reading it costs a pass over the cache. Weights: knowledge written into the "
       "parameters by editing or training; nobody can read it, a single fact cannot be deleted, and it "
       "needs the weights; reading it costs nothing extra, writing it costs training or an edit. Under "
       "the three, a note: a vector store is text memory, because its embeddings are only an index, "
       "and the model reads the text that the search finds.")

# (role, icon, name, where, how it reaches the model, [(property, state)], costs, examples)
FORMS = [
    ("store", "file-text", "Text", "outside the model",
     "pasted into the prompt",
     [("A person can read it", "yes"), ("One fact can be corrected or deleted", "yes"),
      ("Works with a hosted model's API", "yes")],
     [("Read", "prompt tokens on every request"), ("Write", "a model call, or plain code")],
     "Mem0, Zep, Letta, the chat assistants"),
    ("llm", "cpu", "Internal state", "of the model",
     "attended to inside the model",
     [("A person can read it", "no"), ("One fact can be corrected or deleted", "rarely"),
      ("Works with a hosted model's API", "no")],
     [("Read", "a pass over the cache"), ("Write", "a forward pass, or training")],
     "Memorizing Transformers, MemoryLLM, Cartridges"),
    ("code", "brain", "Weights", "the model's parameters",
     "used in every forward pass",
     [("A person can read it", "no"), ("One fact can be corrected or deleted", "no"),
      ("Works with a hosted model's API", "no")],
     [("Read", "nothing extra"), ("Write", "training or an edit")],
     "MEMIT, memory layers, fine-tuning, Titans"),
]
STATE = {"yes": ("store", "check", "yes"), "no": ("stale", "x", "no"), "rarely": ("both", "x", "rarely")}
TEXT_LINES = ["Lives in Berlin (since May 2026)", "Works as a nurse", "Prefers short answers"]
GAP = 14


def _illustration(c: Canvas, box: Box, kind: str) -> None:
    t = c.theme
    c.rect(box, fill=t.surface, r=8)
    if kind == "Text":
        for i, line in enumerate(TEXT_LINES):
            c.text(box.x + 10, box.y + 20 + i * 17, line, TINY - 1, MONO, t.ink)
    elif kind == "Internal state":
        for i in range(3):
            x = box.x + 10
            for j in range(5):
                x += vector_strip(c, x, box.y + 8 + i * 17, f"kv{i}{j}", t["llm"].accent, 7) + 6
    else:
        cols, rows = 16, 4
        cw, ch = (box.w - 20) / cols, (box.h - 16) / rows
        for i in range(rows):
            for j in range(cols):
                hot = (i * 7 + j * 3) % 11 == 0
                c.rect(Box(box.x + 10 + j * cw + 1, box.y + 8 + i * ch + 1, cw - 2, ch - 2),
                       fill=t["code"].accent if hot else t.line, r=1.5, opacity=0.9 if hot else 1)


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The same fact can be kept as text, as internal state of the model, or in "
                       "its weights. The form decides who can read it and which models can use it.",
                       W - 2 * M, SUBTITLE, SANS, t.muted)
    y0 = 62 + used + 26
    cw = (W - 2 * M - 2 * GAP) / 3
    bottom = y0
    starts = []
    for i, (role, icon, name, where, how, props, costs, examples) in enumerate(FORMS):
        x = M + i * (cw + GAP)
        r = t[role]
        starts.append(len(c.parts))
        icon_tile(c, x + 12, y0 + 12, role, icon, 30)
        c.text(x + 50, y0 + 26, name, SMALL + 1.5, BOLD, t.ink)
        c.text(x + 50, y0 + 42, where, TINY, SANS, t.muted)
        _illustration(c, Box(x + 12, y0 + 56, cw - 24, 66), name)
        y = y0 + 140
        c.text(x + 12, y, "Reaches the model:", TINY, SANS, t.muted)
        c.text(x + 12, y + 17, how, SMALL, MEDIUM, r.ink if role != "code" else t.ink)
        y += 34
        c.line(x + 12, y, x + cw - 12, y, t.line)
        y += 10
        for label, state in props:
            srole, sicon, word = STATE[state]
            sr = t[srole]
            icon_tile(c, x + 12, y, srole, sicon, 18)
            lines = wrap(label, TINY, cw - 100)
            for k, line in enumerate(lines):
                c.text(x + 38, y + 13 + k * TINY * 1.3, line, TINY, SANS, t.ink)
            c.text(x + cw - 12, y + 13, word, TINY, BOLD, sr.accent, anchor="end")
            y += max(26, len(lines) * TINY * 1.3 + 10)
        c.line(x + 12, y, x + cw - 12, y, t.line)
        y += 8
        for label, value in costs:
            c.text(x + 12, y + 14, label, TINY, BOLD, t.muted)
            for k, line in enumerate(wrap(value, TINY, cw - 70)):
                c.text(x + 58, y + 14 + k * TINY * 1.3, line, TINY, SANS, t.ink)
            y += 22
        y += 6
        c.text(x + 12, y + 12, "Examples", TINY, BOLD, t.muted)
        for k, line in enumerate(wrap(examples, TINY, cw - 24, ITALIC)):
            c.text(x + 12, y + 29 + k * TINY * 1.35, line, TINY, ITALIC, t.muted)
        bottom = max(bottom, y + 29 + len(wrap(examples, TINY, cw - 24, ITALIC)) * TINY * 1.35 + 4)
    # the cards, all as tall as the tallest, slipped in under each column's content
    for i in reversed(range(3)):
        c.rect(Box(M + i * (cw + GAP), y0, cw, bottom - y0 + 8), fill=t.card, stroke=t.line, r=12)
        c.parts.insert(starts[i], c.parts.pop())

    # the note about vector stores
    y = bottom + 30
    note = Box(M, y, W - 2 * M, 74)
    s = t["store"]
    c.rect(note, fill=s.wash, r=10)
    c.text(M + 14, y + 22, "A vector store is still text memory.", SMALL, BOLD, s.ink)
    c.paragraph(M + 14, y + 28, "The embedding is an index: a search compares it with the request to find "
                "the text, and the model reads the text.", 420, TINY, SANS, s.ink)
    # text → its embedding; the search finds it; the text goes into the prompt
    tx = M + 470
    c.rect(Box(tx, y + 16, 130, 24), fill=t.card, r=6)
    c.text(tx + 8, y + 32, "Lives in Berlin …", TINY - 1, MONO, t.ink)
    vector_strip(c, tx + 26, y + 46, "berlin", s.accent, 12)
    c.text(tx + 70, y + 58, "index", TINY - 1, ITALIC, s.ink)
    arrow(c, [(tx + 136, y + 28), (tx + 178, y + 28)], s.accent, dashed=True)
    p = t["prompt"]
    pb = Box(tx + 184, y + 12, W - M - 14 - (tx + 184), 50)
    c.rect(pb, fill=p.wash, stroke=p.accent, r=8, width=1)
    c.text(pb.x + 8, pb.y + 18, "the prompt", TINY - 1, BOLD, p.ink)
    c.text(pb.x + 8, pb.y + 36, "Lives in Berlin …", TINY - 1, MONO, p.ink)
    source_line(c, note.bottom + 22, "Forms after Hu et al., Memory in the Age of AI Agents (2025), p. 13 and 30–31")
    return c
