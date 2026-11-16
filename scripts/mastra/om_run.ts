// One run of Mastra's Observational Memory on one LongMemEval history, for part 9 of
// the blog series ("What ChatGPT, Claude and Gemini ship").
//
// The whole history of one knowledge-update question is fed into one Mastra thread,
// session by session, in date order, with Mastra's default settings (thread scope,
// 30,000 and 40,000 tokens). After each session the Observer is asked to run, and it
// observes only when the unobserved messages pass its threshold. The only model calls
// while feeding are the Observer's and the Reflector's. Then the question is asked on
// the same thread by a real model. Run with TZ=UTC so that the times the Observer
// writes match the dataset's.
//
// Every model call (prompt, reply, tokens) is written to <run dir>/calls.jsonl, and the
// observation log, its history and the answer to <run dir>/result.json.
//
// Model calls: Gemini API free tier, gemini-3.1-flash-lite (the series' model).
//
//   npm install && npx tsx om_run.ts --question 6a1eabeb --out runs/<name>
//   options: --sessions N (feed only the first N sessions), --message-tokens T,
//            --observation-tokens T (defaults: Mastra's, 30000 and 40000),
//            --reflect (call the Reflector once more after the answer, to see it work),
//            --observe-tail (observe the unobserved tail before the question is asked)

import { mkdirSync, readFileSync, writeFileSync, appendFileSync, rmSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { config as loadEnv } from 'dotenv';
import { Agent } from '@mastra/core/agent';
import { Memory } from '@mastra/memory';
import { LibSQLStore } from '@mastra/libsql';
import { createGoogleGenerativeAI } from '@ai-sdk/google';
import { wrapLanguageModel } from 'ai';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '..', '..');
loadEnv({ path: join(repo, '.env'), quiet: true });

const { values: args } = parseArgs({
  options: {
    question: { type: 'string', default: '6a1eabeb' },
    out: { type: 'string', default: 'runs/default' },
    sessions: { type: 'string' },
    'message-tokens': { type: 'string' },
    'observation-tokens': { type: 'string' },
    reflect: { type: 'boolean', default: false },
    'observe-tail': { type: 'boolean', default: false },
  },
});

const MODEL = 'gemini-3.1-flash-lite';
const MIN_GAP_MS = 4_500; // the free tier allows 15 requests a minute for this model

const runDir = resolve(here, args.out!);
rmSync(runDir, { recursive: true, force: true });
mkdirSync(runDir, { recursive: true });
const callsPath = join(runDir, 'calls.jsonl');

// --- The model, with every call logged -------------------------------------------------

let lastCall = 0;
let callIndex = 0;
let phase = 'feed';

async function throttle() {
  const wait = lastCall + MIN_GAP_MS - Date.now();
  if (wait > 0) await new Promise(r => setTimeout(r, wait));
  lastCall = Date.now();
}

function promptText(prompt: any[]): { role: string; text: string }[] {
  return prompt.map(m => ({
    role: m.role,
    text:
      typeof m.content === 'string'
        ? m.content
        : m.content.map((p: any) => (p.type === 'text' ? p.text : `[${p.type}]`)).join(''),
  }));
}

function logCall(kind: string, params: any, text: string, usage: any) {
  callIndex++;
  appendFileSync(
    callsPath,
    JSON.stringify({
      index: callIndex,
      phase,
      kind,
      prompt: promptText(params.prompt),
      settings: { temperature: params.temperature, maxOutputTokens: params.maxOutputTokens, providerOptions: params.providerOptions },
      reply: text,
      usage,
    }) + '\n',
  );
  console.log(`  call ${callIndex} (${phase}, ${kind}): in ${usage?.inputTokens?.total ?? usage?.inputTokens} out ${usage?.outputTokens?.total ?? usage?.outputTokens}`);
}

