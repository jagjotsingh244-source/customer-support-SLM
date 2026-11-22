"""Read the 5-rows-per-intent Bitext sample with Gemini and write one note per intent.

Same sample as data_prep/bitext_eda.ipynb (seed 3407). For each intent, Gemini sees Nova's rules, the intent's
triage decision from data/DECISIONS.md, and the five customer messages with their original replies, and answers:
what would a good Nova reply do differently? The notes go into the "Reading notes" table in data/DECISIONS.md,
and the full answers (with the patterns Gemini cites) into data/eda/reading_notes.json.

    set -a; source .env; set +a          # VERTEX_API_KEY, VERTEX_PROJECT
    uv run --group data python data_prep/reading_notes.py

The notes are a first pass, not the final word: read them against data/eda/reading_sample.md.
"""

import json
import os
import re
import time
from pathlib import Path

from datasets import load_dataset
from google import genai
from google.genai import errors, types

REPO = Path(__file__).resolve().parent.parent
DECISIONS = REPO / "data" / "DECISIONS.md"
OUT = REPO / "data" / "eda" / "reading_notes.json"
MODEL = "gemini-4-hydrogen"
SEED = 3407

PROMPT = """You are reviewing training data for Nova, the customer-support assistant of NimbusCart, an Indian online store.
Nova's tone fine-tune learns only the *form* of these replies, never their content. Nova's rules:
- 25 to 70 words, warm and plain, no exclamation marks, no lists or headers.
- No procedures, menu paths, URLs, timelines or numbers from memory: facts come from NimbusCart's help center and
  order tools at answer time. The {{{{...}}}} placeholders are a made-up company's details and must not survive.
- Respond to what the customer actually said, including frustration, rudeness or typos.
- End with exactly one next step Nova can really take: check their order, look up the policy, ask one clarifying
  question, or connect a teammate.

Triage decision for the intent "{intent}": {decision}
(Keep = Nova handles it with tools or the help center. Redirect = outside Nova's tools; a short honest pointer to the
website or a teammate. Drop = not used for training.)

Below are 5 random customer messages from this intent, each with the dataset's original reply.
Read all five, then answer in JSON with these keys:
- "note": ONE line, at most 30 words: what a good Nova reply to this intent would do differently from these replies.
  Be specific to this intent, not generic advice that fits every intent.
- "patterns": 2 to 4 short observations about these replies or messages, each tied to what you saw (quote a few
  words where useful).
- "meaning_risk": one short sentence on anything a rewrite could get wrong for this intent (e.g. the customer asks
  something the reply ignores), or "" if none.

{rows}"""


def triage() -> dict[str, str]:
    """Intent -> Keep/Redirect/Drop, read from the triage table in DECISIONS.md."""
    rows = re.findall(r"^\| (\w+) \| [A-Z]+ \| (Keep|Redirect|Drop) \|", DECISIONS.read_text(), re.M)
    return dict(rows)


def ask(client, prompt: str) -> dict:
    for wait in (10, 20, 40, 60, None):
        try:
            r = client.models.generate_content(
                model=MODEL, contents=prompt,
                config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=8192,
                                                   response_mime_type="application/json"))
            return json.loads(r.text)
        except errors.APIError as e:
            if wait is None or e.code not in (429, 500, 503):
                raise
            time.sleep(wait)


def write_table(notes: dict[str, dict]) -> None:
    text = DECISIONS.read_text()
    for intent, n in notes.items():
        line = n["note"].replace("|", "/").replace("\n", " ").strip()
        # Only the reading-notes table has two columns; match that row shape.
        text, k = re.subn(rf"^\| {intent} \| [^|]*\|$", f"| {intent} | {line} |", text, flags=re.M)
        assert k == 1, f"{intent}: expected one row in the reading-notes table, found {k}"
    DECISIONS.write_text(text)


def main():
    decisions = triage()
    assert len(decisions) == 27, f"triage table has {len(decisions)} intents, expected 27"
    df = load_dataset("bitext/Bitext-customer-support-llm-chatbot-training-dataset", split="train").to_pandas()
    sample = df.groupby("intent").sample(5, random_state=SEED).sort_values(["category", "intent"])

    client = genai.Client(vertexai=True, api_key=os.environ["VERTEX_API_KEY"],
                          project=os.environ["VERTEX_PROJECT"], location=os.environ.get("VERTEX_LOCATION", "global"))
    notes = json.loads(OUT.read_text()) if OUT.exists() else {}
    for intent, g in sample.groupby("intent", sort=False):
        if intent in notes:
            continue
        rows = "\n\n".join(f"[{i}] Customer ({r['flags']}): {r['instruction']}\nOriginal reply: {r['response']}"
                           for i, (_, r) in enumerate(g.iterrows(), 1))
        notes[intent] = ask(client, PROMPT.format(intent=intent, decision=decisions[intent], rows=rows))
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(notes, indent=2, ensure_ascii=False))   # saved after each intent: safe to rerun
        print(f"{intent:26s} {notes[intent]['note']}")
    write_table(notes)
    print(f"\n{len(notes)} notes written to {DECISIONS.relative_to(REPO)}; details in {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
