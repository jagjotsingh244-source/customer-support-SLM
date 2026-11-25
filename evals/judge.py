"""An LLM judge for the two things code cannot check in a reply: grounded and resolved.

    # agreement with the hand labels (evals/judge/labels.jsonl) on one half of the 50
    uv run python evals/judge.py agree --split tune --prompt v1
    # every reply of some runs; verdicts go to evals/runs/<run>/judge-<prompt>.jsonl
    uv run python evals/judge.py run --prompt v2 2026-11-25_golden-sft2a 2026-11-25_sim-sft2a-r1
    # the same prompt with Gemini as the judge (Vertex AI: VERTEX_API_KEY, VERTEX_PROJECT); all 75 labels at once
    uv run python evals/judge.py agree --judge gemini --split all --prompt v5

The judge is gpt-oss-120b (serving/modal_judge.py): not the model that wrote the training conversations
(Qwen3.5-27B), so it does not simply prefer the style it taught. JUDGE_URL is the server, without /v1; the key
is TEACHER_API_KEY. Temperature 0. With --judge gemini the judge is gemini-4-hydrogen instead, a different family
from both the teacher and the student; it did rewrite the Bitext replies SFT-1 was trained on, so its verdicts on
SFT-1 replies may lean towards that style.

One question per criterion, each a separate call with a yes/no answer, never a score: a 1-10 scale has no
threshold that means anything. The judge sees the evidence Nova had (every tool result so far, today's date,
the customer's name), the customer's message and the reply; without the evidence it could only judge fluency.

Prompts are versioned and never edited once used: a change is a new version. Each version is tuned only on the
"tune" half of the labels; agreement is reported on the "test" half, in both directions, because most replies
pass and plain accuracy flatters a judge that misses failures:
  TPR  of the replies the labels pass, the share the judge passes
  TNR  of the replies the labels fail, the share the judge fails (the failures it catches)
"""

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from evals.judge_labels import load as load_labels  # noqa: E402
from evals.judge_units import date_facts, evidence_text, get_unit, history_text, load_units  # noqa: E402
from synth.generate import env_from_dotenv  # noqa: E402

JUDGE_MODEL = "gpt-oss-120b"
OUT = ROOT / "evals" / "judge"
CRITERIA = ("grounded", "resolved")
VERDICT = re.compile(r"VERDICT:\s*\**\s*(PASS|FAIL)", re.I)

# v1: the plain prompts, before looking at any label (one criterion each, evidence included).
PROMPTS: dict[str, dict[str, str]] = {"v1": {
    "grounded": """\
You are grading one reply from Nova, a support assistant for the online store NimbusCart.

Criterion: GROUNDED. Answer PASS only if every factual claim in the reply (dates, statuses, amounts, policies, \
steps) is directly supported by the EVIDENCE below. Friendly phrases and questions are not claims.

EVIDENCE (tool results and help-center results Nova had when it wrote the reply):
{evidence}

EARLIER IN THE CHAT:
{history}

CUSTOMER MESSAGE: {customer}

REPLY: {reply}

First list each claim and whether the evidence supports it. Then output exactly one line:
VERDICT: PASS or VERDICT: FAIL""",
    "resolved": """\
You are grading one reply from Nova, a support assistant for the online store NimbusCart.

Criterion: RESOLVED. Answer PASS only if the reply deals with what the customer actually asked in their \
message: it answers it, or it correctly hands the customer to a human teammate.

EVIDENCE (tool results and help-center results Nova had when it wrote the reply):
{evidence}

EARLIER IN THE CHAT:
{history}

CUSTOMER MESSAGE: {customer}

REPLY: {reply}

First say what the customer asked and whether the reply deals with it. Then output exactly one line:
VERDICT: PASS or VERDICT: FAIL""",
}}

