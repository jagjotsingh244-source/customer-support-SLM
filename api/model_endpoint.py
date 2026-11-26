"""One of the backend's two ways out: the model server. The other is the tracer (api/tracing.py); both have fixed
destinations. Kept apart from api/app.py and the tools, which reach only Postgres (tests/test_guardrails.py
checks they import no network library), so the code that touches customer data cannot send it anywhere but these.

    MODEL_BASE_URL  the model server's OpenAI-compatible URL, e.g. https://.../v1
    NOVA_KEY        its API key
"""

import os
import urllib.error
import urllib.request
from functools import cache

MODEL_BASE_URL = os.environ.get("MODEL_BASE_URL", "http://localhost:8000/v1")


@cache
def client():
    from openai import OpenAI
    return OpenAI(base_url=MODEL_BASE_URL, api_key=os.environ.get("NOVA_KEY", "EMPTY"), timeout=600, max_retries=0)


def ready(timeout: float) -> tuple[bool, str]:
    """Whether the model server answers /models with the key; a scale-to-zero endpoint still starting times out."""
    req = urllib.request.Request(f"{MODEL_BASE_URL}/models",
                                 headers={"Authorization": f"Bearer {os.environ.get('NOVA_KEY', '')}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status == 200, "ready"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, f"not answering yet ({type(e).__name__})"
