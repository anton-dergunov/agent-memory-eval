# Mem0: an append-only store, dated by day

Hand-written, from the result files in `results/main/mem0/` (every memory
stored, the 20 retrieved for the answer, the answer), read next to the
LongMemEval histories. Mem0's main-run prompts were not logged, but its
replies are in the reply cache, and the full-history run logged its prompts in
full; quotations of the extraction prompt come from there (the same library
version). 67 questions are too few for rates; the mechanisms are the result.

## Summary

Mem0 answers 56 of 67 (84%, 95% interval 73–91%), at 10 model calls and $0.040
per question. It never resolves a conflict: in this release the extraction
prompt's "sole operation is ADD", so an old value and a new one simply both
become memories. That works when both reach the answer with dates that order
them (41 of 45 such questions correct). The 11 failures:

| Cause | answers | questions |
|---|--:|---|
| The revision, or the value asked for, was never extracted from its session | 4 | `59524333`, `71315a70`, `f685340e`, `07741c44` |
| Both values stored, dated the same day, so not ordered | 1 | `a2f3aa27` |
| Both values delivered; the answer added them, or read the new one as a one-off | 2 | `f9e8c073`, `dad224aa` |
| The answer misread the question | 1 | `eace081b` |
| The question or its key is flawed | 3 | `618f13b2`, `852ce960`, `e66b632c` |

What reached the answer, by the probes:

| What the 20 retrieved memories held | questions | correct |
|---|--:|--:|
| new value and old value | 45 | 41 |
| new value only | 7 | 7 |
| old value only | 6 | 0 |
| (no old value in the first evidence session) | 9 | 8 |

## How Mem0 ran here

