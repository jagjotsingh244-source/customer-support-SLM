"""Nova's tools, built so that a talked-into model still cannot leak data or confirm a return.

Four layers, narrowest first:

1. Narrow tools. Six tools, each doing one thing with the fewest arguments. The customer is never an
   argument: it comes from the session, which the app builds from the sign-in.
2. Typed arguments. One Pydantic model per tool validates every call (strict types, no extra fields, so
   a `customer_id` the model adds is rejected) and generates the JSON schema the model sees.
3. Database roles and row-level security (db/roles.sql). The tools connect as nova_reader and
   nova_writer, never as the owner. Every tool call runs in a transaction that sets app.customer_id, and
   Postgres itself filters every row to that customer. The Python filters by customer too, so a bug in
   either layer alone still returns nothing.
4. Writes that need a human click. propose_return can only insert a *proposed* return; the database
   refuses anything else from nova_writer. Confirming happens only in the backend, when the customer clicks
   Confirm (api/returns.py, role nova_confirmer). No tool here can confirm anything.

Order lookups reuse the first tools' SQL (agent/tools_v0.py), so their results are unchanged and eval runs
stay comparable; help-center search is the vector search of agent/tools_v1.py.

Needs db/roles.py applied (db/seed.py does it) and, for search, the `rag` dependency group.
"""

import sys
from contextlib import contextmanager
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Literal, NamedTuple

import psycopg
from pydantic import BaseModel, ConfigDict, Field
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent import tools_v0 as v0  # noqa: E402
from agent.returns import PROPOSAL_TTL, REASONS, eligibility, item_facts  # noqa: E402
from agent.tools_v1 import CITE_NOTE, MIN_SCORE, NO_MATCH, TOP_K  # noqa: E402
from config import now  # noqa: E402
from db.roles import role_url  # noqa: E402

TOOLS_VERSION = "v2"
AGENT_IDS_FROM = 900001        # returns and tickets the tools create (db/schema.sql identity columns)
TICKET_REASONS = ("not_received", "lost_parcel", "damaged", "payment_issue", "refund_delay", "other")
# Written to the model, about what to say next: a third-person note ("a button is shown to the customer")
# was repeated to the customer word for word by the 2B model.
PROPOSAL_NOTE = "Not returned yet. Ask the customer to press Confirm on the card."


# 1-2. Arguments: one strict model per tool ---------------------------------------------------------

