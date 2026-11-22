"""Style metrics count what they claim, with the same definitions the rewritten replies were checked with.

    uv run --group data --group dev pytest tests/test_style_metrics.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from evals.style_metrics import OFFER, features, metrics, opening  # noqa: E402


def test_offer_matches_the_rewrite_checks():
    from data_prep.prepare_bitext import OFFER as REWRITE_OFFER

    assert OFFER.pattern == REWRITE_OFFER.pattern and OFFER.flags == REWRITE_OFFER.flags


def test_features():
    nova = "I'm sorry the refund hasn't reached you yet. Would you like me to check your order?"
    base = ("I'd be happy to help! Please follow these steps:\n1. Sign in to {{Online Company Portal Info}}.\n"
            "2. Open your orders. Refunds take 5-7 business days.")
    f, g = features(nova), features(base)
    assert f == {"words": 16, "placeholder": False, "list": False, "digit": False, "next_step": True,
                 "over_limit": False, "exclamation": False}
    assert g["placeholder"] and g["list"] and g["digit"] and g["exclamation"]
    assert not g["next_step"]  # ends on a statement with no offer


def test_openings_and_shares():
    same = "I understand your concern regarding your order, and I'm here to help."
    m = metrics([same, same, "Hello, how can I help you today?", same.upper()])
    assert opening(same) == "i understand your concern regarding"
    assert m["distinct openings"] == 0.5          # case and punctuation do not make an opening new
    assert m["most common opening"].endswith("(75%)")
    assert m["ends with a question or offer"] == 0.25
