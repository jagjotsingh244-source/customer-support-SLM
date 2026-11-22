"""Second check on the rewritten Bitext replies: did a rewrite change what the customer meant?

The automatic checks in prepare_bitext.py catch form (length, digits, lists...). They cannot tell whether a reply
still answers the customer's actual message, or whether it slipped in a fact or a promise. Here a model judges
every pair that passed those checks, and a hand review reads 200 of them.

1. Judge (--judge): for each row in data/processed/bitext_rewritten.jsonl, Gemini answers three yes/no questions
   in JSON. Cached in data/processed/bitext_judgements.jsonl, so reruns only ask for new rows.
2. Hand review sheet: 8 rows per intent (200 in all, seed 3407) plus every row the judge rejected, written to
   data/eda/hand_review.md for reading side by side with the originals.
3. Hand rejections: row numbers rejected by hand, with a reason, live in data_prep/hand_rejections.json.
4. Final rows = passed the checks, accepted by the judge, not rejected by hand ->
   data/processed/bitext_final.jsonl. A section with the counts is added to the rewrite report.

    set -a; source .env; set +a
    uv run --group data python data_prep/review_rewrites.py --judge
"""

import argparse
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
ROWS = REPO / "data" / "processed" / "bitext_rewritten.jsonl"
CACHE = REPO / "data" / "processed" / "bitext_judgements.jsonl"
FINAL = REPO / "data" / "processed" / "bitext_final.jsonl"
SHEET = REPO / "data" / "eda" / "hand_review.md"
HAND = REPO / "data_prep" / "hand_rejections.json"
REPORT = REPO / "data_prep" / "reports" / "bitext_rewrite_report.md"
SEED, PER_INTENT = 3407, 8
JUDGE_VERSION = "j2"

PROMPT = """You check training data for Nova, the support assistant of NimbusCart, an online store in India.
Each example is a customer message and a rewritten reply. The reply is meant to carry no facts at all: Nova looks
facts up later with its tools and help center. Triage for this intent: {triage}
(Keep = Nova can help with its order tools or help center. Redirect = Nova cannot do this; it should say so
honestly and point to the NimbusCart website or app, or offer a teammate.)

Customer: {instruction}
Reply: {rewritten}

Answer in JSON with these keys:
- "same_request": true if the reply responds to what this customer actually asked or said (the same request,
  the same item: an invoice is not an order, a refund is not a cancellation), false otherwise.
- "no_invented_content": true if the reply states no fact, rule, timeline, procedure, menu, price or promise
  about NimbusCart and says nothing has been done; false if it does.
- "fitting_next_step": true if the reply ends with exactly one next step that fits the triage (Keep: check the
  order, look up the policy, ask one question, or a teammate; Redirect: the website or app, or a teammate).
  False if there is no next step, if it does not fit the triage, or if the customer is offered a choice of
  several next steps ("the NimbusCart website or app" counts as one).
- "reason": one short sentence explaining any false, or "" if all are true."""


