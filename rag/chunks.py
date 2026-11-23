"""Turn help-center pages into retrieval chunks.

The pages are written one rule per `##` section (kb/README.md), so a section is
the natural unit: small enough that a 2B model reads the one rule it needs,
big enough to keep an exception next to the rule it changes. A section over
MAX_TOKENS is split by paragraph; none is today.

Each chunk carries the page title and heading as its path
('Returning electronics › Opened electronics') and a stable ID made from the
page and heading slugs. Parsing is shared with db/load_kb.py.
"""

import sys
from functools import cache
from pathlib import Path

from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from db.load_kb import indexed_pages, sections  # noqa: E402

MAX_TOKENS = 400
TOKENIZER = "Qwen/Qwen3.5-2B"  # token counts are in the model's own tokens: they spend its context


@cache
def _tokenizer() -> Tokenizer:
    return Tokenizer.from_pretrained(TOKENIZER)


def count_tokens(text: str) -> int:
    return len(_tokenizer().encode(text, add_special_tokens=False).ids)


def chunk_text(path: str, body: str) -> str:
    """What gets embedded and what the model reads: path line, then the body."""
    return f"{path}\n{body}"


def _split(body: str, path: str) -> list[str]:
    """Group whole paragraphs into parts of at most MAX_TOKENS. Never cuts a paragraph."""
    parts, current = [], []
    for para in [p.strip() for p in body.split("\n\n") if p.strip()]:
        trial = "\n\n".join(current + [para])
        if current and count_tokens(chunk_text(path, trial)) > MAX_TOKENS:
            parts.append("\n\n".join(current))
            current = [para]
        else:
            current.append(para)
    parts.append("\n\n".join(current))
    return parts


def chunks_from_page(page: Path) -> list[dict]:
    out = []
    for s in sections(page):
        path = f"{s['page_title']} › {s['heading']}"
        bodies = [s["body"]]
        if count_tokens(chunk_text(path, s["body"])) > MAX_TOKENS:
            bodies = _split(s["body"], path)
        for i, body in enumerate(bodies, start=1):
            # The first part keeps the section's ID, so citations of the section still resolve.
            chunk_id = s["section_id"] if i == 1 else f"{s['section_id']}-{i}"
            out.append({
                "chunk_id": chunk_id,
                "page_id": s["page_id"],
                "path": path,
                "body": body,
                "policy_version": s["policy_version"],
                "effective_date": s["effective_date"],
                "tokens": count_tokens(chunk_text(path, body)),
            })
    return out


def all_chunks() -> list[dict]:
    """Every chunk of every indexed page (never kb/_archive/ or kb/_*.md), checked."""
    pages = indexed_pages()
    old = [p.name for p in pages if "superseded_by:" in p.read_text().split("\n---", 1)[0]]
    if old:  # an archived policy moved back into kb/ would compete with the current rule
        raise ValueError(f"pages marked superseded_by must stay in kb/_archive/: {old}")
    rows = [c for p in pages for c in chunks_from_page(p)]
    ids = [r["chunk_id"] for r in rows]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise ValueError(f"duplicate chunk ids (two headings on one page slug the same): {dupes}")
    too_long = [(r["chunk_id"], r["tokens"]) for r in rows if r["tokens"] > MAX_TOKENS]
    if too_long:
        raise ValueError(f"chunks over {MAX_TOKENS} tokens (one paragraph is too long; shorten it): {too_long}")
    return rows
