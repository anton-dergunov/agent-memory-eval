# Graphiti: where the dated graph helps and where it fails

Hand-written, from the recorded model calls of the Graphiti run in
`results/main/graphiti/` (one episode per message), read next to the
LongMemEval histories and the source of graphiti-core 0.31.1. Every call the
library made was logged with its prompt and reply: the entities and facts
extracted from each message, with their dates, and every decision on whether
a new fact duplicates or contradicts an existing one. So for each question one
can follow the revised fact from the message that states it, through
extraction and resolution, into the graph and into the ten facts retrieved at
question time.

67 questions are too few to estimate rates; the counts describe this run, and
the mechanisms are the result.

## Summary

Graphiti answers 55 of 67 (82%, 95% interval 71–89%), in the same band as Mem0
and Honcho's dialectic chat, at 720 model calls and $0.64 per question, by far
the most expensive arm. When its design works it works well: in the 26
questions where the new fact reached the answer and the old one reached it
marked `[superseded]`, the answer was right every time. The 12 failures come
from four places:

1. **The revision was never extracted** (6). The extraction prompt keeps the
   subject of a message and drops asides: "brings my total species count to
   32" produced facts about sunflower seeds, suet and the Northern Flicker but
   no count; "like we do every other week" became "planning to play tennis…
   this coming Sunday". With no fact carrying the new value there was nothing
   to supersede the old one.
2. **The revision was extracted in a form that does not contradict the old
   fact** (1). "Head to the gym, which is usually at 6:00 pm" became "a gym
   commitment at 6:00 pm on Tuesday", next to the unchanged
   Monday/Wednesday/Friday 7 pm.
