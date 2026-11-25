"""The eval judge, gpt-oss-120b, served by vLLM on Modal as a private OpenAI-compatible endpoint.

The judge must not be the model that wrote the training data (Qwen3.5-27B), or it would favour the style it
taught: gpt-oss is another family, with open weights (Apache-2.0), so its verdicts can be re-run by anyone.
One H100 holds it in its native 4-bit (MXFP4) weights.

    uv run --group teacher modal run serving/modal_judge.py::download     # once: weights to the volume, on CPU
    uv run --group teacher modal deploy serving/modal_judge.py            # prints the endpoint URL
    uv run --group teacher modal app stop -y nova-judge                   # when done

It uses the same API key as the teacher (Modal secret nova-teacher), scales to zero after SCALEDOWN_S idle
seconds, and a cold start reloads the weights (minutes, billed).
"""

import os
import subprocess

import modal

MODEL = "openai/gpt-oss-120b"
SERVED_NAME = "judge"
PORT = 8000
SCALEDOWN_S = 300

app = modal.App("nova-judge")
weights = modal.Volume.from_name("nova-hf-cache", create_if_missing=True)
compile_cache = modal.Volume.from_name("nova-vllm-cache", create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("vllm==0.34.0", "huggingface_hub[hf_xet]")
    .env({"HF_HOME": "/hf", "HF_XET_HIGH_PERFORMANCE": "1", "VLLM_CACHE_ROOT": "/vllm-cache"})
)


@app.function(image=image, volumes={"/hf": weights}, timeout=3 * 3600, cpu=8, memory=16 * 1024)
def download() -> None:
    """Fetch the weights into the volume once; files already there are skipped."""
    from huggingface_hub import snapshot_download
    path = snapshot_download(MODEL, allow_patterns=["*.json", "*.safetensors", "*.txt", "*.jinja"],
                             ignore_patterns=["original/*", "metal/*"])
    weights.commit()
    print("weights in", path)


@app.function(image=image, gpu="H100", volumes={"/hf": weights, "/vllm-cache": compile_cache},
              secrets=[modal.Secret.from_name("nova-teacher")], scaledown_window=SCALEDOWN_S,
              timeout=8 * 3600, max_containers=1)
@modal.concurrent(max_inputs=64)
@modal.web_server(port=PORT, startup_timeout=40 * 60)
def serve() -> None:
    cmd = ["vllm", "serve", MODEL, "--served-model-name", SERVED_NAME, "--port", str(PORT),
           "--max-model-len", "16384", "--max-num-seqs", "64", "--gpu-memory-utilization", "0.92",
           "--enable-prefix-caching",       # the rubric opens every request
           "--api-key", os.environ["VLLM_API_KEY"]]
    subprocess.Popen(cmd)
