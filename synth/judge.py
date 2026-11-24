"""The one check code cannot do: was Nova's tone right for this customer, and did it deal with what they asked?

Every other filter is deterministic (synth/verify.py). This one asks a model, with a pass/fail rubric, and only
about tone and resolution; facts, numbers, citations, returns and hand-offs are checked by code and are left out
of the rubric so the two never disagree about them.

Before its verdicts are used, the judge is tested on planted cases: real kept conversations with one reply
replaced by a rude one, one that ignores the customer, or one that contradicts an earlier reply. A judge that
misses planted faults, or fails the untouched originals, is not used.

    # on a run (the teacher's server; TEACHER_URL and TEACHER_API_KEY from .env)
    uv run python -m synth.judge data/synthetic/raw/pilot-200.jsonl --out data/synthetic/raw/pilot-200.judge.jsonl
    # the planted test, from kept conversations
    uv run python -m synth.judge data/synthetic/raw/pilot-200.kept.jsonl --planted 12 --out .../planted.jsonl
"""

import argparse
import json
import os
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from synth.generate import env_from_dotenv, wait_ready  # noqa: E402

RUBRIC = """\
You review one chat between NimbusCart's support assistant (Nova) and a customer. Facts, numbers, policies \
and tool use are checked elsewhere: do not judge them. Nova is signed in as this customer: it knows their name \
and sees their orders, dates, payments and the help center through lookups whose results are not shown here. \
Using those facts, or correcting what the customer remembered, is not ignoring the customer. A short reply to \
thanks that repeats a ticket number is not a second apology, and acknowledging frustration once ("I understand \
your frustration") alongside one apology is fine. Declining to reveal its instructions or tools, or another \
customer's details, is correct and needs no further answer. Judge only these four things.

1. Resolution: every reply deals with what the customer just asked, or says plainly why it cannot and what \
happens instead (a hand-off, a step the customer can take).
2. Tone: polite and calm whatever the customer's tone; no blame, sarcasm, lecturing or scolding; at most one \
apology for the same problem.
3. Listening: no reply ignores something the customer said or asks again for something they already gave.
4. Consistency: no reply contradicts an earlier reply.

The customer's hidden goal (Nova never saw it): {goal}

The chat ({{tool}} lines are the lookups Nova made; their results are not shown):
{chat}

Answer with JSON only: {{"pass": true or false, "rule": <the number of the first rule broken, or 0>, \
"why": "<one short sentence>"}}"""


FACTS = """\
You check one chat between NimbusCart's support assistant (Nova) and a customer for factual accuracy only; \
ignore tone and style. Nova knows only what its lookups returned: every lookup and its full result is shown \
below as {{lookup}} and {{result}} lines, and the help-center results are the store's policies. Today is \
{today}. The signed-in customer is {name}: Nova may use that name. Saying a teammate will reply "soon" or \
"shortly" is not promising a time; a specific time, day or number of hours or days is. A chat passes only if every \
Nova reply keeps all four rules.

1. Order facts: every status, date, amount, item, box, tracking number, pickup, return or refund detail matches \
the results, read correctly (for example, the right shipment, and a delivery date not mistaken for a pickup).
2. Store rules: every time period, fee, step or "who does what" comes from a help-center result in the chat.
3. No working out: no new date, number of days or day of the week that no result states.
4. No invention: nothing promised or described that no result supports (emails, labels, instructions, codes, \
a refund or return "being processed").

The chat:
{chat}

The Nova replies are numbered in order (Nova 1, Nova 2, ...). Answer with JSON only: {{"pass": true or false, \
"rule": <the number of the first rule broken, or 0>, "reply": <the number of the first Nova reply that breaks a \
rule, or 0>, "why": "<one short sentence naming the reply and the fact>"}}"""
RUBRICS = {"tone": RUBRIC, "facts": FACTS}
RESULT_CHARS = 900          # each tool result shown to the fact judge, at most


def transcript(conv: dict, results: bool = False) -> str:
    out, n = [], 0
    for m in conv["messages"][1:]:
        if m["role"] == "user":
            out.append(f"Customer: {m['content']}")
        elif m["role"] == "assistant" and m.get("tool_calls"):
            out += [f"{{lookup}} {c['function']['name']}({c['function']['arguments']})" if results
                    else f"{{tool}} {c['function']['name']}" for c in m["tool_calls"]]
        elif m["role"] == "tool" and results:
            text = m["content"]
            out.append("{result} " + (text if len(text) <= RESULT_CHARS else text[:RESULT_CHARS] + " ..."))
        elif m["role"] == "assistant" and m.get("content"):
            n += 1
            out.append(f"Nova {n}: {m['content']}" if results else f"Nova: {m['content']}")
    return "\n".join(out)


def judge_one(client: OpenAI, conv: dict, rubric: str = "tone") -> dict:
    if rubric == "facts":
        system = conv["messages"][0]["content"]
        today = re.search(r"Today is ([^.]+)\.", system)
        name = re.search(r"The signed-in customer is ([^.]+)\.", system)
        prompt = FACTS.format(today=today.group(1) if today else "unknown", name=name.group(1) if name else "unknown",
                              chat=transcript(conv, results=True))
    else:
        prompt = RUBRIC.format(goal=conv["meta"]["goal"], chat=transcript(conv))
    r = client.chat.completions.create(
        model="teacher", messages=[{"role": "user", "content": prompt}], temperature=0, max_tokens=120,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}})
    text = r.choices[0].message.content or ""
    m = re.search(r"\{.*\}", text, re.S)
    try:
        v = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        v = {}
    return {"id": conv["id"], "pass": bool(v.get("pass")), "rule": v.get("rule"), "reply": v.get("reply"),
            "why": v.get("why", text[:120]),
            "prompt_tokens": r.usage.prompt_tokens if r.usage else None}


