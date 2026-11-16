"""One LongMemEval question's history, session by session, and the trimmed history made from it.

Question 6a1eabeb ("What was my personal best time in the charity 5K run?"), from
data/longmemeval_s_cleaned.json through memeval.data: its 40 sessions in date order, which
kind each is (from the session id), and which 10 the main run kept (memeval.data.question with
seed 0). Token counts are from the answering model's tokenizer
(scripts/replays/token_counts_output.txt).
"""

from __future__ import annotations

from ..kit import BOLD, MEDIUM, SANS, Box, Canvas, W, M, measure, wrap
from ..theme import SUBTITLE, TINY, TITLE as TITLE_SIZE, Theme
from .graphiti_graph import source_line

NAME = "lme-history"
TITLE = "One question's history"
ALT = ("The history of the question 'What was my personal best time in the charity 5K run?' as a "
       "row of 40 sessions from 23 April to 30 May 2023: most are simulated chats about the same "
       "user's other topics, some are public chats from ShareGPT and UltraChat, and two are the "
       "evidence sessions. On 23 May the user mentions a personal best of 27:12 while asking about "
       "soccer; on 30 May, asking about endurance training, they say they hope to beat their "
       "personal best of 25:50. The question is asked on 25 June, and the answer is 25:50. A second "
       "row shows the trimmed history used in the main run: the two evidence sessions and eight "
       "others drawn at random, in date order.")

# (date, kind, kept in the trimmed history), in date order
SESSIONS = [
    ("04-23 08:57", "simulated", True), ("04-24 09:36", "public", False), ("04-27 13:38", "simulated", False),
    ("05-05 03:48", "simulated", False), ("05-05 05:36", "simulated", False), ("05-06 02:58", "simulated", False),
    ("05-07 00:43", "public", True), ("05-07 06:52", "public", True), ("05-08 12:15", "public", False),
    ("05-08 22:55", "public", False), ("05-10 05:13", "public", False), ("05-10 23:14", "public", False),
    ("05-14 09:02", "public", False), ("05-15 01:50", "public", False), ("05-15 05:38", "simulated", False),
    ("05-15 17:17", "simulated", True), ("05-16 19:02", "public", False), ("05-19 04:25", "simulated", False),
    ("05-23 05:18", "simulated", False), ("05-23 13:01", "evidence", True), ("05-23 23:20", "simulated", True),
    ("05-24 01:14", "simulated", False), ("05-25 05:50", "simulated", False), ("05-25 18:13", "simulated", False),
    ("05-25 21:22", "simulated", False), ("05-26 05:56", "simulated", False), ("05-26 16:19", "public", False),
    ("05-27 00:33", "simulated", False), ("05-27 09:35", "public", False), ("05-27 14:54", "simulated", False),
    ("05-28 05:27", "simulated", False), ("05-28 22:04", "public", False), ("05-29 08:11", "public", False),
    ("05-29 09:17", "simulated", False), ("05-29 23:29", "simulated", False), ("05-30 06:09", "simulated", True),
    ("05-30 13:53", "evidence", True), ("05-30 15:35", "simulated", False), ("05-30 18:35", "simulated", True),
    ("05-30 19:15", "public", True),
]
QUOTES = {
    19: ("23 May, evidence session 1", "“I recently set a personal best time in a charity 5K run "
         "with a time of 27:12. Do you have any tips on how to improve my running technique […] on "
         "the soccer field?”"),
    36: ("30 May, evidence session 2", "“I'm training for another charity 5K run […] By the way, "
         "I'm hoping to beat my personal best time of 25:50 this time around.”"),
}
MONTHS = {"04": "Apr", "05": "May"}
KINDS = [("simulated", "simulated chat with the same user, about other things", "person"),
         ("public", "public chat (ShareGPT, UltraChat)", "code"),
         ("evidence", "evidence session", "prompt")]


def _label(date: str) -> str:
    month, rest = date.split("-")
    return f"{int(rest.split()[0])} {MONTHS[month]}"


def _cell(c: Canvas, box: Box, kind: str, theme: Theme) -> None:
    role = dict((k, r) for k, _, r in KINDS)[kind]
    if kind == "evidence":
        c.rect(box, fill=theme[role].accent, stroke=theme[role].accent, r=3)
    else:
        c.rect(box, fill=theme[role].wash, stroke=theme[role].accent, r=3, width=0.7)


