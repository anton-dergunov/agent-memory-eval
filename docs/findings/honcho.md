# Honcho: one store, two read paths

Hand-written, from the result files in `results/main/honcho-chat/` and
`results/main/honcho-repr/`, read next to the LongMemEval histories. Both arms
read the same Honcho store, built once per question; they differ only in how
it is read. Honcho's main-run prompts were not logged, so this reading works
from the stored conclusions, what each read path returned, and the answers.
67 questions are too few for rates; the mechanisms are the result.

## Summary

| Read path | correct | 95% interval | context given to the answer |
|---|--:|---|--:|
| dialectic chat (`peer.chat`) | 58 of 67 (87%) | 76–93% | 77 tokens |
| representation (`peer.representation`) | 62 of 67 (93%) | 84–97% | 935 tokens |

Honcho's deriver turns each user message into explicit conclusions with
minute-level timestamps, about 111 per question; a scheduled "dream" adds
about two deductive and two inductive ones. It does not close old conclusions:
the probe finds the old value still stored in 81% of questions and still
current in 64%, the highest of any system. Both read paths therefore depend on
the answering model to choose the newer value, and they hand it the choice in
different shapes:

- **The representation path** returns the conclusions themselves, each with its
  timestamp ("[2023-05-20 10:21:00] user has a to-watch list consisting of 20
  titles."). The answering model orders them and picks the newer: 51 of 53
  questions where both values were delivered.
- **The dialectic path** asks Honcho's own agent, which searches the
  conclusions and writes a short answer. When it finds two values it often
  writes the conflict up as a question to the user ("Which of these numbers is
  correct?"), and the answering model then declines too. In the 17 questions
  where the dialectic reply framed a contradiction, the chat path was right 12
  times and the representation path, on the same store, 15 times.

The wrong answers:

| Cause | chat | repr | questions |
|---|--:|--:|---|
| The dialectic reply framed the values as a conflict, or as unconfirmed, and the answer declined | 5 | – | `4d6b87c8`, `830ce83f`, `dad224aa`, `1cea1afa`, `0ddfec37` |
| Both values delivered; the answer split hairs to keep the old one | 2 | – | `6a1eabeb`, `945e3d21` |
| Both values delivered; the answer declined or picked by wording | – | 2 | `ba61f0b9`, `41698283` |
| The revision was never derived | 1 | 1 | `42ec0761` |
| The question or its key is flawed | 1 | 2 | `618f13b2`; `618f13b2`, `e66b632c` |
| **wrong answers** | **9** | **5** | |

## How Honcho ran here

- Honcho v3.3.0, self-hosted (API, deriver, Postgres, Redis), every model role
  on `gemini-3.1-flash-lite`.
- Messages are added with their history timestamps; the assistant is a peer
  Honcho does not model, so its turns are context for the user's.
- After the history, one dream is scheduled (Honcho would otherwise start one
  only after 50 new conclusions and an hour idle).
- **chat:** `peer.chat(question)` at the server's default reasoning level; its
  reply goes to the shared answer prompt like any memory.
- **repr:** `peer.representation(search_query=question)`, retrieval over the
  conclusions with no model call.

The conclusions are short and literal: "user has a to-watch list consisting of
25 titles.", "user has 600 followers on Instagram as of 2023-05-28.", "user
practices yoga twice a week." They keep the value; they rarely keep the
context, which matters in two of the failures below.

## Every wrong answer

"Other arms" are the six arms outside Honcho.

### The dialectic reply framed a conflict, and the answer declined (chat only)

#### `4d6b87c8` — "How many titles are currently on my to-watch list?" (25)

- Stored: "[explicit] user has a to-watch list consisting of 20 titles." and
  "…consisting of 25 titles.", timestamped 2023-05-20 10:21 and 2023-05-22 03:29.
- **chat context:** "there is contradictory information regarding the number
  of titles on your to-watch list… I do not have information confirming
  whether your list was updated or if one of these figures was recorded in
  error. Which of these numbers is correct?"
- **chat answer:** "It is not possible to determine the exact number of titles
  currently on your to-watch list. The history contains conflicting
  information (20 titles on May 20 vs. 25 titles on May 22)…"
- **repr answer:** "The most recent record… is from May 22, 2023, which states
  the list consists of 25 titles." Correct.
- Other arms: 5 of 6 correct.

#### `830ce83f` — "Where did Rachel move to after her recent relocation?" (the suburbs)

- Stored: "user's friend Rachel lives in Chicago." (2023-05-24) and "user has a
  friend named Rachel who recently moved to the suburbs." (2023-05-27).
- **chat context:** "Because these statements were recorded only a few days
  apart and appear to conflict, I cannot definitively say where she moved.
  Could you clarify which of these locations is correct?"
- **chat answer:** "…Clarification is required to resolve the discrepancy."
- **repr answer:** "Rachel moved to the suburbs of Chicago." Correct.
- Other arms: 5 of 6 correct.

#### `dad224aa` — "What time do I wake up on Saturday mornings?" (7:30 am)

- **chat context:** "In our conversation on May 23, 2023, you stated that you
  wake up at **8:30 am** on Saturdays. However, in a later conversation on May
  27, 2023, you mentioned waking up at **7:30 am**. Which of these times is
  correct?"
- **chat answer:** "You would need to clarify which time is currently accurate
  for your schedule."
- **repr answer:** "Since the May 27 entry is the most recent observation…
  you wake up at **7:30 am**." Correct.
- Other arms: 4 of 6 correct.

#### `1cea1afa` — "How many Instagram followers do I currently have?" (600)

- The dialectic reply was right: "you had 600 followers on Instagram as of May
  28, 2023."
- **chat answer:** "…you had 600 followers as of May 28, 2023. I do not have any
  updated data to confirm if this number has changed since then, so I cannot
  provide your current follower count…" The answer took "currently" (June 14)
  literally and the judge marked the hedge wrong.
- **repr answer:** "you had **600 followers** as of May 28, 2023." Correct.
- Other arms: 5 of 6 correct.

#### `0ddfec37` — "How many autographed baseballs have I added to my collection in the first three months of collection?" (15)

- Stored: "user has a collection of 15 autographed baseballs." (2023-07-11; the
  user had said "that's 15 autographed baseballs since I started collecting
  three months ago!").
- **chat context:** "there is no explicit information stating exactly how many
  autographed baseballs you added to your collection during your first three
  months… it does not confirm if all 15 were acquired within those specific
  first three months…"
- **chat answer:** "it cannot be determined exactly…"
- **repr answer:** "the 15 baseballs represent the total amount accumulated
  during that initial three-month window." Correct.
- The conclusion had dropped "since I started collecting three months ago",
  and the dialectic agent noticed the gap and refused to fill it. Other arms:
  all six correct.

### Both delivered; the answer split hairs (chat only)

#### `6a1eabeb` — "What was my personal best time in the charity 5K run?" (25:50)

- Stored: "user recently completed a charity 5K run with a personal best time
  of 27:12." and "user has a personal best time of 25:50 for a 5K run." The
  second dropped "charity" from "I'm training for another charity 5K… I'm
  hoping to beat my personal best time of 25:50".
- **chat context:** "Could you clarify which of these is the correct personal
  best time?"
- **chat answer:** "The record from May 30 provides a faster time (25:50), but
  it refers to your general personal best for a 5K run, not specifically the
  charity event… 27:12."
- **repr answer:** "the most recent and fastest recorded time is the correct
  answer." Correct.
- Other arms: all six correct.

#### `945e3d21` — "How often do I attend yoga classes to help with my anxiety?" (three times a week)

- Stored: "user practices yoga twice a week." and "user attends yoga classes
  three times a week."
- **chat context:** "On August 11, 2023, you noted that you were practicing
  yoga **twice a week** to help you feel grounded and centered while
  experiencing anxiety… on November 30, 2023, you mentioned that you attend
  yoga classes **three times a week**, noting that it helps you feel more
  focused and clear-headed while dealing with work-related stress."
- **chat answer:** "The 'three times a week' routine mentioned on November 30,
  2023, is associated with 'work-related stress,' not anxiety… twice a week."
  The dialectic agent supplied the distinction from the surrounding
  conclusions; Graphiti's answer drew the same line.
- **repr answer:** "you attend yoga classes **three times a week**." Correct.
- Other arms: 5 of 6 correct.

### Both delivered; the representation answer went wrong (repr only)

#### `ba61f0b9` — "How many women are on the team led by my former manager Rachel?" (6)

- Stored: "half of the team led by Rachel are women", "there are 5 women on
  Rachel's team" (2023-01-18) and "a team managed by Rachel that consisted of 6
  women out of 10 people" (2023-07-20).
- **repr answer:** "Because the user has provided two different figures for the
  same team, there is no single definitive answer… The information provided is
  contradictory." The one refusal on this path.
- **chat answer:** "the figure of 6 women is the most accurate…" Correct.
- Other arms: 5 of 6 correct.

#### `41698283` — "What type of camera lens did I purchase most recently?" (a 70-200mm zoom lens)

- Stored: "user recently acquired a 50mm prime lens." (2023-03-11) and "user owns
  a 70-200mm zoom lens." (2023-08-30). The user's "my new 70-200mm zoom lens"
  became plain ownership.
- **repr answer:** "the 50mm prime lens is the only lens explicitly identified as
  a recent acquisition… (Note: While you also own a 70-200mm zoom lens, the logs
  do not specify a purchase date for it…)"
- **chat answer:** compared the two dates and answered 70-200mm. Correct.
- Other arms: 5 of 6 correct.

### The revision was never derived (both paths)

#### `42ec0761` — "Do I have a spare screwdriver for opening up my laptop?" (yes)

- **2023-08-11, message 3:** "…I realized I misplaced the small screwdriver I use
  for that. I'll need to pick one up next time I'm out." Derived as a plan to buy
  one.
- **2023-08-15, message 4:** "I actually have a spare screwdriver that I picked
  up when I organized my computer desk a while back, so I'm all set there."
  No conclusion about it was stored.
- **chat answer:** "an intention is not confirmation of a completed action…
  No, there is no information confirming that you have a spare screwdriver…"
  **repr answer:** "…there is no evidence that you currently have a spare
  screwdriver."
- Other arms: all six correct.

### The question or its key

- **`618f13b2`** (key: six). Both counts stored with their times (17:49 and
  22:26 on 2023-05-30); both paths chose the later four, as every arm but
  Graphiti did. The dialectic reply asked for clarification, and this time the
  answer resolved it by recency.
- **`e66b632c`** (key: 27:45), repr only. Both stored; the later conclusion reads
  "user previously completed a 5K charity run with a personal best time of 26
  minutes and 30 seconds", and the answer took "previously" literally. The chat
  path answered 27:45.

## How the correct answers were reached

- **Representation:** in 51 of the 53 questions where both values were
  delivered, the answer ordered the timestamped conclusions and took the later
  one; the minute-level timestamps also order same-day statements, which is
  how it answers `a2f3aa27` (1250 at 05:28, "close to 1300" at 09:32) where Mem0,
  dated by day, could not.
- **Dialectic chat:** when the dialectic reply states one value, the answer
  follows it (46 of 50). Its replies are a few sentences, the shortest context of
  any arm, which is enough when the agent commits to an answer.
- The two paths fail on almost disjoint questions: only `618f13b2` and
  `42ec0761` are wrong on both.

## Limits

- Honcho's prompts were not logged in the main run; the dialectic agent's
  searches are known only through its final reply.
- One run per question at the server's defaults.
