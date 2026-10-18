"""Full context: no memory system. Every session goes into the prompt.

The control row. At about 28,000 tokens per question the whole trimmed history
fits easily, so this is close to the ceiling a memory layer can only lose to.
"""

from .. import prompts
from ..data import Question, Session, render_session
from .base import Arm, Read


class FullContext(Arm):
    name = "full-context"
    answer_prompt = prompts.ANSWER_FROM_HISTORY

    def reset(self, q: Question) -> None:
        self.sessions: list[Session] = []

    def ingest(self, session: Session) -> None:
        self.sessions.append(session)

    def read(self, q: Question) -> Read:
        return Read(context="\n\n".join(render_session(s) for s in self.sessions))