def draw(theme: Theme) -> Canvas:
    c = Canvas(W, theme, TITLE, ALT)
    t = theme
    c.text(M, 52, TITLE, TITLE_SIZE, BOLD)
    used = c.paragraph(M, 62, "“What was my personal best time in the charity 5K run?” The "
                       "history holds 40 sessions. Two carry the evidence, and the change is said in "
                       "passing, inside a question about something else.", W - 2 * M, SUBTITLE, SANS, t.muted)
    y = 62 + used + 26
    x = M
    for kind, label, role in KINDS:
        _cell(c, Box(x, y - 11, 14, 14), kind, t)
        x += 20 + c.text(x + 20, y, label, TINY, SANS, t.muted) + 18
    y += 26

    # the quotes, above the first row
    n = len(SESSIONS)
    step = (W - 2 * M) / n
    cell_w = step - 3
    cx = {i: M + i * step + cell_w / 2 for i in range(n)}
    quote_w = 330
    boxes = {19: M + 150, 36: W - M - quote_w}
    qh = max(len(wrap(text, TINY, quote_w - 24, SANS)) for _, text in QUOTES.values()) * TINY * 1.38 + 40
    for i, (head, text) in QUOTES.items():
        bx = boxes[i]
        c.rect(Box(bx, y, quote_w, qh), fill=t["prompt"].wash, stroke=t["prompt"].accent, r=8, width=0.9)
        c.text(bx + 12, y + 20, head, TINY, BOLD, t["prompt"].ink)
        c.paragraph(bx + 12, y + 26, text, quote_w - 24, TINY, SANS, t["prompt"].ink)
    row1 = y + qh + 34
    for i in QUOTES:
        c.line(cx[i], y + qh, cx[i], row1 - 4, t["prompt"].accent, 1.2)

    # row 1: the whole history
    for i, (date, kind, _kept) in enumerate(SESSIONS):
        _cell(c, Box(M + i * step, row1, cell_w, 26), kind, t)
    # row 2: the trimmed history
    row2 = row1 + 132
    kept = [i for i, s in enumerate(SESSIONS) if s[2]]
    gap = 8
    w2 = (W - 2 * M - gap * (len(kept) - 1)) / len(kept)
    for j, i in enumerate(kept):
        bx = M + j * (w2 + gap)
        c.path(f"M {cx[i]:.1f} {row1 + 28:.1f} C {cx[i]:.1f} {row1 + 80:.1f}, {bx + w2 / 2:.1f} "
               f"{row2 - 50:.1f}, {bx + w2 / 2:.1f} {row2 - 2:.1f}", stroke=t.faint, width=0.8)
        date, kind, _ = SESSIONS[i]
        _cell(c, Box(bx, row2, w2, 30), kind, t)
        ink = t.paper if kind == "evidence" else t.ink
        c.text(bx + w2 / 2, row2 + 20, _label(date), TINY - 1, MEDIUM, ink, anchor="middle")
    # drawn after the curves, on the paper colour, so the curves pass behind them
    caption1 = ("The whole history, as LongMemEval's S version has it: 40 sessions, about 108,000 tokens. "
                "The full-history run used it.")
    c.rect(Box(M - 4, row1 + 52, measure(caption1, TINY, MEDIUM) + 8, 20), fill=t.paper, r=0)
    c.text(M, row1 + 66, caption1, TINY, MEDIUM, t.ink)
    for i in (0, 6, 15, 19, 36):
        label = _label(SESSIONS[i][0])
        lw = measure(label, TINY - 1, SANS)
        c.rect(Box(cx[i] - lw / 2 - 3, row1 + 31, lw + 6, 16), fill=t.paper, r=0)
        c.text(cx[i], row1 + 43, label, TINY - 1, SANS, t.faint, anchor="middle")
    c.text(M, row2 + 52, "The trimmed history of the main run: the 2 evidence sessions and 8 others drawn "
           "at random, in date order, about 28,000 tokens.", TINY, MEDIUM, t.ink)

    # the question
    y = row2 + 72
    q = Box(M, y, W - 2 * M, 44)
    c.rect(q, fill=t["person"].wash, stroke=t["person"].accent, r=8, width=0.9)
    c.runs(M + 12, y + 27, [("25 June, the question: ", BOLD, t["person"].ink),
                            ("“What was my personal best time in the charity 5K run?”", SANS, t["person"].ink)],
           TINY)
    c.text(W - M - 12, y + 27, "Answer key: 25:50", TINY, BOLD, t["person"].ink, anchor="end")
    source_line(c, y + 68, "LongMemEval S (cleaned), question 6a1eabeb")
    return c

