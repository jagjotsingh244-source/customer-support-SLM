"""Training entry point for the disconnect drill.

All training logic lives here, versioned in Git. The notebook only calls run().

Run from the repo root:
    python training/train.py --config training/configs/drill.yaml
    python training/train.py --config training/configs/drill.yaml --resume
"""

import argparse
import os
import time

import torch
import yaml
from datasets import load_dataset
from huggingface_hub import snapshot_download
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainerCallback, set_seed
from trl import SFTConfig, SFTTrainer


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def format_row(row):
    # Drill only: plain text, no chat template. notes/generation-experiments/ explains why real runs
    # must use the model's chat template instead.
    return {"text": f"Customer: {row['instruction']}\nAgent: {row['response']}"}


class StepReporter(TrainerCallback):
    """Prints the two lines the drill is about: where training starts, and each save."""

    def on_train_begin(self, args, state, control, **kwargs):
        print(f">>> Training starts at step {state.global_step} of {state.max_steps}")

    def on_save(self, args, state, control, **kwargs):
        print(f">>> Saved checkpoint at step {state.global_step}")


class DrillPause(TrainerCallback):
    """Drill only: waits at one step so there is time to delete the runtime by hand."""

    def __init__(self, step, minutes):
        self.step, self.minutes = step, minutes

    def on_step_end(self, args, state, control, **kwargs):
        if state.global_step == self.step:
            print(
                f">>> PAUSED at step {self.step}. Delete the runtime now "
                f"(Runtime -> Disconnect and delete runtime). "
                f"Training continues by itself in {self.minutes} minutes."
            )
            time.sleep(self.minutes * 60)


def run(cfg, resume=False):
    tok = AutoTokenizer.from_pretrained(cfg["model_name"])
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(cfg["model_name"])

    ds = load_dataset(cfg["dataset_name"], split="train")
    ds = ds.shuffle(seed=cfg["seed"]).select(range(cfg["num_rows"]))
    ds = ds.map(format_row, remove_columns=ds.column_names)

    args = SFTConfig(
        output_dir=cfg["output_dir"],
        seed=cfg["seed"],
        max_steps=cfg["max_steps"],
        per_device_train_batch_size=cfg["per_device_train_batch_size"],
        learning_rate=cfg["learning_rate"],
        logging_steps=cfg["logging_steps"],
        save_steps=cfg["save_steps"],
        save_total_limit=cfg["save_total_limit"],
        fp16=torch.cuda.is_available(),  # the T4 has no bf16
        report_to="none",
        push_to_hub=cfg["push_to_hub"],
        hub_model_id=cfg.get("hub_model_id"),
        hub_private_repo=True,
        hub_strategy="checkpoint",  # every save also goes to <repo>/last-checkpoint
    )
    lora = LoraConfig(
        r=cfg["lora_r"],
        lora_alpha=cfg["lora_alpha"],
        target_modules="all-linear",
        task_type="CAUSAL_LM",
    )
    callbacks = [StepReporter()]
    if cfg.get("pause_at_step") and not resume:  # a resumed run must not pause again
        callbacks.append(DrillPause(cfg["pause_at_step"], cfg.get("pause_minutes", 15)))

    trainer = SFTTrainer(
        model=model,
        args=args,
        train_dataset=ds,
        processing_class=tok,
        peft_config=lora,
        callbacks=callbacks,
    )

    checkpoint = None
    if resume:
        # After a disconnect the local disk is empty: pull the last save from the Hub.
        checkpoint = os.path.join(cfg["output_dir"], "last-checkpoint")
        if cfg["push_to_hub"]:
            snapshot_download(
                cfg["hub_model_id"],
                allow_patterns="last-checkpoint/*",
                local_dir=cfg["output_dir"],
            )
        if not os.path.isdir(checkpoint):
            checkpoint = True  # no Hub copy: resume from the newest local checkpoint-N

    trainer.train(resume_from_checkpoint=checkpoint)
    trainer.save_model()
    if cfg["push_to_hub"]:
        trainer.push_to_hub()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--resume", action="store_true")
    a = parser.parse_args()
    cfg = load_config(a.config)
    set_seed(cfg["seed"])
    run(cfg, resume=a.resume)


if __name__ == "__main__":
    main()
