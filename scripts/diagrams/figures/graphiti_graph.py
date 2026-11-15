"""Zep / Graphiti: the stored graph after session 1 and after session 2, drawn the same way.

The entities, their types and the facts between them are the committed run of
notebooks/03-zep-graphiti.ipynb (the graph drawings and fact tables of sections 2 and 3). Each
entity keeps its place in both panels, so what session 2 added stands out. graphiti_walk.py
draws the same graph with the walk of section 5 on it.
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, SANS, Box, Canvas, W, M, _head, label_pill, measure
from ..theme import SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme

NAME = "graphiti-graph"
TITLE = "The graph, after each session"
ALT = ("The graph Graphiti stored for the example, after session 1 and after session 2. Entities "
       "are boxes coloured by their type: person, place, preference, health condition. After "
       "session 1, seven facts all start at Anton: a dinner plan stored twice, once to Anton's "
       "sister and once to Berlin; strictly vegetarian; a peanut allergy; Indian cuisine; paneer "
       "dishes; a budget of 40 euros a head. The assistant is an entity with no facts. After "
       "session 2, the vegetarian fact is dashed, closed on 20 July, and a pescatarian diet fact "
       "starts at Anton. The assistant has a fact pointing at the pescatarian diet. Anton lives in "
       "Kreuzberg and has a sister named Lena; from Anton's sister a fact leads to Lena's partner "
       "Jonas, and from Jonas to coeliac. A second node called Lena, connected to nothing else, "
       "holds 'Lena cannot eat shellfish'.")

# Entity: (type, centre in the panel, session it first appears in)
ENTITIES = {
    "Anton": ("Person", (410, 190), 1),
    "vegetarian": ("Preference", (190, 48), 1),
    "pescatarian diet": ("Preference", (440, 48), 2),
    "Assistant": ("Person", (745, 48), 1),
    "Indian cuisine": ("Preference", (112, 118), 1),
    "Paneer dishes": ("Preference", (92, 205), 1),
    "40 euros a head budget": ("Preference", (140, 292), 1),
    "peanut allergy": ("HealthCondition", (720, 130), 1),
    "Kreuzberg": ("Place", (740, 210), 2),
    "Berlin": ("Place", (708, 292), 1),
    "Anton's sister": ("Person", (340, 335), 1),
    "Lena's partner Jonas": ("Person", (520, 420), 2),
    "coeliac": ("HealthCondition", (772, 420), 2),
    "Lena": ("Person", (70, 420), 2),
    "shellfish": ("HealthCondition", (300, 420), 2),
}
# Fact: (from, to, relation, session, closed on). Two facts join Anton and Anton's sister.
FACTS = [
    ("Anton", "Anton's sister", "PLANS_TO_VISIT", 1, None),
    ("Anton", "Berlin", "PLANS_TO_VISIT", 1, None),
    ("Anton", "vegetarian", "HAS_DIETARY_PREFERENCE", 1, "20 Jul"),
    ("Anton", "peanut allergy", "HAS_HEALTH_CONDITION", 1, None),
    ("Anton", "Indian cuisine", "PREFERS_CUISINE", 1, None),
    ("Anton", "Paneer dishes", "PREFERS_DISHES", 1, None),
    ("Anton", "40 euros a head budget", "HAS_BUDGET", 1, None),
    ("Anton", "pescatarian diet", "ADOPTS_DIET", 2, None),
    ("Assistant", "pescatarian diet", "ACKNOWLEDGES_INCLUSION_OF", 2, None),
    ("Anton", "Kreuzberg", "LIVES_IN", 2, None),
    ("Anton", "Anton's sister", "HAS_SISTER", 2, None),
    ("Anton's sister", "Lena's partner Jonas", "IS_PARTNER_OF", 2, None),
    ("Lena", "shellfish", "HAS_DIETARY_RESTRICTION", 2, None),
    ("Lena's partner Jonas", "coeliac", "HAS_HEALTH_CONDITION", 2, None),
]
TYPE_ROLE = {"Person": "person", "Place": "code", "Preference": "store", "HealthCondition": "both"}
TYPE_NAME = {"Person": "person", "Place": "place", "Preference": "preference",
             "HealthCondition": "health condition"}
PANEL_W = W - 2 * M
PANEL_H = {1: 370, 2: 455}
LABEL = TINY - 2


def pill_box(name: str, x: float, y: float) -> Box:
    (cx, cy) = ENTITIES[name][1]
    w = measure(name, TINY, MEDIUM) + 18
    return Box(x + cx - w / 2, y + cy - 12, w, 24)


def _edge_point(box: Box, fx: float, fy: float) -> tuple[float, float]:
    """Where the line from (fx, fy) to the box's centre meets the box's edge."""
    dx, dy = box.cx - fx, box.cy - fy
    t = min((box.w / 2 + 3) / abs(dx) if dx else 1e9, (box.h / 2 + 3) / abs(dy) if dy else 1e9)
    return box.cx - dx * t, box.cy - dy * t


def draw_graph(c: Canvas, x: float, y: float, session: int, highlight=(), starts=(), drop_closed=False,
               faded=()) -> Box:
    """The graph as it stood after `session`, in a panel at (x, y).

    `highlight` lists (from, to) facts drawn thick in the prompt colour, `starts` the entities
    a walk starts from, `drop_closed` leaves closed facts out, `faded` entities drawn pale.
    """
    t = c.theme
    panel = Box(x, y, PANEL_W, PANEL_H[session])
    c.rect(panel, fill=t["store"].wash, r=14)
    names = [n for n, (_, _, s) in ENTITIES.items() if s <= session]
    facts = [f for f in FACTS if f[3] <= session and not (drop_closed and f[4])]
    boxes = {n: pill_box(n, x, y) for n in names}

    pairs: dict[tuple[str, str], int] = {}
    for a, b, *_ in facts:
        pairs[(a, b)] = pairs.get((a, b), 0) + 1
    seen: dict[tuple[str, str], int] = {}
    labels = []
    for a, b, relation, s, closed in facts:
        k = seen.get((a, b), 0)
        seen[(a, b)] = k + 1
        ba, bb = boxes[a], boxes[b]
        # two facts between the same entities are drawn side by side
        shift = (k - (pairs[(a, b)] - 1) / 2) * 30
        ax, ay = ba.cx + shift, ba.cy
        bx, by = bb.cx + shift, bb.cy
        if closed and session >= 2:
            colour, width, dash = t["stale"].accent, 1.4, "5 4"
        elif (a, b) in highlight:
            colour, width, dash = t["prompt"].accent, 3.2, None
        else:
            colour, width, dash = t["store"].accent, 1.3, None
        sx, sy = _edge_point(Box(ba.x + shift, ba.y, ba.w, ba.h), bx, by)
        ex, ey = _edge_point(Box(bb.x + shift, bb.y, bb.w, bb.h), ax, ay)
        length = ((ex - sx) ** 2 + (ey - sy) ** 2) ** 0.5
        ux, uy = (ex - sx) / length, (ey - sy) / length
        c.line(sx, sy, ex - ux * 5, ey - uy * 5, colour, width, dash=dash)
        _head(c, (ex, ey), (ux, uy), colour, 7 if width < 2 else 9)
        text = relation + (f"\nuntil {closed}" if closed and session >= 2 else "")
        at = 0.5 if pairs[(a, b)] == 1 else 0.3 + 0.4 * k   # side-by-side facts: labels apart
        lift = 13 if abs(ey - sy) < 8 else 0   # on a level edge the label sits above the line
        labels.append((sx + (ex - sx) * at, sy + (ey - sy) * at - lift, text, colour))
    for lx, ly, text, colour in labels:
        label_pill(c, lx, ly, text, colour, MEDIUM, LABEL)

    for n in names:
        kind, _, _ = ENTITIES[n]
        role = t[TYPE_ROLE[kind]]
        box = boxes[n]
        stale = n in faded
        c.rect(box, fill=t.paper if stale else role.wash,
               stroke=t["stale"].accent if stale else role.accent, r=12,
               width=2.6 if n in starts else 1.1, dash="3 2.5" if stale else None)
        if n in starts:
            c.rect(Box(box.x - 4, box.y - 4, box.w + 8, box.h + 8), stroke=t["prompt"].accent, r=15, width=1.6)
        c.text(box.cx, box.cy + 4.5, n, TINY, BOLD if n == "Anton" else MEDIUM,
               t["stale"].ink if stale else role.ink, anchor="middle")
    return panel


def type_key(c: Canvas, x: float, y: float) -> float:
    """The four entity types and their colours, on one line. Returns its width."""
    t = c.theme
    start = x
    x += c.text(x, y, "Entity types:", TINY, MEDIUM, t.muted) + 10
    for kind in ("Person", "Place", "Preference", "HealthCondition"):
        role = t[TYPE_ROLE[kind]]
        c.rect(Box(x, y - 11, 14, 14), fill=role.wash, stroke=role.accent, r=4)
        x += 20 + c.text(x + 20, y, TYPE_NAME[kind], TINY, SANS, t.muted) + 14
    return x - start


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "Every entity is a box and every fact is an arrow between two of them, "
                       "named by its relation. Each entity is drawn in the same place in both "
                       "pictures, so what session 2 added stands out.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 30
    for session, caption in ((1, "After session 1, in March: 7 facts, all starting at Anton"),
                             (2, "After session 2, in July: 14 facts, one of them closed")):
        c.text(M, y, caption, SUBTITLE, BOLD)
        panel = draw_graph(c, M, y + 12, session)
        y = panel.bottom + 34
    y -= 10
    type_key(c, M, y)
    y += 18
    for note in ("The closed fact is dashed, with the day it ended. The second box called Lena is "
                 "a second node for the same person: step 2 did not match it to Anton's sister.",):
        used = c.paragraph(M, y, note, W - 2 * M, TINY, SANS, t.muted)
        y += used
    source_line(c, y + 16, "From notebooks/03-zep-graphiti.ipynb, sections 2 and 3")
    return c


def source_line(c: Canvas, y: float, source: str) -> None:
    """A rule and where the example came from: the footer of a figure that needs no legend."""
    c.line(M, y, W - M, y, c.theme.line)
    c.text(W - M, y + 20, source, TINY, SANS, c.theme.muted, anchor="end")
    c.height = int(y + 40)
