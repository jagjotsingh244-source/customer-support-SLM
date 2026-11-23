"""Return eligibility: one pure function, and the query that feeds it.

eligibility() decides whether an item can be returned, from facts loaded from the database and the
time passed in. It reads no clock and no database, so every rule is unit-tested (tests/test_eligibility.py)
and the same decision is made in both places that need it: propose_return (agent/tools_v2.py), when the
model asks, and the confirm endpoint (api/returns.py), when the customer clicks Confirm. The model cannot
argue with it: no prompt text decides eligibility.

The rules match the help center and the first tools (agent/tools_v0.py), checked in this order:
  not_delivered           the item's box has not been delivered
  already_returning       the item is in a confirmed, picked-up or refunded return
  outside_window          more than WINDOW_DAYS since delivery (7 for electronics, 15 otherwise)
  not_returnable          a hygiene item, unsealed, for a change of mind
  report_for_replacement  the same item, faulty or wrong: replaced through a teammate, not returned
  opened_not_faulty       opened electronics, for a change of mind
  eligible                anything else
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from config import WINDOW_DAYS

REASONS = ("faulty", "damaged_in_transit", "wrong_item", "changed_mind")
PROPOSAL_TTL = timedelta(minutes=30)   # an unconfirmed proposal lapses after this


@dataclass(frozen=True)
class ItemFacts:
    """What the rules need about one order line."""
    name: str
    category: str
    returnable: bool
    opened: bool
    delivered_at: datetime | None
    in_active_return: bool             # in a return that is confirmed, picked up or refunded
    value_inr: Decimal


@dataclass(frozen=True)
class Verdict:
    ok: bool
    reason: str                        # "eligible" or the rule that failed, as listed above
    window_days: int
    delivered_on: date | None
    window_ends: datetime | None


def eligibility(item: ItemFacts, reason: str, now: datetime) -> Verdict:
    if reason not in REASONS:
        raise ValueError(f"reason must be one of {REASONS}")
    days = WINDOW_DAYS[item.category]
    ends = item.delivered_at + timedelta(days=days) if item.delivered_at else None

    def verdict(why: str) -> Verdict:
        return Verdict(why == "eligible", why, days, item.delivered_at.date() if item.delivered_at else None, ends)

    if item.delivered_at is None:
        return verdict("not_delivered")
    if item.in_active_return:
        return verdict("already_returning")
    if now > ends:
        return verdict("outside_window")
    if not item.returnable and item.opened:      # hygiene item, unsealed; sealed ones follow the window
        return verdict("not_returnable" if reason == "changed_mind" else "report_for_replacement")
    if item.category == "electronics" and item.opened and reason == "changed_mind":
        return verdict("opened_not_faulty")
    return verdict("eligible")


ITEM_FACTS_SQL = """
    SELECT p.name, p.category, p.returnable, i.opened, s.delivered_at,
           i.qty * i.unit_price_inr AS value_inr,
           EXISTS (SELECT 1 FROM return_items x JOIN returns r USING (return_id, order_id)
                   WHERE x.order_id = i.order_id AND x.line_no = i.line_no
                     AND r.status IN ('confirmed', 'picked_up', 'refunded')) AS in_active_return
    FROM order_items i
    JOIN products p USING (product_id)
    LEFT JOIN shipments s ON s.shipment_id = i.shipment_id
    WHERE i.order_id = %(oid)s AND i.line_no = %(line)s"""


def item_facts(conn, order_id: int, line_no: int) -> ItemFacts | None:
    """One line of one order, or None. Runs under the caller's role and app.customer_id, so row-level
    security makes another customer's order look exactly like one that does not exist."""
    row = conn.execute(ITEM_FACTS_SQL, {"oid": order_id, "line": line_no}).fetchone()
    return ItemFacts(**row) if row else None
