"""Every number that blog part 8 quotes, recomputed from the committed results.

    uv run python scripts/replays/experiment_numbers.py > scripts/replays/experiment_numbers_output.txt

Reads results/{main,full,pilot}/ (the result files and the saved call ledgers)
and data/longmemeval_s_cleaned.json. Makes no model calls.

"Context tokens" in the repository's report are characters / 4. Where the
ledger has the model's own count (the answer call's input tokens), both are
printed, so the post can use the measured one.
"""

from __future__ import annotations

import itertools
import json
import math
import statistics as st
from collections import Counter, defaultdict

from memeval import config, data
from memeval.findings import BOTH, PREVIOUS, costs, load, per_q
from memeval.report import ORDER, ledger, outcome, wilson

ARMS_MAIN = ORDER


def head(title: str) -> None:
    print(f"\n## {title}\n")


def pct(k, n):
    return f"{k}/{n} = {k / n:.1%}" if n else "-"


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar: binomial test on the discordant pairs."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def dataset() -> None:
    raw = data.load_raw()
    head("Dataset: LongMemEval S, cleaned")
    types = Counter(x["question_type"] for x in raw)
    print("questions:", len(raw), dict(types))
    abs_all = [x for x in raw if x["question_id"].endswith("_abs")]
    print("abstention questions in all types:", len(abs_all), Counter(x["question_type"] for x in abs_all))
    ku = [x for x in raw if x["question_type"] == "knowledge-update"]
    ku_na = [x for x in ku if not x["question_id"].endswith("_abs")]
    print("knowledge-update:", len(ku), "of which abstention:", len(ku) - len(ku_na))

    def stats(rows, label):
        n_sess = [len(x["haystack_sessions"]) for x in rows]
        turns = [len(s) for x in rows for s in x["haystack_sessions"]]
        chars = [sum(len(t["content"]) for s in x["haystack_sessions"] for t in s) for x in rows]
        user = sum(len(t["content"]) for x in rows for s in x["haystack_sessions"] for t in s if t["role"] == "user")
        ev = Counter(len(x["answer_session_ids"]) for x in rows)
        print(f"[{label}] n={len(rows)} sessions/question mean {st.mean(n_sess):.1f} min {min(n_sess)} max {max(n_sess)}")
        print(f"[{label}] turns/session mean {st.mean(turns):.1f} median {st.median(turns)}")
        print(f"[{label}] chars/question mean {st.mean(chars):,.0f} -> chars/4 {st.mean(chars) / 4:,.0f}")
        print(f"[{label}] chars/session mean {sum(chars) / sum(n_sess):,.0f} -> /4 {sum(chars) / sum(n_sess) / 4:,.0f}")
        print(f"[{label}] user share of characters {user / sum(chars):.1%}")
        print(f"[{label}] evidence sessions per question: {dict(ev)}")

    stats(raw, "all 500")
    stats(ku_na, "KU, 72 without abstention")
    gaps, after, pos = [], [], []
    for x in ku_na:
        dates = {sid: data.parse_date(d) for sid, d in zip(x["haystack_session_ids"], x["haystack_dates"])}
        ev = sorted(dates[s] for s in x["answer_session_ids"])
        gaps.append((ev[-1] - ev[0]).days)
        after.append((data.parse_date(x["question_date"]) - ev[-1]).days)
        order = sorted(range(len(x["haystack_session_ids"])), key=lambda i: data.parse_date(x["haystack_dates"][i]))
        rank = {x["haystack_session_ids"][i]: r for r, i in enumerate(order)}
        pos.append([rank[s] / (len(order) - 1) for s in x["answer_session_ids"]])
    print(f"days between the two evidence sessions: median {st.median(gaps)}, min {min(gaps)}, max {max(gaps)}, "
          f"same day {sum(g == 0 for g in gaps)}")
    print(f"days from the second evidence session to the question: median {st.median(after)}, min {min(after)}, max {max(after)}")
    print(f"evidence position in the dated history (0 first, 1 last): first mean {st.mean(p[0] for p in pos):.2f}, "
          f"second mean {st.mean(p[-1] for p in pos):.2f}")
    print("abstention examples:")
    for x in [x for x in ku if x["question_id"].endswith("_abs")]:
        print("  ", x["question_id"], "|", x["question"], "|", x["answer"])
    distractor = Counter(("sharegpt" if s.startswith("sharegpt") else "ultrachat" if s.startswith("ultrachat")
                          else "answer" if s.startswith("answer") else "simulated")
                         for x in ku_na for s in x["haystack_session_ids"])
    print("session id kinds in the 72 KU histories:", dict(distractor))

    head("Splits")
    for name in ("pilot", "main", "full"):
        print(name, len(data.split(name)))
    print("previous-value questions:", len(PREVIOUS), "both:", len(BOTH))
    main_ids = set(data.split("main"))
    print("6a1eabeb in main:", "6a1eabeb" in main_ids, "in full:", "6a1eabeb" in data.split("full"))

    head("The 5K question, trimmed and full")
    for full in (False, True):
        q = data.question("6a1eabeb", full_history=full)
        chars = sum(len(t.content) for s in q.sessions for t in s.turns)
        print(f"full={full}: {len(q.sessions)} sessions, chars/4 {chars / 4:,.0f}, first {q.sessions[0].date}, "
              f"last {q.sessions[-1].date}, asked {q.date}")
        if not full:
            for s in q.sessions:
                print(f"   {s.date:%Y-%m-%d %H:%M} {'EVIDENCE' if s.evidence else '        '} {s.id} turns={len(s.turns)}")
    tri = [sum(len(t.content) for s in data.question(i).sessions for t in s.turns) / 4 for i in data.split("main")]
    print(f"trimmed main histories, chars/4: mean {st.mean(tri):,.0f}, min {min(tri):,.0f}, max {max(tri):,.0f}")
    fl = [sum(len(t.content) for s in data.question(i, full_history=True).sessions for t in s.turns) / 4
          for i in data.split("full")]
    print(f"full histories (25), chars/4: mean {st.mean(fl):,.0f}")


