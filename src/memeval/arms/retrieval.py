"""Plain retrieval over raw turns: nothing is written but an index.

The unit is one round (a user turn and the assistant reply after it), the
granularity LongMemEval's own retrieval experiments found best. BM25, the top
10 rounds, each labelled with its session date and put back in date order.
"""

import re

from rank_bm25 import BM25Okapi

from .. import prompts
from ..data import Question, Session
from .base import Arm, Read

TOP_K = 10


def words(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


class Retrieval(Arm):
    name = "retrieval"
    answer_prompt = prompts.ANSWER_FROM_HISTORY

    def settings(self) -> dict:
        return {"index": "BM25Okapi (rank-bm25 defaults)", "unit": "round", "top_k": TOP_K}

    def reset(self, q: Question) -> None:
        self.rounds: list[tuple] = []  # (date, position, text)

    def ingest(self, session: Session) -> None:
        current: list[str] = []
        for turn in session.turns:
            if turn.role == "user" and current:
                self.rounds.append((session.date, len(self.rounds), "\n".join(current)))
                current = []
            current.append(f"{turn.role}: {turn.content}")
        if current:
            self.rounds.append((session.date, len(self.rounds), "\n".join(current)))

    def read(self, q: Question) -> Read:
        index = BM25Okapi([words(text) for _, _, text in self.rounds])
        scores = index.get_scores(words(q.question))
        top = sorted(range(len(self.rounds)), key=lambda i: -scores[i])[:TOP_K]
        hits = sorted(self.rounds[i] for i in top)
        context = "\n\n".join(f"[Session date: {date:%Y-%m-%d %H:%M}]\n{text}" for date, _, text in hits)
        return Read(context=context)
