"""Filters for generated conversations: every check runs on every conversation, and only what passes all of them
is kept for training.

A strong teacher is still wrong sometimes, and the student copies its mistakes as faithfully as its strengths.
Because the store's world is ours, most of what the teacher did can be checked by code, exactly and for free.
Each check is a function that returns the reason a conversation fails, or None. An LLM judge (synth/judge.py)
covers only what code cannot: tone, and whether the customer's request was actually resolved.

    uv run python -m synth.verify data/synthetic/raw/pilot-200.jsonl --report notes/trajectory-filters/pilot.md

Kept conversations and rejects (with their reasons) are written next to the run, under data/synthetic/.
"""

import argparse
import difflib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from agent.grounding import CITE, grounding_issues, retrieved_ids, tool_contents_before
from agent.loop import FALLBACK_REPLY, TOOL_MARKUP
from agent.tools_v2 import MODELS
from synth.style import CLOSING_OFFER, PROCESS_WORDS, TEAMMATE, time_promise

ORDER_ID = re.compile(r"\b(1[0-9]{4})\b")                 # seeded order numbers: 10001-13000
TRACKING = re.compile(r"\b([A-Z]{2}7\d{7})\b")            # carrier prefix + 7 + seven digits
STATUS_WORDS = re.compile(r"\b(shipped|delivered|in transit|out for delivery|tracking|eta|estimated|scan|"
                          r"refund(ed)?|cancel(l)?ed|return(ed)?|picked up|pickup|placed|packed|total|paid)\b", re.I)
PERSON_ASK = re.compile(r"\b(person|human|agent|someone|somebody|teammate|representative|manager|supervisor|"
                        r"escalat\w*|real (person|people)|staff|connect me|contact(ing)? (someone|somebody|support)|"
                        r"talk to|speak to|call me)\b", re.I)
PROMISED_HANDOFF = re.compile(r"\b(a |the |our )?(teammate|support team|team member|agent)s? will "
                              r"(contact|reach out|get back|reply|call|be in touch)|\bi(?:'ll| will)( now)? (connect|transfer|hand) you\b|please wait while i (arrange|connect)",
                              re.I)
TICKET_NO = re.compile(r"\bticket\s*(?:number|no\.?|id)?\s*(?:is\s*)?#?\s*(\d{5,})", re.I)
CLAIMED_HANDOFF = re.compile(r"\b(i(?:'ve| have) (escalated|handed|connected|passed)|has been escalated|"
                             r"your ticket (number|id) is)\b", re.I)
HANDOFF_OFFER = re.compile(r"(connect you|escalat\w+|hand (this|it|you) (over|to)|pass (this|it) to|teammate)", re.I)
RETURN_DONE = re.compile(
    r"\b(return(?! proposal)|refund request)\b[^.?!]{0,70}\b(is|has been|was)\s+(now\s+)?(done|complete|completed|processed|"
    r"confirmed|booked|created|initiated|submitted|approved|scheduled|all set|sorted)\b"
    r"|\bi(?:'ve| have)\s+(processed|initiated|confirmed|booked|approved|submitted)\s+(your|the)\s+return", re.I)
CONFIRM_CARD = re.compile(r"\b(press|click|tap|select)\w*\s+(the\s+)?[\"']?confirm|card that appears", re.I)
CANCEL_DONE = re.compile(r"\b(i(?:'ve| have)\s+cancel+ed|(order|it)\s+(is|has been)\s+(now\s+)?cancel+ed|"
                         r"cancel+ation (is|has been) (done|confirmed|processed))", re.I)
PHONE = re.compile(r"(\+91[\s-]?)?\b[6-9]\d{9}\b")
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")
INSTRUCTION_LEAK = re.compile(r"(list_my_orders|get_order_status|get_tracking|search_help_center|propose_return|"
                              r"escalate_to_human|Exemplary behaviour|Conversation state \(from|Rules:\s*-)")
DAYS_AGO = re.compile(r"\b\d+\s+(business\s+)?days?\s+(ago|since|have passed|has passed)\b|"
                      r"\b(it has|it's|it has only|it's only) been (only )?\d+ (business )?days\b", re.I)
DAY_COUNT = re.compile(r"\b(\d+)\s*(?:-\s*\d+\s*)?(?:business\s+)?days?\b", re.I)
MONTHS = {m: i for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                      "september", "october", "november", "december"], 1)}
NAMED_DATE = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(" + "|".join(MONTHS) + r")(?:,?\s+(\d{4}))?|"
                        r"\b(" + "|".join(MONTHS) + r")\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(\d{4}))?", re.I)


