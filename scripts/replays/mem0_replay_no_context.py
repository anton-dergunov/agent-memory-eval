import sys, json, time, re
sys.argv = ["x", "none"]
src = open(__file__.replace("mem0_replay_no_context.py", "mem0_replay.py")).read().split("which = sys.argv[1]")[0]
exec(src)
m = make("store-c")
blank = re.sub(r"## Last k Messages\n.*?\n\n\n## Recently", "## Last k Messages\n\n\n## Recently", user2, flags=re.S)
blank = re.sub(r"## Existing Memories\n\[.*?\]\n", "## Existing Memories\n[]\n", blank, flags=re.S)
print(blank[:260]); print("...")
for i in range(3):
    r = m.llm.generate_response(messages=[{"role": "system", "content": ADDITIVE_EXTRACTION_PROMPT}, {"role": "user", "content": blank}], response_format={"type": "json_object"})
    print(f"--- reply {i+1} ---"); [print("  ", x["text"], x.get("linked_memory_ids", "")) for x in json.loads(r)["memory"]]
    time.sleep(5)
