"""Turn Bitext into Nova-voiced reply data, following data/DECISIONS.md.

Steps, in order:
1. Dedup the full dataset (26,872 rows) on the normalised customer message or its first 12 normalised words.
2. Triage: keep or redirect intents by the table in data/DECISIONS.md; drop the rest.
3. Customer placeholders: drop messages that use {{Account Type}} or {{Account Category}} (no NimbusCart
   equivalent); fill the others with seeded fake values in NimbusCart's formats. Reply placeholders are never filled.
4. Sample: at most 300 rows per kept intent and 100 per redirect intent (seed 3407), rows with a rare phrasing
   flag (keyword, negation, offensive, politeness) at double weight so they are not thinned out.
5. Rewrite each sampled reply with a larger model into Nova's voice, content-free (--rewrite).
6. Check every rewrite automatically; drop failures and report the drop rate per intent and per flag.

Every row keeps its Bitext row number, intent, category, flags and the original message and reply.

Also saves every original customer message (all 26,872 rows, untouched, with flags, category and intent) to
data/processed/bitext_questions.parquet: the opening lines for tool-using conversations later.

    uv run --group data python data_prep/prepare_bitext.py                          # steps 1-4 only, no model calls
    set -a; source .env; set +a
    uv run --group data python data_prep/prepare_bitext.py --rewrite --limit 2      # 2 rows per intent: a smoke test
    uv run --group data python data_prep/prepare_bitext.py --rewrite                # everything

Rewrites are cached in data/processed/bitext_rewrites.jsonl by row number, so a rerun only asks for rows it has
not seen (change --model or delete the file to redo them). Requests run in parallel (--workers), never one by one.
"""

import argparse
import json
import os
import random
import re
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
from datasets import load_dataset
from faker import Faker

REPO = Path(__file__).resolve().parent.parent
DECISIONS = REPO / "data" / "DECISIONS.md"
OUT = REPO / "data" / "processed"
SAMPLE = OUT / "bitext_sample.jsonl"
CACHE = OUT / "bitext_rewrites.jsonl"
FINAL = OUT / "bitext_rewritten.jsonl"
QUESTIONS = OUT / "bitext_questions.parquet"
REPORT = REPO / "data_prep" / "reports" / "bitext_rewrite_report.md"

SEED = 3407
PER_INTENT = {"Keep": 300, "Redirect": 100}
NO_EQUIVALENT = ("{{Account Type}}", "{{Account Category}}")
OTHER_COUNTRIES = ["Nepal", "Bangladesh", "Sri Lanka", "the UAE", "Singapore", "the UK", "the USA", "Canada",
                   "Australia", "Germany"]
MIN_WORDS, MAX_WORDS = 25, 70
RARE_FLAGS = set("KNWP")      # keyword, negation, offensive, politeness: sampled at double weight (decision 5)


# ---------- steps 1-4: no model calls ----------

def normalise(s: pd.Series) -> pd.Series:
    return (s.str.lower().str.replace(r"[^a-z0-9 ]", "", regex=True)
            .str.replace(r"\s+", " ", regex=True).str.strip())


def triage() -> dict[str, str]:
    """Intent -> Keep / Redirect / Drop, from the triage table in DECISIONS.md."""
    rows = dict(re.findall(r"^\| (\w+) \| [A-Z]+ \| (Keep|Redirect|Drop) \|", DECISIONS.read_text(), re.M))
    assert len(rows) == 27, f"triage table has {len(rows)} intents, expected 27"
    return rows


