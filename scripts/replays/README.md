# Replays and checks behind the blog series

These are working checks made while writing the blog series *How LLM agents remember*. They are kept for reference: each one backs a number, a quote or a claim in a post. They are not needed to run the notebooks or the experiment, and they are not maintained.

Run them from the top of the repository. Several need the experiment's reply cache or call logs (`.cache/`), which are not in the repository; the ones that make model calls say so at the top.

| Files | Part | What they check |
|---|---|---|
| `mem0_*` | 4, Mem0 | replays of the notebook's extraction prompt with parts emptied; how often the model's links to related facts appear in the experiment's cache |
| `graphiti_*` | 5, Zep and Graphiti | a dump of every call of notebook 03; the prompts quoted in the post against graphiti-core; a replay of the contradiction step under the newer prompt; invented ids in the experiment's logs |
| `letta_*` | 6, Letta | a dump of notebook 04 from the cache; replays of the agent's first message and of the change, at the server's temperature; the server's search rule applied offline; the cost of searching, from the ledger; the post's quotes against the server's source |
| `honcho_server_run.py`, `honcho_server_runs/` | 7, Honcho | three runs of a real Honcho 3.3.0 server (`infra/honcho/up.sh`) on the series' example: every request and reply, the stored rows with their links, the peer card and both read outputs |
| `honcho_server_summary.py` | 7 | prints the runs above, step by step, or compared (`--brief`) |
| `honcho_verify_source.py` | 7 | the prompts and tool schemas that `notebooks/honcho_source.py` builds, against the requests the server sent |
| `honcho_dream_window.py` | 7 | where a question's old and new values sat in each benchmark store, against the 20 newest rows a dream agent asked for |
| `honcho_fill_post.py` | 7 | puts the server run's prompts and outputs into the post verbatim, and checks them (`--check`); takes the post's path |

`*_output.txt` files are the outputs that the posts quote.
