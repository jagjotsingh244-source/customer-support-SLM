"""Supervised fine-tuning of Nova's voice: a 16-bit LoRA over Qwen3.5-2B with Unsloth.

All training logic lives here, versioned in Git; notebooks only call it. One run:

- tokenizes every split with training/masking.py (the code tests/test_masking.py checks), so the loss counts only
  Nova's reply and its <|im_end|>, and fails if a row would not fit max_seq_length instead of truncating it;
- checks, on real rows, that the trained tokens decode to exactly the reply, and that the tokenizer Unsloth loads
  renders the chat template exactly like the reference tokenizer (a template mismatch is the usual reason a model
  behaves worse after export);
- trains, measuring loss on the validation split and on the held-out intents at every evaluation, starting at
  step 0;
- generates fixed probe prompts greedily at every evaluation, so the replies can be read as they change;
- records what the run was: config, dataset revision, git commit, library versions, trainable parameters
  against the hand count, and peak GPU memory, in <output_dir>/run_info.json.

The data is tokenized and padded here, so the trainer is plain transformers.Trainer: it gets input_ids and labels
and adds no data processing of its own.

    python training/sft.py --config training/configs/sft1.yaml                     # train (GPU)
    python training/sft.py --config training/configs/sft1.yaml --push --report-to wandb
    python training/sft.py --config training/configs/sft1.yaml --set r=8 lora_alpha=8 train_rows=1000
    uv run --group data --group local-model python training/sft.py --config training/configs/sft1.yaml --dry-run
"""

import argparse
import importlib.metadata as md
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from agent.prompts import PROMPT_VERSION, system_prompt  # noqa: E402
from config import now  # noqa: E402
from agent.chat_template import for_template  # noqa: E402
from training.masking import END, IGNORE, tokenize  # noqa: E402

REFERENCE_TOKENIZER = "Qwen/Qwen3.5-2B"  # the tokenizer tests/test_masking.py checks the markers against
LOAD_SEQ_LEN = 512  # what Unsloth is told at load time: room for a probe prompt (~200 tokens) plus its reply
# The second fine-tune's probes: conversations rendered with Nova's tools, as served. Each says what a good first
# step is: "call" a tool or "reply" without one. "thanks!" calling list_my_orders is the failure to catch early.
TOOL_PROBES = [
    ("thanks!", [{"role": "user", "content": "thanks!"}], "reply"),
    ("are you a bot?", [{"role": "user", "content": "are you a bot?"}], "reply"),
    ("where is order 11904", [{"role": "user", "content": "where is my order 11904?"}], "call"),
    ("refund time (policy)", [{"role": "user", "content": "how long do card refunds take?"}], "call"),
    ("thanks after an answer", [
        {"role": "user", "content": "where is my order 11904?"},
        {"role": "assistant", "content": "Order 11904, your 1080p webcam, is in transit with SwiftShip (SS70001836); "
                                          "it was last scanned at the Nagpur hub on 2026-11-18."},
        {"role": "user", "content": "ok thanks, that's all"}], "reply"),
]
PROBE_CUSTOMER = "Anay Vasa"
PROBES = [
    "hello",
    "thanks, bye",
    "i want to cancel my order",
    "where is my refund??",
    "where is my order?",
    "your service is terrible",
    "can you change my address",
    "i want to talk to a real person",
]
VERSIONS = ["torch", "transformers", "peft", "unsloth", "unsloth_zoo", "accelerate", "datasets",
            "bitsandbytes", "triton"]


# ---------------------------------------------------------------- config and identity

def load_config(path, overrides=()):
    with open(path) as f:
        cfg = yaml.safe_load(f)
    for item in overrides:
        key, sep, value = item.partition("=")
        if not sep or key not in cfg:
            raise SystemExit(f"--set expects key=value with a key from {path}; got {item!r}")
        cfg[key] = yaml.safe_load(value)
    return cfg


def lr_tag(lr):
    mantissa, exp = f"{lr:.0e}".split("e")
    return f"{mantissa}e{int(exp)}"  # 2e-4, not 2e-04