def judge_all(rows: pd.DataFrame, model: str, workers: int) -> dict[int, dict]:
    from google import genai
    from google.genai import errors, types
    client = genai.Client(vertexai=True, api_key=os.environ["VERTEX_API_KEY"], project=os.environ["VERTEX_PROJECT"],
                          location=os.environ.get("VERTEX_LOCATION", "global"))
    setup = f"{model} | judge {JUDGE_VERSION}"
    cache = {}
    if CACHE.exists():
        for line in CACHE.read_text().splitlines():
            c = json.loads(line)
            if c["setup"] == setup:
                cache[c["row_id"]] = c
    text = dict(zip(rows.row_id, rows.rewritten))
    # A judgement is only reused for the exact text it judged (older records did not store it).
    cache = {i: c for i, c in cache.items() if c.get("rewritten", text.get(i)) == text.get(i)}

    def ask(r) -> dict:
        prompt = PROMPT.format(triage=r.triage, instruction=r.instruction, rewritten=r.rewritten)
        for wait in (10, 20, 40, 60, 60, None):
            try:
                out = client.models.generate_content(
                    model=model, contents=prompt,
                    config=types.GenerateContentConfig(temperature=0, max_output_tokens=8192,
                                                       response_mime_type="application/json",
                                                       thinking_config=types.ThinkingConfig(thinking_level="low")))
                return {"row_id": int(r.row_id), "setup": setup, "rewritten": r.rewritten, **json.loads(out.text)}
            except errors.APIError as e:
                if wait is None or e.code not in (429, 500, 503):
                    raise
                time.sleep(wait)

    todo = [r for r in rows.itertuples() if r.row_id not in cache]
    print(f"judgements: {len(rows) - len(todo)} cached, {len(todo)} to request ({setup}, {workers} workers)")
    lock = threading.Lock()
    with ThreadPoolExecutor(workers) as pool, CACHE.open("a") as f:
        for k, fut in enumerate(as_completed([pool.submit(ask, r) for r in todo]), 1):
            c = fut.result()
            cache[c["row_id"]] = c
            with lock:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
                f.flush()
            if k % 500 == 0 or k == len(todo):
                print(f"  {k}/{len(todo)}")
    return cache


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", action="store_true", help="ask the model for judgements not yet cached")
    ap.add_argument("--model", default="gemini-4-hydrogen")
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()

    rows = pd.read_json(ROWS, lines=True)
    if a.judge:
        judge_all(rows, a.model, a.workers)
    cache = {json.loads(l)["row_id"]: json.loads(l) for l in CACHE.read_text().splitlines()} if CACHE.exists() else {}
    missing = set(rows.row_id) - set(cache)
    assert not missing, f"{len(missing)} rows have no judgement; run with --judge"

    keys = ["same_request", "no_invented_content", "fitting_next_step"]
    j = pd.DataFrame([cache[i] for i in rows.row_id])
    rows = rows.assign(**{k: j[k].astype(bool).values for k in keys}, judge_reason=j["reason"].values)
    rows["judge_ok"] = rows[keys].all(axis=1)

    hand = json.loads(HAND.read_text()) if HAND.exists() else {"rejected": {}}
    rows["hand_rejected"] = rows.row_id.astype(str).isin(hand["rejected"])

    if hand.get("reviewed"):        # the rows actually read, even if later checks dropped some of them
        sample = rows[rows.row_id.isin(hand["reviewed"])]
    else:
        sample = rows.groupby("intent", group_keys=False)[list(rows.columns)].apply(
            lambda g: g.sample(min(len(g), PER_INTENT), random_state=SEED))
    flagged = rows[~rows.judge_ok]
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    out = ["# Hand review: rewritten replies next to the originals", "",
           f"{len(sample)} sampled rows ({PER_INTENT} per intent, seed {SEED}), then the {len(flagged)} rows the "
           "judge rejected. Reject a row by adding its number and a reason to data_prep/hand_rejections.json.", ""]
    for title, part in [("Sample", sample), ("Rejected by the judge", flagged)]:
        out += [f"## {title}", ""]
        for r in part.itertuples():
            verdict = "" if r.judge_ok else f"  \n**Judge:** {r.judge_reason}"
            out += [f"### row {r.row_id} · {r.intent} · {r.triage} · flags {r.flags}", "",
                    f"**Customer:** {r.instruction}", "", f"**Original:** {r.response_original}", "",
                    f"**Rewritten:** {r.rewritten}{verdict}", "", "---", ""]
    SHEET.write_text("\n".join(out))

    final = rows[rows.judge_ok & ~rows.hand_rejected]
    final.drop(columns=keys + ["judge_reason", "judge_ok", "hand_rejected"]).to_json(
        FINAL, orient="records", lines=True, force_ascii=False)

    by_intent = rows.groupby(["triage", "intent"]).agg(
        rewritten=("judge_ok", "size"), judge_ok=("judge_ok", "sum"), hand_rejected=("hand_rejected", "sum"))
    by_intent["final"] = final.groupby(["triage", "intent"]).size()
    by_intent = by_intent.fillna(0).astype(int).reset_index()
    section = [
        "## Meaning check (judge and hand review)", "",
        f"Judge `{a.model} | judge {JUDGE_VERSION}` on the {len(rows)} rows that passed the automatic checks: "
        f"{int(rows.judge_ok.sum())} accepted ({rows.judge_ok.mean():.1%}). "
        + ", ".join(f"{k}: {int((~rows[k]).sum())} false" for k in keys) + ".  ",
        f"Hand review: {len(hand.get('reviewed', sample))} pairs read ({PER_INTENT} per intent), "
        f"{len(hand['rejected'])} rejected ({int(rows.hand_rejected.sum())} still present after the automatic checks, "
        f"{int((rows.hand_rejected & rows.judge_ok).sum())} of them accepted by the judge).  ",
        f"**Final: {len(final)} rows** in data/processed/bitext_final.jsonl.", "",
        "| Triage | Intent | After checks | Judge accepted | Rejected by hand | Final |", "|---|---|---|---|---|---|",
        *[f"| {r.triage} | {r.intent} | {r.rewritten} | {r.judge_ok} | {r.hand_rejected} | {r.final} |"
          for r in by_intent.itertuples()], "",
    ]
    text = REPORT.read_text().split("## Meaning check")[0].rstrip() + "\n\n"
    REPORT.write_text(text + "\n".join(section))
    print(f"judge accepted {int(rows.judge_ok.sum())}/{len(rows)}; final {len(final)} rows; sheet {SHEET.relative_to(REPO)}")


if __name__ == "__main__":
    main()
