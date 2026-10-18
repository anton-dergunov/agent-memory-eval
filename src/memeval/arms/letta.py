"""Letta (MemGPT), the real server: the agent edits its own memory with tools.

Letta 0.16.8, the last release of Letta's Python server (its source is now
archived; the `letta` name on PyPI has since moved to a different product).
It runs from `infra/letta/up.sh` with its model calls going through
`memeval.proxy` on port 8101.

* **One agent per question**, `letta_v1_agent` (the server's default), with
  Letta's two default memory blocks: `persona` (Letta's `memgpt_starter`
  text) and an empty `human` block.
* **Each session is a new conversation with that agent.** The session's
  messages, user and assistant, are sent in one request; the agent then takes
  its turn, which is when it decides what to write into its blocks. A new
  conversation starts with the blocks and nothing else in context, so what
  reaches the next session is what the agent wrote, plus whatever it finds
  with `conversation_search` over past messages. This is the setting MemGPT
  was designed for.
* **The question is asked in a new conversation** and the agent's reply is the
  answer. Answering is part of this system, so it does not use the shared
  answer prompt. The context recorded for the probes is the memory blocks
  plus every tool result the agent saw while answering.
* **Dates.** The server stamps every message with the time it arrives and has
  no way to import one with its own date, so each message is prefixed with
  its session's date and time.
* Letta's default context window (128,000 tokens) and every other setting are
  left as they are.
"""

from __future__ import annotations

import os

from .. import config, proxy
from ..data import Question, Session
from .base import Arm, Read

PROXY_PORT = 8101
# letta/personas/examples/memgpt_starter.txt in Letta 0.16.8 (Apache-2.0).
PERSONA = ("The following is a blank slate starter persona, I need to expand this to develop "
           "my own personality.\n\nMy name is Letta.\nI am kind, thoughtful, and inquisitive.")
CONTEXT_WINDOW = 128_000  # letta.constants.DEFAULT_CONTEXT_WINDOW


def _stamp(when, text: str) -> str:
    return f"[{when:%Y-%m-%d %H:%M}] {text}"


class LettaArm(Arm):
    name = "letta"

    def __init__(self):
        from letta_client import Letta

        self.url = proxy.start(PROXY_PORT)
        self.client = Letta(base_url=os.environ.get("MEMEVAL_LETTA_URL", "http://127.0.0.1:8283"),
                            timeout=900)
        self.agent = None

    def settings(self) -> dict:
        return {"server": "letta 0.16.8", "client": "letta-client 1.11.0",
                "agent_type": "letta_v1_agent (default)", "context_window": CONTEXT_WINDOW,
                "blocks": "persona=memgpt_starter, human=empty", "llm": config.CHAT_MODEL,
                "embedder": f"{config.EMBED_MODEL}@{config.EMBED_DIMS}",
                "sessions": ("one conversation per session, the whole session in one request"
                             if os.environ.get("MEMEVAL_LETTA_INGEST", "turns") == "batch" else
                             "one conversation per session, one agent step per user message"),
                "dates": "prefixed to each message"}

    def reset(self, q: Question) -> None:
        self.close()
        self.agent = self.client.agents.create(
            name=f"lme-{q.qid}",
            memory_blocks=[{"label": "persona", "value": PERSONA},
                           {"label": "human", "value": ""}],
            llm_config={"model": config.CHAT_MODEL, "model_endpoint_type": "openai",
                        "model_endpoint": self.url, "context_window": CONTEXT_WINDOW},
            embedding_config={"embedding_model": config.EMBED_MODEL, "embedding_endpoint_type": "openai",
                              "embedding_endpoint": self.url, "embedding_dim": config.EMBED_DIMS,
                              "embedding_chunk_size": 300})
        self.steps = 0
        self.events = []

    def _send(self, messages: list[dict]) -> list:
        """Send messages into a new conversation and wait for the agent's whole
        turn. The server answers conversation messages as a stream; it is read
        to the end, which is also what lets the turn finish."""
        conversation = self.client.conversations.create(agent_id=self.agent.id)
        stream = self.client.conversations.messages.create(conversation.id, messages=messages)
        out = [event for event in stream if getattr(event, "message_type", None)]
        self.steps += 1
        return out

    def ingest(self, session: Session) -> None:
        if os.environ.get("MEMEVAL_LETTA_INGEST", "turns") == "batch":
            # The first main run: the whole session in one request. Sessions end
            # with an assistant message, so the agent had nothing to answer and
            # mostly took no step at all, and so never edited its memory.
            self._send([{"role": t.role, "content": _stamp(session.date, t.content)}
                        for t in session.turns])
            return
        # One agent step per user message, in one conversation per session: the
        # agent is the assistant, writes its own replies, and decides at every
        # step what to keep. The recorded assistant replies are not sent.
        conversation = self.client.conversations.create(agent_id=self.agent.id)
        for t in session.turns:
            if t.role != "user":
                continue
            stream = self.client.conversations.messages.create(
                conversation.id, messages=[{"role": "user", "content": _stamp(session.date, t.content)}])
            self.events.extend(e for e in stream if getattr(e, "message_type", None))
            self.steps += 1

    def _blocks(self) -> str:
        blocks = self.client.agents.blocks.list(self.agent.id)
        return "\n\n".join(f"<{b.label}>\n{b.value}\n</{b.label}>" for b in blocks)

    def read(self, q: Question) -> Read:
        blocks = self._blocks()
        events = self._send([{"role": "user", "content": _stamp(q.date, q.question)}])
        replies, tool_results, tool_calls = [], [], []
        for m in events:
            kind = getattr(m, "message_type", "")
            if kind == "assistant_message":
                content = m.content if isinstance(m.content, str) else " ".join(
                    getattr(c, "text", "") for c in m.content)
                replies.append(content)
            elif kind == "tool_call_message":
                tool_calls.append(f"{m.tool_call.name}({m.tool_call.arguments})")
            elif kind == "tool_return_message":
                tool_results.append(str(m.tool_return)[:4000])
        context = blocks + ("\n\nTool results while answering:\n" + "\n".join(tool_results)
                            if tool_results else "")
        answer = "\n".join(replies).strip() or "(no reply)"
        return Read(context=context, answer=answer,
                    extra={"tool_calls": tool_calls, "blocks_chars": len(blocks),
                           "write_steps": self.steps - 1,
                           "write_tool_calls": [e.tool_call.name for e in self.events
                                                if getattr(e, "message_type", "") == "tool_call_message"]})

    def dump(self) -> str:
        return self._blocks()

    def close(self) -> None:
        if self.agent is not None:
            try:
                self.client.agents.delete(self.agent.id)
            except Exception:  # noqa: BLE001
                pass
            self.agent = None
