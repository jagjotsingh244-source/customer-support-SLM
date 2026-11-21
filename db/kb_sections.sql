-- The help center as searchable sections: one row per `##` section of a
-- kb/*.md page. search_help_center reads this table with Postgres full-text
-- search. Filled by db/load_kb.py, which runs this file first.
-- Separate from db/schema.sql: reseeding the store must not touch policy text,
-- and reloading policy text must not touch the store.

DROP TABLE IF EXISTS kb_sections;

CREATE TABLE kb_sections (
  -- '<page id>#<heading slug>', e.g. 'returns-electronics#opened-electronics'.
  -- Stable across reloads, so eval cases and citations can point at it.
  section_id     TEXT PRIMARY KEY,
  page_id        TEXT NOT NULL,
  page_title     TEXT NOT NULL,
  heading        TEXT NOT NULL,
  body           TEXT NOT NULL,
  policy_version INT  NOT NULL,
  effective_date DATE NOT NULL,
  -- The heading is searched too: it often holds the key word
  -- ("Opened electronics") that the body only implies.
  tsv tsvector GENERATED ALWAYS AS (
    to_tsvector('english', page_title || ' ' || heading || ' ' || body)
  ) STORED
);

CREATE INDEX ON kb_sections USING GIN (tsv);
