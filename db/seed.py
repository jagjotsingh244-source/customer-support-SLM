"""Seed NimbusCart's world: 500 customers, 60 products and 3,000 orders.

Every order is built from a named scenario. About a third carry a deliberate
problem (late, lost, split, returned, rejected...), far more than a real store,
because Nova is judged on the bad days and the evals need enough of each.
Everything comes from config.NOW and config.SEED, so the same command always
builds the same world.

Run from the repo root (needs Postgres from docker-compose.yml):
    uv run python -m db.seed

It reloads db/schema.sql, inserts everything, writes db/scenarios.csv and runs
db/checks.sql. It exits non-zero if any check returns rows.
"""

import csv
import datetime as dt
import os
import random
import re
import sys
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

import psycopg
from faker import Faker

from config import IST, SEED, WINDOW_DAYS, now, partition_for

NOW = now()
TODAY = NOW.date()
DB_URL = os.environ.get("DB_URL", "postgresql://nimbus:nimbus@localhost:5433/nimbus")
HERE = Path(__file__).parent

N_CUSTOMERS, N_ORDERS, FIRST_ORDER_ID = 500, 3000, 10001
MIN_EVAL_ORDERS = 5          # every scenario needs at least this many orders on eval customers
FAILED_PAYMENT_SHARE = 0.08  # customers with a debited-but-failed payment (no order)

rng = random.Random(SEED)
fake = Faker("en_IN")
fake.seed_instance(SEED)

# Scenario catalog: share of the 3,000 orders, and why it is hard for Nova.
SCENARIOS = {
    "delivered_on_time":        0.33,  # baseline; most questions are simple
    "not_yet_shipped":          0.03,  # placed or packed: free cancel, address change
    "in_transit":               0.15,  # must quote the ETA, not invent one
    "delayed":                  0.08,  # ETA already passed; must not promise a new date
    "split_shipment":           0.06,  # one box delivered, one not
    "cancelled_before_ship":    0.05,  # refund timing depends on payment method
    "return_eligible":          0.08,  # inside the return window; a return can be proposed
    "return_in_progress":       0.04,  # pickup and refund status questions
    "refunded":                 0.03,  # "where is my money?" after it was sent
    "lost":                     0.03,  # no scan for 7+ days; should escalate
    "window_just_expired":      0.03,  # 1-3 days past the window
    "opened_electronics":       0.03,  # returnable only if faulty
    "ship_then_cancel_request": 0.02,  # too late to cancel; explain the return route
    "return_rejected":          0.02,  # "why was my return rejected?"
    "delivered_not_received":   0.02,  # marked delivered, customer says no; ticket open
}

# Catalog -----------------------------------------------------------------------

@dataclass(frozen=True)
class Product:
    id: int
    name: str
    category: str
    price: Decimal
    returnable: bool = True
    warranty_months: int = 0


