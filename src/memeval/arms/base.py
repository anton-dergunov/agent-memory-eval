"""The interface every arm implements.

One question at a time: `reset` starts an empty memory, `ingest` is called
once per session in date order, `finish` marks the end of the history, and
`read` is what the system returns for the question. An arm either returns a
context for the shared answer prompt or, if answering is part of the system
(Letta), its own answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .. import llm, prompts
from ..data import Question, Session


@dataclass
class Read:
    context: str
    answer: str | None = None
    extra: dict = field(default_factory=dict)


class Arm:
    name = "arm"
    # Which shared prompt turns this arm's context into an answer.
    answer_prompt = prompts.ANSWER_FROM_MEMORY

    def settings(self) -> dict:
        """Every setting that could change a result, for the manifest."""
        return {}

    def reset(self, q: Question) -> None:
        raise NotImplementedError

    def ingest(self, session: Session) -> None:
        raise NotImplementedError

    def finish(self) -> None:
        """Called after the last session, before the question."""

    def read(self, q: Question) -> Read:
        raise NotImplementedError

    def reads(self, q: Question) -> dict[str, Read]:
        """One read per reported arm. An arm whose store supports two read
        paths (Honcho) returns both, so the store is built once."""
        return {self.name: self.read(q)}

    def dump(self) -> str | None:
        """Everything the memory holds, as text, for the `stored?` probe.
        None for arms that store the raw history (stored by construction)."""
        return None

    def close(self) -> None:
        """Release servers, files, connections."""

    def answer(self, q: Question, context: str) -> str:
        prompt = self.answer_prompt.format(context=context or "(nothing)",
                                           date=f"{q.date:%Y/%m/%d %H:%M}",
                                           question=q.question)
        return llm.generate(prompt).text
