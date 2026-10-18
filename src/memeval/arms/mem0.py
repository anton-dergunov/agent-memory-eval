"""Mem0, the real open-source library: an extraction pipeline into a vector store.

Each session is one `add()` call. Mem0 extracts short facts from it in one
model call (this release only adds, it never updates or deletes), embeds them
and stores them in a local Qdrant. The read path is `search()` with the
question, at the library's defaults.

What this wrapper changes, and why:

* **The session date.** The library's extraction prompt has an "Observation
  Date" against which "last week" is resolved, but the open-source `add()`
  fills it with today's date and rejects `timestamp=` as a platform-only
  feature. The prompt builder itself accepts a date, so it is given the
  session's.
* **Its model calls go through `memeval.proxy`**, which counts and caches them
  like every other arm's. The embedder is the same `gemini-embedding-001`.
* **A fresh store per question**, because `add()` only appends.
* **Silent losses are counted.** Mem0 logs and drops a reply it cannot parse
  as JSON, and reports success. Those are counted per question.
"""

from __future__ import annotations

import functools
import logging
import os
import shutil
import tempfile

from .. import config, proxy
from ..data import Question, Session
from .base import Arm, Read

os.environ.setdefault("MEM0_TELEMETRY", "False")
PROXY_PORT = 8102
# The library extracts from each add() call in one model call; very long
# batches have been seen to store nothing at all, so a session is split.
MAX_MESSAGES = 20


class _ParseFailures(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.ERROR)
        self.count = 0

    def emit(self, record):
        if "parsing extraction response" in record.getMessage():
            self.count += 1


class Mem0Arm(Arm):
    name = "mem0"

    def __init__(self):
        self.url = proxy.start(PROXY_PORT)
        self.home = None
        self.memory = None
        self.failures = _ParseFailures()
        logging.getLogger("mem0.memory.main").addHandler(self.failures)

    def settings(self) -> dict:
        import mem0
        from mem0.configs.llms.base import BaseLlmConfig

        defaults = BaseLlmConfig()
        return {"mem0ai": mem0.__version__ if hasattr(mem0, "__version__") else "2.2.1",
                "llm": config.CHAT_MODEL, "embedder": f"{config.EMBED_MODEL}@{config.EMBED_DIMS}",
                "llm_max_tokens": defaults.max_tokens, "llm_temperature": defaults.temperature,
                "search": "library defaults (top_k=20, threshold=0.1)",
                "add": "one call per session (split above 20 messages), session date injected"}

    def _config(self) -> dict:
        return {
            "llm": {"provider": "openai",
                    "config": {"model": config.CHAT_MODEL, "api_key": "proxy",
                               "openai_base_url": self.url}},
            "embedder": {"provider": "openai",
                         "config": {"model": config.EMBED_MODEL, "api_key": "proxy",
                                    "openai_base_url": self.url,
                                    "embedding_dims": config.EMBED_DIMS}},
            "vector_store": {"provider": "qdrant",
                             "config": {"path": os.path.join(self.home, "qdrant"),
                                        "collection_name": "memories",
                                        "embedding_model_dims": config.EMBED_DIMS}},
            "history_db_path": os.path.join(self.home, "history.db"),
        }

    def reset(self, q: Question) -> None:
        from mem0 import Memory

        self.close()
        self.home = tempfile.mkdtemp(prefix=f"mem0-{q.qid}-")
        self.memory = Memory.from_config(self._config())
        self.user = "user"
        self.failures.count = 0
        self.stored = 0

    def ingest(self, session: Session) -> None:
        import mem0.memory.main as main

        day = f"{session.date:%Y-%m-%d}"
        original = main.generate_additive_extraction_prompt
        main.generate_additive_extraction_prompt = functools.partial(
            original, timestamp=day, current_date=day)
        try:
            messages = [{"role": t.role, "content": t.content} for t in session.turns]
            for start in range(0, len(messages), MAX_MESSAGES):
                outcome = self.memory.add(messages[start:start + MAX_MESSAGES], user_id=self.user,
                                          metadata={"session_date": day})
                self.stored += len(outcome.get("results", []) if isinstance(outcome, dict) else outcome)
        finally:
            main.generate_additive_extraction_prompt = original

    def _all(self) -> list[dict]:
        found = self.memory.get_all(filters={"user_id": self.user}, top_k=10_000)
        return found.get("results", found) if isinstance(found, dict) else found

    def read(self, q: Question) -> Read:
        found = self.memory.search(query=q.question, filters={"user_id": self.user})
        results = found.get("results", found) if isinstance(found, dict) else found
        lines = [f"- {r['memory']}" + (f" (from a chat on {r['metadata']['session_date']})"
                                       if (r.get("metadata") or {}).get("session_date") else "")
                 for r in results]
        return Read(context="\n".join(lines),
                    extra={"retrieved": len(results), "stored": len(self._all()),
                           "parse_failures": self.failures.count})

    def dump(self) -> str:
        rows = self._all()
        return "\n".join(f"- {r['memory']} (session {(r.get('metadata') or {}).get('session_date')})"
                         for r in rows)

    def close(self) -> None:
        if self.memory is not None:
            try:
                self.memory.vector_store.client.close()
            except Exception:  # noqa: BLE001
                pass
            self.memory = None
        if self.home:
            shutil.rmtree(self.home, ignore_errors=True)
            self.home = None