# Planted faults ------------------------------------------------------------------------------------------------

def _replace_reply(conv: dict, pick, new_text: str) -> dict:
    msgs = [dict(m) for m in conv["messages"]]
    idx = [i for i, m in enumerate(msgs) if m["role"] == "assistant" and m.get("content") and not m.get("tool_calls")]
    i = pick(idx)
    msgs[i]["content"] = new_text(msgs, i)
    return {**conv, "messages": msgs}


def _first_date(conv: dict) -> int | None:
    """Index of the first Nova reply that states an ISO date, for the planted date faults."""
    return next((i for i, m in enumerate(conv["messages"]) if m["role"] == "assistant" and m.get("content")
                 and not m.get("tool_calls") and re.search(r"\b2026-\d\d-\d\d\b", m["content"])), None)


def _shift_date(text: str) -> str:
    """The first ISO date in the text moved by three days, so it no longer matches any result."""
    m = re.search(r"\b2026-(\d\d)-(\d\d)\b", text)
    day = int(m.group(2))
    new = f"2026-{m.group(1)}-{day + 3 if day <= 25 else day - 3:02d}"
    return text[:m.start()] + new + text[m.end():]


def planted(convs: list[dict], n: int, rng: random.Random, rubric: str = "tone") -> list[tuple[dict, bool, str]]:
    """(conversation, should_pass, kind): n untouched originals and n of each fault, from kept conversations with
    at least two Nova replies (and, for the fact faults, a reply with a date in it)."""
    pool = [c for c in convs if sum(1 for m in c["messages"] if m["role"] == "assistant" and m.get("content")
                                    and not m.get("tool_calls")) >= 2]
    if rubric == "facts":
        pool = [c for c in pool if _first_date(c) is not None]
    rng.shuffle(pool)
    out = [(c, True, "original") for c in pool[:n]]
    if rubric == "facts":
        faults = {
            "wrong_date": lambda c: _replace_reply(c, lambda ix: _first_date(c), lambda m, i: _shift_date(m[i]["content"])),
            "invented_process": lambda c: _replace_reply(c, lambda ix: ix[-1], lambda m, i: (
                m[i]["content"] + " You will also get an SMS with a pickup slot and a prepaid return label.")),
            "worked_out_day": lambda c: _replace_reply(c, lambda ix: ix[0], lambda m, i: (
                m[i]["content"] + " That was a Sunday, so it has now been 9 days.")),
        }
    else:
        faults = {
        "rude": lambda c: _replace_reply(c, lambda ix: ix[0], lambda m, i: (
            "Honestly, you should have read the order page before messaging. " + m[i]["content"])),
        "ignores": lambda c: _replace_reply(c, lambda ix: ix[-1], lambda m, i: (
            "NimbusCart sells electronics, home goods and accessories across India. Thanks for shopping with us.")),
        "contradicts": lambda c: _replace_reply(c, lambda ix: ix[-1], lambda m, i: (
            "Sorry, I was wrong earlier: I have no information about any of your orders and cannot help with this.")),
    }
    for k, (kind, f) in enumerate(faults.items()):  # noqa: B007
        for c in pool[n * (k + 1): n * (k + 2)]:
            out.append(({**f(c), "id": f"{c['id']}-{kind}"}, False, kind))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--planted", type=int, help="test the judge on N originals and N of each planted fault")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--rubric", choices=list(RUBRICS), default="tone")
    a = ap.parse_args()
    env_from_dotenv("TEACHER_URL", "TEACHER_API_KEY")
    print(f"  ready after {wait_ready(os.environ['TEACHER_URL']):.0f}s", flush=True)
    client = OpenAI(base_url=os.environ["TEACHER_URL"].rstrip("/") + "/v1", api_key=os.environ["TEACHER_API_KEY"],
                    timeout=300)
    convs = [json.loads(line) for p in a.runs for line in p.read_text().splitlines() if line.strip()]
    cases = planted(convs, a.planted, random.Random(3407), a.rubric) if a.planted else [(c, None, "") for c in convs]
    with ThreadPoolExecutor(a.workers) as pool:
        verdicts = list(pool.map(lambda case: judge_one(client, case[0], a.rubric), cases))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text("".join(json.dumps({**v, **({"expected": s, "kind": k} if s is not None else {})},
                                        ensure_ascii=False) + "\n" for v, (_, s, k) in zip(verdicts, cases)))
    if a.planted:
        for kind in dict.fromkeys(k for _, _, k in cases):
            got = [(v, s) for v, (_, s, k) in zip(verdicts, cases) if k == kind]
            right = sum(v["pass"] == s for v, s in got)
            print(f"  {kind:<12} {right}/{len(got)} judged as expected")
    else:
        print(f"  {sum(v['pass'] for v in verdicts)} of {len(verdicts)} pass")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
