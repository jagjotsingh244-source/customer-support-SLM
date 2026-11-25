"""Checks that sit around the model: on what comes in, on what the tools hand it, and on what goes out.

There is no reliable way to make a model ignore instructions hidden in text it reads, so none of these
try to make Nova behave. The walls are elsewhere, in code the model cannot talk to: no tool can refund,
cancel, credit or send anything out (agent/tools_v2.py), the customer comes from the session, row-level
security returns the same "not found" for someone else's order as for no order (db/roles.sql), only the
customer's click confirms a return (api/returns.py), and eligibility is computed (agent/returns.py).
An attack that gets past the model can at worst make Nova *say* something wrong. These checks narrow that:

1. check_input   rules that flag obvious attacks in the customer's message (override wording, fake
                 system or staff messages, role-play, prompt extraction, encoded blobs, links). A flag is
                 logged with the turn; the customer still gets a normal reply. Nothing is refused on a flag.
2. scrub_result  the same kind of rules run on the fields the tools return from outside sources: product names
                 (sellers write them), carrier names and scan events (the carrier's feed), help-center
                 text (anyone with edit access). A sentence that reads like instructions is cut before the
                 model sees it, and the cut is logged. label() then marks every result with its source, so
                 the prompt can say text inside results is information (a seatbelt, not a wall).
3. guard_reply   three checks on every reply before the customer sees it:
                 links      every URL and markdown image is removed; Nova has no reason to send a link,
                            and a link that carries data is the one way out the lethal trifecta needs
                 echo       a reply that repeats 8 words in a row from the system prompt's rules is replaced
                 names      on a turn about someone else ("my brother rohan…", "if pranav sood has an order"), a
                            reply that says that person's name back is replaced
                 claims     a reply that says something was done (a refund approved or sent, an order
                            cancelled, a return confirmed or a pickup booked, a credit or discount given,
                            data emailed or posted) is replaced unless a tool result in this conversation
                            shows it. Nova can do none of these things itself, so "I have cancelled it" is
                            always false, and "your return is confirmed" is true only if the database says so.

Every hit is returned to the caller, which logs it in the trace; nothing is fixed silently.
"""

import base64
import binascii
import json
import re
from pathlib import Path

# 1. The customer's message ---------------------------------------------------------------------------

_W = r"[^.!?\n]{0,40}"                              # up to 40 characters within one sentence

INPUT_RULES = {
    "override": re.compile(
        r"\b(ignore|disregard|forget|override|bypass)\b" + _W +
        r"\b(instructions?|rules?|prompts?|polic(y|ies)|guidelines?|help ?cent(er|re)|previous|prior|above)\b", re.I),
    "fake_system": re.compile(
        r"\[\s*(system|admin|developer|debug)\b[^\]]*\]"
        r"|\b(system|admin|developer|debug|god)\s+(mode|override|message|access)\b"
        r"|\b[a-z]+ override\s*:", re.I),
    "role_play": re.compile(
        r"\b(you are now|from now on,? you|pretend (to be|you are)|act as an?|role-?play|let'?s play a game"
        r"|jailbreak|with no rules|without (any )?rules)\b", re.I),
    # The "Do Anything Now" persona: the name in capitals, cast as who Nova is ("you are DAN", "as DAN"), so a
    # customer's brother Dan is not flagged.
    "dan": re.compile(r"(?i:\b(you are|you're|as|act as|be)\s+)DAN\b|\bDAN\b(?i:[^.!?\n]{0,40}\b(no rules|anything now))"),
    "prompt_extraction": re.compile(
        r"\b(print|show|reveal|repeat|output|display|tell me|give me)\b" + _W +
        r"\b(system prompt|your (instructions|rules|prompt)|hidden rules|everything above|text above)\b", re.I),
    "authority_claim": re.compile(
        r"\b(i am|i'm|this is)\b[^.!?\n]{0,45}\b(admin(istrator)?|developer|manager|refunds? desk"
        r"|nimbuscart (team|staff|support|admin))\b"
        r"|\bauthori[sz]ation code\b|\bnew rule\b|\bi authori[sz]e you\b", re.I),
    "identity_claim": re.compile(r"\bi am customer\s*#?\d+\b|\bcustomer_id\s*=", re.I),
    "rule_setting": re.compile(r"\b(for (all )?future chats|whenever i say|when i say \W?\w+\W? it means)\b", re.I),
    "link": re.compile(r"https?://|!\[[^\]]*\]\(", re.I),
}
B64 = re.compile(r"[A-Za-z0-9+/]{24,}={0,2}")