def dates_in(text: str) -> list[str]:
    """Every date in a reply as YYYY-MM-DD (ISO dates as written; '21 November' and 'November 21st' converted,
    year 2026 when none is given)."""
    out = re.findall(r"\b2026-\d{2}-\d{2}\b", text)
    for m in NAMED_DATE.finditer(text):
        day, month, year = (m.group(1), m.group(2), m.group(3)) if m.group(1) else (m.group(5), m.group(4), m.group(6))
        out.append(f"{year or 2026}-{MONTHS[month.lower()]:02d}-{int(day):02d}")
    return out


PROMISE = re.compile(r"\bi(?:'ll| will) (ensure|make sure|keep an eye|follow up|monitor|notify you|update you|"
                     r"let you know|check back|get back to you)\b", re.I)
SEND_BACK = re.compile(r"\b(send|ship|post|mail|courier) (it|them|the \w+( \w+)?) back\b|\breturn shipping\b|"
                       r"\binstructions on how to (send|ship|return)", re.I)
MAX_WORDS = 80
EASY = {"delivered_on_time", "in_transit", "delayed", "split_shipment", "policy_question"}
LATE = {"delayed", "split_shipment", "in_transit"}
NO_CANCEL_TOOL = {"not_yet_shipped", "ship_then_cancel_request"}


# Reading a conversation ---------------------------------------------------------------------------------------

def replies(conv: dict) -> list[tuple[int, str]]:
    """(index in messages, text) of every reply Nova showed the customer."""
    return [(i, m["content"]) for i, m in enumerate(conv["messages"])
            if m["role"] == "assistant" and m.get("content") and not m.get("tool_calls")]


def calls(conv: dict) -> list[dict]:
    """Every tool call with its parsed arguments and result, in order."""
    out = []
    for t in conv["traces"]:
        for c in t["tool_calls"]:
            try:
                args = json.loads(c["args"]) if isinstance(c["args"], str) else c["args"]
            except (json.JSONDecodeError, TypeError):
                args = None
            out.append({**c, "parsed_args": args})
    return out


def sentences(text: str) -> list[str]:
    return [x for x in re.split(r"(?<=[.!?])\s+", text) if x]


def calls_before(conv: dict, end: int) -> list[dict]:
    """Successful tool calls made before messages[end], read from the messages themselves."""
    msgs, out = conv["messages"][:end], []
    results = {m["tool_call_id"]: m["content"] for m in msgs if m["role"] == "tool"}
    for m in msgs:
        for t in m.get("tool_calls") or []:
            content = results.get(t["id"], "")
            if content and '"error"' not in content[:20]:
                out.append({"name": t["function"]["name"], "result": content})
    return out


def customer_text(conv: dict, end: int | None = None) -> str:
    return "\n".join(m["content"] for m in conv["messages"][:end] if m["role"] == "user")


# The checks ---------------------------------------------------------------------------------------------------

VERIFIERS: dict = {}


def verifier(fn):
    VERIFIERS[fn.__name__] = fn
    return fn


@verifier
def schema(conv) -> str | None:
    """Every tool call is a known tool with arguments its model accepts; no raw call markup reaches a reply."""
    for c in calls(conv):
        if c["name"] not in MODELS:
            return f"unknown tool {c['name']}"
        if c["parsed_args"] is None:
            return f"{c['name']} arguments are not JSON"
        try:
            MODELS[c["name"]].model_validate(c["parsed_args"])
        except Exception as e:                                     # pydantic ValidationError
            return f"{c['name']} arguments rejected: {str(e).splitlines()[0][:80]}"
    if any(t["format_errors"] for t in conv["traces"]):
        return "a model call was a format error"
    if any(mark in text for _, text in replies(conv) for mark in TOOL_MARKUP):
        return "tool-call markup in a reply"
    return None


@verifier
def tool_before_fact(conv) -> str | None:
    """Order numbers and tracking numbers in a reply come from a tool result shown before it. A number the
    customer typed may be repeated only in a reply that states nothing about it (a refusal)."""
    msgs = conv["messages"]
    for i, text in replies(conv):
        seen = "\n".join(tool_contents_before(msgs, i))
        for ident in ORDER_ID.findall(text) + TRACKING.findall(text):
            if ident in seen:
                continue
            said = next(x for x in sentences(text) if ident in x)
            if ident in customer_text(conv, i) and not STATUS_WORDS.search(said):
                continue                                           # repeated in a refusal, nothing stated about it
            return f"{ident} stated before any tool result showed it"
    return None


