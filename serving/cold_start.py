"""Cold starts of the scale-to-zero model endpoint, measured through the deployed backend.

    BACKEND_TOKEN=$(gcloud auth print-identity-token) uv run --group teacher python serving/cold_start.py \\
        --backend https://<backend> --runs 3 --out serving/deploy/cold_starts.json

Each run waits until Modal reports no running container for the model app (the GPU has scaled to zero), then
calls the backend's /warmup, which polls the model endpoint until it answers, and then sends one real chat turn.
Recorded: the warm-up wait (container start + model load + vLLM start), and the first chat turn after it.
BACKEND_TOKEN is the identity token the private Cloud Run service needs; leave it unset for a public backend.
"""

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

import httpx

APP = "nova-serve"


def running_containers() -> int:
    out = subprocess.run(["modal", "app", "list", "--json"], capture_output=True, text=True, check=True).stdout
    return sum(int(a["tasks"]) for a in json.loads(out) if a["description"] == APP and a["state"] == "deployed")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", required=True)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--customer", type=int, default=1)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    headers = {"Authorization": f"Bearer {os.environ['BACKEND_TOKEN']}"} if os.environ.get("BACKEND_TOKEN") else {}
    results = []
    for i in range(1, a.runs + 1):
        t0 = time.time()
        while running_containers():
            time.sleep(10)
        asleep_after = round(time.time() - t0)
        with httpx.Client(base_url=a.backend, headers=headers, timeout=900) as c:
            t1 = time.perf_counter()
            w = c.post("/warmup").json()
            warm_s = time.perf_counter() - t1
            c.post("/demo-login", json={"customer_id": a.customer}).raise_for_status()
            t2 = time.perf_counter()
            r = c.post("/chat", json={"message": "where is my latest order?"}).json()
            chat_s = time.perf_counter() - t2
        res = {"run": i, "waited_for_scale_to_zero_s": asleep_after, "warmup_s": round(warm_s, 1),
               "warmup_reported_s": w.get("waited_s"), "first_chat_s": round(chat_s, 2),
               "first_chat_server_s": r.get("turn_s"), "first_chat_model_calls": r.get("model_calls")}
        print(res, flush=True)
        results.append(res)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(results, indent=1) + "\n")


if __name__ == "__main__":
    main()
