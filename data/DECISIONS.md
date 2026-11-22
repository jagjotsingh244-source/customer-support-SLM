# Bitext data decisions

What Nova's tone fine-tune keeps from the Bitext customer-support dataset, and why. Evidence comes from
`data_prep/bitext_eda.ipynb` (run on all 26,872 rows; lengths in Qwen3.5-2B tokens). The fine-tune's results
are read against these decisions, so each one says what it expects to change.

The rule behind all of them: the fine-tune takes Bitext's **form** (acknowledge, respond to the actual message,
one next step, polite close) and none of its **content** (procedures, menus, timelines for a company that does
not exist). Facts come from the help center and the tools.

## 1. Intent triage

Raw counts are flat (950 to 1,000 rows per intent), so triage is about Nova's job, not balance.
**Keep** = Nova answers it with a tool or a help-center page. **Redirect** = outside Nova's tools; teach a short,
honest pointer to the website or a teammate. **Drop** = no value for a support assistant.

| Intent | Category | Decision | Why |
|---|---|---|---|
| cancel_order | CANCEL | Keep | `kb/cancellations.md` + order status tool |
| check_cancellation_fee | CANCEL | Keep | `kb/cancellations.md` |
| change_order | ORDER | Keep | Order status decides what can change (before shipping only) |
| track_order | ORDER | Keep | `get_tracking` |
| place_order | ORDER | Redirect | Nova cannot place orders |
| track_refund | REFUND | Keep | Refund status from the order tools |
| get_refund | REFUND | Keep | Returns and refunds pages, `propose_return` |
| check_refund_policy | REFUND | Keep | `kb/refunds-*.md`, `kb/returns-*.md` |
| delivery_options | DELIVERY | Keep | `kb/shipping-charges.md`, `kb/shipping-times.md` |
| delivery_period | DELIVERY | Keep | `kb/shipping-times.md` |
| change_shipping_address | SHIPPING | Keep | `kb/account-and-address.md` (order address before shipping) |
| set_up_shipping_address | SHIPPING | Redirect | Saved addresses are managed in the account, not by Nova |
| payment_issue | PAYMENT | Keep | `kb/payment-failures.md` |
| check_payment_methods | PAYMENT | Keep | `kb/payment-failures.md` (payment methods), `kb/cash-on-delivery.md` |
| complaint | FEEDBACK | Keep | Tone under frustration; often ends in a handoff |
| review | FEEDBACK | Drop | Nova does not collect reviews |
| contact_human_agent | CONTACT | Keep | `escalate_to_human`, `kb/contacting-a-human.md` |
| contact_customer_service | CONTACT | Keep | `kb/contacting-a-human.md` |
| create_account | ACCOUNT | Redirect | No account tools |
| delete_account | ACCOUNT | Redirect | No account tools; privacy-sensitive, so point to a teammate |
| edit_account | ACCOUNT | Redirect | No account tools |
| switch_account | ACCOUNT | Redirect | No account tools; Bitext's account tiers ("{{Account Type}}") do not exist at NimbusCart |
| recover_password | ACCOUNT | Redirect | `kb/account-and-address.md` (signing in) gives the pointer; Nova never handles passwords |
| registration_problems | ACCOUNT | Redirect | No account tools |
| get_invoice | INVOICE | Redirect | No invoice tool or help-center page |
| check_invoice | INVOICE | Redirect | No invoice tool or help-center page |
| newsletter_subscription | SUBSCRIPTION | Drop | Not support work |

Totals: 15 keep, 10 redirect, 2 drop. Two kept intents (`change_shipping_address`, `payment_issue`) are held out
whole as an unseen-intent test.

**Expect:** after fine-tuning, account and invoice questions get a short pointer, not an invented procedure.

## 2. Reply length and form: 25 to 70 words, no lists, no exclamation marks

Evidence:
- Replies have a median of 104 tokens (90 words), p90 220, p99 366. Only 23% fall in 25 to 70 words; 76% are longer.
- Length varies 7x by intent: median 48 tokens for `check_cancellation_fee`, 340 for `check_refund_policy`.
  Trained as is, the model learns that some topics deserve an essay.
- 54% of replies contain an exclamation mark, 23% a numbered list, 5% markdown bold.
- Stock openers repeat: "Thank you for" starts 13% of replies; "I'm on it!", "I'll take care" and two others
  start exactly 370 replies each (a generation template).

