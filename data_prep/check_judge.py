"""Prove the meaning judge catches bad rewrites before trusting it with 5,500 of them.

data_prep/judge_planted.jsonl holds 20 hand-written pairs: 8 good ones and 4 planted mistakes of each kind the
judge looks for (answers a different request, invents content, wrong or missing next step). The judge must accept
every good pair and reject every bad one on the right question.

    set -a; source .env; set +a
    uv run --group data python data_prep/check_judge.py
"""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from google import genai
from google.genai import types

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_rewrites import PROMPT  # noqa: E402

PLANTED = Path(__file__).resolve().parent / "judge_planted.jsonl"
KEYS = ("same_request", "no_invented_content", "fitting_next_step")


def main(model: str = "gemini-4-hydrogen"):
    cases = [json.loads(l) for l in PLANTED.read_text().splitlines()]
    client = genai.Client(vertexai=True, api_key=os.environ["VERTEX_API_KEY"], project=os.environ["VERTEX_PROJECT"],
                          location=os.environ.get("VERTEX_LOCATION", "global"))

    def judge(c):
        r = client.models.generate_content(
            model=model, contents=PROMPT.format(triage=c["triage"], instruction=c["instruction"],
                                                rewritten=c["rewritten"]),
            config=types.GenerateContentConfig(temperature=0, response_mime_type="application/json",
                                               thinking_config=types.ThinkingConfig(thinking_level="low")))
        return json.loads(r.text)

    with ThreadPoolExecutor(10) as pool:
        verdicts = list(pool.map(judge, cases))
    wrong = 0
    for c, v in zip(cases, verdicts):
        failed = [k for k in KEYS if not v[k]]
        if c["expect"] == "ok":
            right = not failed
        else:
            right = c["expect"] in failed
        wrong += not right
        mark = "ok  " if right else "MISS"
        print(f"{mark} {c['id']:16s} expected {c['expect']:20s} judge failed {failed or '-'}  {v['reason']}")
    print(f"\n{len(cases) - wrong}/{len(cases)} judged as expected")
    sys.exit(1 if wrong else 0)


if __name__ == "__main__":
    main()
