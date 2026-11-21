"""Same question, thinking off vs on: tokens, time and the final answer."""
import time

import torch
from transformers import AutoModelForMultimodalLM, AutoTokenizer

from common import MID, ORDER_STATUS, messages

tok = AutoTokenizer.from_pretrained(MID)
model = AutoModelForMultimodalLM.from_pretrained(MID, dtype=torch.float16).to("mps").eval()
EOS = [tok.convert_tokens_to_ids("<|im_end|>"), tok.convert_tokens_to_ids("<|endoftext|>")]

for tools, label in [(None, "no tools"), ([ORDER_STATUS], "with get_order_status")]:
    for thinking in (False, True):
        prompt = tok.apply_chat_template(messages(), tools=tools, add_generation_prompt=True,
                                         tokenize=False, enable_thinking=thinking)
        ids = tok(prompt, return_tensors="pt").input_ids.to("mps")
        t0 = time.time()
        out = model.generate(ids, max_new_tokens=1500, do_sample=False, eos_token_id=EOS)[0, ids.shape[1]:]
        secs = time.time() - t0
        text = tok.decode(out, skip_special_tokens=False)
        think, _, answer = text.partition("</think>") if "</think>" in text else ("", "", text)
        print(f"\n===== {label} | thinking {'ON' if thinking else 'OFF'} =====")
        print(f"prompt ends with: {prompt[-40:]!r}")
        print(f"total {len(out)} tokens in {secs:.1f}s | thinking part {len(tok(think).input_ids) if think else 0} tokens")
        if think:
            print("--- thinking (first 400 chars) ---\n" + think.strip()[:400] + " ...")
        print("--- answer ---\n" + answer.strip()[:500])
