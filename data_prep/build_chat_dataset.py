"""Turn the reviewed Bitext rewrites into nimbus-bitext-v1: chat messages, three splits, token stats, a card.

Each row becomes system / user / assistant messages. The system prompt is Nova's v0 prompt from agent/prompts.py,
the one the server uses, with no tool schemas (these replies never call a tool, so showing tools would teach the
model to ignore them). {today} and {customer_name} are filled with seeded random values per row, so the model
does not memorise one date or one name.

Splits, made after dedup (prepare_bitext.py dedups the full dataset first):
- test_unseen_intents: every row of change_shipping_address and payment_issue, never trained on.
- validation: 5% of each remaining intent (seed 3407).
- train: the rest.

Token stats are measured on the rendered examples with Qwen3.5-2B's chat template; max_seq_length is the 99th
percentile rounded up to a multiple of 64. The card goes to data_prep/cards/nimbus-bitext-v1.md and, with --push,
to the Hub with the data (private). --push also uploads the untouched questions as nimbus-bitext-questions.

    uv run --group data --group local-model python data_prep/build_chat_dataset.py
    uv run --group data --group local-model python data_prep/build_chat_dataset.py --push    # needs hf auth login
"""

import argparse
import math
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from datasets import Dataset, DatasetDict
from faker import Faker
from transformers import AutoTokenizer

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from agent.prompts import PROMPT_VERSION, system_prompt  # noqa: E402
from data_prep.prepare_bitext import PROMPT_VERSION as REWRITE_PROMPT_VERSION  # noqa: E402
from data_prep.prepare_bitext import PROMPTS, RULES  # noqa: E402
from training.masking import IGNORE, RESPONSE_PART, tokenize  # noqa: E402

PROCESSED = REPO / "data" / "processed"
INPUT = PROCESSED / "bitext_final.jsonl"
QUESTIONS = PROCESSED / "bitext_questions.parquet"
OUT = PROCESSED / "nimbus-bitext-v1"
CARD = REPO / "data_prep" / "cards" / "nimbus-bitext-v1.md"
REPORT = REPO / "data_prep" / "reports" / "bitext_rewrite_report.md"
MODEL = "Qwen/Qwen3.5-2B"
HUB_USER = "123jagjot"
SEED = 3407
HELD_OUT = ("change_shipping_address", "payment_issue")
VAL_SHARE = 0.05
FIRST_DAY = datetime(2026, 1, 1)


QUESTIONS_CARD = """---
license: cdla-sharing-1.0
language: [en]
---

# nimbus-bitext-questions

All 26,872 customer messages from the [Bitext customer-support dataset](https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset),
untouched (placeholders such as `{{Order Number}}` kept), with Bitext's `flags`, `category` and `intent` and the
original row number. Kept apart from the replies: these are opening lines for tool-using conversations with Nova,
NimbusCart's support assistant. Licence CDLA-Sharing 1.0, as the source.
"""


def session(row_id: int) -> tuple[datetime, str]:
    """A seeded date in 2026 and an Indian customer name for one row."""
    rng = random.Random(f"{SEED}-session-{row_id}")
    fake = Faker("en_IN")
    fake.seed_instance(f"{SEED}-session-{row_id}")
    return FIRST_DAY + timedelta(days=rng.randrange(365)), fake.name()


def to_example(row) -> dict:
    today, name = session(row["row_id"])
    return {"messages": [{"role": "system", "content": system_prompt(today, name)},
                         {"role": "user", "content": row["instruction"]},
                         {"role": "assistant", "content": row["rewritten"]}],
            "row_id": int(row["row_id"]), "intent": row["intent"], "category": row["category"],
            "flags": row["flags"], "triage": row["triage"]}