Decision: every kept reply is rewritten to 25 to 70 words (about 30 to 85 tokens at 1.21 tokens per word),
plain sentences, no lists or headers, no exclamation marks, and no stock opener used more than a few percent of
the time. The rewrite checks drop anything outside these limits.

**Expect:** Nova's median reply length on the golden set falls to the 25–70 word band, and no reply contains a list.

## 3. Deduplicate on the customer message, within intent, before splitting

Evidence:
- 2,237 exact duplicate questions; 2,888 after normalising (lowercase, strip punctuation, collapse spaces);
  3,108 when rows also count as duplicates if their first 12 normalised words match.
- Duplicates are concentrated: 59% of `cancel_order` rows repeat an earlier question (about 410 distinct out of
  998), then `delivery_options` 36%, `track_refund` 32%.
- No normalised question appears under two intents, so there are no label conflicts.
- Only 2 replies are duplicated; the same question carries many different replies.

Decision: drop a row if its normalised message, or its first 12 normalised words, match an earlier row's.
Run it once on the full dataset before sampling and before any split, so near-copies never sit on both sides.
Sample at most 300 rows per kept intent and 100 per redirect intent from what survives.
After this rule and the placeholder rule in decision 4, 22,576 rows survive; the smallest kept intent is
`cancel_order` with 413 distinct questions, so every kept intent can fill its 300.

**Expect:** no cancellation drift: golden-set replies to questions that are not about cancelling do not bring
up cancelling.

## 4. Placeholders: never fill on Nova's side; fill with seeded NimbusCart-format values on the customer's side

Evidence:
- 13,006 of 26,872 replies (48%) contain a placeholder; 391 distinct kinds. Top: Order Number (5,122),
  Account Type (4,429), Account Category (3,078), Online Order Interaction (2,699), Customer Support Phone
  Number (2,635), Website URL (2,534), Customer Support Hours (2,325).
- `cancel_order` replies average 8 placeholders each: the menu paths live there.
- 6,670 customer messages also contain one: Order Number (2,907), Account Type (1,011), Person Name (887),
  Account Category (822), Refund Amount (624), Currency Symbol (372), Delivery City (234), Delivery Country (177).

Decision:
- **Replies:** never replace a placeholder with a NimbusCart value. The rewrite removes the sentence's need for
  the fact; a rewritten reply containing `{{` is dropped.
- **Customer messages:** these are the customer's own details, so fill them with seeded fake values in
  NimbusCart's formats: order numbers as 5-digit IDs (10001 and up), Indian names, rupee amounts (₹), Indian
  cities, invoice numbers in one made-up format. Countries are a mix of India and other countries, because
  "do you ship to {{Delivery Country}}" is a question about shipping abroad. The help center says nothing about
  shipping outside India, so those replies must not answer it; they offer to check or to connect a teammate. Drop rows whose message uses a placeholder with no NimbusCart equivalent
  (Account Type, Account Category). 239 messages (185 `track_refund`, 54 `get_refund`) say "{{Refund Amount}}
  dollars"; replace the word with rupees along with the amount. Keep the original message too, untouched, in the
  separate questions dataset.

**Expect:** zero `{{` in any generated reply, and no menu path or URL that is not in the help center.

## 5. Keep the phrasing flags on every row, and check the rare ones survive

Evidence (rows with each flag): basic syntax B 26,872, lexical L 24,115, colloquial Q 8,968,
interrogative I 7,839, typos Z 5,286, morphological M 4,920, coordinated C 2,646, keyword K 2,227,
abbreviations E 1,882, politeness P 1,329, offensive W 1,288, negation N 463, S 417, V 77.
S and V are not described in the dataset card. All 417 S rows are `delivery_options` questions about shipping
to a place; V rows (mostly `get_refund` and `recover_password`) state something already done ("I have paid ...").

Decision: carry `flags` through every step so results can be broken down by phrasing. After dedup and sampling,
report the count per flag and make sure N, W, P and K are not thinned out more than the overall sampling rate.
The golden set gets cases with negation, offensive language, keyword-only messages and heavy typos.

**Expect:** the fine-tune's scores on typo, keyword and offensive messages are within a few points of its scores
on clean messages; a larger gap means the data did not cover them.

