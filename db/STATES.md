# State machines

Every allowed move gets a row. **Anything not listed is forbidden**, including
staying put by "jumping back" (e.g. `delivered → packed`).

"Nova?" says whether a Nova tool may cause the move. Everything else
is caused by the warehouse, the carrier or the backend, and Nova only reads it.
Only two moves are Nova's: cancelling, and confirming a return. Both happen
only after the customer explicitly says yes.

## Order status

Eight statuses: placed, packed, shipped, out_for_delivery, delivered,
cancelled, return_requested, refunded.

| From | To | What triggers it | Nova? |
|------|----|------------------|-------|
| placed | packed | Warehouse packs the items; shipment rows are created (`label_created`) | |
| placed | cancelled | Customer cancels; free. A refund row is created unless COD | ✅ |
| packed | cancelled | Customer cancels; still free, because nothing has shipped. Every shipment moves `label_created → cancelled` | ✅ |
| packed | shipped | Carrier picks up the **first** box | |
| shipped | out_for_delivery | Every box not yet delivered is out for delivery | |
| shipped | delivered | Last box delivered without an out-for-delivery scan (carriers skip it) | |
| out_for_delivery | shipped | Delivery attempt failed, box goes back to the hub | |
| out_for_delivery | delivered | Last box delivered | |
| delivered | return_requested | A return is **confirmed** (`returns.status = 'confirmed'`), for one item or more | ✅ |
| return_requested | refunded | The return's refund is issued (`returns.status = 'refunded'`) | |
| return_requested | delivered | The return is rejected at pickup inspection (`failed_inspection`) | |

Terminal: `cancelled`, `refunded`.

**Rules that tie the order to its boxes** (to be checked in `db/checks.sql` after seeding):

- Once shipped, the order follows its **least advanced box**: one box
  delivered and one in transit means the order is `shipped`, not `delivered`.
- `delivered` only when every box is delivered.
- A cancelled order keeps the status `cancelled`. Its money is tracked in
  `refunds` (with `return_id` NULL), not by moving the order to `refunded`.
  `refunded` means "refunded after a return".

**Deliberately not modelled:**

- `shipped → cancelled`. Cancellation is free only until the order ships;
  after that the routes are "refuse delivery" or a return (policy table).
- A lost parcel's ending. The order stays `shipped` while support investigates
  (the seeded `lost` scenario stops before it is resolved).
- A second return after `refunded`. One return per order keeps the demo world
  simple; revisit if the scenarios need it.

## Shipment status

label_created, in_transit, out_for_delivery, delivered, lost, cancelled.

| From | To | What triggers it |
|------|----|------------------|
| label_created | in_transit | Carrier `picked_up` scan; `shipped_at` is set |
| label_created | cancelled | The order is cancelled while packed; the label is voided before pickup |
| in_transit | out_for_delivery | `out_for_delivery` scan |
| in_transit | delivered | `delivered` scan without an out-for-delivery scan; `delivered_at` is set |
| in_transit | lost | Carrier investigation confirms the loss |
| out_for_delivery | delivered | `delivered` scan; `delivered_at` is set |
| out_for_delivery | in_transit | Delivery attempt failed, back to the hub |
| out_for_delivery | lost | Carrier investigation confirms the loss |

Terminal: `delivered`, `lost`, `cancelled`. Only `label_created` can be
cancelled: once the carrier has the box, the routes are refusal or a return.

A new hub scan (`arrived_hub`) adds a `shipment_events` row but does not change
the status. **Possible loss** (no scan for 7 days) is computed from the last
event, not stored as a status: `lost` means the carrier has confirmed it.

## Return status

proposed, confirmed, picked_up, refunded, rejected.

| From | To | What triggers it | Nova? |
|------|----|------------------|-------|
| proposed | confirmed | Customer explicitly says yes; `confirmed_at` and `pickup_date` are set | ✅ |
| proposed | rejected | Backend eligibility check fails: `outside_window`, `not_returnable` or `opened_not_faulty` | |
| confirmed | picked_up | Courier collects the item; `picked_up_at` is set | |
| picked_up | refunded | Inspection passes and the money is sent. For COD the `refunds` row is created at inspection as `awaiting_bank_details`, and the return moves to `refunded` only once bank details are added | |
| picked_up | rejected | Inspection fails: `failed_inspection`; the item is sent back | |

Terminal: `refunded`, `rejected`.

A proposal the customer never confirms stays `proposed` and does nothing.

## Refund status

initiated, awaiting_bank_details, completed.

| From | To | What triggers it |
|------|----|------------------|
| awaiting_bank_details | initiated | COD customer adds bank details; `bank_details_added_at` is set |
| initiated | completed | Money reaches the customer; `completed_at` is set |

Return refunds cover the returned items only; the shipping fee is not refunded.
Cancellation refunds cover the full order total.

A refund starts as `awaiting_bank_details` for COD orders and `initiated` for
UPI, card and wallet. Terminal: `completed`.

## Ticket status

open, in_progress, resolved.

| From | To | What triggers it |
|------|----|------------------|
| open | in_progress | A human agent picks it up |
| open | resolved | Solved without work, e.g. the parcel turns up; `resolved_at` is set |
| in_progress | resolved | Agent closes it; `resolved_at` is set |

Terminal: `resolved`. A customer who comes back gets a new ticket.

## Payment status

success, failed, reversed.

| From | To | What triggers it |
|------|----|------------------|
| failed | reversed | The bank returns money debited for a failed attempt; `reversed_at` is set |

A payment starts as `success` or `failed`. Money back for a successful payment
is a refund, never a payment reversal.

## Decisions

1. **Cancelling a packed order voids its labels** (2026-11-21). Found while
   writing `packed → cancelled`: the `label_created` shipment had nowhere to
   go. Added `cancelled` to `shipment_status` rather than creating shipments
   only at pickup, so a packed order can still show its tracking number.

## Go deeper (not built)

Postgres could enforce these tables itself: a `BEFORE UPDATE` trigger that
looks up `(OLD.status, NEW.status)` in an allowed-moves table and raises an
error otherwise. The seed script only inserts final states, so it is not
needed for the demo.
