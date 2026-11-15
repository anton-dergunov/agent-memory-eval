"""Check every quoted artefact in part 6 against its source, ignoring line breaks and spacing.

Run:  python3 <this file> POST.md letta_dump.json
Sources: Letta 0.16.8 (vendor/letta/src) prompts, persona and sleep-time preface; the tool
descriptions of a request the server sent (.cache/calls/calls-33743.jsonl); the dump of notebook 04;
docs/findings/letta.md; src/memeval/arms/letta.py. Prints each code-block line and each quotation
of five or more words that is not found in any source.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
post = Path(sys.argv[1]).read_text()
dump = json.loads(Path(sys.argv[2]).read_text())
L = REPO / "vendor/letta/src/letta"
request = next(json.loads(l)["request"] for l in (REPO / ".cache/calls/calls-33743.jsonl").open()
               if json.loads(l)["source"] == "proxy")
sources = [
    (L / "prompts/system_prompts/letta_v1.py").read_text(),
    (L / "prompts/system_prompts/sleeptime_v2.py").read_text(),
    (L / "personas/examples/sleeptime_memory_persona.txt").read_text(),
    (L / "personas/examples/memgpt_starter.txt").read_text(),
    (L / "groups/sleeptime_multi_agent_v4.py").read_text().replace('\\n"\n                "', "\n").replace('"\n                "', ""),
    json.dumps(request["tools"], ensure_ascii=False).replace("\\n", "\n").replace('\\"', '"'),
    json.dumps(request["messages"][0]["content"]),
    request["messages"][0]["content"],
    json.dumps(dump, ensure_ascii=False).replace("\\n", "\n").replace('\\"', '"'),
    (REPO / "docs/findings/letta.md").read_text(),
    (REPO / "src/memeval/arms/letta.py").read_text().replace('"\n    "', "").replace("\\n", "\n").replace('\\"', '"'),
    (REPO / "notebooks/04-letta.nb.py").read_text(),
    *(p.read_text() for p in Path(__file__).parent.glob("letta_replay*_output.txt")),
]


def norm(s):
    s = s.replace("’", "'").replace("“", '"').replace("”", '"').replace("**", "")
    return re.sub(r"\s+", " ", s).strip()


corpus = norm("\n".join(sources))
corpus_nospace = corpus.replace(" ", "")

missing = 0
for block in re.findall(r"```(?:text|python)?\n(.*?)```", post, re.S):
    if "def " in block and "return" in block:
        continue                        # pseudocode, not a quotation
    for piece in re.split(r"\[…[^\]]*\]|…", block):
        for line in piece.split("\n"):
            n = norm(line)
            if len(n) < 12 or n.startswith(("label ", "old_string ", "new_string ", "insert_line ", "query ", "roles ", "limit ", "start_date ", "end_date ")):
                continue
            if n not in corpus and n.replace(" ", "") not in corpus_nospace:
                print("BLOCK  ", n[:150]); missing += 1
prose = re.sub(r"```.*?```", "", post, flags=re.S)
for line in prose.split("\n"):
    if line.startswith(("{" + "%", "title:", "excerpt:", "[")) or "<mark" in line:
        continue
    for q in re.findall(r'"([^"]+)"', line):
        for part in re.split(r"\[…\]|…", q):
            n = norm(part)
            if len(n.split()) >= 4 and n not in corpus and n.replace(" ", "") not in corpus_nospace:
                print("QUOTE  ", n[:150]); missing += 1
# transcripts: the user's words without the highlight tags
for line in prose.split("\n"):
    if "<mark" in line:
        n = norm(re.sub(r"<[^>]+>", "", line).lstrip("> ").replace("User: ", ""))
        if n and n not in corpus:
            print("USER   ", n[:150]); missing += 1
# tool calls quoted in blocks: compare the string arguments, joined
for block in re.findall(r"```text\n(memory_(?:insert|replace)\(label=.*?)```", post, re.S):
    for value in re.findall(r'(?:old_string|new_string)="(.*?)"\)?(?:,|$)', block, re.S):
        n = norm(value)
        if n not in corpus:
            print("CALL   ", n[:150]); missing += 1
print(f"{missing} not found")
