"""Export the fine-tune as a merged 16-bit model, and check the merge changed only what the adapter covers.

Nova ships as base + LoRA adapter by default (the adapter repo already holds the tokenizer and the chat template
the model was trained with). The merged copy is the fallback: one model, no LoRA at serve time.

    uv run --group local-model --with peft==0.21.2 python serving/export_formats.py merge \\
        --adapter outputs/sft2a-r16-lr2e-4-traj_v1 --out /data/nova-sft2a-v1-merged

Exporting is a change to the model, so the script measures it:
- weights: every tensor the adapter does not target must be bit-identical to the base; the targeted ones must change;
- outputs: next-token logits of the merged model against base + adapter (PEFT, unmerged) on a few prompts, with the
  largest difference and whether the top token agrees.

The tokenizer and chat-template files are copied from the adapter (the training render), the image and video
processor files from the base model, so the merged folder serves on its own.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

TRAINING_FILES = ["tokenizer.json", "tokenizer_config.json", "chat_template.jinja"]
BASE_FILES = ["preprocessor_config.json", "video_preprocessor_config.json", "generation_config.json"]
PROMPTS = [
    [{"role": "system", "content": "You are Nova, NimbusCart's support assistant."},
     {"role": "user", "content": "where is my order 10452?"}],
    [{"role": "user", "content": "I want to return the headphones I bought last week"}],
    [{"role": "user", "content": "can I talk to a person please, this is the third time I'm asking"}],
]


def load_base(name: str, device: str):
    import torch
    from transformers import AutoModelForImageTextToText

    return AutoModelForImageTextToText.from_pretrained(name, dtype=torch.bfloat16).to(device).eval()


def merge(adapter: str, out: Path, device: str, base: str) -> None:
    import torch
    from huggingface_hub import snapshot_download
    from peft import PeftModel
    from transformers import AutoTokenizer

    adapter_dir = Path(adapter) if Path(adapter).is_dir() else Path(snapshot_download(adapter))
    cfg = json.loads((adapter_dir / "adapter_config.json").read_text())
    base_name = base   # the base vLLM serves the adapter on, so every format starts from the same weights
    print(f"base {base_name} (trained on {cfg['base_model_name_or_path']}), adapter {adapter_dir} "
          f"(r={cfg['r']}, alpha={cfg['lora_alpha']})")

    tok = AutoTokenizer.from_pretrained(adapter_dir)
    base_sd = {k: v.detach().cpu().clone() for k, v in load_base(base_name, "cpu").state_dict().items()}

    peft_model = PeftModel.from_pretrained(load_base(base_name, device), adapter_dir).eval()
    prompts = [tok.apply_chat_template(p, add_generation_prompt=True, return_tensors="pt", return_dict=True)
               for p in PROMPTS]
    with torch.no_grad():
        ref = [peft_model(**{k: v.to(device) for k, v in p.items()}).logits[0, -1].float().cpu() for p in prompts]
    merged = peft_model.merge_and_unload()
    with torch.no_grad():
        got = [merged(**{k: v.to(device) for k, v in p.items()}).logits[0, -1].float().cpu() for p in prompts]

    merged_sd = merged.state_dict()
    changed = [k for k, v in merged_sd.items() if not torch.equal(v.cpu(), base_sd[k])]
    missing = sorted(set(base_sd) ^ set(merged_sd))
    targets = {"q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"}
    outside = [k for k in changed if k.split(".")[-2] not in targets]
    report = {
        "base": base_name, "adapter": str(adapter), "tensors": len(merged_sd), "changed": len(changed),
        "changed_outside_lora_targets": outside, "keys_not_in_both": missing,
        "logits_max_abs_diff": [round(float((a - b).abs().max()), 4) for a, b in zip(ref, got)],
        "top_token_agrees": [int(a.argmax()) == int(b.argmax()) for a, b in zip(ref, got)],
    }
    print(json.dumps(report, indent=1))
    if outside or missing or not changed or not all(report["top_token_agrees"]):
        raise SystemExit("merge check failed")

    out.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(out, safe_serialization=True, max_shard_size="5GB")
    base_dir = Path(snapshot_download(base_name, allow_patterns=["*.json", "*.jinja", "*.txt"]))
    for f in BASE_FILES:
        if (base_dir / f).exists():
            shutil.copy(base_dir / f, out / f)
    for f in TRAINING_FILES:
        shutil.copy(adapter_dir / f, out / f)
    (out / "merge_check.json").write_text(json.dumps(report, indent=1) + "\n")
    print(f"saved {out}: {sorted(p.name for p in out.iterdir())}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("merge")
    m.add_argument("--adapter", required=True, help="adapter folder or Hub repo")
    m.add_argument("--out", type=Path, required=True)
    m.add_argument("--device", default="cuda")
    m.add_argument("--base", default="Qwen/Qwen3.5-2B", help="the base model the server loads")
    a = ap.parse_args()
    merge(a.adapter, a.out, a.device, a.base)


if __name__ == "__main__":
    main()
