"""Models and the Gemini calls shared by every notebook in this directory.

Change the model names here and every notebook follows.

`generate` and `embed` are thin wrappers over the google-genai client. They add
what a notebook should not have to show: pacing for the free tier, a retry when
the per-minute quota is hit, and an optional on-disk cache of replies.
"""

import hashlib
import json
import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

CHAT_MODEL = "gemini-3.1-flash-lite"
EMBED_MODEL = "gemini-embedding-001"

# The free tier allows 15 chat requests a minute for this model. Set to None on
# a paid key to stop waiting between calls.
REQUESTS_PER_MINUTE = 15

REPO = next(p for p in (Path(__file__).resolve().parent, *Path(__file__).resolve().parents)
            if (p / "pyproject.toml").exists())

# Set MEMORY_NOTEBOOKS_CACHE=1 to replay earlier replies from .cache/ instead of
# calling the model again. Off by default, so a normal run is a real run.
CACHE_DIR = REPO / ".cache" / "gemini" if os.environ.get("MEMORY_NOTEBOOKS_CACHE") else None

_client = None
_last_call = 0.0

logging.getLogger("google_genai.models").setLevel(logging.ERROR)


def gemini_api_key() -> str:
    """Read GEMINI_API_KEY from the `.env` at the top of the repository."""
    load_dotenv(REPO / ".env")
    return os.environ["GEMINI_API_KEY"]


def gemini() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=gemini_api_key())
    return _client


def _cached(kind, request, call, load, dump):
    if CACHE_DIR is None:
        return call()
    key = hashlib.sha256(json.dumps([kind, request], sort_keys=True, default=str).encode()).hexdigest()
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        return load(path.read_text())
    result = call()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(dump(result))
    return result


def _with_retry(call):
    for _ in range(10):
        try:
            return call()
        except Exception as error:  # the per-minute quota answers with HTTP 429
            if "429" not in str(error) and "503" not in str(error):
                raise
            time.sleep(15)
    return call()


def generate(contents, *, system=None, schema=None, as_json=False, tools=None, temperature=0.0,
             model=None):
    """One chat call. Returns the google-genai response object."""
    config = {"temperature": temperature}
    if as_json:
        config["response_mime_type"] = "application/json"
    if system:
        config["system_instruction"] = system
    if schema is not None:
        config["response_mime_type"] = "application/json"
        config["response_schema"] = schema
    if tools:
        config["tools"] = tools
        config["automatic_function_calling"] = {"disable": True}
    model = model or CHAT_MODEL

    def call():
        global _last_call
        if REQUESTS_PER_MINUTE:
            time.sleep(max(0.0, 60 / REQUESTS_PER_MINUTE + 0.3 - (time.time() - _last_call)))
        _last_call = time.time()
        return _with_retry(
            lambda: gemini().models.generate_content(model=model, contents=contents, config=config)
        )

    schema_key = schema.model_json_schema() if hasattr(schema, "model_json_schema") else schema
    request = [model, contents, system, schema_key, tools, temperature] + (["json"] if as_json else [])
    return _cached(
        "generate", request, call,
        load=types.GenerateContentResponse.model_validate_json,
        dump=lambda response: response.model_dump_json(exclude_none=True),
    )


def embed(texts, *, model=None):
    """Embed a list of texts. Returns one list of floats per text."""
    model = model or EMBED_MODEL
    texts = list(texts)

    def call():
        reply = _with_retry(lambda: gemini().models.embed_content(model=model, contents=texts))
        return [e.values for e in reply.embeddings]

    return _cached("embed", [model, texts], call, load=json.loads, dump=json.dumps)