_CATALOG = {
    "electronics": [
        ("Wireless earbuds", 1999, False, 12), ("Wired earphones", 499, False, 6),
        ("Neckband earphones", 1299, False, 12), ("Bluetooth speaker", 2499, True, 12),
        ("Mini portable speaker", 1299, True, 6), ("Power bank 10000mAh", 1499, True, 6),
        ("Power bank 20000mAh", 2299, True, 12), ("Smartwatch", 3999, True, 12),
        ("Fitness band", 1799, True, 12), ("Wireless mouse", 699, True, 12),
        ("Mechanical keyboard", 3499, True, 12), ("USB-C hub", 1899, True, 12),
        ("1080p webcam", 2799, True, 12), ("Wi-Fi router", 2999, True, 24),
        ("32GB pen drive", 449, True, 24), ("1TB external SSD", 6999, True, 36),
        ("10-inch tablet", 14999, True, 12), ("Noise-cancelling headphones", 7999, True, 12),
        ("Beard trimmer", 1599, False, 12), ("Smart LED bulb", 599, True, 12),
    ],
    "home": [
        ("Steel water bottle", 399, True, 0), ("Desk lamp", 499, True, 6),
        ("Non-stick frying pan", 1199, True, 12), ("3L pressure cooker", 1899, True, 24),
        ("Cotton bedsheet set", 999, True, 0), ("Bath towel set", 799, True, 0),
        ("Ceramic dinner set", 2499, True, 0), ("Electric kettle", 1299, True, 12),
        ("Mixer grinder", 3499, True, 24), ("Wall clock", 699, True, 6),
        ("Storage container set", 599, True, 0), ("Cushion covers", 449, True, 0),
        ("Table fan", 2199, True, 24), ("Air fryer", 5999, True, 24),
        ("Induction cooktop", 2799, True, 12), ("Steam iron", 1499, True, 24),
        ("Lunch box", 349, True, 0), ("Coffee mug set", 399, True, 0),
        ("Bed pillow", 699, False, 0), ("Doormat", 299, True, 0),
    ],
    "accessories": [
        ("Phone case", 299, True, 0), ("Screen protector", 249, False, 0),
        ("Laptop sleeve", 899, True, 0), ("Backpack", 1799, True, 6),
        ("Leather wallet", 799, True, 0), ("Sunglasses", 1299, True, 0),
        ("Watch strap", 399, True, 0), ("USB-C cable", 299, True, 6),
        ("20W fast charger", 899, True, 12), ("Car phone holder", 499, True, 0),
        ("Travel adapter", 699, True, 6), ("Keychain", 199, True, 0),
        ("Umbrella", 499, True, 0), ("Belt", 599, True, 0),
        ("Cap", 349, True, 0), ("Tote bag", 449, True, 0),
        ("Earphone case", 199, True, 0), ("Laptop stand", 1299, True, 6),
        ("Cable organiser", 249, True, 0), ("Phone ring holder", 149, True, 0),
    ],
}
PRODUCTS = [Product(i, name, cat, Decimal(price), ret, war)
            for i, (cat, name, price, ret, war) in enumerate(
                ((c, *row) for c, rows in _CATALOG.items() for row in rows), start=1)]

METRO = {"Mumbai": 400001, "Delhi": 110001, "Bengaluru": 560001, "Chennai": 600001,
         "Kolkata": 700001, "Hyderabad": 500001, "Pune": 411001, "Ahmedabad": 380001}
OTHER = {"Ludhiana": 141001, "Jaipur": 302001, "Lucknow": 226001, "Indore": 452001,
         "Nagpur": 440001, "Coimbatore": 641001, "Kochi": 682001, "Bhopal": 462001,
         "Patna": 800001, "Chandigarh": 160001, "Surat": 395001, "Visakhapatnam": 530001,
         "Guwahati": 781001, "Mysuru": 570001, "Dehradun": 248001, "Amritsar": 143001}
CARRIERS = {"BlueLine": "BL", "SwiftShip": "SS"}
FCS = ["Mumbai FC", "Delhi FC", "Bengaluru FC", "Kolkata FC"]
HUBS = ["Nagpur hub", "Jaipur hub", "Hyderabad hub", "Lucknow hub", "Ahmedabad hub", "Vijayawada hub"]
PAYMENTS = {"upi": 0.45, "card": 0.25, "wallet": 0.10, "cod": 0.20}
REFUND_DAYS = {"upi": (1, 3), "wallet": (1, 3), "card": (5, 7), "bank_transfer": (5, 7)}  # business days
REVERSAL_DAYS = (5, 7)       # business days for a failed payment's debit to come back
FREE_SHIPPING_ABOVE, SHIPPING_FEE = Decimal(499), Decimal(49)
TRANSIT_DAYS = {"metro": (2, 4), "other": (4, 7)}   # after the order ships
PICKUP_DAYS = (1, 2)          # after a return is confirmed
INSPECTION_HOURS = (6, 36)    # after pickup; the help center promises within 2 days

# Time helpers: every moment is built from TODAY and checked against NOW ---------

def ago(lo: int, hi: int) -> dt.date:
    return TODAY - dt.timedelta(days=rng.randint(lo, hi))


def at(day: dt.date, lo: int = 8, hi: int = 20) -> dt.datetime:
    """A random minute on `day` between lo:00 and hi:00 IST. Never after NOW."""
    t = dt.datetime.combine(day, dt.time(lo), IST) + dt.timedelta(minutes=rng.randint(0, (hi - lo) * 60))
    assert t < NOW, f"builder asked for {t}, after NOW"
    return t


def later(t: dt.datetime, lo_h: float, hi_h: float) -> dt.datetime:
    out = t + dt.timedelta(minutes=rng.randint(int(lo_h * 60), int(hi_h * 60)))
    assert out < NOW, f"builder asked for {out}, after NOW"
    return out