const google = createGoogleGenerativeAI({ apiKey: process.env.GEMINI_API_KEY });
const gemini = wrapLanguageModel({
  model: google(MODEL),
  middleware: {
    specificationVersion: 'v4',
    wrapGenerate: async ({ doGenerate, params }) => {
      await throttle();
      const result = await doGenerate();
      const text = result.content.map((p: any) => (p.type === 'text' ? p.text : '')).join('');
      logCall('generate', params, text, result.usage);
      return result;
    },
    wrapStream: async ({ doStream, params }) => {
      await throttle();
      const { stream, ...rest } = await doStream();
      let text = '';
      let usage: any;
      const logged = stream.pipeThrough(
        new TransformStream({
          transform(chunk: any, controller) {
            if (chunk.type === 'text-delta') text += chunk.delta;
            if (chunk.type === 'finish') usage = chunk.usage;
            controller.enqueue(chunk);
          },
          flush() {
            logCall('stream', params, text, usage);
          },
        }),
      );
      return { stream: logged, ...rest };
    },
  } as any,
});


// --- Memory: Mastra's defaults, except the model ----------------------------------------

const observation: Record<string, number> = {};
if (args['message-tokens']) observation.messageTokens = Number(args['message-tokens']);
const reflection: Record<string, number> = {};
if (args['observation-tokens']) reflection.observationTokens = Number(args['observation-tokens']);

const memory = new Memory({
  storage: new LibSQLStore({ id: 'om-run', url: `file:${join(runDir, 'memory.db')}` }),
  options: {
    observationalMemory: { model: gemini as any, observation, reflection },
  },
});


// --- The question and its history --------------------------------------------------------

const data = JSON.parse(readFileSync(join(repo, 'data', 'longmemeval_s_cleaned.json'), 'utf8'));
const q = data.find((x: any) => x.question_id === args.question);
if (!q) throw new Error(`question ${args.question} not found`);

// "2023/05/30 (Tue) 13:53" -> Date (UTC)
function lmeDate(s: string): Date {
  const m = s.match(/(\d{4})\/(\d{2})\/(\d{2}) \(\w+\) (\d{2}):(\d{2})/)!;
  return new Date(Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]));
}

// Sessions in date order, as the experiment in part 8 feeds them.
let sessions = q.haystack_session_ids
  .map((id: string, i: number) => ({ id, date: lmeDate(q.haystack_dates[i]), turns: q.haystack_sessions[i] }))
  .sort((a: any, b: any) => a.date.getTime() - b.date.getTime());
if (args.sessions) sessions = sessions.slice(0, Number(args.sessions));

const thread = `lme-${q.question_id}`;
const resource = 'lme-user';
const memoryOpts = { thread, resource };

console.log(`question ${q.question_id}: ${sessions.length} sessions, thread ${thread}`);

const om = await memory.omEngine;
if (!om) throw new Error('Observational Memory is not enabled');

// An agent turn stamps its input messages with the time of the run, so the Observer would
// date every observation "today". Instead each user/assistant pair is saved to storage with
// its own dates, and then the step that a turn runs is run by hand, as getStatus()
// documents it: activate buffered observations at the threshold, observe synchronously
// past blockAfter, buffer in between, and reflect when the log passes its threshold.
// Buffering and reflection are awaited here; in a live agent they run in the background.
const ids = { threadId: thread, resourceId: resource };
const events: any[] = [];
async function step(label: string) {
  const st = await om!.getStatus(ids);
  let did = '';
  if (st.shouldObserve && st.canActivate) {
    did = 'activate';
    await om!.activate(ids);
  } else if (st.shouldObserve && !st.inAsyncObservationBand) {
    did = 'observe';
    await om!.observe({ ...ids, trigger: 'manual' as any });
  } else if (st.shouldBuffer) {
    did = 'buffer';
    await om!.buffer({ ...ids, pendingTokens: st.pendingTokens });
  }
  const after = await om!.getStatus(ids);
  if (after.shouldReflect) {
    did += (did ? '+' : '') + 'reflect';
    await om!.reflect(thread, resource);
  }
  if (did) {
    const rec = await om!.getRecord(thread, resource);
    events.push({ at: label, did, pendingTokens: st.pendingTokens, observationTokens: rec?.observationTokenCount, generation: rec?.generationCount });
    console.log(`  ${label}: ${did} (pending ${st.pendingTokens}, log ${rec?.observationTokenCount} tokens)`);
  }
}

