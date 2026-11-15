"""R3: what Letta 0.16.8's self-hosted search would have returned for each search in notebook 04.

Run:  python3 <this file> letta_dump.json      (the dump written by letta_dump_run.py)

The notebook's conversation_search counts the words a message shares with the query and returns
the ten best. Without Turbopuffer, the server does this instead (letta/services/message_manager.py,
list_messages; letta/services/tool_executor/core_tool_executor.py, conversation_search):

- keep the messages whose text contains the whole query as one substring, ignoring case
  (ILIKE '%query%');
- order them newest first and keep RETRIEVAL_QUERY_DEFAULT_PAGE_SIZE = 5;
- drop tool messages after that limit.

The notebook's recall holds only user and assistant messages, so there are no tool messages to drop;
on the server, the echoes of memory edits would compete for the five places as well.
"""
import json
import sys

dump = json.load(open(sys.argv[1]))

for call in dump["calls"]:
    for part in call["reply"]["candidates"][0]["content"].get("parts", []):
        fc = part.get("function_call")
        if not fc or fc["name"] != "conversation_search":
            continue
        query = fc["args"].get("query", "")
        # the conversation this call belongs to: the last user text in the contents sent
        last_user = next(p["text"] for m in reversed(call["contents"]) if m["role"] == "user"
                         for p in m["parts"] if "text" in p)
        # the primary (sleep-time set-up) is offered one tool; the in-line agent three
        agent = "primary" if len(call["tools"][0]["function_declarations"]) == 1 else "agent"
        recall = dump["recall"][agent]
        # recall up to and including the user message being answered
        cut = max(i for i, m in enumerate(recall) if m["role"] == "user" and m["content"] == last_user)
        visible = recall[:cut + 1]
        words = set(query.lower().split())
        server = [m for m in reversed(visible) if query.lower() in m["content"].lower()][:5]
        notebook_hits = sum(1 for m in visible if words & set(m["content"].lower().split()))
        print(f"{agent:8} query={query!r}")
        print(f"         notebook rule: {min(notebook_hits, 10)} of {len(visible)} messages returned;"
              f" server rule: {len(server)} returned"
              + (f" -> {[m['content'][:60] for m in server]}" if server else " (\"No results found.\")"))
