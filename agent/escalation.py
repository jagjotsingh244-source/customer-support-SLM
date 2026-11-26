"""When Nova must hand off, decided in code; the ticket summary, built from the conversation state; support hours.

Escalation is split by how certain the trigger is. The certain ones live here and fire every time:

    trigger                                   reason              ticket reason
    the customer asks for a person            asked_for_person    other
    a payment dispute, fraud, a legal threat  high_risk:<topic>   payment_issue / other / damaged
      or a safety problem
    a parcel with no scan for 7+ days         possible_lost       lost_parcel
    two turns in a row without progress       no_progress         other

Judgement calls (clear frustration, a question the help center does not cover) stay with the trained model.
Escalating on every negative word is its own failure: an angry customer is usually best served by a fast,
correct answer.

"Progress" is concrete: a successful tool result the conversation has not had before (a new fact), or a return
proposal. A turn that only says thanks or ok is not counted either way.

When a rule fires, the loop opens the ticket itself with ticket_summary(), so the teammate gets the order ids,
what was checked and what the customer wants, whatever the model would have written, and asks the model only to
tell the customer what happens next (handoff_note(), which knows the support hours: 9:00 to 21:00 IST, every
day, help center "Contacting a human").
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta

from config import IST

OPENS, CLOSES = time(9, 0), time(21, 0)       # support hours, IST, every day; open from 9:00 until 21:00
LOST_AFTER_DAYS = 7                            # no scan for this long: a possible loss (help center, delays)
NO_PROGRESS_TURNS = 2

# Asking for a person is a request, not a mention: "your customer service is a joke" and "my manager asked me"
# are not asks. A strong noun (a human, a representative, customer care) needs a request word in the same
# sentence; a weak one (a person, someone, an agent) needs a verb of talking to or being put through to.
_STRONG = (r"(human|real person|actual person|live person|real human|live agent|representative|supervisor|manager|"
           r"customer (care|service|support)|someone real)")
_WEAK = r"(a person|someone|somebody|an agent|an executive|the team|the support team|a teammate|your team|support)"
HUMAN_REQUEST = [
    re.compile(r"\b(want|need|let me|can i|could i|may i|i'?d like|connect|transfer|get me|put me|give me|talk|speak|"
               r"chat|reach|contact|escalate|number|is there|where is)\b[^.!?\n]{0,40}\b" + _STRONG + r"\b", re.I),
    re.compile(_STRONG + r"\b[^.!?\n]{0,20}\b(number|phone|contact|please|now|asap)\b", re.I),
    re.compile(r"\b(talk|speak|chat|connect|transfer|put me through)\b[^.!?\n]{0,15}\b(to|with)\s+" + _WEAK + r"\b", re.I),
    re.compile(r"\b(call me( back)?|not (a|this) bot|no more bots?|stop the bot|(do ?n[o']?t|dont) want (to talk to )?a bot)\b",
               re.I),
]
NOT_HUMAN = re.compile(r"\b(delivery|courier) (agent|person|executive|guy|boy|team)\b", re.I)

HIGH_RISK = {   # topic: (pattern, ticket reason). Events and requests, not figures of speech: "a burning
                # question", "fire away", "this is a scam" said of a late parcel, "I don't dispute that".
    "payment_dispute": (re.compile(r"\b(charge-?back|(raise|file|open) a dispute|dispute (the|this|a|my) "
                                   r"(charge|payment|transaction|debit)|charged twice|double charged|debited twice|"
                                   r"deducted twice|unauthori[sz]ed (charge|payment|transaction|debit))\b", re.I),
                        "payment_issue"),
    "fraud": (re.compile(r"\b(fraud(ulent)? (charge|transaction|order|payment|debit)|i did(n'?t| not) (place|make|order) "
                         r"(this|that|the|any)|someone (else )?(used|placed|ordered|logged into|got into)|"
                         r"(account|card) (was |got |has been )?hacked)\b", re.I), "payment_issue"),
    "legal": (re.compile(r"\b(consumer (court|forum)|legal (action|notice)|lawyer|advocate|sue (you|nimbuscart)|"
                         r"take (you|this) to court|police (complaint|case)|(file|lodge|register) an? fir)\b", re.I),
              "other"),
    "safety": (re.compile(r"\b(caught fire|on fire|burst into flames|smok(e|ing) (from|out of|coming)|sparks?(ed|ing)?\b"
                          r"|electric(al)? shock|shocked me|gave me a shock|explod\w*|melt(ed|ing)|"
                          r"burn(ed|t) (my|me|his|her|the|a hole)|got burn(ed|t)|injur\w*|cut (my|his|her) (hand|finger))",
                          re.I), "damaged"),
}
CLOSING = re.compile(r"^\W*(ok(ay)?|k|thanks?|thank you|thx|ty|got it|great|cool|fine|perfect|alright|bye|no|nope|"
                     r"that'?s all|that'?s it|nothing else|will wait|i'?ll wait|waiting|sure)"
                     r"(\W+(ok(ay)?|thanks?|thank you|so much|a lot|bye|great|nova|then|for now|waiting|i'?ll wait|"
                     r"will wait|perfect|cool))*\W*$", re.I)


# A customer who thanks or signs off is not stuck, whatever Nova said: "cool thx have a good day", "That answers
# my question". Used by the no-progress rule only.
SATISFIED = re.compile(r"\b(thanks?|thank you|thx|ty|appreciate|that (answers|helps|covers|is (exactly|what))|"
                       r"got it|perfect|great|bye|have a (good|nice)|will wait|i'?ll wait)\b", re.I)


def content(msg: str) -> bool:
    return bool(CLOSING.match(msg or "") or SATISFIED.search(msg or ""))


@dataclass(frozen=True)
class Escalation:
    reason: str            # asked_for_person, high_risk:<topic>, possible_lost, no_progress
    ticket_reason: str     # one of agent/tools_v2.py TICKET_REASONS


def asks_for_person(text: str) -> bool:
    text = NOT_HUMAN.sub("", text or "")
    return any(rule.search(text) for rule in HUMAN_REQUEST)


def high_risk(text: str) -> tuple[str, str] | None:
    for topic, (rule, reason) in HIGH_RISK.items():
        if rule.search(text or ""):
            return topic, reason
    return None


def _when(x) -> datetime | None:
    if isinstance(x, datetime):
        return x
    try:
        return datetime.fromisoformat(str(x))
    except (TypeError, ValueError):
        return None


def days_since_last_scan(result: dict, now: datetime) -> float | None:
    """For a get_tracking result: the longest a box still on its way has gone without a scan, in days."""
    gaps = []
    for b in result.get("shipments", []) if isinstance(result, dict) else []:
        if b.get("status") in ("in_transit", "out_for_delivery", "label_created") and (at := _when(b.get("last_scan_at"))):
            gaps.append((now - at).total_seconds() / 86400)
    return max(gaps) if gaps else None


def must_escalate(user_msg: str, turns_without_progress: int, results: list, now: datetime) -> Escalation | None:
    """The certain triggers, checked in order of certainty. `results` are this turn's tool results (dicts)."""
    if asks_for_person(user_msg):
        return Escalation("asked_for_person", "other")
    if hit := high_risk(user_msg):
        return Escalation(f"high_risk:{hit[0]}", hit[1])
    for r in results:
        if (d := days_since_last_scan(r, now)) is not None and d >= LOST_AFTER_DAYS:
            return Escalation("possible_lost", "lost_parcel")
    if turns_without_progress >= NO_PROGRESS_TURNS and not content(user_msg):
        return Escalation("no_progress", "other")
    return None


