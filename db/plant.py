"""Build nimbus_planted: a copy of the seeded store with attack text planted in it (db/planted.sql).

    uv run python -m db.plant          # (re)creates nimbus_planted from nimbus

The attack cases in evals/attacks/ run against this copy (DB_URL=.../nimbus_planted). The copy is made with
CREATE DATABASE ... TEMPLATE, so roles, row-level security and the help-center embeddings come with it, and
the real store is never written to. Nothing else may connect to nimbus while the copy is made.
"""

import os
import sys
from pathlib import Path

import psycopg

HERE = Path(__file__).parent
SOURCE, TARGET = "nimbus", "nimbus_planted"
DB_URL = os.environ.get("DB_URL", f"postgresql://nimbus:nimbus@localhost:5433/{SOURCE}")


def url_for(db: str) -> str:
    return DB_URL.rsplit("/", 1)[0] + "/" + db


def main() -> None:
    if DB_URL.rsplit("/", 1)[1] != SOURCE:
        sys.exit(f"DB_URL must point at the seeded store ({SOURCE}); the copy is always {TARGET}")
    with psycopg.connect(url_for("postgres"), autocommit=True) as admin:
        admin.execute(f"DROP DATABASE IF EXISTS {TARGET} WITH (FORCE)")
        admin.execute(f"CREATE DATABASE {TARGET} TEMPLATE {SOURCE}")
    with psycopg.connect(url_for(TARGET)) as conn:
        assert conn.execute("SELECT current_database()").fetchone()[0] == TARGET   # never plant in the real store
        conn.execute((HERE / "planted.sql").read_text())
    print(f"{TARGET}: copy of {SOURCE} with the attack text of db/planted.sql")


if __name__ == "__main__":
    main()
