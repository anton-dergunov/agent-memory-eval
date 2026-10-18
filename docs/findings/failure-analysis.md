# Findings: why the answers were wrong

Hand-written, from reading every wrong answer in
[failures.md](failures.md) (generated) next to its result file. The first part
covers full context, retrieval, textual memory, Mem0 and Honcho's two read
paths (39 wrong answers out of 402); Letta and Graphiti, re-run with the
ingestion fixed, have their own sections below.

With 2 to 11 failures per arm these are illustrations of mechanisms, not
rates. A mechanism is worth reporting when it recurs, or when it is specific
to how one system stores or reads memory.

## The causes, and how many answers each explains

| Cause | full-context | retrieval | textual | Mem0 | Honcho chat | Honcho repr | total |
|---|--:|--:|--:|--:|--:|--:|--:|
| A. The question or its answer key is at fault | 3 | 2 | 1 | 3 | 1 | 2 | 12 |
| B. The update was never written to memory | – | – | 1 | 5 | 1 | 2 | 9 |
| C. Both values reached the model; it chose or combined wrongly | 3 | 0 | 0 | 2 | 2 | 0 | 7 |
| D. The value reached the model; it declined to answer | 1 | 0 | 0 | 1 | 5 | 1 | 8 |
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

## B. The update was never written (9 answers)

The loss the knowledge-update questions are designed to find. Mem0 has the
most (5 of its 11), each a revision mentioned in passing that the extraction
step did not turn into a fact, or turned into a fact without the new value:

- `a2f3aa27` (Instagram, 1,250 → "nearing 1,300"): Mem0 stored both "has 1250
  followers" and "is nearing 1300 followers" from the same session; the
  answer kept 1,250.
- `71315a70` (sculpture hours, 5–6 → 10–12), `59524333` (gym, 7 pm → 6 pm),
  `f685340e` (tennis, weekly → every other week): the later sessions'
  revision is not among the stored facts at all.

Honcho's deriver missed `42ec0761` (the user later says they *have* a spare
screwdriver; both read paths answer no) and `41698283` for the
representation (the 70–200 mm lens is stored without its purchase date, so
the 50 mm "recent acquisition" wins). Textual memory dropped one aside
(`07741c44`, where the sneakers are kept).

## C. Both values delivered, and the model chose or combined them wrongly (7)

The answering model had the old and the new value with dates and still got
it wrong. Two patterns:

- **Combining instead of replacing.** Mem0's `f9e8c073`: "attended three
  sessions" and "attended five sessions … last year" come back as two facts,
  and the answer adds them: 3 + 5 = 8.
- **Splitting hairs to keep the old value.** Honcho chat's `6a1eabeb`: 25:50
  is "your general personal best for a 5K, not specifically the charity
  event", so it keeps 27:12. `945e3d21`: three times a week is "for
  work-related stress, not anxiety". Full context's `7401057b` and
  `830ce83f` reason their way back to the first statement.

## D. The value was delivered, and the model declined to answer (8)

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

Specific to textual memory. Its rewrite keeps a running state with dates
("collection of 17 postcards as of August; 25 as of November"), and the
answering model then treats a question about a total as a question about the
change: `01493427` answers 25 − 17 = 8 (key 25), `5831f84d` answers
15 − 12 = 3 (key 15). `2133c1b5` counts the months in Harajuku from the wrong
start. The facts are right; the profile's phrasing invites the subtraction.

## Per-answer assignments

| Arm | A | B | C | D | E |
|---|---|---|---|---|---|
| full-context | 618f13b2, 852ce960, e66b632c | | 7401057b, 830ce83f, ba61f0b9 | a2f3aa27 | |
| retrieval | 618f13b2, 852ce960 | | | | |
| textual | 618f13b2 | 07741c44 | | | 01493427, 5831f84d, 2133c1b5 |
| Mem0 | 618f13b2, 852ce960, e66b632c | 07741c44, 59524333, 71315a70, a2f3aa27, f685340e | f9e8c073, dad224aa | eace081b | |
| Honcho chat | 618f13b2 | 42ec0761 | 6a1eabeb, 945e3d21 | 0ddfec37, 1cea1afa, 4d6b87c8, 830ce83f, dad224aa | |
| Honcho repr | 618f13b2, e66b632c | 42ec0761, 41698283 | | ba61f0b9 | |

## Letta: the agent appends, and does not replace (21 wrong of 67)

Re-run with one agent step per user message, Letta scores 69% (57–78%), up
from 58% when whole sessions were sent at once, and still clearly below the
other memory systems. Fifteen of its 21 wrong answers are "update never
stored", and on 14 of those 15 questions at least three of the five other
arms checked answer correctly (the exception is `618f13b2`, the dataset
question every arm misses).

The mechanism is visible in the memory blocks. While reading a history the
agent edits its `human` block about ten times per question: on average 8.2
`memory_insert` calls and 1.4 `memory_replace` calls (plus 12
`conversation_search` calls). It writes the first value down and, when the
revision arrives later in passing, adds nothing or adds an unrelated detail:

| Question | reference | what the `human` block says | edits while reading |
|---|---|---|---|
| `06db6396` projects since starting painting classes | 5 | "has completed 4 projects so far" | 7 inserts, 0 replaces |
| `1cea1afa` Instagram followers now | 600 | "recently hit 500 followers on Instagram" | 7 inserts, 0 replaces |
| `4b24c848` tops bought from H&M | five | "recently bought three tops there" | 9 inserts, 0 replaces |
| `cc5ded98` daily coding time | about two hours | "practicing Python coding for one hour daily" | 3 inserts, 0 replaces |