What happened: dedup thinned keyword messages (8.3% of raw rows, 5.8% of the deduped pool, 4.7% of a plain
sample), so the sample gives rows with K, N, W or P double weight. Sampled shares: keyword 6.9%, negation 3.0%,
offensive 8.4%, politeness 8.5%, all at or above their share of the deduped pool.

Gap found: the golden set's first turns contain no offensive messages, 3 with heavy typos, 3 polite ones and 4
keyword-length ones (negation is covered: 12). Closed with 12 phrasing probes in `evals/probes/phrasing.jsonl`:
3 each of offensive, typo-heavy, polite and keyword-only, each a rewording of a golden case with the same
customer, order and expectations (`evals/validate.py --probes` enforces that). They stay out of the 100-case
golden set so baseline scores remain comparable, and `evals/run_eval.py --cases probes --paired-run <golden run>`
reports each probe next to its clean twin. With 3 cases per phrasing, a difference of one case is noise; the probes
flag large gaps, they do not measure small ones.

## 6. Rewrite the replies with a larger model, and read the output for new habits

Rewriting removes Bitext's content, but a rewriting model has habits of its own, and a 2B model trained on its
output copies them. Each full run was measured for repeated phrases, and each habit found became a rule in the
next prompt version (`PROMPT_VERSION` in `data_prep/prepare_bitext.py`). Rows that did not show the habit kept
their earlier rewrite; only rows that did were redone.

| Prompt | Found in its output | Rule added |
|---|---|---|
| v1 (50-row test) | stiff ("I do not", "I am"), filler ("I am here to help you") | contractions, no filler |
| v2 (50-row test) | 19% opened "You're looking to"; invented rules ("not always possible once an order is placed") | ban stock openers; never explain when something is possible |
| v3 (full run, 5,500) | 31% of replies said "I'd be glad" | ban "I'd be glad" / "I'd be happy" (v4) |
| v4 | 21% of calm customers were told their situation was "frustrating"; 21% said "I don't have ... in front of me" before offering to check | name a feeling only if the customer shows one; go straight to the next step (v5) |

Model `gemini-4-hydrogen` at thinking level "low" (the default level spent about 2,250 thinking tokens to write a
50-token reply; "low" about 1,050). Automatic checks and the drop rate per intent:
`data_prep/reports/bitext_rewrite_report.md`.

The meaning judge (`data_prep/review_rewrites.py`) was tested first on 20 hand-written pairs with planted mistakes
(`data_prep/check_judge.py`): it caught all 12 bad ones once the rule "exactly one next step" was spelled out.
Writing the test also showed two of my own "good" pairs were not: one stated a refund rule, one offered two next steps.

Results of the meaning check, and what it could not catch:
- The judge accepted 5,277 of the 5,333 rows that passed the automatic checks. It caught every reply listing
  payment methods (all 29 with "bank transfer", all 17 with "PayPal").
- It caught only 3 of the 6 rows rejected in the 200-pair hand review. It let through vague claims about the
  store ("We offer a few different shipping options": about half of 88 such rows) and one reply saying Nova cannot
  hand off to a person. Vague quantity claims became an automatic check (`store_claim`, 108 rows dropped).
- The hand review also found "I haven't seen your order details yet", the "can't see" filler in new words (31% of
  `cancel_order` replies); it joined the banned habits and those 332 rows were redone.

Final: **5,276 rows** (`data/processed/bitext_final.jsonl`). Split into train 4,447, validation 235 and
`test_unseen_intents` 594. Rendered with the Qwen3.5-2B template, examples run to median 224 and at most 255
tokens (p99 245), so **max_seq_length is 256**. Every example's trained tokens decode to exactly its reply plus
`<|im_end|>`.

**Expect:** no stock phrase in more than about 5% of Nova's replies after fine-tuning.

## Reading notes (5 rows per intent)

Sample in `data/eda/reading_sample.md` (seed 3407, not in Git). One line per intent: what a good Nova reply would do differently.
First pass written by Gemini (`gemini-4-hydrogen`, temperature 0.2) with `data_prep/reading_notes.py`, which also saves
the patterns behind each note to `data/eda/reading_notes.json`; spot-checked against the sample by hand. Two notes were corrected by hand where they promised something Nova
cannot do (`payment_issue`: "take the report"; `complaint`: "look up the complaint policy", which does not exist).

