"""The golden-set scorer (evals/run_eval.py, eval-v4): which tool sequences pass required_calls, and amounts
written with digit groups.

    uv run --group dev pytest tests/test_scorer.py
"""

import sys
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from evals.run_eval import _required, plain_amounts  # noqa: E402


def exp(*calls):
    return [NS(name=n, args=a) for n, a in calls]


def got(*calls):
    return [{"name": n, "args": a} for n, a in calls]


LIST, STATUS, TRACK = ("list_my_orders", {}), ("get_order_status", {"order_id": 1}), ("get_tracking", {"order_id": 1})


def test_lookups_in_any_order_pass():                      # ord-005
    assert _required(exp(LIST, TRACK, STATUS), got(("list_my_orders", {"limit": 5}), STATUS, TRACK))


def test_a_missing_or_wrong_lookup_fails():
    assert not _required(exp(LIST, TRACK), got(LIST, STATUS))
    assert not _required(exp(TRACK), got(("get_tracking", {"order_id": 2})))


def test_an_action_before_what_it_depends_on_fails():
    propose = ("propose_return", {"order_id": 1, "line_no": 1, "reason": "faulty"})
    assert _required(exp(STATUS, propose), got(STATUS, propose))
    assert not _required(exp(STATUS, propose), got(propose, STATUS))
    assert not _required(exp(TRACK, ("escalate_to_human", None)), got(("escalate_to_human", {}), TRACK))


def test_a_repeated_lookup_is_matched_where_it_lets_the_case_pass():
    esc = ("escalate_to_human", None)
    assert _required(exp(TRACK, esc), got(TRACK, ("escalate_to_human", {"reason": "lost"}), TRACK))


def test_extra_calls_are_allowed():
    assert _required(exp(TRACK), got(LIST, STATUS, TRACK))


def test_grouped_amounts_read_as_plain_numbers():
    assert plain_amounts("₹3,598.00 and ₹1,19,900") == "₹3598.00 and ₹119900"
    assert plain_amounts("orders 11904, 12578 and 5,7 days") == "orders 11904, 12578 and 5,7 days"
