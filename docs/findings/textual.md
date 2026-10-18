# Textual memory: a profile that overwrites, and keeps the history in the line

Hand-written, from the replayed model calls of the textual-memory arm (every
profile rewrite, after every session, was reproduced byte for byte from the
cache), read next to the LongMemEval histories and the result files in
`results/main/textual/`. 67 questions are too few for rates; the mechanisms are
the result.

## Summary

Textual memory answers 62 of 67 (93%, 95% interval 84–97%), at 10 model calls
and $0.022 per question. It is the one memory system that resolves conflicts
when it writes, because its prompt tells it to: the probe finds the old value
still presented as current in only 7% of questions, against 21–64% for the
others. Its five failures come from the same rewrite that makes it work:

| Cause | answers | questions |
|---|--:|---|
| The profile line recorded the change as a difference, and the answer subtracted | 2 | `01493427`, `5831f84d` |
| The rewrite's own date arithmetic corrupted the value | 1 | `2133c1b5` |
| The value asked for (an earlier one) was never written | 1 | `07741c44` |
| The question or its key is flawed | 1 | `618f13b2` |

What reached the answer, by the probes: both values in 39 questions (37
correct), only the new one in 18 (16 correct), only the old one in 1 (0), and
9 without an old value in the first evidence session (9 correct).

## How it ran here

One plain-text profile per question, rewritten whole after every session by
one model call, under a 3,000-word cap; the answer reads the whole profile
(about 1,500 tokens). The rewrite prompt is ours, after PersonaMem-v3's textual
memory baseline. Two of its rules matter here:

> When the new conversation changes or contradicts something in the profile,
> replace it with the new information and record that it changed, with dates
> (for example "Now X, since 2023-05-26; previously Y").
>
> Write dates as absolute dates, resolving words like "last week" against the
> conversation's date.

The first rule is why it keeps few stale values: the old one is moved into a
"previously" clause instead of standing next to the new one. It is also why the
profile records a running count with its history ("15 … as of 2023-09-30;
previously 12 as of 2023-08-11"), which answers "what was it before?" well
(7 of 8 earlier-value questions) and invites a subtraction when the question
asks for the current total. The second rule converts "a month now" into a
start date, which is right until the model miscounts.

## Every wrong answer

"Other arms" are the seven other arms of the main run. Each entry follows the
topic's lines in the profile through the ten rewrites.

#### `01493427` — "How many new postcards have I added to my collection since I started collecting again?" (25)

- **2023-08-11, message 4:** "…I've added 17 new ones since I started collecting
  again…" Profile: "The user has recently resumed collecting postcards, having
  acquired 17 new items in the two months prior to 2023-08-11."
- **2023-11-30, message 4:** "…I just realized I've added 25 new postcards to my
  collection since I started collecting again." Profile: "The user has 25
  postcards in their collection as of 2023-11-30 (up from 17 items reported on
  2023-08-11)", and under the changes heading "Postcard collection size: 25
  items as of 2023-11-30; previously 17 items as of 2023-08-11."
- **Answer:** "To find the number of postcards added between these two dates, we
  subtract the initial count from the current count: 25 - 17 = 8."
- Both of the user's numbers were counts "since I started collecting again".
  The rewrite turned them into a collection size that grew from 17 to 25, and
  the question's "how many… have I added" then reads as the difference. Other
  arms: all seven correct.

#### `5831f84d` — "How many Crash Course videos have I watched in the past few weeks?" (15)

- **2023-08-11, message 1:** "…I've already finished 10 videos in the past few
  weeks!" Later in the same session, message 5: "…I just finished my 12th video
  on computer science!" Profile: "The user has completed 12 Crash Course videos
  on computer science (as of 2023-08-11)."
- **2023-09-30, message 1:** "…having watched 15 Crash Course videos in the past
  few weeks." Profile: "The user has completed 15 Crash Course videos on
  computer science (as of 2023-09-30; previously 12 as of 2023-08-11)."
- **Answer:** "To find the number of videos watched in that timeframe, I subtract
  the initial count from the final count: 15 - 12 = 3."
- "In the past few weeks" is a rolling window; the profile made it a running
  total with a previous value. Other arms: all seven correct.

#### `2133c1b5` — "How long have I been living in my current apartment in Harajuku?" (3 months)

- **2023-04-11, message 3:** "…my new studio apartment in Harajuku - it's been a
  month now…" Profile: "The user lives in a studio apartment in the Harajuku
  district of Tokyo, Japan (since March 2023)." The rewrite resolved "a month"
  into a start date, as its rules ask.
- **2023-10-15, message 2:** "…I've been living in Harajuku for 3 months now…"
  Profile: "The user lives in a studio apartment in the Harajuku district of
  Tokyo, Japan. (Now 7 months, since 2023-10-15; previously 3 months as of
  2023-10-15)." The rewrite counted from its own March date, recorded the
  user's three months as the *previous* value, and labelled its computed seven
  months as current.
- **Answer:** counted March to October: "You have been living in your current
  apartment in Harajuku for 7 months."
- The history is itself inconsistent (one month in April, three in October),
  and Graphiti also missed it; but the corruption here is the rewrite's. Other
  arms: 6 of 7 correct.

#### `07741c44` — "Where do I initially keep my old sneakers?" (under my bed)

- **2023-08-11, message 2:** "…I've been keeping them under my bed for storage,
  and they're starting to smell." Profile: "The user plans to take their old
  sneakers to a cobbler for polishing and conditioning during the weekend of
  August 12–13, 2023." The location was not written.
- **2023-11-30, message 1:** "…my old sneakers in a shoe rack in it…" Profile:
  "The user plans to organize their closet and store old sneakers on a shoe rack
  during the weekend of December 2–3, 2023."
- **Answer:** "You currently keep your old sneakers in your closet… You have
  plans to move them to a shoe rack during the weekend of December 2–3, 2023."
- A detail mentioned once in passing, dropped in the first rewrite; Mem0 lost
  the same one. Other arms: 6 of 7 correct.

#### `618f13b2` — "How many times have I worn my new black Converse…?" (key: six)

The rewrite after the 17:45 session wrote "worn six times as of 2023-05-30";
after the 22:16 session it wrote "four times as of 2023-05-30… previously six
times as of 2023-05-30 (Note: The user provided a corrected count of four
during the 2023-05-30 conversation)." The answer followed the correction. The
key holds the earlier value; every arm but Graphiti answers four.

## How the correct answers were reached

The profile usually carries one current value per fact, with the earlier one in
a "previously" clause and both dates, and the answer reads it off. The same
format answers questions about an earlier value (7 of 8: "previously Y" is right
there) and questions that ask for both. The failures are the cases where the
"previously" clause was taken as the start of a subtraction, or where the
rewrite's own arithmetic, not the user's statement, ended up as the current
value.

## The full history

On the 25 questions with the whole history (~48 sessions), textual memory goes
from 96% to 92%, and costs 13 times more (one rewrite per session, of a profile
that grows to about 5,600 tokens). Its two full-history errors: `07741c44` again,
and `830ce83f`, where the profile kept Rachel in Chicago and the answer found no
relocation at all.

## Limits

- One run per question at temperature 0; the replay reproduces it exactly.
- The rewrite prompt is ours; a different wording of the "previously" rule
  would change exactly the two subtraction failures.
