-- NimbusCart schema. The schema is the contract: the agent's tool schemas,
-- the synthetic training chats and the golden eval cases all depend on it.
-- Designed backwards from the 16 questions in db/QUESTIONS.md.
-- Load: psql "$DB_URL" -f db/schema.sql
-- Re-runnable: drops everything first. Local dev data only.
--
-- Rules: every status is an enum; money is NUMERIC, never FLOAT; every
-- timestamp a "when" question needs is stored; no free-text notes a model
-- could be tricked by; foreign keys everywhere.

DROP TABLE IF EXISTS scenarios, payments, tickets, refunds, return_items, returns,
                     shipment_events, order_items, shipments, orders,
                     products, customers CASCADE;
DROP TYPE IF EXISTS order_status, shipment_status, return_status,
                    return_reason, rejection_reason, refund_status,
                    ticket_reason, ticket_status, payment_status CASCADE;

-- Enums -----------------------------------------------------------------------

CREATE TYPE order_status AS ENUM ('placed','packed','shipped','out_for_delivery',
  'delivered','cancelled','return_requested','refunded');
-- 'cancelled' voids a label when a packed order is cancelled before pickup
-- (db/STATES.md); without it the row would sit at label_created forever.
CREATE TYPE shipment_status AS ENUM ('label_created','in_transit',
  'out_for_delivery','delivered','lost','cancelled');
CREATE TYPE return_status AS ENUM ('proposed','confirmed','picked_up',
  'refunded','rejected');
-- Why the customer is returning. Needed for Q4: opened electronics are
-- returnable only if faulty.
CREATE TYPE return_reason AS ENUM ('faulty','damaged_in_transit','wrong_item',
  'changed_mind');
CREATE TYPE rejection_reason AS ENUM ('outside_window','opened_not_faulty',
  'not_returnable','failed_inspection');
CREATE TYPE refund_status AS ENUM ('initiated','awaiting_bank_details',
  'completed');
CREATE TYPE ticket_reason AS ENUM ('not_received','lost_parcel','damaged',
  'payment_issue','refund_delay','other');
CREATE TYPE ticket_status AS ENUM ('open','in_progress','resolved');
CREATE TYPE payment_status AS ENUM ('success','failed','reversed');

-- Customers and catalog -------------------------------------------------------

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
  product_id      BIGINT PRIMARY KEY,
  name            TEXT NOT NULL,
  category        TEXT NOT NULL CHECK (category IN ('electronics','home','accessories')),
  price_inr       NUMERIC(10,2) NOT NULL CHECK (price_inr > 0),
  returnable      BOOLEAN NOT NULL DEFAULT true,   -- false: hygiene item, not returnable once unsealed (order_items.opened)
  warranty_months INT NOT NULL DEFAULT 0 CHECK (warranty_months >= 0)   -- Q15
);

-- Orders and shipping ---------------------------------------------------------

CREATE TABLE orders (
  order_id         BIGINT PRIMARY KEY,            -- start at 10001
  customer_id      BIGINT NOT NULL REFERENCES customers,
  status           order_status NOT NULL,
  payment_method   TEXT NOT NULL CHECK (payment_method IN ('upi','card','wallet','cod')),
  -- total_inr = sum of items + shipping_fee_inr (checked in db/checks.sql)
  total_inr        NUMERIC(10,2) NOT NULL CHECK (total_inr > 0),
  shipping_fee_inr NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (shipping_fee_inr >= 0), -- Q8
  -- The order's own copy of the address: changing the customer's profile
  -- later must not move an order already placed (Q9).
  ship_address     TEXT NOT NULL,
  ship_city        TEXT NOT NULL,
  ship_pincode     TEXT NOT NULL CHECK (ship_pincode ~ '^[1-9][0-9]{5}$'),
  placed_at        TIMESTAMPTZ NOT NULL,
  cancelled_at     TIMESTAMPTZ,
  CHECK ((status = 'cancelled') = (cancelled_at IS NOT NULL))
);

CREATE TABLE shipments (
  shipment_id   BIGINT PRIMARY KEY,
  order_id      BIGINT NOT NULL REFERENCES orders,
  carrier       TEXT NOT NULL,
  tracking_no   TEXT NOT NULL UNIQUE,
  status        shipment_status NOT NULL,
  shipped_at    TIMESTAMPTZ,
  eta           DATE,
  delivered_at  TIMESTAMPTZ,
  CHECK ((status = 'delivered') = (delivered_at IS NOT NULL))
);

CREATE TABLE order_items (
  order_id       BIGINT REFERENCES orders,
  line_no        INT,
  product_id     BIGINT NOT NULL REFERENCES products,
  qty            INT NOT NULL CHECK (qty > 0),
  unit_price_inr NUMERIC(10,2) NOT NULL CHECK (unit_price_inr > 0),
  shipment_id    BIGINT REFERENCES shipments,   -- which box it travels in
  opened         BOOLEAN NOT NULL DEFAULT false,
  PRIMARY KEY (order_id, line_no)
);

