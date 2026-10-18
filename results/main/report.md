## Results: main

| Arm | n | Accuracy | 95% interval |
|---|--:|--:|---|
| full-context | 67 | 90% | 80%–95% |
| retrieval | 67 | 97% | 90%–99% |
| textual | 67 | 93% | 84%–97% |
| mem0 | 67 | 84% | 73%–91% |
| honcho-chat | 67 | 87% | 76%–93% |
| honcho-repr | 67 | 93% | 84%–97% |
| graphiti | 67 | 82% | 71%–89% |
| graphiti-chunk | 67 | 18% | 11%–29% |
| letta | 67 | 69% | 57%–78% |
| letta-batch | 67 | 58% | 46%–69% |
| letta-persona | 67 | 90% | 80%–95% |

### Where answers were lost

| Arm | correct | update never stored | stored, not delivered | delivered, answered old value | delivered, other error | wrong, unclassified | old value stored as current | old value delivered |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| full-context | 60 | 0 | 0 | 5 | 1 | 1 | n/a | 58 |
| retrieval | 65 | 0 | 0 | 2 | 0 | 0 | n/a | 56 |
| textual | 62 | 1 | 0 | 1 | 3 | 0 | 5 | 40 |
| mem0 | 56 | 6 | 0 | 2 | 2 | 1 | 25 | 51 |
| honcho-chat | 58 | 1 | 1 | 3 | 4 | 0 | 43 | 40 |
| honcho-repr | 62 | 2 | 0 | 1 | 1 | 1 | 43 | 54 |
| graphiti | 55 | 5 | 2 | 1 | 3 | 1 | 14 | 46 |
| graphiti-chunk | 12 | 45 | 0 | 0 | 1 | 9 | 15 | 17 |
| letta | 46 | 15 | 0 | 0 | 2 | 4 | 16 | 24 |
| letta-batch | 39 | 22 | 0 | 0 | 0 | 6 | 1 | 11 |
| letta-persona | 60 | 3 | 0 | 0 | 2 | 2 | 6 | 45 |

### Cost per question (USD, mean)

| Arm | write | read | answer | total system | model calls (write) | input tokens (write) |
|---|--:|--:|--:|--:|--:|--:|
| full-context | 0.0000 | 0.0000 | 0.0065 | 0.0065 | 0.0 | 0 |
| retrieval | 0.0000 | 0.0000 | 0.0017 | 0.0017 | 0.0 | 0 |
| textual | 0.0212 | 0.0000 | 0.0007 | 0.0219 | 10.1 | 34,269 |
| mem0 | 0.0389 | 0.0000 | 0.0006 | 0.0395 | 10.1 | 116,073 |
| honcho-chat | 0.0274 | 0.0014 | 0.0003 | 0.0291 | 38.3 | 70,661 |
| honcho-repr | 0.0274 | 0.0000 | 0.0007 | 0.0281 | 38.3 | 70,661 |
| graphiti | 0.6400 | 0.0000 | 0.0004 | 0.6405 | 720.1 | 2,345,801 |
| graphiti-chunk | 0.2375 | 0.0000 | 0.0004 | 0.2380 | 120.6 | 897,212 |
| letta | 0.1298 | 0.0026 | 0.0000 | 0.1324 | 81.2 | 325,687 |
| letta-batch | 0.0249 | 0.0039 | 0.0000 | 0.0288 | 10.8 | 51,712 |
| letta-persona | 0.1482 | 0.0036 | 0.0000 | 0.1518 | 87.8 | 398,307 |

### What each system stored and returned (mean per question)

- **full-context**: context tokens 27,890
- **retrieval**: context tokens 5,761
- **textual**: profile tokens 1513
- **mem0**: facts stored 54; facts returned 20; unparsed extraction replies 0.00
- **honcho-chat**: deductive conclusions 2; explicit conclusions 111; inductive conclusions 2; context tokens 77
- **honcho-repr**: deductive conclusions 2; explicit conclusions 111; inductive conclusions 2; context tokens 935
- **graphiti**: edges 319; edges closed (superseded) 4.8; episodes 107; failed episodes 0.00; facts returned 10
- **graphiti-chunk**: edges 57; edges closed (superseded) 0.2; episodes 20; failed episodes 0.00; facts returned 10
- **letta**: human block chars 1322; questions with an empty human block 0/67; tool calls while answering 2.3; no reply 0/67
- **letta-batch**: human block chars 109; questions with an empty human block 43/67; tool calls while answering 3.4; no reply 1/67
- **letta-persona**: human block chars 1586; questions with an empty human block 0/67; tool calls while answering 2.5; no reply 0/67

Judge agreement (gemini-3.1-pro-preview vs gemini-3.8-flash): 130/132 (98%).

Spent on this split: $92.66 (of which judging and probes $6.17).
