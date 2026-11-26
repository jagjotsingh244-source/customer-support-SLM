"""Nova's model as a scale-to-zero GPU endpoint on Modal: serving/launch_vllm.sh inside a container that runs
only while requests arrive. After SCALEDOWN seconds without a request the GPU is released and billing stops;
the next request waits for a cold start (container start, model load, vLLM warm-up). The backend's /warmup
route, or a "Waking Nova up..." button in the UI, hides that wait before a demo.

The weights are uploaded from this machine into a Modal volume, so no Hub token goes to Modal. One 4.4 GB file
failed mid-upload (connection reset), so they go as 1 GB shards (same tensors, bit for bit), one file at a time:

    for f in outputs/nova-sft2a-v1-merged-shards/*; do
        uv run --group teacher modal volume put -f nova-models "$f" "/nova-sft2a-v1-merged/$(basename $f)"; done
    uv run --group teacher modal secret create nova-serve --from-dotenv <file with NOVA_KEY=...>
    uv run --group teacher modal deploy serving/modal_nova.py
    # the endpoint: https://<workspace>--nova-serve-serve.us-east.modal.run/v1  (MODEL_BASE_URL for the backend)

Same vLLM version as every measured run (0.34.0), the shipping format (FP8 from the merged model) and the
API key, all from launch_vllm.sh. The compile caches sit in a volume so later cold starts skip compiling.
"""

import os
import subprocess

import modal

PORT = 8000
# Idle seconds before the GPU is released. 15 minutes: a visitor waits for one cold start (about 2 minutes) on their
# first message and never again in the same visit; the idle tail costs about $0.22 per visit (L4 at ~$0.89/h).
SCALEDOWN = int(os.environ.get("NOVA_SCALEDOWN", "900"))
# One deployed app per model, each under a permanent name (RUNBOOK.md, "Release a new model"). The defaults are
# production; a canary is the same file deployed with other values, e.g.
#   NOVA_APP=nova-next-serve NOVA_MODEL_DIR=nova-sft2b-v1-merged NOVA_SERVED=nova-next modal deploy serving/modal_nova.py
# The values are baked into the image's environment, so the container reads the same ones it was deployed with.
APP_NAME = os.environ.get("NOVA_APP", "nova-serve")
MODEL_DIR = os.environ.get("NOVA_MODEL_DIR", "nova-sft2a-v1-merged")
SERVED_NAME = os.environ.get("NOVA_SERVED", "nova")
HERE = os.path.dirname(os.path.abspath(__file__))

app = modal.App(APP_NAME)
models = modal.Volume.from_name("nova-models")
compile_cache = modal.Volume.from_name("nova-vllm-cache", create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("vllm==0.34.0")
    # vLLM keeps its own compile cache under /root/.cache/vllm (the volume); Triton's kernels (the hybrid
    # model's linear-attention layers) and Inductor's code default to the container's disk and were rebuilt on
    # every cold start (about two minutes). Both now live in the volume too.
    .env({"TRITON_CACHE_DIR": "/root/.cache/vllm/triton", "TORCHINDUCTOR_CACHE_DIR": "/root/.cache/vllm/inductor"})
    .add_local_file(os.path.join(HERE, "launch_vllm.sh"), "/srv/launch_vllm.sh")
    .env({"NOVA_APP": APP_NAME, "NOVA_MODEL_DIR": MODEL_DIR, "NOVA_SERVED": SERVED_NAME})
)


@app.function(image=image, gpu="L4", volumes={"/models": models, "/root/.cache/vllm": compile_cache},
              secrets=[modal.Secret.from_name("nova-serve")], scaledown_window=SCALEDOWN, timeout=4 * 3600,
              min_containers=0, max_containers=1)
@modal.concurrent(max_inputs=64)
@modal.web_server(port=PORT, startup_timeout=20 * 60)
def serve() -> None:
    env = dict(os.environ, MODEL=f"/models/{MODEL_DIR}", SERVED_NAME=SERVED_NAME, PORT=str(PORT))
    subprocess.Popen(["bash", "/srv/launch_vllm.sh"], env=env)