def business_days_after(t: dt.datetime, n: int) -> dt.datetime:
    while n:
        t += dt.timedelta(days=1)
        n -= t.weekday() < 5
    return t


def transit_days(city: str) -> int:
    return rng.randint(*TRANSIT_DAYS["metro" if city in METRO else "other"])

# One order before IDs are assigned ---------------------------------------------

@dataclass
class Customer:
    id: int
    name: str
    email: str
    phone: str
    city: str
    address: str
    pincode: str
    partition: str


@dataclass
class Draft:
    scenario: str
    customer: Customer
    payment: str
    items: list = field(default_factory=list)    # {product, qty, box, opened}
    status: str = "placed"
    placed_at: dt.datetime = None
    cancelled_at: dt.datetime = None
    boxes: list = field(default_factory=list)    # shipments, with their events
    returns: list = field(default_factory=list)
    refunds: list = field(default_factory=list)
    tickets: list = field(default_factory=list)

    @property
    def city(self):
        return self.customer.city

    def subtotal(self, lines=None):
        lines = range(len(self.items)) if lines is None else lines
        return sum(self.items[i]["product"].price * self.items[i]["qty"] for i in lines)

    def shipping_fee(self):
        return Decimal(0) if self.subtotal() > FREE_SHIPPING_ABOVE else SHIPPING_FEE

    def total(self):
        return self.subtotal() + self.shipping_fee()


def lines(n_lo=1, n_hi=3, category=None, returnable=None):
    """1-3 order lines of distinct products, optionally all from one category."""
    pool = [p for p in PRODUCTS if (category is None or p.category == category)
            and (returnable is None or p.returnable == returnable)]
    n = min(rng.choices(range(n_lo, n_hi + 1), weights=[6, 3, 1][: n_hi - n_lo + 1])[0], len(pool))
    return [{"product": p, "qty": 2 if p.price < 600 and rng.random() < 0.2 else 1,
             "box": None, "opened": False} for p in rng.sample(pool, n)]


def one_category_lines(returnable=True):
    return lines(category=rng.choice(list(WINDOW_DAYS)), returnable=returnable)


def window(d: Draft) -> int:
    return min(WINDOW_DAYS[i["product"].category] for i in d.items)

# Shipping helpers ---------------------------------------------------------------

def place(d: Draft, day: dt.date):
    d.placed_at = at(day)


def dispatch(d: Draft, line_ids=None, after_days=1, eta=None):
    """Hand a box to the carrier `after_days` after the order was placed."""
    day = d.placed_at.date() + dt.timedelta(days=after_days)
    shipped = at(day, 6, 9) if day == TODAY else at(day, 9, 18)
    carrier = rng.choice(list(CARRIERS))
    box = {"carrier": carrier, "status": "in_transit", "shipped_at": shipped,
           "eta": eta or shipped.date() + dt.timedelta(days=transit_days(d.city)),
           "delivered_at": None, "events": [(shipped, rng.choice(FCS), "picked_up")]}
    for i in (range(len(d.items)) if line_ids is None else line_ids):
        d.items[i]["box"] = len(d.boxes)
    d.boxes.append(box)
    d.status = "shipped"
    return box


def scan(box, when, where=None, event="arrived_hub"):
    box["events"].append((when, where or rng.choice(HUBS), event))


def deliver(d: Draft, box, day: dt.date):
    when = at(day, 12, 20)
    if (day - box["shipped_at"].date()).days >= 2:
        scan(box, at(box["shipped_at"].date() + dt.timedelta(days=1), 6, 22))
    scan(box, when - dt.timedelta(hours=rng.randint(2, 4)), f"{d.city} hub", "out_for_delivery")
    scan(box, when, d.city, "delivered")
    box.update(status="delivered", delivered_at=when)


def delivered_on(d: Draft, day: dt.date):
    """Place, ship and deliver the whole order so it arrives on `day`, on time."""
    place(d, day - dt.timedelta(days=transit_days(d.city) + 1))
    box = dispatch(d, eta=day + dt.timedelta(days=rng.randint(0, 1)))
    deliver(d, box, day)
    d.status = "delivered"
    return box


