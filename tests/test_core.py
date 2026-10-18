"""Checks that need no API key: data handling, the cache, the budget stop, the
baseline arms and the report, with the model replaced by a stub."""

import json
from datetime import datetime

import pytest

from memeval import config, data, llm, report
from memeval.arms import build


def raw_entry(qid, n_sessions=12, evidence=(3, 9)):
    sessions, ids, dates = [], [], []
    for i in range(n_sessions):
        sid = f"answer_{qid}_{i}" if i in evidence else f"s{i}"
        ids.append(sid)
        dates.append(f"2023/05/{i + 1:02d} (Mon) 10:00")
        fact = f"My personal best is {25 + i} minutes." if i in evidence else f"Talk about topic {i}."
        sessions.append([{"role": "user", "content": fact},
                         {"role": "assistant", "content": f"Noted, session {i}."}])
    return {"question_id": qid, "question_type": "knowledge-update",
            "question": "What is my personal best?", "answer": "34 minutes",
            "question_date": "2023/06/01 (Thu) 09:00",
            "answer_session_ids": [ids[i] for i in evidence],
            "haystack_session_ids": ids, "haystack_dates": dates, "haystack_sessions": sessions}


@pytest.fixture
def raw():
    entries = [raw_entry(f"q{i}") for i in range(40)]
    entries.append({**raw_entry("q0_abs"), "question_id": "q0_abs"})
    entries.append({**raw_entry("other"), "question_type": "multi-session"})
    return entries


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path / "cache")
    monkeypatch.setattr(config, "LEDGER_DIR", tmp_path / "ledger")
    monkeypatch.setattr(config, "RESULTS_DIR", tmp_path / "results")
    llm._spent_cache.update(at=0.0, usd=0.0)


def test_splits_are_disjoint_and_skip_abstention(raw):
    pilot, main, full = data.split("pilot", raw), data.split("main", raw), data.split("full", raw)
    assert len(pilot) == 5 and len(main) == 35
    assert not set(pilot) & set(main)
    assert set(full) <= set(main)
    assert "q0_abs" not in pilot + main
    assert data.split("pilot", raw) == pilot  # deterministic


def test_trim_keeps_evidence_order_and_dates(raw):
    q = data.question("q1", raw=raw)
    assert len(q.sessions) == 2 + data.DISTRACTORS
    assert sum(s.evidence for s in q.sessions) == 2
    assert [s.date for s in q.sessions] == sorted(s.date for s in q.sessions)
    assert q.date == datetime(2023, 6, 1, 9, 0)
    assert len(data.question("q1", raw=raw, full_history=True).sessions) == 12
    again = data.question("q1", raw=raw)
    assert [s.id for s in again.sessions] == [s.id for s in q.sessions]


def test_budget_stops_calls(monkeypatch):
    monkeypatch.setattr(config, "BUDGET_USD", 0.01)
    llm.record("gemini-3.1-flash-lite", 100_000, 0)  # $0.025
    llm._spent_cache["at"] = 0.0
    with pytest.raises(llm.BudgetExceeded):
        llm.check_budget()


def test_cache_round_trip():
    key = llm.cache_key("x", 1)
    assert llm.cache_get(key) is None
    llm.cache_put(key, {"a": 1})
    assert llm.cache_get(key) == {"a": 1}


def test_price():
    assert config.price("gemini-3.1-flash-lite", 1_000_000, 1_000_000) == pytest.approx(1.75)
    assert config.price("google/gemini-3.8-flash", 1_000_000, 0) == pytest.approx(0.75)




def test_baselines_end_to_end(raw, monkeypatch):
    seen = []

    def fake_generate(prompt, **kwargs):
        seen.append(prompt)
        return llm.Reply(text="Your personal best is 34 minutes.")

    monkeypatch.setattr(llm, "generate", fake_generate)
    q = data.question("q1", raw=raw)
    for name in ("full-context", "retrieval"):
        arm = build(name)
        arm.reset(q)
        for s in q.sessions:
            arm.ingest(s)
        arm.finish()
        read = arm.read(q)
        assert "34 minutes" in read.context  # the latest evidence session is reachable
        assert "[Session date:" in read.context
        assert arm.answer(q, read.context).startswith("Your personal best")
    assert "Current Date: 2023/06/01 09:00" in seen[0]


def test_report_tables(tmp_path):
    root = config.RESULTS_DIR / "pilot" / "full-context"
    root.mkdir(parents=True)
    for i, ok in enumerate([True, False]):
        (root / f"q{i}.json").write_text(json.dumps({
            "qid": f"q{i}", "judge": {"correct": ok}, "dump": None, "context": "ctx", "answer": "a",
            "probe": {"delivered": {"new_present": True}, "stale": {"gave_old": not ok}}}))
    llm.record("gemini-3.1-flash-lite", 1000, 100,
               tags={"split": "pilot", "arm": "full-context", "qid": "q0", "phase": "answer"})
    text = report.report("pilot")
    assert "| full-context | 2 | 50% |" in text
    assert "delivered, answered old value" in text
