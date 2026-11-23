-- Database roles for Nova. The model's tools connect as nova_reader and
-- nova_writer; the confirm-return endpoint connects as nova_confirmer. None of
-- them owns a table, so Postgres applies row-level security to all three.
--
-- What each role can do, and nothing else:
--   nova_reader     SELECT the signed-in customer's own rows (orders, items,
--                   shipments, scan events, returns, refunds, their customer
--                   row), the catalog and the help center. Never tickets,
--                   payments or seed metadata (scenarios).
--   nova_writer     INSERT a *proposed* return for one of the customer's own
--                   orders, its items, and an *open* ticket for the customer.
--                   No UPDATE or DELETE anywhere, so it cannot confirm a return.
--   nova_confirmer  UPDATE one of the customer's own proposed returns to
--                   confirmed. Used only by the backend, after the customer
--                   clicks Confirm; no tool has its password.
--
-- "The customer" is the transaction setting app.customer_id, set by the app
-- from the signed-in session (agent/tools_v2.py, api/returns.py). When it is
-- not set, app_customer_id() is NULL and every policy matches no rows.
--
-- Applied by db/roles.py, which also sets the passwords. Re-runnable. Dropping
-- a table drops its grants and policies with it, so a reseed fails closed (the
-- roles lose access, they never gain it): db/seed.py, db/load_kb.py and
-- rag/index.py reapply this file after loading.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nova_reader') THEN
    CREATE ROLE nova_reader LOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nova_writer') THEN
    CREATE ROLE nova_writer LOGIN;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nova_confirmer') THEN
    CREATE ROLE nova_confirmer LOGIN;
  END IF;
END $$;

-- The session's customer, or NULL. missing_ok = true: unset is not an error.
CREATE OR REPLACE FUNCTION app_customer_id() RETURNS bigint
  LANGUAGE sql STABLE
  AS $$ SELECT NULLIF(current_setting('app.customer_id', true), '')::bigint $$;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM nova_reader, nova_writer, nova_confirmer;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM nova_reader, nova_writer, nova_confirmer;
GRANT USAGE ON SCHEMA public TO nova_reader, nova_writer, nova_confirmer;
GRANT EXECUTE ON FUNCTION app_customer_id() TO nova_reader, nova_writer, nova_confirmer;

-- Grants -----------------------------------------------------------------------

GRANT SELECT ON customers, orders, order_items, products, shipments, shipment_events,
                returns, return_items, refunds TO nova_reader;

-- The writer reads only what its insert checks need: which orders are the
-- customer's, and the next ID.
GRANT SELECT ON orders TO nova_writer;
GRANT INSERT ON returns, return_items, tickets TO nova_writer;
GRANT USAGE ON SEQUENCE returns_return_id_seq, tickets_ticket_id_seq TO nova_writer;

-- The confirmer re-checks eligibility before it confirms, so it reads what that
-- check needs, and may change only the three columns a confirmation sets.
GRANT SELECT ON orders, order_items, products, shipments, returns, return_items TO nova_confirmer;
GRANT UPDATE (status, confirmed_at, pickup_date) ON returns TO nova_confirmer;

-- Row-level security -------------------------------------------------------------
-- A policy on a child table asks "is this row's order one of the customer's?"
-- by reading orders, whose own policy already limits it to the customer.

ALTER TABLE customers       ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders          ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items     ENABLE ROW LEVEL SECURITY;
ALTER TABLE shipments       ENABLE ROW LEVEL SECURITY;
ALTER TABLE shipment_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE returns         ENABLE ROW LEVEL SECURITY;
ALTER TABLE return_items    ENABLE ROW LEVEL SECURITY;
ALTER TABLE refunds         ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets         ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS own_customer ON customers;
CREATE POLICY own_customer ON customers FOR SELECT TO nova_reader
  USING (customer_id = app_customer_id());

DROP POLICY IF EXISTS own_orders ON orders;
CREATE POLICY own_orders ON orders FOR SELECT TO nova_reader, nova_writer, nova_confirmer
  USING (customer_id = app_customer_id());

DROP POLICY IF EXISTS own_items ON order_items;
CREATE POLICY own_items ON order_items FOR SELECT TO nova_reader, nova_confirmer
  USING (order_id IN (SELECT order_id FROM orders));

DROP POLICY IF EXISTS own_shipments ON shipments;
CREATE POLICY own_shipments ON shipments FOR SELECT TO nova_reader, nova_confirmer
  USING (order_id IN (SELECT order_id FROM orders));

DROP POLICY IF EXISTS own_events ON shipment_events;
CREATE POLICY own_events ON shipment_events FOR SELECT TO nova_reader
  USING (shipment_id IN (SELECT shipment_id FROM shipments));

DROP POLICY IF EXISTS own_refunds ON refunds;
CREATE POLICY own_refunds ON refunds FOR SELECT TO nova_reader
  USING (order_id IN (SELECT order_id FROM orders));

DROP POLICY IF EXISTS own_returns ON returns;
CREATE POLICY own_returns ON returns FOR SELECT TO nova_reader, nova_confirmer
  USING (order_id IN (SELECT order_id FROM orders));

DROP POLICY IF EXISTS own_return_items ON return_items;
CREATE POLICY own_return_items ON return_items FOR SELECT TO nova_reader, nova_confirmer
  USING (order_id IN (SELECT order_id FROM orders));

-- Writes. A new return can only be a proposal on the customer's own order; the
-- database rejects anything else, whatever the Python sends.
DROP POLICY IF EXISTS propose_only ON returns;
CREATE POLICY propose_only ON returns FOR INSERT TO nova_writer
  WITH CHECK (order_id IN (SELECT order_id FROM orders)
              AND status = 'proposed' AND confirmed_at IS NULL AND pickup_date IS NULL
              AND picked_up_at IS NULL AND refunded_at IS NULL AND rejected_at IS NULL);

DROP POLICY IF EXISTS propose_items ON return_items;
CREATE POLICY propose_items ON return_items FOR INSERT TO nova_writer
  WITH CHECK (order_id IN (SELECT order_id FROM orders));

DROP POLICY IF EXISTS open_ticket ON tickets;
CREATE POLICY open_ticket ON tickets FOR INSERT TO nova_writer
  WITH CHECK (customer_id = app_customer_id() AND status = 'open' AND resolved_at IS NULL
              AND (order_id IS NULL OR order_id IN (SELECT order_id FROM orders)));

-- Confirming: only the customer's own proposal, and only to confirmed.
DROP POLICY IF EXISTS confirm_own ON returns;
CREATE POLICY confirm_own ON returns FOR UPDATE TO nova_confirmer
  USING (order_id IN (SELECT order_id FROM orders) AND status = 'proposed')
  WITH CHECK (status = 'confirmed' AND confirmed_at IS NOT NULL);

-- The help center is public text: readable by the tools, no row filter. These
-- tables are loaded by their own scripts and may not exist yet.
DO $$
BEGIN
  IF to_regclass('kb_chunks') IS NOT NULL THEN
    GRANT SELECT ON kb_chunks TO nova_reader;
  END IF;
  IF to_regclass('kb_sections') IS NOT NULL THEN
    GRANT SELECT ON kb_sections TO nova_reader;
  END IF;
END $$;
