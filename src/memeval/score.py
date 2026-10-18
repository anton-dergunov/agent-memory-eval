"""The judge and the probes, added to each result file by `run score`.

* `judge`: LongMemEval's knowledge-update judge on the arm's answer.
* `judge_check`: the same prompt on the probe model, for a fixed subset of
  questions, to report how often the two judges agree.
* `facts`: the value before the revision, read once per question from the
  first evidence session. The other probes need it.
* `probe`: was the new value written (`stored`), did it reach the answering
  model (`delivered`), and did the answer give the old value (`stale`).
"""

from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor

from . import config, data, llm, prompts

# Questions judged by both models, for the agreement figure: every pilot
# question and the first 12 of the main split, each across all arms.
CALIBRATION = 12


def parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError(f"no JSON in reply: {text[:200]!r}")
    return json.loads(match.group(0))


def judge(question: str, reference: str, response: str, model: str) -> bool:
    prompt = prompts.JUDGE_KNOWLEDGE_UPDATE.format(question=question, answer=reference,
                                                   response=response)
    reply = llm.generate(prompt, model=model).text.strip().lower()
    return reply.startswith("yes") or (reply.find("yes") != -1 and reply.find("no") == -1)


def facts(split: str, qid: str) -> dict:
    path = config.RESULTS_DIR / split / "_facts" / f"{qid}.json"
    if path.exists():
        return json.loads(path.read_text())
    q = data.question(qid)
    first, second = [s for s in q.sessions if s.evidence][:2]
    reply = llm.generate(prompts.OLD_VALUE.format(first=data.render_session(first),
                                                  second=data.render_session(second),
                                                  question=q.question, answer=q.answer),
                         model=config.PROBE_MODEL, json_output=True)
    out = {"qid": qid, "question": q.question, **parse_json(reply.text)}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    return out


def probe(result: dict, fact: dict) -> dict:
    old, new = fact.get("old_value"), fact.get("new_value") or result["reference"]
    if not old:
        return {"skipped": "no old value in the first evidence session"}
    common = {"question": result["question"], "old": old, "new": new}
    out = {}
    if result["dump"] is not None:
        out["stored"] = parse_json(llm.generate(
            prompts.STORED.format(memory=result["dump"] or "(empty)", **common),
            model=config.PROBE_MODEL, json_output=True).text)
    if result["arm"] == "full-context":
        # The context is the whole history, so both values are in it by construction.
        out["delivered"] = {"new_present": True, "old_present": True, "by_construction": True}
    else:
        out["delivered"] = parse_json(llm.generate(
            prompts.DELIVERED.format(context=result["context"] or "(empty)", **common),
            model=config.PROBE_MODEL, json_output=True).text)
    out["stale"] = parse_json(llm.generate(
        prompts.STALE.format(response=result["answer"], **common),
        model=config.PROBE_MODEL, json_output=True).text)
    return out


def score_split(split: str, arms: list[str] | None = None, workers: int = 8) -> None:
    root = config.RESULTS_DIR / split
    arms = arms or sorted(p.name for p in root.iterdir() if p.is_dir() and not p.name.startswith("_"))
    paths = [(arm, path) for arm in arms for path in sorted((root / arm).glob("*.json"))]
    # The old values first, once per question, so threads do not race for them.
    for qid in sorted({p.stem for _, p in paths}):
        with llm.tagged(split=split, arm="_facts", qid=qid, phase="probe"):
            facts(split, qid)
    with ThreadPoolExecutor(workers) as pool:
        for future in [pool.submit(_score_one, split, arm, path) for arm, path in paths]:
            future.result()


def _score_one(split: str, arm: str, path) -> None:
    calibration = set(data.split("pilot")) | set(data.split("main")[:CALIBRATION])
    result = json.loads(path.read_text())
    qid = result["qid"]
    changed = False
    with llm.tagged(local=True, split=split, arm=arm, qid=qid, phase="judge"):
        if "judge" not in result:
            result["judge"] = {"model": config.JUDGE_MODEL,
                               "correct": judge(result["question"], result["reference"],
                                                result["answer"], config.JUDGE_MODEL)}
            changed = True
        if qid in calibration and "judge_check" not in result:
            result["judge_check"] = {"model": config.PROBE_MODEL,
                                     "correct": judge(result["question"], result["reference"],
                                                      result["answer"], config.PROBE_MODEL)}
            changed = True
    with llm.tagged(local=True, split=split, arm=arm, qid=qid, phase="probe"):
        if "probe" not in result:
            result["probe"] = probe(result, facts(split, qid))
            changed = True
    if changed:
        path.write_text(json.dumps(result, indent=1, ensure_ascii=False))
    print(f"[score] {arm} {qid} correct={result['judge']['correct']}", flush=True)