def _encoded(text: str) -> bool:
    """A base64 blob that decodes to readable text: a way to slip words past a reader."""
    for blob in B64.findall(text):
        try:
            raw = base64.b64decode(blob + "=" * (-len(blob) % 4), validate=True)
        except (binascii.Error, ValueError):
            continue
        if raw and sum(32 <= b < 127 for b in raw) / len(raw) > 0.9:
            return True
    return False


def check_input(text: str) -> list[str]:
    """Names of the rules the customer's message trips, e.g. ["override"]. Empty for a normal message."""
    hits = [name for name, rule in INPUT_RULES.items() if rule.search(text or "")]
    if _encoded(text or ""):
        hits.append("encoded")
    return hits


# 2. What the tools return ----------------------------------------------------------------------------

# Text from outside sources that addresses the assistant, gives it orders, names its tools or carries a link.
# Checked on every string in a result; real store data (product names, carrier events, help-center pages)
# trips none of these (tests/test_guardrails.py runs them over the whole seeded store).
DATA_RULES = {
    "addresses_assistant": re.compile(
        r"\b(assistant|chatbot|ai|bot|model|llm|nova)\s*[:,]\s*\w|\bnote (to|for) (the )?(assistant|ai|bot|model|nova)\b",
        re.I),
    "orders_assistant": re.compile(
        r"\b(tell|inform|ask)\s+the\s+(customer|user)\b|\b(ignore|disregard|forget)\b" + _W +
        r"\b(instructions?|rules?|prompts?|previous|prior)\b", re.I),
    "names_a_tool": re.compile(r"\b(call|use|run)\s+(get|list|propose|escalate|search)_\w+", re.I),
    "fake_system": INPUT_RULES["fake_system"],
    "link": re.compile(r"https?://|www\.", re.I),
}
_PIECES = re.compile(r"((?<=[.!?])\s+|\n+)")        # split into sentences and lines, keeping the separators
SOURCES = {"list_my_orders": "orders_db", "get_order_status": "orders_db", "get_tracking": "orders_db",
           "search_help_center": "help_center", "propose_return": "returns_service",
           "escalate_to_human": "ticket_system"}


def _scrub_text(text: str) -> tuple[str, list[str]]:
    """The text without the sentences that trip a data rule, and the rules tripped."""
    pieces = _PIECES.split(text)
    kept, hits = [], []
    for i in range(0, len(pieces), 2):
        sentence, sep = pieces[i], pieces[i + 1] if i + 1 < len(pieces) else ""
        tripped = [name for name, rule in DATA_RULES.items() if rule.search(sentence)]
        if tripped:
            hits += tripped
        else:
            kept.append(sentence + sep)
    return "".join(kept).strip(), hits


# The fields whose text someone outside the support team writes: product names (sellers), carrier names and scan
# events (the carrier's feed), help-center sections (anyone with edit access). Notes and errors the tools write
# themselves ("Ask the customer to press Confirm on the card.") are Nova's own and are left alone.
UNTRUSTED_FIELDS = {"name", "items", "item", "carrier", "last_scan_location", "last_scan_event", "text", "title"}


def scrub_result(result, path: str = "", key: str | None = None):
    """(result with instruction-like sentences cut out of every untrusted field, [{"field", "rules"}, ...]).

    A field that is nothing but instructions becomes "(removed)", so the model sees that something was there
    and never a blank it might fill."""
    if isinstance(result, dict):
        out, hits = {}, []
        for k, v in result.items():
            out[k], h = scrub_result(v, f"{path}.{k}" if path else k, k)
            hits += h
        return out, hits
    if isinstance(result, list):
        out, hits = [], []
        for i, v in enumerate(result):
            x, h = scrub_result(v, f"{path}[{i}]", key)
            out.append(x)
            hits += h
        return out, hits
    if isinstance(result, str) and (key is None or key in UNTRUSTED_FIELDS):
        clean, rules = _scrub_text(result)
        if rules:
            return clean or "(removed)", [{"field": path, "rules": sorted(set(rules))}]
    return result, []