# v2: definitions and two short examples per criterion, from the "tune" half of the labels only. What v1 got
# wrong there: it took Nova's own hand-off summary as evidence, accepted a proposal described as a created
# return and a past date called "the correct timeline", and counted "Let me connect you" and "shortly" as
# claims; for resolved it passed replies that ask permission instead of looking, bare hand-off lines, invented
# answers and answers to a different question.
_EVIDENCE_BLOCK = """\
EVIDENCE (what Nova's tools returned before it wrote the reply; today's date and the customer's name are known):
{evidence}

EARLIER IN THE CHAT:
{history}

CUSTOMER MESSAGE: {customer}

REPLY: {reply}"""

PROMPTS["v2"] = {
    "grounded": """\
You are grading one reply from Nova, a support assistant for the online store NimbusCart. Nova can only know \
what its tools returned.

Criterion: GROUNDED. Answer PASS only if every factual claim in the reply is directly supported by the \
EVIDENCE below.

What counts as a factual claim: anything about this customer's orders, items, dates, amounts, statuses, \
tracking, refunds, the store's policies and steps, and actions Nova says it has taken (a ticket opened, a \
return created, a teammate connected).
What is not a claim: greetings, apologies, questions, what Nova can or cannot do, saying what it is about to \
do ("Let me connect you with a teammate"), and vague timing such as "shortly" or "soon".

Rules:
- Only tool RESULTS are evidence. The arguments Nova sent to a tool (a search query, a hand-off summary) are \
Nova's own words, not evidence.
- What the customer said is not evidence either: repeating it as if it had been checked is unsupported.
- Dates must agree with today's date: calling a date that has passed "on time", "correct" or "still on its \
way as planned", or calling a parcel late before its estimated date, is unsupported. A date Nova works out \
itself is supported only if every input is in the evidence and the arithmetic is right. An order date is not \
a delivery or shipping date.
- A return proposal (propose_return with eligible true) is not a return: saying a return or return request \
"has been created", "is confirmed" or "is processed" before the customer confirms is unsupported. An action \
Nova says it has done must appear in the evidence (a hand-off needs an escalate_to_human result).
- "Not lost", "on its way" and similar reassurance need evidence: a parcel long past its estimated date with no \
recent scan does not support them.

Examples (from labelled replies):
1. Customer: "noise cancelling headphones never came, tracking stuck for like 2 weeks." Tracking: last scan \
9 Nov, ETA 3 Nov; a hand-off returned ticket 901807. Reply: "...Since it has been over 14 days without \
delivery, I have escalated this to a teammate under ticket 901807." -> FAIL: "over 14 days" echoes the \
customer's "2 weeks" (and Nova's own hand-off summary); the tracking shows 11 days since the last scan.
2. Customer: "i need to return the webcam". The tools returned an eligible proposal. Reply: "Let me connect \
you with a teammate." -> PASS: no factual claim is made.

""" + _EVIDENCE_BLOCK + """

List each factual claim and the evidence for it (or say none supports it). Then output exactly one line:
VERDICT: PASS or VERDICT: FAIL""",
    "resolved": """\
You are grading one reply from Nova, a support assistant for the online store NimbusCart. Nova can look up \
the customer's orders, tracking, the help center, propose returns (the customer then presses Confirm) and \
hand the customer to a human teammate (escalate_to_human).

Criterion: RESOLVED. Answer PASS only if the reply deals with what the customer asked in THIS message:
- it answers every part of the question correctly, using the evidence; or
- when the evidence cannot answer it (the help center has nothing, or it needs a person), it says so and \
offers or makes a hand-off; or
- it makes a hand-off the situation calls for: the customer asked for a person or manager, a parcel may be \
lost (long past its estimated date with no movement), or a parcel shows delivered but never arrived.

FAIL when the reply:
- asks permission to look something up ("Would you like me to check?") instead of looking;
- answers a different question, or assumes which order the customer means when what they said does not fit it;
- leaves part of the question unanswered, or ignores something the customer just said;
- gives an answer the evidence does not support (an invented time, a wrong date or status) — a wrong answer \
does not resolve anything;
- is only a hand-off line ("Let me connect you with a teammate") with nothing else, when no hand-off was \
needed or none was actually made, so the customer learns nothing;
- declines a request flatly without offering a teammate when the store cannot do it here.
Tone does not matter here; a correct, short reply passes.

Examples (from labelled replies):
1. Customer: "want to return the frying pan, dont need it anymore". No tool called. Reply: "...I can check \
your order to see what's available for you. Would you like me to take a look?" -> FAIL: asks permission \
instead of checking the order and proposing the return.
2. Customer: "hi pls can i pay in emi for my next order". The help-center search found nothing. Reply: "The \
help center does not cover payment in installments. Would you like me to connect you with a teammate?" -> \
PASS: says it cannot answer and offers a person.

""" + _EVIDENCE_BLOCK + """

Say what the customer asked, what the reply does about each part, and which rule applies. Then output exactly \
one line:
VERDICT: PASS or VERDICT: FAIL""",
}

