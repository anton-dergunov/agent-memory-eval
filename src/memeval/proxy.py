"""An OpenAI-compatible endpoint backed by Vertex AI, for systems that bring their
own model client (Mem0, Honcho, Letta).

    url = proxy.start(8100)   # http://127.0.0.1:8100/v1

Point the system at `url` with any API key. Every request then goes through
the same cache, cost ledger and budget stop as the experiment's own calls
(`memeval.llm`), so a system that calls its model itself is measured exactly
like one whose calls we make. Without this, the in-process system's bill is
measured and the server-side one's is not, and the unmeasured one always looks
cheaper.

* `/v1/chat/completions` is forwarded to Vertex's OpenAI-compatible endpoint.
  The bearer token is minted per request from Application Default
  Credentials, because the tools behind this take a key once at startup and a
  Google token expires after an hour.
* `/v1/embeddings` is answered with `gemini-embedding-001` through
  `memeval.llm.embed`: Vertex's OpenAI endpoint does not serve embeddings, and
  one embedder for every arm means arms differ by design rather than vectors.
* A bare model name such as `gemini-3.1-flash-lite` becomes Vertex's
  `google/gemini-3.1-flash-lite`.
* Replies cut off at the output cap are not cached, and their finish reason
  goes into the ledger, so truncation can be counted per system.
* **Thought signatures are put back.** Gemini 3 attaches a signature to every
  tool call it makes and rejects the next request if the call comes back
  without it. OpenAI-style clients (Honcho, Letta) do not know the field and
  drop it, so every agentic loop failed on its second step. The proxy
  remembers each signature by tool-call id and restores it.

Bound to localhost: it forwards anything it receives to a billed endpoint.
"""

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import config, llm

_servers: dict[int, ThreadingHTTPServer] = {}
_signatures: dict[str, dict] = {}  # tool-call id -> Gemini's extra_content
_credentials = None
_auth_lock = threading.Lock()


def _token() -> str:
    global _credentials
    with _auth_lock:
        if _credentials is None:
            import google.auth

            config.ensure_credentials()
            _credentials, _ = google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"])
        if not _credentials.valid:
            from google.auth.transport.requests import Request

            _credentials.refresh(Request())
        return _credentials.token