At question time the agent trusts its block: it makes 2.3 searches on
average, and answers "4 projects", "500 followers", "three tops", "one hour".
The 46 questions where the agent used `memory_replace` at least once score
36/46 (78%); the 20 where it only appended score 10/20 (50%). The block
holds the old value as current in 16 of 66 questions.

This is the design working as specified: in Letta the model decides what to
remember and when to revise it, so the memory is exactly as good as the
model's judgement of "this replaces something I wrote earlier". With
`gemini-3.1-flash-lite` in that seat, revisions mentioned in passing are often
missed. (In the trace of `06db6396` made while testing the fix, the same agent
did call `memory_replace` and answered 5; across runs the outcome depends on
that one decision.)

Three of the fifteen show the same gap from the other side: with nothing
written down and no search hit, the agent says it has no record (`dad224aa`,
`db467c8c`, and `a2f3aa27`, which adds "I don't have access to your Instagram").

The other six wrong answers:

- `eace081b` (Hawaii): names Oahu correctly, then reads "where am I planning to
  stay" as a hotel and says it has none on record, the same misreading as
  Mem0's answer.
- `6071bd76` (French press): quotes the June ratio and turns the question back
  to the user instead of saying it changed.
- `0f05491a` (Starbucks Gold): the agent answers from its own knowledge that
  the Gold tier no longer exists, rather than from the conversation (120 stars).
- `50635ada` (previous United status): says it has no record of the status
  before Premier Gold, one of the questions about an earlier value.
- `e66b632c`: the dataset question from cause A.
- `184da446`: no answer. In four separate builds Vertex returned a reply with
  `finish_reason=content_filter` and no message while the agent was reading the
  history (the question is about a named book), and Letta stops on such a
  reply. It is counted as wrong.

## Graphiti: the update mostly arrives, and the dates decide (12 wrong of 67)

Re-run with one episode per message, Graphiti scores 82% (71–89%), up from
18% with 8,000-character episodes, in line with Mem0 and Honcho's dialectic
chat. It is still the most expensive system by far: 720 model calls and 2.3
million input tokens per question ($0.64), against 10–40 calls for the others.
The graph holds about 319 edges per question, and closes 4.8 of them as
superseded (0.2 before the fix).

| Cause | answers |
|---|---|
| Update never extracted | 5: `5c40ec5b`, `a2f3aa27`, `affe2881`, `c6853660`, `f685340e` |
| Update extracted, then the dates or invalidation went wrong | 2: `9ea5eabc`, `945e3d21` |
| Update extracted in a different form, not delivered as the answer needs | 2: `59524333`, `c4ea545c` |
| Delivered; the answer combined, computed or hedged wrongly | 3: `2133c1b5`, `4d6b87c8`, `7401057b` |

**Never extracted (5).** As with Mem0, revisions mentioned in passing: the
graph keeps "has spotted 27 different bird species in their local park" with
no later count (32), "consumes one cup of dark roast coffee in the morning"
with no later increase, "plays tennis with friends on a weekly basis" with no
change to every other week, "has 1250 followers" with no 1,300, and only the
first meeting with Alex.

**The temporal model works against the answer (2).** These are the failures
specific to a dated graph, and the most interesting ones for the post:

- `9ea5eabc` (*"Where did I go on my most recent family trip?"*, Paris).
  Graphiti dates a fact by when it became true, not when it was said. "Visited
  Paris with family last month", said in May, became an edge valid from
  2023-04-01; "a recent family trip to Hawaii" became an edge valid from
  2023-05-26, the day it was mentioned. Comparing those dates, Graphiti closed
  the Paris edge as superseded by Hawaii ("valid from 2023-04-01 until
  2023-05-26 [superseded]"), and the answer, reading the validity windows as
  instructed, picked Hawaii. Every other system answered Paris.
- `945e3d21` (yoga for anxiety, twice → three times a week). The old value was
  stored as two near-duplicate edges. The update closed one ("practices yoga
  twice a week to help relax and focus … [superseded]") and left the other
  ("twice a week to feel grounded … on days when experiencing anxiety")
  current; the new edge says the three classes are "to help clear their head",
  so the answer kept twice a week for anxiety.

**Extracted in another form (2).** `59524333`: the change to 6 pm became "has
a gym commitment at 6:00 pm on Tuesday", next to the unchanged Monday,
Wednesday and Friday sessions, so the answer kept 7 pm. `c4ea545c` (*"Do I go
to the gym more frequently than I did previously?"*): only the new schedule is
in the graph, so there is nothing to compare it with.

**Delivered, answered wrongly (3).** `2133c1b5` computes six months from the
studio apartment's first mention although "has been living in Harajuku for 3
months" was delivered; `4d6b87c8` adds two planned titles to the 25 on the
list (27); `7401057b` gets both the one-night and two-night facts and answers
with advice on checking the points balance.

Graphiti misses none of the dataset questions from cause A; it is the only arm
that answers `618f13b2` with the key's "six", and by luck: of the ten facts
retrieved, eight are the assistant's cleaning tips, and only "wore their new
black Converse six times" reached the answer, not the later "four". Its old value
is still presented as current in 14 of 67 questions (21%), the lowest of the
memory systems after textual memory.
