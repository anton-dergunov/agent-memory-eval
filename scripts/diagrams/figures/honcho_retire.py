"""Honcho: what happened to the vegetarian fact, and to what rested on it, in the first server run.

Rows, links and states from scripts/replays/honcho_server_runs/run1.json: the stored rows
(deleted_at), the premise links (document_sources) and the peer card. The two rules at the bottom
are delete_observations (src/utils/agent_tools.py) and the scope-removal cascade
(src/deriver/scope_backfill.py) in Honcho 3.3.0.
"""

from __future__ import annotations

from ..kit import BOLD, ITALIC, MONO, SANS, Box, Canvas, W, M, arrow, heading, label_pill, measure, node
from ..theme import SMALL, SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line
from .honcho_parts import conclusion, legend

NAME = "honcho-retire"
TITLE = "What rested on the deleted fact"
ALT = ("The first server run, after dream 2. The explicit row 'Anton has followed a strict "
       "vegetarian diet for eight years' was deleted. Three conclusions cite it. The update, "
       "'Anton transitioned from a vegetarian diet to a pescatarian diet in June 2026', cites it on "
       "purpose. 'Anton is likely to order vegetarian Indian food featuring paneer during his "
       "dinner' is still live and carries the old value. Dream 1's pattern 'consistently "
       "prioritizes vegetarian options' was replaced by a near duplicate written in dream 2, after "
       "the update: 'a consistent preference for vegetarian cuisine', confidence high, derived "
       "twice, which cites the old pattern. The peer card was rewritten from Vegetarian to "
       "Pescatarian. Bottom: a dream's delete stamps only the rows it names; removing a session "
       "from a scope deletes every derived row with a deleted source, repeatedly, and would delete "
       "all three live rows here, the update included.")


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "The first server run, after dream 2. A delete removes the row it "
                       "names; the rows that cite it keep their links and stay live.",
                       W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 26
    legend(c, M, y, ["deleted", "stale", "update", "live"])
    y += 26
    ax, aw = M, 220
    bx, bw = M + 280, 270
    cx_, cw = M + 600, W - M - (M + 600)
    d20 = conclusion(c, bx, y, bw, "deductive", "Anton transitioned from a vegetarian diet to a pescatarian "
                     "diet in June 2026.", "update", note="cites the old fact on purpose")
    d7 = conclusion(c, bx, d20.bottom + 16, bw, "deductive", "Anton is likely to order vegetarian Indian food "
                    "featuring paneer during his dinner.", "stale", note="from dream 1; still live")
    i9 = conclusion(c, bx, d7.bottom + 16, bw, "inductive", "Anton consistently prioritizes vegetarian options "
                    "that include paneer when selecting meals.", "deleted", tag="medium",
                    note="from dream 1; replaced in dream 2 by a near duplicate")
    i22 = conclusion(c, cx_, i9.y - 6, cw, "inductive", "Anton has a consistent preference for vegetarian "
                     "cuisine, specifically Indian dishes containing paneer.", "stale",
                     tag="high · derived ×2", note="written in dream 2, after the update")
    mid = (d20.y + i9.bottom) / 2
    e2 = conclusion(c, ax, mid - 44, aw, "explicit", "Anton has followed a strict vegetarian diet for "
                    "eight years.", "deleted", note="said 14 March; deleted in dream 2")
    for card in (d20, d7, i9):
        ey = e2.cy
        arrow(c, [(card.x, card.cy), (card.x - 24, card.cy), (card.x - 24, ey), (e2.right, ey)],
              t["stale"].accent if card is not d20 else t["store"].accent, radius=8, width=1.2)
    label_pill(c, bx - 24, mid + 30, "cites", t["stale"].accent, BOLD)
    arrow(c, [(i22.x, i9.cy), (i9.right, i9.cy)], t["stale"].accent, width=1.2, label="cites", label_face=BOLD)
    # the peer card
    py = e2.bottom + 40
    card = Box(ax, py, aw, 92)
    c.rect(card, fill=t["store"].wash, r=10)
    c.text(ax + 10, py + 20, "Peer card", SMALL, BOLD, t["store"].ink)
    old = "ATTRIBUTE: Diet: Vegetarian"
    c.text(ax + 10, py + 44, old, TINY - 0.5, MONO, t.muted)
    c.line(ax + 10, py + 40, ax + 10 + measure(old, TINY - 0.5, MONO), py + 40, t["stale"].accent, 1.1)
    c.text(ax + 10, py + 64, "ATTRIBUTE: Diet: Pescatarian", TINY - 0.5, MONO, t["store"].ink)
    c.text(ax + 10, py + 82, "rewritten whole by the deduction agent", TINY - 1, ITALIC, t["store"].ink)
    y = max(i9.bottom, i22.bottom, card.bottom) + 34
    heading(c, M, y, W - 2 * M, "TWO DELETE RULES IN HONCHO 3.3.0")
    y += 22
    half = (W - 2 * M - 24) / 2
    left = node(c, M, y, half, "code", "x", "A dream's delete", api="delete_observations(ids)",
                body="Stamps deleted_at on the rows it names. Rows that cite them keep their links and "
                     "the premise text they copied, and stay live.",
                tags=[{"text": "here: two stale rows stay live", "role": "stale"}])
    right = node(c, M + half + 24, y, half, "code", "network", "Removing a session from a scope",
                 api="scope_removal",
                 body="Deletes the session's explicit rows, then every derived row with a deleted "
                      "source, until none is left. One deleted source is enough.",
                 tags=[{"text": "here: would delete all three live rows, the update too", "role": "code"}])
    source_line(c, max(left.bottom, right.bottom) + 24, "From the first run of a Honcho 3.3.0 server on the example")
    return c
