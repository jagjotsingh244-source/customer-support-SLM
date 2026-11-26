"""The output filter and log redaction (agent/privacy.py): what must be caught, and what must pass.

    uv run --group dev pytest tests/test_privacy.py
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent.privacy import SAFE_REPLY, mask_phone, output_filter, personal_data, plain_tool_words, redact, redact_obj  # noqa: E402

# Strings a correct reply contains all the time. None may be caught.
MUST_PASS = [
    "Your order 10482 is on its way.",
    "Tracking: SwiftShip SS70001836.",
    "BlueLine tracking number BL70002499, ETA 25 Nov.",
    "The total was ₹1,299.00 including ₹49 shipping.",
    "Your refund of ₹5999 was sent on 2026-11-18.",
    "A refund of ₹12,999.00 reaches your card in 5–7 business days.",
    "It was delivered on 20/11/2026 at 14:32.",
    "Last scan: Nagpur hub, 2026-11-20 03:21.",
    "I've opened ticket 900003 for a teammate.",
    "Return proposal #900001 is waiting for your Confirm.",
    "Pickup is 1–2 days after you confirm, to pincode 560001.",
    "UPI refunds arrive in 1–3 business days.",
    "Orders 11203, 11281 and 11904 are not on this account.",
    "Human support is open 09:00–21:00 IST.",
    "Your card ending 4242 will get the refund.",
    "The 7-day window for electronics ended on 17 Nov.",
    "Line 2 of order 11324: Umbrella, qty 1, ₹499.00.",
    "Reference 202611201234 is the UPI transaction id.",     # 12 digits: a UPI reference, not a card
]

# Strings that must never reach a customer.
MUST_CATCH = [
    ("Her number is 9876543210.", "phone"),
    ("Call +91 98765 43210 for help.", "phone"),
    ("Reach them at 098765-43210.", "phone"),
    ("Card 4111 1111 1111 1111 is on file.", "card_like"),
    ("Your card 4111-1111-1111-1111 was charged.", "card_like"),
    ("Paid with 5500000000000004.", "card_like"),
    ("Write to pranav.sood@example.com.", "foreign_email"),
    ("I sent it to wahab.backup@protonmail.com.", "foreign_email"),
    ("Call 919876543210 or 987 654 3210.", "phone"),
    ("Reach +91 9876 543 210 any time.", "phone"),
    ("Pay to asha.k@okicici and share the screenshot.", "upi_id"),
    ("Your Aadhaar 2345 6789 0123 is linked.", "id_number"),
    ("PAN ABCDE1234F, IFSC HDFC0001234.", "id_number"),
    ("Please share your OTP to continue.", "asks_for_secret"),
    ("To release this parcel, I need your card number and CVV.", "asks_for_secret"),
    ("Please share your bank details here so I can send the refund.", "asks_for_secret"),
    ("Add your bank details on the order page and share the OTP with me.", "asks_for_secret"),
    ("I need your card number on the order page.", "asks_for_secret"),
]


@pytest.mark.parametrize("text", MUST_PASS)
def test_ordinary_reply_passes(text):
    assert personal_data(text) == []
    assert output_filter(text) == (text, [])
    assert redact(text) == text


@pytest.mark.parametrize("text, kind", MUST_CATCH)
def test_personal_data_is_caught(text, kind):
    reply, hits = output_filter(text)
    assert reply == SAFE_REPLY and kind in hits


@pytest.mark.parametrize("text", ["Never share your OTP, CVV or UPI PIN with anyone, including us.",
                                  "We will not ask for your card number or bank details in chat.",
                                  "Add your bank details on the order page to get the refund.",
                                  "You need to add your bank details on the order page; the refund arrives in "
                                  "5–7 business days after you add them.",
                                  "Please provide your bank details on your order page."])
def test_warnings_about_secrets_pass(text):
    assert output_filter(text) == (text, [])


def test_minimise_drops_unneeded_ids_and_times_of_day():
    from agent.privacy import minimise
    status = {"order_id": 11281, "placed_at": "2026-11-02 14:31:00+05:30", "payment_method": "card",
              "returns": [{"return_id": 3, "status": "refunded", "proposed_at": "2026-11-05T10:00:00+05:30"}],
              "refunds": [{"refund_id": 7, "amount_inr": "999.00", "initiated_at": "2026-11-08 09:12:00+05:30",
                           "bank_details_added_at": "2026-11-07 18:00:00+05:30"}],
              "shipments": [{"shipment_id": 1, "delivered_at": "2026-11-04 16:50:00+05:30",
                             "last_scan_at": "2026-11-04 16:50:00+05:30"}]}
    assert minimise(status) == {
        "order_id": 11281, "placed_at": "2026-11-02", "payment_method": "card",
        "returns": [{"status": "refunded", "proposed_at": "2026-11-05"}],
        "refunds": [{"amount_inr": "999.00", "initiated_at": "2026-11-08"}],
        "shipments": [{"delivered_at": "2026-11-04 16:50:00+05:30", "last_scan_at": "2026-11-04 16:50:00+05:30"}]}


def test_there_are_at_least_twenty_strings():
    assert len(MUST_PASS) + len(MUST_CATCH) >= 20


def test_the_customers_own_email_passes():
    assert personal_data("We'll write to you at asha@example.com.", own_email="Asha@Example.com") == []
    assert personal_data("We'll write to you at asha@example.com.") == ["foreign_email"]


def test_tool_names_are_said_in_plain_words():
    assert plain_tool_words("Please check the number, or I can call list_my_orders.")[0] == \
        "Please check the number, or I can check your recent orders."
    assert plain_tool_words("I'll use the get_tracking tool for that.")[0] == "I'll check the tracking for that."
    assert output_filter("Try `escalate_to_human` if needed.") == ("Try a teammate if needed.", ["tool_name"])
    assert plain_tool_words("Your recent orders are below.") == ("Your recent orders are below.", False)


def test_redaction_masks_phones_and_removes_cards_and_emails():
    assert mask_phone("+91 98765 43210") == "••••••3210"
    line = "cust says 9876543210, card 4111 1111 1111 1111, mail x.y@gmail.com, order 10482, ₹1,299.00"
    assert redact(line) == "cust says ••••••3210, card [card], mail [email], order 10482, ₹1,299.00"
    assert redact("upi asha.k@okicici, aadhaar 2345 6789 0123") == "upi [upi id], aadhaar [id]"


def test_redaction_reaches_every_string_in_a_trace():
    trace = {"id": "adv-004", "turns": [{"reply": "ok"}], "messages": [{"role": "user", "content": "her number is 9876543210"}],
             "latency_s": 1.2}
    out = redact_obj(trace)
    assert out["messages"][0]["content"] == "her number is ••••••3210"
    assert out["latency_s"] == 1.2 and out["turns"] == [{"reply": "ok"}]