3. **The resolution went wrong** (2). Once because of how dates work: a fact is
   dated by when it became true, which for "a recent family trip to Hawaii" is
   the day it was mentioned and for Paris ("we just went there as a family
   last month") is a month earlier, so Graphiti closed Paris as superseded by
   Hawaii. Once because the
   old value was stored twice and only one copy was closed.
4. **Both values were delivered and the answer still went wrong** (3): it
   computed a duration from the wrong fact, added planned titles to a count,
   and declined to give a number.

| Cause | answers | questions |
|---|--:|---|
| Revision never extracted as a fact carrying the new value | 6 | `5c40ec5b`, `a2f3aa27`, `affe2881`, `c4ea545c`, `c6853660`, `f685340e` |
| Revision extracted in a form that does not contradict the old fact | 1 | `59524333` |
| Resolution: the date logic closed the new fact instead of the old | 1 | `9ea5eabc` |
| Resolution: the old value was stored twice, one copy closed | 1 | `945e3d21` |
| Revision delivered; the answer computed, added or hedged wrongly | 3 | `2133c1b5`, `4d6b87c8`, `7401057b` |

What reached the answer, for every question:

| What the ten retrieved facts held | questions | correct |
|---|--:|--:|
| the new fact, and the old one marked `[superseded]` | 26 | 26 |
| the new fact, and the old one still current | 13 | 10 |
| the new fact, and no old one | 12 | 10 |
| the new fact only as a closed edge | 1 | 0 |
| no fact with the new value | 4 | 0 |
| (questions about an earlier value, or both values) | 11 | 9 |
| **total** | **67** | **55** |

## How Graphiti ran here

- **Every message is one episode**, "user: …" or "assistant: …", as
  Graphiti's own chat examples add a conversation, with the session's date as
  its reference time (one minute apart within a session). The histories hold
  7,167 distinct messages, about 107 per question, half of them the
  assistant's.
- **For each episode** Graphiti extracts entities, resolves them against the
  entities already in the graph, extracts facts between them (each with a
  `valid_at` and an optional `invalid_at`), and then, for every new fact, asks
  the model whether it duplicates or contradicts facts already stored. A
  contradicted fact gets an `invalid_at` and is shown as superseded.
- **At question time** `graphiti.search(question)` with the library defaults:
  hybrid BM25 and embedding search over facts, fused by reciprocal rank, ten
  results. Each fact is shown to the shared answer prompt with its validity
  window.
- No custom entity types; every setting is the library default.

Where the 720 calls per question go:

| Step | calls | per question |
|---|--:|--:|
| Does this new fact duplicate or contradict existing ones? | 25,122 | 375 |
| Extract entities from the message | 7,980 | 119 |
| Extract facts from the message | 7,974 | 119 |
| Resolve entities against existing ones | 5,451 | 81 |
| Summarise entities | 1,675 | 25 |
| Extract dates for a fact | 43 | 0.6 |

Most of that work is spent on the assistant's text. Assistant messages produced
17,211 of the 22,702 facts extracted (76%), 4.8 per message against 1.5 per user
message: "The assistant recommends using hand soap to clean black Converse",
"The Hilton Lake Las Vegas Resort typically requires approximately 40,000
points for a standard room reward night". Each of those facts then gets its own
contradiction check. Of the 670 facts retrieved over all questions, 133 are
about the assistant or its advice and 127 are general facts with no user in
them; 410 are about the user.

## 1. Extraction: a revision mentioned in passing becomes no fact

The fact-extraction prompt asks for "fact triples" between the entities found
in the current message and tells the model to preserve "quantities, counts…
specific items". The entity prompt, which runs first, says "When in doubt, do
not extract the entity" and tells the model to never extract "Generic
event/activity nouns", "Abstract concepts", "Bare generic objects". In practice
the model extracts what the message is about and lets the aside go:

| Question | the revision, as said | facts extracted from that message |
|---|---|---|
| `affe2881` | "…I just saw a Northern Flicker in my local park last weekend, which brings my total species count to 32." | "plans to bring sunflower seeds to the park to attract woodpeckers"; "plans to bring suet…"; "The Northern Flicker is a species of woodpecker"; "observed a Northern Flicker in their local park last weekend" |
| `a2f3aa27` | "…I've been meaning to check my current follower count - I think I'm close to 1300 now." | "is actively creating content for their Instagram account"; "has a target audience based in the US" (and the UK, and Australia) |
| `5c40ec5b` | "…I've got a friend Alex from there who I met at a music festival, and we've met up twice already…" | "is friends with Alex, whom they met at a music festival"; "Alex is from Germany"; "met their friend Alex at a music festival" |
| `f685340e` | "…I'm planning to play tennis with my friends at the local park this Sunday, like we do every other week." | "is planning to play tennis with the user's friends at the local park this coming Sunday"; "will play tennis at the local park with friends this Sunday" |
| `c4ea545c` | "…since I've been consistent with my gym routine - four times a week, actually." | "plans to meal prep healthy dinner recipes on Sunday"; "plans to have a post-workout smoothie on Saturday as a reward for consistent gym attendance" |
| `c6853660` | "…I'm thinking of changing my morning coffee limit to two cups…" and later "…I have increased the limit to two cups…" | "is currently using a drip coffee maker"; then "is excited to try out the French press method", "intends to use a darker roast with the French press method", two facts about stevia and honey |

In each case the earlier value had been extracted cleanly, because there it
was the point of a sentence: "The user has spotted 27 different bird species in
their local park", "The user has 1250 followers on Instagram", "The user plays
tennis with friends on a weekly basis", "The user goes to the gym on Tuesdays,
Thursdays, and Saturdays", "The user consumes one cup of dark roast coffee in
the morning". These stay current, and they are what the search retrieves.

The extraction is not careless in general: in 78% of questions the probe finds
the new value somewhere in the graph. It fails on a specific shape, a
quantity or frequency stated as an aside to a request about something else,
or as a plan ("thinking of changing… to two cups").

## 2. Resolution: when a new fact closes an old one

For each new fact, Graphiti retrieves two lists: facts between the same two
entities ("EXISTING FACTS") and similar facts anywhere ("FACT INVALIDATION
CANDIDATES"), and asks the model which of them the new fact duplicates and
which it contradicts. The prompt is deliberately conservative:

> NEVER mark facts as contradicted unless the new fact explicitly makes the old
> fact false. … A contradiction requires explicit evidence that the old fact
> stopped being true or was replaced… Do NOT infer contradiction from recency
> alone, episode dates…

Over the run, 301 of the 25,122 decisions (1.2%) marked any contradiction, and
1,264 marked a duplicate. The graph closed 4.8 facts per question out of
about 319.

When the model does mark a contradiction, Graphiti still decides *which* fact
to close from the dates, not from the order the facts arrived in
(`resolve_extracted_edge` and `resolve_edge_contradictions` in
`graphiti_core/utils/maintenance/edge_operations.py`):

- an old fact whose `valid_at` is earlier than the new fact's is closed at the
  new fact's `valid_at`;
- but if a contradicted fact's `valid_at` is *later* than the new fact's,
  the new fact is closed instead ("A candidate that starts later supersedes
  this edge, so expire this one instead");
- and when the new fact is a duplicate of an existing one, the existing fact
  is kept with its original dates.

`valid_at` comes from the extraction prompt's rule: "If the fact is ongoing
(present tense), set `valid_at` to the timestamp of the episode", while
relative phrases are resolved ("last month" → the first of last month). Of the
5,491 facts extracted from user messages, 5,267 got the message's own day, 183
an earlier date resolved from the text, and 24 a later one. This mostly works,
and it is what makes the newer value win when both reach the answer. It fails
when the two values are dated on different principles, as in `9ea5eabc`.

## 3. Retrieval and the answer

The search returns ten facts. In this run the new value, when it existed in the
graph, was usually among them; the failures are rarely retrieval. What
retrieval adds is noise: a fifth of the facts shown are the assistant's
suggestions, and those can carry the answer by accident. In `dad224aa` the only
fact with 7:30 was "The assistant suggests starting a jog at 8:15-8:30 am to
allow time to wake up at 7:30 am and have a cup of coffee beforehand"; the
answer reasoned from it to the right time. In `618f13b2`, the question whose
key is the earlier statement, seven of the ten facts were the assistant's
cleaning tips and the only count retrieved was "wore their new black Converse
six times" (the later "four" was not), so Graphiti is the one arm that matches
the key.

When both values reach the answer with their validity windows, the answering
model follows the dates: 37 of the 39 questions where the probe found both
delivered were answered correctly.

## Every wrong answer

Positions are the user's message number within the session. "Other arms" are
the seven other arms of the main run; "first run" is `graphiti-chunk`, where
sessions were cut into 8,000-character episodes.

### Revision never extracted

#### `affe2881` — "How many different species of birds have I seen in my local park?" (32)

- **2023-05-24, message 3:** "…I've managed to spot 27 different species so
  far." Extracted: "The user has spotted 27 different bird species in their
  local park."
- **2023-05-29, message 2:** "…I just saw a Northern Flicker in my local park
  last weekend, which brings my total species count to 32. Do you think the
  suet will attract any other woodpecker species as well?" Extracted the four
  facts in the table above; the count is not among them. "observed a Northern
  Flicker… last weekend" got `valid_at` 2023-05-21 from "last weekend". No
  contradiction was marked.
- **Retrieved:** first "The user has spotted 27 different bird species in their
  local park. (valid since 2023-05-24)", then the Flicker sighting.
- **Answer:** "You have seen 27 different species of birds in your local park."
- Other arms: all seven correct. First run: wrong.

#### `a2f3aa27` — "How many followers do I have on Instagram now?" (1300)

- **2023-05-25 05:26, message 2:** "…I've got 1250 followers on Instagram now…"
  Extracted: "The user has 1250 followers on Instagram."
- **2023-05-25 09:28, message 1:** "…I think I'm close to 1300 now." Extracted:
  content creation and three audience facts. The 1250 fact was among the
  candidates for three of the four and was not contradicted by any.
- **Retrieved:** "The user has 1250 followers on Instagram. (valid since
  2023-05-25)" first, then nine facts about Instagram features and captions.
- **Answer:** "There is no subsequent information… indicating that this number
  has changed… you have 1250 followers on Instagram."
- Other arms: 4 of 7 correct (full context, Mem0 and Letta also missed it).
  First run: wrong.

#### `5c40ec5b` — "How many times have I met up with Alex from Germany?" (twice)

- **2023-08-11, message 4:** "…the music festival where I met Alex." Extracted
  a duplicate of an existing fact: "The user and Alex share a mutual love for
  indie rock music."
- **2023-09-30, message 1:** "…we've met up twice already - he's really cool."
  Extracted "is friends with Alex, whom they met at a music festival", "Alex is
  from Germany" (a duplicate), "met their friend Alex at a music festival". The
  count was dropped.
- The graph also merged two people called Alex: among the facts about this Alex
  are "The user is in the process of buying a home with their partner Alex" and
  "The assistant advises the user on steps for buying a home with Alex", from
  an unrelated session.
- **Answer:** "The facts state that the user *met* Alex at a music festival
  (past tense), which accounts for one meeting… You have met up with Alex one
  time (at a music festival)."
- Other arms: all seven correct. First run: **correct** — its 8,000-character
  episode produced "The user has met their friend Alex from Germany twice
  before and plans to meet him again in Berlin."

#### `c4ea545c` — "Do I go to the gym more frequently than I did previously?" (yes)

- **2023-06-01, message 3:** "…I go to the gym on Tuesdays, Thursdays, and
  Saturdays." Extracted: "The user goes to the gym on Tuesdays, Thursdays, and
  Saturdays."
- **2023-08-15, message 1:** "…I've been consistent with my gym routine - four
  times a week, actually." Extracted: meal prep on Sunday, and "plans to have a
  post-workout smoothie on Saturday as a reward for consistent gym
  attendance". The frequency was dropped; the old schedule was a candidate for
  the smoothie fact and was not contradicted.
- **Answer:** "there is no information to suggest that you go to the gym more
  frequently than you did previously. The records only indicate a consistent
  schedule of Tuesdays, Thursdays, and Saturdays starting from June 1, 2023."
- Other arms: all seven correct. First run: wrong.

#### `c6853660` — "Did I mostly recently increase or decrease the limit on the number of cups of coffee in the morning?" (increased, one to two)

- **2023-05-25, message 1:** "…I've switched to a darker roast and cut back to
  just one cup in the morning…" Extracted: "The user consumes one cup of dark
  roast coffee in the morning to feel more focused."
- **2023-05-26, message 1:** "…I'm thinking of changing my morning coffee limit
  to two cups, do you think that's a good idea?" Extracted only "The user is
  currently using a drip coffee maker", which closed "has been using a French
  press".
- **2023-05-26, message 4** (not flagged as evidence by the dataset, but the
  clearest statement): "…I have increased the limit to two cups, and I'm
  thinking of experimenting with different sweeteners…" Extracted: French
  press, darker roast, stevia, honey. No limit.
- **Answer:** "There are no subsequent entries in the provided history
  indicating a change in the number of cups consumed in the morning."
- Other arms: all seven correct. First run: wrong.

#### `f685340e` — "How often do I play tennis with my friends at the local park previously? How often do I play now?" (weekly, now every other week)

- **2023-03-11, message 1:** "…reminds me of my own weekly tennis sessions with
  friends." Extracted both "participates in weekly tennis sessions with
  friends" and "plays tennis with friends on a weekly basis".
- **2023-07-30, message 1:** "…I'm planning to play tennis with my friends at
  the local park this Sunday, like we do every other week." Extracted a plan for
  this Sunday, twice; the second was marked a duplicate of "will visit the
  local park this Sunday, March 12, 2023, to play tennis with friends". Both
  weekly facts were candidates; neither was contradicted, and "every other
  week" was not extracted.
- **Answer:** "The records indicate that the user has been participating in
  tennis sessions with friends on a 'weekly basis' since at least March 2023…"
  Other arms: 5 of 7 correct. First run: wrong.

### Revision extracted in a form that does not contradict

#### `59524333` — "What time do I usually go to the gym?" (6:00 pm)

- **2023-02-11, message 3:** "…my gym sessions, which I usually go to at 7:00
  pm on Mondays, Wednesdays, and Fridays?" Extracted: "The user uses Todoist
  for task management and intends to use it to set reminders for gym sessions
  on Mondays, Wednesdays, and Fridays at 7:00 PM."
- **2023-05-30, message 3:** "I think Tuesday afternoon at 2:00 pm could work
  well. I need to make sure I'm done with the meeting before I head to the gym,
  which is usually at 6:00 pm." Extracted "plans to schedule a meeting for
  Tuesday at 2:00 pm" and "has a gym commitment at 6:00 pm on Tuesday". The
  7 pm fact was a candidate and, being about other days, was not contradicted.
  Another fact from the same session, "The user attends the gym on Mondays,
  Wednesdays, and Fridays", was dated 2023-05-30.
- **Answer:** "You typically go to the gym at 7:00 PM on Mondays, Wednesdays, and
  Fridays. You also have a specific gym commitment on Tuesdays at 6:00 PM."
- Other arms: 6 of 7 correct. First run: wrong.

### Resolution went wrong

#### `9ea5eabc` — "Where did I go on my most recent family trip?" (Paris)

- **2023-05-26 23:01, message 2:** "…my recent family trip to Hawaii and how we
  had a great time snorkeling together." Extracted "The user went on a recent
  family trip to Hawaii where they went snorkeling together", `valid_at`
  2023-05-26 (present-tense rule: the day of the message). The same session
  added "The assistant acknowledges that the user visited Hawaii and went
  snorkeling there" and, from the user's next message about wanting more time
  "to explore Waikiki", "the user visited Waikiki during their recent family
  trip", both dated 2023-05-26.
- **2023-05-28 04:57**, an earlier message of the Paris session: "…we just went
  there as a family last month…" Extracted "the user visited Paris with their
  family last month", `valid_at` 2023-04-01.
- **2023-05-28 04:55, message 5:** "…Since I've been thinking about my recent
  family trip to Paris…" Extracted "The user visited Paris with their family
  recently in April 2023". The model marked it a **duplicate** of the Paris
  fact above and **contradicting** the three Hawaii facts, which is the right
  judgement.
- Graphiti then applied the dates. The surviving Paris fact kept `valid_at`
  2023-04-01; the contradicted Hawaii facts start 2023-05-26, later; so the
  rule "a candidate that starts later supersedes this edge" closed **Paris**,
  at 2023-05-26.
- **Retrieved:** "The user went on a recent family trip to Hawaii… (valid since
  2023-05-26)", "the user visited Waikiki during their recent family trip
  (valid since 2023-05-26)", and "the user visited Paris with their family last
  month (valid from 2023-04-01 until 2023-05-26) [superseded]".
- **Answer:** "The trip to Hawaii is marked as a 'recent family trip' with a
  validity starting 2023-05-26, which is more recent than the Paris trip… You
  went to Hawaii…"
- Hawaii was dated by when it was mentioned, Paris by when it happened. Every
  other arm answered Paris. First run: wrong.

#### `945e3d21` — "How often do I attend yoga classes to help with my anxiety?" (three times a week)

- **2023-08-11, message 3:** "…I've been doing yoga twice a week, which has
  really been helping me relax and focus." Extracted "practices yoga twice a
  week to help relax and focus". A later message of the same session produced a
  second fact: "The user performs yoga twice a week to feel grounded and
  centered, particularly on days when experiencing anxiety."
- **2023-11-30, message 2:** "…I'm more focused on days when I attend yoga
  classes, which is three times a week - it really helps me clear my head."
  Extracted "attends yoga classes three times a week to help clear their head
  and improve focus". Both twice-a-week facts were candidates; the model marked
  only the first (the "relax and focus" one) as contradicted.
- **Retrieved:** the three-times fact, the anxiety twice-a-week fact (current),
  and the closed relax-and-focus fact.
- **Answer:** "The user has two distinct yoga routines mentioned. One is for
  focus (three times a week) and one is specifically linked to managing anxiety
  (twice a week)… You attend yoga classes twice a week to help with your
  anxiety."
- Other arms: 6 of 7 correct. First run: wrong.

### Delivered; the answer went wrong

#### `2133c1b5` — "How long have I been living in my current apartment in Harajuku?" (3 months)

- **2023-04-11, message 3:** "…my new studio apartment in Harajuku - it's been
  a month now…" Extracted "is currently living in Tokyo" and "resides in a
  studio apartment in Harajuku", both `valid_at` 2023-04-11. The duration
  ("a month") was not kept.
- **2023-10-15, message 2:** "…I've been living in Harajuku for 3 months now…"
  Extracted "has been living in Harajuku for 3 months". The apartment fact was
  a candidate and was not contradicted (they are compatible).
- **Retrieved:** the 3-months fact first, then the apartment fact.
- **Answer:** used only the apartment fact: "The user started living in the
  apartment on 2023-04-11… You have been living in your current apartment in
  Harajuku for 6 months and 4 days." The question says "apartment"; the
  three-months fact says "Harajuku".
- The history itself is inconsistent (a month in April and three months in
  October); textual memory also missed it. Other arms: 6 of 7 correct. First
  run: wrong.

#### `4d6b87c8` — "How many titles are currently on my to-watch list?" (25)

- Neither flagged statement produced a count: "…with 20 titles waiting to be
  checked off" (2023-05-20) gave facts about The Haunting of Hill House, and
  "…currently 25…" (2023-05-22, message 2) gave a duplicate fact about
  watching Victoria. A later message of that session, "I've got 25 titles on it
  right now", produced "The user has a to-watch list that currently contains 25
  titles". Retrieved with it: "plans to add the movie Amistad to their to-watch
  list" and "…Hotel Rwanda…".
- **Answer:** "Adding these two titles to the existing 25 results in a total of
  27 titles… There are currently 27 titles on your to-watch list." The plans
  were read as done.
- Other arms: 6 of 7 correct. First run: wrong.

#### `7401057b` — "How many free night's stays can I redeem at any Hilton property with my accumulated points?" (two)

- **2023-05-29, message 3:** "I've accumulated enough points for a single free
  night's stay…" Extracted "plans to redeem accumulated points for a single
  free night's stay at the Category 5 Hilton Lake Las Vegas Resort".
- **2023-05-30, message 1:** "…I've accumulated enough points for two free
  night's stays at any Hilton property…" Extracted "plans to use points for two
  free night's stays at a Hilton property for a separate trip to Las Vegas".
  The single-night fact was a candidate and was **not** contradicted: one is a
  plan for one resort, the other a plan for a trip.
- **Retrieved:** both, current, plus point prices for two hotels.
- **Answer:** "it is not possible to determine exactly how many free night's
  stays you can redeem because your current total point balance is not
  specified… log in to your Hilton Honors account…" It reasoned from the
  points-per-night facts and ignored both counts.
- Other arms: 6 of 7 correct. First run: wrong.

## How the correct answers were reached

The 55 correct answers by what the answer was given:

- **The old fact marked superseded, the new one current (26).** The design
  working as intended: `08e075c7` (Fitbit 6 → 9 months), `1cea1afa` (500 →
  600 followers), `4b24c848` (three → five tops), `ed4ddc30` (30 → 20 dozen
  eggs), `ce6d2d27` (Thursday → Friday), `db467c8c` (six → nine months), and
  twenty more. Several of these are revisions in passing that Letta's agent
  acknowledged and did not write down; Graphiti's extraction turned them into
  facts and its resolution closed the old ones.
- In `06db6396`, filed below under "only the new fact", the revision Letta
  missed ("By the way, I just finished my 5th project since starting painting
  classes") became "The user has completed their 5th project since they began
  attending painting classes", while the earlier "4 projects" was never
  extracted at all.
- **Both current, the dates decided (10).** `01493427` (17 → 25 postcards),
  `0e4e4c46` (124 → 132 points), `18bc8abd` (Sweet Baby Ray's → Kansas City
  Masterpiece), `41698283` (50mm → 70-200mm: "Comparing the acquisition dates,
  the 70-200mm zoom lens is the most recent addition"), `603deb26`,
  `7e974930`, `c7dc5443`, `cf22b7bf`, `dad224aa` (through the assistant's fact,
  above), `eace081b`.
- **Only the new fact retrieved (10).** `06db6396`, `22d2cb42`, `26bdc477`,
  `42ec0761`, `45dc21b6`, `5a4f22c0`, `618f13b2` (by luck, above), `a1eacc2a`,
  `ba61f0b9`, `cc5ded98`.
- **Questions about an earlier value or both (9 of 11).** The graph keeps
  closed facts with their windows, so "what was my previous…" can be answered
  from them: `50635ada` (Premier Silver), `9bbe84a2` (level 100), `dfde3500`,
  `07741c44`, `0ddfec37`, `10e09553`, `89941a94`, `031748ae`, `e66b632c`.

## First run against the re-run

| first run (8,000-character episodes) → re-run (one message per episode) | questions |
|---|--:|
| correct → correct | 11 |
| wrong → correct | 44 |
| correct → wrong | 1 |
| wrong → wrong | 11 |

The one loss, `5c40ec5b`, is the case above: the long episode kept "met… twice
before" in one fact, the single-message episode dropped the count. The eleven
wrong both times include all six revisions that were never extracted in the
re-run: what the long episodes lost in general, the short ones still lose for
asides.

## What would change the outcome

What the logs support:

- **Extraction that keeps asides.** Six of twelve failures are a revised
  quantity or frequency that the extraction prompt did not turn into a fact.
  Custom entity types (none were set) or a prompt that asks for the user's
  stated counts and schedules would target exactly this; whether it would add
  noise elsewhere is untested.
- **Not extracting the assistant's advice as facts about the world.** Three
  quarters of the facts, and of the contradiction checks, come from assistant
  messages, and a fifth of what is retrieved is the assistant's advice. Adding
  only the user's messages would cut the cost by roughly that much; it would
  also lose the occasional fact the assistant restates (`dad224aa`).
- **Dating by mention.** A fact dated by when it was said rather than when it
  became true would have kept Paris current in `9ea5eabc`; it would also lose
  the ordering that relative dates provide elsewhere. This is a design choice
  of the library, not a bug.
- **The model.** Extraction and resolution are model judgements at
  `gemini-3.1-flash-lite`; the resolution prompt's caution ("NEVER mark facts as
  contradicted unless…") is calibrated for a model that over-contradicts.

## Limits

- One run per question at temperature 0; the probes and this reading cover the
  final graph, not alternative runs.
- The counts of what reached the answer use a pattern per question for the old
  and new value, checked by reading all twelve wrong answers and the borderline
  correct ones.
- The logged calls include questions that were rebuilt after a failed episode
  (the rebuild is a cache replay); the per-step counts are over all logged
  calls.
