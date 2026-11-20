"""Exercises 2-5 with Qwen3.5-2B on the Mac (MPS, float16 like the T4)."""
import json
import sys
import time

import torch
import transformers
from transformers import AutoTokenizer

from common import MID, ORDER_STATUS, USER, messages

try:
    from transformers import AutoModelForMultimodalLM as ModelClass
except ImportError:
    from transformers import AutoModelForImageTextToText as ModelClass

which = set(sys.argv[1:]) or {"2", "3", "4", "5"}
device = "mps" if torch.backends.mps.is_available() else "cpu"
tok = AutoTokenizer.from_pretrained(MID)
t0 = time.time()
model = ModelClass.from_pretrained(MID, dtype=torch.float16).to(device).eval()
print(f"[{ModelClass.__name__} loaded on {device} in {time.time() - t0:.0f}s]")
STOP = tok.convert_tokens_to_ids("<|im_end|>")
# config.json says eos = <|endoftext|>, but a chat turn ends with <|im_end|>: stop on both
EOS = [STOP, tok.convert_tokens_to_ids("<|endoftext|>")]
results = {}


def ids_of(text):
    return tok(text, return_tensors="pt").input_ids.to(device)


def render(tools=None, gen=True):
    return tok.apply_chat_template(messages(), tools=tools, add_generation_prompt=gen, tokenize=False)


def greedy(text, n=60):
    ids = ids_of(text)
    out = model.generate(ids, max_new_tokens=n, do_sample=False, eos_token_id=EOS)
    return tok.decode(out[0, ids.shape[1]:], skip_special_tokens=False)


def show(title, text):
    print(f"\n----- {title} -----\n{text}")


if "2" in which:
    print("\n" + "=" * 25, "EXERCISE 2: raw vs template vs no cue", "=" * 25)
    cases = {
        "a) raw string, no template": USER,
        "b) template + add_generation_prompt=True": render(),
        "c) template + add_generation_prompt=False": render(gen=False),
    }
    for title, prompt in cases.items():
        if title.startswith("c"):
            show("prompt ends with", repr(prompt[-60:]))
        reply = greedy(prompt)
        show(title, reply)
        results[title] = reply

if "3" in which:
    print("\n" + "=" * 25, "EXERCISE 3: hand-written loop vs generate", "=" * 25)
    prompt_ids = ids_of(render([ORDER_STATUS]))
    ids = prompt_ids
    t0 = time.time()
    for _ in range(80):
        with torch.no_grad():
            logits = model(input_ids=ids).logits[:, -1, :]
        nxt = logits.argmax(dim=-1, keepdim=True)
        ids = torch.cat([ids, nxt], dim=-1)
        if nxt.item() == STOP:
            break
    loop_time = time.time() - t0
    mine = ids[0, prompt_ids.shape[1]:].tolist()
    t0 = time.time()
    ref = model.generate(prompt_ids, max_new_tokens=80, do_sample=False, eos_token_id=EOS)[0, prompt_ids.shape[1]:].tolist()
    gen_time = time.time() - t0
    same = mine == ref
    first_diff = next((i for i, (a, b) in enumerate(zip(mine, ref)) if a != b), None)
    show("my loop", tok.decode(mine, skip_special_tokens=False))
    show("model.generate", tok.decode(ref, skip_special_tokens=False))
    print(f"\nidentical: {same} | my loop {len(mine)} tokens in {loop_time:.1f}s "
          f"| generate {len(ref)} tokens in {gen_time:.1f}s | first difference at: {first_diff}")
    results["ex3"] = {"identical": same, "loop_s": loop_time, "generate_s": gen_time,
                      "loop_tokens": len(mine), "first_diff": first_diff}

if "4" in which:
    print("\n" + "=" * 25, "EXERCISE 4: sampling", "=" * 25)
    ids = ids_of(render())
    settings = {
        "temperature 0.2": dict(temperature=0.2, top_p=1.0, top_k=0),
        "model card (temp 1.0, top_p 1.0, top_k 20)": dict(temperature=1.0, top_p=1.0, top_k=20),
    }
    for name, kw in settings.items():
        print(f"\n### {name}")
        outs = []
        for seed in range(5):
            torch.manual_seed(seed)
            out = model.generate(ids, max_new_tokens=60, do_sample=True, eos_token_id=EOS, **kw)[0, ids.shape[1]:]
            text = tok.decode(out, skip_special_tokens=True).strip().replace("\n", " ")
            outs.append(text)
            print(f"  run {seed + 1} ({len(out)} tokens): {text}")
        results[name] = outs

if "5" in which:
    print("\n" + "=" * 25, "EXERCISE 5: does the base model call the tool?", "=" * 25)
    prompt = render([ORDER_STATUS])
    raw = greedy(prompt, n=120)
    show("raw output, special tokens kept", raw)
    results["ex5_prompt"] = prompt
    results["ex5_raw"] = raw

json.dump(results, open("results_" + "".join(sorted(which)) + ".json", "w"), indent=1)
print(f"\n[transformers {transformers.__version__}, torch {torch.__version__}]")
