"""Fill tiktoken's cache without reaching openaipublic.blob.core.windows.net.

Honcho counts tokens with tiktoken, which downloads its encodings from an Azure
blob on first use. Where that host is blocked, this rebuilds the two encodings
Honcho uses from the Hugging Face copies of the same tokenizers and writes them
where tiktoken looks first. tiktoken checks every file against a SHA-256 it
ships with, and so does this script, so the result is byte-identical to the
official file or nothing is written.

    python infra/tiktoken_cache.py <cache dir>    # then export TIKTOKEN_CACHE_DIR=<cache dir>
"""

import base64
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ENCODINGS = {
    # name: (Hugging Face repo with the same vocabulary, expected sha256 from tiktoken_ext)
    "o200k_base": ("Xenova/gpt-4o",
                   "446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d"),
    "cl100k_base": ("Xenova/gpt-4",
                    "223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7"),
}
OFFICIAL = "https://openaipublic.blob.core.windows.net/encodings/{}.tiktoken"


def bytes_to_unicode() -> dict[int, str]:
    """GPT-2's byte-to-character table, which byte-level BPE vocabularies use."""
    bs = list(range(ord("!"), ord("~") + 1)) + list(range(ord("¡"), ord("¬") + 1)) + \
        list(range(ord("®"), ord("ÿ") + 1))
    cs = bs[:]
    n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return dict(zip(bs, (chr(c) for c in cs)))


def rebuild(repo: str) -> bytes:
    with urllib.request.urlopen(f"https://huggingface.co/{repo}/resolve/main/tokenizer.json") as r:
        tokenizer = json.load(r)
    # Special tokens sit in the same vocabulary here; tiktoken keeps them apart.
    special = {t["content"] for t in tokenizer.get("added_tokens", [])}
    special |= {k for k in tokenizer["model"]["vocab"] if k.startswith("<|") and k.endswith("|>")}
    vocab = {k: v for k, v in tokenizer["model"]["vocab"].items() if k not in special}
    decode = {c: b for b, c in bytes_to_unicode().items()}
    lines = []
    for token, rank in sorted(vocab.items(), key=lambda kv: kv[1]):
        raw = bytes(decode[ch] for ch in token)
        lines.append(base64.b64encode(raw) + b" " + str(rank).encode())
    return b"\n".join(lines) + b"\n"


def main() -> int:
    cache = Path(sys.argv[1] if len(sys.argv) > 1 else ".cache/tiktoken")
    cache.mkdir(parents=True, exist_ok=True)
    for name, (repo, expected) in ENCODINGS.items():
        target = cache / hashlib.sha1(OFFICIAL.format(name).encode()).hexdigest()
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == expected:
            print(f"{name}: already cached")
            continue
        blob = rebuild(repo)
        digest = hashlib.sha256(blob).hexdigest()
        if digest != expected:
            print(f"{name}: rebuilt file has sha256 {digest}, expected {expected}; not written")
            return 1
        target.write_bytes(blob)
        print(f"{name}: written to {target} (sha256 verified)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