await memory.saveThread({ thread: { id: thread, resourceId: resource, title: thread, createdAt: sessions[0].date, updatedAt: sessions[0].date } });
for (const [si, s] of sessions.entries()) {
  phase = `feed:${si + 1}:${s.id}`;
  console.log(`session ${si + 1}/${sessions.length} ${s.id} ${s.date.toISOString()} (${s.turns.length} turns)`);
  const messages = s.turns
    .filter((t: any) => t.content)
    .map((t: any, ti: number) => ({
      id: `${s.id}-${ti}`,
      threadId: thread,
      resourceId: resource,
      role: t.role === 'assistant' ? 'assistant' : 'user',
      createdAt: new Date(s.date.getTime() + ti * 5_000), // 5 s apart, as Mastra's runner does
      content: { format: 2, parts: [{ type: 'text', text: t.content }] },
    }));
  for (let i = 0; i < messages.length; i += 2) {
    await memory.saveMessages({ messages: messages.slice(i, i + 2) as any });
    await step(`${si + 1}:${s.id}:${i / 2 + 1}`);
  }
}
await om.settled(ids);

async function snapshot() {
  const record = await om!.getRecord(thread, resource);
  const status = await om!.getStatus({ threadId: thread, resourceId: resource });
  return { record, status };
}

if (args['observe-tail']) {
  phase = 'observe-tail';
  await om.observe({ ...ids, force: true, trigger: 'manual' as any });
}

const beforeAnswer = await snapshot();
writeFileSync(join(runDir, 'record-before-answer.json'), JSON.stringify(beforeAnswer, null, 2));

// --- The question, asked on the same thread by a real model -----------------------------

// The clock is set to the question's date, so that the dates Mastra adds ("3 weeks ago")
// and the date of the question itself are the ones a user asking then would see.
const asked = lmeDate(q.question_date);
{
  const RealDate = Date;
  const offset = asked.getTime() - RealDate.now();
  class ShiftedDate extends RealDate {
    constructor(...a: any[]) {
      if (a.length === 0) super(RealDate.now() + offset);
      else super(...(a as [any]));
    }
    static now() {
      return RealDate.now() + offset;
    }
  }
  (globalThis as any).Date = ShiftedDate;
}

phase = 'answer';
const answerer = new Agent({
  id: 'answerer',
  name: 'answerer',
  instructions: 'You are a helpful assistant.',
  model: gemini as any,
  memory,
});
const answer = await answerer.generate(q.question, {
  memory: memoryOpts,
});
await om.settled({ threadId: thread, resourceId: resource });
const afterAnswer = await snapshot();

let afterReflect: any = null;
if (args.reflect) {
  phase = 'reflect';
  const r = await om.reflect(thread, resource);
  afterReflect = { reflected: r.reflected, usage: r.usage, ...(await snapshot()) };
}

const history = await om.getHistory(thread, resource);

writeFileSync(
  join(runDir, 'result.json'),
  JSON.stringify(
    {
      question_id: q.question_id,
      question: q.question,
      question_date: q.question_date,
      expected: q.answer,
      model: MODEL,
      packages: JSON.parse(readFileSync(join(here, 'package.json'), 'utf8')).dependencies,
      settings: { observation, reflection, scope: 'default (thread)', observeTail: args['observe-tail'] },
      events,
      sessions: sessions.map((s: any) => ({ id: s.id, date: s.date.toISOString(), turns: s.turns.length })),
      answer: answer.text,
      calls: callIndex,
      afterAnswer,
      afterReflect,
      history,
    },
    null,
    2,
  ),
);
console.log(`\nanswer: ${answer.text}\nexpected: ${q.answer}\ncalls: ${callIndex}\nrun: ${runDir}`);
process.exit(0);
