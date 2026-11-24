"""Nova's own model, Qwen3.5-2B, served by vLLM on Modal with its LoRA adapters, for evals.

One server answers for every system being compared: the base model under its own name and each adapter under a
short name (sft1, sft2a, sft2b), the way vLLM serves LoRA modules. Same vLLM version, tool-call parser and
settings as the student was checked with on Kaggle (requirements-serve.txt), on a cheaper card than the teacher's (an L4, or an A10G or L40S when no L4 is free):
a 2B model needs about 5 GB.

The adapters are uploaded from this machine into a Modal volume (no Hub token goes to Modal):

    # only the two adapter files per adapter (a run folder also holds its checkpoints)
    uv run --group teacher modal volume put -f nova-adapters <adapter folder>/adapter_config.json /sft2a/adapter_config.json
    uv run --group teacher modal volume put -f nova-adapters <adapter folder>/adapter_model.safetensors /sft2a/adapter_model.safetensors
    uv run --group teacher modal deploy serving/modal_student.py
    # then evals/run_eval.py --base-url <url>/v1 --model sft2a ... (OPENAI_API_KEY = TEACHER_API_KEY)
    # adapters are read when a container starts: after adding one, stop the app (modal app stop -y nova-student)
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


@app.function(image=image, gpu=["L4", "A10G", "L40S"], volumes={"/hf": weights, "/adapters": adapters},
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
