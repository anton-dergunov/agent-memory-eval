# Letta: why it scores lowest

Hand-written, from the recorded model calls of the Letta run in
`results/main/letta/` (one agent step per user message), read next to the
LongMemEval histories and the source of the Letta server that ran them
(0.16.8). Every request the agent sent and every reply it got was logged: the
messages it was shown, the memory edits it made with their arguments, what each
tool returned, and the reply it wrote. That makes it possible to say, for each
question, what the agent did at the moment the revised fact arrived.

67 questions are too few to estimate rates. The numbers below count what
happened in this run; the mechanisms are the result.

## Summary

Letta answers 46 of 67 (69%, 95% interval 57–78%), the only arm clearly below
the others. The failures are not one weakness but a chain of three, each of
which the next one could have caught:

1. **The agent often does not write the revision down.** At the user message
   that carries the new value, it edited memory to record that value in 31 of
   the 64 questions that have such a message. In the other 33 it made no memory
   edit for it, and in 18 of those its own reply names the new value
   ("Congratulations on hitting 600 followers!"): it noticed, answered, and
   moved on.
2. **When the value is not in memory, the search cannot find it.** The only
   fallback is `conversation_search`, which on a self-hosted Letta 0.16.8 is a
   case-insensitive *phrase* match that returns the **five newest** matching
   messages. The agent searches with paraphrases ("painting projects
   completed") that never occur verbatim, so 97 of its 146 searches at answer
   time returned nothing. Short queries do match, but the five newest matches
   are usually the question itself and the agent's own recent replies, so an
   older user message falls outside them.
3. **When the memory holds the old value, the agent trusts it.** In six of the
   wrong answers the block still said "has completed 4 projects", "recently hit
   500 followers", "bought three tops", the searches came back empty, and the
   agent answered from the block ("According to your records…").

| What the answer had to work with | questions | correct |
|---|--:|--:|
| the memory block held the value asked for | 36 | 31 |
| the block did not; a search returned it | 17 | 14 |
| neither | 13 | 1 |
| no memory: build stopped by the provider's content filter | 1 | 0 |
| **total** | **67** | **46** |

The 21 wrong answers, by cause:

| Cause | answers | questions |
|---|--:|---|
| Revision never written; the block still held the earlier value, the search found nothing, the answer came from the block | 6 | `06db6396`, `1cea1afa`, `4b24c848`, `cc5ded98`, `ce6d2d27`, `ed4ddc30` |
| Revision never written, nothing usable in the block, the search found nothing (or only the earlier message) | 5 | `26bdc477`, `6a27ffc2`, `a2f3aa27`, `dad224aa`, `db467c8c` |
| Revision never written; a search returned it, but the answer did not use it | 3 | `41698283`, `6071bd76`, `f685340e` |
| The agent replaced the earlier value that the question asks for | 2 | `031748ae`, `50635ada` |
| The agent answered from its own knowledge against what the user said | 1 | `0f05491a` |
| The agent misread the question | 1 | `eace081b` |
| The question or its key is flawed | 2 | `618f13b2`, `e66b632c` |
| No answer: the provider's content filter stopped the build | 1 | `184da446` |

In 14 of the 21 the revision was never in memory (the first three rows); in
each of those the search was the only way back to it, and it failed.

## How Letta ran here

- **One agent per question**, `letta_v1_agent`, with Letta's two default memory
  blocks: `persona` (Letta's starter text) and an empty `human` block. Every
  other setting is Letta's default, including the sampling temperature the
  server sends, 1.0.
- **Each session is a new conversation** with that agent, and **each user
  message is one agent step**: the agent replies as the assistant (the
  dataset's recorded assistant replies are not sent) and decides at that step
  whether to call a tool. The date of the session is prefixed to every message,
  because the server stamps messages with the time they arrive and cannot
  import a date. A new conversation starts with the memory blocks and nothing
  else in context.
- **The question is asked in a new conversation** and the agent's reply is the
  answer.

The agent's whole instruction about memory is Letta's base prompt:

> You have an advanced memory system that enables you to remember past
> interactions and continuously improve your own capabilities. Your memory
> consists of memory blocks and external memory: … Memory management tools
> allow you to edit existing memory blocks and query for external memories.

It says nothing about when to write or about correcting what was written. The
`human` block's description is "Stores key details about the person you are
conversing with, allowing for more personalized and friend-like conversation."
The tools offered are `memory_insert` (whose first example is "append to the
end of the block"), `memory_replace` (exact string replacement; "Do NOT attempt
to replace long strings") and `conversation_search`, described as "Search prior
conversation history using hybrid search (text + semantic similarity)".

## 1. The write side: what the agent does with a revision

While reading a history the agent made 538 `memory_insert` and 93
`memory_replace` calls over the 66 complete questions (8.2 and 1.4 per
question). Eleven failed: six replaces whose `old_string` did not match the
block exactly, four inserts into blocks that do not exist ("Block field
reading_list does not exist (available sections = persona, human)") and one
insert at a line number past the end. It also made 791 `conversation_search`
calls while reading, 684 of which (86%) returned nothing. The two memory blocks
end at about 1,560 characters together.

What it did at the user message that carries the new value:

| At the message with the revision, the agent… | questions | correct |
|---|--:|--:|
| replaced the old text with one containing the new value | 19 | 16 |
| inserted a new line with the new value | 12 | 11 |
| edited memory, but not with the new value | 2 | 2 |
| searched the history and edited nothing | 12 | 4 |
| made no tool call at all | 19 | 12 |
| (no such message: both statements are in one session) | 2 | 1 |

When it wrote the new value at that message, it answered 27 of 31 correctly,
and none of the four misses is a lost update: two are overwrites of a value
the question asks for, one is an answer from the model's own knowledge, one is
a flawed question. When it did not, it answered 16 of 31: 13 rescued by a
search at answer time, 2 by an edit at another message of the same session,
1 by luck. Only 2 of the 31 got the value into the block at a later message.

The misses are revisions mentioned in passing, inside a message about
something else, and the agent's reply often shows it read them:

| Question | the revision, as the user said it | the agent's reply at that step | memory edit |
|---|---|---|---|
| `06db6396` | "By the way, I just finished my 5th project since starting painting classes" | "Congratulations on finishing your 5th project!" | none |
| `1cea1afa` | "By the way, I just checked and I'm now at 600 followers" | "Congratulations on hitting 600 followers!" | none |
| `4b24c848` | "By the way, I've already got five tops from H&M so far" | "Five is a great start" (after an empty search for "H&M Sephora sales promotions mall") | none |
| `cc5ded98` | "By the way, I've been dedicating about two hours each day to coding exercises" | "Two hours a day is a serious commitment" | none |
| `ed4ddc30` | "we've got 20 dozen stocked up in the fridge right now" | "Since you have such an impressive stockpile of 20 dozen eggs…" | none |

The first value had usually been written at a moment when the user's message
*was* about it. In `06db6396` the agent did not save "I've completed 4
projects" when it was said; it saved it one message later, in a summary line
written while the user asked about signing paintings: "They are an emerging
painter who has completed 4 projects so far and is currently working on a
sunset scene for their sister's birthday." The revision, two months later, came
as an aside in a request for painting ideas, and no line was touched.

Replacing is not always right either. In two of the 19 replaces the old value
was what the question needed (`031748ae`, `50635ada`, below): the agent kept
the block current by deleting the history.

## 2. The read side: why the search does not find what was not written

At question time the agent searched in 63 of 66 questions, 146 searches in all,
and 97 of them returned "No results found." The cause is in the server, not
in the model. Without Turbopuffer (a hosted vector service) configured, Letta
0.16.8's `conversation_search` takes this path
(`letta/services/message_manager.py`, `search_messages_async`, and
`letta/services/tool_executor/core_tool_executor.py`):

- it calls `list_messages(query_text=…, limit=5, ascending=False)`, which
  filters message text with `ILIKE '%<query>%'`: the whole query must appear,
  verbatim, as one substring. Quotation marks are matched literally, so
  `"tennis"` with quotes finds nothing;
- the limit is `RETRIEVAL_QUERY_DEFAULT_PAGE_SIZE = 5`, newest first;
- tool messages are removed *after* the limit is applied;
- `start_date` and `end_date` are accepted but not passed to this query; and
  in any case every message carries the server's timestamp from October 2026,
  not the history's date.

The tool description promises "hybrid search (text + semantic similarity)", and
the agent queries it the way one would query such a search, with paraphrases of
the question:

| Question | the agent's searches at answer time | results |
|---|---|---|
| `06db6396` | "painting projects completed", "painting classes projects" | none, none |
| `cc5ded98` | "how much time coding exercises each day" | none |
| `db467c8c` | "parents stay US duration arrival date", "parents visa expiration arrival", "parents US duration", "parents immigration overstay", "parents visit US dates" | none ×5 |
| `031748ae` | "number of engineers lead team size", "team of 5 engineers", "Senior Software Engineer team", "\"lead a team of\"", "\"my team of\"" (and two that matched only the question itself) | none |

Short queries do match, and then the newest-five limit decides. Three things
fill those five places before an old user message can:

- **the question itself**, the newest message, which always contains the
  question's words;
- **the agent's own replies**, which are long and repeat the topic (in
  `1cea1afa`, "Instagram followers" returned the question and three of the
  agent's replies about content for "your Instagram followers");
- **the echoes of its own memory edits.** Every `memory_insert` and
  `memory_replace` returns the whole `human` block as its result, and that
  result is stored as a tool message. Once a fact is in the block, each later
  edit adds another message containing it; those take the five places and are
  then removed. In `50635ada` the agent searched "20,000 miles", the exact
  phrase of the message it needed ("I actually just hit 20,000 miles on United
  Airlines…"), and got nothing: the newest matches were echoes of the block.
  Writing a fact down makes it harder to find in the history.

To check how much a better query would have helped, the message store of each
question can be rebuilt from the log (user messages, the agent's replies, tool
results, in order) and the server's rule applied to it. Of the 144 real
searches it can replay (two used extra filters), the rebuilt store reproduces
118 exactly, and where it differs it almost always returns one message more
than the server did, so it errs toward finding things. For the 14 wrong answers where the revision was never written, with the
most natural one-word query:

| Question | query | messages containing it | update returned in the five? |
|---|---|--:|---|
| `06db6396` | painting | 37 | no |
| `1cea1afa` | followers | 40 | no |
| `4b24c848` | H&M | 13 | yes |
| `cc5ded98` | coding | 30 | no |
| `ce6d2d27` | cocktail | 18 | no |
| `ed4ddc30` | eggs | 28 | yes |
| `26bdc477` | 80D | 11 | no |
| `6a27ffc2` | Corey | 12 | yes |
| `dad224aa` | Saturday | 8 | yes |
| `db467c8c` | parents | 19 | no |
| `a2f3aa27` | followers | 9 | no |
| `41698283` | lens | 18 | no |
| `f685340e` | tennis | 20 | no |
| `6071bd76` | French press | 12 | yes |

So a well-chosen word would have rescued about a third of them. The rest are
out of reach of any topic word; only the new value itself finds them ("600",
"5th", "1300"), and the agent does not know the new value — that is the
question.

Where the search did succeed, it was with short, distinctive terms whose
matches were few: "Crash Course", "MCU", "gym", "tidying routine", "Korean
restaurants", "family trip", "5K run", "level 100", "baseball".

## 3. Trusting the block

When the block holds a value, the agent treats it as the record. In the six
answers where it held the earlier value, the agent made one or two searches,
all empty, and answered from the block in the block's words:

| Question | the line in the `human` block | the answer |
|---|---|---|
| `06db6396` | "…an emerging painter who has completed 4 projects so far…" | "According to your records, you have completed **4 projects** so far." |
| `1cea1afa` | "The user recently hit 500 followers on Instagram…" | "According to the information in your user profile, you recently hit **500 followers** on Instagram." |
| `4b24c848` | "The user loves H&M's summer collection and recently bought three tops there." | "You have bought three tops from H&M's summer collection so far." |
| `cc5ded98` | "Currently practicing Python coding for one hour daily." | "Based on your current habits, you dedicate **one hour** to Python coding exercises each day." |
| `ce6d2d27` | "…They are attending a cocktail-making class this coming Thursday." | "According to your records, you are attending your cocktail-making class this coming Thursday!" |
| `ed4ddc30` | "…currently has a large surplus of 30 dozen eggs…" | "Based on our records, you currently have a surplus of 30 dozen eggs." |

The block carries no dates: "recently hit 500 followers" written in May reads
the same in June. Nothing in it says that a later message might have changed
it, and the agent does not check.

## Every wrong answer

Each entry gives the two statements as the user made them (session date, and
the position of the message among the user's messages in that session), what
the agent did at each, what the block said at the end, the searches at answer
time and the answer. "Other arms" counts the seven other arms of the main run
(full context, retrieval, textual memory, Mem0, both Honcho read paths,
Graphiti); "first run" is the same question in `letta-batch`, where whole
sessions were sent in one request.

### Revision never written; the block held the earlier value

#### `06db6396` — "How many projects have I completed since starting painting classes?" (5)

- **2023-08-16, message 3:** "I've completed 4 projects since starting
  painting classes…" The agent replied with varnishing tips and no tool call.
  At the next message it inserted: "They are an emerging painter who has
  completed 4 projects so far and is currently working on a sunset scene for
  their sister's birthday."
- **2023-10-09, message 1:** "By the way, I just finished my 5th project since
  starting painting classes, and I'm feeling pretty accomplished!" Reply:
  "Congratulations on finishing your 5th project! That is a fantastic
  milestone…" No tool call.
- **Answer time:** block unchanged; searches "painting projects completed" and
  "painting classes projects", both empty. Answer: "According to your records,
  you have completed **4 projects** so far."
- Other arms: all seven correct. First run: correct ("You mentioned reaching
  that milestone back in early October"), by search. In a separate trace of
  this question made while testing the fix, the agent also made no memory call
  at the revision, then searched "painting classes", which returned the
  October message, and answered 5. The outcome turns on whether one query
  happens to match.

#### `1cea1afa` — "How many Instagram followers do I currently have?" (600)

- **2023-05-27, message 1:** "By the way, I just reached 500 followers last
  week…" No tool call; at the next message it inserted "The user recently hit
  500 followers on Instagram and is looking to grow their presence…"
- **2023-05-28, message 1:** "By the way, I just checked and I'm now at 600
  followers, which is a nice milestone!" Reply: "Congratulations on hitting
  600 followers!" No tool call. Two messages later it inserted a line about
  planning an Instagram Q&A, leaving the 500 line as it was.
- **Answer time:** "Instagram followers count" (empty), "Instagram followers"
  (the question and three of the agent's replies). Answer: "…you recently hit
  **500 followers** on Instagram."
- Other arms: 6 of 7 correct (Honcho's dialectic chat declined). First run:
  correct, by search.

#### `4b24c848` — "How many tops have I bought from H&M so far?" (five)

- **2023-08-11, message 3:** "I've already bought three tops from H&M…" The
  agent inserted "The user loves H&M's summer collection and recently bought
  three tops there."
- **2023-09-30, message 1:** "By the way, I've already got five tops from H&M so
  far, and I'm thinking of getting a few more." The agent searched "H&M Sephora
  sales promotions mall" with `start_date: 2023-09-25` (empty; the date is
  ignored and the phrase never occurs), then replied "Five is a great start".
  No memory edit.
- **Answer time:** "tops H&M bought", empty. Answer: "You have bought three tops
  from H&M's summer collection so far." The single word "H&M" would have
  returned the September message.
- Other arms: all correct. First run: correct ("you mentioned on September 30,
  2023, that you had five tops").

#### `cc5ded98` — "How much time do I dedicate to coding exercises each day?" (about two hours)

- **2023-05-20, message 3:** "I've been dedicating about an hour each day to
  coding exercises…" Inserted: "Currently practicing Python coding for one
  hour daily."
- **2023-05-29, message 1:** "By the way, I've been dedicating about two hours
  each day to coding exercises…" Reply: "That is fantastic! Two hours a day is
  a serious commitment…" No tool call.
- **Answer time:** one search, "how much time coding exercises each day",
  empty. Answer: "you dedicate **one hour** to Python coding exercises each
  day."
- Other arms: all correct. First run: correct, by searching "coding
  exercises".

#### `ce6d2d27` — "What day of the week do I take a cocktail-making class?" (Friday)

- **2023-06-16, message 3:** "…I have a cocktail-making class on Thursday…"
  Inserted as part of a dinner-party note: "They are attending a
  cocktail-making class this coming Thursday."
- **2023-06-30, message 1:** "By the way, I have a cocktail-making class on
  Fridays…" The agent searched "cocktail-making class" and "spicy mango
  margarita" (both empty), replied "How exciting about your upcoming
  cocktail-making class!", and edited nothing; two messages later it inserted
  a line about basil and roasted watermelon.
- **Answer time:** "cocktail-making class", empty. Answer: "you are attending
  your cocktail-making class this coming Thursday!" Note that the stored line
  was a one-off plan ("this coming Thursday"), which the answer then reads as a
  weekly schedule.
- Other arms: all correct. First run: correct ("on **Fridays**").

#### `ed4ddc30` — "How many dozen eggs do we currently have stocked up in our refrigerator?" (20)

- **2023-01-11, message 2:** "…30 dozen at the moment!" No tool call; next
  message: "The user lives on a homestead with goats and currently has a large
  surplus of 30 dozen eggs." Later replaced to add goat milk, keeping "30
  dozen".
- **2023-03-15, message 2:** "…we've got 20 dozen stocked up in the fridge
  right now." Reply: "Since you have such an impressive stockpile of 20 dozen
  eggs, storage is definitely key." No tool call.
- **Answer time:** "eggs stocked refrigerator", empty. Answer: "you currently
  have a surplus of 30 dozen eggs."
- Other arms: all correct. First run: wrong too (it found no record).

### Revision never written, nothing usable in the block

#### `26bdc477` — "How many trips have I taken my Canon EOS 80D camera on?" (five)

- **2023-03-16, message 2:** "…including three trips to Yellowstone, Yosemite,
  and the Grand Canyon…" No tool call; two messages later the agent inserted
  a list including "Currently uses Canon EOS 80D." and "Active adventurer: has
  visited Yellowstone, Yosemite, and the Grand Canyon." The count was not
  kept, only the places.
- **2023-05-30, message 1:** "By the way, I've had my Canon EOS 80D with me on
  five trips now, and it's been a beast!" Reply about shooting in Zion; no tool
  call.
- **Answer time:** "Canon EOS 80D trips", "Yellowstone Yosemite Grand Canyon
  camera", "Canon EOS 80D photography", all empty. Answer: "you've mentioned
  taking your Canon EOS 80D on trips to **Yellowstone, Yosemite, and the Grand
  Canyon**. That makes at least three major adventures…"
- Other arms: all correct. First run: wrong (no consolidated count).

#### `6a27ffc2` — "How many videos of Corey Schafer's Python programming series have I completed so far?" (30)

- **2023-05-24, message 1:** "…I've completed 20 videos so far." Reply only;
  the later insert about the project mentions no count.
- **2023-05-26, message 2:** "I've completed 30 videos so far for Corey's
  series…" The agent searched "setting up NLP project environment library
  installation" (empty) and replied "30 videos into Corey Schafer's series puts
  you in a perfect position…" No memory edit.
- **Answer time:** "Corey Schafer Python programming series completed" and
  "Corey Schafer Python", empty; "Python programming series" returned the
  question and the **May 24** message, the one with 20 (the May 26 message
  calls it "Corey's series"). Answer: "You have completed 20 videos… You
  mentioned this during our conversation on May 24th."
- Other arms: all correct. First run: correct, by searching "Corey Schafer".

#### `a2f3aa27` — "How many followers do I have on Instagram now?" (1300)

- **2023-05-25 05:26, message 2:** "…I've got 1250 followers on Instagram now…"
  Reply ("hitting 1,250 followers is a great milestone"); no tool call.
- **2023-05-25 09:28, message 1:** "…I think I'm close to 1300 now." The agent
  searched "follower count" (two results, neither the 1,250 message) and
  replied "It's so exciting that you're nearing 1,300 followers!" No memory
  edit. The only follower-related line ever written was "Interested in hosting
  Instagram Lives to engage with followers."
- **Answer time:** "Instagram followers", empty. Answer: "I'm sorry, I don't
  actually have access to your personal social media accounts or real-time
  data from platforms like Instagram…" With nothing in memory and nothing
  found, the answer falls back on the model's stock disclaimer.
- Other arms: 4 of 7 correct. First run: wrong (the same disclaimer).

#### `dad224aa` — "What time do I wake up on Saturday mornings?" (7:30 am)

- **2023-05-23, message 2:** "I've been waking up around 8:30 am on
  Saturdays…" Reply only.
- **2023-05-27, message 2:** "…I like to wake up at 7:30 am on Saturdays…" The
  agent searched "neighborhood jog route location address" (empty) and asked
  where the user lives. No memory edit.
- **Answer time:** "wake up Saturday morning", "wake up time", empty (the user
  wrote "waking up" and "wake up at"). Answer: "I don't seem to have a record
  of when you typically wake up on Saturday mornings…" "Saturday" alone would
  have returned the May 27 message.
- Other arms: 5 of 7 correct. First run: wrong (8:30, the earlier value).

#### `db467c8c` — "How long have my parents been staying with me in the US?" (nine months)

- **2023-07-16, message 2:** "…it's been great to have them around for the
  past six months." Reply only.
- **2023-10-20, message 1:** "…they've been staying with me for nine months
  now." The agent searched "green card documents process parents paperwork"
  (empty) and replied with an immigration disclaimer. Two messages later it
  inserted "Parents are currently in the US with expired visas (overstaying)."
  The duration was never written. (An unrelated line says "Marketing
  specialist with ~9 months of experience.")
- **Answer time:** five searches, all multi-word, all empty. Answer: "I don't
  have a record of when your parents arrived in the US or exactly how long they
  have been staying with you."
- Other arms: all correct. First run: correct, by searching "parents".

### Revision never written; a search returned it, the answer did not use it

#### `41698283` — "What type of camera lens did I purchase most recently?" (a 70-200mm zoom lens)

- **2023-03-11, message 2:** "…I recently got a new 50mm prime lens…" Inserted:
  "Owns a Nikon D5600, currently uses a 50mm prime lens…"
- **2023-08-30, message 1:** "By the way, I've been getting some great shots
  with my new 70-200mm zoom lens lately." Searched "tripod tripod Gitzo Really
  Right Stuff RRS 70-200mm" (empty), replied "That's wonderful to hear that
  you're having success with the new 70-200mm lens!" No memory edit.
- **Answer time:** eight searches; "70-200mm" returned two of the user's
  messages from the last session about the 70-200mm lens. Answer: "you currently
  have a 50mm prime lens and a 70-200mm zoom lens… I don't have a record of
  you purchasing a new lens most recently." The search delivered the new lens;
  the block still called the 50mm current, and the answer declined to say
  which came last.
- Other arms: 6 of 7 correct. First run: correct.

#### `6071bd76` — "For the coffee-to-water ratio in my French press, did I switch to more water per tablespoon of coffee, or less?" (less: 5 ounces)

- **2023-02-11, message 1:** "…1 tablespoon of coffee for every 6 ounces of
  water is the perfect ratio for me." Reply only; the insert two messages
  later records Kenyan coffee and Earl Grey, not the ratio.
- **2023-06-30, message 1:** "…1 tablespoon of coffee for every 5 ounces of
  water." Reply only.
- **Answer time:** "French press coffee-to-water ratio" (empty), "French
  press" (five results, all from the June session and the question). Answer:
  "you mentioned that your French press ratio was **1 tablespoon of coffee for
  every 5 ounces of water**… Have you tried adjusting that ratio recently?" The
  February value was never in memory and was not among the five newest
  matches, so the agent had one value and could not say which way it changed.
- Other arms: all correct. First run: wrong (same answer).

#### `f685340e` — "How often do I play tennis with my friends at the local park previously? How often do I play now?" (weekly, now every other week)

- **2023-03-11, message 1:** "…reminds me of my own weekly tennis sessions with
  friends." Inserted: "The user plays tennis weekly with friends."
- **2023-07-30, message 1:** "…I'm planning to play tennis with my friends at
  the local park this Sunday, like we do every other week." The agent searched
  "location home address area" and "apartment moved commute" (both empty) and
  asked where the user lives. No memory edit; a reply later in the session
  speaks of "your bi-weekly tennis games".
- **Answer time:** "tennis" returned three of the newest messages, one of them
  the agent's reply with "bi-weekly tennis games"; `"tennis"` (quoted, with
  and without `roles: ["user"]`) and `"weekly"` returned nothing. Answer: "you
  currently play tennis **weekly** with your friends. I don't have a specific
  record of you playing at a different frequency in the past."
- Other arms: 5 of 7 correct. First run: wrong.

### The agent replaced the earlier value the question asks for

#### `031748ae` — "How many engineers do I lead when I just started my new role as Senior Software Engineer? How many engineers do I lead now?" (4, now 5)

- **2023-05-11, message 6:** "I lead a team of 4 engineers in my new role as
  Senior Software Engineer." The agent replaced its earlier line with "The
  user is a Senior Software Engineer leading a team of 4 engineers…"
- **2023-10-24, message 2:** "…I now lead a team of five engineers…" The agent
  replaced the line again: "…leading a team of 5 engineers… (7 people total)",
  and told the user "I've updated my notes to reflect that your team has grown
  to seven people total."
- **Answer time:** eight searches; two whole-question queries matched only the
  question itself, the rest were empty. Answer: "you lead a team of **5
  engineers**… I don't have a specific record of a different team size at the
  beginning of your role."
- This is the replace working as intended and losing what the question needs.
  Other arms: all correct. First run: no reply.

#### `50635ada` — "What was my previous frequent flyer status on United Airlines before I got the current status?" (Premier Silver)

- **2022-09-16, message 3:** "I actually just hit 20,000 miles on United
  Airlines, which means I'm finally eligible for Premier Silver status."
  Inserted: "The user has reached 20,000 miles on United Airlines and is now
  eligible for Premier Silver status."
- **2023-05-30, message 2:** "…I just reached Premier Gold status." The agent
  rewrote the block with `memory_replace`; the line became "…is now eligible
  for Premier Gold status." Silver was gone from memory.
- **Answer time:** "United Airlines" returned the question and two messages
  from the last session; "United Airlines status before" and "20,000 miles"
  returned nothing. The 2022 message contains "20,000 miles" verbatim, but the
  newest matches were echoes of the block. Answer: "I don't see a mention of
  your specific status prior to reaching Premier Gold… Do you remember if you
  were Silver status…?"
- Other arms: all correct. First run: wrong.

### The agent answered from its own knowledge

#### `0f05491a` — "How many stars do I need to reach the gold level on my Starbucks Rewards app?" (120)

- **2023-07-11, message 6:** "…I actually need **125 stars** to reach the Gold
  level… not 400." Replaced: "The user believes they need 125 stars to reach
  the Gold level…" Reply: "the current national Starbucks Rewards program
  doesn't use the 'Gold' level anymore."
- **2023-07-30, message 4:** "Actually, I need 120 stars to reach the gold
  level, not 300." Replaced: "The user persists in their belief about a 'Gold'
  level and a specific Star requirement (previously 125, now 120), despite the
  system having changed. I should remain helpful and supportive without being
  overly argumentative, while gently encouraging them to check their app's
  official status page…"
- **Answer time:** one empty search. Answer: "the 'Gold' status structure isn't
  the primary way the rewards work anymore… the current program doesn't have a
  'Gold' tier in the same way it used to."
- The new value was in memory, with its history. The agent had recorded the
  user as mistaken and answered from what it believes about the real program.
  Three of its edits in between failed (`old_string` not found). Other arms:
  all correct. First run: wrong, the same way. In the trace of this question
  the agent answered 120.

### The agent misread the question

#### `eace081b` — "Where am I planning to stay for my birthday trip to Hawaii?" (Oahu)

- Only one statement is in the trimmed history: "I'm actually planning to stay
  on Oahu…" (2023-05-25, message 2). The agent inserted "Planning a trip to
  Oahu, Hawaii in October 2023 for their birthday."
- **Answer:** "you are planning a trip to Oahu, Hawaii… However, I don't see a
  specific mention of where you are planning to stay during that trip… Have
  you decided on a hotel?" It read "stay" as a hotel. Mem0's answer misread it
  the same way. Other arms: 6 of 7 correct. First run: wrong.

### The question or its key is flawed

#### `618f13b2` — "How many times have I worn my new black Converse…?" (key: six)

Two sessions on 2023-05-30. At 17:45 the user says "that's six times now"; the
agent inserted "recently purchased black Converse (worn 6 times)". At 22:16,
the later session, the user says "I've worn them four times already" (twice,
messages 2 and 6), and the agent replaced the line with "(worn 4 times)". It
answered 4. The agent kept the most recent statement, which is what an
updating memory should do; the key holds the earlier one. Every arm except
Graphiti answers four.

#### `e66b632c` — "What was my previous personal best time for the charity 5K run?" (key: 27:45)

The earlier session gives 27:45 as a personal best; the later one calls 26:30
"my previous charity 5K run performance… a personal best time of 26 minutes
and 30 seconds". The agent inserted the 26:30 line and answered 26:30. Four
arms miss this question; see the failure analysis.

### No answer

#### `184da446` — "How many pages of 'A Short History of Nearly Everything' have I read so far?" (220)

In each of four builds, Vertex returned `finish_reason=content_filter` with no
message at the same point: the first user message of the third session, a
distractor, "I'm looking for some inspiration for my daily devotions. Can you
suggest some Bible verses or prayers that focus on perseverance and faith…".
Letta stops the step on such a reply, so the build never finished and there
is no answer. By then the agent had written "Currently reading 'A Short
History of Nearly Everything' by Bill Bryson (on page 200)." The first run,
which sent whole sessions, answered 220.

## How the correct answers were reached

| Question | asked | reference | at the revision message | the answer came from |
|---|---|---|---|---|
| `01493427` | How many new postcards have I added to my collection since I started collecting again? | 25 | replaced old text with the new value | the block |
| `07741c44` | Where do I initially keep my old sneakers? | under my bed | edited memory, not with the new value | the block |
| `08e075c7` | How long have I been using my Fitbit Charge 3? | 9 months | inserted the new value | the block |
| `0ddfec37` | How many autographed baseballs have I added to my collection in the first three months of collection? | 15 | edited memory, not with the new value | a search ("baseball") |
| `0e4e4c46` | What is my current highest score in Ticket to Ride? | 132 points | replaced old text with the new value | the block |
| `10e09553` | How many largemouth bass did I catch with Alex on the earlier fishing trip to Lake Michigan before the 7/22 trip? | 7 | replaced old text with the new value | the block |
| `18bc8abd` | What brand of BBQ sauce am I currently obsessed with? | Kansas City Masterpiece | inserted the new value | the block |
| `2133c1b5` | How long have I been living in my current apartment in Harajuku? | 3 months | replaced old text with the new value | the block |
| `22d2cb42` | Where did I get my guitar serviced? | The music shop on Main St. | (one statement only) | the block |
| `2698e78f` | How often do I see my therapist, Dr. Smith? | every week | replaced old text with the new value | the block |
| `42ec0761` | Do I have a spare screwdriver for opening up my laptop? | Yes | replaced old text with the new value | the block |
| `45dc21b6` | How many of Emma's recipes have I tried out? | 3 | no tool call | a search ("Emma's recipes") |
| `4d6b87c8` | How many titles are currently on my to-watch list? | 25 | inserted the new value | the block |
| `5831f84d` | How many Crash Course videos have I watched in the past few weeks? | 15 | searched only | a search ("Crash Course") |
| `59524333` | What time do I usually go to the gym? | 6:00 pm | no tool call | a search ("gym") |
| `5a4f22c0` | What company is Rachel, an old colleague from my previous company, currently working at? | TechCorp | searched only | a search ("TechConnect") |
| `5c40ec5b` | How many times have I met up with Alex from Germany? | twice | replaced old text with the new value | the block |
| `603deb26` | How many times have I tried making a Negroni at home since my friend Emma showed me how to make it? | 10 | replaced old text with the new value | the block |
| `6a1eabeb` | What was my personal best time in the charity 5K run? | 25:50 | no tool call | a search ("5K run") |
| `6aeb4375` | How many Korean restaurants have I tried in my city? | four | searched only | a search ("Korean restaurants") |
| `71315a70` | How many hours have I spent on my abstract ocean sculpture? | 10-12 hours | no tool call | a search ("sculpture") |
| `72e3ee87` | How many episodes of the Science series have I completed on Crash Course? | 50 | replaced old text with the new value | the block |
| `7401057b` | How many free night's stays can I redeem at any Hilton property with my accumulated points? | Two | replaced old text with the new value | the block |
| `7a87bd0c` | How long have I been sticking to my daily tidying routine? | 4 weeks | no tool call | a search ("tidying routine") |
| `7e974930` | How much did I earn at the Downtown Farmers Market on my most recent visit? | $420 | inserted the new value | the block |
| `830ce83f` | Where did Rachel move to after her recent relocation? | the suburbs | inserted the new value | the block |
| `852ce960` | What was the amount I was pre-approved for when I got my mortgage from Wells Fargo? | $400,000 | inserted the new value | the block |
| `89941a93` | How many bikes do I currently own? | 4 | replaced old text with the new value | the block |
| `89941a94` | Before I purchased the gravel bike, do I have other bikes in addition to my mountain bike and my commuter bike? | Yes (a road bike) | replaced old text with the new value | the block |
| `8fb83627` | How many issues of National Geographic have I finished reading? | Five | no tool call (written earlier in the session) | the block |
| `945e3d21` | How often do I attend yoga classes to help with my anxiety? | Three times a week | no tool call | neither (see below) |
| `9bbe84a2` | What was my previous goal for my Apex Legends level before I updated my goal? | level 100 | no tool call | a search ("level 100") |
| `9ea5eabc` | Where did I go on my most recent family trip? | Paris | no tool call | a search ("family trip") |
| `a1eacc2a` | How many short stories have I written since I started writing regularly? | seven | no tool call | a search ("writing regularly") |
| `affe2881` | How many different species of birds have I seen in my local park? | 32 | replaced old text with the new value | the block |
| `b01defab` | Did I finish reading 'The Nightingale' by Kristin Hannah? | Yes | searched only | a search ("Nightingale") |
| `b6019101` | How many MCU films did I watch in the last 3 months? | 5 | no tool call | a search ("MCU") |
| `ba61f0b9` | How many women are on the team led by my former manager Rachel? | 6 | inserted the new value | the block |
| `c4ea545c` | Do I go to the gym more frequently than I did previously? | Yes | replaced old text with the new value | the block |
| `c6853660` | Did I mostly recently increase or decrease the limit on the number of cups of coffee in the morning? | increased | no tool call (written later in the session) | the block |
| `c7dc5443` | What is my current record in the recreational volleyball league? | 5-2 | inserted the new value | the block |
| `cf22b7bf` | How much weight have I lost since I started going to the gym consistently? | 10 pounds | replaced old text with the new value | the block |
| `d7c942c3` | Is my mom using the same grocery list method as me? | Yes | inserted the new value | the block |
| `dfde3500` | What day of the week did I meet with my previous language exchange tutor Juan? | Wednesday | replaced old text with the new value | the block |
| `e61a7584` | How long have I had my cat, Luna? | 9 months | inserted the new value | the block |
| `f9e8c073` | How many sessions of the bereavement support group did I attend? | five | inserted the new value | the block |

Three patterns account for nearly all of them:

- **The revision was the moment the agent first wrote the fact down.** In
  many questions the first statement drew no memory edit at all, and the
  revision, which often came in a message more about the topic, did:
  "The user has been using their Fitbit Charge 3 for 9 months now"
  (`08e075c7`), "The user has 25 titles on their historical drama to-watch
  list" (`4d6b87c8`), "…a fan of Kansas City Masterpiece BBQ sauce on ribs"
  (`18bc8abd`). With no old value written there is nothing to be stale.
- **The replace kept the history in the line.** "The user has been living in
  Tokyo for 3 months now in a studio apartment in Harajuku (previously reported
  as 1 month, updated to 3)" (`2133c1b5`); "Rachel initially moved to Chicago,
  but she has since moved back to the suburbs" (`830ce83f`, answered from two
  inserted lines).
- **A short search with few matches.** Fourteen correct answers came from a
  search that returned the user's message, and the queries that worked were
  one or two distinctive words. When the block disagreed, the answer usually
  followed the dated message: in `6a1eabeb` the block said "ran a 5K charity
  run in 27:12", the search "5K run" returned "I'm hoping to beat my personal
  best time of 25:50", and the answer said 25:50; in `9ea5eabc` the block held
  only Hawaii, the search "family trip" returned the Paris message, and the
  answer said Paris.

One correct answer is luck. In `945e3d21` nothing about the yoga frequency was
in memory and the search "yoga" returned no message stating it. The answer:
"we haven't actually settled on a fixed frequency yet! In a recent planning
session, I suggested that you attend yoga **three days a week**… but you hadn't
confirmed if that was your current routine." The judge accepted three times a
week; the number was the agent's own suggestion.

## First run against the re-run

The first run sent each session in one request; the agent mostly took no
step, its `human` block stayed empty in 43 of 67 histories, and it answered by
searching. The re-run gave it a step per message:

| first run → re-run | questions |
|---|--:|
| correct → correct | 30 |
| wrong → correct | 16 |
| correct → wrong | 9 |
| wrong → wrong | 12 |

The fix gained 16 and lost 9, and the nine are informative: `06db6396`,
`1cea1afa`, `4b24c848`, `cc5ded98`, `ce6d2d27`, `6a27ffc2`, `db467c8c`,
`41698283` and `184da446`. In the first five the re-run's block held the old
value and the agent answered from it; with an empty block the first run had
searched and found the revision. The next three were lost to the search
(longer queries, and a history now full of the agent's own replies). The last
is the content filter. The first run's model calls were not logged, so its
queries are known only from the result files: shorter ones ("coding
exercises", "parents", "Corey Schafer", "H&M") over a message store that held
only the dataset's messages.

So writing memory helps Letta when the agent writes the revision and hurts it
when it writes only the first value: an empty block sends it to the history,
a stale block stops it there.

## What would change the outcome

What the logs support, not a tuned configuration:

- **A real search.** Each failure in the first three causes needed the history,
  and the history was reachable only through a phrase match limited to five
  messages. The tool description promises hybrid text and semantic search;
  that is what Letta's hosted service provides (through Turbopuffer) and what
  this self-hosted server does not. A self-hosted server can turn it on only
  with a Turbopuffer account (a paid hosted service) and an OpenAI key: the
  message index embeds with OpenAI's `text-embedding-3-small`, which is fixed
  in the Turbopuffer client rather than taken from the agent's embedding
  settings, so every other seat would stay on Gemini and this one would not. With a search that ranks by meaning over
  all messages, most of the 14 would likely have been found, as the first run
  found several of them.
- **An instruction to revise.** Nothing in the prompt asks the agent to check
  new statements against what it wrote. It noticed 18 revisions in its replies
  and wrote none of them.
- **The model.** The agent's memory policy is the model's judgement at
  temperature 1.0. The trace runs of `06db6396` and `0f05491a` came out
  differently from the scored run with the same history. A stronger model
  would change this row more than any other.

## Limits

- One run per question, at Letta's default temperature of 1.0; repeated runs
  can differ, as the traces show.
- The search simulation rebuilds the message store from the log and matches
  118 of the 144 real searches it can replay exactly; the counts in its table
  are close, not exact.
- The classification of each write (which edit recorded the new value) was
  made with a pattern per question and checked by reading every wrong answer
  and every correct one.
- The trimmed histories hold about ten sessions. With the whole history (~48
  sessions) the search problem would grow: more of the agent's own replies
  compete for the same five places.
