# Findings: why the answers were wrong

Hand-written, from reading every wrong answer in
[failures.md](failures.md) (generated) next to its result file. The first part
covers full context, retrieval, textual memory, Mem0 and Honcho's two read
paths (39 wrong answers out of 402); Letta and Graphiti, re-run with the
ingestion fixed, have their own sections below.

This is the overview. Each system has its own, more detailed account, which
follows every wrong answer through the model calls and also says how the right
answers were reached: [letta.md](letta.md), [graphiti.md](graphiti.md),
[mem0.md](mem0.md), [honcho.md](honcho.md), [textual.md](textual.md),
[full-context.md](full-context.md) and [retrieval.md](retrieval.md). Where
those accounts reclassified an answer, the counts here follow them.

With 2 to 11 failures per arm these are illustrations of mechanisms, not
rates. A mechanism is worth reporting when it recurs, or when it is specific
to how one system stores or reads memory.

## The causes, and how many answers each explains

| Cause | full-context | retrieval | textual | Mem0 | Honcho chat | Honcho repr | total |
|---|--:|--:|--:|--:|--:|--:|--:|
| A. The question or its answer key is at fault | 3 | 2 | 1 | 3 | 1 | 2 | 12 |
| B. The update was never written to memory | – | – | 1 | 4 | 1 | 1 | 7 |
| C. Both values reached the model; it chose or combined wrongly | 4 | 0 | 0 | 3 | 2 | 1 | 10 |
| D. The value reached the model; it declined to answer | 0 | 0 | 0 | 1 | 5 | 1 | 7 |
| E. Arithmetic over dated values in a profile | 0 | 0 | 3 | 0 | 0 | 0 | 3 |
| **wrong answers** | **7** | **2** | **5** | **11** | **9** | **5** | **39** |

(Per-answer assignments are listed at the end. Where two causes apply, the
earlier one in the list is used.)

## A. The question or its answer key (12 answers, 3 questions)

Three questions account for almost a third of all wrong answers among these
arms, and in each the dataset is at least as much at fault as the systems:

- **`618f13b2`** *"How many times have I worn my new black Converse…?"* — every
  one of the six arms answers "four". Two sessions on the same day say six
  (17:45) and then four (22:16); the answer key says six, the earlier value.
  This is the dataset quirk noted in the run's status: some trimmed sessions
  are dated hours apart on one day, and here the order contradicts the key.
- **`852ce960`** *"What was the amount I was pre-approved for when I got my
  mortgage from Wells Fargo?"* — key $400,000 (the later figure). Full context
  and retrieval both see $350,000 and $400,000 and read "when I got my
  mortgage" as asking for the first; full context even says so.
- **`e66b632c`** *"What was my previous personal best time…?"* — key 27:45.
  A later session says the new best is 26:30, "about a minute and a half"
  faster than before, which makes the previous one about 28:00; the systems
  answer 28:00 or 26:30.

Leaving these three out moves every arm up by a few points and changes no
conclusion. The post should say they exist rather than quietly drop them.

## B. The update was never written (7 answers)

The loss the knowledge-update questions are designed to find. Mem0 has the
most (4 of its 11), each a revision mentioned in passing that the extraction
step did not turn into a fact:

- `71315a70` (sculpture hours, 5–6 → 10–12), `59524333` (gym, 7 pm → 6 pm),
  `f685340e` (tennis, weekly → every other week): the later sessions'
  revision is not among the stored facts at all.
- `07741c44` (where the old sneakers were first kept): the earlier location,
  which the question asks for, was never stored.

Honcho's deriver missed `42ec0761` (the user later says they *have* a spare
screwdriver; both read paths answer no). Textual memory dropped one aside
(`07741c44`, the same question).

## C. Both values delivered, and the model chose or combined them wrongly (10)

The answering model had the old and the new value with dates and still got
it wrong. Four patterns:

- **Combining instead of replacing.** Mem0's `f9e8c073`: "attended three
  sessions" and "attended five sessions … last year" come back as two facts,
  and the answer adds them: 3 + 5 = 8.
- **Nothing to order them by.** Mem0's `a2f3aa27` (Instagram, 1,250 →
  "close to 1300"): both facts were stored, from two sessions on the same day,
  and Mem0 dates memories by day, so both carry 2023-05-25; the answer kept
  1,250. Full context's `a2f3aa27` took the later statement but kept the
  user's hedge ("you were nearing 1300 followers"), which the judge did not
  accept for 1300.
- **Picking by wording.** Honcho representation's `41698283`: the 50 mm lens
  was stored as a "recent acquisition" and the "new 70-200mm zoom lens" as
  plain ownership, and the answer took the lens called recent.
- **Splitting hairs to keep the old value.** Honcho chat's `6a1eabeb`: 25:50
  is "your general personal best for a 5K run, not specifically the charity
  event", so it keeps 27:12. `945e3d21`: three times a week "is associated
  with 'work-related stress,' not anxiety". Full context's `7401057b` and
  `830ce83f` reason their way back to the first statement.