def fill_customer(text: str, row_id: int) -> str:
    """Fill a customer message's placeholders with fake values, the same ones every run (seeded by row)."""
    rng = random.Random(f"{SEED}-{row_id}")
    fake = Faker("en_IN")
    fake.seed_instance(f"{SEED}-{row_id}")
    amount = rng.choice([199, 349, 499, 799, 1299, 1499, 2199, 2499, 3999, 5499, 8999, 12499])
    amount_text = f"{amount:,}"

    text = re.sub(r"\{\{Refund Amount\}\}\s*(dollars?|doolars?|USD)", f"{amount_text} rupees", text, flags=re.I)
    text = text.replace("{{Currency Symbol}}{{Refund Amount}}", f"₹{amount_text}")
    text = text.replace("{{Refund Amount}}", f"₹{amount_text}")
    text = text.replace("{{Currency Symbol}}", "₹")
    text = text.replace("{{Order Number}}", str(rng.randint(10001, 13999)))
    text = re.sub(r"(?<=\S)\{\{Invoice Number\}\}", " {{Invoice Number}}", text)      # "invoice{{...}}" in Bitext
    text = text.replace("{{Invoice Number}}", f"INV-{rng.randint(100000, 999999)}")
    text = text.replace("{{Person Name}}", fake.name())
    text = text.replace("{{Delivery City}}", fake.city())
    text = text.replace("{{Delivery Country}}", "India" if rng.random() < 0.4 else rng.choice(OTHER_COUNTRIES))
    assert "{{" not in text, f"row {row_id}: unfilled placeholder in {text!r}"
    return text


def build_sample() -> pd.DataFrame:
    df = load_dataset("bitext/Bitext-customer-support-llm-chatbot-training-dataset", split="train").to_pandas()
    df.insert(0, "row_id", range(len(df)))
    n_raw = len(df)
    df[["row_id", "flags", "instruction", "category", "intent"]].to_parquet(QUESTIONS, index=False)

    norm = normalise(df.instruction)
    first12 = norm.str.split().str[:12].str.join(" ")
    df = df[~(norm.duplicated() | first12.duplicated())]
    n_dedup = len(df)

    decisions = triage()
    df = df.assign(triage=df.intent.map(decisions))
    df = df[df.triage.isin(PER_INTENT)]
    df = df[~df.instruction.str.contains("|".join(map(re.escape, NO_EQUIVALENT)), regex=True)]

    # Weighted sampling without replacement (Efraimidis-Spirakis): key = u ** (1 / weight), keep the top n keys.
    weight = df["flags"].map(lambda f: 2.0 if RARE_FLAGS & set(f) else 1.0)
    df = df.assign(key=np.random.default_rng(SEED).random(len(df)) ** (1 / weight))
    df = (df.sort_values("key", ascending=False)
            .groupby("intent", group_keys=False)[list(df.columns)]
            .apply(lambda g: g.head(PER_INTENT[g.triage.iloc[0]]))
            .drop(columns="key"))
    df = df.rename(columns={"instruction": "instruction_original", "response": "response_original"})
    df["instruction"] = [fill_customer(t, i) for t, i in zip(df.instruction_original, df.row_id)]
    df = df.sort_values(["triage", "intent", "row_id"]).reset_index(drop=True)
    print(f"{n_raw} rows -> {n_dedup} after dedup -> {len(df)} sampled "
          f"({df.intent.nunique()} intents: {(df.triage == 'Keep').sum()} keep, {(df.triage == 'Redirect').sum()} redirect)")
    return df


# ---------- step 5: rewrite ----------

RULES = """Rules:
- 25 to 70 words. Warm, plain, no exclamation marks, no lists, no headers.
- Remove every procedure, menu path, URL, timeline, number and {{{{placeholder}}}}.
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
- Name a feeling (frustration, worry) only if the customer's message shows it."""

PROMPT_VERSION = "v5"     # bump when RULES or PROMPTS change: cached rewrites from another version are redone
# v4 and v5 only add bans on habits found in the full v3 run, so an older rewrite without those habits is still
# valid and is kept; only rows that have one are redone. In the v3 run, 31% of replies said "I'd be glad",
# 21% of calm customers were told their situation was "frustrating", and 21% said "I don't have ... in front of me"
# before offering to check the order.
STOCK_PHRASES = re.compile(r"I'd be (?:glad|happy)", re.I)
FEELING = re.compile(r"frustrat|upset|annoy|worr(?:y|ied|ying)|stress", re.I)
CANT_SEE = re.compile(r"in front of me|can't see|cannot see|not able to see|don't have (?:your|the|those)|"
                      r"haven't (?:seen|pulled up|looked at)", re.I)
