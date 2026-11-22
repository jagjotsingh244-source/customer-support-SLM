"""Nova's first, rough tools: six plain functions over the store's database.

They only need to work. The real tool layer (validation, a confirmation step for
writes, better errors) and real retrieval replace them later. Even here, two
rules are not negotiable:

1. The customer comes from the session, never from the model. No tool takes a
   customer_id argument, and every query filters on session.customer_id, so
   asking about someone else's order returns "not_found".
2. Nothing writes. The connection is read-only: propose_return only checks
   eligibility and returns a draft, and escalate_to_human only records the
   hand-off in the trace.

The SQL starts from db/questions.sql. Facts come from the database; policy
text (how long refunds take) comes from search_help_center.
"""

import sys
from dataclasses import dataclass
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import WINDOW_DAYS, now  # noqa: E402


def connect(url: str) -> psycopg.Connection:
    """One connection per eval run: read-only, rows as dicts, dates in IST."""
    conn = psycopg.connect(url, autocommit=True, row_factory=dict_row)
    conn.execute("SET TIME ZONE 'Asia/Kolkata'")       # "today" must be India's today
    conn.execute("SET default_transaction_read_only = on")  # v0 tools can never write
    return conn


@dataclass
class Session:
    """Who is signed in. Built by the app (or the eval), never by the model."""
    conn: psycopg.Connection
    customer_id: int
    customer_name: str

    @classmethod
    def open(cls, conn: psycopg.Connection, customer_id: int) -> "Session":
        row = conn.execute("SELECT full_name FROM customers WHERE customer_id = %s",
                           (customer_id,)).fetchone()
        if row is None:
            raise ValueError(f"no customer {customer_id}")
        return cls(conn, customer_id, row["full_name"])

    def all(self, sql: str, params: dict) -> list[dict]:
        return self.conn.execute(sql, {"cid": self.customer_id, "now": now(), **params}).fetchall()


# The six tools -----------------------------------------------------------------

def list_my_orders(session: Session, limit: int = 5) -> list[dict]:
    """The customer's most recent orders, newest first (Q7)."""
    limit = max(1, min(int(limit), 10))
    return session.all("""
        SELECT o.order_id, o.placed_at::date AS placed_on, o.status, o.total_inr,
               string_agg(p.name, ', ' ORDER BY i.line_no) AS items
        FROM orders o
        JOIN order_items i USING (order_id)
        JOIN products p USING (product_id)
        WHERE o.customer_id = %(cid)s
        GROUP BY o.order_id
        ORDER BY o.placed_at DESC
        LIMIT %(limit)s""", {"limit": limit})


def get_order_status(session: Session, order_id: int) -> dict:
    """One order: status, money, items, and any return or refund on it (Q3, Q5, Q8, Q11, Q12)."""
    order = session.all("""
        SELECT order_id, status, placed_at, cancelled_at, payment_method,
               total_inr, shipping_fee_inr, ship_city
        FROM orders WHERE order_id = %(oid)s AND customer_id = %(cid)s""", {"oid": order_id})
    if not order:
        return {"error": "not_found"}
    out = order[0]
    out["items"] = session.all("""
        SELECT i.line_no, p.name, p.category, i.qty, i.unit_price_inr, i.opened
        FROM order_items i JOIN orders o USING (order_id) JOIN products p USING (product_id)
        WHERE o.order_id = %(oid)s AND o.customer_id = %(cid)s
        ORDER BY i.line_no""", {"oid": order_id})
    out["returns"] = session.all("""
        SELECT r.return_id, r.status, r.reason, r.proposed_at, r.pickup_date, r.picked_up_at,
               r.rejection_reason, r.rejected_at,
               array_agg(x.line_no ORDER BY x.line_no) AS line_nos
        FROM returns r JOIN orders o USING (order_id)
        LEFT JOIN return_items x USING (return_id, order_id)
        WHERE r.order_id = %(oid)s AND o.customer_id = %(cid)s
        GROUP BY r.return_id ORDER BY r.proposed_at""", {"oid": order_id})
    out["refunds"] = session.all("""
        SELECT f.refund_id, f.amount_inr, f.method, f.status, f.initiated_at,
               f.bank_details_added_at, f.completed_at
        FROM refunds f JOIN orders o USING (order_id)
        WHERE f.order_id = %(oid)s AND o.customer_id = %(cid)s
        ORDER BY f.initiated_at""", {"oid": order_id})
    return out


def get_tracking(session: Session, order_id: int) -> dict:
    """Every shipment of one order: carrier, tracking number, ETA, items, last scan (Q1, Q2, Q6, Q13)."""
    order = session.all("SELECT order_id, status FROM orders WHERE order_id = %(oid)s AND customer_id = %(cid)s",
                        {"oid": order_id})
    if not order:
        return {"error": "not_found"}
    shipments = session.all("""
        SELECT s.shipment_id, s.carrier, s.tracking_no, s.status, s.eta, s.delivered_at,
               (SELECT string_agg(p.name, ', ' ORDER BY i.line_no)
                FROM order_items i JOIN products p USING (product_id)
                WHERE i.shipment_id = s.shipment_id) AS items,
               last.at AS last_scan_at, last.location AS last_scan_location, last.event AS last_scan_event
        FROM shipments s
        JOIN orders o USING (order_id)
        LEFT JOIN LATERAL (
          SELECT at, location, event FROM shipment_events e
          WHERE e.shipment_id = s.shipment_id ORDER BY at DESC LIMIT 1
        ) last ON true
        WHERE s.order_id = %(oid)s AND o.customer_id = %(cid)s
        ORDER BY s.shipment_id""", {"oid": order_id})
    return {"order_id": order_id, "order_status": order[0]["status"], "shipments": shipments}