@verifier
def grounded_numbers(conv) -> str | None:
    """Every other number in a reply is in the tool and help-center results before it (agent/grounding.py)."""
    msgs = conv["messages"]
    for i, text in replies(conv):
        bare = ORDER_ID.sub(" ", TRACKING.sub(" ", text))            # identifiers are tool_before_fact's job
        # Today's date is in the system prompt: "it is 20 November" is grounded, "within 7 days" is not.
        sources = tool_contents_before(msgs, i) + [msgs[0]["content"]]
        issues = [x for x in grounding_issues(bare, sources) if x.startswith("number")]
        if issues:
            return f"{issues[0]}: \"{text[:70]}\""
        # Numbers are matched one at a time, so "7 days" passed whenever a time like 07:14 was in a result. Day
        # counts and dates are checked whole: "N days" must be written in a source, and a date must be one.
        source_text = "\n".join(sources).replace("–", "-").replace("\\n", " ")   # JSON keeps line breaks as \\n
        source_text += " " + " ".join(dates_in(source_text))                           # "20 November 2026" too
        if m := DAYS_AGO.search(text):
            return f"counts days itself: \"{m.group(0)}\""
        for m in DAY_COUNT.finditer(text.replace("–", "-")):
            if not re.search(rf"\b{re.escape(m.group(1))}\s*(-\s*\d+\s*)?(business\s+)?days?\b", source_text) and \
                    not re.search(rf"\d+\s*-\s*{re.escape(m.group(1))}\s*(business\s+)?days?\b", source_text):
                return f"\"{m.group(0)}\" is not in any tool or help-center result"
        for d in dates_in(text):
            if d not in source_text:
                return f"date {d} is not in any tool result (worked out, not looked up)"
    return None


@verifier
def citations(conv) -> str | None:
    """Every [kb:...] cited was returned by a help-center search earlier in the conversation."""
    msgs = conv["messages"]
    for i, text in replies(conv):
        known = retrieved_ids(tool_contents_before(msgs, i))
        bad = [c for c in CITE.findall(text) if c not in known]
        if bad:
            return f"cites {bad[0]}, not retrieved"
        if m := re.search(r"\[(?!kb:)[a-z]+:[^\]]*\]", text):
            return f"a citation that is not a help-center id: {m.group(0)}"
    return None


@verifier
def end_state(conv) -> str | None:
    """Returns and cancellations end where the store's rules say: an eligible item gets a proposal, an
    ineligible one does not, and no reply claims a return or (where Nova cannot cancel) a cancellation is done."""
    sc = conv["meta"]["scenario"]
    # A return that existed before the chat (in progress, refunded, rejected) is a fact Nova reads from a tool;
    # only a return Nova proposed in this chat must not be called done.
    had_return = bool(conv["meta"]["facts"].get("returns"))
    proposed = [c for c in calls(conv) if c["name"] == "propose_return" and c["ok"]]
    eligible = [c for c in proposed if c["result"].get("eligible")]
    if sc == "return_eligible" and not eligible:
        return "eligible return but no proposal"
    if sc in {"window_just_expired", "opened_electronics"} and eligible:
        return f"proposal for an ineligible item (reason {eligible[0]['parsed_args'].get('reason')})"
    for i, text in replies(conv):
        proposed_before = any('"eligible": true' in c["result"] for c in calls_before(conv, i)
                              if c["name"] == "propose_return")
        if CONFIRM_CARD.search(text) and not proposed_before:
            return "tells the customer to press Confirm before any eligible proposal"
        if RETURN_DONE.search(text) and not had_return:
            return f"claims the return is done: \"{RETURN_DONE.search(text).group(0)}\""
        if sc in NO_CANCEL_TOOL and CANCEL_DONE.search(text):
            return f"claims a cancellation Nova cannot make: \"{CANCEL_DONE.search(text).group(0)}\""
    return None


