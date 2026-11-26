"""Load test for the deployed backend: simulated customers chatting with golden-set messages.

    uv run --with locust locust -f serving/locustfile.py --host https://<backend> --headless \\
        -u 10 -r 2 -t 5m --csv serving/load/u10 --only-summary
    # a private Cloud Run backend: BACKEND_TOKEN=$(gcloud auth print-identity-token)

Each simulated customer signs in as an eval-partition demo account, has a conversation of TURNS messages
(a golden case's opening message, then follow-ups from other cases, so prompt lengths are realistic), waits
2-6 s between messages like a person reading the reply, then starts a new conversation.

Besides locust's own timings (seen from this machine, so they include the network to the backend), every
reply's own server-side turn time (model calls + tools + database, from the response body) is recorded as a
separate entry, "turn (server)", and the model's share as "model (server)".
"""

import glob
import json
import os
import random
import sys
from pathlib import Path

from locust import HttpUser, between, events, task

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import partition_for  # noqa: E402

TURNS = int(os.environ.get("TURNS", "3"))
ROOT = Path(__file__).resolve().parent.parent
CASES = [json.loads(line) for f in sorted(glob.glob(str(ROOT / "evals/golden/*.jsonl"))) for line in open(f)]
OPENERS = [c["turns"][0] for c in CASES]
DEMO_CUSTOMERS = sorted({c["customer_id"] for c in CASES if partition_for(c["customer_id"]) == "eval"})


def server_entry(name: str, ms: float, length: int) -> None:
    events.request.fire(request_type="SERVER", name=name, response_time=ms, response_length=length,
                        exception=None, context={})


class Customer(HttpUser):
    wait_time = between(2, 6)

    def on_start(self):
        self.left = 0
        if os.environ.get("BACKEND_TOKEN"):              # a private Cloud Run service: an identity token
            self.client.headers["Authorization"] = f"Bearer {os.environ['BACKEND_TOKEN']}"

    @task
    def chat(self):
        if self.left == 0:                                  # a new conversation, a new session
            self.client.cookies.clear()
            r = self.client.post("/demo-login", json={"customer_id": random.choice(DEMO_CUSTOMERS)},
                                 name="/demo-login")
            if r.status_code != 200:
                return
            self.left = TURNS
        message = random.choice(OPENERS)
        with self.client.post("/chat", json={"message": message}, name="/chat", catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"HTTP {r.status_code}")
                self.left = 0
                return
            body = r.json()
            if not (body.get("reply") or "").strip():
                r.failure("empty reply")
            server_entry("turn (server)", body["turn_s"] * 1000, len(body.get("reply") or ""))
            server_entry("model (server)", body["model_s"] * 1000, body["model_calls"])
        self.left -= 1