def search_help_center(session: Session, query: str) -> list[dict]:
    """Top 3 help-center sections by Postgres full-text search. Every word must match (rough on purpose)."""
    return session.all("""
        SELECT section_id, page_title, heading, body
        FROM kb_sections, websearch_to_tsquery('english', %(q)s) q
        WHERE tsv @@ q
        ORDER BY ts_rank(tsv, q) DESC
        LIMIT 3""", {"q": query})


REASONS = ("faulty", "damaged_in_transit", "wrong_item", "changed_mind")


def propose_return(session: Session, order_id: int, line_no: int, reason: str) -> dict:
    """Check whether one item can be returned and draft the return. Writes nothing (Q4)."""
    if reason not in REASONS:
        return {"error": "bad_reason", "allowed": list(REASONS)}
    rows = session.all("""
        SELECT i.line_no, p.name, p.category, p.returnable, i.opened,
               i.qty * i.unit_price_inr AS item_value_inr,
               s.delivered_at, w.window_ends,
               EXISTS (SELECT 1 FROM return_items x JOIN returns r USING (return_id, order_id)
                       WHERE x.order_id = i.order_id AND x.line_no = i.line_no
                         AND r.status <> 'rejected') AS already_returning
        FROM orders o
        JOIN order_items i USING (order_id)
        JOIN products p USING (product_id)
        LEFT JOIN shipments s ON s.shipment_id = i.shipment_id
        CROSS JOIN LATERAL (
          SELECT s.delivered_at + make_interval(days => CASE p.category
                   WHEN 'electronics' THEN %(win_el)s ELSE %(win_other)s END) AS window_ends
        ) w
        WHERE o.order_id = %(oid)s AND o.customer_id = %(cid)s AND i.line_no = %(line)s""",
        {"oid": order_id, "line": line_no,
         "win_el": WINDOW_DAYS["electronics"], "win_other": WINDOW_DAYS["home"]})
    if not rows:
        return {"error": "not_found"}
    it = rows[0]
    if it["delivered_at"] is None:
        verdict = "not_delivered"
    elif it["already_returning"]:
        verdict = "already_returning"
    elif now() > it["window_ends"]:
        verdict = "outside_window"
    elif not it["returnable"] and it["opened"]:      # hygiene item, unsealed; sealed ones follow the window
        verdict = "not_returnable" if reason == "changed_mind" else "report_for_replacement"
    elif it["category"] == "electronics" and it["opened"] and reason == "changed_mind":
        verdict = "opened_not_faulty"
    else:
        verdict = "eligible"
    draft = {"order_id": order_id, "line_no": line_no, "item": it["name"], "reason": reason,
             "eligible": verdict == "eligible", "verdict": verdict,
             "delivered_at": it["delivered_at"], "window_ends": it["window_ends"]}
    if verdict == "eligible":
        draft["refund_estimate_inr"] = it["item_value_inr"]
        draft["next_step"] = "Ask the customer to confirm. Nothing has been created yet."
    return draft


def escalate_to_human(session: Session, summary: str) -> dict:
    """Hand the conversation to the support team. v0 records it in the trace only."""
    return {"handed_off": True, "summary": summary}


# Schemas the model sees (OpenAI tool format) and the name -> function map ------

def _fn(name: str, description: str, props: dict, required: list[str]) -> dict:
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": props, "required": required}}}


_ORDER_ID = {"order_id": {"type": "integer", "description": "NimbusCart order number, e.g. 10482"}}

TOOLS = [
    _fn("list_my_orders", "List the signed-in customer's recent orders, newest first.",
        {"limit": {"type": "integer", "description": "How many orders, 1-10 (default 5)"}}, []),
    _fn("get_order_status", "Status, items, payment, returns and refunds of one of the customer's orders.",
        _ORDER_ID, ["order_id"]),
    _fn("get_tracking", "Shipments of one order: carrier, tracking number, estimated delivery date, last scan.",
        _ORDER_ID, ["order_id"]),
    _fn("search_help_center", "Search NimbusCart's help center for policy: returns, refunds, shipping, warranty.",
        {"query": {"type": "string", "description": "A few keywords"}}, ["query"]),
    _fn("propose_return", "Check if one item can be returned and draft the return. Does not create it.",
        {**_ORDER_ID,
         "line_no": {"type": "integer", "description": "Item line number from get_order_status"},
         "reason": {"type": "string", "enum": list(REASONS)}},
        ["order_id", "line_no", "reason"]),
    _fn("escalate_to_human", "Hand the conversation to the support team.",
        {"summary": {"type": "string", "description": "One sentence on the issue"}}, ["summary"]),
]

REGISTRY = {f.__name__: f for f in (list_my_orders, get_order_status, get_tracking,
                                     search_help_center, propose_return, escalate_to_human)}
assert set(REGISTRY) == {t["function"]["name"] for t in TOOLS}
