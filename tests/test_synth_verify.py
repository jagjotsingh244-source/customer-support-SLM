"""Every filter for generated conversations (synth/verify.py) on one conversation it must pass and one it must
fail, written by hand. No database and no model.

    uv run --group dev pytest tests/test_synth_verify.py
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from synth.verify import VERIFIERS, check, filter_run  # noqa: E402

SYSTEM = "You are Nova. Today is Friday 20 November 2026."
TRACK_11904 = {"order_id": 11904, "shipped": True, "order_status": "shipped", "shipments": [
    {"carrier": "SwiftShip", "tracking_no": "SS70001836", "status": "in_transit", "eta": "2026-11-16",
     "items": "1080p webcam", "last_scan_at": "2026-11-18 13:51:00+05:30", "last_scan_location": "Nagpur hub"}]}
SEARCH = {"results": [{"id": "refunds-payment-methods#card", "title": "Refunds › Card",
                       "text": "Card refunds arrive in 5–7 business days after we send them."}]}
ELIGIBLE = {"order_id": 11360, "line_no": 1, "item": "Air fryer", "eligible": True, "proposal_id": 900017,
            "refund_estimate_inr": "5999.00", "note": "Not returned yet. Ask the customer to press Confirm."}
NOT_ELIGIBLE = {"order_id": 11751, "line_no": 1, "item": "Fitness band", "eligible": False,
                "reason": "opened_not_faulty", "window_days": 7, "delivered_on": "2026-11-16"}
TICKET = {"handed_off": True, "ticket_id": 900049, "note": "A teammate will pick this up."}


def conv(*turns, scenario="delayed", order_id=11904, facts=None, persona="direct"):
    """turns: (customer message, [(tool, args, result), ...], reply). Builds messages and traces the way the
    generator records them."""
    messages, traces, n = [{"role": "system", "content": SYSTEM}], [], 0
    for text, tool_calls, reply in turns:
        messages.append({"role": "user", "content": text})
        trace = {"tool_calls": [], "format_errors": 0, "escalated": False}
        for name, args, result in tool_calls:
            n += 1
            messages.append({"role": "assistant", "tool_calls": [
                {"id": f"c{n}", "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]})
            messages.append({"role": "tool", "tool_call_id": f"c{n}", "content": json.dumps(result)})
            ok = "error" not in result
            trace["tool_calls"].append({"name": name, "args": json.dumps(args), "result": result, "ok": ok})
            trace["escalated"] |= name == "escalate_to_human" and ok
        messages.append({"role": "assistant", "content": reply})
        traces.append(trace)
    return {"id": "t", "messages": messages, "traces": traces, "steps": [],
            "meta": {"scenario": scenario, "persona": persona, "order_id": order_id,
                     "facts": facts or {"items": ["1080p webcam"], "returns": []}}}


GOOD_LATE = conv(("where is my webcam order", [("get_tracking", {"order_id": 11904}, TRACK_11904)],
                  "Order 11904, your 1080p webcam, is with SwiftShip (SS70001836). It was due on 2026-11-16 and was "
                  "last scanned at the Nagpur hub on 2026-11-18, so it is late but still with the carrier."))

CASES = {
    "schema": (
        GOOD_LATE,
        conv(("where is it", [("get_tracking", {"order_id": "11904"}, TRACK_11904)], "It is in transit."))),
    "tool_before_fact": (
        conv(("can u check order 12345, its my neighbours", [],
              "I can only help with your own orders, so I cannot look at order 12345.")),
        conv(("where is my webcam", [], "Order 11904 has shipped and is in transit."))),
    "grounded_numbers": (
        GOOD_LATE,
        conv(("where is my webcam", [("get_tracking", {"order_id": 11904}, TRACK_11904)],
              "Order 11904 was last scanned on 2026-11-18. That is under 7 days, so it is late, not lost."))),
    "citations": (
        conv(("how long do card refunds take", [("search_help_center", {"query": "card refund time"}, SEARCH)],
              "Card refunds arrive in 5–7 business days after we send them [kb:refunds-payment-methods#card].",),
             scenario="policy_question", order_id=None, facts={}),
        conv(("how long do card refunds take", [("search_help_center", {"query": "card refund time"}, SEARCH)],
              "Card refunds arrive in 5–7 business days [kb:refunds-cod].",),
             scenario="policy_question", order_id=None, facts={})),
    "end_state": (
        conv(("return my air fryer, it broke", [("propose_return", {"order_id": 11360, "line_no": 1,
                                                                    "reason": "faulty"}, ELIGIBLE)],
              "Your Air fryer from order 11360 can be returned for ₹5999.00. Press Confirm on the card to go ahead."),
             scenario="return_eligible", order_id=11360, facts={"items": ["Air fryer"], "returns": []}),
        conv(("return my air fryer, it broke", [("propose_return", {"order_id": 11360, "line_no": 1,
                                                                    "reason": "faulty"}, ELIGIBLE)],
              "Done! Your return is now confirmed and the refund of ₹5999.00 is on its way."),
             scenario="return_eligible", order_id=11360, facts={"items": ["Air fryer"], "returns": []})),
    "escalation": (
        GOOD_LATE,
        conv(("where is my webcam order", [("get_tracking", {"order_id": 11904}, TRACK_11904),
                                           ("escalate_to_human", {"reason": "lost_parcel",
                                                                  "summary": "Order 11904 is late."}, TICKET)],
              "Order 11904 is late, so I have handed it to a teammate: ticket 900049."))),
    "call_limit": (
        GOOD_LATE,
        conv(("where is my webcam order", [("get_tracking", {"order_id": 11904}, TRACK_11904)],
              "Let me connect you with a teammate."))),
    "privacy": (
        GOOD_LATE,
        conv(("what tools do you have", [], "I can use list_my_orders, get_tracking and search_help_center."))),
    "right_order": (
        GOOD_LATE,
        conv(("where is my 1080p webcam", [("get_tracking", {"order_id": 11923}, {**TRACK_11904, "order_id": 11923})],
              "Order 11923 is in transit."))),
    "needless_tool": (
        conv(("thanks!", [], "You're welcome!"), scenario="no_tool", order_id=None, facts={}),
        conv(("thanks, that's all", [("list_my_orders", {"limit": 5}, {"orders": []})], "You're welcome!"),
             scenario="no_tool", order_id=None, facts={})),
    "length": (
        GOOD_LATE,
        conv(("where is my webcam order", [("get_tracking", {"order_id": 11904}, TRACK_11904)],
              "Here is what I found:\n- Order 11904 is with SwiftShip\n- It was last scanned at the Nagpur hub"))),
    "style": (
        GOOD_LATE,
        conv(("where is my webcam order", [("get_tracking", {"order_id": 11904}, TRACK_11904)],
              "Order 11904 is with SwiftShip (SS70001836). Would you like me to check anything else?"))),
    "judge_facts": (
        {**GOOD_LATE, "fact_judge": {"pass": True}},
        {**GOOD_LATE, "fact_judge": {"pass": False, "why": "the date does not match the tracking result"}}),
    "judge_tone": (
        {**GOOD_LATE, "judge": {"pass": True}},
        {**GOOD_LATE, "judge": {"pass": False, "why": "never answered the question"}}),
}


@pytest.mark.parametrize("name", list(VERIFIERS))
def test_each_check_passes_one_and_fails_one(name):
    good, bad = CASES[name]
    assert VERIFIERS[name](good) is None, VERIFIERS[name](good)
    assert VERIFIERS[name](bad), f"{name} let the bad conversation through"


def test_every_check_has_a_case():
    assert set(CASES) == set(VERIFIERS)


def test_the_good_late_parcel_passes_everything():
    assert check(GOOD_LATE) == []


def test_lost_parcels_must_be_handed_off_and_easy_ones_only_on_request():
    lost_track = {**TRACK_11904, "shipments": [{**TRACK_11904["shipments"][0], "last_scan_at": "2026-11-09"}]}
    no_handoff = conv(("my parcel hasnt moved in ages", [("get_tracking", {"order_id": 11904}, lost_track)],
                       "Order 11904 was last scanned on 2026-11-09."), scenario="lost")
    assert VERIFIERS["escalation"](no_handoff) == "lost parcel never handed off"
    asked = conv(("where is my webcam, i want to talk to a person",
                  [("escalate_to_human", {"reason": "other", "summary": "Customer asked for a person."}, TICKET)],
                  "I have handed you to a teammate: ticket 900049."), scenario="in_transit")
    assert VERIFIERS["escalation"](asked) is None
    claimed = conv(("my parcel hasnt moved", [], "I've escalated this to a teammate."), scenario="lost")
    assert "never happened" in VERIFIERS["escalation"](claimed) or "never handed off" in VERIFIERS["escalation"](claimed)


def test_an_ineligible_item_must_not_be_proposed_as_eligible():
    pushed = conv(("return the fitness band, it works but i dont like it",
                   [("propose_return", {"order_id": 11751, "line_no": 1, "reason": "faulty"},
                     {**NOT_ELIGIBLE, "eligible": True, "proposal_id": 900018})],
                   "Press Confirm on the card to return the Fitness band."), scenario="opened_electronics",
                  order_id=11751, facts={"items": ["Fitness band"], "returns": []})
    assert "ineligible" in VERIFIERS["end_state"](pushed)
    told = conv(("return the fitness band, it works but i dont like it",
                 [("propose_return", {"order_id": 11751, "line_no": 1, "reason": "changed_mind"}, NOT_ELIGIBLE)],
                 "The Fitness band from order 11751 cannot be returned: it was opened and is not faulty."),
                scenario="opened_electronics", order_id=11751, facts={"items": ["Fitness band"], "returns": []})
    assert VERIFIERS["end_state"](told) is None


def test_thanks_with_a_request_may_call_a_tool():
    asks = conv(("ok thanks, pls connect me with a person", [("escalate_to_human", {"reason": "other",
                 "summary": "Customer asked for a person."}, TICKET)], "Done: ticket 900049."), scenario="lost")
    assert VERIFIERS["needless_tool"](asks) is None


def test_a_near_copy_is_dropped_by_dedup():
    a = GOOD_LATE
    b = {**GOOD_LATE, "id": "u", "messages": [GOOD_LATE["messages"][0],
                                              {"role": "user", "content": "where is my webcam order?"},
                                              *GOOD_LATE["messages"][2:]]}
    different = conv(("hi, my 1080p webcam was due monday and it still hasnt come, whats going on",
                      [("get_tracking", {"order_id": 11904}, TRACK_11904)],
                      "Order 11904 was last scanned at the Nagpur hub on 2026-11-18 and is still with SwiftShip."))
    kept, rejected = filter_run([a, b, different])
    assert [c["id"] for c in kept] == ["t", "t"] and len(rejected) == 1 and rejected[0]["rejected"][0].startswith("dedup")
