## Results: full

| Arm | n | Accuracy | 95% interval |
|---|--:|--:|---|
| full-context | 25 | 84% | 65%–94% |
| retrieval | 25 | 96% | 80%–99% |
| textual | 25 | 92% | 75%–98% |
| mem0 | 25 | 84% | 65%–94% |

### Where answers were lost

| Arm | correct | update never stored | stored, not delivered | delivered, answered old value | delivered, other error | wrong, unclassified | old value stored as current | old value delivered |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| full-context | 21 | 0 | 0 | 4 | 0 | 0 | n/a | 23 |
| retrieval | 24 | 0 | 0 | 0 | 1 | 0 | n/a | 23 |
| textual | 23 | 2 | 0 | 0 | 0 | 0 | 2 | 12 |
| mem0 | 21 | 1 | 0 | 1 | 2 | 0 | 9 | 20 |

### Cost per question (USD, mean)

| Arm | write | read | answer | total system | model calls (write) | input tokens (write) |
|---|--:|--:|--:|--:|--:|--:|
| full-context | 0.0000 | 0.0000 | 0.0275 | 0.0275 | 0.0 | 0 |
| retrieval | 0.0000 | 0.0000 | 0.0016 | 0.0016 | 0.0 | 0 |
| textual | 0.2755 | 0.0000 | 0.0018 | 0.2773 | 58.8 | 312,253 |
| mem0 | 0.1800 | 0.0000 | 0.0006 | 0.1806 | 51.4 | 586,310 |

### What each system stored and returned (mean per question)

- **full-context**: context tokens 123,631
- **retrieval**: context tokens 5,881
- **textual**: profile tokens 5567
- **mem0**: facts stored 250; facts returned 20; unparsed extraction replies 0.00

Judge agreement (gemini-3.1-pro-preview vs gemini-3.8-flash): 48/48 (100%).

Spent on this split: $13.26 (of which judging and probes $1.09).
