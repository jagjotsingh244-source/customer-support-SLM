"""Run the 16 customer-question queries against the seeded store and check the rows.

    uv run python -m db.seed            # first
    uv run python db/verify_queries.py

The SQL is read from db/questions.sql, so there is one copy of each query.
Each case runs a query for every eval-partition order of one scenario and
checks the answer against what that scenario built (db/scenarios.csv is the
ground truth). Exits non-zero if any case fails.
"""

import calendar
import datetime as dt
import re
import sys
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from config import now  # noqa: E402
from db.seed import DB_URL  # noqa: E402

NOW = now()
TODAY = NOW.date()


def load_queries() -> dict:
    """{1: sql, ..., 16: sql, 'scope': sql} from the \\echo '=== Qn.' blocks."""
    text = (ROOT / "db" / "questions.sql").read_text()
    out = {}
    for block in re.split(r"^\\echo '\\n=== ", text, flags=re.M)[1:]:
        key = int(m.group(1)) if (m := re.match(r"Q(\d+)\.", block)) else "scope"
        body = "\n".join(line for line in block.splitlines()[1:] if not line.startswith("\\"))
        sql = body[: body.index(";") + 1]
        sql = sql.replace(":'now'", "%(now)s")
        out[key] = re.sub(r"(?<!:):(oid|cid)\b", r"%(\1)s", sql)
    return out


def add_months(d: dt.date, months: int) -> dt.date:
    y, m = divmod(d.month - 1 + months, 12)
    y, m = d.year + y, m + 1
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


class Gate:
    def __init__(self, conn):
        self.conn, self.q, self.results = conn, load_queries(), []

    def ask(self, q, cid, oid=None):
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(self.q[q], {"cid": cid, "oid": oid, "now": NOW})
            return cur.fetchall()

    def fact(self, sql, *args):
        with self.conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, args)
            return cur.fetchall()

    def eval_orders(self, scenario):
        return self.fact("""SELECT o.* FROM scenarios s JOIN orders o USING (order_id)
                            JOIN customers c USING (customer_id)
                            WHERE s.scenario = %s AND c.partition = 'eval' ORDER BY o.order_id""", scenario)

    def case(self, q, what, scenario, check):
        orders = self.eval_orders(scenario)
        bad = [o["order_id"] for o in orders if not check(self.ask(q, o["customer_id"], o["order_id"]), o)]
        self.results.append((q, what, scenario, len(orders), bad))

    def customer_case(self, q, what, customers, check):
        bad = [c for c in customers if not check(self.ask(q, c), c)]
        self.results.append((q, what, "per customer", len(customers), bad))