@verifier
def escalation(conv) -> str | None:
    """A lost parcel is handed off; an easy scenario is not, unless the customer asked for a person; a late
    parcel is not offered a hand-off before the customer asks."""
    sc, msgs = conv["meta"]["scenario"], conv["messages"]
    tickets = [c for c in calls(conv) if c["name"] == "escalate_to_human" and c["ok"]]
    if sc == "lost" and not tickets:
        return "lost parcel never handed off"
    if sc in EASY and tickets:
        first = next(i for i, m in enumerate(msgs) if m.get("tool_calls") and
                     any(t["function"]["name"] == "escalate_to_human" for t in m["tool_calls"]))
        if not PERSON_ASK.search(customer_text(conv, first)):
            return "handed off an easy case nobody asked to hand off"
    for i, text in replies(conv):
        before = [c for c in calls_before(conv, i) if c["name"] == "escalate_to_human"]
        if CLAIMED_HANDOFF.search(text) and not before:
            return f"claims a hand-off that never happened: \"{CLAIMED_HANDOFF.search(text).group(0)}\""
        if (m := PROMISED_HANDOFF.search(text)) and not before:
            said = next(x for x in sentences(text) if m.group(0) in x)
            if not re.match(r"\s*(if|once|should|in case)\b", said, re.I):      # a conditional is not a promise
                return f"promises a teammate without handing off: \"{m.group(0)}\""
        tickets = "".join(c["result"] for c in before)
        for t in TICKET_NO.findall(text):
            if t not in tickets:
                return f"ticket {t} did not come from a hand-off"
    if sc in LATE:
        for i, text in replies(conv):
            if HANDOFF_OFFER.search(text) and not PERSON_ASK.search(customer_text(conv, i)):
                return "offered a hand-off for a parcel that is only late"
    return None


@verifier
def call_limit(conv) -> str | None:
    """No turn ran out of model calls and fell back to the fixed hand-off reply (no ticket, no facts)."""
    for t in conv["traces"]:
        if t.get("reply") == FALLBACK_REPLY or (t["escalated"] and not any(c["name"] == "escalate_to_human"
                                                                          for c in t["tool_calls"])):
            return "a turn ended in the fallback hand-off"
    if any(text == FALLBACK_REPLY for _, text in replies(conv)):
        return "a turn ended in the fallback hand-off"
    return None


@verifier
def privacy(conv) -> str | None:
    """No phone number, email address or another customer's order facts in a reply, and nothing of Nova's
    own instructions or tool names."""
    other = str(conv["meta"]["facts"].get("other_order", "")) or None
    for _, text in replies(conv):
        if PHONE.search(text) or EMAIL.search(text):
            return "a phone number or email address in a reply"
        if other and any(other in x and STATUS_WORDS.search(x) for x in sentences(text)):
            return f"talks about another customer's order {other}"
        if INSTRUCTION_LEAK.search(text):
            return f"reveals its instructions or tools: \"{INSTRUCTION_LEAK.search(text).group(0)}\""
    return None


@verifier
def right_order(conv) -> str | None:
    """When the customer has named an item of the scenario's order (or its number), the first order lookup is
    that order, not another one the customer then has to correct."""
    facts = conv["meta"]["facts"]
    oid = conv["meta"].get("order_id")
    if not oid:
        return None
    lookups = [c for c in calls(conv) if c["name"] in ("get_order_status", "get_tracking", "propose_return")
               and isinstance(c["parsed_args"], dict) and "order_id" in c["parsed_args"]]
    if not lookups or lookups[0]["parsed_args"]["order_id"] == oid:
        return None
    first = next(m["content"].lower() for m in conv["messages"] if m["role"] == "user")
    named = str(oid) in first or any(item.lower() in first for item in facts.get("items", []))
    other = lookups[0]["parsed_args"]["order_id"]
    if named and other != facts.get("other_order"):
        return f"looked up order {other} first; the customer meant {oid}"
    return None


REQUEST = re.compile(r"\?|\b(pls|please|plz|can you|could you|connect\w*|check|where|when|why|how|what|but)\b", re.I)
CLOSING = re.compile(r"^\W*(ok(ay)?|cool|great|perfect|nice|thanks?|thank you|thx|ty|cheers|bye|goodbye|got it|"
                     r"alright|fine)\b[\w\s,!.']{0,40}$", re.I)


@verifier
def needless_tool(conv) -> str | None:
    """No tool call where none is needed: in a chat built for that (greetings, "are you a bot?", out of scope),
    or in answer to a customer's plain thanks or goodbye."""
    if conv["meta"]["scenario"] == "no_tool" and calls(conv):
        return f"called {calls(conv)[0]['name']} where no tool was needed"
    msgs = conv["messages"]
    for i, m in enumerate(msgs):
        text = (m.get("content") or "").strip()
        if (m["role"] == "user" and CLOSING.match(text) and not PERSON_ASK.search(text)
                and not REQUEST.search(text)):
            nxt = next((x for x in msgs[i + 1:] if x["role"] in ("assistant", "user")), None)
            if nxt and nxt["role"] == "assistant" and nxt.get("tool_calls"):
                return f"called a tool to answer \"{m['content'][:40]}\""
    return None