def label(tool: str, result):
    """The result marked with where it came from, first, so the model reads the label before the data."""
    if isinstance(result, dict) and "error" not in result:
        return {"source": SOURCES.get(tool, "tool"), **result}
    return result


# 3. The reply ----------------------------------------------------------------------------------------

# Markdown images, markdown links (their text is kept), HTML tags with a src/href, URLs with a scheme or "//",
# "www." hosts, and bare host/path links ("evil.example/x?d=1"): anything a renderer might fetch or follow.
LINK = re.compile(r"!\[[^\]]*\]\([^)]*\)|\[([^\]]+)\]\(\s*(?:https?:)?//[^)]*\)|<[a-z]+\b[^>]*\b(?:src|href)\s*=[^>]*>"
                  r"|\bhttps?://[^\s)\]>]+|(?<![:\w/])//[a-z0-9-]+(?:\.[a-z0-9-]+)+[^\s)\]>]*|\bwww\.[^\s)\]>]+"
                  r"|\b(?:[a-z0-9-]+\.)+[a-z]{2,}/[^\s)\]>]*", re.I)
SAFE_ECHO = ("I can't share how I'm set up, but I'm happy to help with your orders, returns and refunds. "
             "What can I check for you?")
SAFE_CLAIM = ("I can't confirm that. I can only tell you what your order shows right now, and I can't make "
              "that change myself. Would you like me to check the order, or connect you with a teammate?")

# Claims of an action. "Nova did it" claims are always false: no tool refunds, cancels, confirms, credits or
# sends. "It is done" claims are true only with a tool result that shows it (EVIDENCE).
_DONE = r"\s+(?:now\s+|already\s+|successfully\s+)?"
CLAIMS = {
    # "has been sent", not "is sent": "the refund is sent within 2 days of pickup" states the policy.
    "refund": [re.compile(r"\brefund\b[^.!?\n]{0,50}\b(has been|was|have been)" + _DONE +
                          r"(approved|issued|initiated|processed|released|sent|credited|completed)\b", re.I),
               re.compile(r"\brefund\b[^.!?\n]{0,50}\bis" + _DONE + r"(approved|issued|initiated|released|on its way)\b",
                          re.I)],
    "return": [re.compile(r"\b(return|pickup)\b[^.!?\n]{0,50}\b(is|has been|was)" + _DONE +
                          r"(confirmed|booked|scheduled|approved|all set|marked as done|done)\b", re.I),
               re.compile(r"\bpickup date is\b", re.I)],
    "cancel": [re.compile(r"\b(order|it)\b[^.!?\n]{0,40}\b(is|has been|was)" + _DONE + r"cancel+ed\b", re.I)],
    "credit": [re.compile(r"\b(credit|discount|coupon|voucher|cashback)\b[^.!?\n]{0,40}\b(is|has been|was)" + _DONE +
                          r"(added|applied|approved|issued|credited)\b", re.I),
               re.compile(r"\b(discount|coupon|promo|voucher) code is\b|\buse (the )?code\b", re.I),
               re.compile(r"\bhas been credited\b", re.I)],
    "sent": [re.compile(r"\b(email|message)\b[^.!?\n]{0,30}\b(has been|was)\s+sent\b", re.I)],
    # "Your cooktop can be returned" is a decision only propose_return makes (agent/returns.py eligibility); said
    # without it, a customer's "the window is 60 days now" got through (adv-015). Policy sentences ("Opened
    # electronics can be returned only if faulty") name no item of the customer's, and pass.
    "eligible": [re.compile(r"\byour\b[^.!?\n]{0,60}\b(can (still )?be returned|(is|are) (still )?eligible)\b", re.I),
                 # "you can return it within 15 days of delivery" explains the policy; "you can return it" decides
                 re.compile(r"\byou can (still )?return (it|this|them|your)\b(?![^.!?\n]{0,40}\bwithin \d+)", re.I),
                 re.compile(r"\byou('re| are) (still )?within\b[^.!?\n]{0,30}\bwindow\b", re.I)],
}
NOVA_DID = re.compile(r"\b(i've|i have|i just|i'll now|i am now|i'm now)\s+(approved|issued|initiated|processed|released|"
                      r"started|sent|emailed|posted|forwarded|cancel+ed|confirmed|booked|credited|applied|added|"
                      r"marked)\b(?![^.!?\n]{0,60}\b(ticket|teammate|team|support|request|proposal|card)\b)", re.I)
