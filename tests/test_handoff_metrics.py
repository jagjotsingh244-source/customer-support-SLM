"""The hand-off measurement (evals/handoff.py): precision and recall arithmetic, and the replay of the code rules
turn by turn on hand-made traces. No database, no model.

    uv run --group dev pytest tests/test_handoff_metrics.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent import escalation as e  # noqa: E402
from config import NOW  # noqa: E402
from evals import handoff as h  # noqa: E402

STATUS = {"order_id": 11538, "status": "shipped", "total_inr": "948.00", "items": [{"name": "Cushion covers"}]}
TICKET = {"handed_off": True, "ticket_id": 900001, "note": "A teammate will pick this up."}


def call(name, result, args='{"order_id": 11538}'):
    return {"name": name, "args": args, "parsed": True, "result": result, "ok": "error" not in result}


def tracking(last_scan_at, status="in_transit"):
    return {"order_id": 11303, "shipped": True,
            "shipments": [{"status": status, "last_scan_at": last_scan_at, "tracking_no": "SS1", "carrier": "SwiftShip"}]}


def trace(turns, cid="x-001", escalated=None):
    """turns: [(customer message, [tool calls], reply)]"""
    messages = []
    for msg, _, reply in turns:
        messages += [{"role": "user", "content": msg}, {"role": "assistant", "content": reply}]
    calls = [c for _, cs, _ in turns for c in cs]
    if escalated is None:
        escalated = any(c["name"] == "escalate_to_human" and c["ok"] for c in calls) or \
            any(r == h.FALLBACK_REPLY for _, _, r in turns)
    return {"id": cid, "messages": messages, "escalated": escalated, "tool_calls": calls,
            "replies": [r for _, _, r in turns], "final_reply": turns[-1][2],
            "turns": [{"tool_calls": cs, "reply": r} for _, cs, r in turns]}


# Arithmetic -----------------------------------------------------------------------------------------------

def row(needed, model, fired=False, offered=False):
    f = [h.Fired(0, e.Escalation("asked_for_person", "other"), 0)] if fired else []
    return h.CaseResult("c", "x", needed, model, model, False, offered, f)


def test_precision_and_recall_model_only_and_replayed():
    rows = [row(True, True),                  # needed, handed off
            row(True, False, fired=True),     # needed, missed by the model, caught by a rule
            row(True, False, offered=True),   # needed, missed, offered instead
            row(False, True),                 # not needed, handed off anyway
            row(False, False, fired=True),    # not needed, a rule would add it
            row(False, False)]                # not needed, nothing
    m = h.precision_recall(rows)
    assert (m["needed"], m["handoffs"], m["tp"], m["missed"], m["unneeded"]) == (3, 2, 1, 2, 1)
    assert m["precision"]["mean"] == 1 / 2 and m["recall"]["mean"] == 1 / 3
    assert m["recall_offer"]["k"] == 2 and m["offers"] == 1
    r = h.precision_recall(rows, replayed=True)
    assert (r["handoffs"], r["tp"], r["missed"], r["unneeded"]) == (4, 2, 1, 2)
    assert r["precision"]["mean"] == 2 / 4 and r["recall"]["mean"] == 2 / 3


def test_no_handoffs_gives_no_precision_rather_than_zero():
    m = h.precision_recall([row(True, False), row(False, False)])
    assert m["precision"]["n"] == 0 and m["recall"]["mean"] == 0.0


# Replay ordering ------------------------------------------------------------------------------------------

def test_the_counter_for_a_turn_comes_from_the_turns_before_it():
    t = trace([("where is my cushion cover order", [call("get_order_status", STATUS)], "It has shipped."),
               ("but where is it", [call("get_order_status", STATUS)], "It has shipped."),    # nothing new: 1
               ("hello??", [], "It has shipped."),                                            # 2, counted after
               ("are you there", [], "It has shipped.")])                                     # checked with 2
    fired = h.replay(t, NOW)
    assert [(f.turn, f.rule.reason, f.counter_before) for f in fired] == [(3, "no_progress", 2)]


def test_a_closing_turn_does_not_add_to_the_counter():
    t = trace([("where is my order", [call("get_order_status", STATUS)], "It has shipped."),
               ("ok thanks", [], "You're welcome."),
               ("when will it come", [], "By the 21st."),
               ("ok thanks", [], "You're welcome.")])
    assert h.replay(t, NOW) == []


def test_the_lost_parcel_rule_fires_on_the_turn_with_the_tracking_result():
    t = trace([("hi", [], "Hello, how can I help?"),
               ("my phone case hasnt moved", [call("get_tracking", tracking("2026-11-11T09:00:00+05:30"),
                                                   '{"order_id": 11303}')], "It is in transit.")])
    fired = h.replay(t, NOW)
    assert [(f.turn, f.rule.reason) for f in fired] == [(1, "possible_lost")]


# One case ---------------------------------------------------------------------------------------------------

def test_a_fallback_counts_as_a_handoff_for_golden_but_not_for_simulated():
    t = trace([("cancel it", [], h.FALLBACK_REPLY)])
    truth = h.Truth(needed=False, offer_ok=False, category="order_lookup")
    golden = h.judge_case(t, truth, "golden", NOW)
    sim = h.judge_case(t, truth, "simulated", NOW)
    assert golden.model and golden.fallback and not golden.ticket
    assert not sim.model and sim.fallback


def test_a_rule_turns_a_miss_into_a_replayed_handoff_and_the_offer_is_kept_apart():
    t = trace([("i want to talk to a real person", [], "Would you like me to connect you with our support team?")])
    r = h.judge_case(t, h.Truth(needed=True, offer_ok=True, category="unanswerable"), "golden", NOW)
    assert not r.model and r.offered and r.replayed and r.first_rule.rule.reason == "asked_for_person"
    t2 = trace([("i need a person", [call("escalate_to_human", TICKET, '{"reason": "other", "summary": "wants a person"}')],
                 "Ticket 900001 is open.")])
    r2 = h.judge_case(t2, h.Truth(needed=True, offer_ok=False, category="escalation"), "simulated", NOW)
    assert r2.model and r2.ticket and r2.ticket_turn == 0 and not r2.offered