## D. The value was delivered, and the model declined to answer (7)

The most system-specific pattern here: **five of Honcho chat's nine wrong
answers are refusals**, all on questions where both values reached the
answer:

- `4d6b87c8`: "conflicting information (20 titles on May 20 vs. 25 titles on
  May 22) with no clarification on which figure is correct";
- `830ce83f`: "clarification is required to resolve the discrepancy";
- `dad224aa`: "you would need to clarify which time is currently accurate";
- `1cea1afa`: "you had 600 followers as of May 28 … I cannot provide your
  current follower count";
- `0ddfec37`: "it cannot be determined exactly".

Honcho's dialectic agent hands the answering model a summary that frames the
two values as a contradiction, and the answer declines to resolve it. The
representation read path, given the same conclusions as dated lines, refuses
once (`ba61f0b9`). The same store scores 93% through one read path and 87%
through the other, and this is most of the difference.

Mem0's one case is a misreading rather than a conflict: for `eace081b`
(*"Where am I planning to stay for my birthday trip to Hawaii?"*) it delivered
both the Kauai plan and the later Oahu plan, and the answer took "stay" to
mean a hotel and said there was no information.

## E. Arithmetic over dated values in the profile (3)

Specific to textual memory. Its rewrite keeps a running state with its history
("The user has 25 postcards in their collection as of 2023-11-30 (up from 17
items reported on 2023-08-11)"), and the answering model then treats a
question about a total as a question about the change: `01493427` answers 25 − 17 = 8 (key 25), `5831f84d` answers
15 − 12 = 3 (key 15). The facts are right; the profile's phrasing invites the
subtraction. In `2133c1b5` the rewrite did the arithmetic itself: it counted
seven months from its own March start date, labelled that as current, and kept
the user's "3 months" as the previous value.

## Per-answer assignments

| Arm | A | B | C | D | E |
|---|---|---|---|---|---|
| full-context | 618f13b2, 852ce960, e66b632c | | 7401057b, 830ce83f, ba61f0b9, a2f3aa27 | | |
| retrieval | 618f13b2, 852ce960 | | | | |
| textual | 618f13b2 | 07741c44 | | | 01493427, 5831f84d, 2133c1b5 |
| Mem0 | 618f13b2, 852ce960, e66b632c | 07741c44, 59524333, 71315a70, f685340e | f9e8c073, dad224aa, a2f3aa27 | eace081b | |
| Honcho chat | 618f13b2 | 42ec0761 | 6a1eabeb, 945e3d21 | 0ddfec37, 1cea1afa, 4d6b87c8, 830ce83f, dad224aa | |
| Honcho repr | 618f13b2, e66b632c | 42ec0761 | 41698283 | ba61f0b9 | |

## Letta: the revision is not written, and the search cannot find it (21 wrong of 67)

Re-run with one agent step per user message, Letta scores 69% (57–78%), up
from 58% when whole sessions were sent at once, and still clearly below the
other memory systems. The question-by-question account, from the logged model
calls, is in [letta.md](letta.md); in short, three failures in a row:

