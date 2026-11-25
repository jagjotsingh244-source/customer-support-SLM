"""The eval metrics that turn traces into numbers: pass^k, the bootstrap interval, the tool confusion table, and
the per-layer reading of a trace (evals/metrics.py). No model and no database.

    uv run --group dev pytest tests/test_eval_metrics.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from evals.metrics import (NONE, bootstrap_ci, confusion, end_state, layer_metrics, pass_hat_k,  # noqa: E402
                           pass_k, privacy_violations, rate, return_claimed_done)


def test_pass_hat_k_is_all_or_nothing_when_k_equals_n():
    assert pass_hat_k([True, True, True], 3) == 1
    assert pass_hat_k([True, False, True], 3) == 0


def test_pass_hat_k_unbiased_for_smaller_k():
    # 2 of 3 runs passed: one of 3 pairs passes both, so pass^2 = 1/3; pass^1 is the plain rate.
    assert pass_hat_k([True, False, True], 2) == 1 / 3
    assert pass_hat_k([True, False, True], 1) == 2 / 3


def test_pass_k_over_cases():
    assert pass_k({"a": [True, True, True], "b": [True, False, True]}) == 0.5


def test_bootstrap_interval_contains_the_mean_and_is_repeatable():
    xs = [1.0] * 17 + [0.0] * 8
    lo, hi = bootstrap_ci(xs)
    assert lo < 17 / 25 < hi
    assert bootstrap_ci(xs) == (lo, hi)
    assert bootstrap_ci([1.0] * 10) == (1.0, 1.0)


def test_rate_counts():
    r = rate([True, False, None, True])
    assert (r["n"], r["k"]) == (3, 2)


def test_confusion_pairs_matches_then_swaps_then_misses():
    t = confusion([(["list_my_orders", "get_tracking"], ["list_my_orders", "get_order_status"]),
                   (["search_help_center", "escalate_to_human"], ["search_help_center"]),
                   ([], ["list_my_orders"])])
    assert t[("list_my_orders", "list_my_orders")] == 1
    assert t[("get_tracking", "get_order_status")] == 1          # wrong tool
    assert t[("escalate_to_human", NONE)] == 1                    # missed
    assert t[(NONE, "list_my_orders")] == 1                       # extra


def _trace(calls, replies, users):
    turns, messages = [], [{"role": "system", "content": "s"}]
    for u, r, cs in zip(users, replies, calls):
        messages.append({"role": "user", "content": u})
        turns.append({"tool_calls": [{"name": n, "args": json.dumps(a), "parsed": True, "result": res}
                                     for n, a, res in cs],
                      "model_calls": [{"prompt_tokens": 100, "completion_tokens": 10}], "reply": r,
                      "turn_s": 1.0, "format_errors": 0})
        messages.append({"role": "assistant", "content": r})
    return {"turns": turns, "messages": messages, "replies": replies, "final_reply": replies[-1],
            "tool_calls": [{"name": n} for cs in calls for n, _, _ in cs]}


def test_end_state_reads_proposals_and_tickets_from_tool_results():
    t = _trace([[("propose_return", {"order_id": 1, "line_no": 1, "reason": "changed_mind"},
                  {"eligible": True, "proposal_id": 900001})],
                [("escalate_to_human", {"reason": "other", "summary": "x"}, {"handed_off": True, "ticket_id": 900002})]],
               ["Press Confirm on the card.", "A teammate will contact you."], ["return it", "and a person please"])
    s = end_state(t)
    assert s["proposal"] and s["ticket"] and s["fallback_turns"] == 0


def test_a_ticket_after_the_customer_asked_for_a_person_is_right():
    t = _trace([[("get_tracking", {"order_id": 1}, {"status": "in_transit"})],
                [("escalate_to_human", {"reason": "other", "summary": "x"}, {"handed_off": True, "ticket_id": 9})]],
               ["It is on its way.", "Done, ticket 9."], ["where is it", "let me talk to a person"])
    common = dict(category="order_lookup", expected_tools=None, sources=[], expect_proposal=False,
                  expect_ticket=False, ticket_offer_ok=False, private_terms=[], had_return=False)
    assert layer_metrics(t, **common, person_ask_ok=True)["end_state_ok"]
    assert not layer_metrics(t, **common, person_ask_ok=False)["end_state_ok"]


def test_retrieval_counts_only_cases_that_searched():
    hit = _trace([[("search_help_center", {"query": "q"},
                    {"results": [{"id": "a#x"}, {"id": "returns#window"}]})]], ["It is 15 days."], ["window?"])
    none = _trace([[]], ["I think it is 15 days."], ["window?"])
    kw = dict(category="policy", expected_tools=["search_help_center"], sources=["returns#window"],
              expect_proposal=False, expect_ticket=False, ticket_offer_ok=False, private_terms=[], had_return=False)
    m = layer_metrics(hit, **kw)
    assert (m["searched"], m["recall3"], m["rr"]) == (True, True, 0.5)
    m = layer_metrics(none, **kw)
    assert (m["searched"], m["recall3"], m["rr"]) == (False, None, None)


def test_privacy_ignores_what_the_customer_typed():
    t = _trace([[]], ["I cannot share anything about Pranav's orders."], ["does pranav have an order?"])
    assert privacy_violations(t, ["pranav", "nagpur"]) == []
    leak = _trace([[]], ["Pranav's order is going to Nagpur. Call 9876543210."], ["does pranav have an order?"])
    assert len(privacy_violations(leak, ["pranav", "nagpur"])) == 2


def test_return_claimed_done_skips_negations_conditionals_and_known_returns():
    claim = _trace([[]], ["Your return has been confirmed."], ["return it"])
    assert return_claimed_done(claim, had_return=False)
    for text in ["No return has been created yet. Would you like one?",
                 "The refund will be sent once the return is processed."]:
        assert not return_claimed_done(_trace([[]], [text], ["return it"]), had_return=False)
    known = _trace([[("get_order_status", {"order_id": 1}, {"returns": [{"status": "refunded"}]})]],
                   ["The return was initiated on 4 November and is completed."], ["did my refund come?"])
    assert not return_claimed_done(known, had_return=False)


def test_date_facts_are_relative_to_the_frozen_today():
    from evals.judge_units import Unit, date_facts
    u = Unit("r/c/1", "r", "c", 1, "where is it", "", [], [{"tool": "get_tracking", "args": {"order_id": 1}, "result": {
        "shipments": [{"tracking_no": "BL7", "items": "Fan", "status": "in_transit", "eta": "2026-11-06",
                       "last_scan_at": "2026-11-11 11:44:00+05:30"}]}}], "A")
    text = date_facts(u)
    assert "14 days before today (past, not delivered)" in text and "last scan 11 Nov 2026, 9 days before today" in text


def test_label_sheet_round_trip_keeps_verdicts_and_reads_edits(tmp_path):
    from evals import judge_labels as jl
    rows = [{"id": "2026-11-25_golden-sft2a/ord-014/1", "grounded": "PASS", "grounded_why": "g", "resolved": "PASS",
             "resolved_why": "r", "split": "tune"}]
    path = tmp_path / "sheet.md"
    path.write_text(jl.sheet(rows).replace("**Resolved:** PASS — r", "**Resolved:** FAIL — misses the date"))
    changes = jl.read_sheet(rows, path)
    assert changes == ["2026-11-25_golden-sft2a/ord-014/1: resolved PASS -> FAIL"]
    assert rows[0]["resolved"] == "FAIL" and rows[0]["resolved_draft"] == "PASS" and rows[0]["grounded"] == "PASS"
