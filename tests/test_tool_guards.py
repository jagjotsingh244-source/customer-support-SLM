"""The guards hold in the database, not only in the Python: roles, row-level security, propose-only writes,
and a confirm endpoint that is the only way to confirm a return.

Needs the seeded database with roles applied (uv run python -m db.seed):
    uv run --group dev --group api pytest tests/test_tool_guards.py
"""

import os
import sys
from datetime import timedelta
from pathlib import Path

import psycopg
import pytest
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent import tools_v2 as t  # noqa: E402
from config import now  # noqa: E402

DB_URL = os.environ.get("DB_URL", "postgresql://nimbus:nimbus@localhost:5433/nimbus")
A, B = 416, 341                # two eval customers; B owns order 12578
B_ORDER = 12578

try:
    OWNER = psycopg.connect(DB_URL, autocommit=True, row_factory=dict_row)
    CONNS = t.connect(DB_URL, search=False)
except psycopg.OperationalError as e:
    pytest.skip(f"database or roles not available: {e}", allow_module_level=True)

# Every table nova_reader can read that belongs to an order, and how to tie a row to its order.
ORDER_ROWS = {
    "orders": "SELECT count(*) AS n FROM orders WHERE order_id = %(o)s",
    "order_items": "SELECT count(*) AS n FROM order_items WHERE order_id = %(o)s",
    "shipments": "SELECT count(*) AS n FROM shipments WHERE order_id = %(o)s",
    "shipment_events": "SELECT count(*) AS n FROM shipment_events WHERE shipment_id IN "
                       "(SELECT shipment_id FROM shipments WHERE order_id = %(o)s)",
    "returns": "SELECT count(*) AS n FROM returns WHERE order_id = %(o)s",
    "return_items": "SELECT count(*) AS n FROM return_items WHERE order_id = %(o)s",
    "refunds": "SELECT count(*) AS n FROM refunds WHERE order_id = %(o)s",
}


def owner_count(sql: str, order_id: int) -> int:
    return OWNER.execute(sql, {"o": order_id}).fetchone()["n"]


@pytest.fixture(autouse=True)
def clean():
    t.clear_agent_writes(OWNER)
    yield
    t.clear_agent_writes(OWNER)


@pytest.fixture(scope="module")
def eligible():
    """(customer, order, line) of a delivered item that can be returned today, on an eval customer."""
    for r in OWNER.execute("""SELECT o.customer_id, o.order_id FROM scenarios s JOIN orders o USING (order_id)
                              JOIN customers c USING (customer_id)
                              WHERE s.scenario = 'return_eligible' AND c.partition = 'eval'
                              ORDER BY o.order_id""").fetchall():
        session = t.Session.open(CONNS, r["customer_id"])
        with session.read() as c:
            from agent.returns import eligibility, item_facts
            if eligibility(item_facts(c, r["order_id"], 1), "changed_mind", now()).ok:
                return r["customer_id"], r["order_id"], 1
    pytest.fail("no eligible item in the seed")


def full_order_of_someone_else() -> int:
    """Another customer's order with rows in every table above, so a zero really means "filtered"."""
    row = OWNER.execute("""
        SELECT o.order_id FROM orders o
        WHERE o.customer_id <> %s
          AND EXISTS (SELECT 1 FROM returns r WHERE r.order_id = o.order_id)
          AND EXISTS (SELECT 1 FROM refunds f WHERE f.order_id = o.order_id)
          AND EXISTS (SELECT 1 FROM shipment_events e JOIN shipments s USING (shipment_id)
                      WHERE s.order_id = o.order_id)
        ORDER BY o.order_id LIMIT 1""", (A,)).fetchone()
    assert row, "the seed has no order with returns, refunds and scan events"
    return row["order_id"]


# nova_reader: row-level security ---------------------------------------------------------------------

def test_reader_sees_nothing_of_another_customers_order():
    order = full_order_of_someone_else()
    assert all(owner_count(sql, order) > 0 for sql in ORDER_ROWS.values())      # the owner sees every row
    with t.as_customer(CONNS.reader, A) as c:
        for table, sql in ORDER_ROWS.items():
            assert c.execute(sql, {"o": order}).fetchone()["n"] == 0, table
        # Not only that one order: no row of any other customer's order, anywhere.
        assert c.execute("SELECT count(*) AS n FROM orders WHERE customer_id <> %s", (A,)).fetchone()["n"] == 0
        assert c.execute("SELECT count(*) AS n FROM order_items WHERE order_id NOT IN "
                         "(SELECT order_id FROM orders WHERE customer_id = %s)", (A,)).fetchone()["n"] == 0
        assert c.execute("SELECT count(*) AS n FROM customers").fetchone()["n"] == 1
        assert c.execute("SELECT count(*) AS n FROM orders").fetchone()["n"] > 0     # A's own orders are there