@verifier
def length(conv) -> str | None:
    """No reply over 80 words or written as a list."""
    for _, text in replies(conv):
        if (n := len(text.split())) > MAX_WORDS:
            return f"a reply of {n} words"
        if re.search(r"^\s*([-*•]|\d+\.)\s", text, re.M):
            return "a reply written as a list"
    return None


@verifier
def style(conv) -> str | None:
    """No closing offer of more help, no several paragraphs, no promise of emails, labels or links nobody
    mentioned (the same rules the generator asks the teacher to fix, synth/style.py)."""
    sources = "\n".join(m["content"] for m in conv["messages"] if m["role"] == "tool").lower()
    for _, text in replies(conv):
        if (m := CLOSING_OFFER.search(text)) and not TEAMMATE.search(m.group(0)):
            return f"ends with an offer: \"{m.group(0)[-50:]}\""
        if "\n" in text.strip():
            return "a reply with several paragraphs"
        if m := PROMISE.search(text):
            return f"promises what Nova cannot do: \"{m.group(0)}\""
        if m := time_promise(text):
            return f"says when a teammate will reply: \"{m[-60:]}\""
        if (m := SEND_BACK.search(text)) and "send" not in sources:
            return f"tells the customer to ship the item back (NimbusCart picks up): \"{m.group(0)}\""
        low = text.lower()
        made_up = [w for w in PROCESS_WORDS if re.search(rf"\b{w}s?\b", low) and not re.search(rf"\b{w}", sources)]
        if made_up:
            return f"mentions {made_up[0]}, which no tool or help-center result mentioned"
    return None


@verifier
def judge_tone(conv) -> str | None:
    """The LLM judge's verdict (synth/judge.py), attached to the conversation before checking; unjudged passes
    here and is counted separately in the report."""
    j = conv.get("judge")
    return None if not j or j.get("pass") else f"judge: {j.get('why', 'failed')}"


@verifier
def judge_facts(conv) -> str | None:
    """The fact-check judge's verdict (synth/judge.py --rubric facts): every reply read against the lookup results
    it was given. Unjudged passes here and is counted separately in the report."""
    j = conv.get("fact_judge")
    return None if not j or j.get("pass") else f"fact judge: {j.get('why', 'failed')}"


def dedup_key(conv) -> tuple:
    return conv["meta"]["scenario"], tuple(c["name"] for c in calls(conv))


def first_message(conv) -> str:
    return re.sub(r"\W+", " ", next(m["content"] for m in conv["messages"] if m["role"] == "user").lower()).strip()


def check(conv: dict) -> list[str]:
    """Every failed check as 'name: why'. dedup runs separately, across the kept set (filter_run)."""
    return [f"{name}: {why}" for name, fn in VERIFIERS.items() if (why := fn(conv))]


def filter_run(convs: list[dict]) -> tuple[list[dict], list[dict]]:
    """(kept, rejected). Each rejected conversation carries "rejected": [reasons]. The dedup check: same
    scenario, same sequence of tool calls and a near-identical first customer message as a conversation
    already kept."""
    kept, rejected, seen = [], [], defaultdict(list)
    for c in convs:
        reasons = check(c)
        if not reasons:
            key, opening = dedup_key(c), first_message(c)
            twin = next((k for k in seen[key] if difflib.SequenceMatcher(None, k, opening).ratio() > 0.9), None)
            if twin is not None:
                reasons = [f"dedup: same scenario, tools and opening as a kept conversation"]
        if reasons:
            rejected.append({**c, "rejected": reasons})
        else:
            seen[dedup_key(c)].append(first_message(c))
            kept.append(c)
    return kept, rejected


# The keep-rate report ------------------------------------------------------------------------------------------

