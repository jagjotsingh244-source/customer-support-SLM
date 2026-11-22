"""Count LoRA parameters by hand, check the count against PEFT, and estimate training memory.

Runs on a laptop CPU: the model is built on PyTorch's "meta" device from its config, so there are shapes but no
weights, and nothing is downloaded beyond config.json.

    uv run --group local-model --with peft==0.21.2 python training/lora_budget.py

A LoRA adapter on a linear layer W (d_out x d_in) adds B (d_out x r) and A (r x d_in), so it trains
r * (d_in + d_out) parameters instead of d_in * d_out. The script reads every targeted layer's shape, applies that
formula, then wraps the same model with PEFT (the library Unsloth builds on) and checks the two counts agree.
"""

import argparse
import collections

import torch
from transformers import AutoConfig, AutoModelForImageTextToText

MODEL = "Qwen/Qwen3.5-2B"
# Unsloth's Qwen3.5 recipe. In this model only the 6 full-attention layers have q/k/v/o_proj; the 18
# linear-attention (Gated DeltaNet) layers name theirs in_proj_qkv, in_proj_z, in_proj_a, in_proj_b, out_proj.
TARGETS = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
RANKS = [8, 16, 64]
GB = 1e9


def build_skeleton():
    cfg = AutoConfig.from_pretrained(MODEL)
    with torch.device("meta"):
        return AutoModelForImageTextToText.from_config(cfg), cfg


def part(name):
    return "vision" if ".visual." in name else "text"


def linear_layers(model):
    """(name, d_in, d_out) for every nn.Linear except the output head (tied to the embeddings here)."""
    return [(n, m.in_features, m.out_features) for n, m in model.named_modules()
            if isinstance(m, torch.nn.Linear) and not n.endswith("lm_head")]


def hand_count(layers, targets, r):
    rows = collections.defaultdict(lambda: [0, 0, None])  # suffix -> [count, params, shape]
    for name, d_in, d_out in layers:
        suffix = name.split(".")[-1]
        if suffix in targets and part(name) == "text":
            row = rows[suffix]
            row[0] += 1
            row[1] += r * (d_in + d_out)
            row[2] = (d_out, d_in)
    return rows


def peft_count(model, targets, r):
    from peft import LoraConfig, get_peft_model

    lora = LoraConfig(r=r, lora_alpha=r, lora_dropout=0.0, bias="none", target_modules=targets,
                      task_type="CAUSAL_LM")
    wrapped = get_peft_model(model, lora)
    trainable = sum(p.numel() for p in wrapped.parameters() if p.requires_grad)
    wrapped_names = [n for n, m in wrapped.named_modules() if hasattr(m, "lora_A") and len(m.lora_A) > 0]
    wrapped.unload()  # take the adapters off again so the next rank starts from the bare model
    return trainable, wrapped_names


