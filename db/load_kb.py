"""Load the help center into Postgres as one row per section.

    uv run python db/load_kb.py                 # local Docker database
    DB_URL=... uv run python db/load_kb.py      # any other database

Reads every kb/*.md page except README.md and files starting with `_` (the
archive and the customer-words list are never searchable), splits each page on
its `##` headings, and replaces the whole kb_sections table in one
transaction. Running it twice gives the same rows.
"""

import re
import sys
from pathlib import Path

import psycopg
import yaml

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "kb"
sys.path.insert(0, str(ROOT))
from db.seed import DB_URL  # noqa: E402

FRONT_MATTER = re.compile(r"---\n(.*?)\n---\n(.*)", re.S)
HEADING = re.compile(r"^## (.+)$", re.M)


def slug(text: str) -> str:
    """'Earbuds, earphones and trimmers' -> 'earbuds-earphones-and-trimmers'."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def indexed_pages() -> list[Path]:
    return [p for p in sorted(KB.glob("*.md"))
            if p.name != "README.md" and not p.name.startswith("_")]


def sections(path: Path) -> list[dict]:
    m = FRONT_MATTER.match(path.read_text())
    if not m:
        raise ValueError(f"{path.name}: no front matter")
    meta, text = yaml.safe_load(m.group(1)), m.group(2)

    # re.split with a capture group gives [before, heading1, body1, heading2, body2, ...].
    # `before` is the `# Title` line; the title comes from the front matter instead.
    parts = HEADING.split(text)[1:]
    rows = []
    for heading, body in zip(parts[0::2], parts[1::2]):
        rows.append({
            "section_id": f"{meta['id']}#{slug(heading)}",
            "page_id": meta["id"],
            "page_title": meta["title"],
            "heading": heading.strip(),
            "body": body.strip(),
            "policy_version": meta["policy_version"],
            "effective_date": meta["effective_date"],
        })
    if not rows:
        raise ValueError(f"{path.name}: no ## sections")
    return rows


def main() -> None:
    rows = [r for p in indexed_pages() for r in sections(p)]
    ids = [r["section_id"] for r in rows]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        sys.exit(f"duplicate section ids (two headings on one page slug the same): {dupes}")
    empty = [r["section_id"] for r in rows if not r["body"]]
    if empty:
        sys.exit(f"sections with no text: {empty}")

    with psycopg.connect(DB_URL) as conn:  # one transaction: commits on success, rolls back on error
        conn.execute((ROOT / "db" / "kb_sections.sql").read_text())
        with conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO kb_sections (section_id, page_id, page_title, heading, body,
                                            policy_version, effective_date)
                   VALUES (%(section_id)s, %(page_id)s, %(page_title)s, %(heading)s, %(body)s,
                           %(policy_version)s, %(effective_date)s)""",
                rows)

    pages = len({r["page_id"] for r in rows})
    print(f"loaded {len(rows)} sections from {pages} pages into kb_sections")


if __name__ == "__main__":
    main()
