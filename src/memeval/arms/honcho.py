"""Honcho, the real self-hosted server: a background reasoner over the conversation.

Messages go in; Honcho's deriver extracts explicit conclusions about the user
in the background, and a "dream" pass later derives deductive and inductive
conclusions and marks contradictions. Two read paths are reported from the
same store:

* `honcho-chat`: `peer.chat(question)`, Honcho's dialectic agent, which
  searches the conclusions with tools and answers. Its reply is handed to the
  shared answer prompt like any other memory.
* `honcho-repr`: `peer.representation(search_query=question)`, retrieval over
  the derived conclusions with no model call.

The server runs from `infra/honcho/up.sh`, with every model role pointed at
`memeval.proxy` on port 8100. What this wrapper does beyond calling the SDK,
each for a reason found the hard way:

* **Message dates.** Without `created_at` Honcho stamps every message with the
  moment of ingestion, so no conclusion can supersede another.
* **A workspace per question,** with plain peer ids ("user", "assistant").
  Honcho writes the peer id into every conclusion, so a random id would end up
  in the text the answering model reads.
* **The assistant is a peer Honcho does not model** (`observe_me=False`). Its
  turns are still context for the user's.
* **One dream after the history.** Honcho starts a dream on its own only after
  50 new conclusions and 60 idle minutes, which a benchmark never provides;
  the scheduled dream stands in for the gap before the question.
* **Wait for the queue, twice in a row.** Work is enqueued asynchronously, so
  one empty poll right after a request can precede the work it should cover.
  The workspace queue is polled, because dreams carry no session.
* **Never scope a read to a session.** A session-scoped read keeps only
  explicit conclusions and drops the derived ones.
* **An empty store is an error,** not a result: a misconfigured server derives
  nothing and still answers every request.
"""

from __future__ import annotations

import os
import re
import time
import uuid
from datetime import timedelta

from .. import config, llm, proxy
from ..data import Question, Session
from .base import Arm, Read

PROXY_PORT = 8100  # must match MEMEVAL_HONCHO_PROXY in infra/honcho/up.sh
USER, ASSISTANT = "user", "assistant"
BATCH = 50
QUEUE_TIMEOUT = 3600
POLL = 3.0


class HonchoArm(Arm):
    name = "honcho"
    variants = ["honcho-chat", "honcho-repr"]

    def __init__(self):
        proxy.start(PROXY_PORT)
        self.base_url = os.environ.get("MEMEVAL_HONCHO_URL", "http://127.0.0.1:8000")
        self.honcho = None

    def settings(self) -> dict:
        return {"server": "honcho v3.3.0 (608aec8)", "sdk": "honcho-ai 2.6.0",
                "models": f"{config.CHAT_MODEL} for every role; {config.EMBED_MODEL}@{config.EMBED_DIMS}",
                "dream": "one scheduled after the history",
                "chat": "peer.chat(question), server-default reasoning level",
                "representation": "peer.representation(search_query=question), server defaults",
                "env": "infra/honcho/honcho.env.template"}

    def reset(self, q: Question) -> None:
        from honcho import Honcho
        from honcho.api_types import PeerConfig

        self.workspace = f"lme-{q.qid}-{uuid.uuid4().hex[:8]}"
        self.honcho = Honcho(api_key="local", base_url=self.base_url, workspace_id=self.workspace,
                             timeout=900)
        self.user = self.honcho.peer(USER)
        self.assistant = self.honcho.peer(ASSISTANT, configuration=PeerConfig(observe_me=False))
        self.messages = 0

    def ingest(self, session: Session) -> None:
        from honcho.api_types import MessageCreateParams

        chat = self.honcho.session(f"s-{re.sub(r'[^A-Za-z0-9_-]', '-', session.id)}",
                                   peers=[self.user, self.assistant])
        messages = [MessageCreateParams(peer_id=USER if t.role == "user" else ASSISTANT,
                                        content=t.content,
                                        # A minute apart, so the order survives.
                                        created_at=session.date + timedelta(minutes=i))
                    for i, t in enumerate(session.turns)]
        for start in range(0, len(messages), BATCH):
            chat.add_messages(messages[start:start + BATCH])
        self.messages += len(messages)

    def finish(self) -> None:
        self._drain()
        self.honcho.schedule_dream(observer=self.user, observed=self.user)
        self._drain()
        if not self._conclusions():
            raise RuntimeError(f"Honcho stored no conclusions for {self.workspace} from "
                               f"{self.messages} messages; check vendor/honcho/logs/deriver.log")

    def _drain(self, confirmations: int = 2) -> None:
        deadline = time.monotonic() + QUEUE_TIMEOUT
        empty = 0
        while time.monotonic() < deadline:
            status = self.honcho.queue_status()
            if status.pending_work_units or status.in_progress_work_units:
                empty = 0
            else:
                empty += 1
                if empty >= confirmations:
                    return
            time.sleep(POLL)
        raise RuntimeError(f"Honcho's queue did not drain within {QUEUE_TIMEOUT}s for {self.workspace}")

    def _conclusions(self) -> list:
        out, page = [], 1
        while True:
            batch = self.user.conclusions.list(page=page, size=100)
            out += list(batch.items)
            if not batch.has_next_page():
                return out
            page += 1

    def reads(self, q: Question) -> dict[str, Read]:
        with llm.tagged(arm="honcho-chat"):
            reply = self.user.chat(q.question)
        text = reply if isinstance(reply, str) else getattr(reply, "content", None) or str(reply or "")
        with llm.tagged(arm="honcho-repr"):
            representation = self.user.representation(search_query=q.question)
        return {"honcho-chat": Read(context=text),
                "honcho-repr": Read(context=representation or "")}

    def dump(self) -> str:
        # Each conclusion's own timestamp is when it was derived (today), not
        # when it was said; the representation carries the message dates.
        rows = sorted(self._conclusions(), key=lambda c: c.created_at)
        return "\n".join(f"- [{c.level}] {c.content}" for c in rows)
