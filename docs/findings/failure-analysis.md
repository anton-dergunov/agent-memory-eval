# Findings: why the answers were wrong

Hand-written, from reading every wrong answer in
[failures.md](failures.md) (generated) next to its result file. Covers the six
arms whose runs are final: full context, retrieval, textual memory, Mem0 and
Honcho's two read paths, 39 wrong answers out of 402. Graphiti and Letta are
added when their re-runs finish.

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