UPSET_MESSAGE = re.compile(r"damn|bloody|fuck|hell\b|shit|crap|stupid|ridiculous|angry|annoy|upset|frustrat|"
                           r"worr|\?\?|!!|can't|cannot|unable|not working|problem|issue|error|wrong|lost", re.I)


def has_old_habit(row, text: str) -> bool:
    """Whether a rewrite shows a habit that prompt v4/v5 bans, given the customer's message."""
    return bool(STOCK_PHRASES.search(text)
                or (FEELING.search(text) and not ("W" in row["flags"] or UPSET_MESSAGE.search(row["instruction"])))
                or (row["triage"] == "Keep" and CANT_SEE.search(text)))


STILL_VALID_FROM = ("v3", "v4")
PROMPTS = {
    "Keep": """Rewrite this customer-support reply for Nova, NimbusCart's assistant.
{rules}
- Do not say what you cannot see or do not have in front of you; go straight to the next step.
- End with exactly one next step Nova can take: offer to check their order, offer to look up the policy,
  ask one clarifying question, or offer a teammate. Prefer checking the order or looking up the policy when
  either could answer the message; offer a teammate when the customer asks for a person or nothing else fits.

Customer: {instruction}
Original reply: {response}

Answer with the rewritten reply only.""",
    "Redirect": """Rewrite this customer-support reply for Nova, NimbusCart's assistant.
Nova cannot do what this customer asks: it has no tools for accounts, invoices or placing orders.
{rules}
- Say briefly and honestly that this is not something Nova can do here, without describing how to do it.
- End with exactly one next step: point them to the NimbusCart website or app (name no menu or page),
  or offer to connect a teammate.

Customer: {instruction}
Original reply: {response}

Answer with the rewritten reply only.""",
}


def prompt_for(row) -> str:
    return PROMPTS[row["triage"]].format(rules=RULES.format(), instruction=row["instruction"],
                                         response=row["response_original"])


class Rewriter:
    def __init__(self, model: str, thinking: str):
        from google import genai
        from google.genai import types
        self.model, self.types, self.thinking = model, types, thinking
        self.client = genai.Client(vertexai=True, api_key=os.environ["VERTEX_API_KEY"],
                                   project=os.environ["VERTEX_PROJECT"],
                                   location=os.environ.get("VERTEX_LOCATION", "global"))

    def __call__(self, prompt: str) -> dict:
        from google.genai import errors
        for wait in (10, 20, 40, 60, 60, None):
            try:
                r = self.client.models.generate_content(
                    model=self.model, contents=prompt,
                    config=self.types.GenerateContentConfig(
                        temperature=0.7, max_output_tokens=8192,
                        thinking_config=self.types.ThinkingConfig(thinking_level=self.thinking)))
                u = r.usage_metadata
                return {"rewritten": (r.text or "").strip(), "setup": setup(self.model, self.thinking),
                        "model": self.model,
                        "tokens_in": u.prompt_token_count, "tokens_out": u.candidates_token_count,
                        "tokens_thinking": u.thoughts_token_count or 0}
            except errors.APIError as e:
                if wait is None or e.code not in (429, 500, 503):
                    raise
                time.sleep(wait)


def setup(model: str, thinking: str, version: str = PROMPT_VERSION) -> str:
    return f"{model} | prompt {version} | thinking {thinking}"


