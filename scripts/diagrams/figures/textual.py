"""Textual memory: an LLM rewrites one text profile after each session; all of it is read.

Every example below is from the committed run of notebooks/textual.ipynb, shortened to fit:
the profile after session 2 (section 2), the cost table (section 4), the answer (section 3).
"""

from __future__ import annotations

from ..kit import (BOLD, ITALIC, MEDIUM, SANS, Box, Canvas, W, answer_card, arrow, bubble, column, footer,
                   frame, heading, node, panel, prompt_card, wrap)
from ..theme import SMALL, TINY, Theme

NAME = "textual"
TITLE = "Textual memory"
ALT = ("Textual memory's architecture, with the running example. Writing: after each session, "
       "one LLM call reads the current profile and the new session and writes the whole profile "
       "again. Memory: one text profile under four headings, 153 words after two sessions; the "
       "diet line now says pescatarian and keeps the old diet as 'previously'. Reading: no "
       "search; the whole profile goes into the prompt, and the answer covers every constraint.")

SESSION_1 = ("“I've been strictly vegetarian for eight years, and I have a severe peanut "
             "allergy … Indian, usually.”")
SESSION_2 = ("“So I'm pescatarian now, not vegetarian … I moved to Kreuzberg in May … Lena "
             "can't eat shellfish, and Jonas is coeliac.”")
QUESTION = ("“My sister and her partner are in town tonight. Book the three of us somewhere for "
            "dinner — you know what we can and can't eat.”")

# The profile after session 2, under its four headings, each line cut short. The second field
# marks the line the rewrite changed and kept the history of.
PROFILE = [
    ("Personal facts", [
        ("Pescatarian since June 2026; previously vegetarian", "changed"),
        ("Severe, anaphylactic peanut allergy", None),
        ("Sister Lena; her partner Jonas", None),
        ("Lives in Kreuzberg since May 2026", None),
    ]),
    ("Preferences and habits", [
        ("Indian food, paneer dishes", None),
        ("At most 40 € a head", None),
        ("Guests: Lena no shellfish, Jonas coeliac", None),
    ]),
    ("Ongoing situations and plans", [
        ("Dinner for Lena and Jonas, autumn 2026", None),
    ]),
    ("Changes over time", [
        ("Now pescatarian since 2026-06-20; previously vegetarian", None),
        ("Moved to Kreuzberg 2026-05-01", None),
    ]),
]

ANSWER = ("Booked Chutnify in Kreuzberg: Indian with paneer, within 40 € a head, with the "
          "peanut allergy, Lena's shellfish and Jonas's coeliac disease noted.")
NEEDS = [("diet", "yes"), ("peanuts", "yes"), ("shellfish", "yes"), ("gluten", "yes"),
         ("cuisine", "yes"), ("area", "yes")]


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, "Textual memory: one profile, rewritten", ALT)
    t = theme
    top = frame(
        c, "Textual memory",
        "The memory is one plain-text profile of the user. An LLM rewrites all of it after each "
        "session; the whole profile goes into every prompt.")

    wx, ww = column("write")
    b1 = bubble(c, wx, top, ww, "March · session 1", SESSION_1)
    b2 = bubble(c, wx, b1.bottom + 14, ww, "July · session 2", SESSION_2)
    rx, rw = column("read")
    q = bubble(c, rx, top, rw, "September · session 3", QUESTION, target=True)

    row = max(b2.bottom, q.bottom) + 34
    rewriter = node(
        c, wx, row, ww, "llm", "sparkles", "Rewriter",
        body="Reads the current profile and the new session, and writes the whole profile "
             "again, under a 3,000-word cap.",
        tags=[{"text": "1 LLM call per session", "role": "llm", "icon": "sparkles"}])
    nothing = node(
        c, rx, row, rw, "code", "circle-dashed", "No search", dashed=True, badge=False,
        body="Nothing is selected: the whole profile goes into the prompt, every time.",
        tags=[{"text": "no LLM call, no embedding", "role": "code", "icon": "code-xml"}])
    arrow(c, [(wx + 30, b2.bottom + 4), (wx + 30, rewriter.y)], t["person"].accent)
    arrow(c, [(rx + 30, q.bottom + 4), (rx + 30, nothing.y)], t["person"].accent)

    sx, sw = column("store")
    store = _profile(c, sx, top, sw)

    y_write = rewriter.y + 34
    arrow(c, [(rewriter.right, y_write), (store.x, y_write)], t.ink, label="the new\nprofile")
    y_back = rewriter.y + 92
    arrow(c, [(store.x, y_back), (rewriter.right, y_back)], t.muted, dashed=True, label="the current\nprofile")
    y_read = nothing.y + 34
    arrow(c, [(store.right, y_read), (nothing.x, y_read)], t.muted, dashed=True, label="all of it")

    band = max(rewriter.bottom, nothing.bottom, store.bottom) + 30
    heading(c, wx, band, W - 2 * wx, "USE", "what the answering model is given, and what it replies")
    px = sx
    prompt = prompt_card(
        c, px, band + 22, W - wx - px, "You are a booking assistant. Be brief and concrete.",
        "what you remember about this user",
        "The whole profile above, under its four headings: 153 words. The answer call read "
        "365 tokens in all.", QUESTION)
    arrow(c, [(nothing.cx, nothing.bottom), (nothing.cx, prompt.y)], t.muted, dashed=True)
    answer = answer_card(c, wx, band + 22, ww, ANSWER, NEEDS)
    arrow(c, [(prompt.x, band + 22 + 13), (answer.right + 4, band + 22 + 13)], t["prompt"].accent)

    footer(c, max(prompt.bottom, answer.bottom) + 24, "Example from notebooks/textual.ipynb, shortened")
    return c


def _profile(c: Canvas, x: float, y: float, w: float) -> Box:
    """The profile as a page, with the March version behind it: each rewrite replaces the page."""
    t = c.theme
    s = t["store"]
    page_w = w - 30
    # measure the page first
    rows, h = [], 0.0
    for heading_text, lines in PROFILE:
        rows.append((heading_text, None, True, h))
        h += 20
        for text, mark in lines:
            for i, line in enumerate(wrap(text, TINY, page_w - 36)):
                rows.append((line, mark, i == 0, h))
                h += 17
            h += 2
        h += 6
    page_h = h + 16
    box = panel(c, x, y, w, 48 + 16 + page_h + 32, "file-text", "Text profile", "153 words")
    # the March page, replaced, peeking out behind
    old = Box(x + 20, y + 48, w - 34, page_h)
    c.rect(old, fill=t.card, stroke=t.line, r=6, opacity=0.55)
    c.text(old.right - 8, old.y + 13, "March: 91 words, replaced", TINY - 1.5, ITALIC, t.muted, anchor="end")
    page = Box(x + 10, y + 48 + 18, page_w, page_h)
    c.rect(page, fill=t.card, stroke=t.line, r=6)
    headings = {name for name, _ in PROFILE}
    for text, mark, first, ry in rows:
        ty = page.y + 12 + ry
        if mark is None and first and text in headings:
            c.text(page.x + 10, ty + 11, text, TINY, BOLD, s.ink)
            continue
        if mark:
            c.rect(Box(page.x + 5, ty, page.w - 10, 17), fill=t["both"].wash, r=3)
        if first:
            c.text(page.x + 18, ty + 12, "·", TINY, BOLD, t.muted)
        c.text(page.x + 26, ty + 12, text, TINY, MEDIUM if mark else SANS, t["both"].ink if mark else t.ink)
    c.text(x + 12, box.bottom - 12, "July: rewritten whole, 153 of 3,000 words", TINY, SANS, s.ink)
    return box