def accuracy(split: str, res) -> None:
    head(f"Accuracy ({split})")
    for arm, rows in res.items():
        n = len(rows)
        k = sum(r["judge"]["correct"] for r in rows.values())
        lo, hi = wilson(k, n)
        print(f"{arm:15s} {pct(k, n):>16s}  95% {lo:.1%}-{hi:.1%}  half-width ~{(hi - lo) / 2:.1%}")


def pairs(res) -> None:
    head("McNemar, every pair of the arms between 82% and 97% (main)")
    band = [a for a, rows in res.items()
            if 0.81 <= sum(r["judge"]["correct"] for r in rows.values()) / len(rows) <= 0.98]
    print("arms in the band:", band, "pairs:", len(list(itertools.combinations(band, 2))))
    out = []
    for a, b in itertools.combinations(band, 2):
        qs = set(res[a]) & set(res[b])
        only_a = sum(res[a][q]["judge"]["correct"] and not res[b][q]["judge"]["correct"] for q in qs)
        only_b = sum(res[b][q]["judge"]["correct"] and not res[a][q]["judge"]["correct"] for q in qs)
        out.append((mcnemar_exact(only_a, only_b), a, b, only_a, only_b))
    m = len(out)
    for p, a, b, x, y in sorted(out)[:8]:
        print(f"{a} vs {b}: only {a} {x}, only {b} {y}, p={p:.4f} (Bonferroni threshold 0.05/{m}={0.05 / m:.4f})")


def judges(split: str, res) -> None:
    agree = n = 0
    for rows in res.values():
        for r in rows.values():
            jc = r.get("judge_check")
            if jc is not None:
                n += 1
                agree += jc.get("correct") == r["judge"]["correct"]
    print(f"[{split}] judge agreement: {agree}/{n}")


def cost(split: str, res, cost_) -> None:
    head(f"Cost and time per question ({split})")
    calls = ledger(split)
    phase = defaultdict(lambda: defaultdict(float))
    ans_tokens = defaultdict(list)
    read_tokens = defaultdict(lambda: defaultdict(int))
    for c in calls:
        arm = c.get("arm")
        if c.get("phase") in ("write", "read", "answer"):
            phase[arm][c["phase"]] += c["usd"]
        if c.get("phase") in ("read", "answer") and c["kind"] == "chat":
            read_tokens[arm][c["qid"]] += c["input_tokens"]
        if c.get("phase") == "answer" and c["kind"] == "chat":
            ans_tokens[arm].append(c["input_tokens"])
    for arm, rows in res.items():
        secs = st.mean((r.get("seconds") or {}).get("write", 0) for r in rows.values())
        ctx = st.mean(len(r["context"] or "") for r in rows.values()) / 4
        la = "honcho" if arm.startswith("honcho") else arm
        rt = read_tokens.get(arm, {})
        print(f"{arm:15s} USD/q {per_q(cost_, arm, rows):.4f}  write calls {per_q(cost_, arm, rows, 'calls'):.1f}  "
              f"write input tokens {per_q(cost_, arm, rows, 'tokens'):,.0f}  write secs {secs:.0f}  "
              f"context chars/4 {ctx:,.0f}  read+answer input tokens/q {st.mean(rt.values()) if rt else 0:,.0f}")
    total = sum(c["usd"] for c in calls)
    jp = sum(c["usd"] for c in calls if c.get("phase") not in ("write", "read", "answer"))
    print(f"split total ${total:.2f}, of which judging/probes/other ${jp:.2f}")
    for arm in ("letta-persona", "graphiti", "graphiti-chunk"):
        print(f"  arm total {arm}: ${sum(c['usd'] for c in calls if c.get('arm') == arm):.2f}")


