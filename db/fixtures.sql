-- A tiny hand-built world for testing the 16 queries in db/questions.sql
-- (Lesson 1.1, exercise 3). Not the real seed: Lesson 1.3's seed.py builds
-- 3,000 orders. Every row here is chosen so one question has a known answer.
--
-- The clock is NOW = 2026-11-20 10:00 IST (Lesson 1.2). Every timestamp is
-- before it.
--
-- Customer 1 (Asha, train) owns orders 10001-10009, one per situation.
-- Customer 2 (Gurpreet, eval) owns 10010; no query for customer 1 may see it.

INSERT INTO customers VALUES
  (1, 'Asha Rao',      'asha.rao@example.in',      '+919800000001', 'Pune',     'train', '2026-01-05 10:00+05:30'),
  (2, 'Gurpreet Gill', 'gurpreet.gill@example.in', '+919800000002', 'Ludhiana', 'eval',  '2026-03-10 10:00+05:30');

INSERT INTO products (product_id, name, category, price_inr, returnable, warranty_months) VALUES
  (1, 'Phone case',         'accessories',  299.00, true,   0),
  (2, 'Desk lamp',          'home',         499.00, true,   6),
  (3, 'Bluetooth speaker',  'electronics', 2499.00, true,  12),
  (4, 'Power bank',         'electronics', 1499.00, true,   6),
  (5, 'Wireless earbuds',   'electronics', 1999.00, false, 12),  -- not returnable once unsealed
  (6, 'Steel water bottle', 'home',         399.00, true,   0);

INSERT INTO orders VALUES
  -- id    cust status              pay      total   ship   address              city        pincode   placed_at                  cancelled_at
  (10001, 1, 'shipped',          'upi',     348.00, 49.00, '12 MG Road, Camp',   'Pune',     '411001', '2026-11-18 09:00+05:30', NULL),  -- Q1 in transit
  (10002, 1, 'shipped',          'card',    548.00, 49.00, '12 MG Road, Camp',   'Pune',     '411001', '2026-11-09 12:00+05:30', NULL),  -- Q2 late, Q8 ₹499 + ₹49
  (10003, 1, 'placed',           'upi',    2499.00,  0.00, '12 MG Road, Camp',   'Pune',     '411001', '2026-11-20 08:00+05:30', NULL),  -- Q3 cancel, Q9 address
  (10004, 1, 'delivered',        'card',   3498.00,  0.00, '12 MG Road, Camp',   'Pune',     '411001', '2026-11-12 10:00+05:30', NULL),  -- Q4 return, Q15 warranty
  (10005, 1, 'shipped',          'upi',    2898.00,  0.00, '12 MG Road, Camp',   'Pune',     '411001', '2026-11-14 10:00+05:30', NULL),  -- Q6 split shipment
  (10006, 1, 'cancelled',        'card',   1499.00,  0.00, '12 MG Road, Camp',   'Pune',     '411001', '2026-11-17 10:00+05:30', '2026-11-17 11:00+05:30'),  -- Q5 refund after cancel
  (10007, 1, 'return_requested', 'upi',     698.00,  0.00, '12 MG Road, Camp',   'Pune',     '411001', '2026-11-05 10:00+05:30', NULL),  -- Q10, Q11 return of one item
  (10008, 1, 'delivered',        'cod',    2499.00,  0.00, '12 MG Road, Camp',   'Pune',     '411001', '2026-11-04 10:00+05:30', NULL),  -- Q12 rejected return
  (10009, 1, 'delivered',        'wallet',  448.00, 49.00, '12 MG Road, Camp',   'Pune',     '411001', '2026-11-15 10:00+05:30', NULL),  -- Q13 delivered, not received
  (10010, 2, 'delivered',        'upi',    1499.00,  0.00, '7 Model Town',       'Ludhiana', '141002', '2026-11-10 10:00+05:30', NULL);  -- other customer

INSERT INTO shipments VALUES
  (1, 10001, 'BlueLine',  'BL100001', 'in_transit', '2026-11-19 10:00+05:30', '2026-11-22', NULL),
  (2, 10002, 'SwiftShip', 'SS200002', 'in_transit', '2026-11-11 10:00+05:30', '2026-11-15', NULL),  -- ETA passed
  (3, 10004, 'BlueLine',  'BL100003', 'delivered',  '2026-11-13 10:00+05:30', '2026-11-16', '2026-11-16 15:00+05:30'),
  (4, 10005, 'BlueLine',  'BL100004', 'delivered',  '2026-11-15 10:00+05:30', '2026-11-18', '2026-11-18 14:00+05:30'),  -- box 1
  (5, 10005, 'SwiftShip', 'SS200005', 'in_transit', '2026-11-17 10:00+05:30', '2026-11-21', NULL),                      -- box 2
  (6, 10007, 'SwiftShip', 'SS200006', 'delivered',  '2026-11-06 10:00+05:30', '2026-11-08', '2026-11-08 13:00+05:30'),
  (7, 10008, 'BlueLine',  'BL100007', 'delivered',  '2026-11-05 10:00+05:30', '2026-11-07', '2026-11-07 12:00+05:30'),
  (8, 10009, 'SwiftShip', 'SS200008', 'delivered',  '2026-11-16 10:00+05:30', '2026-11-19', '2026-11-19 18:00+05:30'),
  (9, 10010, 'BlueLine',  'BL100009', 'delivered',  '2026-11-11 10:00+05:30', '2026-11-15', '2026-11-14 12:00+05:30');

