## Results: pilot

| Arm | n | Accuracy | 95% interval |
|---|--:|--:|---|
| full-context | 5 | 80% | 38%–96% |
| retrieval | 5 | 100% | 57%–100% |
| textual | 5 | 80% | 38%–96% |
| mem0 | 5 | 100% | 57%–100% |
| honcho-chat | 5 | 60% | 23%–88% |
| honcho-repr | 5 | 60% | 23%–88% |
| graphiti | 5 | 40% | 12%–77% |
| letta | 5 | 80% | 38%–96% |

### Where answers were lost

| Arm | correct | update never stored | stored, not delivered | delivered, answered old value | delivered, other error | wrong, unclassified | old value stored as current | old value delivered |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| full-context | 4 | 0 | 0 | 1 | 0 | 0 | n/a | 4 |
| retrieval | 5 | 0 | 0 | 0 | 0 | 0 | n/a | 4 |
| textual | 4 | 0 | 0 | 0 | 1 | 0 | 0 | 2 |
| mem0 | 5 | 0 | 0 | 0 | 0 | 0 | 1 | 4 |
| honcho-chat | 3 | 1 | 0 | 1 | 0 | 0 | 2 | 4 |
| honcho-repr | 3 | 1 | 1 | 0 | 0 | 0 | 2 | 4 |
| graphiti | 2 | 3 | 0 | 0 | 0 | 0 | 2 | 3 |
| letta | 4 | 0 | 0 | 0 | 0 | 1 | 0 | 1 |

### Cost per question (USD, mean)

| Arm | write | read | answer | total system | model calls (write) | input tokens (write) |
|---|--:|--:|--:|--:|--:|--:|
| full-context | 0.0000 | 0.0000 | 0.0060 | 0.0060 | 0.0 | 0 |
| retrieval | 0.0000 | 0.0000 | 0.0018 | 0.0018 | 0.0 | 0 |
| textual | 0.0195 | 0.0000 | 0.0007 | 0.0202 | 10.0 | 31,224 |
| mem0 | 0.0378 | 0.0000 | 0.0008 | 0.0385 | 12.0 | 136,101 |
| honcho-chat | 0.0245 | 0.0017 | 0.0004 | 0.0266 | 33.6 | 62,549 |
| honcho-repr | 0.0245 | 0.0000 | 0.0007 | 0.0252 | 33.6 | 62,549 |
| graphiti | 0.2220 | 0.0000 | 0.0004 | 0.2224 | 121.2 | 801,944 |
| letta | 0.0644 | 0.0208 | 0.0000 | 0.0852 | 10.8 | 49,357 |

Judge agreement (gemini-3.1-pro-preview vs gemini-3.8-flash): 39/40 (98%).

Spent on this split: $2.63 (of which judging and probes $0.62).