def split(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    held = df[df.intent.isin(HELD_OUT)]
    seen = df[~df.intent.isin(HELD_OUT)]
    val = seen.groupby("intent", group_keys=False)[list(seen.columns)].apply(
        lambda g: g.sample(max(1, round(len(g) * VAL_SHARE)), random_state=SEED))
    train = seen.drop(val.index)
    return {"train": train, "validation": val, "test_unseen_intents": held}


def token_stats(examples: list[dict], tok) -> pd.DataFrame:
    rows = []
    for ex in examples:
        enc = tokenize(ex["messages"], tok)
        rows.append({"total": len(enc["input_ids"]), "trained": sum(l != IGNORE for l in enc["labels"])})
    return pd.DataFrame(rows)


def annotated_render(example: dict, tok) -> str:
    text = tok.apply_chat_template(example["messages"], tokenize=False)
    return text.replace("\n", "\\n\n")


def card(splits, stats, max_len, render, n_input) -> str:
    sizes = {k: len(v) for k, v in splits.items()}
    by_intent = pd.concat([v.assign(split=k) for k, v in splits.items()]).pivot_table(
        index=["triage", "intent"], columns="split", values="row_id", aggfunc="count", fill_value=0)
    cols = [c for c in ("train", "validation", "test_unseen_intents") if c in by_intent]
    intent_table = "\n".join(
        ["| Triage | Intent | " + " | ".join(cols) + " |", "|---|---|" + "---|" * len(cols)]
        + [f"| {t} | {i} | " + " | ".join(str(by_intent.loc[(t, i), c]) for c in cols) + " |"
           for t, i in by_intent.index])
    q = stats.total.quantile([.5, .9, .99]).round().astype(int)
    report_meaning = REPORT.read_text().split("## Meaning check")[-1] if REPORT.exists() else ""
    rules = RULES.format()
    return f"""---
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
   names and cities, rupee amounts); messages with `{{{{Account Type}}}}` or `{{{{Account Category}}}}` dropped.
   Reply placeholders were never filled: the rewrite removes the need for the fact.
4. **Sample**: up to 300 rows per kept intent and 100 per redirected intent, rows with rare phrasing flags
   (keyword, negation, offensive, politeness) at double weight.
5. **Rewrite** with `gemini-4-hydrogen` (prompt {REWRITE_PROMPT_VERSION}, below), then automatic checks (no
   placeholders, digits, URLs, exclamation marks, lists; 25 to 70 words; ends with a question or an offer).
6. **Meaning check**: a judge model on every pair (same request, no invented content, fitting next step), and
   200 pairs read by hand. {n_input} rows survived all checks.

Decisions and evidence: `data/DECISIONS.md` in the project repo.

### Rewrite prompt (kept intents)

```
{PROMPTS["Keep"].format(rules=rules, instruction="{{instruction}}", response="{{response}}")}
```

Redirected intents use the same rules, and say briefly that Nova cannot do this here, ending with a pointer to the
NimbusCart website or app, or a teammate.

## Format

Each row: `messages` (system, user, assistant), `row_id` (Bitext row number), `intent`, `category`, `flags`
(Bitext's phrasing tags) and `triage` (Keep or Redirect).

The system prompt is Nova's prompt {PROMPT_VERSION}, the same text the server uses, **without tool schemas**: these
replies never call a tool. Today's date and the customer's name are seeded random values per row.

Render with the model's own template (`tokenizer.apply_chat_template`), never a hand-built string, and train on
the reply only. The trained part starts after `{RESPONSE_PART.encode("unicode_escape").decode()}` (the empty
think block is already in the serving prompt) and ends with `<|im_end|>`.

One rendered example (newlines shown as `\\n`):

```
{render}
```

## Splits

| Split | Rows | What it tells you |
|---|---|---|
| train | {sizes["train"]} | What the model learns from |
| validation | {sizes["validation"]} | 5% of each seen intent: does the model fit data like its training data |
| test_unseen_intents | {sizes["test_unseen_intents"]} | `{HELD_OUT[0]}` and `{HELD_OUT[1]}`, never trained on: did it learn support behaviour or memorise templates |

{intent_table}

## Token statistics (Qwen3.5-2B template, train split)

Whole rendered example: median {q[.5]}, p90 {q[.9]}, p99 {q[.99]}, max {stats.total.max()} tokens.
Trained tokens (the reply and `<|im_end|>`): median {stats.trained.median():.0f}, max {stats.trained.max()}.

**max_seq_length: {max_len}** (the 99th percentile rounded up to a multiple of 64).

## Meaning check
{report_meaning.strip()}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, default=INPUT)
    ap.add_argument("--push", action="store_true", help="push both datasets to the Hub (private)")
    a = ap.parse_args()

    df = pd.read_json(a.input, lines=True)
    tok = AutoTokenizer.from_pretrained(MODEL)
    parts = split(df)
    examples = {k: [to_example(r) for r in v.to_dict("records")] for k, v in parts.items()}
    stats = token_stats(examples["train"], tok)
    max_len = math.ceil(stats.total.quantile(.99) / 64) * 64
    print({k: len(v) for k, v in examples.items()}, f"max_seq_length {max_len}")

    dd = DatasetDict({k: Dataset.from_list(v) for k, v in examples.items()})
    dd.save_to_disk(OUT)
    CARD.parent.mkdir(parents=True, exist_ok=True)
    CARD.write_text(card(parts, stats, max_len, annotated_render(examples["train"][0], tok), len(df)))
    print(f"saved {OUT.relative_to(REPO)} and {CARD.relative_to(REPO)}")

    if a.push:
        from huggingface_hub import DatasetCard
        repo = f"{HUB_USER}/nimbus-bitext-v1"
        dd.push_to_hub(repo, private=True)
        DatasetCard(CARD.read_text()).push_to_hub(repo, repo_type="dataset")
        q = Dataset.from_pandas(pd.read_parquet(QUESTIONS), preserve_index=False)
        q.push_to_hub(f"{HUB_USER}/nimbus-bitext-questions", private=True)
        DatasetCard(QUESTIONS_CARD).push_to_hub(f"{HUB_USER}/nimbus-bitext-questions", repo_type="dataset")
        print(f"pushed {repo} and {HUB_USER}/nimbus-bitext-questions (private)")


if __name__ == "__main__":
    main()