def test_every_other_customers_orders_are_invisible():
    """For each eval customer: as that customer, the reader sees exactly the orders the owner says they have."""
    own = {r["customer_id"]: r["n"] for r in OWNER.execute(
        "SELECT customer_id, count(*) AS n FROM orders GROUP BY customer_id").fetchall()}
    eval_ids = [r["customer_id"] for r in OWNER.execute(
        "SELECT customer_id FROM customers WHERE partition = 'eval' ORDER BY customer_id").fetchall()]
    for cid in eval_ids:
        with t.as_customer(CONNS.reader, cid) as c:
            seen = c.execute("SELECT count(*) AS n, count(*) FILTER (WHERE customer_id <> %s) AS other "
                             "FROM orders", (cid,)).fetchone()
        assert seen["other"] == 0 and seen["n"] == own.get(cid, 0), cid


def test_no_customer_set_means_no_rows():
    assert CONNS.reader.execute("SELECT count(*) AS n FROM orders").fetchone()["n"] == 0
    with t.as_customer(CONNS.reader, A):
        pass
    # The setting was local to that transaction: gone afterwards.
    assert CONNS.reader.execute("SELECT count(*) AS n FROM orders").fetchone()["n"] == 0


@pytest.mark.parametrize("sql", ["SELECT * FROM tickets", "SELECT * FROM payments", "SELECT * FROM scenarios",
                                 "INSERT INTO tickets (customer_id, reason, status, created_at) "
                                 "VALUES (416, 'other', 'open', now())",
                                 "UPDATE orders SET status = 'cancelled' WHERE order_id = 11904"])
def test_reader_cannot_touch_the_rest(sql):
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with t.as_customer(CONNS.reader, A) as c:
            c.execute(sql)


# nova_writer: proposals and tickets only -----------------------------------------------------------------

def insert_return(c, order_id, status="proposed", **cols):
    names = ["order_id", "status", "reason", "proposed_at", *cols]
    c.execute(f"INSERT INTO returns ({', '.join(names)}) VALUES ({', '.join(['%s'] * len(names))})",
              [order_id, status, "changed_mind", now(), *cols.values()])


def test_writer_cannot_insert_a_confirmed_return(eligible):
    cid, order, _ = eligible
    with pytest.raises(psycopg.errors.InsufficientPrivilege):          # row-level security violation
        with t.as_customer(CONNS.writer, cid) as c:
            insert_return(c, order, "confirmed", confirmed_at=now())


def test_writer_cannot_propose_on_another_customers_order():
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with t.as_customer(CONNS.writer, A) as c:
            insert_return(c, B_ORDER)


@pytest.mark.parametrize("sql", ["UPDATE returns SET status = 'confirmed' WHERE return_id = 1",
                                 "DELETE FROM returns WHERE return_id = 1",
                                 "SELECT * FROM tickets",
                                 "SELECT * FROM customers"])
def test_writer_cannot_update_delete_or_read(sql):
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with t.as_customer(CONNS.writer, A) as c:
            c.execute(sql)


def test_writer_cannot_open_a_ticket_for_someone_else():
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        with t.as_customer(CONNS.writer, A) as c:
            c.execute("INSERT INTO tickets (ticket_id, customer_id, reason, status, created_at) "
                      "VALUES (nextval('tickets_ticket_id_seq'), %s, 'other', 'open', now())", (B,))


# The tools ---------------------------------------------------------------------------------------------

def test_no_tool_can_confirm_or_choose_the_customer():
    assert [x["function"]["name"] for x in t.TOOLS] == ["list_my_orders", "get_order_status", "get_tracking",
                                                        "search_help_center", "propose_return", "escalate_to_human"]
    for x in t.TOOLS:
        props = x["function"]["parameters"]["properties"]
        assert not {"customer_id", "confirmed", "confirm", "status"} & set(props), x["function"]["name"]


