"""Graphiti (the open-source engine behind Zep), the real library on Neo4j.

A pipeline writes facts as dated edges between entities. Every edge carries
when it became true (`valid_at`) and, once a later fact contradicts it, when it
stopped (`invalid_at`). That is the property a knowledge-update question tests:
the old value should be an edge that has been closed.

* **Write:** every message becomes one `message` episode ("user: ..." or
  "assistant: ..."), as Graphiti's own chat examples add a conversation, each
  with the session's date as `reference_time`. Graphiti dates every fact from
  it; without it every fact would start on the day of the run and none could
  supersede another. (The first main run cut sessions into 8,000-character
  episodes instead: `MEMEVAL_GRAPHITI_EPISODES=chunk`.)
* **Read:** `graphiti.search(question)` with the library's defaults (hybrid
  BM25 and embedding search over edges, fused by reciprocal rank, 10 results).
  Each fact is shown with its validity window, and closed ones are labelled.
* **Models:** Graphiti's own Gemini client on Vertex, on the experiment's chat
  and embedding models. The client is wrapped so its calls are cached, costed
  and budgeted like every other arm's.
* Neo4j comes from `infra/graphiti/up.sh`; each question gets its own group.
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import uuid
from datetime import timedelta, timezone

from .. import config, llm
from ..data import Question, Session
from .base import Arm, Read

# "message" (one episode per message) or "chunk" (the first main run).
EPISODES = os.environ.get("MEMEVAL_GRAPHITI_EPISODES", "message")
MAX_EPISODE_CHARS = 8000
os.environ.setdefault("GRAPHITI_TELEMETRY_ENABLED", "false")
logging.getLogger("neo4j.notifications").setLevel(logging.ERROR)


def _jsonable(value):
    """A cache key for a request: Graphiti's configs hold Pydantic classes as
    response schemas, which `model_dump` cannot serialise."""
    if isinstance(value, type) and hasattr(value, "model_json_schema"):
        return value.model_json_schema()
    if hasattr(value, "model_fields"):
        return {k: _jsonable(getattr(value, k)) for k in type(value).model_fields
                if getattr(value, k, None) is not None}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    return value if isinstance(value, (str, int, float, bool, type(None))) else repr(value)


async def _retry(call, attempts: int = 6):
    for attempt in range(attempts):
        try:
            return await call()
        except Exception as error:  # noqa: BLE001
            if attempt == attempts - 1 or not any(t in str(error) for t in llm.TRANSIENT):
                raise
            await asyncio.sleep(min(60.0, 2.0 ** attempt) * (1 + random.random()))


class _Models:
    """`client.aio.models` with the experiment's cache, ledger and budget."""

    def __init__(self, inner):
        self.inner = inner

    async def generate_content(self, *, model, contents, config=None, **kwargs):
        from google.genai import types

        key = llm.cache_key("graphiti", model, _jsonable(contents), _jsonable(config))
        hit = llm.cache_get(key)
        if hit is not None:
            response = types.GenerateContentResponse.model_validate_json(hit)
            llm.log_call("graphiti", {"model": model, "contents": _jsonable(contents),
                                      "config": _jsonable(config)}, response.text, cache_hit=True)
            usage = response.usage_metadata
            llm.record(model, usage.prompt_token_count or 0,
                       (usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0),
                       cache_hit=True)
            return response
        llm.check_budget()
        response = await _retry(lambda: self.inner.generate_content(
            model=model, contents=contents, config=config, **kwargs))
        usage = response.usage_metadata
        thinking = usage.thoughts_token_count or 0
        finish = str(response.candidates[0].finish_reason) if response.candidates else None
        llm.record(model, usage.prompt_token_count or 0, (usage.candidates_token_count or 0) + thinking,
                   cached_tokens=usage.cached_content_token_count or 0, thinking_tokens=thinking,
                   finish=finish)
        if response.text and not (finish or "").endswith("MAX_TOKENS"):
            llm.cache_put(key, response.model_dump_json(exclude_none=True))
        llm.log_call("graphiti", {"model": model, "contents": _jsonable(contents), "config": _jsonable(config)},
                     response.text, cache_hit=False)
        return response

    async def embed_content(self, *, model, contents, config=None, **kwargs):
        from google.genai import types

        texts = [contents] if isinstance(contents, str) else list(contents)
        dims = getattr(config, "output_dimensionality", None) or 1536
        vectors = await asyncio.to_thread(llm.embed, texts, model=model, dims=dims)
        return types.EmbedContentResponse(embeddings=[types.ContentEmbedding(values=v) for v in vectors])

    def __getattr__(self, name):
        return getattr(self.inner, name)


class _RecordingClient:
    def __init__(self, inner):
        self._inner = inner
        self.aio = type("Aio", (), {})()
        self.aio.models = _Models(inner.aio.models)

    def __getattr__(self, name):
        return getattr(self._inner, name)


