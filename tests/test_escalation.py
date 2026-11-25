"""The hand-off rules in code (agent/escalation.py): each trigger, the hours on both sides of 21:00 IST, progress,
and the ticket summary.

    uv run --group dev pytest tests/test_escalation.py
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent import escalation as e  # noqa: E402
from agent.state import State  # noqa: E402
from config import IST, NOW  # noqa: E402


def at(h, m=0, s=0, day=20):
    return datetime(2026, 11, day, h, m, s, tzinfo=IST)


# Asked for a person ----------------------------------------------------------------------------------

@pytest.mark.parametrize("text", ["i want to talk to a real person", "just connect me to a human, dont want to talk to a bot",
                                  "whats the customer care number", "I want to talk to a PERSON", "get me your manager",
                                  "can someone call me back", "speak to someone please",
                                  "connect me to the support team", "yes pls connect me to a human right now"])
def test_asking_for_a_person_forces_a_handoff(text):
    assert e.must_escalate(text, 0, [], NOW) == e.Escalation("asked_for_person", "other")


@pytest.mark.parametrize("text", ["the delivery agent never came", "the courier person said i wasnt home",
                                  "where is my order 10482", "it's a gift for a friend", "this is so frustrating, where is it",
                                  # mentions, not requests, and figures of speech (found in saved simulated chats)
                                  "your customer service is a joke", "my manager asked me to order this",
                                  "im an executive, i dont have time for this", "thanks for getting a human on it",
                                  "i want to send a gift for a person", "can i get the delivery charge back?",
                                  "this is a scam, its been 10 days", "i have a burning question", "fire away",
                                  "that really hurt my feelings", "the fir tree decoration arrived broken",
                                  "i don't dispute that, just tell me when", "cool thanks bye",
                                  "what information do I need to provide to the support team if Nova doesn't help?"])
def test_ordinary_messages_do_not(text):
    assert e.must_escalate(text, 0, [], NOW) is None


# High-risk topics ------------------------------------------------------------------------------------

@pytest.mark.parametrize("text, topic, reason", [
    ("i was charged twice for order 11549", "payment_dispute", "payment_issue"),
    ("i'll raise a chargeback with my bank", "payment_dispute", "payment_issue"),
    ("i didn't place this order, is this fraud?", "fraud", "payment_issue"),
    ("this is the THIRD time. i will go to consumer court", "legal", "other"),
    ("the power bank caught fire on my desk", "safety", "damaged"),
    ("the iron gave me an electric shock", "safety", "damaged"),
    ("there's smoke coming out of the charger", "safety", "damaged"),
])
def test_high_risk_topics_force_a_handoff(text, topic, reason):
    assert e.must_escalate(text, 0, [], NOW) == e.Escalation(f"high_risk:{topic}", reason)


# Lost parcel -----------------------------------------------------------------------------------------

def tracking(last_scan_at, status="in_transit"):
    return {"order_id": 11303, "shipped": True,
            "shipments": [{"status": status, "last_scan_at": last_scan_at, "tracking_no": "SS1"}]}


def test_seven_days_without_a_scan_is_a_possible_loss():
    assert e.must_escalate("where is it", 0, [tracking("2026-11-13T09:59:00+05:30")], NOW).reason == "possible_lost"
    assert e.must_escalate("where is it", 0, [tracking(datetime(2026, 11, 11, 8, 0, tzinfo=IST))], NOW).reason == "possible_lost"


def test_six_days_or_a_delivered_box_is_not():
    assert e.must_escalate("where is it", 0, [tracking("2026-11-14T10:00:00+05:30")], NOW) is None
    assert e.must_escalate("where is it", 0, [tracking("2026-11-01T10:00:00+05:30", "delivered")], NOW) is None
    assert e.must_escalate("where is it", 0, [{"error": "not_found"}], NOW) is None


# No progress -----------------------------------------------------------------------------------------

STATUS = {"name": "get_order_status", "ok": True, "result": {"order_id": 11538, "status": "shipped"}}


def test_two_turns_without_anything_new_force_a_handoff():
    p = e.Progress()
    assert p.end_turn("my cushion covers are late", [STATUS]) == 0          # a new fact: progress
    assert p.end_turn("but where is it", [STATUS]) == 1                     # the same result again
    assert p.end_turn("you said that already, WHERE IS IT", []) == 2
    assert e.must_escalate("hello??", p.turns_without_progress, [], NOW).reason == "no_progress"


def test_the_no_progress_rule_never_fires_on_a_closing_message():
    assert e.must_escalate("ok thanks, i'll wait", 5, [], NOW) is None
    assert e.must_escalate("still nothing??", 2, [], NOW).reason == "no_progress"


def test_a_repeated_reply_counts_a_new_answer_does_not():
    p = e.Progress()
    p.end_turn("where is 11538", [STATUS], "It is shipped and on its way.")
    assert p.end_turn("when will it come", [], "The estimate was 12 Nov, so it is late.") == 0
    assert p.end_turn("but where is it", [], "It is shipped and on its way!") == 1
    assert p.end_turn("hello??", [], "Let me connect you with a teammate.") == 2


def test_thanks_is_not_a_turn_without_progress_and_new_facts_reset():
    p = e.Progress()
    p.end_turn("where is my order", [STATUS])
    assert p.end_turn("ok thanks!", []) == 0
    assert p.end_turn("and when will it come", []) == 1
    track = {"name": "get_tracking", "ok": True, "result": tracking("2026-11-19T10:00:00+05:30")}
    assert p.end_turn("can you check tracking", [track]) == 0
    assert p.end_turn("hm", [{"name": "get_tracking", "ok": False, "result": {"error": "not_found"}}]) == 1


# Hours -----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("when, open_", [(at(8, 59, 59), False), (at(9), True), (at(20, 59, 59), True),
                                         (at(21), False), (at(21, 0, 1), False), (at(23, 30), False), (at(0, 15), False)])
def test_support_hours_on_both_sides_of_the_edges(when, open_):
    assert e.support_open(when) is open_


def test_just_before_21_00_promises_no_time():
    note = e.handoff_note(at(20, 59), 900003)
    assert "900003" in note and "without promising a time" in note and "offline" not in note


def test_just_after_21_00_says_tomorrow_at_9():
    note = e.handoff_note(at(21, 1), 900003)
    assert "offline" in note and "9:00 IST tomorrow" in note
    assert e.next_opening(at(21, 1)) == at(9, day=21)


def test_after_midnight_says_today_at_9():
    assert "9:00 IST today" in e.handoff_note(at(0, 30, day=21), 900004)
    assert e.next_opening(at(0, 30, day=21)) == at(9, day=21)


def test_the_hours_are_read_in_ist_whatever_the_clock_zone():
    from datetime import timezone
    assert e.support_open(datetime(2026, 11, 20, 15, 29, tzinfo=timezone.utc)) is True    # 20:59 IST
    assert e.support_open(datetime(2026, 11, 20, 15, 31, tzinfo=timezone.utc)) is False   # 21:01 IST


# Ticket summary --------------------------------------------------------------------------------------

def test_the_summary_comes_from_the_state_with_every_order_id():
    s = State()
    s.update("get_tracking", {"order_id": 11303},
             {"shipped": True, "shipments": [{"status": "in_transit", "carrier": "SwiftShip", "tracking_no": "SS70001303",
                                              "items": "Phone case", "last_scan_location": "Vijayawada hub",
                                              "last_scan_at": "2026-11-11T09:00:00+05:30"}]})
    s.update("get_order_status", {"order_id": 11538}, {"status": "shipped", "total_inr": "948.00",
                                                     "items": [{"name": "Cushion covers"}]})
    summary = e.ticket_summary(s, e.Escalation("possible_lost", "lost_parcel"),
                               ["hi", "my phone case hasnt moved, call me on 9876543210"], ["get_tracking", "get_order_status"])
    assert "11303" in summary and "11538" in summary and "SS70001303" in summary
    assert "possible lost" in summary and "Checked: get_tracking, get_order_status." in summary
    assert summary.index("Customer:") < summary.index("11303")      # what they want comes first
    assert "9876543210" not in summary and "••••••3210" in summary
    assert len(summary) <= 500
