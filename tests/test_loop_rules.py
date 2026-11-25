"""The agent loop with the hand-off rules and the guard on, against a scripted model and fake tools (no GPU, no
database): forced hand-offs happen in code, the ticket summary comes from the state, nothing is handed off twice,
personal data never reaches the customer, and the tool log is redacted.

    uv run --group dev pytest tests/test_loop_rules.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from openai.types.chat import ChatCompletion  # noqa: E402

from agent.escalation import HandoffRules  # noqa: E402
from agent.guardrails import Guard  # noqa: E402
from agent.loop import run_turn  # noqa: E402
from agent.privacy import SAFE_REPLY  # noqa: E402
from config import IST, NOW  # noqa: E402


def completion(content=None, calls=None):
    return ChatCompletion.model_validate({
        "id": "x", "object": "chat.completion", "created": 0, "model": "m",
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        "choices": [{"index": 0, "finish_reason": "tool_calls" if calls else "stop",
                     "message": {"role": "assistant", "content": content, "tool_calls": calls}}]})


def call(name, args, cid="c0"):
    return {"id": cid, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}


class Model:
    """Returns the scripted completions in order and keeps what it was sent."""

    def __init__(self, *replies):
        self.replies, self.seen = list(replies), []
        self.chat = self.completions = self

    def create(self, messages, **_):
        self.seen.append([dict(m) for m in messages])
        return self.replies.pop(0)


class Tools:
    """A dispatcher like agent/tools_v2.call_tool, with canned results; records every call."""

    def __init__(self):
        self.calls, self.tickets = [], 0

    def __call__(self, name, raw, session, attempts):
        args = json.loads(raw)
        self.calls.append((name, args))
        if name == "escalate_to_human":
            self.tickets += 1
            return {"handed_off": True, "ticket_id": 900000 + self.tickets, "note": "A teammate will pick this up."}
        if name == "get_tracking":
            return {"order_id": args["order_id"], "shipped": True, "order_status": "shipped",
                    "shipments": [{"status": "in_transit", "carrier": "SwiftShip", "tracking_no": "SS70001303",
                                   "items": "Phone case", "last_scan_location": "Vijayawada hub",
                                   # 11303 has been stuck since 11 Nov; every other order was scanned yesterday
                                   "last_scan_at": "2026-11-11T09:00:00+05:30" if args["order_id"] == 11303
                                   else "2026-11-19T09:00:00+05:30"}]}
        if name == "get_order_status":
            return {"order_id": args["order_id"], "status": "shipped", "total_inr": "948.00",
                    "items": [{"line_no": 1, "name": "Cushion covers"}]}
        return {"error": "unknown_tool"}


def turn(model, tools, messages, rules=None, guard=None):
    return run_turn(model, "m", messages, [], tools, session=None, trace_id="t", rules=rules, guard=guard)


def test_asking_for_a_person_hands_off_before_the_model_runs():
    tools, rules = Tools(), HandoffRules(now=lambda: NOW)
    model = Model(completion("I've passed this to our support team; a teammate will reply here."))
    messages = [{"role": "system", "content": "rules"}, {"role": "user", "content": "i want to talk to a real person"}]
    reply, trace = turn(model, tools, messages, rules)
    assert tools.calls[0][0] == "escalate_to_human" and trace["forced_handoff"] == "asked_for_person"
    assert trace["escalated"] is True
    summary = tools.calls[0][1]["summary"]
    assert "asked for person" in summary and "i want to talk to a real person" in summary
    # the model saw the hand-off as a call it made, and a result telling it what to say
    sent = model.seen[0]
    assert sent[-2]["tool_calls"][0]["function"]["name"] == "escalate_to_human"
    assert "without promising a time" in json.loads(sent[-1]["content"])["note"]


def test_a_lost_parcel_is_handed_off_after_the_tracking_result():
    tools, rules = Tools(), HandoffRules(now=lambda: NOW)
    model = Model(completion(calls=[call("get_tracking", {"order_id": 11303})]),
                  completion("Your phone case has not moved since 11 Nov, so I've asked our team to investigate."))
    messages = [{"role": "system", "content": "rules"}, {"role": "user", "content": "where is my phone case 11303"}]
    reply, trace = turn(model, tools, messages, rules)
    assert [c[0] for c in tools.calls] == ["get_tracking", "escalate_to_human"]
    assert trace["forced_handoff"] == "possible_lost"
    args = tools.calls[1][1]
    assert args["reason"] == "lost_parcel" and "11303" in args["summary"] and "SS70001303" in args["summary"]


def test_a_shipped_order_seen_only_by_status_gets_its_tracking_read_and_handed_off():
    tools, rules = Tools(), HandoffRules(now=lambda: NOW)
    model = Model(completion(calls=[call("get_order_status", {"order_id": 11303})]),
                  completion("Your phone case has not moved since 11 Nov; I've asked the team to investigate."))
    messages = [{"role": "system", "content": "rules"}, {"role": "user", "content": "my phone case 11303, where is it"}]
    reply, trace = turn(model, tools, messages, rules)
    assert [c[0] for c in tools.calls] == ["get_order_status", "get_tracking", "escalate_to_human"]
    assert trace["forced_tracking"] == [11303] and trace["forced_handoff"] == "possible_lost"


def test_tracking_is_read_once_per_order():
    tools, rules = Tools(), HandoffRules(now=lambda: NOW)
    rules.observe("get_tracking", {"order_id": 11538}, {"order_id": 11538, "shipped": True, "shipments": []})
    assert rules.tracking_to_check([{"order_id": 11538, "status": "shipped", "items": []}]) is None
    assert rules.tracking_to_check([{"order_id": 11539, "status": "delivered", "items": []}]) is None


def test_the_models_own_handoff_gets_the_state_summary_and_no_second_ticket():
    tools, rules = Tools(), HandoffRules(now=lambda: NOW)
    model = Model(completion(calls=[call("get_order_status", {"order_id": 11538})]),
                  completion(calls=[call("escalate_to_human", {"reason": "other", "summary": "customer upset"}, "c1")]),
                  completion("A teammate will take it from here."),
                  completion(calls=[call("escalate_to_human", {"reason": "other", "summary": "again"}, "c2")]),
                  completion("It is already with the team."))
    messages = [{"role": "system", "content": "rules"}, {"role": "user", "content": "my cushion covers 11538 are late"}]
    turn(model, tools, messages, rules)
    assert [c[0] for c in tools.calls] == ["get_order_status", "get_tracking", "escalate_to_human"]   # tracking read by the loop
    summary = tools.calls[2][1]["summary"]
    assert summary != "customer upset" and "11538" in summary and "Cushion covers" in summary
    messages.append({"role": "user", "content": "so what now"})
    reply, trace = turn(model, tools, messages, rules)
    assert tools.tickets == 1                       # the repeat call reused ticket 900001
    assert trace["tool_calls"][0]["result"]["ticket_id"] == 900001


def test_the_same_answer_twice_forces_a_handoff_on_the_next_ask():
    tools, rules = Tools(), HandoffRules(now=lambda: NOW)
    same = "Your order 11538 is shipped and on its way to you."
    model = Model(completion(calls=[call("get_order_status", {"order_id": 11538})]), completion(same),
                  completion(calls=[call("get_order_status", {"order_id": 11538})]), completion(same),
                  completion("I've passed this to the team; a teammate will reply here."))
    messages = [{"role": "system", "content": "rules"}]
    for text in ["where are my cushion covers 11538", "but WHERE is it", "this is useless"]:
        messages.append({"role": "user", "content": text})
        reply, trace = turn(model, tools, messages, rules)
    assert trace["forced_handoff"] == "no_progress" and tools.tickets == 1   # the same answer twice, then a third ask


def test_new_answers_from_known_facts_are_not_counted_as_stuck():
    tools, rules = Tools(), HandoffRules(now=lambda: NOW)
    model = Model(completion(calls=[call("get_order_status", {"order_id": 11538})]), completion("It is shipped."),
                  completion("It left the warehouse on 12 Nov."), completion("The total was ₹948."),
                  completion("Anything else?"))
    messages = [{"role": "system", "content": "rules"}]
    for text in ["where are my cushion covers 11538", "when did it leave", "how much did i pay", "and the items?"]:
        messages.append({"role": "user", "content": text})
        reply, trace = turn(model, tools, messages, rules)
    assert tools.tickets == 0 and rules.progress.turns_without_progress == 0


def test_after_21_00_the_model_is_told_when_support_opens():
    tools, rules = Tools(), HandoffRules(now=lambda: datetime(2026, 11, 20, 21, 30, tzinfo=IST))
    model = Model(completion("Done: a teammate will pick this up at 9:00 IST tomorrow."))
    messages = [{"role": "system", "content": "rules"}, {"role": "user", "content": "connect me to a human"}]
    turn(model, tools, messages, rules)
    note = json.loads(model.seen[0][-1]["content"])["note"]
    assert "offline" in note and "9:00 IST tomorrow" in note


def test_without_rules_nothing_is_forced():
    tools = Tools()
    model = Model(completion("Sure, what is your order number?"))
    messages = [{"role": "system", "content": "rules"}, {"role": "user", "content": "i want to talk to a real person"}]
    reply, trace = turn(model, tools, messages)
    assert tools.calls == [] and "forced_handoff" not in trace


def test_personal_data_never_reaches_the_customer_and_the_log_is_redacted(caplog):
    tools, guard = Tools(), Guard("Rules: be helpful.")
    model = Model(completion(calls=[call("get_order_status", {"order_id": 11538, "note": "call 9876543210"})]),
                  completion("Sure, I'll call her on 9876543210 about it."))
    messages = [{"role": "system", "content": "rules"}, {"role": "user", "content": "her number is 9876543210"}]
    with caplog.at_level("INFO", logger="nova.tools"):
        reply, trace = turn(model, tools, messages, guard=guard)
    assert reply == SAFE_REPLY and trace["output_guard"]["hits"] == ["phone"]
    args = [json.loads(r.getMessage())["args"] for r in caplog.records if r.levelname == "INFO"]
    assert args == ['{"order_id": 11538, "note": "call ••••••3210"}']
