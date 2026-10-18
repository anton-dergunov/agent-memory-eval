# Full context: no memory, and what goes wrong anyway

Hand-written, from the replayed model calls of the full-context arm and the
result files in `results/main/full-context/` and `results/full/full-context/`.
Full context is the control: the whole trimmed history (about 28,000 tokens)
goes into the prompt, so every value said is in front of the answering model.
What it gets wrong is therefore about the questions and about the answering
model, not about memory.

## Summary

Full context answers 60 of 67 (90%, 95% interval 80–95%), at $0.007 per
question. Both values were in the prompt in all 58 questions with an old
value, and it chose correctly in 52.

| Cause | answers | questions |
|---|--:|---|
| The question or its key is flawed | 3 | `618f13b2`, `852ce960`, `e66b632c` |
| Both values in the prompt; the answer kept the first or reasoned back to it | 3 | `7401057b`, `830ce83f`, `ba61f0b9` |
| The answer kept the user's hedge instead of the key's number | 1 | `a2f3aa27` |

## Every wrong answer

"Other arms" are the seven other arms of the main run.

#### `7401057b` — "How many free night's stays can I redeem at any Hilton property with my accumulated points?" (two)

- 2023-05-29: "I've accumulated enough points for a single free night's stay at
  any Hilton property." 2023-05-30: "…I've accumulated enough points for two
  free night's stays at any Hilton property, so I might use that for a separate
  trip to Las Vegas."
- **Answer:** "Since you have explicitly confirmed that your current point
  balance is sufficient for a 'single free night's stay,' the answer is limited
  to one night." The second statement's "for a separate trip" made it read as a
  different plan. Other arms: 6 of 7 correct.

#### `830ce83f` — "Where did Rachel move to after her recent relocation?" (the suburbs)

- 2023-05-24: "…my friend Rachel who recently moved to a new apartment in the
  city." / "She moved to Chicago." 2023-05-27: "My friend Rachel actually just
  moved back to the suburbs again…"
- **Answer:** "The user confirms the location of Rachel's new apartment… Rachel
  moved to **Chicago**." The explicit "She moved to Chicago" outweighed the
  later aside. Other arms: 6 of 7 correct.

#### `ba61f0b9` — "How many women are on the team led by my former manager Rachel?" (6)

- 2023-01-18: "…who's now leading a team of 10 people… half of them are women."
  2023-07-20: "…my former manager Rachel's team is a great example of a diverse
  team, with 6 women out of 10 people."
- **Answer:** "the assistant's detailed breakdown in the 2023-07-20 session
  explicitly lists **5 specific women** by name and role (Sarah, Emily, Maya,
  Sofia, and Leila)… There are 5 women on the team led by Rachel." The
  dataset's own assistant reply had invented five names, and the model trusted
  that list over the user's six. Only a system that ignores the assistant's
  turns is immune to this. Other arms: 6 of 7 correct.

#### `a2f3aa27` — "How many followers do I have on Instagram now?" (1300)

- 05:26: "I've got 1250 followers on Instagram now." 09:28, the same day: "I
  think I'm close to 1300 now."
- **Answer:** "As of your last update on May 25, 2023, you were nearing 1300
  followers." The answer used the later statement and kept the user's own
  hedge; the judge wanted 1300. Four arms miss this question.

#### The flawed questions

- **`618f13b2`** (key: six): "Given that the most recent and repeated statement
  in the final session is 'four times,' it is likely that the 'six times'
  mentioned earlier was either a miscount…"
- **`852ce960`** (key: $400,000): "Based on the chronological record of our
  conversations, the first time you mentioned the pre-approval amount, you
  specified **$350,000**." It read "when I got my mortgage" as the first
  figure.
- **`e66b632c`** (key: 27:45): computed "approximately **28 minutes**" from
  "about a minute and a half" faster than 26:30.

## The full history

With all ~48 sessions (about 124,000 tokens) on 25 questions, accuracy goes from
92% to 84%. All four errors have the new value in the prompt and the old one in
the answer:

- `7401057b`: one night again ("based on your most recent confirmation regarding
  your current balance, you have enough for one night"), now with the two-night
  statement acknowledged and set aside.
- `830ce83f`: Chicago again.
- `6a1eabeb`: "The chat history explicitly states your personal best time for
  the charity 5K run as 27:12", missing the later 25:50.
- `0f05491a`: 125 stars, the earlier figure, after "a back-and-forth regarding the
  specific star requirement".

On 25 questions that is two answers more than on the trimmed history, inside the
interval; the paper's GPT-4o fell from 0.87 to 0.61 on the same histories.

## What this says about the other arms

Every value is delivered here, and the answering model still keeps the first of
two values in about one question in ten where both appear. Memory systems that
deliver both values inherit this rate; the ones that do better (retrieval,
Honcho's representation) deliver less around the two values, so there is less
to reason back from.
