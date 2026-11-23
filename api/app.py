"""Nova's backend API. So far one route: the customer's Confirm click on a proposed return.

    uv run --group api fastapi dev api/app.py

The customer comes from the request's session, never from the body or the conversation. Until the chat
UI has a sign-in, `signed_in_customer` reads a development header, X-Customer-Id; the sign-in replaces
that one function, and nothing else here changes.
"""

import os
import sys
from functools import cache
from pathlib import Path

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api.returns import confirm_return  # noqa: E402
from config import now  # noqa: E402
from db.roles import role_url  # noqa: E402

DB_URL = os.environ.get("DB_URL", "postgresql://nimbus:nimbus@localhost:5433/nimbus")

app = FastAPI(title="Nova backend")


@cache
def confirmer() -> psycopg.Connection:
    conn = psycopg.connect(role_url("nova_confirmer", DB_URL), autocommit=True, row_factory=dict_row)
    conn.execute("SET TIME ZONE 'Asia/Kolkata'")
    return conn


def signed_in_customer(x_customer_id: int | None = Header(default=None)) -> int:
    """Development stand-in for the session: the sign-in will supply this."""
    if x_customer_id is None:
        raise HTTPException(401, "not signed in")
    return x_customer_id


@app.post("/returns/{proposal_id}/confirm")
def confirm(proposal_id: int, customer_id: int = Depends(signed_in_customer)):
    outcome = confirm_return(confirmer(), customer_id, proposal_id, now())
    return JSONResponse(outcome.body, status_code=outcome.status)