# Progress ---------------------------------------------------------------------------------------------

@dataclass
class Progress:
    """Counts the customer's turns in a row in which Nova got nowhere. Updated by the loop after every turn.

    A turn makes progress when a tool returns something the conversation has not had before, or a return is
    proposed. A turn without new facts is still fine when Nova answers from what it knows ("so when will it
    come?" answered from the tracking already found). It counts as *no* progress only when, on top of nothing
    new, Nova repeats an earlier reply, ends on the fallback, or every tool call failed: the customer is going
    round in circles. A closing message ("ok thanks") never counts.
    """
    seen: set = field(default_factory=set)
    replies: list = field(default_factory=list)
    turns_without_progress: int = 0

    def end_turn(self, user_msg: str, calls: list[dict], reply: str | None = None) -> int:
        """`calls` are this turn's tool calls as the trace keeps them ({"name", "result", "ok"}); `reply` is what
        Nova said."""
        new = False
        for c in calls:
            if not c.get("ok") or c["name"] == "escalate_to_human":
                continue
            key = hashlib.sha1((c["name"] + json.dumps(c["result"], sort_keys=True, default=str)).encode()).hexdigest()
            if key not in self.seen:
                self.seen.add(key)
                new = True
            if c["name"] == "propose_return" and isinstance(c["result"], dict) and c["result"].get("eligible"):
                new = True
        stuck = (reply is None or _repeats(reply, self.replies) or reply.startswith(FALLBACK)
                 or (calls and not any(c.get("ok") for c in calls)))
        if reply:
            self.replies.append(reply)
        if new:
            self.turns_without_progress = 0
        elif stuck and not content(user_msg):
            # A repeated reply means the customer asked twice and got the same answer: two turns going nowhere.
            # Counting only the repeat let a customer give up after three identical replies (sim-una-004).
            repeat = reply is not None and _repeats(reply, self.replies[:-1])
            self.turns_without_progress = max(self.turns_without_progress + 1, NO_PROGRESS_TURNS if repeat else 0)
        return self.turns_without_progress