def _vertex_url(suffix: str) -> str:
    host = ("https://aiplatform.googleapis.com" if config.LOCATION == "global"
            else f"https://{config.LOCATION}-aiplatform.googleapis.com")
    return (f"{host}/v1beta1/projects/{config.project()}/locations/{config.LOCATION}"
            f"/endpoints/openapi{suffix}")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # quiet
        pass

    def _send(self, status: int, payload: dict | bytes, content_type="application/json"):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802 - a /v1/models probe
        self._send(200, {"object": "list", "data": [{"id": config.CHAT_MODEL, "object": "model"},
                                                    {"id": config.EMBED_MODEL, "object": "model"}]})

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            return self._send(400, {"error": {"message": "body is not JSON"}})
        suffix = self.path.split("/v1", 1)[-1] if "/v1" in self.path else self.path
        try:
            llm.check_budget()
            if suffix.startswith("/embeddings"):
                return self._embeddings(payload)
            if suffix.startswith("/chat/completions"):
                return self._chat(payload)
            return self._send(404, {"error": {"message": f"not served: {suffix}"}})
        except llm.BudgetExceeded as exc:
            return self._send(402, {"error": {"message": str(exc), "type": "budget"}})
        except Exception as exc:  # noqa: BLE001 - surface it to the client
            return self._send(502, {"error": {"message": f"{type(exc).__name__}: {exc}"}})

    def _embeddings(self, payload: dict):
        texts = payload.get("input", [])
        texts = [texts] if isinstance(texts, str) else list(texts)
        if texts and not isinstance(texts[0], str):
            return self._send(400, {"error": {"message": "token-id input is not supported"}})
        dims = int(payload.get("dimensions") or config.EMBED_DIMS)
        vectors = llm.embed(texts, dims=dims)
        self._send(200, {"object": "list", "model": config.EMBED_MODEL,
                         "data": [{"object": "embedding", "index": i, "embedding": v}
                                  for i, v in enumerate(vectors)],
                         "usage": {"prompt_tokens": 0, "total_tokens": 0}})

    def _chat(self, payload: dict):
        model = str(payload.get("model") or config.CHAT_MODEL)
        if "/" not in model:
            payload["model"] = f"google/{model}"
        stream = bool(payload.pop("stream", False))
        payload.pop("stream_options", None)
        _restore_signatures(payload)
        # Fields that do not change the reply stay out of the cache key.
        key = llm.cache_key("chat", {k: v for k, v in payload.items() if k not in ("user", "metadata")})
        reply = llm.cache_get(key)
        cache_hit = reply is not None
        if not cache_hit:
            reply = self._forward(payload)
        # Vertex sometimes sends null token counts (seen on a reply that was
        # only a tool call); OpenAI's schema says integers, and Letta rejects null.
        usage = reply.setdefault("usage", {}) or {}
        for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
            usage[field] = int(usage.get(field) or 0)
        reply["usage"] = usage
        choices = reply.get("choices") or [{}]
        finish = choices[0].get("finish_reason")
        thinking = int((usage.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0)
        visible = int(usage.get("completion_tokens") or 0)
        llm.record(payload["model"], int(usage.get("prompt_tokens") or 0), visible + thinking,
                   thinking_tokens=thinking, finish=finish, cache_hit=cache_hit)
        message = choices[0].get("message") or {}
        for call in message.get("tool_calls") or []:
            if call.get("id") and call.get("extra_content"):
                _signatures[call["id"]] = call["extra_content"]
        if not cache_hit and finish != "length" and (message.get("content") or message.get("tool_calls")):
            llm.cache_put(key, reply)
        if stream:
            return self._stream(reply)
        self._send(200, reply)

    def _forward(self, payload: dict) -> dict:
        body = json.dumps(payload).encode()

        def call():
            request = urllib.request.Request(
                _vertex_url("/chat/completions"), data=body, method="POST",
                headers={"Authorization": f"Bearer {_token()}", "Content-Type": "application/json",
                         "x-goog-user-project": config.project()})
            try:
                with urllib.request.urlopen(request, timeout=600) as response:
                    return json.loads(response.read())
            except urllib.error.HTTPError as exc:
                raise RuntimeError(f"HTTP {exc.code} from Vertex: {exc.read()[:500]!r}") from exc

        return llm.with_retry(call)

    def _stream(self, reply: dict):
        """Replay a complete reply as one server-sent-event chunk, for clients
        that ask for a stream. Simpler than streaming, and the reply is the same."""
        choice = (reply.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        delta = {"role": "assistant", "content": message.get("content")}
        if message.get("tool_calls"):
            delta["tool_calls"] = [{**c, "index": i} for i, c in enumerate(message["tool_calls"])]
        chunk = {"id": reply.get("id", "x"), "object": "chat.completion.chunk",
                 "created": reply.get("created", 0), "model": reply.get("model"),
                 "choices": [{"index": 0, "delta": delta, "finish_reason": choice.get("finish_reason")}]}
        tail = {**chunk, "choices": [], "usage": reply.get("usage")}
        body = (f"data: {json.dumps(chunk)}\n\ndata: {json.dumps(tail)}\n\ndata: [DONE]\n\n").encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def _restore_signatures(payload: dict) -> None:
    for message in payload.get("messages") or []:
        for call in message.get("tool_calls") or []:
            if not call.get("extra_content") and call.get("id") in _signatures:
                call["extra_content"] = _signatures[call["id"]]


def start(port: int = 0, host: str = "127.0.0.1") -> str:
    """Start the proxy in a background thread (once per port); return its URL."""
    if port in _servers:
        server = _servers[port]
    else:
        server = ThreadingHTTPServer((host, port), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        _servers[server.server_address[1]] = server
        _servers[port] = server
    return f"http://127.0.0.1:{server.server_address[1]}/v1"
