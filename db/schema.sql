-- NimbusCart schema (Lesson 1.1). The schema is the contract: tool schemas
-- (Module 6), synthetic chats (Module 7) and golden cases (Module 2) depend on it.
-- Load: psql "$DB_URL" -f db/schema.sql
-- Re-runnable: drops everything first. Local dev data only.

DROP TABLE IF EXISTS shipment_events, order_items, shipments, orders,
                     products, customers CASCADE;
DROP TYPE IF EXISTS order_status, shipment_status CASCADE;

-- Tables from the lesson -----------------------------------------------------

CREATE TYPE order_status AS ENUM ('placed','packed','shipped','out_for_delivery',
  'delivered','cancelled','return_requested','refunded');
CREATE TYPE shipment_status AS ENUM ('label_created','in_transit',
  'out_for_delivery','delivered','lost');

CREATE TABLE customers (
  customer_id BIGINT PRIMARY KEY,
  full_name   TEXT NOT NULL,
  email       TEXT NOT NULL UNIQUE,
  phone       TEXT NOT NULL,
  city        TEXT NOT NULL,
  partition   TEXT NOT NULL CHECK (partition IN ('train','eval')),
  created_at  TIMESTAMPTZ NOT NULL
);

CREATE TABLE products (
  product_id  BIGINT PRIMARY KEY,
  name        TEXT NOT NULL,
  category    TEXT NOT NULL CHECK (category IN ('electronics','home','accessories')),
  price_inr   NUMERIC(10,2) NOT NULL CHECK (price_inr > 0),
  returnable  BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE orders (
  order_id       BIGINT PRIMARY KEY,            -- start at 10001
  customer_id    BIGINT NOT NULL REFERENCES customers,
  status         order_status NOT NULL,
  payment_method TEXT NOT NULL CHECK (payment_method IN ('upi','card','wallet','cod')),
  total_inr      NUMERIC(10,2) NOT NULL,
  placed_at      TIMESTAMPTZ NOT NULL,
  cancelled_at   TIMESTAMPTZ
);

CREATE TABLE shipments (
  shipment_id   BIGINT PRIMARY KEY,
  order_id      BIGINT NOT NULL REFERENCES orders,
  carrier       TEXT NOT NULL,
  tracking_no   TEXT NOT NULL UNIQUE,
  status        shipment_status NOT NULL,
  shipped_at    TIMESTAMPTZ,
  eta           DATE,
  delivered_at  TIMESTAMPTZ
);

CREATE TABLE order_items (
  order_id       BIGINT REFERENCES orders,
  line_no        INT,
  product_id     BIGINT NOT NULL REFERENCES products,
  qty            INT NOT NULL CHECK (qty > 0),
  unit_price_inr NUMERIC(10,2) NOT NULL,
  shipment_id    BIGINT REFERENCES shipments,   -- which box it travels in
  opened         BOOLEAN NOT NULL DEFAULT false,
  PRIMARY KEY (order_id, line_no)
);

CREATE TABLE shipment_events (
  shipment_id BIGINT REFERENCES shipments,
  at          TIMESTAMPTZ NOT NULL,
  location    TEXT NOT NULL,
  event       TEXT NOT NULL                     -- 'picked_up', 'arrived_hub', ...
);

-- YOUR TURN ------------------------------------------------------------------
-- 1. return_status enum: proposed, confirmed, picked_up, refunded, rejected
-- 2. returns:       one row per return; a timestamp for each step; FKs
-- 3. return_items:  which order lines are in the return
-- 4. tickets:       human-handoff tickets (status enum, reason, timestamps)
-- 5. Indexes: orders(customer_id), shipments(order_id), plus any your
--    QUESTIONS.md queries need
-- 6. Anything QUESTIONS.md exercise 3 shows is missing (add it to the
--    DROP lines at the top too, so the file stays re-runnable)
