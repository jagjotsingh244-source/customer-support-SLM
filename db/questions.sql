-- One SQL query per customer question in db/QUESTIONS.md.
-- These are the first drafts of the agent's order tools.
--
-- Run: psql "$DB_URL" -f db/questions.sql
-- Loads db/fixtures.sql inside a transaction, runs all 16, then rolls back,
-- so the database is left as it was.
--
-- Two rules every query follows:
--   1. Scoped to one customer: `customer_id = :cid` is in every WHERE clause,
--      even when an order_id is given. Asking about someone else's order
--      returns no rows (see the scope check at the end).
--   2. The clock is :'now' (config.NOW), never the database's own clock;
--      scripts/check_clock.sh enforces it. Dates are compared in IST, because a
--      session in UTC sees a different "today" between 00:00 and 05:30 IST.
--
-- The SQL returns facts (dates, statuses, flags). Policy text and timings
-- ("card refunds take 5-7 business days") come from the help center (RAG).
-- The window lengths below (7 and 15 days) repeat the help-center policy;
-- The tool layer will hold them in one place in code.

\set ON_ERROR_STOP on
\set QUIET on
\pset footer off
BEGIN;
-- Start from empty tables. TRUNCATE is transactional, so the ROLLBACK at the
-- end brings the seeded data back untouched.
TRUNCATE customers, products, orders, shipments, order_items, shipment_events,
         returns, return_items, refunds, tickets, payments, scenarios;
-- The database defaults to UTC. Without this, ::date casts in Q4/Q15 would
-- give a different day for anything between 00:00 and 05:30 IST.
SET LOCAL TIME ZONE 'Asia/Kolkata';
\ir fixtures.sql

\set cid 1
\set now '2026-11-20 10:00:00+05:30'

\echo '\n=== Q1. Where is my order? (10001)'
\set oid 10001
SELECT o.order_id, o.status AS order_status, s.carrier, s.tracking_no,
       s.status AS shipment_status, s.eta,
       last.at AS last_scan_at, last.location, last.event
FROM orders o
LEFT JOIN shipments s USING (order_id)
LEFT JOIN LATERAL (
  SELECT at, location, event FROM shipment_events e
  WHERE e.shipment_id = s.shipment_id ORDER BY at DESC LIMIT 1
) last ON true
WHERE o.order_id = :oid AND o.customer_id = :cid;

\echo '\n=== Q2. Why is it late? (10002)'
\set oid 10002
SELECT s.tracking_no, s.eta,
       (:'now'::timestamptz AT TIME ZONE 'Asia/Kolkata')::date - s.eta AS days_past_eta,
       last.at AS last_scan_at, last.location,
       date_part('day', :'now'::timestamptz - last.at)::int AS days_since_scan,
       last.at <= :'now'::timestamptz - interval '7 days' AS possible_loss
FROM orders o
JOIN shipments s USING (order_id)
LEFT JOIN LATERAL (
  SELECT at, location FROM shipment_events e
  WHERE e.shipment_id = s.shipment_id ORDER BY at DESC LIMIT 1
) last ON true
WHERE o.order_id = :oid AND o.customer_id = :cid
  AND s.status <> 'delivered'
  AND s.eta < (:'now'::timestamptz AT TIME ZONE 'Asia/Kolkata')::date;

\echo '\n=== Q3. Can I cancel? (10003)'
\set oid 10003
SELECT order_id, status,
       CASE WHEN status IN ('placed','packed')               THEN 'cancel_free'
            WHEN status IN ('shipped','out_for_delivery')    THEN 'refuse_delivery_or_return'
            WHEN status = 'delivered'                        THEN 'return_instead'
            ELSE 'not_applicable' END AS cancel_route
FROM orders
WHERE order_id = :oid AND customer_id = :cid;

\echo '\n=== Q4. Can I return this? (10004, per item)'
\set oid 10004
SELECT i.line_no, p.name, p.category, p.returnable, i.opened,
       s.delivered_at::date AS delivered_on,
       w.window_ends::date AS window_ends,
       CASE WHEN s.delivered_at IS NULL                     THEN 'not_delivered'
            WHEN NOT p.returnable                           THEN 'not_returnable'
            WHEN :'now'::timestamptz > w.window_ends        THEN 'outside_window'
            WHEN ri.return_id IS NOT NULL                   THEN 'already_returning'
            WHEN p.category = 'electronics' AND i.opened     THEN 'only_if_faulty'
            ELSE 'eligible' END AS verdict
FROM orders o
JOIN order_items i USING (order_id)
JOIN products p USING (product_id)
LEFT JOIN shipments s ON s.shipment_id = i.shipment_id      -- this item's box
CROSS JOIN LATERAL (
  SELECT s.delivered_at + CASE p.category WHEN 'electronics' THEN interval '7 days'
                                          ELSE interval '15 days' END AS window_ends
) w
LEFT JOIN LATERAL (                                          -- open return for this line
  SELECT r.return_id FROM return_items x JOIN returns r USING (return_id, order_id)
  WHERE x.order_id = i.order_id AND x.line_no = i.line_no AND r.status <> 'rejected'
  LIMIT 1
) ri ON true
WHERE o.order_id = :oid AND o.customer_id = :cid
ORDER BY i.line_no;