def rewrite(df: pd.DataFrame, model: str, thinking: str, workers: int) -> pd.DataFrame:
    current, older = {}, {}
    if CACHE.exists():
        for line in CACHE.read_text().splitlines():
            c = json.loads(line)
            if c.get("setup") == setup(model, thinking):
                current[c["row_id"]] = c
            elif c.get("setup") in {setup(model, thinking, v) for v in STILL_VALID_FROM}:
                older[c["row_id"]] = c          # later lines (newer prompts) overwrite earlier ones
    cache = {}
    for _, r in df.iterrows():
        if r.row_id in current:
            cache[r.row_id] = current[r.row_id]
        elif r.row_id in older and not has_old_habit(r, older[r.row_id]["rewritten"]):
            cache[r.row_id] = older[r.row_id]
    todo = [r for _, r in df.iterrows() if r.row_id not in cache]
    print(f"rewrites: {len(df) - len(todo)} cached, {len(todo)} to request ({setup(model, thinking)}, {workers} workers)")
    if todo:
        ask, lock = Rewriter(model, thinking), threading.Lock()
        with ThreadPoolExecutor(workers) as pool, CACHE.open("a") as f:
            futures = {pool.submit(ask, prompt_for(r)): r.row_id for r in todo}
            for k, fut in enumerate(as_completed(futures), 1):
                c = {"row_id": int(futures[fut]), **fut.result()}
                cache[c["row_id"]] = c
                with lock:
                    f.write(json.dumps(c, ensure_ascii=False) + "\n")
                    f.flush()
                if k % 100 == 0 or k == len(todo):
                    print(f"  {k}/{len(todo)}")
    cols = ["rewritten", "setup", "model", "tokens_in", "tokens_out", "tokens_thinking"]
    return df.assign(**{c: [cache[i][c] for i in df.row_id] for c in cols})


# ---------- step 6: automatic checks ----------

OFFER = re.compile(r"\b(I can|I could|I'd|I would|I'll|let me|shall I|would you like|want me to|"
                   r"happy to|glad to|a teammate|our team|the NimbusCart (website|app))\b", re.I)


# Saying the store has several of something ("We offer a few different shipping options") is a claim about
# NimbusCart with no source. Found in the hand review; the meaning judge let about half of these through.
STORE_CLAIM = re.compile(r"\b(?:a few|several|a variety of|plenty of|a range of|lots of|many|a couple of) "
                         r"(?:different )?(?:ways|options|methods|choices|payment|shipping|delivery)|toll-free", re.I)


def failures(text: str) -> list[str]:
    """Names of the checks a rewritten reply fails; empty means it passes."""
    out = []
    words = len(text.split())
    last = re.split(r"(?<=[.?])\s+", text.strip())[-1]
    if "{{" in text or "}}" in text:
        out.append("placeholder")
    if re.search(r"\d", text):
        out.append("digit")
    if re.search(r"https?:|www\.|\.com\b", text, re.I):
        out.append("url")
    if not MIN_WORDS <= words <= MAX_WORDS:
        out.append("length")
    if "!" in text:
        out.append("exclamation")
    if re.search(r"^\s*([-*•]|\d+[.)])\s", text, re.M) or "**" in text or re.search(r"^#", text, re.M):
        out.append("list_or_markup")
    if not (last.endswith("?") or OFFER.search(last)):
        out.append("no_next_step")
    if STORE_CLAIM.search(text):
        out.append("store_claim")
    return out


def check(df: pd.DataFrame) -> pd.DataFrame:
    failed = [failures(r.rewritten) + (["old_habit"] if has_old_habit(r, r.rewritten) else [])
              for _, r in df.iterrows()]
    df = df.assign(failed=failed)
    return df.assign(passed=df.failed.map(len) == 0)


