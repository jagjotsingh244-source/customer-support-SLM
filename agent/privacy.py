"""Personal data in replies and in logs: the patterns, the output filter, and redaction.

Privacy is handled in three places, in this order:

1. At the source. The tools return only what an answer needs: the delivery city, never the street, the
   pincode, the phone or the email; no card details at all (agent/tools_v0.py SQL, tests/test_guardrails.py).
   Data the model never sees, it cannot repeat.
2. In the reply. output_filter() runs on every reply before the customer sees it. A phone number, a card-like
   number or an email address that is not the customer's own replaces the whole reply with a safe one, and the
   hit is logged. Nova has no tool that returns any of these, so one in a reply came from the customer's message
   or was made up, and repeating either is wrong. Tool names ("call list_my_orders") are rewritten into plain
   words: they are Nova's internals, not something a customer can do.
   minimise() trims what the tools return before the model reads it (unneeded ids, times of day).
3. In the logs. redact() masks the same patterns in anything written to a trace or a log line, so traces can be
   shared and kept (scripts/prune_traces.py deletes raw traces after the retention period).

The patterns are tested against the strings that must pass: 5-digit order numbers, tracking numbers, prices,
dates, ticket and proposal ids, pincodes, refund amounts (tests/test_privacy.py).
"""

import re

# A 10-digit Indian mobile number (starts 6-9), alone or with +91 / 0, and with one space or dash in the middle.
# Not inside a longer number or a price: no word character or ₹ before, no digit or ".5"/",5" after.
_START, _END = r"(?<![\w₹])(?<!\d[.,])", r"(?!\w)(?![.,]\d)"
# The ten digits may be split by single spaces, dots or dashes anywhere ("987 654 3210", "+91 9876 543 210"),
# and the prefix may be +91, 91 or 0 ("919876543210").
PHONE = re.compile(_START + r"(?:\+?91[\s.-]?|0)?[6-9](?:[\s.-]?\d){9}" + _END)
# 13 to 19 digits, in groups separated by single spaces or dashes; a card only if the Luhn check passes, so a
# long reference number is not taken for one.
CARD_LIKE = re.compile(_START + r"\d(?:[ -]?\d){12,18}" + _END)
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
UPI_ID = re.compile(r"\b[\w.-]{2,}@(?:ok)?[a-z]{2,}\b(?!\.[\w-])", re.I)     # name@okicici; no dot after the @
AADHAAR = re.compile(r"(?<![\w.,])[2-9]\d{3}[\s-]\d{4}[\s-]\d{4}(?![\w.,])")   # written in groups, as on the card
PAN = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
IFSC = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")
# A reply that asks the customer for a secret. Nova never needs one (help center, "Payment safety"); a planted
# carrier name made SFT-2a ask for a card number and CVV (evals/reports/05a_attacks.md). Warnings pass.
SECRET = r"(otp|one[- ]time password|cvv|cvc|upi pin|\bpin\b|password|card number|card details|bank details|" \
         r"account number|ifsc|aadhaar|pan number)"
ASKS = re.compile(r"\b(share|send|give|provide|tell|enter|type|confirm|need|require|what is|what's)\b[^.!?\n]{0,40}"
                  + SECRET, re.I)
WARNS = re.compile(r"\b(never|do not|don't|won't|will not|not|no one|nobody)\b", re.I)
# The one place a customer does enter a secret: bank details for a cash-on-delivery refund, on the order page
# (help center, "Cash on delivery"). "You need to add your bank details on the order page" sends them there, it
# does not ask for them in chat; it was blanked in three golden cases. Only bank details, and only the order page.
ORDER_PAGE = re.compile(r"\bbank details\b[^.!?\n]{0,40}\bon (the|your) order page\b", re.I)

TOOL_NAMES = {   # what each tool means to a customer
    "list_my_orders": ("check your recent orders", "your recent orders"),
    "get_order_status": ("check the order", "the order details"),
    "get_tracking": ("check the tracking", "the tracking"),
    "search_help_center": ("check the help center", "the help center"),
    "propose_return": ("set up the return", "the return"),
    "escalate_to_human": ("connect you with a teammate", "a teammate"),
}
_NAMES = "|".join(TOOL_NAMES)
TOOL_CALL = re.compile(r"\b(?:call(?:ing)?|us(?:e|ing)|run(?:ning)?)\s+(?:the\s+)?`?(" + _NAMES + r")`?(?:\s+tool)?\b", re.I)
TOOL_NAME = re.compile(r"(?:\bthe\s+)?`?\b(" + _NAMES + r")\b`?(?:\s+(?:tool|function|api))?", re.I)
# The source labels the guard puts on tool results (agent/guardrails.py SOURCES), said the same way.
SOURCE_NAMES = {"orders_db": "our order records", "help_center": "the help center",
                "returns_service": "the returns process", "ticket_system": "our support team"}
SOURCE_NAME = re.compile(r"(?:\bthe\s+)?`?\b(" + "|".join(SOURCE_NAMES) + r")\b`?", re.I)
# Any other snake_case word is a field name or a status code from a tool result ("awaiting_bank_details",
# "line_no", "opened_not_faulty"): said as words, without the quotes or backticks around it.
SNAKE = re.compile(r"[\"'`]?\b([a-z]+(?:_[a-z0-9]+)+)\b[\"'`]?", re.I)