def probes(res) -> None:
    head("Probes (main): what memory held, what was delivered, where answers were lost")
    for arm, rows in res.items():
        pr = [r["probe"] for r in rows.values() if r.get("probe") and "skipped" not in r["probe"]]
        n = len(pr)
        st_ = [p["stored"] for p in pr if "stored" in p]
        both = [r for r in rows.values() if r.get("probe") and "skipped" not in r["probe"]
                and r["probe"]["delivered"].get("new_present") and r["probe"]["delivered"].get("old_present")]
        line = f"{arm:15s} probed {n}"
        if st_:
            line += (f"  new stored {pct(sum(bool(s.get('new_present')) for s in st_), len(st_))}"
                     f"  old stored {pct(sum(bool(s.get('old_present')) for s in st_), len(st_))}"
                     f"  old as current {pct(sum(bool(s.get('old_as_current')) for s in st_), len(st_))}")
        line += f"  both delivered {len(both)}, correct {sum(r['judge']['correct'] for r in both)}"
        print(line)
        print("   outcomes:", dict(Counter(outcome(r) for r in rows.values())))
    skipped = [q for q, r in res["full-context"].items() if "skipped" in (r.get("probe") or {})]
    print("questions with no old value (probes skipped):", len(skipped), skipped)


def intent(res) -> None:
    head("Current value / earlier value / both (main)")
    for arm, rows in res.items():
        g = defaultdict(lambda: [0, 0])
        for q, r in rows.items():
            k = "previous" if q in PREVIOUS else "both" if q in BOTH else "current"
            g[k][0] += r["judge"]["correct"]
            g[k][1] += 1
        print(f"{arm:15s}", {k: f"{v[0]}/{v[1]}" for k, v in g.items()})


def history(main, full, cm, cf) -> None:
    head("Full history against trimmed, same 25 questions")
    for arm, frows in full.items():
        mrows = {q: r for q, r in main[arm].items() if q in frows}
        km = sum(r["judge"]["correct"] for r in mrows.values())
        kf = sum(r["judge"]["correct"] for r in frows.values())
        ctxm = st.mean(len(r["context"]) for r in mrows.values()) / 4
        ctxf = st.mean(len(r["context"]) for r in frows.values()) / 4
        um, uf = per_q(cm, arm, mrows), per_q(cf, arm, frows)
        lost = [q for q in frows if mrows[q]["judge"]["correct"] and not frows[q]["judge"]["correct"]]
        gained = [q for q in frows if frows[q]["judge"]["correct"] and not mrows[q]["judge"]["correct"]]
        print(f"{arm:13s} 10 sessions {pct(km, len(mrows))}  full {pct(kf, len(frows))}  ctx {ctxm:,.0f} -> {ctxf:,.0f}  "
              f"USD {um:.4f} -> {uf:.4f} (x{uf / um if um else 0:.1f})  lost {lost} gained {gained}")
        if arm == "full-context":
            for q, r in frows.items():
                if not r["judge"]["correct"]:
                    print("    full-context wrong on full history:", q, r["question"], "| key:", r["reference"],
                          "| outcome:", outcome(r))
    calls = ledger("full")
    fc = [c["input_tokens"] for c in calls if c.get("arm") == "full-context" and c.get("phase") == "answer"]
    print(f"full-context answer input tokens on full histories: mean {st.mean(fc):,.0f}")
    fm = [c["input_tokens"] for c in ledger("main") if c.get("arm") == "full-context" and c.get("phase") == "answer"]
    print(f"full-context answer input tokens on trimmed histories: mean {st.mean(fm):,.0f}, min {min(fm):,}, max {max(fm):,}")


def spend() -> None:
    head("Spend by split")
    for split in ("pilot", "main", "full"):
        print(split, f"${sum(c['usd'] for c in ledger(split)):.2f}")


def example() -> None:
    head("The 5K question across arms (main and full)")
    for split in ("main", "full"):
        for arm_dir in sorted((config.RESULTS_DIR / split).iterdir()):
            p = arm_dir / "6a1eabeb.json"
            if p.exists() and "judge" in (r := json.loads(p.read_text())):
                print(f"[{split}] {arm_dir.name:15s} correct={r['judge']['correct']}  probe={json.dumps(r.get('probe'))}")


def main() -> None:
    dataset()
    res, cm = load("main"), costs("main")
    accuracy("main", res)
    pairs(res)
    judges("main", res)
    judges("pilot", load("pilot"))
    cost("main", res, cm)
    probes(res)
    intent(res)
    full, cf = load("full"), costs("full")
    accuracy("full", full)
    cost("full", full, cf)
    history(res, full, cm, cf)
    spend()
    example()


if __name__ == "__main__":
    main()