def refund(d: Draft, amount, created_at, ret=None, bank_details=True):
    """A refund row. Card/UPI/wallet go back to the source; COD by bank transfer
    once the customer adds bank details. Completed only if NOW has passed."""
    method = "bank_transfer" if d.payment == "cod" else d.payment
    sent_at = created_at
    bank_at = None
    if method == "bank_transfer":
        bank_at = created_at + dt.timedelta(hours=rng.randint(2, 48)) if bank_details else None
        sent_at = bank_at if bank_at and bank_at < NOW else None
    r = {"amount": amount, "method": method, "initiated_at": created_at,
         "bank_details_added_at": bank_at if sent_at else None, "completed_at": None,
         "status": "awaiting_bank_details" if sent_at is None else "initiated", "ret": ret}
    if sent_at:
        done = business_days_after(sent_at, rng.randint(*REFUND_DAYS[method]))
        if done < NOW:
            r.update(status="completed", completed_at=done)
    d.refunds.append(r)
    return sent_at


def new_return(d: Draft, start, line_ids, reason, confirm=True):
    ret = {"status": "proposed", "reason": reason, "proposed_at": start, "confirmed_at": None,
           "pickup_date": None, "picked_up_at": None, "refunded_at": None,
           "rejected_at": None, "rejection_reason": None, "lines": list(line_ids)}
    if confirm:
        ret.update(status="confirmed", confirmed_at=later(start, 0.05, 2))
        ret["pickup_date"] = ret["confirmed_at"].date() + dt.timedelta(days=rng.randint(*PICKUP_DAYS))
        if ret["pickup_date"] < TODAY:
            ret.update(status="picked_up", picked_up_at=at(ret["pickup_date"], 10, 18))
    d.returns.append(ret)
    return ret


def some_lines(d: Draft):
    """Return one line or all of them."""
    return [rng.randrange(len(d.items))] if rng.random() < 0.5 else range(len(d.items))

# One builder per scenario -------------------------------------------------------

def build_delivered_on_time(d):
    box = delivered_on(d, ago(21, 150))                  # outside every return window
    for i in d.items:
        i["opened"] = i["product"].category == "electronics" and rng.random() < 0.7
    if rng.random() < 0.05:                              # an old complaint, already resolved
        opened = later(box["delivered_at"], 24, 72)
        d.tickets.append({"reason": rng.choice(["damaged", "other"]), "status": "resolved",
                          "created_at": opened, "resolved_at": later(opened, 2, 48)})


def build_not_yet_shipped(d):
    if rng.random() < 0.5:                               # placed this morning
        d.placed_at = at(TODAY, 6, 9)
    else:                                                # placed yesterday, packed, label printed
        d.placed_at = at(TODAY - dt.timedelta(days=1), 12, 20)
        d.status = "packed"
        d.boxes.append({"carrier": rng.choice(list(CARRIERS)), "status": "label_created", "shipped_at": None,
                        "eta": None, "delivered_at": None, "events": []})
        for i in d.items:
            i["box"] = 0


def build_in_transit(d):
    place(d, ago(1, 3))
    box = dispatch(d)
    box["eta"] = max(box["eta"], TODAY)
    if box["shipped_at"].date() < TODAY and rng.random() < 0.25:
        scan(box, at(TODAY, 6, 9), f"{d.city} hub", "out_for_delivery")
        box.update(status="out_for_delivery", eta=TODAY)
        d.status = "out_for_delivery"
    elif box["shipped_at"].date() < TODAY:
        scan(box, at(TODAY, 6, 9))


def build_delayed(d):
    place(d, ago(7, 11))
    box = dispatch(d)                                    # shipped 6-10 days ago
    box["eta"] = box["shipped_at"].date() + dt.timedelta(days=rng.randint(2, 4))  # already past
    scan(box, at(ago(1, 5)))                             # last scan 1-5 days ago: late, not lost


def build_split_shipment(d):
    d.items = lines(2, 3)
    place(d, ago(4, 7))
    first = dispatch(d, [0])
    last_day = min(first["eta"], TODAY - dt.timedelta(days=1))
    deliver(d, first, first["shipped_at"].date() + dt.timedelta(
        days=rng.randint(1, (last_day - first["shipped_at"].date()).days)))
    second = dispatch(d, range(1, len(d.items)), after_days=rng.randint(2, 3))
    second["eta"] = max(second["eta"], TODAY + dt.timedelta(days=1))
    d.status = "shipped"                                 # follows the least advanced box