- Mem0 2.2.1, the open-source library, with a local Qdrant store per question.
- **Each session is one `add()` call** (split above 20 messages). One model
  call extracts memories from the whole batch, with the last messages, a
  summary and similar existing memories as context, and an "Observation Date"
  (the session's day) to resolve "last week".
- **Read:** `search(question)` at the library defaults (top 20, threshold 0.1),
  each memory shown with "(from a chat on YYYY-MM-DD)".
- About 54 memories per question; a third are framed as advice the assistant
  gave ("User was recommended…", "User was provided with…").

The extraction prompt sets the design:

> Your sole operation is ADD: identify every piece of memorable information
> and produce self-contained, contextually rich factual statements.

and, for existing memories:

> If new information in New Messages is semantically equivalent to an Existing
> Memory with no meaningful new context, skip it. When a new memory is related
> to an Existing Memory — same topic, overlapping entities, updated/shifted
> preference… — include the Existing Memory's ID in the new memory's
> "linked_memory_ids" array.

So nothing is closed or replaced. The probe finds the old value still stored in
81% of questions and still presented as current in 37%; the reader is left to
order the two values by their dates.

## The mechanisms

**Session-level extraction drops asides.** One call extracts from up to twenty
messages, and the revision is typically one clause in one message about
something else. The prompt warns against exactly this ("When a conversation
covers multiple topics, extract each one separately. Do not let a dominant
topic cause you to miss secondary information."), and still the clause is
dropped. In `71315a70` the cached reply for the June 17 session holds five
memories — the sunset sculpture, natural materials, fabric, sculpting tools,
techniques for found ocean objects — and none about the "10-12 hours" the user
had put into the ocean sculpture.

**Dates have day resolution.** Each memory carries its session's day. Two
sessions on the same day produce memories with the same date, and the answer
cannot tell which is later (`a2f3aa27`). Honcho, which stamps conclusions to the
minute, answers the same question correctly.

**Phrasing becomes the meaning.** The extraction rewrites what the user said
into a self-contained statement, and that rewrite decides how the answer reads
it: "wake up at 7:30 am" inside a jogging plan became part of a plan for one
Saturday (`dad224aa`); "five sessions… last year" stayed "last year" and read as
a separate episode (`f9e8c073`).

## Every wrong answer

"Other arms" are the seven other arms of the main run.

### The revision, or the value asked for, was never extracted

#### `71315a70` — "How many hours have I spent on my abstract ocean sculpture?" (10-12 hours)

- **2023-06-11, message 3:** "…I've spent around 5-6 hours on it so far."
  Stored: "User is working on an abstract ocean sculpture at home and has spent
  approximately 5-6 hours on it so far."
- **2023-06-17, message 1:** "…I've been spending a lot of time on my abstract
  ocean sculpture lately - I've already put in 10-12 hours, and it's still a
  work in progress." Not stored; the session produced the five memories above.
- **Answer:** "There are no subsequent entries in the provided history that
  update the total time spent… approximately 5-6 hours."
- Other arms: all seven correct.

#### `59524333` — "What time do I usually go to the gym?" (6:00 pm)

- **2023-02-11, message 3:** "…my gym sessions, which I usually go to at 7:00
  pm on Mondays, Wednesdays, and Fridays?" Stored: "User plans to use Todoist
  for their gym sessions, which occur at 7:00 PM on Mondays, Wednesdays, and
  Fridays." The same session also stored the assistant's suggestion: "User was
  recommended to set up gym sessions in Todoist as a recurring task… with a
  reminder set for 6:00 PM."
- **2023-05-30, message 3:** "…before I head to the gym, which is usually at
  6:00 pm." Not stored.
- **Answer:** "The 6:00 PM reminder mentioned in the chat is a notification to
  prepare for the session, not the session time itself… You usually go to the
  gym at 7:00 PM…" The only 6 pm in memory was the assistant's.
- Other arms: 6 of 7 correct (Graphiti also missed it).

#### `f685340e` — "How often do I play tennis with my friends at the local park previously? How often do I play now?" (weekly, now every other week)

- **2023-03-11, message 1:** "…my own weekly tennis sessions with friends."
  Stored: "User plays tennis weekly with friends and plans to play at the local
  park on Sunday, March 12, 2023."
- **2023-07-30, message 1:** "…I'm planning to play tennis with my friends at
  the local park this Sunday, like we do every other week." The session's
  reply (in the cache) stored a jogging route, a yoga studio, swim lessons,
  motivation tips, swimming tips and "User is looking for a new tennis bag…";
  not the frequency.
- **Answer:** "…there is no information in the chat history indicating that you
  have stopped playing tennis or changed the frequency… you **still play
  tennis weekly**."
- Other arms: 5 of 7 correct.

#### `07741c44` — "Where do I initially keep my old sneakers?" (under my bed)

- An earlier-value question. **2023-08-11, message 2:** "…I've been keeping them
  under my bed for storage, and they're starting to smell." The session's
  memories (cached) are about sandals, a cobbler visit, donating dress shoes
  and organising the closet; "under my bed" is not among them.
- **2023-11-30, message 1:** "…get rid of some of my old sneakers in a shoe rack
  in it…" Stored: "…using a shoe rack to store old sneakers to save space."
- **Answer:** "You keep your old sneakers on a shoe rack…" (inside the
  closet). The only location in memory was the later one.
- Other arms: 6 of 7 correct (textual memory also lost it).

### Both stored, the same day

#### `a2f3aa27` — "How many followers do I have on Instagram now?" (1300)

- Both statements were made on 2023-05-25, in sessions at 05:26 ("I've got 1250
  followers on Instagram now") and 09:28 ("I think I'm close to 1300 now").
- Stored: "User has 1250 followers on Instagram…" and "User is nearing 1300
  followers on Instagram…", both "(session 2023-05-25)". Both were retrieved,
  first and second.
- **Answer:** "…where the user had 1250 followers and was approaching 1300…
  your last recorded follower count was 1250 (as of May 25, 2023)."
- With the same date on both, nothing marks one as later. Other arms: 4 of 7
  correct.

### Both delivered, read wrongly

#### `f9e8c073` — "How many sessions of the bereavement support group did I attend?" (five)

- **2023-05-11, message 3:** "I did attend three sessions…" Stored: "User
  attended three sessions of a bereavement support group…"
- **2023-10-30, message 4:** "…the bereavement support group I attended last
  year. I remember attending five sessions…" Stored: "User attended five
  sessions of a bereavement support group last year…"
- **Answer:** "To find the total number of sessions attended, add the two
  amounts together: 3 + 5 = 8." The "last year" in the second memory, faithful
  to the user's words, made the two look like separate episodes.
- Other arms: all seven correct.

#### `dad224aa` — "What time do I wake up on Saturday mornings?" (7:30 am)

- **2023-05-23, message 2:** "I've been waking up around 8:30 am on
  Saturdays…" Stored: "User is establishing a consistent weekend morning
  routine and currently wakes up at 8:30 am on Saturdays to fit in a 30-minute
  jog."
- **2023-05-27, message 2:** "…considering I like to wake up at 7:30 am on
  Saturdays…" Stored inside a plan: "User plans to go for a 30-minute jog… on
  Saturday, May 27, 2023, aiming to start around 8:15-8:30 am after waking up at
  7:30 am and having coffee."
- **Answer:** "While you made a one-time adjustment to wake up at 7:30 am on May
  27, 2023… your established consistent weekend routine… is to wake up at 8:30
  am." The extraction's framing (a routine against a dated plan) decided it.
- Other arms: 5 of 7 correct.

### Misread

#### `eace081b` — "Where am I planning to stay for my birthday trip to Hawaii?" (Oahu)

- Both trips were stored and retrieved: "User is planning a birthday trip to
  Kauai, Hawaii…" (2023-05-22) and "User is planning a birthday trip to Oahu,
  Hawaii, in October 2023…" (2023-05-25).
- **Answer:** "there is no information in the provided history regarding where
  the user is planning to stay for either of these Hawaii trips." It read
  "stay" as accommodation; Letta's answer did the same. Other arms: 6 of 7
  correct.

### The question or its key

- **`618f13b2`** (key: six). Both counts stored: "worn four times as of May 30,
  2023" and "worn six times as of May 29, 2023" (the extraction resolved
  "yesterday"). The answer chose four because that memory names "Chuck Taylor
  All Star", as the question does. Every arm but Graphiti answers four.
- **`852ce960`** (key: $400,000). Only "has received a pre-approval for $350,000
  from Wells Fargo" was stored; the later mention ("remember when I got
  pre-approved for $400,000 from Wells Fargo?") came as a reminiscence inside a
  request about cable TV and was not extracted. The question ("when I got my
  mortgage") is ambiguous; full context and retrieval, which saw both, also
  answered $350,000.
- **`e66b632c`** (key: 27:45). Both stored; the later one says 26:30 "is 1.5
  minutes faster than their previous record", and the answer computed 28:00.

## How the correct answers were reached

- **Both values delivered with different days (41 of 45).** The answer prompt
  orders by date, and Mem0's dates are right to the day: "The most recent data
  point…" is the usual reasoning.
- **Only the new value delivered (7 of 7).** Either the old value was never
  stored, or the search ranked the new memory above it.
- The failures with both delivered are not about storage: a same-day pair, a
  "last year" that split one fact into two, a routine against a plan, and a
  flawed question.

## The full history

On the 25 questions run with the whole history (~48 sessions), Mem0 scores 84%
both times; it stores about 250 memories instead of 54, and retrieval still
picks 20. Its four full-history errors: `4d6b87c8` (25 titles plus two planned
additions, 27, the same arithmetic Graphiti made), `6a1eabeb` (read "hoping to
beat my personal best time of 25:50" as a target and kept 27:12), and two
repeats of trimmed-run failures (`07741c44`, `f9e8c073`).

## Limits

- The main run's prompts were not logged; what the extraction saw is inferred
  from the session text, the cached replies, and the same prompt logged in the
  full-history run.
- One run per question at temperature 0.1.