FALLBACK = "Let me connect you with a teammate."       # agent/loop.py FALLBACK_REPLY


def _words(text: str) -> set:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _repeats(reply: str, earlier: list[str], overlap: float = 0.6) -> bool:
    """The reply says mostly what an earlier one said (word overlap, Jaccard >= 0.6)."""
    w = _words(reply)
    return any(w and (len(w & e) / len(w | e)) >= overlap for e in map(_words, earlier))


# Support hours ----------------------------------------------------------------------------------------

def support_open(now: datetime) -> bool:
    t = now.astimezone(IST).time()
    return OPENS <= t < CLOSES


def next_opening(now: datetime) -> datetime:
    local = now.astimezone(IST)
    day = local.date() if local.time() < OPENS else local.date() + timedelta(days=1)
    return datetime.combine(day, OPENS, tzinfo=IST)


def handoff_note(now: datetime, ticket_id: int) -> str:
    """What the model is told to say after a forced hand-off. Inside hours it promises no time; outside, it says
    when a person will reply, from the clock, never "shortly"."""
    if support_open(now):
        return (f"Ticket {ticket_id} is open and a teammate from the support team will reply here. "
                "Tell the customer that, without promising a time, and do not ask them to repeat anything.")
    opens = next_opening(now)
    day = "today" if opens.date() == now.astimezone(IST).date() else "tomorrow"
    return (f"Ticket {ticket_id} is open. The support team is offline now (hours are 9:00 to 21:00 IST). "
            f"Tell the customer a teammate will pick it up when support opens at 9:00 IST {day}, "
            "and that they do not need to repeat anything.")


# The ticket summary -----------------------------------------------------------------------------------

def _cut(text: str, limit: int) -> str:
    """At most `limit` characters, cut at a word boundary."""
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def ticket_summary(state, reason: Escalation, customer_msgs: list[str], tools_called: list[str],
                   limit: int = 500) -> str:
    """One paragraph for the teammate, from the conversation state, never from the model: why it was handed
    off, what the customer wants (their last message that is not a "thanks"), the order in focus first and the
    others after it, what was checked, an earlier ticket, any open proposal. `state` is an agent.state.State; the
    customer's words are redacted (agent/privacy.py)."""
    from agent.privacy import redact
    parts = [f"Handed off: {reason.reason.replace('_', ' ')}."]
    asks = [m for m in customer_msgs if m.strip() and not CLOSING.match(m)]
    if asks:
        parts.append(f'Customer: "{_cut(redact(" ".join(asks[-1].split())), 160)}"')
    orders = list(state.facts)
    if state.focus_order in orders:
        orders.remove(state.focus_order)
        orders.insert(0, state.focus_order)
    for oid in orders:
        facts = "; ".join(state.facts[oid].values())
        parts.append(f"{state.label(oid)}" + (f": {facts}." if facts else "."))
    if state.open_proposal:
        parts.append(f"Return proposed, not confirmed: {state.open_proposal}.")
    if state.handoff:
        parts.append(f"Earlier ticket: {state.handoff}.")
    checked = [t for t in dict.fromkeys(tools_called) if t != "escalate_to_human"]
    if checked:
        parts.append("Checked: " + ", ".join(checked) + ".")
    return _cut(" ".join(parts), limit)


# The rules as the agent loop uses them, for one conversation ------------------------------------------

