"""Create Nova's database roles, set their passwords and apply the grants and row-level security in db/roles.sql.

    uv run python -m db.roles            # against DB_URL (the owner's connection)

Passwords come from NOVA_READER_PASSWORD, NOVA_WRITER_PASSWORD and NOVA_CONFIRMER_PASSWORD. The defaults
are for the local Docker database only, like its nimbus/nimbus owner; set real ones anywhere else.
role_url() builds a role's connection URL from the owner's, so every script keeps a single DB_URL.

db/seed.py, db/load_kb.py and rag/index.py call apply() after they load, because recreating a table drops
its grants and policies.
"""

import os
import sys
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

import psycopg
from psycopg import sql

HERE = Path(__file__).resolve().parent
DB_URL = os.environ.get("DB_URL", "postgresql://nimbus:nimbus@localhost:5433/nimbus")
ROLES = ("nova_reader", "nova_writer", "nova_confirmer")


def password(role: str) -> str:
    return os.environ.get(f"{role.upper()}_PASSWORD", f"{role}_local_dev")


def role_url(role: str, owner_url: str = DB_URL) -> str:
    """The owner's URL with the role's name and password: same host, port, database and options."""
    assert role in ROLES, role
    u = urlsplit(owner_url)
    host = u.hostname + (f":{u.port}" if u.port else "")
    return urlunsplit((u.scheme, f"{role}:{quote(password(role), safe='')}@{host}", u.path, u.query, u.fragment))


def apply(conn: psycopg.Connection) -> None:
    """Run db/roles.sql and set the passwords, in the caller's transaction."""
    conn.execute((HERE / "roles.sql").read_text())
    conn.execute((HERE / "demo.sql").read_text())    # the public demo: customer list and per-visitor reset
    for role in ROLES:
        conn.execute(sql.SQL("ALTER ROLE {} PASSWORD {}").format(sql.Identifier(role), sql.Literal(password(role))))


def main() -> None:
    with psycopg.connect(DB_URL) as conn:
        apply(conn)
    print("roles applied:", ", ".join(ROLES), file=sys.stderr)


if __name__ == "__main__":
    main()
