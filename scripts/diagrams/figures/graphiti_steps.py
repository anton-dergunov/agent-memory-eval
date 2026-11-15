"""Zep / Graphiti: the four steps of the write path, for one message.

The message is the first of session 2. Every entity, score, fact and reply below is from the
committed run of notebooks/03-zep-graphiti.ipynb (section 3, and the model calls behind it);
the similarity of "pescatarian diet" to "vegetarian" is the score that put "vegetarian" into
the matching prompt as a candidate.
"""

from __future__ import annotations

from ..kit import (BOLD, ITALIC, MEDIUM, MONO, SANS, Box, Canvas, W, M, arrow, bubble, chip, measure,
                   wrap)
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import TYPE_ROLE, source_line

NAME = "graphiti-steps"
TITLE = "Four steps for one message"
ALT = ("The four steps Graphiti runs for one message, traced with the first message of session 2. "
       "Step 1, an LLM call, finds three entities: Anton, pescatarian diet and peanut allergy. Step "
       "2 matches them to stored entities: Anton and peanut allergy by exact name, with no call; "
       "pescatarian diet has no exact match, its name scores 0.691 against the stored "
       "'vegetarian', above the 0.6 floor, so an LLM call is asked and says they are different: a "
       "new entity. Step 3, an LLM call, extracts two facts with dates: Anton started following a "
       "pescatarian diet about a month ago, replacing his previous vegetarian diet, dated 20 July; "
       "and Anton has a severe, anaphylactic peanut allergy, dated 14 March. Step 4 compares each new fact with "
       "stored ones. For the diet, code finds no fact between the same two entities and seven by "
       "search; an LLM call says it contradicts 'Anton has been strictly vegetarian for eight "
       "years'; code ends that fact on 20 July, because it started earlier. For the allergy, code "
       "finds the stored allergy fact between the same two entities; an LLM call says it is a "
       "duplicate, so nothing new is stored. In all: five LLM calls and three embedding calls; one "
       "fact added and one closed.")

MESSAGE = ("“Small update on the food thing — I started eating fish about a month ago. So I'm "
           "pescatarian now, not vegetarian. Still no meat, and the peanut situation obviously "
           "hasn't changed.”")
LEFT_W = 250
GUT = 22


def _card(c: Canvas, y: float, h: float, n: int, title: str, kinds: list[tuple[str, str]], api: str) -> None:
    """The step: its number, name, what does it (LLM or code) and the prompt it uses."""
    t = c.theme
    llm = any(role == "llm" for role, _ in kinds)
    box = Box(M, y, LEFT_W, h)
    c.rect(box, fill=t.card, stroke=t["llm"].accent if llm else t.line, r=12, width=1.6 if llm else 1)
    c.circle(M + 24, y + 24, 12, fill=t["llm"].wash if llm else t["code"].wash)
    c.text(M + 24, y + 29, str(n), SMALL, BOLD, t["llm"].ink if llm else t["code"].ink, anchor="middle")
    c.text(M + 44, y + 29, title, 15, BOLD)
    cx = M + 14
    for role, text in kinds:
        icon = "sparkles" if role == "llm" else "code-xml"
        cx = chip(c, cx, y + 46, text, role, icon=icon).right + 5
    if api:
        size = min(TINY, TINY * (LEFT_W - 28) / measure(api, TINY, MONO))
        c.text(M + 14, y + 90, api, size, MONO, t["llm"].accent)


def _entity(c: Canvas, x: float, y: float, name: str, kind: str) -> Box:
    t = c.theme
    role = t[TYPE_ROLE[kind]]
    w = measure(name, TINY, MEDIUM) + 18
    box = Box(x, y, w, 24)
    c.rect(box, fill=role.wash, stroke=role.accent, r=12)
    c.text(box.cx, y + 16.5, name, TINY, MEDIUM, role.ink, anchor="middle")
    return box


