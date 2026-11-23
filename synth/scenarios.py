"""Scenarios for synthetic conversations: a real train-partition order, the customer's hidden goal, and what the
customer knows.

Every conversation starts from a real order in the seeded world (db/seed.py), owned by a customer on the train
side of the split (config.partition_for). The goal and the knowledge are written from that order's rows, so the
simulated customer can only mention things that exist: their own items, roughly when they ordered, the date they
were promised. They never know carrier names, policies, or (unless the knowledge says so) the order number.

Order scenarios are the seed's catalog (db/seed.py, SCENARIOS). One more, policy_question, has no order: the
customer asks about a help-center section in their own words.
"""

import random
from dataclasses import dataclass
from datetime import date

import psycopg
from psycopg.rows import dict_row

from config import now, partition_for

ORDER_SCENARIOS = [
    "delivered_on_time", "not_yet_shipped", "in_transit", "delayed", "split_shipment", "cancelled_before_ship",
    "return_eligible", "return_in_progress", "refunded", "lost", "window_just_expired", "opened_electronics",
    "ship_then_cancel_request", "return_rejected", "delivered_not_received",
]
SCENARIOS = ORDER_SCENARIOS + ["policy_question"]

# Help-center pages a shopper would not ask about out of the blue, or that only point elsewhere.
POLICY_SKIP = ("_customer_words", "privacy#", "account-and-address#signing-in")
PAYMENT_WORDS = {"upi": "UPI", "card": "card", "wallet": "a wallet", "cod": "cash on delivery"}


@dataclass
class Scenario:
    name: str
    customer_id: int
    order_id: int | None          # None for policy_question
    goal: str                     # hidden from Nova; shown only to the simulator
    knowledge: list[str]          # what the customer knows; everything else they must ask for or do without
    facts: dict                   # the rows behind it, kept in the record's metadata for the verifiers
    intents: list[str]            # Bitext intents that fit the goal, for the opening message


def _when(d: date) -> str:
    """How a customer remembers a date: roughly, relative to today."""
    days = (now().date() - d).days
    if days <= 1:
        return "today" if days == 0 else "yesterday"
    if days <= 6:
        return f"{days} days ago"
    if days <= 13:
        return "last week"
    if days <= 45:
        return "a few weeks ago"
    return f"back in {d:%B}"


def _day(d: date) -> str:
    return f"{d:%A} {d.day} {d:%B}"


class World:
    """Read-only access to the seeded rows, as the database owner (the simulator side, not Nova's tools)."""

    def __init__(self, owner_url: str):
        self.conn = psycopg.connect(owner_url, autocommit=True, row_factory=dict_row)
        self.conn.execute("SET TIME ZONE 'Asia/Kolkata'")
        rows = self.conn.execute(
            "SELECT s.scenario, o.order_id, o.customer_id FROM scenarios s JOIN orders o USING (order_id)").fetchall()
        self.orders: dict[str, list[tuple[int, int]]] = {}
        for r in rows:
            if partition_for(r["customer_id"]) == "train":     # the eval side never reaches training data
                self.orders.setdefault(r["scenario"], []).append((r["order_id"], r["customer_id"]))
        self.train_customers = sorted({c for v in self.orders.values() for _, c in v})
        self.policy_chunks = [r for r in self.conn.execute("SELECT chunk_id, path FROM kb_chunks ORDER BY chunk_id")
                              if not any(s in r["chunk_id"] for s in POLICY_SKIP)]

    def order(self, order_id: int) -> dict:
        o = self.conn.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,)).fetchone()
        o["items"] = self.conn.execute(
            "SELECT i.line_no, p.name, p.category, i.opened, i.shipment_id FROM order_items i "
            "JOIN products p USING (product_id) WHERE order_id = %s ORDER BY line_no", (order_id,)).fetchall()
        o["shipments"] = self.conn.execute(
            "SELECT shipment_id, status, eta, delivered_at::date AS delivered FROM shipments WHERE order_id = %s "
            "ORDER BY shipment_id", (order_id,)).fetchall()
        o["returns"] = self.conn.execute(
            "SELECT return_id, status, reason, rejection_reason FROM returns WHERE order_id = %s", (order_id,)).fetchall()
        o["returned"] = [r["name"] for r in self.conn.execute(        # the items in those returns, not the whole order
            "SELECT DISTINCT p.name FROM return_items ri JOIN order_items i USING (order_id, line_no) "
            "JOIN products p USING (product_id) WHERE ri.order_id = %s ORDER BY 1", (order_id,))]
        o["refunds"] = self.conn.execute(
            "SELECT amount_inr, status FROM refunds WHERE order_id = %s", (order_id,)).fetchall()
        return o