1. **The revision is not written down.** At the user message carrying the new
   value, the agent recorded it in 31 of 64 questions. Inserting it worked as
   well as replacing (11 of 12 correct against 16 of 19), so the problem is not
   appending instead of replacing: in the other 33 it made no edit for the new
   value, and in 18 of those its own reply named it ("Congratulations on
   hitting 600 followers!").
2. **The search cannot find what was not written.** On a self-hosted Letta
   0.16.8, `conversation_search` is a literal phrase match returning the five
   newest matches. The agent searches with paraphrases ("painting projects
   completed"), and 97 of its 146 searches at answer time returned nothing;
   short queries match, but the question itself, the agent's replies and the
   echoes of its memory edits fill the five places.
3. **A stale block is trusted.** In six wrong answers the block still held the
   first value ("has completed 4 projects so far", "recently hit 500 followers
   on Instagram", "recently bought three tops there"), the searches came back
   empty, and the agent answered from the block.

| Cause | answers |
|---|---|
| Revision never written; the block held the earlier value | 6: `06db6396`, `1cea1afa`, `4b24c848`, `cc5ded98`, `ce6d2d27`, `ed4ddc30` |
| Revision never written; nothing usable in the block or the search | 5: `26bdc477`, `6a27ffc2`, `a2f3aa27`, `dad224aa`, `db467c8c` |
| Revision never written; a search returned it, the answer did not use it | 3: `41698283`, `6071bd76`, `f685340e` |
| The agent replaced the earlier value the question asks for | 2: `031748ae`, `50635ada` |
| The agent answered from its own knowledge (`0f05491a`, Starbucks Gold) | 1 |
| The agent misread "where am I planning to stay" as a hotel (`eace081b`) | 1 |
| The question or its key is flawed | 2: `618f13b2`, `e66b632c` |
| No answer: the provider's content filter stopped the build (`184da446`) | 1 |

The probe counts 15 wrong answers with the value asked for not stored; the
call-level count of 14 differs because the probe also counts `031748ae` (the
earlier value overwritten) and `618f13b2` (the key's value), and misses
`6071bd76` (it found no old value to check). The questions where the agent used `memory_replace` at least once
score 36/46 (78%) and those where it only appended 10/20 (50%), but that split
tracks how actively the agent wrote, not the kind of edit.

**With an instructed persona (`letta-persona`, 7 wrong of 67).** The agent's
persona had been Letta's blank starter text. Three lines added to it (write
the message's date on every fact, update the line when a value changes and
keep the earlier value, search with one or two words) raise the revisions
written at the message from 31 to 57 of 64, and the score to 90% (80–95%).
The seven left:

| Cause | answers |
|---|---|
| Revision never written; the search returned only echoes of the agent's own edits | 1: `9ea5eabc` |
| Revision written as a dated plan, not as the new frequency | 1: `f685340e` |
| Both values in memory with dates; the answer reasoned wrongly | 2: `5c40ec5b` (counted the first meeting too), `6071bd76` (5 oz after 6 oz called "more water") |
| A stated intention ("I'm definitely going to add…") written as an update, 25 → 27 | 1: `4d6b87c8` |
| The question or its key is flawed | 1: `618f13b2` |
| No answer: the provider's content filter stopped the build | 1: `184da446` |

The persona was written after this analysis, on the same questions; see
[letta.md](letta.md#the-persona-re-run-letta-persona).

## Graphiti: the update mostly arrives, and the dates decide (12 wrong of 67)

Re-run with one episode per message, Graphiti scores 82% (71–89%), up from
18% with 8,000-character episodes, in line with Mem0 and Honcho's dialectic
chat. It is still the most expensive system by far: 720 model calls and 2.3
million input tokens per question ($0.64), against 10–40 calls for the others.
The graph holds about 319 edges per question, and closes 4.8 of them as
superseded (0.2 before the fix).

| Cause | answers |
|---|---|
| Update never extracted | 6: `5c40ec5b`, `a2f3aa27`, `affe2881`, `c4ea545c`, `c6853660`, `f685340e` |
| Update extracted, then the dates or invalidation went wrong | 2: `9ea5eabc`, `945e3d21` |
| Update extracted in a form that does not contradict the old fact | 1: `59524333` |
| Delivered; the answer combined, computed or hedged wrongly | 3: `2133c1b5`, `4d6b87c8`, `7401057b` |

**Never extracted (6).** As with Mem0, revisions mentioned in passing: the
graph keeps "has spotted 27 different bird species in their local park" with
no later count (32), "consumes one cup of dark roast coffee in the morning"
with no later increase, "plays tennis with friends on a weekly basis" with no
change to every other week, "has 1250 followers" with no 1,300, only the
first meeting with Alex, and the old gym schedule (Tuesdays, Thursdays and
Saturdays) with no "four times a week", so `c4ea545c` (*"Do I go to the gym
more frequently than I did previously?"*) had nothing to compare.

**The temporal model works against the answer (2).** These are the failures
specific to a dated graph, and the most interesting ones for the post:

- `9ea5eabc` (*"Where did I go on my most recent family trip?"*, Paris).
  Graphiti dates a fact by when it became true, not when it was said. "The user
  visited Paris with their family last month", said in May, became an edge valid from
  2023-04-01; "a recent family trip to Hawaii" became an edge valid from
  2023-05-26, the day it was mentioned. Comparing those dates, Graphiti closed
  the Paris edge as superseded by Hawaii ("(valid from 2023-04-01 until
  2023-05-26) [superseded]"), and the answer, reading the validity windows as
  instructed, picked Hawaii. Every other system answered Paris.
- `945e3d21` (yoga for anxiety, twice → three times a week). The old value was
  stored as two near-duplicate edges. The update closed one ("practices yoga
  twice a week to help relax and focus … [superseded]") and left the other
  ("twice a week to feel grounded … on days when experiencing anxiety")
  current; the new edge says the three classes are "to help clear their head",
  so the answer kept twice a week for anxiety.

**Extracted in another form (1).** `59524333`: the change to 6 pm became "has
a gym commitment at 6:00 pm on Tuesday", next to the unchanged Monday,
Wednesday and Friday sessions, so the answer kept 7 pm.

**Delivered, answered wrongly (3).** `2133c1b5` computes six months from the
studio apartment's first mention although "has been living in Harajuku for 3
months" was delivered; `4d6b87c8` adds two planned titles to the 25 on the
list (27); `7401057b` gets both the one-night and two-night facts and answers
with advice on checking the points balance.

Graphiti misses none of the dataset questions from cause A; it is the only arm
that answers `618f13b2` with the key's "six", and by luck: of the ten facts
retrieved, seven are the assistant's cleaning tips, and only "wore their new
black Converse six times" reached the answer, not the later "four". Its old value
is still presented as current in 14 of 67 questions (21%), the lowest of the
memory systems after textual memory.
