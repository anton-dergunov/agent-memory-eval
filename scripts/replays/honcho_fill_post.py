"""Put the verbatim artefacts of server run 1 into part 7, between BEGIN/END markers.

Every block comes from `honcho_server_runs/run1.json`: the requests the server sent (prompts),
the rows it stored, its replies. Cuts are whole lines, marked "[…]". Rerunning the script replaces
the blocks, so it is safe to run after editing the prose. `--check` only verifies that each block
in the post equals what the script would write, and that every kept line of a cut prompt appears,
in order, in the full prompt.

    python3 scripts/replays/honcho_fill_post.py PATH/TO/2199-01-01-agent-memory-7-honcho.md [--check]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = json.loads((HERE / "honcho_server_runs/run1.json").read_text())
CUT = "[…]"


def request(step, marker):
    return next(c["request"] for c in RUN["calls"]
                if c["phase"] == step and marker in c["request"]["messages"][0]["content"][:120])


# Liquid's raw tags, built so that this file (which Jekyll also reads) never contains them.
RAW_OPEN, RAW_CLOSE = "{" + "% raw %" + "}", "{" + "% endraw %" + "}"


def fence(text, lang="text"):
    ticks = "````" if "```" in text else "```"     # a prompt may contain a fenced block itself
    block = f"{ticks}{lang}\n{text.rstrip()}\n{ticks}"
    if "{" + "{" in block or "{" + "%" in block:      # Liquid would try to render these
        block = f"{RAW_OPEN}\n\n{block}\n\n{RAW_CLOSE}"
    return block


def deduction_system():
    full = request("dream1", "deductive reasoning")["messages"][0]["content"]
    out, skipping = [], False
    for line in full.splitlines():
        if line.startswith("### Allowed entry kinds"):
            out.append(line)
            continue
        if re.match(r"\s+- `(IDENTITY|ATTRIBUTE|RELATIONSHIP|INSTRUCTION): ", line):
            if out[-1] != CUT:
                out.append(CUT)
            continue
        if line.startswith("### Migrating an existing peer card"):
            skipping = True
            out.append(CUT)
            continue
        if skipping and line.startswith("Call `update_peer_card` with the complete"):
            skipping = False
        if not skipping:
            out.append(line)
    return "\n".join(out), full


def dialectic_system():
    full = request("chat", "dialectic")["messages"][0]["content"]
    out, skipping = [], False
    for line in full.splitlines():
        if line.startswith("4. **For ENUMERATION/AGGREGATION questions**"):
            skipping = True
            out.append(CUT)
            continue
        if skipping and line.startswith("6. **Ground your answer using reasoning chains**"):
            skipping = False
        if not skipping:
            out.append(line)
    return "\n".join(out).strip(), full


def rows(step):
    reply = next(c for c in RUN["calls"] if c["phase"] == step)["reply"]
    items = json.loads(reply["choices"][0]["message"]["content"])["explicit"]
    when = {"s1": "2026-03-14 12:02:00", "s2": "2026-07-20 12:06:00"}[step]
    return "\n".join(f"[{when}] {i['content']}" for i in items)


def stored_row():
    doc = next(d for d in RUN["documents"] if d["content"].startswith("Anton transitioned"))
    links = [link["source_id"] for link in RUN["links"] if link["derived_id"] == doc["id"]]
    shown = {k: doc[k] for k in ("id", "level", "content", "session_name", "observer", "observed",
                                 "times_derived", "deleted_at")}
    shown["internal_metadata"] = doc["internal_metadata"]
    shown["source_ids (document_sources)"] = links
    return json.dumps(shown, indent=2, ensure_ascii=False)


def recent_result():
    last = [c["request"] for c in RUN["calls"] if c["phase"] == "dream2"
            and "deductive reasoning" in c["request"]["messages"][0]["content"][:120]][-1]
    tool = next(m for m in last["messages"] if m["role"] == "tool")
    return tool["content"]


def blocks():
    deduction, deduction_full = deduction_system()
    dialectic, dialectic_full = dialectic_system()
    return {
        "ROW_JSON": (fence(stored_row(), "json"), None),
        "DERIVER_PROMPT": (fence(request("s1", "Analyze")["messages"][0]["content"]), None),
        "DEDUCTION_SYSTEM": (fence(deduction), deduction_full),
        "DEDUCTION_USER": (fence(request("dream2", "deductive reasoning")["messages"][1]["content"]), None),
        "INDUCTION_SYSTEM": (fence(request("dream1", "inductive reasoning")["messages"][0]["content"]), None),
        "RECENT_RESULT": (fence(recent_result()), None),
        "DIALECTIC_SYSTEM": (fence(dialectic), dialectic_full),
        "S1_ROWS": (fence(rows("s1")), None),
        "S2_ROWS": (fence(rows("s2")), None),
        "REPRESENTATION": (fence(RUN["representation"].strip(), "markdown"), None),
        "CHAT": ("\n".join("> " + line.rstrip() if line.strip() else ">"
                            for line in RUN["chat"].strip().splitlines()), None),
    }


def kept_in_order(cut, full):
    """Every non-cut line of `cut` appears in `full`, in the same order."""
    lines, position = full.splitlines(), 0
    for line in cut.splitlines():
        if line.startswith("```") or line in (RAW_OPEN, RAW_CLOSE):
            continue
        if line == CUT:
            continue
        while position < len(lines) and lines[position] != line:
            position += 1
        if position == len(lines):
            return False, line
        position += 1
    return True, None


def main():
    posts = [Path(a) for a in sys.argv[1:] if not a.startswith("--")]
    if len(posts) != 1:
        raise SystemExit(__doc__)
    POST = posts[0]
    text = POST.read_text()
    check = "--check" in sys.argv
    ok = True
    for name, (block, full) in blocks().items():
        wrapped = f"<!-- BEGIN {name} -->\n{block}\n<!-- END {name} -->"
        pattern = re.compile(rf"<!-- BEGIN {name} -->.*?<!-- END {name} -->|<!-- {name} -->", re.S)
        found = pattern.search(text)
        if not found:
            print(f"MISSING {name}")
            ok = False
            continue
        if full is not None:
            good, line = kept_in_order(block, full)
            print(f"{'OK  ' if good else 'BAD '} {name}: kept lines in order" + ("" if good else f": {line!r}"))
            ok &= good
        if check:
            same = found.group(0) == wrapped
            print(f"{'OK  ' if same else 'DIFF'} {name}")
            ok &= same
        else:
            text = text[:found.start()] + wrapped + text[found.end():]
    if not check:
        POST.write_text(text)
        print("filled", POST.name)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
