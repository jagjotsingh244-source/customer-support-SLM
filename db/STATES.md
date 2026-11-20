# Order status state machine (Lesson 1.1, exercise 5)

Eight statuses: placed, packed, shipped, out_for_delivery, delivered,
cancelled, return_requested, refunded.

Every allowed move gets a row. Anything not listed is forbidden.

| From | To | What triggers it |
|------|----|------------------|
| placed | packed | |
| | | |

## Shipment status

label_created, in_transit, out_for_delivery, delivered, lost.

| From | To | What triggers it |
|------|----|------------------|
| | | |

## Return status

proposed, confirmed, picked_up, refunded, rejected.

| From | To | What triggers it |
|------|----|------------------|
| | | |