\echo '\n=== Q5. When will I get my money back? (10006, cancelled)'
\set oid 10006
SELECT o.order_id, o.status AS order_status, o.payment_method,
       f.refund_id, f.return_id, f.amount_inr, f.method AS refund_method,
       f.status AS refund_status, f.initiated_at, f.bank_details_added_at, f.completed_at
FROM orders o
LEFT JOIN refunds f USING (order_id)
WHERE o.order_id = :oid AND o.customer_id = :cid;

\echo '\n=== Q6. Where is the second box? (10005)'
\set oid 10005
SELECT s.shipment_id, s.carrier, s.tracking_no, s.status, s.eta,
       s.delivered_at,
       string_agg(p.name || ' x' || i.qty, ', ' ORDER BY i.line_no) AS items
FROM orders o
JOIN order_items i USING (order_id)
JOIN products p USING (product_id)
LEFT JOIN shipments s ON s.shipment_id = i.shipment_id
WHERE o.order_id = :oid AND o.customer_id = :cid
GROUP BY s.shipment_id
ORDER BY s.shipment_id;

\echo '\n=== Q7. Show me my recent orders'
SELECT order_id, placed_at::date AS placed_on, status, total_inr
FROM orders
WHERE customer_id = :cid
ORDER BY placed_at DESC
LIMIT 5;

\echo '\n=== Q8. Why was I charged ₹548 when the item was ₹499? (10002)'
\set oid 10002
SELECT o.order_id, sum(i.qty * i.unit_price_inr) AS items_inr,
       o.shipping_fee_inr, o.total_inr
FROM orders o
JOIN order_items i USING (order_id)
WHERE o.order_id = :oid AND o.customer_id = :cid
GROUP BY o.order_id;

\echo '\n=== Q9. Can I change my delivery address? (10003)'
\set oid 10003
SELECT order_id, status, ship_address, ship_city, ship_pincode,
       status IN ('placed','packed') AS can_change_address
FROM orders
WHERE order_id = :oid AND customer_id = :cid;

\echo '\n=== Q10. How much will I get back if I return just one item? (10007)'
\set oid 10007
SELECT i.line_no, p.name, i.qty * i.unit_price_inr AS line_value_inr,
       r.return_id, r.status AS return_status
FROM orders o
JOIN order_items i USING (order_id)
JOIN products p USING (product_id)
LEFT JOIN return_items x ON x.order_id = i.order_id AND x.line_no = i.line_no
LEFT JOIN returns r ON r.return_id = x.return_id
WHERE o.order_id = :oid AND o.customer_id = :cid
ORDER BY i.line_no;

\echo '\n=== Q11. When is my return pickup? (10007)'
\set oid 10007
SELECT r.return_id, r.status, r.confirmed_at, r.pickup_date, r.picked_up_at
FROM returns r
JOIN orders o USING (order_id)
WHERE r.order_id = :oid AND o.customer_id = :cid
ORDER BY r.proposed_at DESC;

\echo '\n=== Q12. Why was my return rejected? (10008)'
\set oid 10008
SELECT r.return_id, r.reason AS customer_reason, r.status,
       r.rejection_reason, r.rejected_at
FROM returns r
JOIN orders o USING (order_id)
WHERE r.order_id = :oid AND o.customer_id = :cid AND r.status = 'rejected';

\echo '\n=== Q13. It says delivered but I did not get it (10009)'
\set oid 10009
SELECT s.tracking_no, s.status, s.delivered_at,
       last.location AS delivered_at_location, o.ship_address AS ships_to,
       t.ticket_id AS open_ticket, t.status AS ticket_status
FROM orders o
JOIN shipments s USING (order_id)
LEFT JOIN LATERAL (
  SELECT location FROM shipment_events e
  WHERE e.shipment_id = s.shipment_id ORDER BY at DESC LIMIT 1
) last ON true
LEFT JOIN tickets t ON t.order_id = o.order_id AND t.status <> 'resolved'
WHERE o.order_id = :oid AND o.customer_id = :cid;

\echo '\n=== Q14. What is happening with my complaint?'
SELECT ticket_id, order_id, reason, status, created_at, resolved_at
FROM tickets
WHERE customer_id = :cid
ORDER BY created_at DESC;

\echo '\n=== Q15. Is my item still under warranty? (10004)'
\set oid 10004
SELECT i.line_no, p.name, p.warranty_months,
       s.delivered_at::date AS delivered_on,
       (s.delivered_at + make_interval(months => p.warranty_months))::date AS warranty_ends,
       p.warranty_months > 0
         AND :'now'::timestamptz < s.delivered_at + make_interval(months => p.warranty_months)
         AS under_warranty
FROM orders o
JOIN order_items i USING (order_id)
JOIN products p USING (product_id)
JOIN shipments s ON s.shipment_id = i.shipment_id
WHERE o.order_id = :oid AND o.customer_id = :cid
ORDER BY i.line_no;

\echo '\n=== Q16. Money was taken but my order failed'
SELECT payment_id, method, amount_inr, status, attempted_at, reversed_at, order_id
FROM payments
WHERE customer_id = :cid AND status IN ('failed','reversed')
ORDER BY attempted_at DESC;

\echo '\n=== Scope check: customer 1 asks about customer 2''s order 10010 (expect 0 rows)'
\set oid 10010
SELECT count(*) AS rows_visible
FROM orders
WHERE order_id = :oid AND customer_id = :cid;

ROLLBACK;
\echo '\nrolled back; database unchanged'