INSERT INTO order_items VALUES
  -- order line product qty price    box  opened
  (10001, 1, 1, 1,  299.00, 1,    false),
  (10002, 1, 2, 1,  499.00, 2,    false),
  (10003, 1, 3, 1, 2499.00, NULL, false),  -- not packed into a box yet
  (10004, 1, 4, 1, 1499.00, 3,    false),
  (10004, 2, 5, 1, 1999.00, 3,    true),
  (10005, 1, 3, 1, 2499.00, 4,    false),
  (10005, 2, 6, 1,  399.00, 5,    false),
  (10006, 1, 4, 1, 1499.00, NULL, false),
  (10007, 1, 6, 1,  399.00, 6,    false),
  (10007, 2, 1, 1,  299.00, 6,    false),
  (10008, 1, 3, 1, 2499.00, 7,    true),
  (10009, 1, 6, 1,  399.00, 8,    false),
  (10010, 1, 4, 1, 1499.00, 9,    false);

INSERT INTO shipment_events VALUES
  (1, '2026-11-19 10:00+05:30', 'Mumbai FC',      'picked_up'),
  (1, '2026-11-20 08:00+05:30', 'Pune hub',       'arrived_hub'),
  (2, '2026-11-11 10:00+05:30', 'Delhi FC',       'picked_up'),
  (2, '2026-11-13 06:00+05:30', 'Jaipur hub',     'arrived_hub'),
  (2, '2026-11-15 09:00+05:30', 'Nagpur hub',     'arrived_hub'),       -- last scan, 5 days before NOW
  (4, '2026-11-15 10:00+05:30', 'Mumbai FC',      'picked_up'),
  (4, '2026-11-18 14:00+05:30', 'Pune - Camp',    'delivered'),
  (5, '2026-11-17 10:00+05:30', 'Bengaluru FC',   'picked_up'),
  (5, '2026-11-19 07:00+05:30', 'Hyderabad hub',  'arrived_hub'),
  (8, '2026-11-16 10:00+05:30', 'Mumbai FC',      'picked_up'),
  (8, '2026-11-19 08:00+05:30', 'Pune hub',       'out_for_delivery'),
  (8, '2026-11-19 18:00+05:30', 'Pune - Kothrud', 'delivered');         -- the order ships to Camp, not Kothrud

INSERT INTO returns VALUES
  -- id order  status       reason          proposed_at               confirmed_at              pickup        picked_up refunded rejected_at               rejection_reason
  (1, 10007, 'confirmed', 'changed_mind', '2026-11-18 10:00+05:30', '2026-11-18 10:05+05:30', '2026-11-21', NULL,     NULL,    NULL,                     NULL),
  (2, 10008, 'rejected',  'changed_mind', '2026-11-10 10:00+05:30', NULL,                     NULL,         NULL,     NULL,    '2026-11-10 10:01+05:30', 'opened_not_faulty');

INSERT INTO return_items VALUES
  (1, 10007, 1),   -- only the bottle; the phone case stays
  (2, 10008, 1);

INSERT INTO refunds VALUES
  (1, 10006, NULL, 1499.00, 'card', 'initiated', '2026-11-17 11:00+05:30', NULL, NULL);

INSERT INTO tickets VALUES
  (1, 1, 10009, 'not_received',  'open',     '2026-11-20 09:00+05:30', NULL),
  (2, 1, NULL,  'payment_issue', 'resolved', '2026-10-02 10:00+05:30', '2026-10-03 12:00+05:30');

INSERT INTO payments VALUES
  (1, 1, 10001, 'upi',  348.00,  'success',  '2026-11-18 09:00+05:30', NULL),
  (2, 1, NULL,  'upi',  1499.00, 'failed',   '2026-11-19 20:00+05:30', NULL),                      -- debited, no order, not reversed yet
  (3, 1, NULL,  'card', 2499.00, 'reversed', '2026-11-02 15:00+05:30', '2026-11-06 12:00+05:30');
