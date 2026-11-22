"""The loss mask trains Nova's reply and nothing else.

Runs on a laptop with only the tokenizer:  uv run --group local-model --group dev pytest tests/test_masking.py
"""

import sys
from pathlib import Path

import pytest
from transformers import AutoTokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from training.masking import END, IGNORE, INSTRUCTION_PART, RESPONSE_PART, tokenize  # noqa: E402

SYSTEM = "You are Nova, the support assistant for NimbusCart, an online store in India."
USER = "i need help cancelling puchase 12350"
REPLY = "I'd be happy to look into cancelling that for you. Would you like me to check your order?"


@pytest.fixture(scope="module")
def tok():
    return AutoTokenizer.from_pretrained("Qwen/Qwen3.5-2B")


def example(*turns):
    msgs = [{"role": "system", "content": SYSTEM}]
    for i, t in enumerate(turns):
        msgs.append({"role": "user" if i % 2 == 0 else "assistant", "content": t})
    return msgs


def trained_text(enc, tok):
    return tok.decode([t for t, l in zip(enc["input_ids"], enc["labels"]) if l != IGNORE])


def test_markers_match_the_rendered_template(tok):
    text = tok.apply_chat_template(example(USER, REPLY), tokenize=False)
    assert text.count(INSTRUCTION_PART) == 1
    assert text.count(RESPONSE_PART) == 1
    # The serving prompt ends with exactly the marker, so training starts where generation starts.
    prompt = tok.apply_chat_template(example(USER), tokenize=False, add_generation_prompt=True)
    assert prompt.endswith(RESPONSE_PART)


def test_only_the_reply_is_trained(tok):
    enc = tokenize(example(USER, REPLY), tok)
    assert trained_text(enc, tok) == REPLY + END
    # Every token before the reply, the system prompt and the customer message included, is -100.
    first = next(i for i, l in enumerate(enc["labels"]) if l != IGNORE)
    assert all(l == IGNORE for l in enc["labels"][:first])
    assert tok.decode(enc["input_ids"][:first]).endswith(RESPONSE_PART)


def test_labels_equal_input_ids_where_trained(tok):
    enc = tokenize(example(USER, REPLY), tok)
    assert len(enc["labels"]) == len(enc["input_ids"])
    assert all(l in (IGNORE, t) for t, l in zip(enc["input_ids"], enc["labels"]))


def test_only_the_last_reply_is_trained_in_a_longer_conversation(tok):
    # Earlier replies render without the think block, as history does at serving time: context, not targets.
    last = "Would you like me to check the refund?"
    enc = tokenize(example(USER, REPLY, "thanks, and the refund?", last), tok)
    assert trained_text(enc, tok) == last + END


def test_a_conversation_must_end_with_the_reply(tok):
    with pytest.raises(ValueError):
        tokenize(example(USER), tok)


def test_unsloth_finds_the_marker_by_token_ids(tok):
    # Unsloth's train_on_responses_only tokenises the marker on its own and searches for those ids.
    # If the marker tokenised differently inside the conversation, every label would become -100.
    marker = tok(RESPONSE_PART, add_special_tokens=False)["input_ids"]
    ids = tok(tok.apply_chat_template(example(USER, REPLY), tokenize=False), add_special_tokens=False)["input_ids"]
    assert any(ids[i:i + len(marker)] == marker for i in range(len(ids) - len(marker) + 1))
    user_marker = tok(INSTRUCTION_PART, add_special_tokens=False)["input_ids"]
    assert any(ids[i:i + len(user_marker)] == user_marker for i in range(len(ids) - len(user_marker) + 1))
