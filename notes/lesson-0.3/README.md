# Lesson 0.3: how Qwen3.5-2B produces a reply

Run on a MacBook (MPS, float16), Transformers 5.23.0, PyTorch 2.15.0, 2026-11-20.
Not yet run on a T4: that is risk test 1, done in Lesson 0.4.

Scripts (run from this folder with a Python that has `transformers>=5` and `torch`):
`ex1_prompt.py` (exercise 1), `ex2to5.py [2|3|4|5]` (exercises 2–5), `think_compare.py` (thinking on vs off).
`raw_tool_call.txt` is the exact prompt and raw tool-call output Module 6 must parse.

## Findings

1. **Thinking is turned off by the prompt, not by a setting.** With `enable_thinking=False` (the default)
   the template ends the prompt with an empty `<think>\n\n</think>\n\n` block. Training data in Module 3
   must contain the same empty block, or training and serving formats differ.
2. **Wrong stop token in the model config.** The tokenizer's eos is `<|im_end|>` (248046) but
   `config.json` sets `eos_token_id` to `<|endoftext|>` (248044), and the repo has no
   `generation_config.json`. So `model.generate` runs past the end of the turn unless given
   `eos_token_id=[248046, 248044]`. Check the stop tokens again when serving with vLLM (Module 10).
3. **Tool-call format is XML-style, not JSON:**
   `<tool_call>` `<function=NAME>` `<parameter=NAME>` value `</parameter>` `</function>` `</tool_call>`.
   `<tool_call>`, `</tool_call>`, `<think>`, `</think>`, `<|im_start|>`, `<|im_end|>` are single tokens;
   `<function=` and `<parameter=` are ordinary text (3 tokens each), so the model can misspell them.
4. **The base model already calls the tool** for "Where is my order 4417?" with the right name and
   argument, greedy, no fine-tuning. Fine-tuning is still needed for the harder cases (no order number,
   several orders, when not to call).
5. **Token costs:** user message "Hi, where is my order 4417?" = 12 tokens (each digit of 4417 is its own
   token). Short system prompt + user message = 39. One tool adds 261; the 6 draft tools add 656
   (about 180 fixed + about 80 per tool). Vocabulary: 248,077 tokens.
6. **Without the template the lesson's failure looks different here:** the raw string did not continue
   the customer's message; the model jumped into a long thinking block instead. With the template but
   `add_generation_prompt=False`, the model wrote the assistant cue itself, without the empty think
   block, and also started thinking. Both are wrong for Nova.
7. **Hand-written greedy loop = `model.generate(do_sample=False)`**, token for token (31 tokens), once
   both stop on `<|im_end|>`. The loop without a KV cache took 17.5 s against 2.1 s for `generate`.
8. **Sampling** (5 runs each, replies up to 600 tokens, all finished on their own):
   - temperature 0.2: lengths 101–129 tokens (102, 129, 101, 123, 120); all five ask for more details.
   - model card (temperature 1.0, top_p 1.0, top_k 20): lengths 106–284 tokens (185, 106, 284, 208, 205),
     almost 3x spread; three of five claimed "I don't have access to your order", one used an emoji.

   Higher temperature changes length and content, and here it made the model refuse more often.
   Support needs the low end; Module 2 decides the exact value. `presence_penalty=2.0` from the card is a
   vLLM/OpenAI-API setting, not a `generate` argument; Lesson 0.4's notebook repeats this comparison through
   vLLM with it.

## Thinking on vs off (greedy, same question)

| Case | Thinking | Tokens | Time (Mac) | Result |
|---|---|---|---|---|
| No tools | Off | 128 | 6.0 s | Friendly answer asking for details |
| No tools | On | 1,500 (cap hit; 1,449 thinking) | 68.2 s | Answer cut off at the cap |
| With `get_order_status` | Off | 31 | 1.9 s | Correct tool call |
| With `get_order_status` | On | 109 (76 thinking) | 5.4 s | Same tool call |

Conclusion: for Nova's lookup-style turns, thinking adds 3–11x the tokens and time with no better answer.
Nova stays non-thinking.