SAFE_REPLY = "I can't share those details here. Is there anything else about your order I can help with?"


def luhn(digits: str) -> bool:
    total, parity = 0, len(digits) % 2
    for i, ch in enumerate(digits):
        d = int(ch)
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def cards_in(text: str) -> list[str]:
    return [m for m in CARD_LIKE.findall(text) if luhn(re.sub(r"\D", "", m))]


def mask_phone(phone: str) -> str:
    return "••••••" + re.sub(r"\D", "", phone)[-4:]


def personal_data(text: str, own_email: str | None = None) -> list[str]:
    """Kinds of personal data in the text: "phone", "card_like", "foreign_email", "upi_id", "id_number"."""
    hits = []
    if PHONE.search(text):
        hits.append("phone")
    if cards_in(text):
        hits.append("card_like")
    own = (own_email or "").lower()
    if any(e.lower() != own for e in EMAIL.findall(text)):
        hits.append("foreign_email")
    if UPI_ID.search(EMAIL.sub("", text)):
        hits.append("upi_id")
    if AADHAAR.search(text) or PAN.search(text) or IFSC.search(text):
        hits.append("id_number")
    return hits


def asks_for_secret(text: str) -> bool:
    """A sentence that asks for an OTP, CVV, PIN, password, card or bank details, and is not a warning."""
    return any(ASKS.search(s) and not WARNS.search(s) and not _to_order_page(s)
               for s in re.split(r"(?<=[.!?])\s+|\n+", text or ""))


def _to_order_page(sentence: str) -> bool:
    """The sentence points to the order page for bank details, and asks for no other secret."""
    return bool(ORDER_PAGE.search(sentence)) and not ASKS.search(ORDER_PAGE.sub("", sentence))


def plain_tool_words(reply: str) -> tuple[str, bool]:
    """The reply with tool names said in a customer's words: "I can call list_my_orders" -> "I can check your
    recent orders". The 2B models picked the phrase up from the tools' own error text (evals/reports/04_comparison.md)."""
    new = TOOL_CALL.sub(lambda m: TOOL_NAMES[m.group(1).lower()][0], reply)
    new = TOOL_NAME.sub(lambda m: _cased(m, TOOL_NAMES[m.group(1).lower()][1]), new)
    new = SOURCE_NAME.sub(lambda m: _cased(m, SOURCE_NAMES[m.group(1).lower()]), new)
    new = SNAKE.sub(lambda m: _cased(m, m.group(1).replace("_", " ")), new)
    return new, new != reply


def _cased(m: re.Match, words: str) -> str:
    """The replacement, capitalised when what it replaces was ("The list_my_orders function" -> "Your recent...")."""
    return words[:1].upper() + words[1:] if m.group(0).lstrip("\"'`")[:1].isupper() else words


def output_filter(reply: str, own_email: str | None = None) -> tuple[str, list[str]]:
    """(the reply to show, what was found). Personal data replaces the reply; tool names are reworded."""
    hits = personal_data(reply, own_email) + (["asks_for_secret"] if asks_for_secret(reply) else [])
    if hits:
        return SAFE_REPLY, hits
    reply, renamed = plain_tool_words(reply)
    return reply, ["tool_name"] if renamed else []


# Logs -------------------------------------------------------------------------------------------------

def redact(text: str) -> str:
    """The text as it may be logged: phones masked to the last four digits, cards and emails replaced."""
    text = EMAIL.sub("[email]", text)
    text = UPI_ID.sub("[upi id]", text)
    text = CARD_LIKE.sub(lambda m: "[card]" if luhn(re.sub(r"\D", "", m.group())) else m.group(), text)
    for rule in (AADHAAR, PAN, IFSC):                # after cards: an Aadhaar's groups also sit inside a card
        text = rule.sub("[id]", text)
    return PHONE.sub(lambda m: mask_phone(m.group()), text)


def redact_obj(x):
    """redact() applied to every string in a trace (dicts, lists, strings; other values as they are)."""
    if isinstance(x, str):
        return redact(x)
    if isinstance(x, dict):
        return {k: redact_obj(v) for k, v in x.items()}
    if isinstance(x, list):
        return [redact_obj(v) for v in x]
    return x


# Minimising what the model reads ----------------------------------------------------------------------

# Fields no answer needs (evals/reports/05c_privacy_audit.md): internal ids nobody quotes, and when the customer
# added bank details (the refund's status already says whether they are awaited). Timestamps whose time of day no
# answer needs are cut to the date; delivered_at and last_scan_at keep the time (a "never got it" dispute and
# the lost-parcel rule need it).
DROP = {"return_id", "refund_id", "shipment_id", "bank_details_added_at"}
TO_DATE = {"placed_at", "cancelled_at", "proposed_at", "picked_up_at", "rejected_at", "initiated_at", "completed_at"}


def minimise(result):
    """A tool result as the model should see it: unneeded fields dropped, times of day cut where no answer needs
    them. Applied by the guard layer (agent/guardrails.py Guard.tool_content); the tools stay as they are, so
    earlier runs can be repeated exactly."""
    if isinstance(result, dict):
        out = {}
        for k, v in result.items():
            if k in DROP:
                continue
            out[k] = str(v)[:10] if k in TO_DATE and v is not None else minimise(v)
        return out
    if isinstance(result, list):
        return [minimise(v) for v in result]
    return result
