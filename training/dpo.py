"""Preference tuning (DPO) on top of SFT-2a, from the pairs of training/preference_pairs.py.

Starts from SFT-2a merged into the base (serving/export_formats.py merge) and trains a fresh LoRA on it. With a
PEFT model, TRL uses the same weights with the adapter switched off as the frozen reference, so the reference is
exactly SFT-2a and nothing is loaded twice.

Each pair is rendered here with Nova's chat template and tool schemas, exactly as served: the prompt as the
template renders it up to the generation cue, chosen and rejected as the rest of the rendered conversation. TRL
then gets plain strings, so tool calls are scored in the format the model writes them.

    ~/train-env/bin/python training/dpo.py --model outputs/nova-sft2a-v1-merged \\
        --pairs data/preference/nova-pairs-v1.jsonl --out outputs/dpo-sft2a-v1

Settings (beta 0.1, learning rate 5e-6, one epoch) are the usual DPO starting point; the SFT learning rate
(2e-4) would be far too high. Validation is 10% of pairs, held out by conversation.
"""

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agent.chat_template import for_template  # noqa: E402

TARGETS = r".*language_model.*\.(q_proj|k_proj|v_proj|o_proj|gate_proj|up_proj|down_proj)"


def render(tok, tools, prompt: list[dict], reply: list[dict]) -> tuple[str, str]:
    """(prompt text up to the generation cue, the reply's text after it)."""
    head = tok.apply_chat_template(for_template(prompt), tools=tools, add_generation_prompt=True, tokenize=False)
    full = tok.apply_chat_template(for_template(prompt + reply), tools=tools, tokenize=False)
    if not full.startswith(head):
        raise ValueError("the rendered conversation does not start with the rendered prompt")
    return head, full[len(head):]


def to_rows(tok, tools, pairs: list[dict]) -> list[dict]:
    rows = []
    for p in pairs:
        prompt, chosen = render(tok, tools, p["prompt"], p["chosen"])
        _, rejected = render(tok, tools, p["prompt"], p["rejected"])
        if chosen.strip() != rejected.strip():
            rows.append({"prompt": prompt, "chosen": chosen, "rejected": rejected, "tag": p["tag"],
                         "conversation": p["conversation"]})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="SFT-2a merged into the base")
    ap.add_argument("--pairs", nargs="+", default=["data/preference/nova-pairs-v1.jsonl",
                                                   "data/preference/nova-pairs-no-answer-v1.jsonl"])
    ap.add_argument("--out", default="outputs/dpo-sft2a-v1")
    ap.add_argument("--beta", type=float, default=0.1)
    ap.add_argument("--lr", type=float, default=5e-6)
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--r", type=int, default=16)
    ap.add_argument("--max-length", type=int, default=3072)
    ap.add_argument("--seed", type=int, default=3407)
    ap.add_argument("--dry-run", action="store_true", help="render the pairs and print one, no training")
    a = ap.parse_args()

    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForImageTextToText, AutoTokenizer
    from trl import DPOConfig, DPOTrainer

    from agent.tools_v2 import TOOLS

    tok = AutoTokenizer.from_pretrained(a.model)
    pairs = [json.loads(line) for f in a.pairs for line in Path(f).read_text().splitlines()]
    rows = to_rows(tok, TOOLS, pairs)
    convs = sorted({r["conversation"] for r in rows})
    random.Random(a.seed).shuffle(convs)
    held = set(convs[: max(1, len(convs) // 10)])
    train = [r for r in rows if r["conversation"] not in held]
    val = [r for r in rows if r["conversation"] in held]
    print(f"{len(pairs)} pairs, {len(rows)} usable, {len(train)} train / {len(val)} validation")
    if a.dry_run:
        r = train[0]
        print(r["tag"], "\n--- chosen ---\n", r["chosen"], "\n--- rejected ---\n", r["rejected"])
        return

    model = AutoModelForImageTextToText.from_pretrained(a.model, dtype=torch.bfloat16).to("cuda")
    model.config.use_cache = False
    model = get_peft_model(model, LoraConfig(r=a.r, lora_alpha=a.r, lora_dropout=0.0, target_modules=TARGETS,
                                             task_type="CAUSAL_LM"))
    model.print_trainable_parameters()
    keep = ["prompt", "chosen", "rejected"]
    cfg = DPOConfig(output_dir=a.out, beta=a.beta, learning_rate=a.lr, num_train_epochs=a.epochs,
                    per_device_train_batch_size=2, gradient_accumulation_steps=8, per_device_eval_batch_size=2,
                    lr_scheduler_type="cosine", warmup_steps=2, bf16=True, gradient_checkpointing=True,
                    max_length=a.max_length, logging_steps=5, eval_strategy="steps", eval_steps=10,
                    save_strategy="no", report_to=[], seed=a.seed, remove_unused_columns=False)
    trainer = DPOTrainer(model=model, args=cfg, processing_class=tok,
                         train_dataset=Dataset.from_list([{k: r[k] for k in keep} for r in train]),
                         eval_dataset=Dataset.from_list([{k: r[k] for k in keep} for r in val]))
    trainer.train()
    print(json.dumps(trainer.evaluate()))
    model.save_pretrained(a.out)
    tok.save_pretrained(a.out)
    (Path(a.out) / "train_log.json").write_text(json.dumps(trainer.state.log_history, indent=1))


if __name__ == "__main__":
    main()
