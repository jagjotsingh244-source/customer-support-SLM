"""Run training/sft.py on a Modal A100 instead of a Kaggle T4.

The second fine-tune trains on about 11M tokens: roughly 7 hours per run on a T4, under an hour on an A100. The
training code is the same file either way; this only builds the environment (requirements-gpu.txt), ships the
repo's code and the locally built data into the container, runs one config, and keeps the outputs in a Modal
volume. No token goes to Modal: the data and the SFT-1 adapter are copied in from this machine, and the finished
adapter comes back here to be pushed to the Hub from where you are signed in.

    # once: the SFT-1 adapter, for SFT-2b (private on the Hub, so it is fetched here, not in the container)
    uv run --group data python -c "from huggingface_hub import snapshot_download as d; \\
        d('123jagjot/sft1-r16-lr2e-4-bitext_v1', local_dir='data/adapters/sft1-r16-lr2e-4-bitext_v1')"
    uv run --group teacher modal run training/modal_train.py --config training/configs/sft2a.yaml
    uv run --group teacher modal run training/modal_train.py --config training/configs/sft2b.yaml \\
        --sets "init_adapter=data/adapters/sft1-r16-lr2e-4-bitext_v1"
    uv run --group teacher modal volume get nova-train <run name> outputs/
"""

from pathlib import Path

import modal

REPO = Path(__file__).resolve().parent.parent
GPU = "A100-80GB"
CODE = ["agent", "training", "rag", "db", "config.py"]          # what sft.py imports (tools_v2 needs db/roles.py)
DATA = ["data/synthetic/nova-sft2-mix-v1", "data/adapters"]    # built or fetched locally

# The container imports this file again, where the repo is not on disk: only read and add local files here.
pins = [line.split("#")[0].strip() for line in (REPO / "requirements-gpu.txt").read_text().splitlines()
        if line.strip() and not line.startswith("#")] if (REPO / "requirements-gpu.txt").exists() else []
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .uv_pip_install(*pins, "huggingface_hub", "safetensors", "pydantic>=2.14", "psycopg[binary]", "pgvector")
    .env({"HF_HOME": "/hf", "TOKENIZERS_PARALLELISM": "false"})
)
if (REPO / "training").is_dir():                      # on this machine, not inside the container
    for path in CODE:
        src = REPO / path
        image = image.add_local_dir(src, f"/repo/{path}", ignore=["__pycache__"]) if src.is_dir() else \
            image.add_local_file(src, f"/repo/{path}")
    for path in DATA:
        if (REPO / path).exists():
            image = image.add_local_dir(REPO / path, f"/repo/{path}")

app = modal.App("nova-train")
outputs = modal.Volume.from_name("nova-train", create_if_missing=True)
hf_cache = modal.Volume.from_name("nova-hf-cache", create_if_missing=True)


@app.function(image=image, gpu=GPU, volumes={"/outputs": outputs, "/hf": hf_cache}, timeout=4 * 3600)
def train(config: str, sets: list[str]) -> str:
    import os
    import subprocess
    import sys

    os.chdir("/repo")
    cmd = [sys.executable, "training/sft.py", "--config", config, "--set", "output_root=/outputs", *sets]
    print(" ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)
    outputs.commit()
    runs = sorted(Path("/outputs").iterdir(), key=lambda p: p.stat().st_mtime)
    return runs[-1].name


@app.local_entrypoint()
def main(config: str, sets: str = ""):
    name = train.remote(config, sets.split())
    print(f"done: {name}\nfetch with: uv run --group teacher modal volume get nova-train {name} outputs/")