def main():
    with psycopg.connect(DB_URL) as conn:
        conn.execute("SET TIME ZONE 'Asia/Kolkata'")
        g = Gate(conn)
        lines_of = lambda o: g.fact("SELECT * FROM order_items WHERE order_id = %s ORDER BY line_no", o["order_id"])

        g.case(1, "status, carrier, ETA and last scan", "in_transit", lambda r, o: r and all(
            x["order_status"] in ("shipped", "out_for_delivery") and x["eta"] >= TODAY and x["last_scan_at"] for x in r))
        g.case(2, "late: ETA passed, not yet a possible loss", "delayed", lambda r, o: len(r) == 1
               and r[0]["days_past_eta"] >= 1 and not r[0]["possible_loss"])
        g.case(2, "late and no scan for 7+ days: possible loss", "lost", lambda r, o: r and all(x["possible_loss"] for x in r))
        g.case(2, "on time: no late shipment", "in_transit", lambda r, o: r == [])
        g.case(3, "not shipped: free cancel", "not_yet_shipped", lambda r, o: r[0]["cancel_route"] == "cancel_free")
        g.case(3, "shipped: refuse delivery or return", "ship_then_cancel_request",
               lambda r, o: r[0]["cancel_route"] == "refuse_delivery_or_return")
        g.case(4, "inside the window: every line eligible", "return_eligible",
               lambda r, o: r and all(x["verdict"] == "eligible" for x in r))
        g.case(4, "1-3 days late: outside the window", "window_just_expired",
               lambda r, o: r and all(x["verdict"] == "outside_window" for x in r))
        g.case(4, "opened electronics: only if faulty", "opened_electronics",
               lambda r, o: [x["verdict"] for x in r] == ["only_if_faulty"])
        g.case(5, "cancelled: full refund, none for COD", "cancelled_before_ship", lambda r, o: len(r) == 1 and (
            r[0]["refund_id"] is None if o["payment_method"] == "cod" else
            r[0]["amount_inr"] == o["total_inr"] and r[0]["refund_status"] in ("initiated", "completed")))
        g.case(5, "returned: refund sent for the return", "refunded", lambda r, o: len(r) == 1
               and r[0]["return_id"] is not None and r[0]["refund_status"] in ("initiated", "completed"))
        g.case(6, "two boxes: one delivered, one on the way", "split_shipment", lambda r, o: len(r) == 2
               and {x["status"] for x in r} == {"delivered", "in_transit"} and all(x["items"] for x in r))
        g.case(8, "items + shipping = total", "delivered_on_time", lambda r, o: len(r) == 1
               and r[0]["items_inr"] + r[0]["shipping_fee_inr"] == o["total_inr"]
               and r[0]["shipping_fee_inr"] == (0 if r[0]["items_inr"] > 499 else 49))
        g.case(9, "not shipped: address can change", "not_yet_shipped", lambda r, o: r[0]["can_change_address"] is True)
        g.case(9, "delivered: address cannot change", "delivered_on_time", lambda r, o: r[0]["can_change_address"] is False)
        g.case(10, "line values, returned lines marked", "return_in_progress", lambda r, o: len(r) == len(lines_of(o))
               and sum(x["return_id"] is not None for x in r) == len(g.fact(
                   "SELECT 1 FROM return_items WHERE order_id = %s", o["order_id"]))
               and all(x["line_value_inr"] == i["qty"] * i["unit_price_inr"] for x, i in zip(r, lines_of(o))))
        g.case(11, "open return with a pickup date", "return_in_progress", lambda r, o: len(r) == 1
               and r[0]["status"] in ("confirmed", "picked_up") and r[0]["pickup_date"] is not None)
        g.case(12, "rejected with a reason", "return_rejected", lambda r, o: len(r) == 1 and r[0]["rejection_reason"])
        g.case(13, "delivered, ticket already open", "delivered_not_received", lambda r, o: len(r) == 1
               and r[0]["status"] == "delivered" and r[0]["open_ticket"] is not None)
        g.case(15, "warranty ends delivery + months", "delivered_on_time", lambda r, o: r and all(
            x["warranty_ends"] == add_months(x["delivered_on"], x["warranty_months"])
            and x["under_warranty"] == (x["warranty_months"] > 0 and TODAY < x["warranty_ends"]) for x in r))

        eval_customers = [c["customer_id"] for c in g.fact("SELECT customer_id FROM customers WHERE partition = 'eval'")]
        owned = lambda c: [o["order_id"] for o in g.fact(
            "SELECT order_id FROM orders WHERE customer_id = %s ORDER BY placed_at DESC LIMIT 5", c)]
        g.customer_case(7, "newest 5 orders, only the customer's own", eval_customers,
                        lambda r, c: [x["order_id"] for x in r] == owned(c))
        ticketed = sorted({t["customer_id"] for t in g.fact("SELECT customer_id FROM tickets")} & set(eval_customers))
        g.customer_case(14, "every ticket, newest first", ticketed, lambda r, c: r and [x["ticket_id"] for x in r] == [
            t["ticket_id"] for t in g.fact("SELECT ticket_id FROM tickets WHERE customer_id = %s ORDER BY created_at DESC", c)])
        failed = sorted({p["customer_id"] for p in g.fact("SELECT customer_id FROM payments WHERE order_id IS NULL")}
                        & set(eval_customers))
        g.customer_case(16, "failed payments, no order, reversal date", failed, lambda r, c: r and all(
            x["order_id"] is None and (x["status"] == "reversed") == (x["reversed_at"] is not None) for x in r))

        # Scope: every eval order, asked about by a different customer, returns nothing.
        others = g.fact("""SELECT o.order_id, o.customer_id, c2.customer_id AS other
                           FROM orders o JOIN customers c USING (customer_id)
                           JOIN LATERAL (SELECT customer_id FROM customers x WHERE x.customer_id <> o.customer_id
                                         ORDER BY x.customer_id LIMIT 1) c2 ON true
                           WHERE c.partition = 'eval'""")
        bad = [o["order_id"] for o in others if g.ask(1, o["other"], o["order_id"])]
        g.results.append(("scope", "another customer's order returns nothing", "every eval order", len(others), bad))

    print(f"{'Q':>5}  {'case':<44} {'scenario':<26} {'tested':>6}  result")
    for q, what, scenario, n, bad in g.results:
        res = "ok" if n and not bad else ("NO DATA" if not n else f"FAIL {len(bad)}: {bad[:5]}")
        print(f"{q!s:>5}  {what:<44} {scenario:<26} {n:>6}  {res}")
    failed_cases = [r for r in g.results if r[4] or not r[3]]
    covered = sorted({r[0] for r in g.results if isinstance(r[0], int)})
    print(f"\n{len(g.results) - len(failed_cases)}/{len(g.results)} cases passed; questions covered: {covered}")
    sys.exit(1 if failed_cases else 0)


if __name__ == "__main__":
    main()
