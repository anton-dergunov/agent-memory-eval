"""Smoke-test one arm on a tiny hand-written revision, before paying for a run.

    python infra/check_arm.py honcho

Two sessions two months apart: the user states a fact, then revises it. The
check prints what the system stored and returned and flags the failures that
have historically looked like results: an empty store, conclusions dated the
day of the run instead of the conversation, and an answer with the old value.
"""

import re
import sys
from datetime import date, datetime

from memeval import config, llm
from memeval.arms import build
from memeval.data import Question, Session, Turn

SESSIONS = [
    Session("check-1", datetime(2023, 1, 12, 7, 30), [
        Turn("user", "I'm training for the spring half marathon. I run 20 km a week, before work."),
        Turn("assistant", "Great. Want a four-week plan with early sessions?"),
        Turn("user", "Yes, but nothing on Sundays. My best 10K time is 52:40, by the way."),
        Turn("assistant", "Noted: six days a week, Sundays off."),
    ], evidence=True),
    Session("check-2", datetime(2023, 3, 9, 7, 30), [
        Turn("user", "Update: I dropped the half marathon, my knee hurts. I swim three times a week now."),
        Turn("assistant", "Sensible. I'll stop suggesting running mileage."),
        Turn("user", "Also I finally broke my 10K record last week: 49:15!"),
        Turn("assistant", "Congratulations, that's a big improvement."),
    ], evidence=True),
]
QUESTION = Question("check", "What is my current best 10K time?", "49:15",
                    datetime(2023, 4, 1, 9, 0), SESSIONS)


def main(name: str) -> int:
    config.ensure_credentials()
    arm = build(name)
    problems = []
    try:
        with llm.tagged(split="check", arm=name, qid="check", phase="write"):
            arm.reset(QUESTION)
            for s in SESSIONS:
                arm.ingest(s)
            arm.finish()
        with llm.tagged(split="check", arm=name, qid="check", phase="read"):
            reads = arm.reads(QUESTION)
        dump = arm.dump()
        print("=== stored ===\n" + (dump or "(raw history)"))
        if dump is not None and not dump.strip():
            problems.append("the store is empty")
        if dump and str(date.today().year) in dump and "2023" not in dump:
            problems.append("stored dates are today's, not the conversation's")
        for variant, read in reads.items():
            answer = read.answer if read.answer is not None else arm.answer(QUESTION, read.context)
            print(f"=== {variant}: context ===\n{read.context}\n=== {variant}: answer ===\n{answer}")
            if not re.search(r"49\D{1,15}15", answer):
                problems.append(f"{variant} did not answer with the new value")
            if not read.context.strip():
                problems.append(f"{variant} returned an empty context")
    finally:
        arm.close()
    print(f"\nspent so far ${llm.spent():.3f}")
    for p in problems:
        print("PROBLEM:", p)
    print("looks right" if not problems else "")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
