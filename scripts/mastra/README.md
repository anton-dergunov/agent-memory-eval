# One run of Mastra's Observational Memory

A check behind part 9 of the blog series (*What ChatGPT, Claude and Gemini ship*): Mastra's Observational Memory, an open-source design close to what the chat products describe, run on one LongMemEval knowledge-update question (`6a1eabeb`, the 5K question of part 8) with its whole history: 40 sessions, 413 turns, about 108,000 tokens.

- `om_run.ts` feeds the history into one Mastra thread, pair by pair and in date order, with Mastra's default settings (`@mastra/memory` 1.41.1: thread scope, Observer at 30,000 tokens with buffering every 6,000, Reflector at 40,000) and `gemini-3.1-flash-lite`. After each pair it runs the step a live agent turn runs (`getStatus()`, then activate, observe, buffer or reflect). Then it asks the question on the same thread, with the clock set to the question's date, and optionally calls the Reflector once more (`--reflect`).
- `runs/<name>/calls.jsonl` holds every model call: the full prompt, the reply and the tokens. `result.json` holds the observation log before and after, its history, and the answer.
- `om_summary.py` prints what the post quotes; its output is `om_summary_output.txt`.

Two runs are kept: the default flow (the newest sessions still unobserved when the question comes), and one with the unobserved tail observed first (`--observe-tail`).

Run it from this folder (Gemini API free tier, about ten calls a run; the key is read from the repository's `.env`; the dataset from `data/`):

```sh
npm install
TZ=UTC npx tsx om_run.ts --question 6a1eabeb --reflect --out runs/<name>
python3 om_summary.py
```

Model replies vary from run to run, so a rerun can store different lines and give a different answer; the mechanism stays the same.

How this differs from a live agent: messages are saved to storage with their dataset dates instead of being sent through an agent turn (a turn stamps its input with the time of the run, and the Observer would date every observation "today"), and buffering and reflection are awaited instead of running in the background.
