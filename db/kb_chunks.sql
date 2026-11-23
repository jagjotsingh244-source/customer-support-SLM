-- The help center as retrieval chunks: one row per `##` section of a kb/*.md
-- page (a section over 400 tokens is split by paragraph). Filled by
-- rag/index.py, which runs this file first. Replaces kb_sections once the new
-- search_help_center reads it.
-- Separate from db/schema.sql: reseeding the store must not touch policy text,
-- and reloading policy text must not touch the store.

CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS kb_chunks;

CREATE TABLE kb_chunks (
  -- '<page id>#<heading slug>', e.g. 'returns-electronics#opened-electronics'.
  -- Citations, eval labels and traces point at it, so it must survive
  -- reloads: rag/chunk_ids.txt records every ID ever published.
  chunk_id       TEXT PRIMARY KEY,
  page_id        TEXT NOT NULL,
  -- 'Returning electronics › Opened electronics': prepended to the body for
  -- both the embedding and the model, so a chunk says what it is about even
  -- when read on its own.
  path           TEXT NOT NULL,
  body           TEXT NOT NULL,
  policy_version INT  NOT NULL,
  effective_date DATE NOT NULL,
  -- Qwen3.5-2B tokens in path + newline + body: what the chunk costs in
  -- Nova's context budget.
  tokens         INT  NOT NULL CHECK (tokens BETWEEN 1 AND 400),
  -- Filled by `rag/index.py --model ...`. No fixed size, so models of any
  -- dimension can be compared; embedding_model records which one wrote it, and
  -- search refuses to embed a query with a different model.
  embedding       vector,
  embedding_model TEXT,
  tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', path || ' ' || body)) STORED
);

CREATE INDEX ON kb_chunks USING GIN (tsv);
-- No vector index: at about 100 rows an exact scan takes well under a
-- millisecond and never misses a neighbour, while HNSW is approximate. Add one
-- (and give the column a fixed size) if the help center grows to many
-- thousands of chunks.
