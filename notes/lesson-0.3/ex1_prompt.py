"""Exercise 1: print the prompt the model really sees, find the special tokens, count tokens."""
import re
from collections import Counter

from transformers import AutoTokenizer

from common import MID, NOVA_TOOLS, ORDER_STATUS, messages

tok = AutoTokenizer.from_pretrained(MID)


def render(tools=None, gen=True, msgs=None):
    return tok.apply_chat_template(msgs or messages(), tools=tools, add_generation_prompt=gen, tokenize=False)


def n_tokens(text):
    return len(tok(text).input_ids)


plain = render()
one_tool = render([ORDER_STATUS])
all_tools = render(NOVA_TOOLS)

print("=" * 30, "WITHOUT TOOLS", "=" * 30)
print(plain)
print("=" * 30, "WITH get_order_status", "=" * 30)
print(one_tool)

print("=" * 30, "SPECIAL TOKENS", "=" * 30)
for t, c in Counter(re.findall(r"<\|[^|]+\|>|<[a-z_]+>|</[a-z_]+>", one_tool)).items():
    print(f"{t:20s} x{c}")

print("=" * 30, "TOKEN COUNTS", "=" * 30)
sys_only = plain.split("<|im_start|>user")[0]          # the template refuses to render without a user turn
print("system turn only (no tools):        ", n_tokens(sys_only))
print("assistant cue incl. empty think:    ", n_tokens(plain.split("Hi, where is my order 4417?<|im_end|>\n")[1]))
print("=" * 30, "ONE TOKEN OR MANY?", "=" * 30)
for t in ["<|im_start|>", "<|im_end|>", "<think>", "</think>", "<tool_call>", "</tool_call>",
          "<tools>", "<function=", "<parameter=", "<|endoftext|>"]:
    ids = tok(t, add_special_tokens=False).input_ids
    print(f"{t:16s} -> {len(ids)} token(s) {ids}")
print("whole prompt, no tools:             ", n_tokens(plain))
print("whole prompt, get_order_status only:", n_tokens(one_tool), f"(tool block = {n_tokens(one_tool) - n_tokens(plain)})")
print("whole prompt, all 6 draft tools:    ", n_tokens(all_tools), f"(tool block = {n_tokens(all_tools) - n_tokens(plain)})")
print("words in the user message:", len(messages()[1]["content"].split()),
      "| tokens:", n_tokens(messages()[1]["content"]))
print("pieces:", tok.tokenize(messages()[1]["content"]))
print("ids:   ", tok(messages()[1]["content"]).input_ids)
print("vocab size:", len(tok))
