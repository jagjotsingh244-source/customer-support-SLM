-- Invariants for the seeded world. Every query must return ZERO rows.
-- db/seed.py runs them after every seed (and exits non-zero if one fails).
-- By hand: psql "$DB_URL" -v now='2026-11-20 10:00:00+05:30' -f db/checks.sql
-- Each block starts with a "-- check:" line; :'now' is config.NOW.

-- check: delivered shipment that was delivered before it shipped
SELECT shipment_id FROM shipments WHERE delivered_at < shipped_at;

-- check: delivered order with a shipment that is not delivered
SELECT o.order_id FROM orders o JOIN shipments s USING (order_id)
WHERE o.status = 'delivered' AND s.status <> 'delivered';

-- check: order total differs from its items plus the shipping fee
SELECT o.order_id FROM orders o JOIN order_items i USING (order_id)
GROUP BY o.order_id
HAVING o.total_inr <> sum(i.qty * i.unit_price_inr) + o.shipping_fee_inr;

-- check: shipping fee breaks the rule (free above 499, otherwise 49)
SELECT o.order_id FROM orders o JOIN order_items i USING (order_id)
GROUP BY o.order_id
HAVING o.shipping_fee_inr <> CASE WHEN sum(i.qty * i.unit_price_inr) > 499 THEN 0 ELSE 49 END;

-- check: item marked opened that is neither electronics nor a hygiene item
-- (opened = unsealed; it only changes the return rules for those two)
SELECT i.order_id, i.line_no FROM order_items i JOIN products p USING (product_id)
WHERE i.opened AND p.category <> 'electronics' AND p.returnable;

-- check: any timestamp after NOW
SELECT 'customers', customer_id FROM customers WHERE created_at > :'now'
UNION ALL SELECT 'orders', order_id FROM orders WHERE greatest(placed_at, cancelled_at) > :'now'
UNION ALL SELECT 'shipments', shipment_id FROM shipments WHERE greatest(shipped_at, delivered_at) > :'now'
UNION ALL SELECT 'shipment_events', shipment_id FROM shipment_events WHERE at > :'now'
UNION ALL SELECT 'returns', return_id FROM returns
  WHERE greatest(proposed_at, confirmed_at, picked_up_at, refunded_at, rejected_at) > :'now'
UNION ALL SELECT 'refunds', refund_id FROM refunds
  WHERE greatest(initiated_at, bank_details_added_at, completed_at) > :'now'
UNION ALL SELECT 'tickets', ticket_id FROM tickets WHERE greatest(created_at, resolved_at) > :'now'
UNION ALL SELECT 'payments', payment_id FROM payments WHERE greatest(attempted_at, reversed_at) > :'now';

-- check: order placed before its customer's account existed
SELECT o.order_id FROM orders o JOIN customers c USING (customer_id) WHERE o.placed_at < c.created_at;

-- check: shipment shipped before its order was placed
SELECT s.shipment_id FROM shipments s JOIN orders o USING (order_id) WHERE s.shipped_at < o.placed_at;

-- check: tracking event before the box shipped or after it was delivered
SELECT e.shipment_id, e.at FROM shipment_events e JOIN shipments s USING (shipment_id)
WHERE e.at < s.shipped_at OR e.at > s.delivered_at;

-- check: a carrier-held shipment with no shipped_at or ETA
SELECT shipment_id FROM shipments
WHERE status NOT IN ('label_created', 'cancelled') AND (shipped_at IS NULL OR eta IS NULL);

-- check: order status does not follow its least advanced box
WITH box AS (
  SELECT order_id, min(CASE status WHEN 'label_created' THEN 0 WHEN 'in_transit' THEN 1 WHEN 'lost' THEN 1
                                   WHEN 'out_for_delivery' THEN 2 WHEN 'delivered' THEN 3 END) AS r
  FROM shipments WHERE status <> 'cancelled' GROUP BY order_id)
SELECT o.order_id, o.status FROM orders o JOIN box b USING (order_id)
WHERE (o.status = 'shipped'          AND b.r <> 1)
   OR (o.status = 'out_for_delivery' AND b.r <> 2)
   OR (o.status IN ('delivered', 'return_requested', 'refunded') AND b.r <> 3);

-- check: cancelled order with a shipment that was not voided
SELECT o.order_id FROM orders o JOIN shipments s USING (order_id)
WHERE o.status = 'cancelled' AND s.status <> 'cancelled';

-- check: shipped-or-later order with an item in no box
SELECT i.order_id, i.line_no FROM order_items i JOIN orders o USING (order_id)
WHERE o.status NOT IN ('placed', 'packed', 'cancelled') AND i.shipment_id IS NULL;

-- check: return_requested order with no open return, or refunded order with no refunded return
SELECT o.order_id FROM orders o
WHERE (o.status = 'return_requested' AND NOT EXISTS (
         SELECT 1 FROM returns r WHERE r.order_id = o.order_id AND r.status IN ('confirmed', 'picked_up')))
   OR (o.status = 'refunded' AND NOT EXISTS (
         SELECT 1 FROM returns r WHERE r.order_id = o.order_id AND r.status = 'refunded'));

-- check: return proposed before the returned item's box was delivered
SELECT r.return_id FROM returns r
JOIN return_items x USING (return_id, order_id)
JOIN order_items i USING (order_id, line_no)
JOIN shipments s ON s.shipment_id = i.shipment_id
WHERE s.delivered_at IS NULL OR r.proposed_at < s.delivered_at;

-- check: refund larger than what the customer paid
SELECT f.refund_id FROM refunds f JOIN orders o USING (order_id) WHERE f.amount_inr > o.total_inr;

-- check: return refund that differs from the value of the returned lines
SELECT f.refund_id FROM refunds f
JOIN return_items x ON x.return_id = f.return_id
JOIN order_items i ON i.order_id = x.order_id AND i.line_no = x.line_no
GROUP BY f.refund_id, f.amount_inr
HAVING f.amount_inr <> sum(i.qty * i.unit_price_inr);

-- check: order with no scenario
SELECT o.order_id FROM orders o LEFT JOIN scenarios s USING (order_id) WHERE s.order_id IS NULL;

-- check: scenario with fewer than 5 orders on eval customers
SELECT s.scenario, count(*) FILTER (WHERE c.partition = 'eval') AS eval_orders
FROM scenarios s JOIN orders o USING (order_id) JOIN customers c USING (customer_id)
GROUP BY s.scenario
HAVING count(*) FILTER (WHERE c.partition = 'eval') < 5;
