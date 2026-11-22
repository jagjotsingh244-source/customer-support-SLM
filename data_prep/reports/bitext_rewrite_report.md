# Bitext rewrite report

Setups: `gemini-4-hydrogen | prompt v5 | thinking low` 2537; `gemini-4-hydrogen | prompt v3 | thinking low` 2026; `gemini-4-hydrogen | prompt v4 | thinking low` 937. 5500 rows rewritten of 5500 sampled; 5333 pass every check (97.0%).

Checks: no `{{`, no digits, no URLs, 25 to 70 words, no exclamation marks, no lists or markup, and the last sentence is a question or an offer; no claim that the store has several of something (`store_claim`); and none of the habits banned in prompts v4 and v5 (`old_habit`: "I'd be glad/happy", naming a feeling the customer did not show, "I can't see ...").

## Drop rate per intent

| Triage | Intent | Rows | Pass | Drop rate |
|---|---|---|---|---|
| Keep | cancel_order | 300 | 299 | 0.3% |
| Keep | change_order | 300 | 299 | 0.3% |
| Keep | change_shipping_address | 300 | 299 | 0.3% |
| Keep | check_cancellation_fee | 300 | 297 | 1.0% |
| Keep | check_payment_methods | 300 | 271 | 9.7% |
| Keep | check_refund_policy | 300 | 297 | 1.0% |
| Keep | complaint | 300 | 278 | 7.3% |
| Keep | contact_customer_service | 300 | 296 | 1.3% |
| Keep | contact_human_agent | 300 | 285 | 5.0% |
| Keep | delivery_options | 300 | 227 | 24.3% |
| Keep | delivery_period | 300 | 297 | 1.0% |
| Keep | get_refund | 300 | 295 | 1.7% |
| Keep | payment_issue | 300 | 300 | 0.0% |
| Keep | track_order | 300 | 297 | 1.0% |
| Keep | track_refund | 300 | 298 | 0.7% |
| Redirect | check_invoice | 100 | 100 | 0.0% |
| Redirect | create_account | 100 | 100 | 0.0% |
| Redirect | delete_account | 100 | 100 | 0.0% |
| Redirect | edit_account | 100 | 99 | 1.0% |
| Redirect | get_invoice | 100 | 100 | 0.0% |
| Redirect | place_order | 100 | 100 | 0.0% |
| Redirect | recover_password | 100 | 100 | 0.0% |
| Redirect | registration_problems | 100 | 100 | 0.0% |
| Redirect | set_up_shipping_address | 100 | 99 | 1.0% |
| Redirect | switch_account | 100 | 100 | 0.0% |

## Why rows failed (a row can fail several checks)

| Check | Rows |
|---|---|
| store_claim | 108 |
| old_habit | 48 |
| no_next_step | 11 |

## Flags before and after the checks

| Flag | Rewritten | Passed | Kept |
|---|---|---|---|
| B | 5500 | 5333 | 97% |
| L | 4973 | 4813 | 97% |
| Q | 1794 | 1749 | 97% |
| I | 1727 | 1681 | 97% |
| M | 1071 | 1011 | 94% |
| Z | 1064 | 1040 | 98% |
| C | 684 | 634 | 93% |
| P | 466 | 456 | 98% |
| W | 464 | 460 | 99% |
| K | 377 | 371 | 98% |
| E | 371 | 355 | 96% |
| N | 166 | 164 | 99% |
| S | 36 | 36 | 100% |
| V | 26 | 26 | 100% |

## Passing replies

Words: median 34, min 25, max 57.  
Most common opening (first three words): "You want to", 184 replies (3.5%).  
Replies containing "I'd be glad" or "I'd be happy": 0.0%.  
Tokens per request (mean): 561 in, 46 out, 1121 thinking.

## Meaning check (judge and hand review)

Judge `gemini-4-hydrogen | judge j2` on the 5333 rows that passed the automatic checks: 5277 accepted (98.9%). same_request: 1 false, no_invented_content: 38 false, fitting_next_step: 17 false.  
Hand review: 200 pairs read (8 per intent), 6 rejected (2 still present after the automatic checks, 1 of them accepted by the judge).  
**Final: 5276 rows** in data/processed/bitext_final.jsonl.

| Triage | Intent | After checks | Judge accepted | Rejected by hand | Final |
|---|---|---|---|---|---|
| Keep | cancel_order | 299 | 297 | 0 | 297 |
| Keep | change_order | 299 | 299 | 0 | 299 |
| Keep | change_shipping_address | 299 | 299 | 0 | 299 |
| Keep | check_cancellation_fee | 297 | 296 | 0 | 296 |
| Keep | check_payment_methods | 271 | 259 | 1 | 259 |
| Keep | check_refund_policy | 297 | 296 | 0 | 296 |
| Keep | complaint | 278 | 278 | 0 | 278 |
| Keep | contact_customer_service | 296 | 289 | 1 | 288 |
| Keep | contact_human_agent | 285 | 278 | 0 | 278 |
| Keep | delivery_options | 227 | 208 | 0 | 208 |
| Keep | delivery_period | 297 | 297 | 0 | 297 |
| Keep | get_refund | 295 | 295 | 0 | 295 |
| Keep | payment_issue | 300 | 295 | 0 | 295 |
| Keep | track_order | 297 | 297 | 0 | 297 |
| Keep | track_refund | 298 | 297 | 0 | 297 |
| Redirect | check_invoice | 100 | 100 | 0 | 100 |
| Redirect | create_account | 100 | 100 | 0 | 100 |
| Redirect | delete_account | 100 | 100 | 0 | 100 |
| Redirect | edit_account | 99 | 99 | 0 | 99 |
| Redirect | get_invoice | 100 | 100 | 0 | 100 |
| Redirect | place_order | 100 | 100 | 0 | 100 |
| Redirect | recover_password | 100 | 100 | 0 | 100 |
| Redirect | registration_problems | 100 | 100 | 0 | 100 |
| Redirect | set_up_shipping_address | 99 | 99 | 0 | 99 |
| Redirect | switch_account | 100 | 99 | 0 | 99 |