def build_cancelled_before_ship(d):
    place(d, ago(1, 30))
    d.cancelled_at = later(d.placed_at, 0.5, 10)
    d.status = "cancelled"
    if rng.random() < 0.4:                               # cancelled while packed: label voided
        d.boxes.append({"carrier": rng.choice(list(CARRIERS)), "status": "cancelled", "shipped_at": None,
                        "eta": None, "delivered_at": None, "events": []})
        for i in d.items:
            i["box"] = 0
    if d.payment != "cod":                               # nothing was paid on COD
        refund(d, d.total(), d.cancelled_at)


def build_return_eligible(d):
    d.items = lines(returnable=True)
    delivered_on(d, TODAY - dt.timedelta(days=rng.randint(1, window(d) - 2)))


def build_return_in_progress(d):
    d.items = lines(returnable=True)
    box = delivered_on(d, ago(3, 6))
    ret = new_return(d, later(box["delivered_at"], 12, 40), some_lines(d),
                     rng.choice(["changed_mind", "wrong_item", "damaged_in_transit"]))
    if ret["status"] == "picked_up" and d.payment == "cod" and ret["picked_up_at"] < NOW - dt.timedelta(days=1):
        refund(d, d.subtotal(ret["lines"]), later(ret["picked_up_at"], 2, 20), ret, bank_details=False)
    d.status = "return_requested"


def build_refunded(d):
    d.items = lines(returnable=True)
    box = delivered_on(d, ago(10, 40))
    ret = new_return(d, later(box["delivered_at"], 12, 72), some_lines(d),
                     rng.choice(["changed_mind", "wrong_item", "damaged_in_transit", "faulty"]))
    inspected = later(ret["picked_up_at"], *INSPECTION_HOURS)
    sent = refund(d, d.subtotal(ret["lines"]), inspected, ret)   # shipping is not refunded
    assert sent, "a refunded return must have its money sent"
    ret.update(status="refunded", refunded_at=sent)
    d.status = "refunded"


def build_lost(d):
    place(d, ago(13, 22))
    box = dispatch(d)                                    # shipped 12-21 days ago
    scan(box, at(ago(8, 11)))                            # no update for 8-11 days
    if rng.random() < 0.3:
        d.tickets.append({"reason": "lost_parcel", "status": rng.choice(["open", "in_progress"]),
                          "created_at": at(TODAY - dt.timedelta(days=1)), "resolved_at": None})


def build_window_just_expired(d):
    d.items = one_category_lines()
    delivered_on(d, TODAY - dt.timedelta(days=window(d) + rng.randint(1, 3)))


def build_opened_electronics(d):
    d.items = lines(1, 1, category="electronics", returnable=True)
    d.items[0]["opened"] = True
    delivered_on(d, ago(1, 5))


def build_ship_then_cancel_request(d):
    place(d, ago(1, 2))
    box = dispatch(d)
    box["eta"] = max(box["eta"], TODAY + dt.timedelta(days=1))


def build_return_rejected(d):
    why = rng.choice(["opened_not_faulty", "not_returnable", "outside_window", "failed_inspection"])
    if why == "opened_not_faulty":
        d.items = lines(1, 1, category="electronics", returnable=True)
        d.items[0]["opened"] = True
    elif why == "not_returnable":
        d.items = lines(1, 1, returnable=False)
        d.items[0]["opened"] = True                      # hygiene items are returnable while sealed
    else:
        d.items = one_category_lines()
    if why == "outside_window":
        box = delivered_on(d, TODAY - dt.timedelta(days=window(d) + rng.randint(5, 20)))
        start = later(box["delivered_at"], (window(d) + 1) * 24, (window(d) + 4) * 24)
    else:
        box = delivered_on(d, ago(12, 30))
        start = later(box["delivered_at"], 24, 96)
    ret = new_return(d, start, range(len(d.items)), "changed_mind", confirm=why == "failed_inspection")
    if why == "failed_inspection":
        ret.update(reason=rng.choice(["faulty", "damaged_in_transit"]))
    ret.update(status="rejected", rejection_reason=why,
               rejected_at=later(ret["picked_up_at"] or start, 0.02, 30 if ret["picked_up_at"] else 0.1))