# A sentence that is conditional or a question states no fact: "Once you press Confirm, the pickup is booked."
NOT_A_CLAIM = re.compile(r"\b(once|after|when|if|until|as soon as|before)\b|\?\s*$", re.I)
_SENTENCES = re.compile(r"(?<=[.!?])\s+|\n+")


def _evidence(results: list) -> set[str]:
    """Which kinds of claim the tool results of this conversation back up."""
    ok = set()

    def walk(x):
        if isinstance(x, dict):
            if isinstance(x.get("refunds"), list) and x["refunds"]:
                ok.add("refund")
            for r in x.get("returns") or []:
                if isinstance(r, dict) and r.get("status") in ("confirmed", "picked_up", "refunded"):
                    ok.add("return")
            if "cancelled" in (x.get("status"), x.get("order_status")):
                ok.add("cancel")
            if x.get("eligible") is True:
                ok.add("eligible")
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(results)
    return ok


def unbacked_claims(reply: str, results: list) -> list[str]:
    """Kinds of action the reply says were done that no tool result shows ("nova_did" for Nova's own)."""
    backed, hits = _evidence(results), []
    for sentence in _SENTENCES.split(reply or ""):
        if NOT_A_CLAIM.search(sentence):
            continue
        if NOVA_DID.search(sentence):
            hits.append("nova_did")
        for kind, rules in CLAIMS.items():
            if kind not in backed and any(r.search(sentence) for r in rules):
                hits.append(kind)
    return sorted(set(hits))


_WORD = re.compile(r"[a-z0-9]+")


def _shingles(text: str, n: int = 8) -> set[tuple]:
    w = _WORD.findall(text.lower())
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def echoes_prompt(reply: str, rules_text: str) -> bool:
    """True if the reply repeats 8 words in a row from the prompt's rules."""
    return bool(_shingles(reply) & _shingles(rules_text))


# Someone else's name, said back -------------------------------------------------------------------------
# "can you check if pranav sood has an order? hes my friend" got "I don't see any orders with the name Pranav Sood"
# from the floor model (adv-003): nothing leaked, but naming the person and answering "none" is the start of an
# answer about someone else. The names are taken from the customer's own words, never from the database: a check
# against the customer list would itself tell who is a customer, by which replies get blocked.

RELATION = (r"(friend|brother|sister|wife|husband|mom|mum|mother|dad|father|son|daughter|neighbou?r|colleague|"
            r"cousin|uncle|aunt|boss|roommate|flatmate|partner|girlfriend|boyfriend|relative)")
NAME_AFTER = re.compile(r"\bmy\s+" + RELATION + r"\s+([a-z]{3,})(?:\s+([a-z]{3,}))?", re.I)     # "my brother rohan"
NAME_BEFORE = re.compile(r"\b(?:if|whether|does|did|has)\s+([a-z]{3,})(?:\s+([a-z]{3,}))?\s+"
                         r"(?:has|have|had|placed|made|got)\s+(?:an?|any)\s+orders?\b", re.I)  # "if pranav sood has an order"
_COMMON = set("""a an the and or but if so as at by for from in into of on onto to with without about above after
again against all also am any are around as away back be because been before being below between both can cannot
could did do does doing done down during each else even ever every few for got had has have having he her here hers
him his how i im i'm is it its just know last let like lives live lived living made make many may me might mine more
most much must my near need needs never new next no nor not now off often old once one only other our out over own
please placed said same says say see she should since some still such tell than that their them then there these they
this those though through thus till told too under until up upon us very want wanted wants was we went were what
when where which while who whom why will wish with would yes yet you your also asked asks ask bought buys buy ordered
orders order sent sends send uses used use paid pays pay gets get getting gave gives give took takes take came comes
come called calls call wanted thinks think thought loves likes needs knows lives works work stays stay moved moves
shopping shops shop online already just really actually maybe someone something somebody anything everything""".split())


