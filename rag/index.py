"""Load the help center into kb_chunks.

    uv run python rag/index.py                # chunk, check IDs, load the local database
    uv run python rag/index.py --stats        # also print token counts and the extremes
    uv run python rag/index.py --update-ids   # accept a changed set of chunk IDs
    DB_URL=... uv run python rag/index.py     # any other database

Replaces the whole kb_chunks table in one transaction, so running it twice
gives the same rows.

Chunk IDs are a contract: citations, eval labels and old traces point at them.
rag/chunk_ids.txt lists the current set, and loading stops if the chunker
produces a different one. After editing the help center on purpose, check the
printed difference (a removed ID breaks everything that cites it) and rerun
with --update-ids.
"""

import argparse
import statistics
import sys
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from db.seed import DB_URL  # noqa: E402
from rag.chunks import all_chunks, chunk_text  # noqa: E402

ID_FILE = ROOT / "rag" / "chunk_ids.txt"


def check_ids(ids: list[str], update: bool) -> None:
    recorded = set(ID_FILE.read_text().split()) if ID_FILE.exists() else set()
    added, removed = sorted(set(ids) - recorded), sorted(recorded - set(ids))
    if update:
        ID_FILE.write_text("".join(f"{i}\n" for i in sorted(ids)))
        print(f"{ID_FILE.relative_to(ROOT)}: {len(ids)} ids, {len(added)} added, {len(removed)} removed")
        for i in removed:
            print(f"  removed: {i}")
        return
    if added or removed:
        lines = [f"  added:   {i}" for i in added] + [f"  removed: {i}" for i in removed]
        sys.exit("chunk ids differ from rag/chunk_ids.txt:\n" + "\n".join(lines) +
                 "\nIf the help-center edit was intended, rerun with --update-ids.")


def print_stats(rows: list[dict], n: int = 5) -> None:
    t = sorted(r["tokens"] for r in rows)
    print(f"tokens per chunk: min {t[0]}, median {statistics.median(t):g}, max {t[-1]}, "
          f"total {sum(t)}")
    by_size = sorted(rows, key=lambda r: (r["tokens"], r["chunk_id"]))
    for label, group in (("shortest", by_size[:n]), ("longest", by_size[-n:])):
        print(f"\n{label} {n}:")
        for r in group:
            print(f"--- {r['chunk_id']} ({r['tokens']} tokens)\n{chunk_text(r['path'], r['body'])}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--update-ids", action="store_true")
    args = ap.parse_args()

    rows = all_chunks()
    check_ids([r["chunk_id"] for r in rows], args.update_ids)

    with psycopg.connect(DB_URL) as conn:  # one transaction: commits on success, rolls back on error
        conn.execute((ROOT / "db" / "kb_chunks.sql").read_text())
        with conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO kb_chunks (chunk_id, page_id, path, body, policy_version,
                                          effective_date, tokens)
                   VALUES (%(chunk_id)s, %(page_id)s, %(path)s, %(body)s, %(policy_version)s,
                           %(effective_date)s, %(tokens)s)""",
                rows)

    pages = len({r["page_id"] for r in rows})
    print(f"loaded {len(rows)} chunks from {pages} pages into kb_chunks")
    if args.stats:
        print_stats(rows)


if __name__ == "__main__":
    main()