def memory_estimate(n_frozen, n_lora, batch, seq, hidden, layers, vocab):
    """Bytes for one training step. Returns rows of (what, bytes, how)."""
    rows = [
        ("Frozen base weights, 16-bit", 2 * n_frozen, "2 bytes x every base parameter"),
        ("LoRA weights, 32-bit", 4 * n_lora, "PEFT keeps adapters in fp32 over a 16-bit base"),
        ("LoRA gradients, 32-bit", 4 * n_lora, "same dtype as the adapter weights"),
        ("Adam moments, 8-bit (adamw_8bit)", 2 * n_lora, "two moments x 1 byte"),
        ("Saved layer inputs (gradient checkpointing)", batch * seq * hidden * 2 * layers,
         "batch x seq x hidden x 2 bytes x layers"),
        ("Logits and their gradient, 32-bit", 2 * batch * seq * vocab * 4,
         "batch x seq x vocab x 4 bytes, twice; Unsloth's chunked loss avoids most of this"),
    ]
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=2)
    ap.add_argument("--seq", type=int, default=256, help="max_seq_length from the dataset card")
    ap.add_argument("--rank", type=int, default=16, help="rank used for the memory estimate")
    ap.add_argument("--skip-peft", action="store_true")
    a = ap.parse_args()

    model, cfg = build_skeleton()
    tc = cfg.text_config
    layers = linear_layers(model)

    total = sum(p.numel() for p in model.parameters())
    vision = sum(p.numel() for n, p in model.named_parameters() if part(n) == "vision")
    print(f"{MODEL}: {total:,} parameters ({total - vision:,} text, {vision:,} vision; lm_head tied to the "
          f"embeddings, counted once)")
    kinds = collections.Counter(tc.layer_types)
    print(f"Text layers: {tc.num_hidden_layers} ({dict(kinds)})\n")

    print("Hand count, the seven Unsloth targets (text model only):")
    print(f"{'module':<10} {'shape (out x in)':>17} {'layers':>6} " + " ".join(f"{'r=' + str(r):>12}" for r in RANKS))
    per_rank = {r: hand_count(layers, TARGETS, r) for r in RANKS}
    for t in TARGETS:
        count, _, shape = per_rank[RANKS[0]][t]
        cells = " ".join(f"{per_rank[r][t][1]:>12,}" for r in RANKS)
        print(f"{t:<10} {f'{shape[0]} x {shape[1]}':>17} {count:>6} {cells}")
    totals = {r: sum(v[1] for v in per_rank[r].values()) for r in RANKS}
    print(f"{'total':<10} {'':>17} {'':>6} " + " ".join(f"{totals[r]:>12,}" for r in RANKS))
    print("share of model: " + ", ".join(f"r={r} {totals[r] / total:.2%}" for r in RANKS) + "\n")

    missed = [(n, i, o) for n, i, o in layers if part(n) == "text" and n.split(".")[-1] not in TARGETS]
    by = collections.defaultdict(lambda: [0, 0])
    for n, i, o in missed:
        by[n.split(".")[-1]][0] += 1
        by[n.split(".")[-1]][1] += 16 * (i + o)
    print("Text linear layers the seven names do not reach (r=16 cost if added):")
    for k, (c, p) in by.items():
        print(f"  {k:<12} x{c:<3} {p:>11,}")
    vis = [n for n, _, _ in layers if part(n) == "vision"]
    print(f'  ("all-linear" would also wrap {len(vis)} vision-tower layers)\n')

    if not a.skip_peft:
        print("Library check (PEFT get_peft_model, same targets):")
        for r in RANKS:
            n, names = peft_count(model, TARGETS, r)
            vision_hit = sum(part(x) == "vision" for x in names)
            ok = "match" if n == totals[r] else f"OFF BY {n - totals[r]:,}"
            print(f"  r={r:<3} PEFT {n:>12,}  hand {totals[r]:>12,}  {ok}  "
                  f"({len(names)} layers wrapped, {vision_hit} in the vision tower)")
        print()

    n_lora = totals.get(a.rank) or sum(v[1] for v in hand_count(layers, TARGETS, a.rank).values())
    for label, frozen in [("text only", total - vision), ("with the vision tower", total)]:
        rows = memory_estimate(frozen, n_lora, a.batch, a.seq, tc.hidden_size, tc.num_hidden_layers,
                               tc.vocab_size)
        print(f"LoRA r={a.rank} training memory, batch {a.batch} x seq {a.seq}, base loaded {label}:")
        for what, b, how in rows:
            print(f"  {what:<46} {b / GB:>6.2f} GB   {how}")
        print(f"  {'total':<46} {sum(b for _, b, _ in rows) / GB:>6.2f} GB\n")

    for label, n in [("text only", total - vision), ("with the vision tower", total)]:
        print(f"Full fine-tune with Adam, mixed precision, {label}: 16 bytes x {n / 1e9:.2f}B = "
              f"{16 * n / GB:.1f} GB before activations (a T4 has 15 GB usable)")


if __name__ == "__main__":
    main()
