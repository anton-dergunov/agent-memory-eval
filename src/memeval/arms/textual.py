"""Textual memory: one plain-text profile, rewritten whole after every session.

The simplest member of the "background rewriter" family, after PersonaMem-v3's
Textual Memory baseline: a separate call reads the current profile and the new
session and writes the profile again from scratch, under a size cap. The
answering model never writes; the read path is the whole profile. The prompt
is ours.
"""

from .. import llm
from ..data import Question, Session, render_session
from .base import Arm, Read

CAP_WORDS = 3000  # about 4,000 tokens, PersonaMem-v3's cap

REWRITE = """\
You maintain a memory profile of a user for an assistant that will talk to \
them again later. Below is the current profile and a new conversation between \
the user and the assistant. Rewrite the whole profile so that it reflects \
everything known about the user after this conversation.

Rules:
- Keep everything from the current profile that is still true. Add what the \
new conversation reveals about the user: facts about their life, possessions, \
people, numbers, dates, plans, preferences and habits. Be specific.
- When the new conversation changes or contradicts something in the profile, \
replace it with the new information and record that it changed, with dates \
(for example "Now X, since 2023-05-26; previously Y").
- Write dates as absolute dates, resolving words like "last week" against the \
conversation's date.
- Ignore general information the assistant provided unless the user adopted it.
- Use these four headings: Personal facts; Preferences and habits; Ongoing \
situations and plans; Changes over time.
- At most {cap} words. Return only the profile.

Current profile:
{profile}

New conversation:
{session}"""


class TextualMemory(Arm):
    name = "textual"

    def settings(self) -> dict:
        return {"cap_words": CAP_WORDS, "rewrite": "whole profile after each session"}

    def reset(self, q: Question) -> None:
        self.profile = ""

    def ingest(self, session: Session) -> None:
        reply = llm.generate(REWRITE.format(cap=CAP_WORDS, profile=self.profile or "(empty)",
                                            session=render_session(session)))
        self.profile = reply.text

    def read(self, q: Question) -> Read:
        return Read(context=self.profile)

    def dump(self) -> str:
        return self.profile