| Intent | Note |
|---|---|
| cancel_order | Instead of listing self-service portal steps or telling customers to call support, acknowledge the cancellation request and offer to check the order status or cancellation eligibility. |
| check_cancellation_fee | Drop the invented fee menu paths, contract jargon, and exclamation marks; offer to look up NimbusCart's cancellation fee policy or check their specific order directly. |
| change_order | Check the order's eligibility or ask one clear question about the item change needed, without promising edits or giving fabricated self-service menu steps and contact placeholders. |
| track_order | Instead of deflecting customers to website tracking pages, acknowledge the order number they shared and offer to check its live status or ETA directly. |
| place_order | Skip invented checkout steps and item-detail probes; warmly direct customers to order on NimbusCart's website and offer a teammate if they get stuck. |
| track_refund | Drop {{...}} placeholders and 'allow me a moment' stalling, use plain 'refund' wording, and end by asking for their order number to check its status. |
| get_refund | Drop robotic openers and support redirects; offer to check NimbusCart's refund policy for general queries or ask for their order number to check a refund. |
| check_refund_policy | Drop generic numbered refund scenarios and website menu paths; address their specific policy, timeline, or guarantee question plainly and offer to check NimbusCart's policy or their order. |
| delivery_options | Drop the numbered shipping-tier lists and blind international-shipping claims; acknowledge frustration, and ask their location or offer to check current delivery policies. |
| delivery_period | Drop the stiff empathy and placeholders, distinguish general delivery timeframe questions from existing orders, and end directly by asking for an order number or checking shipping policy. |
| change_shipping_address | Drop numbered account-menu steps and support referrals; clarify if they mean an already-placed order or their saved address, and offer to check their order. |
| set_up_shipping_address | Replace guessed numbered menu paths with a plain redirect to their NimbusCart account, acknowledge frustration first, and end with one step like connecting a teammate. |
| payment_issue | Instead of sending customers to phone, email or live chat, Nova asks what went wrong with the payment and offers to check the order, or to connect a teammate. |
| check_payment_methods | Skip invented menu paths and bulleted payment lists; acknowledge any frustration, and offer to look up NimbusCart's current payment options in our help center. |
| complaint | Instead of bouncing customers to 'Customer Support' with fake menu paths or placeholders, Nova acknowledges the problem and asks what went wrong or offers a teammate. |
| review | Keep it concise without exclamation marks, drop invented feedback pages or email placeholders, acknowledge frustration like swearing, and offer to look up review steps or connect a teammate. |
| contact_human_agent | Skip the fake website menus, robotic empathy openers, and platform questions; plainly offer to connect a teammate directly or ask one brief question about their issue. |
| contact_customer_service | Drop exclamation marks, robotic restatements, and placeholder hours or invented channels; instead look up NimbusCart's support hours or offer to connect a teammate. |
| create_account | Instead of collecting personal details or listing sign-up steps, honestly explain Nova cannot create accounts, point them to NimbusCart's site or offer to connect a teammate. |
| delete_account | Drop numbered menu steps, {{Account Type}} tags, and offers to guide closure; honestly state Nova cannot delete accounts and point to the website or connect a teammate. |
| edit_account | Drop the gushing praise, invented menu paths, and promises to edit details step by step; honestly say Nova cannot update accounts and point to the website or a teammate. |
| switch_account | Briefly state you cannot switch account types directly, drop the step-by-step menu paths and upgrade hype, acknowledge frustration, and point to the website or offer a teammate. |
| recover_password | Skip numbered reset steps, button labels, and URL placeholders; honestly state Nova cannot reset passwords, PINs, or access keys, and point to the site or connect a teammate. |
| registration_problems | Skip thanking them for feedback or promising to fix the signup bug, drop fake contact details, and honestly offer to connect a teammate to log their registration error. |
| get_invoice | Instead of inventing Billing menu paths or promising to email invoices, Nova should honestly explain it cannot pull bills and point to the website or connect a teammate. |
| check_invoice | Drop placeholders, numbered menu steps, and requests for date ranges; honestly state Nova cannot pull invoices and point to the website or connect a teammate. |
| newsletter_subscription | Skip email-based newsletter lookups, invented signup paths, and promotional pitches; check the help center for newsletter instructions or connect a teammate instead. |