def build_delivered_not_received(d):
    box = delivered_on(d, ago(1, 3))
    d.tickets.append({"reason": "not_received", "status": rng.choice(["open", "in_progress"]),
                      "created_at": later(box["delivered_at"], 1, 12), "resolved_at": None})


BUILDERS = {name: globals()[f"build_{name}"] for name in SCENARIOS}

# Build the world ----------------------------------------------------------------

def make_customers():
    cities = list(METRO) + list(OTHER)
    weights = [6 / len(METRO)] * len(METRO) + [4 / len(OTHER)] * len(OTHER)
    out = []
    for cid in range(1, N_CUSTOMERS + 1):
        first, last = fake.first_name(), fake.last_name()
        city = rng.choices(cities, weights)[0]
        out.append(Customer(
            id=cid, name=f"{first} {last}",
            email=re.sub(r"[^a-z.0-9]", "", f"{first}.{last}{cid}".lower()) + "@example.in",
            phone=f"+91{rng.randint(6_000_000_000, 9_999_999_999)}", city=city,
            address=fake.street_address().replace("\n", ", "),
            pincode=str({**METRO, **OTHER}[city] + rng.randint(0, 40)),
            partition=partition_for(cid)))
    return out


def assign_orders(customers):
    """Exact scenario counts, shuffled, each on a random customer; then make
    sure every scenario has MIN_EVAL_ORDERS on eval customers."""
    counts = {s: round(share * N_ORDERS) for s, share in SCENARIOS.items()}
    counts["delivered_on_time"] += N_ORDERS - sum(counts.values())
    plan = [s for s, n in counts.items() for _ in range(n)]
    rng.shuffle(plan)
    pairs = [[s, rng.choice(customers)] for s in plan]
    eval_customers = [c for c in customers if c.partition == "eval"]
    for s in SCENARIOS:
        mine = [p for p in pairs if p[0] == s]
        short = MIN_EVAL_ORDERS - sum(p[1].partition == "eval" for p in mine)
        for p in [p for p in mine if p[1].partition == "train"][:max(short, 0)]:
            p[1] = rng.choice(eval_customers)
    return pairs


def build_world():
    customers = make_customers()
    drafts = []
    for scenario, customer in assign_orders(customers):
        d = Draft(scenario, customer, rng.choices(list(PAYMENTS), list(PAYMENTS.values()))[0], items=lines())
        BUILDERS[scenario](d)
        drafts.append(d)
    drafts.sort(key=lambda d: d.placed_at)               # order IDs follow time
    failed = failed_payments(customers)
    return customers, drafts, failed


def failed_payments(customers):
    """Debited-but-failed payments with no order (most are reversed by NOW)."""
    chosen = rng.sample(customers, round(FAILED_PAYMENT_SHARE * N_CUSTOMERS))
    extra = [c for c in customers if c.partition == "eval" and c not in chosen]
    chosen += extra[:max(0, MIN_EVAL_ORDERS - sum(c.partition == "eval" for c in chosen))]
    out = []
    for c in chosen:
        attempted = at(ago(1, 20))
        back = business_days_after(attempted, rng.randint(*REVERSAL_DAYS))
        out.append({"customer": c, "method": rng.choice(["upi", "card", "wallet"]),
                    "amount": rng.choice(PRODUCTS).price, "attempted_at": attempted,
                    "status": "reversed" if back < NOW else "failed",
                    "reversed_at": back if back < NOW else None})
    return out


def created_at(customer, drafts, failed):
    firsts = [d.placed_at for d in drafts if d.customer is customer]
    firsts += [f["attempted_at"] for f in failed if f["customer"] is customer]
    first_day = min(firsts).date() if firsts else TODAY
    return at(first_day - dt.timedelta(days=rng.randint(1, 400)))

# Load into Postgres -------------------------------------------------------------