def run_name(cfg):
    """Names a run by what varies between runs, e.g. sft1-r16-lr2e-4-bitext_v1 or sft1-r8-a8-lr2e-4-bitext_v1-1000rows."""
    name = f"{cfg['run_prefix']}-r{cfg['r']}"
    if cfg["lora_alpha"] != cfg["r"]:
        name += f"-a{cfg['lora_alpha']}"
    name += f"-lr{lr_tag(cfg['learning_rate'])}-{cfg['data_version']}"
    if cfg["train_rows"]:
        name += f"-{cfg['train_rows']}rows"
    return name


def git(*args):
    try:
        return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def versions():
    found = {}
    for name in VERSIONS:
        try:
            found[name] = md.version(name)
        except md.PackageNotFoundError:
            pass
    return found


def plan(cfg, n_train):
    """Optimizer steps for the run, worked out before training so warmup is a fixed number of steps."""
    per_step = cfg["per_device_train_batch_size"] * cfg["gradient_accumulation_steps"]
    steps = math.ceil(n_train / per_step) * cfg["num_train_epochs"]
    return {"examples_per_step": per_step, "steps": steps, "warmup_steps": math.ceil(cfg["warmup_ratio"] * steps),
            "evaluations": 1 + steps // cfg["eval_steps"]}


# ---------------------------------------------------------------- data

def tools_for(cfg):
    """Nova's tool schemas when the config renders with tools (the second fine-tune), else None."""
    if not cfg.get("tools"):
        return None
    from agent.tools_v2 import TOOLS
    return TOOLS


def messages_of(row):
    """A row's messages as the chat template wants them (tool-call arguments as mappings)."""
    msgs = row["messages"]
    return for_template(json.loads(msgs) if isinstance(msgs, str) else msgs)


def load_splits(cfg):
    from datasets import load_dataset, load_from_disk

    if cfg.get("data_path"):                              # a dataset built locally (training/sft2_mix.py)
        path = Path(cfg["data_path"])
        ds = load_from_disk(str(path if path.is_absolute() else REPO / path))
    else:
        ds = load_dataset(cfg["dataset_name"], revision=cfg["dataset_revision"])
    if cfg["train_rows"]:
        ds["train"] = ds["train"].shuffle(seed=cfg["seed"]).select(range(cfg["train_rows"]))
    return ds


def encode(split, tok, max_len, tools=None):
    def one(row):
        out = tokenize(messages_of(row), tok, tools=tools)
        if len(out["input_ids"]) > max_len:
            raise ValueError(f"row {row.get('row_id', row.get('conversation'))} renders to {len(out['input_ids'])} "
                             f"tokens, over max_seq_length {max_len}; truncating would cut the reply, so raise "
                             "max_seq_length instead")
        return out

    return split.map(one, remove_columns=split.column_names)


def check_mask(raw, encoded, tok, n=200):
    """The trained tokens of each row are exactly its last message and <|im_end|>: the reply word for word, or for
    a tool call the call markup with no tool result and no other turn inside it."""
    n = min(n, len(raw))
    for i in range(n):
        ids, labels = encoded[i]["input_ids"], encoded[i]["labels"]
        trained = tok.decode([t for t, lab in zip(ids, labels) if lab != IGNORE])
        last = messages_of(raw[i])[-1]
        where = raw[i].get("row_id", raw[i].get("conversation"))
        if last.get("tool_calls"):
            ok = (trained.startswith("<tool_call>") and trained.endswith("</tool_call>" + END)
                  and "<tool_response>" not in trained and "<|im_start|>" not in trained)
        else:
            ok = trained == last["content"] + END
        if not ok:
            raise AssertionError(f"mask check failed on row {where}:\ntrained:  {trained!r}\nlast message: {last!r}")
    return n


def render(t, messages, **kw):
    return t.apply_chat_template(messages, tokenize=False, **kw)


def check_same_template(ref, tk, rows, tools=None):
    """Unsloth's tokenizer must render and encode exactly like the reference, or training and serving disagree."""
    for row in rows:
        msgs_all = messages_of(row)
        for msgs, kw in [(msgs_all, {"tools": tools}), (msgs_all[:-1], {"add_generation_prompt": True, "tools": tools})]:
            a, b = render(ref, msgs, **kw), render(tk, msgs, **kw)
            if a != b:
                raise AssertionError(f"chat templates differ on row {row.get('row_id')}:\nreference: {a!r}\n"
                                     f"loaded:    {b!r}")
            if ref(a, add_special_tokens=False)["input_ids"] != tk(b, add_special_tokens=False)["input_ids"]:
                raise AssertionError(f"tokenizers encode row {row.get('row_id')} differently")


class PadCollator:
    """Right-pads a batch: input_ids with the pad token, labels with IGNORE, attention_mask with 0."""

    def __init__(self, pad_id):
        self.pad_id = pad_id

    def __call__(self, feats):
        import torch

        n = max(len(f["input_ids"]) for f in feats)

        def pad(key, value):
            return torch.tensor([f[key] + [value] * (n - len(f[key])) for f in feats])

        feats = [{k: f[k] for k in ("input_ids", "attention_mask", "labels")} for f in feats]
        return {"input_ids": pad("input_ids", self.pad_id), "attention_mask": pad("attention_mask", 0),
                "labels": pad("labels", IGNORE)}


def prepare(cfg, ref):
    """Loads, encodes and checks every split. Returns (raw splits, encoded splits, stats)."""
    raw = load_splits(cfg)
    enc = {k: encode(v, ref, cfg["max_seq_length"], tools_for(cfg)) for k, v in raw.items()}
    enc = {k: v.add_column("length", [len(x) for x in v["input_ids"]]) for k, v in enc.items()}  # for group_by_length
    checked = {k: check_mask(raw[k], enc[k], ref) for k in raw}
    stats = {}
    for k, v in enc.items():
        lengths = [len(x) for x in v["input_ids"]]
        trained = [sum(lab != IGNORE for lab in x) for x in v["labels"]]
        stats[k] = {"rows": len(v), "max_tokens": max(lengths), "mean_tokens": round(sum(lengths) / len(lengths), 1),
                    "mean_trained_tokens": round(sum(trained) / len(trained), 1), "mask_checked_rows": checked[k]}
    return raw, enc, stats


# ---------------------------------------------------------------- probes

def make_probe(tok, max_new_tokens, path, tools=None):
    """A callback that generates every probe greedily at each evaluation, prints the replies and appends them to
    probes.jsonl. Built here, not at module level, so the dry run never imports Unsloth."""
    import torch
    from transformers import TrainerCallback
    from unsloth import FastLanguageModel

    tk = getattr(tok, "tokenizer", tok)  # Unsloth may hand back a multimodal processor; its tokenizer is inside
    stop = [tk.convert_tokens_to_ids("<|im_end|>"), tk.convert_tokens_to_ids("<|endoftext|>")]
    if tools:                                          # as served: prompt v2, an empty state block, the tools
        from agent.state import State
        system = system_prompt(now(), PROBE_CUSTOMER, "v2") + "\n\n" + State().render()
        probes = [(name, msgs, want) for name, msgs, want in TOOL_PROBES]
    else:
        system = system_prompt(now(), PROBE_CUSTOMER)
        probes = [(p, [{"role": "user", "content": p}], None) for p in PROBES]

    class _Probe(TrainerCallback):
        def __init__(self):
            self.done, self.rows = set(), []

        def on_evaluate(self, args, state, control, model=None, **kwargs):
            if state.global_step in self.done:  # called once per eval split; probe once per step
                return
            self.done.add(state.global_step)
            FastLanguageModel.for_inference(model)
            try:
                for prompt, msgs, want in probes:
                    text = render(tk, [{"role": "system", "content": system}] + msgs, add_generation_prompt=True,
                                  tools=tools)
                    ids = tk(text, return_tensors="pt", add_special_tokens=False)["input_ids"].to(model.device)
                    with torch.no_grad():
                        out = model.generate(input_ids=ids, attention_mask=torch.ones_like(ids), do_sample=False,
                                             max_new_tokens=max_new_tokens, eos_token_id=stop,
                                             pad_token_id=tk.pad_token_id)
                    new = out[0, ids.shape[1]:].tolist()
                    reply = tk.decode(new, skip_special_tokens=not tools).strip()
                    row = {"step": state.global_step, "prompt": prompt, "reply": reply, "words": len(reply.split()),
                           "tokens": len(new), "stopped": bool(new) and new[-1] in stop}
                    if want:                               # did it call a tool where it should, and only there
                        row["first_step"] = "call" if "<tool_call>" in reply else "reply"
                        row["as_expected"] = row["first_step"] == want
                    self.rows.append(row)
                    with open(path, "a") as f:
                        f.write(json.dumps(row) + "\n")
                    cut = "" if row["stopped"] else "  [no end-of-turn: cut off]"
                    mark = "" if not want else ("  [ok]" if row["as_expected"] else f"  [WRONG: wanted a {want}]")
                    print(f"[step {row['step']}] {prompt!r} -> {reply[:300]}{cut}{mark}", flush=True)
            finally:
                FastLanguageModel.for_training(model)
            self.log_table()

        def log_table(self):
            try:
                import wandb
            except ImportError:
                return
            if wandb.run is not None:
                cols = ["step", "prompt", "reply", "words", "stopped"]
                wandb.log({"probes": wandb.Table(columns=cols, data=[[r[c] for c in cols] for r in self.rows])},
                          commit=False)

    return _Probe()


# ---------------------------------------------------------------- training

def load_adapter_weights(model, adapter):
    """Copy a saved LoRA adapter's weights into the freshly wrapped model (same rank and target modules), so
    training continues from it. `adapter` is a folder or a Hub id. Fails if any adapter tensor is left unloaded."""
    from huggingface_hub import snapshot_download
    from peft import set_peft_model_state_dict
    from safetensors.torch import load_file

    path = Path(adapter) if Path(adapter).exists() else Path(snapshot_download(adapter))
    weights = load_file(str(path / "adapter_model.safetensors"))
    result = set_peft_model_state_dict(model, weights)
    unexpected = getattr(result, "unexpected_keys", []) or []
    if unexpected:
        raise RuntimeError(f"{len(unexpected)} adapter tensors did not match the model, e.g. {unexpected[:2]}")
    print(f"continued from {adapter}: {len(weights)} adapter tensors loaded", flush=True)


def expected_trainable(cfg):
    """The hand count from training/lora_budget.py for this rank and these targets."""
    from training.lora_budget import build_skeleton, hand_count, linear_layers

    skeleton, _ = build_skeleton()
    return sum(v[1] for v in hand_count(linear_layers(skeleton), cfg["target_modules"], cfg["r"]).values())


def training_args(cfg, name, out, steps, precision, push=False, report_to="none"):
    """The trainer's settings for one run. precision: "bf16", "fp16" (a T4 has no bf16) or "fp32"."""
    from transformers import TrainingArguments

    return TrainingArguments(
        output_dir=str(out), run_name=name, seed=cfg["seed"], data_seed=cfg["seed"],
        num_train_epochs=cfg["num_train_epochs"],
        per_device_train_batch_size=cfg["per_device_train_batch_size"],
        gradient_accumulation_steps=cfg["gradient_accumulation_steps"],
        per_device_eval_batch_size=cfg["per_device_eval_batch_size"],
        learning_rate=cfg["learning_rate"], warmup_steps=steps["warmup_steps"],
        lr_scheduler_type=cfg["lr_scheduler_type"], optim=cfg["optim"], weight_decay=cfg["weight_decay"],
        bf16=precision == "bf16", fp16=precision == "fp16",
        logging_steps=cfg["logging_steps"], logging_first_step=True,
        eval_strategy="steps", eval_steps=cfg["eval_steps"], eval_on_start=True,
        save_strategy="steps", save_steps=cfg["save_steps"], save_total_limit=None,
        prediction_loss_only=True, remove_unused_columns=False,
        # transformers 5: length grouping is a sampling strategy (LengthGroupedSampler), not a flag
        train_sampling_strategy="group_by_length" if cfg.get("group_by_length") else "random",
        length_column_name="length",
        report_to=report_to,
        push_to_hub=push, hub_model_id=f"{cfg['hub_user']}/{name}", hub_private_repo=True,
        hub_strategy="checkpoint",  # each save also goes to <repo>/last-checkpoint, so a lost session can resume
    )


def train(cfg, push=False, report_to="none"):
    from unsloth import FastLanguageModel, is_bf16_supported  # first, so Unsloth can patch what follows

    import torch
    from transformers import AutoTokenizer, Trainer

    name = run_name(cfg)
    out = Path(cfg["output_root"]) / name
    out.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("WANDB_PROJECT", "nova")
    os.environ.setdefault("TRACKIO_PROJECT", "nova")
    t_start = time.time()

    ref = AutoTokenizer.from_pretrained(REFERENCE_TOKENIZER)
    raw, enc, data_stats = prepare(cfg, ref)
    steps = plan(cfg, len(enc["train"]))
    print(f"run {name}: {json.dumps(data_stats)}\n{json.dumps(steps)}", flush=True)

    model, tok = FastLanguageModel.from_pretrained(
        model_name=cfg["model_name"], max_seq_length=max(LOAD_SEQ_LEN, cfg["max_seq_length"]),
        load_in_4bit=False, load_in_16bit=True, full_finetuning=False)
    tk = getattr(tok, "tokenizer", tok)
    check_same_template(ref, tk, [raw["train"][i] for i in range(20)], tools_for(cfg))
    memory_after_load = torch.cuda.memory_allocated()

    model = FastLanguageModel.get_peft_model(
        model, r=cfg["r"], lora_alpha=cfg["lora_alpha"], lora_dropout=cfg["lora_dropout"], bias="none",
        target_modules=cfg["target_modules"],
        use_gradient_checkpointing=cfg.get("gradient_checkpointing", "unsloth"), random_state=cfg["seed"])
    if cfg.get("init_adapter"):                       # continue from an earlier adapter (SFT-2b from SFT-1)
        load_adapter_weights(model, cfg["init_adapter"])
    model.print_trainable_parameters()
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    wrapped = [n for n, m in model.named_modules() if hasattr(m, "lora_A") and len(m.lora_A) > 0]
    expected = expected_trainable(cfg)
    print(f"trainable {trainable:,} | hand count {expected:,} | {'match' if trainable == expected else 'MISMATCH'} | "
          f"{len(wrapped)} layers wrapped, {sum('.visual.' in n for n in wrapped)} in the vision tower", flush=True)

    bf16 = is_bf16_supported()
    args = training_args(cfg, name, out, steps, precision="bf16" if bf16 else "fp16", push=push, report_to=report_to)
    probe_path = out / "probes.jsonl"
    probe_path.unlink(missing_ok=True)
    trainer = Trainer(
        model=model, args=args, data_collator=PadCollator(tk.pad_token_id),
        train_dataset=enc["train"],
        eval_dataset={k: v for k, v in enc.items() if k != "train"},
        callbacks=[make_probe(tok, cfg["probe_max_new_tokens"], probe_path, tools_for(cfg))],
    )

    torch.cuda.reset_peak_memory_stats()
    t0 = time.time()
    result = trainer.train()
    train_seconds = time.time() - t0
    peak_allocated, peak_reserved = torch.cuda.max_memory_allocated(), torch.cuda.max_memory_reserved()

    trainer.save_model(str(out))  # the final adapter; checkpoints stay in checkpoint-<step>/
    tok.save_pretrained(str(out))
    history = trainer.state.log_history
    (out / "log_history.json").write_text(json.dumps(history, indent=1))
    merged = {}
    for h in history:
        for k in [x for x in h if x.startswith("eval_") and x.endswith("_loss")]:
            if k in h:
                merged.setdefault(h["step"], {})[k] = round(h[k], 4)
    info = {
        "run_name": name, "config": cfg, "plan": steps, "data": data_stats,
        "dataset": {"name": cfg.get("dataset_name"), "revision": cfg.get("dataset_revision"),
                    "path": cfg.get("data_path")},
        "prompt_version": PROMPT_VERSION, "probe_customer": PROBE_CUSTOMER, "probes": PROBES,
        "git": {"commit": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain"))},
        "versions": versions(), "gpu": torch.cuda.get_device_name(0), "precision": "bf16" if bf16 else "fp16",
        "trainable_params": trainable, "hand_count": expected, "wrapped_layers": len(wrapped),
        "memory_gb": {"after_load": round(memory_after_load / 1e9, 2), "peak_allocated": round(peak_allocated / 1e9, 2),
                      "peak_reserved": round(peak_reserved / 1e9, 2)},
        "train_seconds": round(train_seconds), "total_seconds": round(time.time() - t_start),
        "train_loss": round(result.training_loss, 4), "eval_losses": merged,
    }
    (out / "run_info.json").write_text(json.dumps(info, indent=1))
    print(json.dumps({k: info[k] for k in ("memory_gb", "train_seconds", "train_loss", "trainable_params")}), flush=True)
    if push:
        trainer.push_to_hub(commit_message=f"{name}: final adapter after {steps['steps']} steps")
    return out


def publish_checkpoint(checkpoint_dir, repo_id, note):
    """Uploads one checkpoint's adapter to the root of the run's Hub repo, when an earlier step reads better."""
    from huggingface_hub import HfApi

    keep = ["adapter_model.safetensors", "adapter_config.json", "README.md", "*.json", "*.jinja", "*.txt"]
    skip = ["optimizer.pt", "scheduler.pt", "rng_state*.pth", "trainer_state.json", "training_args.bin"]
    HfApi().upload_folder(folder_path=str(checkpoint_dir), repo_id=repo_id, allow_patterns=keep,
                          ignore_patterns=skip, commit_message=note)


# ---------------------------------------------------------------- dry run

def dry_run(cfg):
    """Everything up to loading the model, on a CPU: data, masks, padding, the step plan and the run name."""
    from transformers import AutoTokenizer

    ref = AutoTokenizer.from_pretrained(REFERENCE_TOKENIZER)
    raw, enc, stats = prepare(cfg, ref)
    batch = PadCollator(ref.pad_token_id)([enc["train"][i] for i in range(cfg["per_device_train_batch_size"])])
    print(f"run name: {run_name(cfg)}")
    for k, v in stats.items():
        print(f"  {k:<20} {v}")
    print(f"plan: {plan(cfg, len(enc['train']))}")
    print(f"one batch: {', '.join(f'{k} {tuple(v.shape)}' for k, v in batch.items())}; "
          f"{int((batch['labels'] != IGNORE).sum())} trained tokens")
    print("probe prompt (rendered):")
    print(render(ref, [{"role": "system", "content": system_prompt(now(), PROBE_CUSTOMER)},
                       {"role": "user", "content": PROBES[0]}], add_generation_prompt=True))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--set", nargs="*", default=[], metavar="KEY=VALUE", help="override config settings")
    ap.add_argument("--dry-run", action="store_true", help="check data and masks without loading the model")
    ap.add_argument("--push", action="store_true", help="push checkpoints and the final adapter to the Hub")
    ap.add_argument("--report-to", default="none", choices=["none", "wandb", "trackio"])
    a = ap.parse_args()
    cfg = load_config(a.config, a.set)
    if a.dry_run:
        dry_run(cfg)
    else:
        from transformers import set_seed

        set_seed(cfg["seed"])
        train(cfg, push=a.push, report_to=a.report_to)


if __name__ == "__main__":
    main()
