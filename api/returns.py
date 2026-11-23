"""Confirming a return: the only path that turns a proposal into a real return.

The model can only propose (agent/tools_v2.py propose_return). When the customer clicks Confirm on the
card, the UI calls POST /returns/{proposal_id}/confirm (api/app.py), which lands here. Nothing the model
writes reaches this code: the request comes from the customer's click, and the customer comes from their
session, not from the conversation.

Before confirming, everything is checked again, because time has passed since the proposal:
  ownership    row-level security as nova_confirmer: someone else's proposal looks like no proposal (404)
  state        still 'proposed', not already confirmed or rejected (409)
  expiry       confirmed within PROPOSAL_TTL of being proposed (410)
  eligibility  the same rules as the proposal (agent/returns.py), at the time of the click (409)
Then one UPDATE, which the database allows only from 'proposed' to 'confirmed' (db/roles.sql).
"""

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent.returns import PROPOSAL_TTL, eligibility, item_facts  # noqa: E402
from agent.tools_v2 import as_customer  # noqa: E402

PICKUP_AFTER = timedelta(days=1)       # the seed schedules pickups 1-2 days after confirmation


@dataclass
class Outcome:
    status: int                        # HTTP status for the endpoint
    body: dict


def confirm_return(conn: psycopg.Connection, customer_id: int, proposal_id: int, now: datetime) -> Outcome:
    """conn is a nova_confirmer connection; customer_id comes from the signed-in session."""
    with as_customer(conn, customer_id) as c:
        ret = c.execute("SELECT return_id, order_id, status, reason, proposed_at FROM returns WHERE return_id = %s",
                        (proposal_id,)).fetchone()
        if ret is None:
            return Outcome(404, {"error": "not_found"})
        if ret["status"] != "proposed":
            return Outcome(409, {"error": "not_open", "status": ret["status"]})
        if now > ret["proposed_at"] + PROPOSAL_TTL:
            return Outcome(410, {"error": "expired", "detail": "Ask Nova to check the return again."})
        lines = [r["line_no"] for r in c.execute(
            "SELECT line_no FROM return_items WHERE return_id = %s ORDER BY line_no", (proposal_id,)).fetchall()]
        for line in lines:
            item = item_facts(c, ret["order_id"], line)
            verdict = eligibility(item, ret["reason"], now)
            if not verdict.ok:
                return Outcome(409, {"error": "not_eligible", "line_no": line, "reason": verdict.reason})
        pickup = (now + PICKUP_AFTER).date()
        done = c.execute("""UPDATE returns SET status = 'confirmed', confirmed_at = %s, pickup_date = %s
                            WHERE return_id = %s AND status = 'proposed'""", (now, pickup, proposal_id))
        if done.rowcount != 1:                     # confirmed by a second click in the meantime
            return Outcome(409, {"error": "not_open"})
    return Outcome(200, {"return_id": proposal_id, "status": "confirmed", "pickup_date": pickup.isoformat()})
