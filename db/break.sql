-- Try to break the schema.
-- Every insert after the fixtures must FAIL. Nothing is kept: the whole run
-- is rolled back at the end.
-- Run: psql "$DB_URL" -f db/break.sql
\set ON_ERROR_ROLLBACK on
\set QUIET on
BEGIN;

-- Fixtures: one valid row of each kind the bad inserts point at
INSERT INTO customers VALUES (1, 'Asha Rao', 'asha@example.in', '+919800000001',
  'Pune', 'train', '2026-01-05 10:00+05:30');
INSERT INTO products (product_id, name, category, price_inr) VALUES
  (1, 'USB-C cable', 'accessories', 299.00);
INSERT INTO orders (order_id, customer_id, status, payment_method, total_inr,
  shipping_fee_inr, ship_address, ship_city, ship_pincode, placed_at) VALUES
  (10001, 1, 'placed', 'upi', 348.00, 49.00, '12 MG Road', 'Pune', '411001',
   '2026-11-18 09:00+05:30'),
  (10002, 1, 'placed', 'upi', 348.00, 49.00, '12 MG Road', 'Pune', '411001',
   '2026-11-18 09:00+05:30');
INSERT INTO order_items (order_id, line_no, product_id, qty, unit_price_inr) VALUES
  (10001, 1, 1, 1, 299.00), (10002, 1, 1, 1, 299.00);
INSERT INTO returns (return_id, order_id, status, reason, proposed_at) VALUES
  (1, 10001, 'proposed', 'changed_mind', '2026-11-19 10:00+05:30');
\echo 'fixtures loaded; every test below should print ERROR'

\echo '1. free-text order status'
INSERT INTO orders VALUES (10003, 1, 'in transit', 'upi', 348.00, 49.00,
  '12 MG Road', 'Pune', '411001', '2026-11-18 09:00+05:30', NULL);

\echo '2. negative price'
INSERT INTO products (product_id, name, category, price_inr) VALUES
  (2, 'Mug', 'home', -50.00);

\echo '3. item pointing at a missing product'
INSERT INTO order_items (order_id, line_no, product_id, qty, unit_price_inr)
  VALUES (10001, 2, 999, 1, 299.00);

\echo '4. unknown payment method'
INSERT INTO orders VALUES (10004, 1, 'placed', 'paypal', 348.00, 49.00,
  '12 MG Road', 'Pune', '411001', '2026-11-18 09:00+05:30', NULL);

\echo '5. cancelled order with no cancelled_at'
INSERT INTO orders VALUES (10005, 1, 'cancelled', 'upi', 348.00, 49.00,
  '12 MG Road', 'Pune', '411001', '2026-11-18 09:00+05:30', NULL);

\echo '6. delivered shipment with no delivered_at'
INSERT INTO shipments (shipment_id, order_id, carrier, tracking_no, status)
  VALUES (1, 10001, 'BlueLine', 'BL0001', 'delivered');

\echo '7. invalid pincode'
INSERT INTO orders VALUES (10006, 1, 'placed', 'upi', 348.00, 49.00,
  '12 MG Road', 'Pune', '41100', '2026-11-18 09:00+05:30', NULL);

\echo '8. rejected return with no rejection reason'
INSERT INTO returns (return_id, order_id, status, reason, proposed_at, rejected_at)
  VALUES (2, 10001, 'rejected', 'changed_mind', '2026-11-19 10:00+05:30',
          '2026-11-20 09:00+05:30');

\echo '9. return line taken from a different order (10002 into a 10001 return)'
INSERT INTO return_items VALUES (1, 10002, 1);

\echo '10. zero-quantity item'
INSERT INTO order_items (order_id, line_no, product_id, qty, unit_price_inr)
  VALUES (10001, 3, 1, 0, 299.00);

ROLLBACK;
\echo 'rolled back; database unchanged'
