"""Serve a Vertex AI endpoint running vLLM as a plain OpenAI-compatible server on localhost, for the generator.

The teacher can run on a Vertex AI endpoint (serving/vertex_teacher.json: the same vLLM 0.34.0 image, model and
flags as serving/modal_teacher.py). Vertex wants a short-lived Google access token on every request and exposes
one route, rawPredict, which it forwards to vLLM's /v1/chat/completions. The generator and the judges speak plain
OpenAI to TEACHER_URL, so this relay sits in between on a Compute Engine VM: it answers /health and /v1/models
itself, forwards chat completions to rawPredict, and takes a fresh token from the VM's metadata server before
the old one runs out. Standard library only.

    python serving/vertex_teacher_proxy.py --endpoint projects/<p>/locations/us-central1/endpoints/<id>
    # then TEACHER_URL=http://localhost:8000
"""

import argparse
import json
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

METADATA_TOKEN = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"


class Token:
    """The VM service account's access token, refreshed five minutes before it expires."""

    def __init__(self):
        self.lock, self.value, self.expires = threading.Lock(), "", 0.0

    def get(self) -> str:
        with self.lock:
            if time.time() > self.expires - 300:
                req = urllib.request.Request(METADATA_TOKEN, headers={"Metadata-Flavor": "Google"})
                d = json.load(urllib.request.urlopen(req, timeout=10))
                self.value, self.expires = d["access_token"], time.time() + d["expires_in"]
            return self.value


def handler(predict_url: str, model_info: dict, token: Token):
    class Relay(BaseHTTPRequestHandler):
        def _send(self, code: int, body: bytes):
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                self._send(200, b"{}")
            elif self.path == "/v1/models":
                self._send(200, json.dumps({"object": "list", "data": [model_info]}).encode())
            else:
                self._send(404, b'{"error": "not found"}')

        def do_POST(self):
            if self.path != "/v1/chat/completions":
                return self._send(404, b'{"error": "only /v1/chat/completions is relayed"}')
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            for attempt in range(3):            # Vertex answers 429/503 briefly while replicas are busy
                req = urllib.request.Request(predict_url, data=body, method="POST", headers={
                    "Authorization": f"Bearer {token.get()}", "Content-Type": "application/json"})
                try:
                    with urllib.request.urlopen(req, timeout=600) as r:
                        return self._send(r.status, r.read())
                except urllib.error.HTTPError as e:
                    if e.code in (429, 503) and attempt < 2:
                        time.sleep(5 * (attempt + 1))
                        continue
                    return self._send(e.code, e.read())
                except Exception as e:          # timeouts and resets: report, the generator retries or logs
                    return self._send(502, json.dumps({"error": f"{type(e).__name__}: {e}"}).encode())

        def log_message(self, *args):          # one line per request is noise at 20 conversations at once
            pass

    return Relay


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", required=True, help="projects/<p>/locations/<region>/endpoints/<id>")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--served-name", default="teacher")
    ap.add_argument("--model", default="Qwen/Qwen3.5-27B", help="recorded in every conversation as the teacher")
    a = ap.parse_args()
    region = a.endpoint.split("/locations/")[1].split("/")[0]
    url = f"https://{region}-aiplatform.googleapis.com/v1/{a.endpoint}:rawPredict"
    info = {"id": a.served_name, "object": "model", "root": a.model, "owned_by": "vertex"}
    server = ThreadingHTTPServer(("127.0.0.1", a.port), handler(url, info, Token()))
    print(f"relaying http://127.0.0.1:{a.port}/v1/chat/completions -> {url}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
