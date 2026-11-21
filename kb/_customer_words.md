# How customers say it

Not indexed. Customers rarely use the help center's terms, so retrieval must
find the right page from their words. Each row is a test: the phrase on the
left should retrieve the page on the right.

Scope: English only, including Indian English ("money cut", "delivery boy").
Nova's training data (Bitext and the synthetic conversations) is English, so
Hinglish is out of scope for the scored tests. A few Hinglish phrases are kept
at the end as an unscored probe, to measure the gap without counting it.

| Customer says | Help-center term | Page |
|---|---|---|
| money back, get my money back, when will my refund come | refund | refunds-timing |
| when will I get my money, how many days for refund | refund timing | refunds-timing |
| money went back to which account, refund to another card | refund by payment method | refunds-payment-methods |
| I returned one thing, why so little refund, delivery charge not refunded | partial refund | refunds-partial |
| send it back, give it back, exchange this | return | returns-general |
| how many days to return, last date to return | return window | returns-general |
| I opened the earbuds, used the speaker once | opened electronics | returns-electronics |
| why can't I return earphones, no return option | not returnable | returns-non-returnable |
| I want to cancel, don't want it anymore, stop my order | cancellation | cancellations |
| parcel, package, box, courier | shipment | order-tracking |
| where is my stuff, when will my order come, track my parcel | tracking | order-tracking |
| AWB number, consignment number, docket number | tracking number | order-tracking |
| how long does delivery take, when will it reach Ludhiana | shipping times | shipping-times |
| delivery fee, why ₹49 extra, delivery charges | shipping charge | shipping-charges |
| only half my order came, second box missing, one item didn't come | split shipment | shipping-split-shipments |
| it's late, still not here, stuck for days | delayed shipment | delays-and-lost-shipments |
| no update for a week, parcel is lost | possible loss | delays-and-lost-shipments |
| says delivered but I didn't get it, never received | delivered but not received | delays-and-lost-shipments |
| money cut but order not placed, amount debited, payment stuck | failed payment | payment-failures |
| pay on delivery, cash payment, COD | cash on delivery | cash-on-delivery |
| guarantee, it stopped working after 2 months, repair | warranty | warranty |
| change my address, wrong address, deliver to office instead | address change | account-and-address |
| talk to a person, customer care number, real human, agent | support team | contacting-a-human |
| complaint, case number, my issue is still open | ticket | contacting-a-human |
| can you tell me my wife's order, check someone else's order | privacy | privacy |

## Not scored: Hinglish probe

Run separately and reported on its own, never mixed into the scores above. It
shows how far an English-only Nova is from customers who write in Hinglish.

| Customer says | Page |
|---|---|
| refund kab aayega, paisa wapas kab milega | refunds-timing |
| order cancel karna hai | cancellations |
| mera order kab aayega | order-tracking |
| paise kat gaye par order nahi hua | payment-failures |