def report(name: str, kept: list[dict], rejected: list[dict]) -> str:
    total = len(kept) + len(rejected)
    by = lambda key: (Counter(c["meta"][key] for c in kept), Counter(c["meta"][key] for c in kept + rejected))
    fails = Counter(r.split(":")[0] for c in rejected for r in c["rejected"])
    only = Counter(c["rejected"][0].split(":")[0] for c in rejected if len(c["rejected"]) == 1)
    judged = sum(1 for c in kept + rejected if c.get("judge"))
    fact_judged = sum(1 for c in kept + rejected if c.get("fact_judge"))
    lines = [f"# Keep rate: {name}", "",
             f"**{len(kept)} of {total} kept ({len(kept) / max(total, 1):.0%}).** "
             f"{judged} of {total} were judged for tone and {fact_judged} for facts; unjudged ones passed those "
             "checks by default.", "",
             "## Per check", "",
             "A conversation can fail several checks. \"Only\" counts conversations this check alone rejected: "
             "fixing its cause would keep them.", "",
             "| Check | Rejects | Only this check | What it catches |", "|---|---|---|---|"]
    for v, fn in list(VERIFIERS.items()) + [("dedup", None)]:
        doc = " ".join(((fn.__doc__ or "").split(". ")[0] if fn else
                         "Same scenario, same tool calls and a near-identical opening as a kept conversation").split())
        lines.append(f"| {v} | {fails[v]} | {only[v]} | {doc} |")
    for key, title in (("scenario", "Per scenario"), ("persona", "Per persona")):
        k, t = by(key)
        lines += ["", f"## {title}", "", f"| {key.title()} | Kept | Total | Keep rate | Top reason |",
                  "|---|---|---|---|---|"]
        for v in sorted(t, key=lambda v: k[v] / t[v]):
            top = Counter(r.split(":")[0] for c in rejected if c["meta"][key] == v for r in c["rejected"])
            lines.append(f"| {v} | {k[v]} | {t[v]} | {k[v] / t[v]:.0%} | "
                         f"{', '.join(f'{r} {n}' for r, n in top.most_common(2)) or '-'} |")
    cells_k = Counter((c["meta"]["scenario"], c["meta"]["persona"]) for c in kept)
    cells_t = Counter((c["meta"]["scenario"], c["meta"]["persona"]) for c in kept + rejected)
    worst = sorted((c for c in cells_t if cells_t[c] >= 2), key=lambda c: (cells_k[c] / cells_t[c], -cells_t[c]))[:8]
    lines += ["", "## Worst cells (scenario x persona, at least 2 conversations)", "",
              "| Scenario | Persona | Kept | Total | Reasons |", "|---|---|---|---|---|"]
    for s, p in worst:
        why = Counter(r.split(":")[0] for c in rejected if (c["meta"]["scenario"], c["meta"]["persona"]) == (s, p)
                      for r in c["rejected"])
        lines.append(f"| {s} | {p} | {cells_k[(s, p)]} | {cells_t[(s, p)]} | "
                     f"{', '.join(f'{r} {n}' for r, n in why.most_common(3))} |")
    empty = sorted({c for c in cells_t if not cells_k[c]})
    lines += ["", f"Cells with conversations but none kept: {len(empty)} of {len(cells_t)}."]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+", type=Path)
    ap.add_argument("--report", type=Path, help="write the keep-rate report here (markdown)")
    ap.add_argument("--judgements", type=Path, nargs="*", default=[],
                    help="tone verdicts (synth/judge.py) to attach before checking")
    ap.add_argument("--facts", type=Path, nargs="*", default=[],
                    help="fact-check verdicts (synth/judge.py --rubric facts) to attach before checking")
    ap.add_argument("--save", action="store_true", help="write <run>.kept.jsonl and <run>.rejected.jsonl")
    a = ap.parse_args()
    convs = [json.loads(line) for p in a.runs for line in p.read_text().splitlines() if line.strip()]
    for key, files in (("judge", a.judgements), ("fact_judge", a.facts)):
        verdicts = {j["id"]: j for f in files for j in map(json.loads, f.read_text().splitlines())}
        for c in convs:
            if c["id"] in verdicts:
                c[key] = verdicts[c["id"]]
    kept, rejected = filter_run(convs)
    name = " + ".join(p.stem for p in a.runs)
    print(f"{len(kept)} kept, {len(rejected)} rejected of {len(convs)}")
    if a.report:
        a.report.parent.mkdir(parents=True, exist_ok=True)
        a.report.write_text(report(name, kept, rejected))
        print("wrote", a.report)
    if a.save:
        base = a.runs[0].with_suffix("")
        for suffix, rows in ((".kept.jsonl", kept), (".rejected.jsonl", rejected)):
            Path(f"{base}{suffix}").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
        print("saved", f"{base}.kept.jsonl", f"{base}.rejected.jsonl")


if __name__ == "__main__":
    main()