def report(df: pd.DataFrame, n_sampled: int) -> str:
    by_intent = (df.groupby(["triage", "intent"])
                   .agg(rows=("passed", "size"), passed=("passed", "sum"))
                   .assign(drop_rate=lambda t: (1 - t.passed / t.rows).round(3)).reset_index())
    reasons = Counter(r for f in df.failed for r in f)
    flags_all = Counter(c for f in df["flags"] for c in set(f))
    flags_ok = Counter(c for f in df[df.passed]["flags"] for c in set(f))
    words = df[df.passed].rewritten.str.split().map(len)
    openers = df[df.passed].rewritten.str.split().str[:3].str.join(" ").value_counts()
    setups = "; ".join(f"`{k}` {v}" for k, v in df.setup.value_counts().items())
    lines = [
        "# Bitext rewrite report", "",
        f"Setups: {setups}. {len(df)} rows rewritten of {n_sampled} sampled; "
        f"{int(df.passed.sum())} pass every check ({df.passed.mean():.1%}).", "",
        "Checks: no `{{`, no digits, no URLs, 25 to 70 words, no exclamation marks, no lists or markup, and the last "
        "sentence is a question or an offer; no claim that the store has several of something (`store_claim`); and none of the habits banned in prompts v4 and v5 (`old_habit`: "
        "\"I'd be glad/happy\", naming a feeling the customer did not show, \"I can't see ...\").", "",
        "## Drop rate per intent", "", "| Triage | Intent | Rows | Pass | Drop rate |", "|---|---|---|---|---|",
        *[f"| {r.triage} | {r.intent} | {r.rows} | {r.passed} | {r.drop_rate:.1%} |" for r in by_intent.itertuples()],
        "", "## Why rows failed (a row can fail several checks)", "", "| Check | Rows |", "|---|---|",
        *[f"| {k} | {v} |" for k, v in reasons.most_common()],
        "", "## Flags before and after the checks", "", "| Flag | Rewritten | Passed | Kept |", "|---|---|---|---|",
        *[f"| {k} | {v} | {flags_ok[k]} | {flags_ok[k] / v:.0%} |" for k, v in flags_all.most_common()],
        "", "## Passing replies", "",
        f"Words: median {words.median():.0f}, min {words.min()}, max {words.max()}.  ",
        f"Most common opening (first three words): \"{openers.index[0]}\", {openers.iloc[0]} replies "
        f"({openers.iloc[0] / len(words):.1%}).  ",
        f"Replies containing \"I'd be glad\" or \"I'd be happy\": "
        f"{df[df.passed].rewritten.str.contains(STOCK_PHRASES).mean():.1%}.  ",
        f"Tokens per request (mean): {df.tokens_in.mean():.0f} in, {df.tokens_out.mean():.0f} out, "
        f"{df.tokens_thinking.mean():.0f} thinking.", "",
    ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rewrite", action="store_true", help="call the model (steps 5-6)")
    ap.add_argument("--limit", type=int, help="only the first N sampled rows per intent (smoke test)")
    ap.add_argument("--model", default="gemini-4-hydrogen")
    ap.add_argument("--thinking", default="low", help="Gemini thinking level (low or high)")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    df = build_sample()
    print(f"saved all original customer messages to {QUESTIONS.relative_to(REPO)}")
    df.to_json(SAMPLE, orient="records", lines=True, force_ascii=False)
    flags = Counter(c for f in df["flags"] for c in set(f))
    print("flags in the sample:", dict(flags.most_common()))
    if not a.rewrite:
        return

    n_sampled = len(df)
    if a.limit:
        df = df.groupby("intent", group_keys=False)[list(df.columns)].apply(lambda g: g.head(a.limit))
    df = check(rewrite(df, a.model, a.thinking, a.workers))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report(df, n_sampled))
    keep = ["row_id", "triage", "category", "intent", "flags", "instruction", "instruction_original",
            "response_original", "rewritten", "setup"]
    df[df.passed][keep].to_json(FINAL, orient="records", lines=True, force_ascii=False)
    print(f"{int(df.passed.sum())}/{len(df)} pass; report in {REPORT.relative_to(REPO)}, rows in {FINAL.relative_to(REPO)}")


if __name__ == "__main__":
    main()
