"""Lay out a generation run for reading: every conversation as a transcript, plus a few counts per run.

    uv run python -m synth.read_run data/synthetic/raw/<run>.jsonl [more runs...] --out data/synthetic/reading/x.md

With several runs, conversations are grouped by scenario so the same situation can be read across teachers.
The counts are quick signals for reading, not the verifiers (those come with the filtering step).
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

CITE = re.compile(r"\[kb:[^\]]+\]")
OFFER = re.compile(r"(would you like me to|do you want me to|shall i|is there anything else)[^.?!]*\?\s*$", re.I)


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def words(text: str | None) -> int:
    return len((text or "").split())


def replies(conv: dict) -> list[str]:
    return [m["content"] for m in conv["messages"] if m["role"] == "assistant" and m.get("content")]


def signals(conv: dict) -> dict:
    rs = replies(conv)
    calls = [c["name"] for t in conv["traces"] for c in t["tool_calls"]]
    return {"outcome": conv["meta"]["outcome"], "customer_turns": conv["meta"]["customer_turns"],
            "tool_calls": len(calls), "tools": calls,
            "format_errors": sum(t["format_errors"] for t in conv["traces"]),
            "grounding_issues": sum(len(t.get("grounding") or []) for t in conv["traces"]),
            "max_reply_words": max((words(r) for r in rs), default=0),
            "citations": sum(len(CITE.findall(r)) for r in rs),
            "escalated": any(t["escalated"] for t in conv["traces"]),
            "fallback": sum(r == "Let me connect you with a teammate." for r in rs),
            "narrated_calls": sum(1 for m in conv["messages"] if m.get("tool_calls") and (m.get("content") or "").strip()),
            "calls_messages": sum(1 for m in conv["messages"] if m.get("tool_calls")),
            "closing_offers": sum(bool(OFFER.search(r)) for r in rs),
            "replies": len(rs),
            "multi_paragraph": sum("\n" in r.strip() for r in rs),
            "tickets": sum(1 for t in conv["traces"] for c in t["tool_calls"]
                           if c["name"] == "escalate_to_human" and c.get("ok")),
            "blind_steps": blind_steps(conv)}


def blind_steps(conv: dict) -> tuple[int, int]:
    """(model calls after the first turn, of which saw none of Nova's earlier replies)."""
    later = blind = 0
    first_user = next(m["content"] for m in conv["messages"] if m["role"] == "user")
    for s in conv["steps"]:
        users = [m for m in s["messages"] if m["role"] == "user"]
        if len(users) == 1 and users[0]["content"] == first_user:
            continue
        later += 1
        blind += not any(m["role"] == "assistant" and m.get("content") and not m.get("tool_calls")
                         for m in s["messages"])
    return later, blind


def transcript(conv: dict) -> list[str]:
    out = []
    for m in conv["messages"][1:]:
        if m["role"] == "user":
            out.append(f"> **Customer:** {m['content']}")
        elif m["role"] == "tool":
            body = m["content"] if len(m["content"]) < 400 else m["content"][:400] + " …"
            out.append(f">> `result` {body}")
        else:
            for c in m.get("tool_calls", []):
                out.append(f">> `{c['function']['name']}({c['function']['arguments']})`")
            if m.get("content"):
                out.append(f"> **Nova:** {m['content']}")
        out.append(">")
    return out[:-1]


def summary(name: str, convs: list[dict]) -> list[str]:
    s = [signals(c) for c in convs]
    n = len(s)
    out = Counter(x["outcome"] for x in s)
    tok = [c["meta"]["teacher_tokens"] for c in convs]
    later, blind = (sum(x["blind_steps"][i] for x in s) for i in (0, 1))
    habits = (f"| {name} | {sum(x['narrated_calls'] for x in s)}/{sum(x['calls_messages'] for x in s)} | "
              f"{sum(x['closing_offers'] for x in s)}/{sum(x['replies'] for x in s)} | "
              f"{sum(x['multi_paragraph'] for x in s)} | {blind}/{later} | "
              f"{sum(x['tickets'] for x in s)} ({sum(x['tickets'] > 1 for x in s)} conversations with two) |")
    return [f"| {name} | {n} | {out['done']}/{out['gave_up']}/{out['max_turns'] + out['error']} | "
            f"{sum(x['customer_turns'] for x in s) / n:.1f} | {sum(x['tool_calls'] for x in s) / n:.1f} | "
            f"{sum(x['format_errors'] for x in s)} | {sum(x['grounding_issues'] for x in s)} | "
            f"{sum(x['fallback'] for x in s)} | {sum(x['max_reply_words'] > 70 for x in s)} | "
            f"{sum(x['citations'] for x in s)} | "
            f"{sum(t['prompt'] for t in tok) / n:,.0f} / {sum(t['completion'] for t in tok) / n:,.0f} | "
            f"{sum(c['meta']['seconds'] for c in convs) / n:.0f} |"], habits


def customers_only(convs: list[dict], out: Path) -> None:
    """Each conversation's customer messages with the persona, the Bitext opener it adapted and its goal, and a
    blank verdict to fill in: realistic or not, and why."""
    lines = ["# Simulated customers, for judging realism", "",
             "Mark each one `realistic: yes` or `realistic: no` with a reason. Nova's side is left out on purpose.", ""]
    for n, c in enumerate(convs, 1):
        m = c["meta"]
        lines += [f"## {n}. {m['persona']} · {m['scenario']} · {m['outcome']}", "",
                  f"*Bitext opener:* {m.get('opener') or '(none)'}  ", f"*Goal:* {m['goal']}", ""]
        lines += [f"{k}. {msg['content']}" for k, msg in
                  enumerate((x for x in c["messages"] if x["role"] == "user"), 1)]
        lines += ["", "realistic: ", ""]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines))
    print(f"wrote {out} ({len(convs)} conversations, customer side only)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--customers", action="store_true",
                    help="only the customer's side, numbered, for judging whether the simulated customers are realistic")
    a = ap.parse_args()
    if a.customers:
        return customers_only([c for p in a.runs for c in load(p)], a.out)
    runs = {p.stem: load(p) for p in a.runs}
    lines = ["# Synthetic conversations, for reading", "",
             "| Run | Convs | done / gave up / other | Customer turns | Tool calls | Format errors | "
             "Grounding issues | Fallback replies | Replies > 70 words | Citations | Teacher tokens in / out | "
             "Seconds |", "|" + "---|" * 12]
    habit_rows = []
    for name, convs in runs.items():
        row, habits = summary(name, convs)
        lines += row
        habit_rows.append(habits)
    lines += ["", "| Run | Tool calls with text | Replies ending in an offer | Replies with several paragraphs | "
              "Later calls blind to Nova's earlier replies | Tickets opened |", "|---|---|---|---|---|---|", *habit_rows]
    by_scenario = defaultdict(list)
    for name, convs in runs.items():
        for c in convs:
            by_scenario[c["meta"]["scenario"]].append((name, c))
    for scenario in sorted(by_scenario):
        lines += ["", f"## {scenario}"]
        for name, c in by_scenario[scenario]:
            m, s = c["meta"], signals(c)
            lines += ["", f"### {name} · {c['id']} · customer {m['customer_id']} · order {m['order_id']} · "
                          f"{s['outcome']}", "",
                      f"*Goal:* {m['goal']}  ", f"*Knows:* {' '.join(m['knowledge'])}  ",
                      f"*Signals:* {s['tool_calls']} calls ({', '.join(s['tools']) or 'none'}), "
                      f"format errors {s['format_errors']}, grounding issues {s['grounding_issues']}, "
                      f"longest reply {s['max_reply_words']} words", ""]
            lines += transcript(c)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text("\n".join(lines) + "\n")
    print(f"wrote {a.out} ({sum(len(v) for v in runs.values())} conversations)")


if __name__ == "__main__":
    main()