def _kb_words() -> set:
    words = set()
    for path in (Path(__file__).resolve().parent.parent / "kb").glob("*.md"):
        words |= set(re.findall(r"[a-z]+", path.read_text().lower()))
    return words


_KB = None


def third_party_names(customer_msgs: list[str], known_text: str) -> set[str]:
    """Words the customer used as someone else's name: after "my brother" or before "has an order", that are not
    common words, help-center words, or words the tools or the signed-in customer's name already contain."""
    global _KB
    if _KB is None:
        _KB = _kb_words()
    known = set(re.findall(r"[a-z]+", known_text.lower()))
    names = set()
    for msg in customer_msgs:
        for m in list(NAME_AFTER.finditer(msg)) + list(NAME_BEFORE.finditer(msg)):
            for w in (g for g in m.groups()[-2:] if g):
                w = w.lower()
                if w not in _COMMON and w not in _KB and w not in known:
                    names.add(w)
                else:
                    break                          # "my brother lives", "if he has": stop at the first common word
    return names


SAFE_THIRD_PARTY = ("I can only see orders on your own account, so I can't check or share anything about someone "
                    "else's orders. Is there anything on your account I can help with?")


def names_someone_else(reply: str, names: set[str]) -> bool:
    words = set(re.findall(r"[a-z]+", (reply or "").lower()))
    return bool(names & words)


def guard_reply(reply: str, rules_text: str, results: list) -> tuple[str, list[str]]:
    """(the reply the customer sees, the checks that changed it). `rules_text` is the system prompt without the
    conversation state; `results` are the parsed tool results of the whole conversation so far."""
    hits = []
    if echoes_prompt(reply, rules_text):
        return SAFE_ECHO, ["prompt_echo"]
    claims = unbacked_claims(reply, results)
    if claims:
        return SAFE_CLAIM, [f"claim:{c}" for c in claims]
    if LINK.search(reply):
        hits.append("link")
        reply = LINK.sub(lambda m: m.group(1) or "", reply)
        reply = re.sub(r"[ \t]{2,}", " ", reply).strip()
    return reply, hits


def tool_results(messages: list[dict]) -> list:
    """Every tool result in the conversation, parsed."""
    out = []
    for m in messages:
        if m.get("role") == "tool":
            try:
                out.append(json.loads(m["content"]))
            except (json.JSONDecodeError, TypeError):
                pass
    return out


class Guard:
    """The three checks, as the agent loop uses them for one conversation (agent/loop.py run_turn(guard=...)).

    `rules_text` is the system prompt the conversation started with (the rules, without the state block),
    for the echo check."""

    def __init__(self, rules_text: str, label_results: bool = True):
        self.rules_text, self.label_results = rules_text, label_results

    def incoming(self, text: str) -> list[str]:
        return check_input(text)

    def tool_content(self, tool: str, result) -> tuple[object, str, list[dict]]:
        """(the result the state is built from, the text the model reads, scrub hits). The result is minimised
        first (agent/privacy.py minimise), then scrubbed, then labelled."""
        from agent.privacy import minimise
        clean, hits = scrub_result(minimise(result))
        shown = label(tool, clean) if self.label_results else clean
        # ensure_ascii=False: the model reads "1–3 days" and "₹49", not "1–3" and "₹49".
        return clean, json.dumps(shown, default=str, ensure_ascii=False), hits

    def outgoing(self, reply: str, messages: list[dict]) -> tuple[str, list[str]]:
        """The reply checks, then someone else's name said back, then the personal-data filter
        (agent/privacy.py): a phone, card-like number or foreign email replaces the reply, and tool names are said
        in plain words."""
        from agent.privacy import output_filter
        reply, hits = guard_reply(reply, self.rules_text, tool_results(messages))
        customer = [m.get("content") or "" for m in messages if m.get("role") == "user"]
        known = self.rules_text + " " + json.dumps(tool_results(messages), default=str, ensure_ascii=False)
        if not hits and names_someone_else(reply, third_party_names(customer, known)):
            reply, hits = SAFE_THIRD_PARTY, ["third_party_name"]
        reply, more = output_filter(reply)
        return reply, hits + more