# v3: grounded unchanged (v2 met the bar on the tune half). Resolved becomes a checklist, because v2 still
# passed invented answers ("refunds take 7-10 business days"), a bare hand-off for a parcel that was only late,
# "I cannot answer" when Nova never searched, and "late" for a parcel due tomorrow.
PROMPTS["v3"] = {
    "grounded": PROMPTS["v2"]["grounded"],
    "resolved": """\
You are grading one reply from Nova, a support assistant for the online store NimbusCart. Nova can look up \
the customer's orders and tracking, search the help center (the store's policies), propose returns (the \
customer then presses Confirm) and hand the customer to a human teammate (escalate_to_human).

Criterion: RESOLVED: did this reply actually deal with what the customer asked in THIS message?

Work through these checks in order:
1. Parts: list each thing the customer asked or needs in this message.
2. Looked: for each part, did Nova look up what it needs before answering? A question about the store's \
rules needs a help-center search; a question about an order needs that order looked up. Asking the customer \
for permission to look ("Would you like me to check?") is not looking.
3. Correct: for each part the reply answers, find the answer in the EVIDENCE. An answer that is not there \
(an invented time or step), contradicts it, or gets a date or status wrong compared with today's date does \
not count as an answer. Check that the reply answers the question the customer asked, about what the customer \
described: if the customer says no order was placed, an answer about some existing order is the wrong question.
4. Hand-off: a hand-off is needed only when the customer asked for a person or manager, a parcel may be lost \
(no tracking scan for about a week or more), or a parcel shows delivered but never arrived. A parcel past its \
estimated date that was scanned recently is delayed, not lost. A hand-off has happened only if the EVIDENCE has \
an escalate_to_human result. A reply that is only a hand-off line ("Let me connect you with a teammate") \
resolves the message only when a hand-off was needed AND happened; otherwise the customer learns nothing.
5. Cannot answer: "the help center does not cover this" passes only if Nova searched and the search found \
nothing relevant, and the reply offers or makes a hand-off. Declining flatly, with no teammate offered, fails.

PASS only if every part is answered correctly (checks 2 and 3), or handled by a justified "cannot answer" \
(check 5), or by a needed hand-off that happened (check 4). Otherwise FAIL. Tone does not matter.

Examples (from labelled replies):
1. Customer: "want to return the frying pan, dont need it anymore". No tool called. Reply: "...I can check \
your order to see what's available for you. Would you like me to take a look?" -> FAIL (check 2): asks \
permission instead of checking the order and proposing the return.
2. Customer: "hi pls can i pay in emi for my next order". The help-center search found nothing. Reply: "The \
help center does not cover payment in installments. Would you like me to connect you with a teammate?" -> \
PASS (check 5): it searched, found nothing, and offers a person.

""" + _EVIDENCE_BLOCK + """

Write the five checks briefly. Then output exactly one line:
VERDICT: PASS or VERDICT: FAIL""",
}