CREATE TABLE shipment_events (
  shipment_id BIGINT NOT NULL REFERENCES shipments,
  at          TIMESTAMPTZ NOT NULL,
  location    TEXT NOT NULL,
  event       TEXT NOT NULL                     -- 'picked_up', 'arrived_hub', ...
);

-- Returns and refunds ---------------------------------------------------------

CREATE TABLE returns (
  return_id        BIGINT PRIMARY KEY,
  order_id         BIGINT NOT NULL REFERENCES orders,
  status           return_status NOT NULL,
  reason           return_reason NOT NULL,
  proposed_at      TIMESTAMPTZ NOT NULL,
  confirmed_at     TIMESTAMPTZ,
  pickup_date      DATE,                        -- Q11: scheduled pickup
  picked_up_at     TIMESTAMPTZ,
  refunded_at      TIMESTAMPTZ,
  rejected_at      TIMESTAMPTZ,
  rejection_reason rejection_reason,            -- Q12
  UNIQUE (return_id, order_id),                 -- target for return_items' FK
  CHECK ((status = 'rejected') = (rejection_reason IS NOT NULL)),
  CHECK ((status = 'rejected') = (rejected_at IS NOT NULL))
);

-- Which order lines are in a return. The composite FKs make it impossible to
-- put a line from order A into a return for order B.
CREATE TABLE return_items (
  return_id BIGINT NOT NULL,
  order_id  BIGINT NOT NULL,
  line_no   INT NOT NULL,
  PRIMARY KEY (return_id, line_no),
  FOREIGN KEY (return_id, order_id) REFERENCES returns (return_id, order_id),
  FOREIGN KEY (order_id, line_no)   REFERENCES order_items (order_id, line_no)
);

-- One row per refund, whether it comes from a cancellation (return_id NULL)
-- or a return (Q5, Q10). COD refunds go by bank transfer once bank details
-- are added.
CREATE TABLE refunds (
  refund_id             BIGINT PRIMARY KEY,
  order_id              BIGINT NOT NULL REFERENCES orders,
  return_id             BIGINT REFERENCES returns,
  amount_inr            NUMERIC(10,2) NOT NULL CHECK (amount_inr > 0),
  method                TEXT NOT NULL CHECK (method IN ('upi','card','wallet','bank_transfer')),
  status                refund_status NOT NULL,
  initiated_at          TIMESTAMPTZ NOT NULL,
  bank_details_added_at TIMESTAMPTZ,
  completed_at          TIMESTAMPTZ,
  CHECK ((status = 'completed') = (completed_at IS NOT NULL))
);

-- Support and payments --------------------------------------------------------

-- Human-handoff tickets (Q13, Q14).
CREATE TABLE tickets (
  ticket_id   BIGINT PRIMARY KEY,
  customer_id BIGINT NOT NULL REFERENCES customers,
  order_id    BIGINT REFERENCES orders,
  reason      ticket_reason NOT NULL,
  status      ticket_status NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL,
  resolved_at TIMESTAMPTZ,
  CHECK ((status = 'resolved') = (resolved_at IS NOT NULL))
);

-- Every payment attempt (Q16). A failed attempt often creates no order, so
-- order_id may be NULL; that keeps order_status at its 8 values.
CREATE TABLE payments (
  payment_id   BIGINT PRIMARY KEY,
  customer_id  BIGINT NOT NULL REFERENCES customers,
  order_id     BIGINT REFERENCES orders,
  method       TEXT NOT NULL CHECK (method IN ('upi','card','wallet','cod')),
  amount_inr   NUMERIC(10,2) NOT NULL CHECK (amount_inr > 0),
  status       payment_status NOT NULL,
  attempted_at TIMESTAMPTZ NOT NULL,
  reversed_at  TIMESTAMPTZ,
  CHECK ((status = 'reversed') = (reversed_at IS NOT NULL))
);

-- Seed metadata ---------------------------------------------------------------

-- Which situation each seeded order was built from (db/seed.py). Used by the
-- eval cases, the synthetic-conversation sampler and per-scenario scores.
-- Never exposed to Nova's tools: it would hand the model the answer.
CREATE TABLE scenarios (
  order_id BIGINT PRIMARY KEY REFERENCES orders,
  scenario TEXT NOT NULL
);

-- Indexes: every tool looks up by customer or order -------------------------

CREATE INDEX ON orders (customer_id, placed_at);
CREATE INDEX ON shipments (order_id);
CREATE INDEX ON order_items (shipment_id);
CREATE INDEX ON shipment_events (shipment_id, at);
CREATE INDEX ON returns (order_id);
CREATE INDEX ON refunds (order_id);
CREATE INDEX ON tickets (customer_id);
CREATE INDEX ON payments (customer_id);
