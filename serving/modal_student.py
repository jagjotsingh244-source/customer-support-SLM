"""Nova's own model, Qwen3.5-2B, served by vLLM on Modal with its LoRA adapters, for evals.

One server answers for every system being compared: the base model under its own name and each adapter under a
short name (sft1, sft2a, sft2b), the way vLLM serves LoRA modules. Same vLLM version, tool-call parser and
settings as the student was checked with on Kaggle (requirements-serve.txt), on a cheaper card than the teacher's:
a 2B model needs about 5 GB.

The adapters are uploaded from this machine into a Modal volume (no Hub token goes to Modal):

    uv run --group teacher modal volume put nova-adapters data/adapters/sft1-r16-lr2e-4-bitext_v1 /sft1
    uv run --group teacher modal volume put nova-adapters outputs/<sft2a run> /sft2a
    uv run --group teacher modal volume put nova-adapters outputs/<sft2b run> /sft2b
    uv run --group teacher modal deploy serving/modal_student.py
    # then evals/run_eval.py --base-url <url>/v1 --model sft2a ... (OPENAI_API_KEY = TEACHER_API_KEY)
"""

import os
import subprocess

import modal

BASE = "Qwen/Qwen3.5-2B"
ADAPTERS = ["sft1", "sft2a", "sft2b"]
PORT = 8000

app = modal.App("nova-student")
weights = modal.Volume.from_name("nova-hf-cache", create_if_missing=True)
adapters = modal.Volume.from_name("nova-adapters", create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("vllm==0.34.0", "huggingface_hub[hf_xet]")
    .env({"HF_HOME": "/hf", "HF_XET_HIGH_PERFORMANCE": "1"})
)


@app.function(image=image, gpu="L4", volumes={"/hf": weights, "/adapters": adapters},
              secrets=[modal.Secret.from_name("nova-teacher")], scaledown_window=300, timeout=8 * 3600,
              max_containers=1)
@modal.concurrent(max_inputs=32)
@modal.web_server(port=PORT, startup_timeout=30 * 60)
def serve() -> None:
    present = [a for a in ADAPTERS if os.path.exists(f"/adapters/{a}/adapter_config.json")]
    cmd = ["vllm", "serve", BASE, "--port", str(PORT), "--dtype", "bfloat16", "--max-model-len", "8192",
           "--language-model-only", "--enable-auto-tool-choice", "--tool-call-parser", "qwen3_coder",
           "--api-key", os.environ["VLLM_API_KEY"]]
    if present:
        cmd += ["--enable-lora", "--max-lora-rank", "16", "--max-loras", str(len(present)),
                "--lora-modules", *[f"{a}=/adapters/{a}" for a in present]]
    print(" ".join(c if c != os.environ["VLLM_API_KEY"] else "***" for c in cmd), flush=True)
    subprocess.Popen(cmd)
