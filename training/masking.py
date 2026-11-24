"""Response-only loss for Qwen3.5 chat data: only Nova's own words are trained.

Every token still goes into the model, but the loss counts only the assistant's reply. Labels for everything
else (system prompt, customer turns, the template's markers) are set to -100, which the loss ignores.

Where Nova's reply starts, exactly. Qwen3.5's template renders every assistant turn as

    <|im_start|>assistant\\n<think>\\n\\n</think>\\n\\n{reply}<|im_end|>\\n

with thinking off. At serving time the generation prompt already ends with "<think>\\n\\n</think>\\n\\n", so the
model never writes that block itself. The trained part therefore starts after it and runs through <|im_end|>
(so the model learns to stop); the newline after <|im_end|> is not trained. RESPONSE_PART below is that marker;
tests/test_masking.py fails if the template ever renders something else.

Only the last assistant turn is trained. The template drops the think block from earlier assistant turns
("<|im_start|>assistant\\nB1<|im_end|>"), exactly as it does for the history at serving time, so only the last
turn has the shape the model actually generates. Earlier turns are context; to train them, make one example per
turn (the conversation cut after that turn).

Tool calls (the second fine-tune). Rendered with the tool schemas, a step in the middle of a turn holds the turn's
earlier tool calls after the last customer message, and the template gives those the think block too: a step
after two calls renders three spans that start with RESPONSE_PART. Only the last one is the step's target; the
earlier calls are context here and each is the target of its own step. tokenize() therefore trains the last span
only. Unsloth's train_on_responses_only would train all three, so tool-call data uses tokenize(). Tool results
render inside a user block (<|im_start|>user\n<tool_response>...), so they are never inside a trained span.

Two ways to use it, both checked by the same test:
- Unsloth: train_on_responses_only(trainer, instruction_part=INSTRUCTION_PART, response_part=RESPONSE_PART).
  Unsloth finds the markers by their token ids, so the test also checks the marker tokenises the same way on its
  own as inside a rendered conversation.
- Plain TRL: tokenize(messages, tok) returns input_ids and labels, already masked.
"""

IGNORE = -100
INSTRUCTION_PART = "<|im_start|>user\n"
RESPONSE_PART = "<|im_start|>assistant\n<think>\n\n</think>\n\n"
END = "<|im_end|>"


def assistant_spans(text: str) -> list[tuple[int, int]]:
    """Character spans [start, end) of each trained part: the reply text plus its closing <|im_end|>."""
    spans, pos = [], 0
    while (start := text.find(RESPONSE_PART, pos)) != -1:
        start += len(RESPONSE_PART)
        end = text.find(END, start)
        if end == -1:
            raise ValueError("assistant turn has no closing <|im_end|>")
        spans.append((start, end + len(END)))
        pos = end
    return spans


def tokenize(messages: list[dict], tok, max_length: int | None = None, tools: list[dict] | None = None) -> dict:
    """Render messages with the model's own chat template (and the tool schemas, if given) and label only the
    last assistant message: a reply or a tool call."""
    text = tok.apply_chat_template(messages, tools=tools, tokenize=False)
    if messages[-1]["role"] != "assistant":
        raise ValueError("the last message must be the assistant reply to train")
    spans = assistant_spans(text)
    if not spans or not text.rstrip().endswith(END):
        raise ValueError("no trainable reply in the render: RESPONSE_PART does not match the chat template")
    spans = spans[-1:]
    enc = tok(text, add_special_tokens=False, return_offsets_mapping=True)
    labels = []
    for tid, (a, b) in zip(enc["input_ids"], enc["offset_mapping"]):
        inside = any(s <= a and b <= e for s, e in spans)
        labels.append(tid if inside else IGNORE)
    out = {"input_ids": enc["input_ids"], "attention_mask": enc["attention_mask"], "labels": labels}
    if max_length is not None:
        out = {k: v[:max_length] for k, v in out.items()}
    return out