def load(conn, customers, drafts, failed):
    rows = {k: [] for k in ("customers", "products", "orders", "shipments", "order_items",
                            "shipment_events", "returns", "return_items", "refunds",
                            "tickets", "payments", "scenarios")}
    for c in customers:
        rows["customers"].append((c.id, c.name, c.email, c.phone, c.city, c.partition,
                                  created_at(c, drafts, failed)))
    for p in PRODUCTS:
        rows["products"].append((p.id, p.name, p.category, p.price, p.returnable, p.warranty_months))
    ship_id = ret_id = refund_id = ticket_id = pay_id = 0
    for n, d in enumerate(drafts):
        oid = FIRST_ORDER_ID + n
        c = d.customer
        rows["orders"].append((oid, c.id, d.status, d.payment, d.total(), d.shipping_fee(),
                               c.address, c.city, c.pincode, d.placed_at, d.cancelled_at))
        rows["scenarios"].append((oid, d.scenario))
        box_ids = []
        for b in d.boxes:
            ship_id += 1
            box_ids.append(ship_id)
            rows["shipments"].append((ship_id, oid, b["carrier"], f"{CARRIERS[b['carrier']]}{70_000_000 + ship_id}",
                                      b["status"], b["shipped_at"], b["eta"], b["delivered_at"]))
            rows["shipment_events"] += [(ship_id, t, where, ev) for t, where, ev in sorted(b["events"])]
        for line_no, i in enumerate(d.items, start=1):
            rows["order_items"].append((oid, line_no, i["product"].id, i["qty"], i["product"].price,
                                        None if i["box"] is None else box_ids[i["box"]], i["opened"]))
        ret_ids = {}
        for r in d.returns:
            ret_id += 1
            ret_ids[id(r)] = ret_id
            rows["returns"].append((ret_id, oid, r["status"], r["reason"], r["proposed_at"], r["confirmed_at"],
                                    r["pickup_date"], r["picked_up_at"], r["refunded_at"], r["rejected_at"],
                                    r["rejection_reason"]))
            rows["return_items"] += [(ret_id, oid, line + 1) for line in r["lines"]]
        for f in d.refunds:
            refund_id += 1
            rows["refunds"].append((refund_id, oid, ret_ids.get(id(f["ret"])), f["amount"], f["method"],
                                    f["status"], f["initiated_at"], f["bank_details_added_at"], f["completed_at"]))
        for t in d.tickets:
            ticket_id += 1
            rows["tickets"].append((ticket_id, c.id, oid, t["reason"], t["status"], t["created_at"], t["resolved_at"]))
        paid_at = d.placed_at if d.payment != "cod" else (
            max(b["delivered_at"] for b in d.boxes) if d.boxes and all(b["delivered_at"] for b in d.boxes) else None)
        if paid_at:
            pay_id += 1
            rows["payments"].append((pay_id, c.id, oid, d.payment, d.total(), "success", paid_at, None))
    for f in sorted(failed, key=lambda f: f["attempted_at"]):
        pay_id += 1
        rows["payments"].append((pay_id, f["customer"].id, None, f["method"], f["amount"], f["status"],
                                 f["attempted_at"], f["reversed_at"]))
    with conn.cursor() as cur:
        cur.execute((HERE / "schema.sql").read_text())
        for table, data in rows.items():
            if data:
                marks = ", ".join(["%s"] * len(data[0]))
                cur.executemany(f"INSERT INTO {table} VALUES ({marks})", data)
    conn.commit()
    return rows


def write_scenarios_csv(rows):
    with open(HERE / "scenarios.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "scenario"])
        w.writerows(rows["scenarios"])


def run_checks(conn) -> bool:
    """Run every query in db/checks.sql; each must return zero rows."""
    text = (HERE / "checks.sql").read_text()
    blocks = re.split(r"^-- check: (.+)$", text, flags=re.M)[1:]
    ok = True
    with conn.cursor() as cur:
        for name, sql in zip(blocks[::2], blocks[1::2]):
            cur.execute(sql.replace(":'now'", "%(now)s"), {"now": NOW})
            bad = cur.fetchall()
            print(f"  {'ok  ' if not bad else 'FAIL'} {name}" + (f"  ({len(bad)} rows, e.g. {bad[:3]})" if bad else ""))
            ok &= not bad
    return ok


def main():
    customers, drafts, failed = build_world()
    with psycopg.connect(DB_URL) as conn:
        conn.execute("SET TIME ZONE 'Asia/Kolkata'")
        rows = load(conn, customers, drafts, failed)
        write_scenarios_csv(rows)
        print("Seeded:", ", ".join(f"{k} {len(v)}" for k, v in rows.items()))
        print("Checks:")
        ok = run_checks(conn)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
