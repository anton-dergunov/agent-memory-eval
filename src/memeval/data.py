"""LongMemEval's knowledge-update questions, split and trimmed with a fixed seed.

Each LongMemEval question comes with its own chat history of about 48 sessions,
two of which (for this question type) hold the evidence: the fact as first
stated and the later revision. The main runs keep both evidence sessions and 8
distractors drawn at random, in their original order and with their original
dates. The full-history run keeps all of them.

Abstention questions (ids ending in `_abs`) ask about something that was never
said; they test refusing rather than updating, so they are left out.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache

from . import config

SEED = 0
PILOT_SIZE = 5
DISTRACTORS = 8
FULL_HISTORY_SIZE = 25


@dataclass
class Turn:
    role: str
    content: str


@dataclass
class Session:
    id: str
    date: datetime
    turns: list[Turn]
    evidence: bool = False


@dataclass
class Question:
    qid: str
    question: str
    answer: str
    date: datetime
    sessions: list[Session] = field(default_factory=list)


def parse_date(text: str) -> datetime:
    """LongMemEval writes dates as `2023/06/25 (Sun) 13:22`."""
    day, _, clock = text.split(" ")
    return datetime.strptime(f"{day} {clock}", "%Y/%m/%d %H:%M")


@lru_cache(maxsize=1)
def load_raw() -> tuple:
    blob = config.DATA_FILE.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != config.DATA_SHA256:
        raise RuntimeError(f"{config.DATA_FILE} has sha256 {digest}, expected {config.DATA_SHA256}")
    return tuple(json.loads(blob))


def knowledge_update_ids(raw=None) -> list[str]:
    raw = raw if raw is not None else load_raw()
    ids = [x["question_id"] for x in raw
           if x["question_type"] == "knowledge-update" and not x["question_id"].endswith("_abs")]
    random.Random(SEED).shuffle(ids)
    return ids


def split(name: str, raw=None) -> list[str]:
    """`pilot`: 5 questions for tuning. `main`: every other question.
    `full`: the first 25 of `main`, run again with the whole history."""
    ids = knowledge_update_ids(raw)
    if name == "pilot":
        return ids[:PILOT_SIZE]
    if name == "main":
        return ids[PILOT_SIZE:]
    if name == "full":
        return ids[PILOT_SIZE:PILOT_SIZE + FULL_HISTORY_SIZE]
    raise ValueError(f"unknown split {name!r}")


def question(qid: str, *, full_history: bool = False, raw=None) -> Question:
    raw = raw if raw is not None else load_raw()
    entry = next(x for x in raw if x["question_id"] == qid)
    evidence_ids = set(entry["answer_session_ids"])
    sessions = [
        Session(id=sid, date=parse_date(date), evidence=sid in evidence_ids,
                turns=[Turn(t["role"], t["content"]) for t in turns if t["content"].strip()])
        for sid, date, turns in zip(entry["haystack_session_ids"], entry["haystack_dates"],
                                    entry["haystack_sessions"])
    ]
    if len([s for s in sessions if s.evidence]) != len(evidence_ids):
        raise RuntimeError(f"{qid}: evidence sessions missing from the haystack")
    if not full_history:
        others = [i for i, s in enumerate(sessions) if not s.evidence]
        keep = set(random.Random(f"{SEED}:{qid}").sample(others, min(DISTRACTORS, len(others))))
        sessions = [s for i, s in enumerate(sessions) if s.evidence or i in keep]
    # Stable sort: sessions on the same minute keep their original order.
    sessions.sort(key=lambda s: s.date)
    return Question(qid=qid, question=entry["question"], answer=entry["answer"],
                    date=parse_date(entry["question_date"]), sessions=sessions)


def render_session(session: Session) -> str:
    lines = [f"[Session date: {session.date:%Y-%m-%d %H:%M}]"]
    lines += [f"{t.role}: {t.content}" for t in session.turns]
    return "\n".join(lines)
