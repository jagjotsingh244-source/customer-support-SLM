"""The teacher model for synthetic conversations, served by vLLM on Modal as a private OpenAI-compatible endpoint.

The generator (synth/generate.py) runs on the laptop: it holds the database, the help-center search and the
customer simulator, and sends only model requests here. The loop does not change; the teacher is a base_url.

Two teachers, both Apache-2.0 (training on their output is allowed), both the student's own family and chat
format. Pick one with TEACHER when deploying; each gets its own app, so both can be up for a side-by-side test.

    27b        Qwen3.5-27B, full precision (bf16), one A100-80GB          ~$2.50 an hour while running
    397b-int4  Qwen3.5-397B-A17B, 4-bit GPTQ, four H100s                  ~$15.80 an hour while running

One-time setup (the weights go to a Modal volume first, on a CPU machine, so no GPU time is spent downloading):

    uv run --group teacher modal setup
    uv run --group teacher modal secret create nova-teacher VLLM_API_KEY=<random string, also TEACHER_API_KEY in .env>
    TEACHER=27b uv run --group teacher modal run serving/modal_teacher.py::download

Then:

    TEACHER=27b uv run --group teacher modal deploy serving/modal_teacher.py    # prints the endpoint URL
    TEACHER=27b uv run --group teacher modal app stop nova-teacher-27b           # when done

The container scales to zero after SCALEDOWN_S idle seconds, so an idle deploy costs nothing, but a cold start
reloads the weights (minutes, billed). The server rejects requests without the API key.
"""

import os
import subprocess

import modal

TEACHERS = {
    "27b": {"model": "Qwen/Qwen3.5-27B", "gpu": "A100-80GB", "tp": 1, "args": []},
    "397b-int4": {"model": "Qwen/Qwen3.5-397B-A17B-GPTQ-Int4", "gpu": "H100:4", "tp": 4,
                  "args": ["--quantization", "moe_wna16"]},
}
NAME = os.environ.get("TEACHER", "27b")
T = TEACHERS[NAME]
SERVED_NAME = "teacher"          # what the generator sends as `model`; the real model is in /v1/models
PORT = 8000
SCALEDOWN_S = 300                # idle seconds before the GPU is released
VLLM_VERSION = "0.34.0"          # the version the student is served with (requirements-serve.txt)

app = modal.App(f"nova-teacher-{NAME}")
weights = modal.Volume.from_name("nova-hf-cache", create_if_missing=True)
compile_cache = modal.Volume.from_name("nova-vllm-cache", create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install(f"vllm=={VLLM_VERSION}", "huggingface_hub[hf_xet]")
    # TEACHER is baked into the image: the container imports this file again, and without it would fall back
    # to the default teacher whatever was chosen on the laptop.
    .env({"HF_HOME": "/hf", "HF_XET_HIGH_PERFORMANCE": "1", "VLLM_CACHE_ROOT": "/vllm-cache", "TEACHER": NAME})
)


@app.function(image=image, volumes={"/hf": weights}, timeout=3 * 3600, cpu=8, memory=16 * 1024)
def download() -> None:
    """Fetch the weights into the volume once. Safe to re-run: files already there are skipped."""
    from huggingface_hub import snapshot_download
    path = snapshot_download(T["model"], allow_patterns=["*.json", "*.safetensors", "*.txt", "*.jinja", "*.model"])
    weights.commit()
    print("weights in", path)


@app.function(image=image, gpu=T["gpu"], volumes={"/hf": weights, "/vllm-cache": compile_cache},
              secrets=[modal.Secret.from_name("nova-teacher")], scaledown_window=SCALEDOWN_S,
              timeout=24 * 3600, max_containers=1)
@modal.concurrent(max_inputs=64)            # one vLLM engine batches all the generator's parallel requests
@modal.web_server(port=PORT, startup_timeout=40 * 60)
def serve() -> None:
    cmd = ["vllm", "serve", T["model"], "--served-model-name", SERVED_NAME, "--port", str(PORT),
           "--tensor-parallel-size", str(T["tp"]),
           "--max-model-len", "16384",      # teacher prompts are ~2-4k tokens; long contexts only cost memory
           "--max-num-seqs", "64",
           "--gpu-memory-utilization", "0.92",
           "--language-model-only",         # skip the vision encoder: text only, more room for the KV cache
           "--enable-auto-tool-choice", "--tool-call-parser", "qwen3_coder",   # same parser as the student
           "--enable-prefix-caching",       # the tool schemas and rules open every request
           "--api-key", os.environ["VLLM_API_KEY"],
           *T["args"]]
    # No --reasoning-parser: the generator turns thinking off per request (chat_template_kwargs), so nothing
    # the student should not learn is ever produced.
    subprocess.Popen(cmd)