class Args(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


OrderId = Field(ge=10001, le=99999, description="Order number, e.g. 10482")


class ListMyOrders(Args):
    limit: int = Field(5, ge=1, le=10, description="1-10, default 5")


class GetOrderStatus(Args):
    order_id: int = OrderId


class GetTracking(Args):
    order_id: int = OrderId


class SearchHelpCenter(Args):
    query: str = Field(min_length=2, max_length=200, description="A few words")


class ProposeReturn(Args):
    order_id: int = OrderId
    line_no: int = Field(ge=1, le=20, description="line_no from get_order_status")
    reason: Literal[REASONS]


class EscalateToHuman(Args):
    reason: Literal[TICKET_REASONS]
    summary: str = Field(min_length=10, max_length=300, description="One sentence for the teammate")


# Generated keys the model does not need: validation enforces them anyway, and each costs tokens on every
# model call (the six schemas went from 953 to the measured count in DESIGN.md by dropping them).
HIDDEN_KEYS = ("title", "minimum", "maximum", "minLength", "maxLength", "default")


def as_tool(name: str, description: str, model: type[BaseModel]) -> dict:
    """The OpenAI tool entry for one model: its JSON schema minus what only the validator needs. Ranges
    a caller must know go in the description; extra fields are refused by validation, not by the schema."""
    schema = model.model_json_schema()
    for key in ("title", "additionalProperties"):
        schema.pop(key, None)
    for prop in schema["properties"].values():
        for key in HIDDEN_KEYS:
            prop.pop(key, None)
    schema.setdefault("required", [])
    return {"type": "function", "function": {"name": name, "description": description, "parameters": schema}}


# 3. Connections: two roles, one customer per transaction ---------------------------------------------

class Conns(NamedTuple):
    reader: psycopg.Connection
    writer: psycopg.Connection


def _role_conn(owner_url: str, role: str) -> psycopg.Connection:
    conn = psycopg.connect(role_url(role, owner_url), autocommit=True, row_factory=dict_row)
    conn.execute("SET TIME ZONE 'Asia/Kolkata'")       # "today" must be India's today
    return conn


@cache
def _embedder():
    from rag.embeddings import Embedder                # the rag group; imported only when searching
    return Embedder()


def connect(owner_url: str, search: bool = True) -> Conns:
    """Connections as nova_reader and nova_writer, at the host and database of `owner_url` (the owner's
    URL; only its address is used). search=False skips loading the embedding model."""
    conns = Conns(_role_conn(owner_url, "nova_reader"), _role_conn(owner_url, "nova_writer"))
    if search:
        from pgvector.psycopg import register_vector
        register_vector(conns.reader)
        _embedder().check_index(conns.reader)
    return conns


@contextmanager
def as_customer(conn: psycopg.Connection, customer_id: int):
    """One transaction in which row-level security sees only this customer. The final `true` makes the
    setting local to the transaction, so it can never leak into the next one on the same connection."""
    with conn.transaction():
        conn.execute("SELECT set_config('app.customer_id', %s, true)", (str(customer_id),))
        yield conn


@dataclass
class Session:
    """Who is signed in. Built by the app (or the eval), never by the model."""
    conns: Conns
    customer_id: int
    customer_name: str

    @classmethod
    def open(cls, conns: Conns, customer_id: int) -> "Session":
        with as_customer(conns.reader, customer_id) as c:
            row = c.execute("SELECT full_name FROM customers WHERE customer_id = %s", (customer_id,)).fetchone()
        if row is None:
            raise ValueError(f"no customer {customer_id}")
        return cls(conns, customer_id, row["full_name"])

    def read(self):
        return as_customer(self.conns.reader, self.customer_id)

    def write(self):
        return as_customer(self.conns.writer, self.customer_id)

    def all(self, sql: str, params: dict) -> list[dict]:
        """The first tools' query helper, now inside a row-level-security transaction."""
        with self.read() as c:
            return c.execute(sql, {"cid": self.customer_id, "now": now(), **params}).fetchall()


# The six tools ---------------------------------------------------------------------------------------

list_my_orders = v0.list_my_orders          # same SQL; Session.all adds the database's own filter
get_order_status = v0.get_order_status
get_tracking = v0.get_tracking


def search_help_center(session: Session, query: str) -> dict:
    """Up to 3 help-center sections at or above the score cutoff, best first (as agent/tools_v1.py)."""
    from rag import search
    with session.read() as c:
        hits = [h for h in search.vector(c, _embedder().query(query), TOP_K) if h["score"] >= MIN_SCORE]
    if not hits:
        return {"results": [], "note": NO_MATCH}
    return {"results": [{"id": h["chunk_id"], "title": h["path"], "text": h["body"],
                         "effective_date": str(h["effective_date"])} for h in hits],
            "note": CITE_NOTE}


def propose_return(session: Session, order_id: int, line_no: int, reason: str) -> dict:
    """Check one item and, if it can go back, record a proposed return and show the customer a Confirm
    button. Creates nothing the customer has not yet confirmed."""
    t = now()
    with session.read() as c:
        item = item_facts(c, order_id, line_no)
        if item is None:
            return {"error": "not_found"}
        verdict = eligibility(item, reason, t)
        if verdict.ok:
            open_ = c.execute("""
                SELECT r.return_id FROM returns r JOIN return_items x USING (return_id, order_id)
                WHERE r.order_id = %s AND x.line_no = %s AND r.status = 'proposed' AND r.proposed_at > %s
                ORDER BY r.proposed_at DESC LIMIT 1""", (order_id, line_no, t - PROPOSAL_TTL)).fetchone()
    if not verdict.ok:
        return {"order_id": order_id, "line_no": line_no, "item": item.name, "eligible": False,
                "reason": verdict.reason, "window_days": verdict.window_days, "delivered_on": verdict.delivered_on}
    if open_:                                   # asked twice: the same proposal, not a second card
        pid = open_["return_id"]
    else:
        with session.write() as c:
            pid = c.execute("SELECT nextval('returns_return_id_seq') AS id").fetchone()["id"]
            c.execute("""INSERT INTO returns (return_id, order_id, status, reason, proposed_at)
                         VALUES (%s, %s, 'proposed', %s, %s)""", (pid, order_id, reason, t))
            c.execute("INSERT INTO return_items (return_id, order_id, line_no) VALUES (%s, %s, %s)",
                      (pid, order_id, line_no))
    return {"order_id": order_id, "line_no": line_no, "item": item.name, "eligible": True,
            "proposal_id": pid, "refund_estimate_inr": item.value_inr, "note": PROPOSAL_NOTE}


def escalate_to_human(session: Session, reason: str, summary: str) -> dict:
    """Open a ticket for the support team. Always allowed."""
    with session.write() as c:
        tid = c.execute("SELECT nextval('tickets_ticket_id_seq') AS id").fetchone()["id"]
        c.execute("""INSERT INTO tickets (ticket_id, customer_id, reason, status, created_at, summary)
                     VALUES (%s, %s, %s, 'open', %s, %s)""", (tid, session.customer_id, reason, now(), summary))
    return {"handed_off": True, "ticket_id": tid,
            "note": "A teammate will pick this up. Tell the customer, without promising a time."}


# What the model sees, and the name -> function map ------------------------------------------------------

SPECS = [
    ("list_my_orders", "List the signed-in customer's recent orders, newest first.", ListMyOrders, list_my_orders),
    ("get_order_status", "One order's status, items, payment, returns and refunds.",
     GetOrderStatus, get_order_status),
    ("get_tracking", "One order's shipments: carrier, tracking number, delivery estimate, last scan.",
     GetTracking, get_tracking),
    ("search_help_center", "Search the help center for policy (returns, refunds, shipping, payments, "
     "warranty). Up to 3 sections with ids to cite.", SearchHelpCenter, search_help_center),
    ("propose_return", "Check if one item can be returned. If so, the customer gets a Confirm button.",
     ProposeReturn, propose_return),
    ("escalate_to_human", "Hand the conversation to the support team.", EscalateToHuman, escalate_to_human),
]


def _typed(model: type[Args], fn):
    def run(session, **raw):
        args = model.model_validate(raw)          # raises before any SQL runs
        return fn(session, **args.model_dump())
    run.__name__ = fn.__name__
    return run


TOOLS = [as_tool(name, desc, model) for name, desc, model, _ in SPECS]
MODELS = {name: model for name, _, model, _ in SPECS}
REGISTRY = {name: _typed(model, fn) for name, _, model, fn in SPECS}
assert set(REGISTRY) == {t["function"]["name"] for t in TOOLS} == set(v0.REGISTRY)


def clear_agent_writes(owner_conn: psycopg.Connection) -> None:
    """Delete every return and ticket the tools created (IDs from AGENT_IDS_FROM). Evals call this between
    cases, as the owner, so one case's proposal never shows up in the next. Never used in production."""
    with owner_conn.transaction():
        owner_conn.execute("DELETE FROM return_items WHERE return_id >= %s", (AGENT_IDS_FROM,))
        owner_conn.execute("DELETE FROM returns WHERE return_id >= %s", (AGENT_IDS_FROM,))
        owner_conn.execute("DELETE FROM tickets WHERE ticket_id >= %s", (AGENT_IDS_FROM,))