class GraphitiArm(Arm):
    name = "graphiti"

    def __init__(self):
        from graphiti_core import Graphiti
        from graphiti_core.cross_encoder.gemini_reranker_client import GeminiRerankerClient
        from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
        from graphiti_core.llm_client.config import LLMConfig
        from graphiti_core.llm_client.gemini_client import GeminiClient

        client = _RecordingClient(llm.client())
        chat = LLMConfig(model=config.CHAT_MODEL, small_model=config.CHAT_MODEL)
        self.loop = asyncio.new_event_loop()
        self.graphiti = Graphiti(
            os.environ.get("MEMEVAL_NEO4J_URI", "bolt://127.0.0.1:7687"), "neo4j", "memeval-local",
            llm_client=GeminiClient(config=chat, client=client),
            embedder=GeminiEmbedder(config=GeminiEmbedderConfig(
                embedding_model=config.EMBED_MODEL, embedding_dim=config.EMBED_DIMS), client=client),
            # Only the cross-encoder search recipe calls it; the default search does not.
            cross_encoder=GeminiRerankerClient(config=LLMConfig(model=config.CHAT_MODEL), client=client))
        self.loop.run_until_complete(self.graphiti.build_indices_and_constraints())
        self.failures = 0

    def settings(self) -> dict:
        return {"graphiti-core": "0.31.1", "neo4j": "5.26", "llm": config.CHAT_MODEL,
                "embedder": f"{config.EMBED_MODEL}@{config.EMBED_DIMS}",
                "episodes": (f"message episodes of at most {MAX_EPISODE_CHARS} chars per session"
                             if EPISODES == "chunk" else "one message episode per message"),
                "search": "graphiti.search(question) defaults: hybrid RRF over edges, 10 results",
                "entity_types": "none (library default)"}

    def reset(self, q: Question) -> None:
        self.group = f"lme-{q.qid}-{uuid.uuid4().hex[:8]}"
        self.failures = 0
        self.episodes = 0

    def ingest(self, session: Session) -> None:
        from graphiti_core.nodes import EpisodeType

        if EPISODES == "chunk":
            # The first main run: several turns per episode, up to 8,000 characters.
            # Graphiti's extraction prompts are written for one message, and it
            # adds the previous 10 episodes as context, so each call carried
            # 60-80k characters and most updates were never extracted.
            bodies, current = [], ""
            for turn in session.turns:
                line = f"{turn.role}: {turn.content}"
                if current and len(current) + len(line) > MAX_EPISODE_CHARS:
                    bodies.append(current)
                    current = ""
                current = f"{current}\n{line}" if current else line
            if current:
                bodies.append(current)
        else:
            # One episode per message, as Graphiti's own chat examples do.
            bodies = [f"{turn.role}: {turn.content}" for turn in session.turns]
        start = session.date.replace(tzinfo=timezone.utc)
        for i, body in enumerate(bodies):
            when = start + timedelta(minutes=i)
            try:
                self.loop.run_until_complete(self.graphiti.add_episode(
                    name=f"chat {when:%Y-%m-%d %H:%M}", episode_body=body,
                    source_description="a chat between a user and an AI assistant",
                    reference_time=when, source=EpisodeType.message, group_id=self.group))
                self.episodes += 1
            except llm.BudgetExceeded:
                raise
            except Exception as exc:  # noqa: BLE001 - counted, and printed
                self.failures += 1
                print(f"  graphiti: episode failed ({type(exc).__name__}: {str(exc)[:200]})")

    def _edges(self) -> list[dict]:
        records, _, _ = self.loop.run_until_complete(self.graphiti.driver.execute_query(
            "MATCH (a:Entity)-[e:RELATES_TO]->(b:Entity) WHERE e.group_id = $group "
            "RETURN e.fact AS fact, e.valid_at AS valid_at, e.invalid_at AS invalid_at, "
            "e.expired_at AS expired_at ORDER BY e.valid_at", group=self.group))
        return [dict(r) for r in records]

    def read(self, q: Question) -> Read:
        edges = self.loop.run_until_complete(self.graphiti.search(q.question, group_ids=[self.group]))
        lines = [render(e.fact, e.valid_at, e.invalid_at, e.expired_at) for e in edges]
        stored = self._edges()
        return Read(context="\n".join(lines),
                    extra={"retrieved": len(edges), "edges": len(stored),
                           "invalidated": sum(1 for e in stored if e["invalid_at"] or e["expired_at"]),
                           "episodes": self.episodes, "episode_failures": self.failures})

    def dump(self) -> str:
        return "\n".join(render(e["fact"], e["valid_at"], e["invalid_at"], e["expired_at"])
                         for e in self._edges())

    def close(self) -> None:
        try:
            self.loop.run_until_complete(self.graphiti.close())
        except Exception:  # noqa: BLE001
            pass


def _day(value) -> str:
    return f"{value:%Y-%m-%d}" if hasattr(value, "year") else str(value)[:10]


def render(fact, valid_at, invalid_at, expired_at) -> str:
    if valid_at and invalid_at:
        window = f"valid from {_day(valid_at)} until {_day(invalid_at)}"
    elif valid_at:
        window = f"valid since {_day(valid_at)}"
    elif invalid_at:
        window = f"valid until {_day(invalid_at)}"
    else:
        window = "date unknown"
    closed = " [superseded]" if (invalid_at or expired_at) else ""
    return f"- {fact} ({window}){closed}"
