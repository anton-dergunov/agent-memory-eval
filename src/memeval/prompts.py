"""The prompts that are the same for every arm: answering, judging, probing.

The answer and judge prompts are LongMemEval's own, from
https://github.com/xiaowu0162/LongMemEval at commit 9e0b455 (MIT licence):
`src/generation/run_generation.py` (the chain-of-thought variants) and
`src/evaluation/evaluate_qa.py` (the knowledge-update judge).
"""

# For the arms that hand the model raw chat history (full context, retrieval).
ANSWER_FROM_HISTORY = (
    "I will give you several history chats between you and a user. Please answer the question "
    "based on the relevant chat history. Answer the question step by step: first extract all the "
    "relevant information, and then reason over the information to get the answer.\n\n\n"
    "History Chats:\n\n{context}\n\nCurrent Date: {date}\nQuestion: {question}\n"
    "Answer (step by step):")

# For the arms that hand the model what a memory system returned. LongMemEval's
# "facts extracted from history chats" variant.
ANSWER_FROM_MEMORY = (
    "I will give you several facts extracted from history chats between you and a user. Please "
    "answer the question based on the relevant facts. Answer the question step by step: first "
    "extract all the relevant information, and then reason over the information to get the "
    "answer.\n\n\nHistory Chats:\n\n{context}\n\nCurrent Date: {date}\nQuestion: {question}\n"
    "Answer (step by step):")

JUDGE_KNOWLEDGE_UPDATE = (
    "I will give you a question, a correct answer, and a response from a model. Please answer yes "
    "if the response contains the correct answer. Otherwise, answer no. If the response contains "
    "some previous information along with an updated answer, the response should be considered as "
    "correct as long as the updated answer is the required answer.\n\nQuestion: {question}\n\n"
    "Correct Answer: {answer}\n\nModel Response: {response}\n\nIs the model response correct? "
    "Answer yes or no only.")

# ---------------------------------------------------------------- probes
# Ours. They turn one accuracy number into the failure breakdown: was the update
# written, did it reach the answering model, and did the model use it.

OLD_VALUE = """\
A user told an assistant something in an earlier chat and later revised it. \
Below are the two chats, a question asked after both, and the correct answer, \
which reflects the revision.

Earlier chat:
{first}

Later chat:
{second}

Question: {question}
Correct (updated) answer: {answer}

What would the answer have been before the revision, according to the earlier \
chat? Reply with JSON: {{"old_value": "<short answer, or null if the earlier \
chat does not give one>", "new_value": "<the updated answer, short>"}}"""

STORED = """\
Below is everything a memory system holds about a user, followed by two \
values for one fact about them: the old value, later replaced, and the new, \
current value.

Fact asked about: {question}
Old value: {old}
New value: {new}

Memory contents:
{memory}

Answer with JSON:
{{"new_present": <true if the memory states the new value anywhere>,
  "old_present": <true if the memory states the old value anywhere>,
  "old_as_current": <true if the memory presents the old value as still \
current, i.e. it is not marked as replaced, superseded, ended or past and the \
new value is not stated as replacing it>}}"""

DELIVERED = """\
Below is the text a memory system put into an assistant's prompt to answer a \
question, followed by two values for the fact asked about: the old value, \
later replaced, and the new, current value.

Question: {question}
Old value: {old}
New value: {new}

Text given to the assistant:
{context}

Answer with JSON:
{{"new_present": <true if the text states the new value>,
  "old_present": <true if the text states the old value>}}"""

STALE = """\
A user's fact changed from an old value to a new value. Did this response \
give the old value as its answer?

Question: {question}
Old value: {old}
New value: {new}
Response: {response}

Answer with JSON: {{"gave_old": <true if the response's final answer is the \
old value>, "gave_new": <true if the response's final answer is the new \
value>}}"""
