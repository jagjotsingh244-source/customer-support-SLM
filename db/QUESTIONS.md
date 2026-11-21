# Customer questions Nova must answer (Lesson 1.1)

Write these BEFORE finishing the schema. For each: the question as a customer
would say it, the columns that answer it, and (exercise 3) the SQL for one customer.

The first six come from the lesson; 7–16 are my own (one more than the lesson's 15,
so payment failures are covered too). **GAP** marks a column the starting schema
did not have.

| # | Question | Columns that answer it | SQL works? |
|---|----------|------------------------|------------|
| 1 | Where is my order? | `orders.status`; per shipment: `shipments.status`, `carrier`, `tracking_no`, `eta`; last scan = latest `shipment_events` row (`at`, `location`, `event`) | ✅ |
| 2 | Why is it late? | `shipments.eta` (late when `eta < NOW` and not delivered), `shipments.status`; last scan from `shipment_events.at` (no scan for 7+ days = possible loss) | ✅ |
| 3 | Can I cancel? | `orders.status` (`placed`/`packed` = free cancel; `shipped` or later = refuse delivery or return), `orders.placed_at` | ✅ |
| 4 | Can I return this? | per line: `products.category`, `products.returnable`, `order_items.opened`; `shipments.delivered_at` of **that line's** box (via `order_items.shipment_id`); any existing return for the line (`return_items`, **GAP**) | ✅ |
| 5 | When will I get my money back? | Return route: `returns.status`, picked-up and refunded timestamps, refund amount (**GAP**). Cancel route: `orders.cancelled_at`, `orders.payment_method`, but no refund amount, status or date anywhere (**GAP**). COD: whether bank details were added (**GAP**) | ✅ |
| 6 | Where is the second box? | `order_items.shipment_id` → `shipments` (`status`, `carrier`, `tracking_no`, `eta`, `delivered_at`), grouped by shipment | ✅ |
| 7 | Show me my recent orders | `orders.order_id`, `placed_at`, `status`, `total_inr` for one `customer_id`, newest first (index on `orders(customer_id, placed_at)`) | ✅ |
| 8 | Why was I charged ₹548 when the item was ₹499? | `order_items.qty × unit_price_inr`; shipping charge (**GAP: no shipping fee column**, so "total = sum of items" breaks for orders under the free-shipping threshold) | ✅ |
| 9 | Can I change my delivery address? | `orders.status` (only before `shipped`); the address the order ships to (**GAP: address lives only as `customers.city`; orders need their own copy**) | ✅ |
| 10 | How much will I get back if I return just one item? | `order_items.unit_price_inr × qty` for the returned lines (`return_items`); refund amount (**GAP: refunds**); whether shipping is refunded is policy (decide in Lesson 1.4) | ✅ |
| 11 | When is my return pickup? | `returns.status`, pickup date, picked-up timestamp (**GAP: returns**) | ✅ |
| 12 | Why was my return rejected? | `returns.status = 'rejected'` + rejection reason as an enum, not free text (**GAP**) | ✅ |
| 13 | It says delivered but I didn't get it | `shipments.status`, `delivered_at`; last `shipment_events` row (`location`); a ticket to follow up (**GAP: tickets**) | ✅ |
| 14 | What's happening with my complaint? | ticket status, reason, order, created and resolved timestamps (**GAP: tickets**) | ✅ |
| 15 | Is my item still under warranty? | `shipments.delivered_at` of the item's box + warranty length (**GAP: no warranty column on products**) | ✅ |
| 16 | Money was taken but my order failed | payment attempts: status, amount, method, attempted and reversed timestamps, order if one was created (**GAP: no payments table**) | ✅ |

## SQL per question

The queries live in one runnable file, [`questions.sql`](questions.sql), so they
cannot drift from a copy here. It loads a small hand-built world
([`fixtures.sql`](fixtures.sql): customer 1 with one order per question, plus
customer 2), runs all 16 for customer 1, and rolls back.

```bash
psql "$DB_URL" -f db/questions.sql
```

"SQL works?" ✅ means the query ran and returned the row I expected from the
fixtures (checked 2026-11-20 against NOW = 2026-11-20 10:00 IST).

Rules every query follows:

- **Scoped to one customer.** `customer_id = :cid` is in every WHERE clause,
  even when an order_id is given. The scope check at the end of the file asks
  for customer 2's order as customer 1 and gets 0 rows.
- **The clock is `:'now'`, never `now()`**, and dates are computed in IST.
- **SQL returns facts; policy text comes from the help center.** Q5 returns the
  refund's status and dates, not "5–7 business days".

What writing the SQL found:

- Q4 needed `returns.reason`: opened electronics are returnable only if faulty,
  so the return must record what the customer said. Added to the schema.
- The return window is per item, counted from the `delivered_at` of the box the
  item travelled in, not from the order.
- The 7- and 15-day windows now appear in both SQL and the help center; Module 6
  should hold them in one place in code.
- `::date` on a timestamp uses the session time zone (UTC in this Docker
  image), which shifts the day for anything between 00:00 and 05:30 IST.
  `questions.sql` sets the session to `Asia/Kolkata`; tools in Module 6 need
  the same.
