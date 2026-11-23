---
library_name: peft
license: apache-2.0
base_model: unsloth/Qwen3.5-2B
tags:
- base_model:adapter:unsloth/Qwen3.5-2B
- lora
- transformers
- unsloth
pipeline_tag: text-generation
model-index:
- name: sft1-r16-lr2e-4-bitext_v1
  results: []
---

<!-- This model card has been generated automatically according to the information the Trainer had access to. You
should probably proofread and complete it, then remove this comment. -->

# sft1-r16-lr2e-4-bitext_v1

This model is a fine-tuned version of [unsloth/Qwen3.5-2B](https://huggingface.co/unsloth/Qwen3.5-2B) on an unknown dataset.

## Model description

More information needed

## Intended uses & limitations

More information needed

## Training and evaluation data

More information needed

## Training procedure

### Training hyperparameters

The following hyperparameters were used during training:
- learning_rate: 0.0002
- train_batch_size: 2
- eval_batch_size: 8
- seed: 3407
- gradient_accumulation_steps: 8
- total_train_batch_size: 16
- optimizer: Use OptimizerNames.ADAMW_8BIT with betas=(0.9,0.999) and epsilon=1e-08 and optimizer_args=No additional optimizer arguments
- lr_scheduler_type: cosine
- lr_scheduler_warmup_steps: 14
- num_epochs: 1
- mixed_precision_training: Native AMP

### Training results



### Framework versions

- PEFT 0.21.2
- Transformers 5.17.0
- Pytorch 2.11.0+cu130
- Datasets 4.8.5
- Tokenizers 0.23.3