class HandoffRules:
    """What agent/loop.py run_turn(rules=...) calls. One per conversation.

    at_turn_start(msg)    the customer's message: asked for a person, a high-risk topic, or no progress over the
                          turns before it -> an Escalation the loop acts on before the model runs
    after_tools(results)  this step's tool results: a parcel with no scan for 7+ days -> an Escalation
    tracking_to_check(r)  a shipped order seen only through its status -> the loop reads its tracking
    observe(...)          every tool call, so the state behind the ticket summary is current
    handoff_args(esc)     the escalate_to_human arguments for a forced hand-off, summary from the state
    rewrite(name, raw)    a hand-off the model asks for gets the same summary from the state; its reason is kept
    note(result)          the hand-off result the model reads, with what to tell the customer for the hour
    end_turn(msg, calls)  updates the no-progress counter
    Nothing fires twice: after one hand-off, the conversation is with the support team.
    """

    def __init__(self, now=None):
        from agent.state import State
        from config import now as clock
        self.now = now or clock
        self.state, self.progress = State(), Progress()
        self.customer_msgs: list[str] = []
        self.tools_called: list[str] = []
        self.handed_off = False
        self.ticket_id: int | None = None
        self.tracked: set[int] = set()              # orders whose tracking this conversation has seen

    def repeat_handoff(self, name: str) -> dict | None:
        """A second escalate_to_human in the same conversation opens no second ticket: the first one's result."""
        if name == "escalate_to_human" and self.handed_off:
            return {"handed_off": True, "ticket_id": self.ticket_id,
                    "note": "Already handed off on this ticket; no new ticket opened."}
        return None

    def at_turn_start(self, msg: str) -> Escalation | None:
        self.customer_msgs.append(msg or "")
        if self.handed_off:
            return None
        return must_escalate(msg, self.progress.turns_without_progress, [], self.now())

    def after_tools(self, results: list) -> Escalation | None:
        if self.handed_off:
            return None
        for r in results:
            if (d := days_since_last_scan(r, self.now())) is not None and d >= LOST_AFTER_DAYS:
                return Escalation("possible_lost", "lost_parcel")
        return None

    def tracking_to_check(self, results: list) -> int | None:
        """An order a status lookup shows still on its way, whose tracking nobody has looked at. The status
        result has no scan date, so the lost-parcel rule cannot see a stuck parcel from it: the loop then reads
        the tracking itself (esc-003 and adv-010 were missed this way)."""
        if self.handed_off:
            return None
        for r in results:
            if (isinstance(r, dict) and "items" in r and r.get("status") in ("shipped", "out_for_delivery")
                    and isinstance(r.get("order_id"), int) and r["order_id"] not in self.tracked):
                return r["order_id"]
        return None

    def observe(self, name: str, args: dict | None, result) -> None:
        self.tools_called.append(name)
        if name == "get_tracking" and isinstance(result, dict) and "error" not in result:
            self.tracked.add(result.get("order_id"))
        if isinstance(result, dict):
            self.state.update(name, args, result)
            if name == "escalate_to_human" and result.get("handed_off"):
                self.handed_off, self.ticket_id = True, result.get("ticket_id")

    def _summary(self, esc: Escalation) -> str:
        return ticket_summary(self.state, esc, self.customer_msgs, self.tools_called, limit=300)

    def handoff_args(self, esc: Escalation) -> dict:
        return {"reason": esc.ticket_reason, "summary": self._summary(esc)}

    def rewrite(self, name: str, raw: str | None) -> str | None:
        if name != "escalate_to_human":
            return raw
        try:
            args = json.loads(raw or "{}")
        except (json.JSONDecodeError, TypeError):
            args = {}
        reason = args.get("reason") if isinstance(args, dict) else None
        from agent.tools_v2 import TICKET_REASONS
        reason = reason if reason in TICKET_REASONS else "other"
        return json.dumps({"reason": reason, "summary": self._summary(Escalation("model_decision", reason))})

    def note(self, result):
        if isinstance(result, dict) and result.get("handed_off"):
            return {**result, "note": handoff_note(self.now(), result["ticket_id"]) + self._found()}
        return result

    def _found(self) -> str:
        """What the lookups showed about the order in focus, from the state, for the hand-off reply. Without it the
        reply after a forced hand-off said only "a teammate will reply" and dropped the last scan the customer
        needs to hear (esc-002, esc-003 and esc-005 failed on it in every served run)."""
        oid = self.state.focus_order
        facts = self.state.facts.get(oid, {}) if oid else {}
        line = facts.get("get_tracking") or facts.get("get_order_status")
        return f" Also tell the customer, in one sentence, what was found: {self.state.label(oid)}: {line}." \
            if line else ""

    def end_turn(self, msg: str, calls: list[dict], reply: str | None = None) -> None:
        self.progress.end_turn(msg, calls, reply)
