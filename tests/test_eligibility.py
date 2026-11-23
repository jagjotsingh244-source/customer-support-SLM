"""Every return rule, one test per seeded situation, with the clock passed in.

    uv run --group dev pytest tests/test_eligibility.py
"""

import sys
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent.returns import ItemFacts, eligibility  # noqa: E402
from config import NOW  # noqa: E402

PAN = ItemFacts(name="Frying pan", category="home", returnable=True, opened=True,
                delivered_at=NOW - timedelta(days=3), in_active_return=False, value_inr=Decimal("1299.00"))
WEBCAM = replace(PAN, name="1080p webcam", category="electronics", opened=False)
EARBUDS = replace(PAN, name="Earbuds", category="electronics", returnable=False)


def test_eligible():
    v = eligibility(PAN, "changed_mind", NOW)
    assert v.ok and v.reason == "eligible" and v.window_days == 15
    assert v.delivered_on == PAN.delivered_at.date() and v.window_ends == PAN.delivered_at + timedelta(days=15)


def test_window_just_expired():
    delivered = NOW - timedelta(days=7)
    on_the_edge = replace(WEBCAM, delivered_at=delivered)
    assert eligibility(on_the_edge, "changed_mind", NOW).ok                     # the last moment still counts
    v = eligibility(on_the_edge, "changed_mind", NOW + timedelta(seconds=1))
    assert not v.ok and v.reason == "outside_window" and v.window_days == 7
    assert eligibility(replace(PAN, delivered_at=NOW - timedelta(days=16)), "faulty", NOW).reason == "outside_window"


def test_window_depends_on_category():
    ten_days = NOW - timedelta(days=10)
    assert eligibility(replace(WEBCAM, delivered_at=ten_days), "changed_mind", NOW).reason == "outside_window"
    assert eligibility(replace(PAN, delivered_at=ten_days), "changed_mind", NOW).ok
    assert eligibility(replace(PAN, category="accessories", delivered_at=ten_days), "changed_mind", NOW).ok


def test_opened_electronics():
    opened = replace(WEBCAM, opened=True)
    assert eligibility(opened, "changed_mind", NOW).reason == "opened_not_faulty"
    for reason in ("faulty", "damaged_in_transit", "wrong_item"):
        assert eligibility(opened, reason, NOW).ok
    assert eligibility(WEBCAM, "changed_mind", NOW).ok                          # sealed: fine


def test_non_returnable_item():
    assert eligibility(EARBUDS, "changed_mind", NOW).reason == "not_returnable"
    assert eligibility(EARBUDS, "faulty", NOW).reason == "report_for_replacement"
    assert eligibility(replace(EARBUDS, opened=False), "changed_mind", NOW).ok  # sealed hygiene items follow the window


def test_not_delivered_and_already_returning():
    v = eligibility(replace(PAN, delivered_at=None), "changed_mind", NOW)
    assert v.reason == "not_delivered" and v.delivered_on is None and v.window_ends is None
    assert eligibility(replace(PAN, in_active_return=True), "changed_mind", NOW).reason == "already_returning"


def test_rules_apply_in_order():
    """An expired window is reported before the item type, so the customer hears the deciding reason."""
    old_earbuds = replace(EARBUDS, delivered_at=NOW - timedelta(days=30))
    assert eligibility(old_earbuds, "changed_mind", NOW).reason == "outside_window"


def test_unknown_reason_is_refused():
    with pytest.raises(ValueError):
        eligibility(PAN, "too_expensive", NOW)
