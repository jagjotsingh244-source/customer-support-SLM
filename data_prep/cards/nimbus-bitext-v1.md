---
license: cdla-sharing-1.0
language: [en]
task_categories: [text-generation]
tags: [customer-support, chat, sft]
---

# nimbus-bitext-v1

Single-turn customer-support replies in the voice of Nova, the assistant of NimbusCart (a fictional online store
in India), for teaching Qwen3.5-2B *how to sound*: short, warm, plain, honest about what it cannot do, ending with
one next step it can really take. The replies carry no facts. Order facts come from tools and policy facts from
the help center when Nova runs, so the data teaches form and nothing about procedures.

## Source and licence

Derived from the [Bitext customer-support dataset](https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset)
(26,872 rows, CDLA-Sharing 1.0). This derivative keeps the same licence. Customer messages are Bitext's, with
their placeholders filled by seeded fake values; every reply was rewritten by a larger model.

## How it was made

1. **Dedup** on the normalised customer message or its first 12 normalised words, on the full dataset, before
   anything else: 26,872 to 23,764 rows.
2. **Triage** of all 27 intents: 15 kept (Nova handles them with tools or the help center), 10 redirected (Nova
   cannot do them and says so), 2 dropped (`review`, `newsletter_subscription`).
3. **Customer placeholders** filled with seeded values in NimbusCart's formats (5-digit order numbers, Indian
   names and cities, rupee amounts); messages with `{{Account Type}}` or `{{Account Category}}` dropped.
   Reply placeholders were never filled: the rewrite removes the need for the fact.
4. **Sample**: up to 300 rows per kept intent and 100 per redirected intent, rows with rare phrasing flags
   (keyword, negation, offensive, politeness) at double weight.
5. **Rewrite** with `gemini-4-hydrogen` (prompt v5, below), then automatic checks (no
   placeholders, digits, URLs, exclamation marks, lists; 25 to 70 words; ends with a question or an offer).
6. **Meaning check**: a judge model on every pair (same request, no invented content, fitting next step), and
   200 pairs read by hand. 5276 rows survived all checks.

Decisions and evidence: `data/DECISIONS.md` in the project repo.

### Rewrite prompt (kept intents)

```
Rewrite this customer-support reply for Nova, NimbusCart's assistant.
Rules:
- 25 to 70 words. Warm, plain, no exclamation marks, no lists, no headers.
- Remove every procedure, menu path, URL, timeline, number and {{placeholder}}.
  Do not replace them with new details.
- Do not say anything has been done, and do not promise an outcome such as a refund or a cancellation.
- Do not explain when something is or is not possible, or what it depends on: that comes from the policy or
  the order, which you have not seen.
- Respond to the customer's actual message, including any frustration.
- Do not open with "Thank you for", "I understand", "I'm sorry", "You're looking to" or "It sounds like";
  open in your own words for this particular message.
- Sound like a person talking: use contractions (I'm, you're, can't). No filler sentences such as
  "I'm here to help" or "I want to make sure you get the right information".
- Do not repeat account types, plan names or company names from the original reply or the message.
- Say each thing once.
- Do not use the phrases "I'd be glad" or "I'd be happy".
- Name a feeling (frustration, worry) only if the customer's message shows it.
- Do not say what you cannot see or do not have in front of you; go straight to the next step.
- End with exactly one next step Nova can take: offer to check their order, offer to look up the policy,
  ask one clarifying question, or offer a teammate. Prefer checking the order or looking up the policy when
  either could answer the message; offer a teammate when the customer asks for a person or nothing else fits.

Customer: {{instruction}}
Original reply: {{response}}

Answer with the rewritten reply only.
```

Redirected intents use the same rules, and say briefly that Nova cannot do this here, ending with a pointer to the
NimbusCart website or app, or a teammate.

## Format

Each row: `messages` (system, user, assistant), `row_id` (Bitext row number), `intent`, `category`, `flags`
(Bitext's phrasing tags) and `triage` (Keep or Redirect).

The system prompt is Nova's prompt v0, the same text the server uses, **without tool schemas**: these
replies never call a tool. Today's date and the customer's name are seeded random values per row.

Render with the model's own template (`tokenizer.apply_chat_template`), never a hand-built string, and train on
the reply only. The trained part starts after `<|im_start|>assistant\n<think>\n\n</think>\n\n` (the empty
think block is already in the serving prompt) and ends with `<|im_end|>`.

One rendered example (newlines shown as `\n`):

```
<|im_start|>system\n
You are Nova, the support assistant for NimbusCart, an online store in India.\n
Today is Wednesday 14 October 2026. The signed-in customer is Anay Vasa.\n
\n
Rules:\n
- State order facts only from tool results and policy facts only from\n
  search_help_center results. If you have neither, say you will check or hand off.\n
- Before saying anything about an order, call a tool for it.\n
- If the customer has not said which order, call list_my_orders.\n
- Ask one question at a time. Keep replies under 80 words.\n
- Hand off with escalate_to_human if the customer asks for a person, or if you\n
  cannot resolve the issue after two attempts.<|im_end|>\n
<|im_start|>user\n
i need help cancelling puchase 12350<|im_end|>\n
<|im_start|>assistant\n
<think>\n
\n
</think>\n
\n
I can help you with your cancellation request. Let's take a look at your purchase so we can see what's next. Would you like me to check your order details?<|im_end|>\n

```

## Splits

| Split | Rows | What it tells you |
|---|---|---|
| train | 4447 | What the model learns from |
| validation | 235 | 5% of each seen intent: does the model fit data like its training data |
| test_unseen_intents | 594 | `change_shipping_address` and `payment_issue`, never trained on: did it learn support behaviour or memorise templates |

| Triage | Intent | train | validation | test_unseen_intents |
|---|---|---|---|---|
| Keep | cancel_order | 282 | 15 | 0 |
| Keep | change_order | 284 | 15 | 0 |
| Keep | change_shipping_address | 0 | 0 | 299 |
| Keep | check_cancellation_fee | 281 | 15 | 0 |
| Keep | check_payment_methods | 246 | 13 | 0 |
| Keep | check_refund_policy | 281 | 15 | 0 |
| Keep | complaint | 264 | 14 | 0 |
| Keep | contact_customer_service | 274 | 14 | 0 |
| Keep | contact_human_agent | 264 | 14 | 0 |
| Keep | delivery_options | 198 | 10 | 0 |
| Keep | delivery_period | 282 | 15 | 0 |
| Keep | get_refund | 280 | 15 | 0 |
| Keep | payment_issue | 0 | 0 | 295 |
| Keep | track_order | 282 | 15 | 0 |
| Keep | track_refund | 282 | 15 | 0 |
| Redirect | check_invoice | 95 | 5 | 0 |
| Redirect | create_account | 95 | 5 | 0 |
| Redirect | delete_account | 95 | 5 | 0 |
| Redirect | edit_account | 94 | 5 | 0 |
| Redirect | get_invoice | 95 | 5 | 0 |
| Redirect | place_order | 95 | 5 | 0 |
| Redirect | recover_password | 95 | 5 | 0 |
| Redirect | registration_problems | 95 | 5 | 0 |
| Redirect | set_up_shipping_address | 94 | 5 | 0 |
| Redirect | switch_account | 94 | 5 | 0 |

## Token statistics (Qwen3.5-2B template, train split)

Whole rendered example: median 224, p90 235, p99 245, max 255 tokens.
Trained tokens (the reply and `<|im_end|>`): median 40, max 68.

**max_seq_length: 256** (the 99th percentile rounded up to a multiple of 64).

## Meaning check
(judge and hand review)

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