# v4 (the last tuning round): v3 plus a listening check, because three of v3's five resolved misses on the
# tune half ignored what the customer had just said or contradicted themselves.
PROMPTS["v4"] = {
    "grounded": PROMPTS["v2"]["grounded"],
    "resolved": PROMPTS["v3"]["resolved"].replace(
        "5. Cannot answer:",
        "5. Listening: the reply must take into account what the customer just said (a correction, \"it is not "
        "faulty\", a date they gave) and must not contradict itself (a deadline that has passed, then an offer "
        "to go ahead anyway). Asking again for something the customer already gave fails.\n6. Cannot answer:").replace(
        "Write the five checks briefly.", "Write the six checks briefly.").replace(
        "(check 5), or by a needed hand-off", "(check 6), or by a needed hand-off").replace(
        "PASS (check 5): it searched", "PASS (check 6): it searched").replace(
        "Otherwise FAIL. Tone does not matter.", "Any failed listening check (check 5) is a FAIL. Otherwise FAIL. "
        "Tone does not matter."),
}

# v5: v3 with the date facts worked out by code (evals/judge_units.date_facts) added to the evidence. On the
# held-out half v3 read a parcel 14 days past its estimate, last scanned 9 days ago, as "recently scanned, not
# lost": the model does not count days reliably, and counting days is code's job.
_DATES = """\

DATE FACTS (worked out by code from the evidence above; they are correct, use them for anything about how long \
ago, how late or how soon):
{dates}"""
PROMPTS["v5"] = {k: v.replace("\n\nEARLIER IN THE CHAT:", _DATES + "\n\nEARLIER IN THE CHAT:", 1)
                 for k, v in PROMPTS["v3"].items()}


GEMINI_JUDGE = "gemini-4-hydrogen"


def client(judge: str = "gpt-oss"):
    if judge == "gemini":
        env_from_dotenv("VERTEX_API_KEY", "VERTEX_PROJECT")
        from google import genai
        return genai.Client(vertexai=True, api_key=os.environ["VERTEX_API_KEY"], project=os.environ["VERTEX_PROJECT"],
                            location="global")
    env_from_dotenv("TEACHER_API_KEY", "JUDGE_URL")
    return OpenAI(base_url=os.environ["JUDGE_URL"].rstrip("/") + "/v1", api_key=os.environ["TEACHER_API_KEY"],
                  timeout=300, max_retries=3)


def ask_gemini(c, prompt: str) -> dict:
    """One verdict from Gemini. Its thinking is not returned in full, only counted; the answer text is kept."""
    from google.genai import errors, types
    t0 = time.perf_counter()
    m, text, u = None, "", None
    for attempt in range(5):
        try:
            r = c.models.generate_content(model=GEMINI_JUDGE, contents=prompt,
                                          config=types.GenerateContentConfig(temperature=0, max_output_tokens=8192))
        except errors.APIError as e:
            if getattr(e, "code", None) in (429, 500, 503) and attempt < 4:
                time.sleep(10 * (attempt + 1))
                continue
            raise
        text, u = r.text or "", r.usage_metadata
        if m := VERDICT.findall(text):
            break
    return {"verdict": m[-1].upper() if m else None, "text": text, "reasoning": None,
            "prompt_tokens": u.prompt_token_count if u else None,
            "completion_tokens": ((u.candidates_token_count or 0) + (u.thoughts_token_count or 0)) if u else None,
            "seconds": round(time.perf_counter() - t0, 1)}


def render(prompt: str, unit) -> str:
    return prompt.format(evidence=evidence_text(unit), dates=date_facts(unit), history=history_text(unit),
                         customer=unit.customer, reply=unit.reply)


def ask(c: OpenAI, prompt: str, effort: str) -> dict:
    """One verdict. The reasoning stays in the record so disagreements can be read."""
    t0 = time.perf_counter()
    for attempt in range(3):
        r = c.chat.completions.create(model="judge", messages=[{"role": "user", "content": prompt}], temperature=0,
                                      max_tokens=4096, extra_body={"reasoning_effort": effort})
        text = r.choices[0].message.content or ""
        if m := VERDICT.findall(text):
            break
    reasoning = getattr(r.choices[0].message, "reasoning_content", None) or getattr(r.choices[0].message, "reasoning", None)
    return {"verdict": m[-1].upper() if m else None, "text": text, "reasoning": reasoning,
            "prompt_tokens": r.usage.prompt_tokens if r.usage else None,
            "completion_tokens": r.usage.completion_tokens if r.usage else None,
            "seconds": round(time.perf_counter() - t0, 1)}


