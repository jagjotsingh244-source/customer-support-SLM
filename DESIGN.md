# Nova design

Nova is NimbusCart's customer-support assistant, built on Qwen3.5-2B.
This file decides where every capability lives and the budgets the system must fit inside.

## The four rules

1. **If it changes often, retrieve it (RAG):** policies, shipping charges, warranty terms.
2. **If it belongs to one customer, fetch it with a tool:** orders, tracking, returns.
3. **If it describes how to act, train it (fine-tune):** tone, one question at a time, calling the right tool before talking about an order, escalating after two failed turns.
4. **If it is a hard rule, enforce it in code:** who may see which order, whether a return is eligible, what counts as a confirmed write.

## Capability map

| Capability | Mechanism | Why this mechanism | How it is measured |
|---|---|---|---|
| Greet and set tone | Fine-tune (+ short system prompt) | Tone is behaviour, not a fact; a 2B model follows long prompt instructions loosely, and every prompt token costs latency on every turn | Rubric score (friendly, concise, on-brand) on held-out openers; reply length within limit; asks at most one question |
| Return-window questions | RAG | Policy changes (e.g. electronics 30 → 15 days); answer must cite current text | Required fact present; citation points at the right chunk |
| Refund-timeline questions | RAG | Timelines vary by payment method and change; must quote the current help-center text, never a remembered number | Required fact present; citation points at the right chunk; no number appears that is absent from retrieved chunks |
| List the customer's recent orders | Tool + fine-tune + code | Data is per customer and live; training teaches when to call; backend scopes the query to the signed-in customer | Correct tool called; listed orders exactly match the DB rows for that customer; zero invented orders |
| Report an order's status | Tool + fine-tune | Data is per customer; training teaches when to call | Tool name and arguments match exactly |
| Give tracking details | Tool + fine-tune | Carrier, tracking number and ETA are live data; training teaches the model to call the tool before stating any date | Carrier, tracking number and dates in the reply match the tool output exactly; no date stated without a tool call |
| Start a return | Tool + code + fine-tune | Eligibility (window, item category, delivered status) is a hard rule decided by the backend; the write happens only after explicit confirmation; training teaches the confirm-then-act flow | Tool arguments correct; backend rejects 100% of ineligible returns; no return created without a confirmed turn |
| Refuse other customers' data | Code | Must hold every time | Cross-customer test returns "not found" |
| Hand off to a human | Fine-tune + tool | When to escalate (explicit request, two failed turns, frustration) is behaviour; the handoff itself is an action | Escalation precision and recall on a labelled set; scripted two-failure conversations escalate by turn 3 |
| Resist "ignore your instructions" | Code + fine-tune | Code guarantees no privilege change no matter what the model says; training teaches a polite refusal that stays on task | Injection red-team set: 0 data leaks or unauthorised actions (must be 100%); refusal rate on attacks; false-refusal rate on benign requests |

## Budgets

Targets are product requirements: change them only deliberately, with a written reason.
Estimates get replaced by measurements as the course goes on.

- **p95 latency, reply with one tool call: 3 s** — *target*. Covers both model passes (emit the tool call, then answer from the result) plus the DB query.
- **Context window: 8,192 tokens** — *target* for the total. The split is an *estimate*:
  - system prompt: 500 (measure in Module 2)
  - tool schemas: 700 (measure in Lesson 0.3)
  - history: 4,000 (refine in Modules 7–8)
  - retrieved chunks: 2,000, e.g. 4 × 500 (refine in Module 5)
  - reply headroom: 992
- **Cost per 1,000 conversations: ~$5** — *estimate*. Assumes a GPU at about $1/hour serving about 200 conversations/hour. Replace with the real GPU rate and measured throughput in Module 10.

## Change log

Record every budget or mechanism change: old → new, and the evidence.

| Date | Change | Reason |
|---|---|---|
| 2026-11-20 | First draft | Lesson 0.1 |
