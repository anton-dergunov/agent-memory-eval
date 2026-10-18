"""Models, prices, paths and credentials, in one place.

Every system in the experiment runs on the same chat model and the same
embedding model. Change them here and every arm follows; the values are written
into each run's manifest.
"""

import json
import os
from pathlib import Path

REPO = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists())

# The model in every seat inside every memory system, and the one that answers.
CHAT_MODEL = os.environ.get("MEMEVAL_CHAT_MODEL", "gemini-3.1-flash-lite")
# The judge reads one short answer against the reference answer.
JUDGE_MODEL = os.environ.get("MEMEVAL_JUDGE_MODEL", "gemini-3.1-pro-preview")
# Probes read whole memory stores, so they run on a cheaper strong model.
PROBE_MODEL = os.environ.get("MEMEVAL_PROBE_MODEL", "gemini-3.8-flash")
# gemini-embedding-2 merges a batch of texts into a single vector (it treats the
# batch as one multimodal input), so the text-only model is used.
EMBED_MODEL = os.environ.get("MEMEVAL_EMBED_MODEL", "gemini-embedding-001")
EMBED_DIMS = 1536

LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

# Vertex AI list prices, USD per million tokens, global endpoint, prompts under
# 200K tokens; checked 17 October 2026. Thinking is billed as output.
# (input, cached input, output)
PRICES = {
    "gemini-3.1-flash-lite": (0.25, 0.025, 1.50),
    "gemini-3.5-flash-lite": (0.30, 0.03, 2.50),
    "gemini-3.8-flash": (0.75, 0.075, 3.75),  # introductory price until 31 Dec 2026
    "gemini-3.1-pro-preview": (2.00, 0.20, 12.00),
    "gemini-embedding-001": (0.15, 0.15, 0.0),
}

CACHE_DIR = Path(os.environ.get("MEMEVAL_CACHE_DIR", REPO / ".cache" / "llm"))
LEDGER_DIR = Path(os.environ.get("MEMEVAL_LEDGER_DIR", REPO / ".cache" / "ledger"))
# Every chat request and its reply, cache hits included, for reading what the
# systems actually sent (the cache keeps only replies, keyed by a hash).
CALLS_DIR = Path(os.environ.get("MEMEVAL_CALLS_DIR", REPO / ".cache" / "calls"))
DATA_FILE = REPO / "data" / "longmemeval_s_cleaned.json"
DATA_SHA256 = "d6f21ea9d60a0d56f34a05b609c79c88a451d2ae03597821ea3d5a9678c3a442"
RESULTS_DIR = REPO / "results"

# Every model call stops once the ledger shows this much spent, across all
# processes. A run is resumable, so stopping costs nothing but time.
BUDGET_USD = float(os.environ.get("MEMEVAL_BUDGET_USD", "45"))


def price(model: str, input_tokens: int, output_tokens: int, cached_tokens: int = 0) -> float:
    model = model.removeprefix("google/")
    if model not in PRICES:
        raise KeyError(f"no price for {model}; add it to memeval.config.PRICES")
    p_in, p_cached, p_out = PRICES[model]
    fresh = max(0, input_tokens - cached_tokens)
    return (fresh * p_in + cached_tokens * p_cached + output_tokens * p_out) / 1e6


def project() -> str:
    value = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not value:
        raise RuntimeError("set GOOGLE_CLOUD_PROJECT to the Vertex project to bill")
    return value


def ensure_credentials() -> None:
    """Point Google's libraries at a credential file.

    A cloud environment can hold the Application Default Credentials JSON in
    `GCP_ADC_JSON`; it is written to a file outside the repository, once.
    """
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return
    raw = os.environ.get("GCP_ADC_JSON")
    if not raw:
        return  # fall back to gcloud's own ADC file
    path = Path.home() / ".config" / "memeval" / "adc.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text() != raw:
        path.write_text(raw)
        path.chmod(0o600)
    json.loads(raw)  # fail here, not deep inside a client, if it is not JSON
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(path)