def _say(c: Canvas, x: float, y: float, w: float, text: str, face=SANS, fill=None, size=SMALL) -> float:
    """A wrapped paragraph; returns the y under it."""
    return y + c.paragraph(x, y, text, w, size, face, fill)


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Every message goes through the same four steps, one message at a "
                       "time and in order. Here they are for the message that changes a fact. "
                       "The model makes judgements; plain code decides what is stored and when a "
                       "fact ends.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 26
    b = bubble(c, M, y, W - 2 * M, "20 July · session 2, first message", MESSAGE)
    y = b.bottom + 30
    rx = M + LEFT_W + GUT
    rw = W - M - rx
    muted, stale, store = t.muted, t["stale"], t["store"]
    rows = []

    # Step 1
    top = y
    yy = _say(c, rx, top - 4, rw, "In: the message, the ten messages before it, and the entity "
              "types. Out: the things it mentions.", fill=muted, size=TINY)
    x = rx
    for name, kind in (("Anton", "Person"), ("pescatarian diet", "Preference"),
                       ("peanut allergy", "HealthCondition")):
        x = _entity(c, x, yy + 6, name, kind).right + 8
    rows.append((top, max(yy + 36, top + 104) - top, 1, "Find entities", [("llm", "LLM")],
                 "extract_nodes.extract_message"))
    y = top + rows[-1][1] + 26

    # Step 2
    top = y
    yy = top
    for name, kind, how, out, role in (
            ("Anton", "Person", "the same name is stored", "same node, no call", "code"),
            ("peanut allergy", "HealthCondition", "the same name is stored", "same node, no call", "code"),
            ("pescatarian diet", "Preference", "no such name; “vegetarian” scores 0.691, over 0.6, "
             "so the model is asked", "a different thing: a new node", "llm")):
        e = _entity(c, rx, yy, name, kind)
        lines = wrap(how, TINY, rw - e.w - measure("→ " + out, TINY, MEDIUM) - 30)
        for i, line in enumerate(lines):
            c.text(e.right + 10, yy + 16 + i * TINY * 1.3, line, TINY, SANS, muted)
        c.text(W - M, yy + 16, "→ " + out, TINY, MEDIUM, t[role].accent, anchor="end")
        yy += max(30, len(lines) * TINY * 1.3 + 14)
    rows.append((top, max(yy - top, 104), 2, "Match to stored ones", [("code", "code"), ("llm", "LLM")],
                 "dedupe_nodes.nodes"))
    y = top + rows[-1][1] + 26

    # Step 3
    top = y
    yy = _say(c, rx, top - 4, rw, "In: the message and the entities. Out: facts between two of them, "
              "each a sentence with the date it became true.", fill=muted, size=TINY) + 4
    for src, rel, dst, kind, text, valid in (
            ("Anton", "ADOPTS_DIET", "pescatarian diet", "Preference",
             "Anton started following a pescatarian diet about a month ago, replacing his previous "
             "vegetarian diet.", "2026-07-20"),
            ("Anton", "HAS_HEALTH_CONDITION", "peanut allergy", "HealthCondition",
             "Anton has a severe, anaphylactic peanut allergy.", "2026-03-14")):
        e1 = _entity(c, rx, yy, src, "Person")
        lw = measure(rel, TINY - 1.5, MEDIUM)
        c.line(e1.right + 4, yy + 12, e1.right + lw + 30, yy + 12, store.accent, 1.3)
        c.text(e1.right + 16, yy + 8, rel, TINY - 1.5, MEDIUM, store.ink)
        e2 = _entity(c, e1.right + lw + 34, yy, dst, kind)
        c.text(W - M, yy + 16, f"valid_at {valid}", TINY, MONO, muted, anchor="end")
        yy = _say(c, rx, yy + 26, rw, f"“{text}”", ITALIC, t.ink, TINY) + 10
    rows.append((top, max(yy - top, 104), 3, "Extract facts", [("llm", "LLM")], "extract_edges.edge"))
    y = top + rows[-1][1] + 26

    # Step 4
    top = y
    yy = top
    for head, pair, found, verdict, result, role in (
            ("The new diet fact", "between the same two entities: none",
             "by a search for its sentence: 7 stored facts",
             "the model: it contradicts “Anton has been strictly vegetarian for eight years”",
             "code: that fact started earlier (14 March), so it ends when this one starts, on 20 July. "
             "The new fact is stored.", "stale"),
            ("The allergy fact", "between the same two entities: “Anton has a severe anaphylactic "
             "peanut allergy”", None, "the model: a duplicate of it",
             "nothing new is stored; the old fact keeps its dates", "store")):
        c.text(rx, yy + 12, head, SMALL, BOLD)
        yy += 20
        for line in (pair, found):
            if line:
                yy = _say(c, rx + 12, yy, rw - 12, "· " + line, SANS, muted, TINY)
        yy = _say(c, rx + 12, yy, rw - 12, "· " + verdict, MEDIUM, t["llm"].accent, TINY)
        yy = _say(c, rx + 12, yy, rw - 12, "· " + result, MEDIUM, t[role].accent, TINY) + 10
    rows.append((top, max(yy - top, 104), 4, "Compare with stored facts",
                 [("code", "code"), ("llm", "LLM"), ("code", "code")], "dedupe_edges.resolve_edge"))
    y = top + rows[-1][1] + 10

    for i, (top, h, n, title, kinds, api) in enumerate(rows):
        _card(c, top, h, n, title, kinds, api)
        if i:
            prev = rows[i - 1]
            arrow(c, [(M + 30, prev[0] + prev[1]), (M + 30, top)], t.muted)
        c.line(rx - GUT / 2, top + 4, rx - GUT / 2, top + h - 4, t.line)

    y += 14
    c.rect(Box(M, y, W - 2 * M, 44), fill=t.surface, r=10)
    c.runs(M + 14, y + 27, [("For this message: ", BOLD, None),
                            ("5 LLM calls (1 + 1 + 1 + 2) and 3 embedding calls. One fact added, "
                             "one closed, one recognised as a repeat.", SANS, None)], SMALL)
    source_line(c, y + 66, "From notebooks/03-zep-graphiti.ipynb, section 3")
    return c