def test_propose_records_a_proposal_only(eligible):
    cid, order, line = eligible
    s = t.Session.open(CONNS, cid)
    out = t.REGISTRY["propose_return"](s, order_id=order, line_no=line, reason="changed_mind")
    assert out["eligible"] and out["proposal_id"] >= t.AGENT_IDS_FROM and "Not returned yet" in out["note"]
    row = OWNER.execute("SELECT status, confirmed_at FROM returns WHERE return_id = %s",
                        (out["proposal_id"],)).fetchone()
    assert row == {"status": "proposed", "confirmed_at": None}
    again = t.REGISTRY["propose_return"](s, order_id=order, line_no=line, reason="changed_mind")
    assert again["proposal_id"] == out["proposal_id"]                  # one card, not two


def test_tools_treat_another_customers_order_as_missing():
    s = t.Session.open(CONNS, A)
    assert t.REGISTRY["get_order_status"](s, order_id=B_ORDER) == t.NOT_FOUND
    assert t.REGISTRY["get_tracking"](s, order_id=B_ORDER) == t.NOT_FOUND
    assert t.REGISTRY["propose_return"](s, order_id=B_ORDER, line_no=1, reason="faulty") == t.NOT_FOUND


def test_customer_id_argument_is_refused():
    s = t.Session.open(CONNS, A)
    with pytest.raises(Exception, match="customer_id"):
        t.REGISTRY["list_my_orders"](s, limit=5, customer_id=B)


def test_escalation_opens_a_ticket_for_the_session_customer():
    s = t.Session.open(CONNS, A)
    out = t.REGISTRY["escalate_to_human"](s, reason="other", summary="Customer asked for a person about a gift.")
    row = OWNER.execute("SELECT customer_id, status, summary FROM tickets WHERE ticket_id = %s",
                        (out["ticket_id"],)).fetchone()
    assert row["customer_id"] == A and row["status"] == "open" and row["summary"].startswith("Customer asked")


# The confirm endpoint ------------------------------------------------------------------------------------

@pytest.fixture
def client():
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from api.app import app
    return TestClient(app)


def propose(customer_id, order, line) -> int:
    out = t.REGISTRY["propose_return"](t.Session.open(CONNS, customer_id), order_id=order, line_no=line,
                                       reason="changed_mind")
    return out["proposal_id"]


def status_of(pid) -> str:
    return OWNER.execute("SELECT status FROM returns WHERE return_id = %s", (pid,)).fetchone()["status"]


def test_customer_click_confirms_once(client, eligible):
    cid, order, line = eligible
    pid = propose(cid, order, line)
    r = client.post(f"/returns/{pid}/confirm", headers={"X-Customer-Id": str(cid)})
    assert r.status_code == 200 and r.json()["status"] == "confirmed" and status_of(pid) == "confirmed"
    again = client.post(f"/returns/{pid}/confirm", headers={"X-Customer-Id": str(cid)})
    assert again.status_code == 409


def test_someone_else_cannot_confirm(client, eligible):
    cid, order, line = eligible
    pid = propose(cid, order, line)
    other = A if cid != A else B
    r = client.post(f"/returns/{pid}/confirm", headers={"X-Customer-Id": str(other)})
    assert r.status_code == 404 and status_of(pid) == "proposed"
    assert client.post(f"/returns/{pid}/confirm").status_code == 401          # no session, no confirm


def test_expired_proposal_is_refused(eligible):
    from api.app import confirmer
    from api.returns import confirm_return
    cid, order, line = eligible
    pid = propose(cid, order, line)
    out = confirm_return(confirmer(), cid, pid, now() + t.PROPOSAL_TTL + timedelta(seconds=1))
    assert out.status == 410 and status_of(pid) == "proposed"


def test_eligibility_is_checked_again_at_the_click(eligible):
    """A proposal that is no longer eligible when the customer clicks (here: inserted for an expired item,
    as the owner, the way a stale proposal would look) is refused."""
    from api.app import confirmer
    from api.returns import confirm_return
    row = OWNER.execute("""SELECT o.customer_id, o.order_id FROM scenarios s JOIN orders o USING (order_id)
                           WHERE s.scenario = 'window_just_expired' ORDER BY o.order_id LIMIT 1""").fetchone()
    with OWNER.transaction():
        insert_return(OWNER, row["order_id"])
        pid = OWNER.execute("SELECT max(return_id) AS id FROM returns").fetchone()["id"]
        OWNER.execute("INSERT INTO return_items VALUES (%s, %s, 1)", (pid, row["order_id"]))
    out = confirm_return(confirmer(), row["customer_id"], pid, now())
    assert out.status == 409 and out.body["reason"] == "outside_window" and status_of(pid) == "proposed"
