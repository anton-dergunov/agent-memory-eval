"""Model calls on Vertex AI, with a disk cache, a cost ledger and a budget stop.

Three things every call in the experiment gets, whichever system makes it:

* **A cache keyed on the full request.** A re-run after a bug fix costs nothing
  for the calls that did not change. Truncated or empty replies are never
  cached, so a retry with a larger budget is a real retry.
* **A ledger line** with the tokens, the price and the tags of whoever made the
  call (`arm`, `qid`, `phase`), so cost can be split by system, by question and
  by write versus read.
* **A budget stop.** The ledger is summed across every process before each call
  and nothing is sent once the configured budget is spent.

The memory systems that call their models themselves reach Vertex through
`memeval.proxy`, which uses the same cache, ledger and budget.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import random
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from . import config

# Who is calling: set by the runner around each phase of each question. A plain
# global rather than a context variable, so the proxy's request threads see it
# too; one runner process works on one question of one arm at a time.
TAGS: dict = {}
_lock = threading.Lock()
_spent_cache = {"at": 0.0, "usd": 0.0}


class BudgetExceeded(RuntimeError):
    pass


class EmptyReply(RuntimeError):
    pass


@contextlib.contextmanager
def tagged(**tags):
    saved = dict(TAGS)
    TAGS.update(tags)
    try:
        yield
    finally:
        TAGS.clear()
        TAGS.update(saved)


# ------------------------------------------------------------------ ledger

def _ledger_file() -> Path:
    config.LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    return config.LEDGER_DIR / f"calls-{os.getpid()}.jsonl"


def record(model: str, input_tokens: int, output_tokens: int, *, cached_tokens: int = 0,
           thinking_tokens: int = 0, finish: str | None = None, cache_hit: bool = False,
           kind: str = "chat", tags: dict | None = None) -> float:
    """Append one call to the ledger. Cache hits are recorded at zero cost."""
    usd = 0.0 if cache_hit else config.price(model, input_tokens, output_tokens, cached_tokens)
    line = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "kind": kind,
            "model": model.removeprefix("google/"), "input_tokens": input_tokens,
            "cached_tokens": cached_tokens, "output_tokens": output_tokens,
            "thinking_tokens": thinking_tokens, "finish": finish, "cache_hit": cache_hit,
            "usd": round(usd, 8), **(tags if tags is not None else TAGS)}
    with _lock, open(_ledger_file(), "a") as fh:
        fh.write(json.dumps(line) + "\n")
    _spent_cache["usd"] += usd
    return usd


def spent() -> float:
    """Total spend across every process, re-read at most every 20 seconds."""
    now = time.time()
    if now - _spent_cache["at"] > 20:
        total = 0.0
        if config.LEDGER_DIR.exists():
            for path in config.LEDGER_DIR.glob("calls-*.jsonl"):
                for raw in path.read_text().splitlines():
                    with contextlib.suppress(ValueError):
                        total += json.loads(raw).get("usd", 0.0)
        _spent_cache.update(at=now, usd=total)
    return _spent_cache["usd"]


def check_budget() -> None:
    if spent() >= config.BUDGET_USD:
        raise BudgetExceeded(f"spent ${spent():.2f} of the ${config.BUDGET_USD:.2f} budget; "
                             f"raise MEMEVAL_BUDGET_USD to continue")


# ------------------------------------------------------------------- cache

def cache_key(*parts) -> str:
    return hashlib.sha256(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()


def cache_get(key: str):
    path = config.CACHE_DIR / key[:2] / f"{key}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except ValueError:
        return None  # a half-written file is a miss


def cache_put(key: str, value) -> None:
    path = config.CACHE_DIR / key[:2] / f"{key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(value))
    tmp.replace(path)


# ------------------------------------------------------------------ client

_client = None


def client():
    global _client
    if _client is None:
        from google import genai

        config.ensure_credentials()
        _client = genai.Client(vertexai=True, project=config.project(), location=config.LOCATION)
    return _client


TRANSIENT = ("429", "500", "502", "503", "504", "RESOURCE_EXHAUSTED", "UNAVAILABLE",
             "DEADLINE_EXCEEDED", "high demand", "overloaded")


def with_retry(call, attempts: int = 6):
    """Retry rate limits and server errors with jittered backoff."""
    for attempt in range(attempts):
        try:
            return call()
        except Exception as error:  # noqa: BLE001
            if attempt == attempts - 1 or not any(t in str(error) for t in TRANSIENT):
                raise
            time.sleep(min(60.0, 2.0 ** attempt) * (1 + random.random()))


@dataclass
class Reply:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    thinking_tokens: int = 0
    finish: str | None = None
    cache_hit: bool = False


def generate(prompt: str, *, system: str | None = None, model: str | None = None,
             temperature: float = 0.0, max_output_tokens: int | None = None,
             json_output: bool = False) -> Reply:
    """One chat call. Never returns an empty or truncated reply as an answer:
    it retries once with double the output budget, then raises."""
    from google.genai import types

    model = model or config.CHAT_MODEL
    for budget in (max_output_tokens, (max_output_tokens or 8192) * 2):
        key = cache_key("generate", model, system, prompt, temperature, budget, json_output)
        hit = cache_get(key)
        if hit is not None:
            reply = Reply(**hit, cache_hit=True)
            record(model, reply.input_tokens, reply.output_tokens,
                   thinking_tokens=reply.thinking_tokens, finish=reply.finish, cache_hit=True)
            return reply
        check_budget()
        cfg = {"temperature": temperature}
        if system:
            cfg["system_instruction"] = system
        if budget:
            cfg["max_output_tokens"] = budget
        if json_output:
            cfg["response_mime_type"] = "application/json"
        response = with_retry(lambda: client().models.generate_content(
            model=model, contents=prompt, config=types.GenerateContentConfig(**cfg)))
        usage = response.usage_metadata
        thinking = usage.thoughts_token_count or 0
        finish = str(response.candidates[0].finish_reason) if response.candidates else None
        reply = Reply(text=(response.text or "").strip(),
                      input_tokens=usage.prompt_token_count or 0,
                      output_tokens=(usage.candidates_token_count or 0) + thinking,
                      thinking_tokens=thinking, finish=finish)
        record(model, reply.input_tokens, reply.output_tokens,
               cached_tokens=usage.cached_content_token_count or 0,
               thinking_tokens=thinking, finish=finish)
        truncated = finish is not None and finish.endswith("MAX_TOKENS")
        if reply.text and not truncated:
            cache_put(key, {k: v for k, v in reply.__dict__.items() if k != "cache_hit"})
            return reply
    raise EmptyReply(f"{model} returned an empty or truncated reply twice (finish={reply.finish})")


def embed(texts: list[str], *, model: str | None = None, dims: int = config.EMBED_DIMS) -> list[list[float]]:
    """Embed texts, 100 at a time, cached per text."""
    from google.genai import types

    model = model or config.EMBED_MODEL
    out: list[list[float] | None] = [None] * len(texts)
    missing = []
    for i, text in enumerate(texts):
        hit = cache_get(cache_key("embed", model, dims, text))
        if hit is not None:
            out[i] = hit
        else:
            missing.append(i)
    for start in range(0, len(missing), 100):
        chunk = missing[start:start + 100]
        check_budget()
        reply = with_retry(lambda: client().models.embed_content(
            model=model, contents=[texts[i] or " " for i in chunk],
            config=types.EmbedContentConfig(output_dimensionality=dims)))
        if len(reply.embeddings) != len(chunk):
            raise RuntimeError(f"{model} returned {len(reply.embeddings)} vectors for {len(chunk)} texts")
        tokens = sum(len(texts[i]) for i in chunk) // 4  # Vertex reports no token count here
        record(model, tokens, 0, kind="embed")
        for i, vector in zip(chunk, reply.embeddings):
            out[i] = list(vector.values)
            cache_put(cache_key("embed", model, dims, texts[i]), out[i])
    return out  # type: ignore[return-value]