def _names(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def _items(o: dict) -> str:
    return _names([i["name"] for i in o["items"]])


# Bitext intents whose questions make a fitting first message for each goal (synth/openers.py).
TRACK, REFUND_STATUS = ["track_order", "delivery_period"], ["track_refund", "get_refund"]
POLICY_INTENTS = {
    "returns": ["check_refund_policy", "get_refund"], "refunds": ["check_refund_policy", "track_refund"],
    "shipping": ["delivery_period", "delivery_options"], "delays": ["track_order", "complaint"],
    "cancellations": ["cancel_order", "check_cancellation_fee"], "payment": ["payment_issue", "check_payment_methods"],
    "cash": ["check_payment_methods"], "account": ["change_shipping_address", "edit_account"],
    "warranty": ["complaint", "get_refund"], "contacting": ["contact_human_agent", "contact_customer_service"],
    "order": ["track_order"],
}


def _goal(name: str, o: dict, rng: random.Random) -> tuple[str, list[str]]:
    """The customer's hidden goal for this order, and the Bitext intents that fit it."""
    items, first = _items(o), o["items"][0]["name"]
    eta = next((s["eta"] for s in o["shipments"] if s["eta"]), None)
    if name == "delivered_on_time":
        return rng.choice([(f"Check that your {items} order was delivered, and on what date.", TRACK),
                           (f"Get the tracking number of your {items} order; you want it for your records.",
                            ["track_order"])])
    if name == "not_yet_shipped":
        return rng.choice([(f"Cancel your {items} order: you found it cheaper elsewhere. Find out if you can, and how.",
                            ["cancel_order", "check_cancellation_fee"]),
                           (f"Change the delivery address of your {items} order to your office. Find out how.",
                            ["change_shipping_address"])])
    if name == "in_transit":
        return rng.choice([(f"Find out where your {items} order is and when it will arrive.", TRACK),
                           (f"Get the tracking number of your {items} order.", ["track_order"])])
    if name == "delayed":
        return (f"Your {items} order was supposed to arrive by {_day(eta)} and has not come. Find out where it is "
                "and what happens next.", ["track_order", "complaint", "delivery_period"])
    if name == "split_shipment":
        got = [i["name"] for i in o["items"] if any(s["shipment_id"] == i["shipment_id"] and s["status"] == "delivered"
                                                   for s in o["shipments"])]
        missing = [i["name"] for i in o["items"] if i["name"] not in got]
        return (f"You received only part of your order: {', '.join(got)} came, but {', '.join(missing)} did not. "
                "Find out where the missing item is.", ["track_order", "complaint"])
    if name == "cancelled_before_ship":
        return f"You cancelled your {items} order. Find out whether the money came back, and how much.", REFUND_STATUS
    if name == "return_eligible":
        why = rng.choice(["you changed your mind", "it is smaller than you expected", "you do not like the colour",
                          "it arrived damaged"])
        return (f"Return the {first} from your recent order, because {why}. Only say why when asked or when it fits.",
                ["get_refund", "change_order"] + (["complaint"] if "damaged" in why else []))
    returned = _names(o["returned"]) if o.get("returned") else items
    if name == "return_in_progress":
        return rng.choice([(f"You started a return for the {returned} from your order. Find out when it will be "
                            "picked up.", ["track_refund", "track_order"]),
                           (f"You started a return for the {returned} from your order. Find out when you will get "
                            "your money.", REFUND_STATUS)])
    if name == "refunded":
        return (f"You returned the {returned} from your order and have not noticed the refund. Find out whether it "
                "was sent, how much, and when.", REFUND_STATUS)
    if name == "lost":
        return (f"Your {items} order has not moved for more than a week. Find out what is going on and get someone "
                "to sort it out.", ["track_order", "complaint", "contact_human_agent"])
    if name == "window_just_expired":
        return (f"Return the {first}: you changed your mind about it. You are not sure exactly when it was delivered.",
                ["get_refund", "check_refund_policy"])
    if name == "opened_electronics":
        return (f"Return the {first}. You opened it and used it, and it works, but you do not like it.",
                ["get_refund", "check_refund_policy"])
    if name == "ship_then_cancel_request":
        return f"Cancel your {items} order; you do not need it any more.", ["cancel_order"]
    if name == "return_rejected":
        return f"Your return of the {first} was rejected. Find out why.", ["complaint", "get_refund"]
    if name == "delivered_not_received":
        return (f"Your {items} order shows as delivered, but you never got it. You reported it already. Find out what "
                "is happening.", ["complaint", "track_order"])
    raise ValueError(name)


def _knowledge(name: str, o: dict, rng: random.Random, knows_number: float) -> list[str]:
    know = [f"You ordered: {_items(o)}.", f"You ordered it {_when(o['placed_at'].date())}.",
            f"You paid by {PAYMENT_WORDS[o['payment_method']]}."]
    eta = next((s["eta"] for s in o["shipments"] if s["eta"]), None)
    if name == "delayed" and eta:
        know.append(f"It was supposed to arrive by {_day(eta)}.")
    if name == "cancelled_before_ship" and o.get("cancelled_at"):
        know.append(f"You cancelled it {_when(o['cancelled_at'].date())}, before it shipped. You never received or "
                    "returned anything.")
    happened = {
        "delivered_on_time": "It arrived and you have it.",
        "not_yet_shipped": "It has not been delivered yet.",
        "in_transit": "It has not arrived yet.", "delayed": "It has not arrived yet.",
        "lost": "It has not arrived.", "ship_then_cancel_request": "It has not arrived yet.",
        "return_eligible": "It arrived recently.", "opened_electronics": "It arrived recently and works fine.",
        "window_just_expired": "It arrived some time ago.",
        "delivered_not_received": "The app says delivered, but nothing reached you.",
        "return_rejected": "You sent a return request and it was rejected; you do not know why.",
    }
    if name in happened:
        know.append(happened[name])
    if rng.random() < knows_number:     # some customers have the order number to hand (the persona decides how many)
        know.append(f"Your order number is {o['order_id']}. Give it only if asked for it.")
    return know


def policy_topic(world: World, rng: random.Random) -> tuple[dict, str, list[str]]:
    """A random help-center section: (chunk, topic in words, fitting Bitext intents)."""
    chunk = rng.choice(world.policy_chunks)
    prefix = chunk["chunk_id"].split("#")[0].split("-")[0]
    return chunk, chunk["path"].replace(" › ", ": "), POLICY_INTENTS.get(prefix, ["check_refund_policy"])


def pick(name: str, world: World, rng: random.Random, knows_number: float = 0.4) -> Scenario:
    """One scenario on a random train-partition order (or, for policy_question, a random train customer).
    knows_number: the chance the customer has the order number to hand."""
    if name == "policy_question":
        chunk, topic, intents = policy_topic(world, rng)
        cid = rng.choice(world.train_customers)
        return Scenario(name, cid, None,
                        goal=f"Find out about this, asked the way a shopper would ask it: {topic}.",
                        knowledge=["You have no particular order in mind; this is a general question."],
                        facts={"chunk_id": chunk["chunk_id"]}, intents=intents)
    order_id, cid = rng.choice(world.orders[name])
    o = world.order(order_id)
    facts = {"order_id": order_id, "status": o["status"], "items": [i["name"] for i in o["items"]],
             "payment_method": o["payment_method"],
             "shipments": [{k: str(v) for k, v in s.items() if v is not None} for s in o["shipments"]],
             "returns": [{k: str(v) for k, v in r.items() if v is not None} for r in o["returns"]]}
    goal, intents = _goal(name, o, rng)
    return Scenario(name, cid, order_id, goal, _knowledge(name, o, rng, knows_number), facts, intents)
