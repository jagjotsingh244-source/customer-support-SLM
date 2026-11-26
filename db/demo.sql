-- The public demo's two database functions: the customer list for the picker, and a reset per visitor.
--
-- 1. demo_reset(): every visitor starts from the seeded store.
--
-- Five demo customers are shared by everyone who opens the demo. Without a reset, the second visitor who
-- signs in as the customer with a returnable item hears "your return is already confirmed", because the first
-- visitor pressed Confirm. With DEMO_RESET=1, /demo-login (api/app.py) calls demo_reset() first.
--
-- It runs with its owner's rights (SECURITY DEFINER) but can only delete what the tools created (ids from
-- 900001, agent/tools_v2.py AGENT_IDS_FROM), only for one eval-partition customer, and only nova_confirmer may
-- call it. Seeded returns and tickets, and every train-partition customer, are out of its reach.
-- Applied by db/roles.py after db/roles.sql; on its own:  psql "$DB_URL" -f db/demo.sql

CREATE OR REPLACE FUNCTION demo_reset(cid bigint) RETURNS integer
  LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
DECLARE
  removed integer;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM customers WHERE customer_id = cid AND partition = 'eval') THEN
    RAISE EXCEPTION 'customer % is not a demo customer', cid;
  END IF;
  DELETE FROM return_items x USING returns r, orders o
   WHERE x.return_id = r.return_id AND r.order_id = o.order_id AND o.customer_id = cid AND r.return_id >= 900001;
  DELETE FROM returns r USING orders o
   WHERE r.order_id = o.order_id AND o.customer_id = cid AND r.return_id >= 900001;
  GET DIAGNOSTICS removed = ROW_COUNT;
  DELETE FROM tickets WHERE customer_id = cid AND ticket_id >= 900001;
  RETURN removed;
END $$;

REVOKE ALL ON FUNCTION demo_reset(bigint) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION demo_reset(bigint) TO nova_confirmer;

-- 2. demo_customer_list(): the picker's list. Row-level security shows the tools' roles one customer at a time,
-- so listing the demo customers needs the owner's rights. It returns only what the picker shows (name, city, the
-- latest order's status) and only for eval-partition customers: the train partition is what the model learned
-- from, and chatting as one of those customers would flatter it. Names and cities are made up by db/seed.py.

CREATE OR REPLACE FUNCTION demo_customer_list()
  RETURNS TABLE (customer_id bigint, full_name text, city text, latest_status text)
  LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public
AS $$
  SELECT c.customer_id, c.full_name, c.city,
         (SELECT o.status::text FROM orders o WHERE o.customer_id = c.customer_id
           ORDER BY o.placed_at DESC LIMIT 1)
    FROM customers c
   WHERE c.partition = 'eval'
   ORDER BY c.full_name
$$;

REVOKE ALL ON FUNCTION demo_customer_list() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION demo_customer_list() TO nova_confirmer;