def judge_units(units: list, version: str, effort: str, workers: int, judge: str = "gpt-oss") -> list[dict]:
    c = client(judge)
    jobs = [(u, k) for u in units for k in CRITERIA]

    def one(job):
        u, k = job
        prompt = render(PROMPTS[version][k], u)
        return {"id": u.id, "criterion": k, **(ask_gemini(c, prompt) if judge == "gemini" else ask(c, prompt, effort))}
    with ThreadPoolExecutor(workers) as pool:
        return list(pool.map(one, jobs))


def agreement(human: list[bool], judge: list[bool]) -> dict:
    tp = sum(h and j for h, j in zip(human, judge))
    tn = sum(not h and not j for h, j in zip(human, judge))
    pos, neg = sum(human), len(human) - sum(human)
    return {"TPR": tp / pos if pos else None, "TNR": tn / neg if neg else None, "n": len(human),
            "pos": pos, "neg": neg, "accuracy": (tp + tn) / len(human)}


def agree(a) -> None:
    labels = [r for r in load_labels() if a.split == "all" or r["split"] == a.split]
    units = [get_unit(r["id"]) for r in labels]
    out = judge_units(units, a.prompt, a.effort, a.workers, a.judge)
    name = f"{a.prompt}-{a.split}" if a.judge == "gpt-oss" else f"{a.judge}-{a.prompt}-{a.split}"
    path = OUT / "agreement" / f"{name}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out))
    by = {(x["id"], x["criterion"]): x for x in out}
    model = GEMINI_JUDGE if a.judge == "gemini" else f"{JUDGE_MODEL}, effort {a.effort}"
    print(f"prompt {a.prompt}, {a.split} ({len(labels)} replies), judge {model}")
    report_agreement(labels, by)


def report_agreement(labels: list[dict], by: dict) -> None:
    for k in CRITERIA:
        human = [r[k] == "PASS" for r in labels]
        judge = [by[(r["id"], k)]["verdict"] == "PASS" for r in labels]
        ag = agreement(human, judge)
        print(f"  {k}: TPR {ag['TPR']:.2f} ({ag['pos']} labelled PASS), TNR {ag['TNR']:.2f} ({ag['neg']} labelled FAIL), "
              f"accuracy {ag['accuracy']:.2f}")
        for r in labels:
            j = by[(r["id"], k)]["verdict"]
            if (j == "PASS") != (r[k] == "PASS"):
                print(f"    disagree {r['id']}: label {r[k]}, judge {j}")


def run(a) -> None:
    for run_name in a.runs:
        units = list(load_units(run_name).values())
        path = ROOT / "evals" / "runs" / run_name / f"judge-{a.prompt}.jsonl"
        done = {(x["id"], x["criterion"]) for x in map(json.loads, path.read_text().splitlines())} if path.exists() else set()
        todo = [u for u in units if any((u.id, k) not in done for k in CRITERIA)]
        print(f"{run_name}: {len(units)} replies, {len(todo)} to judge", flush=True)
        out = judge_units(todo, a.prompt, a.effort, a.workers)
        with path.open("a") as f:
            for x in out:
                if (x["id"], x["criterion"]) not in done:
                    f.write(json.dumps({**x, "judge": JUDGE_MODEL, "prompt": a.prompt, "effort": a.effort},
                                       ensure_ascii=False) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("agree")
    g.add_argument("--split", choices=["tune", "test", "fresh", "all"], required=True)
    g.add_argument("--judge", choices=["gpt-oss", "gemini"], default="gpt-oss")
    r = sub.add_parser("run")
    r.add_argument("runs", nargs="+")
    for p in (g, r):
        p.add_argument("--prompt", choices=list(PROMPTS), required=True)
        p.add_argument("--effort", choices=["low", "medium", "high"], default="medium")
        p.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    agree(a) if a.cmd == "agree" else run(a)


if __name__ == "__main__":
    main()
