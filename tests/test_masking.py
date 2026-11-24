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


# Tool calls, rendered with Nova's tool schemas as the second fine-tune trains them -----------------------------

def two_call_step(target):
    """A step after two tool calls in the same turn, ending with `target`; results from the seeded world."""
    import json
    results = json.loads((Path(__file__).parent / "fixtures" / "long_chat_results.json").read_text())["results"]

    def call(i, name, args):
        return {"role": "assistant", "content": "", "tool_calls": [
            {"id": f"c{i}", "type": "function", "function": {"name": name, "arguments": args}}]}
    return [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": "where is my webcam? and did the tote bag order arrive"},
            call(1, "get_tracking", {"order_id": 11904}),
            {"role": "tool", "tool_call_id": "c1", "content": json.dumps(results["get_tracking:11904"])},
            call(2, "get_order_status", {"order_id": 10689}),
            {"role": "tool", "tool_call_id": "c2", "content": json.dumps(results["get_order_status:10689"])},
            target]


@pytest.fixture(scope="module")
def tools():
    pytest.importorskip("pydantic")
    pytest.importorskip("psycopg")              # the tokenizer-only CI job skips these; the state job runs them
    from agent.tools_v2 import TOOLS
    return TOOLS


def test_a_tool_call_target_after_two_calls_trains_only_that_call(tok, tools):
    target = {"role": "assistant", "content": "", "tool_calls": [{"id": "c3", "type": "function", "function": {
        "name": "escalate_to_human", "arguments": {"reason": "other", "summary": "Customer asked for a person."}}}]}
    msgs = two_call_step(target)
    text = tok.apply_chat_template(msgs, tools=tools, tokenize=False)
    assert text.count(RESPONSE_PART) == 3                  # the two earlier calls render with the marker too
    trained = trained_text(tokenize(msgs, tok, tools=tools), tok)
    assert trained.startswith("<tool_call>\n<function=escalate_to_human>") and trained.endswith("</tool_call>" + END)
    assert "get_tracking" not in trained and "get_order_status" not in trained          # earlier calls: context
    assert "tool_response" not in trained and "SS70001836" not in trained                # results: never trained


def test_a_reply_after_two_calls_trains_only_the_reply(tok, tools):
    reply = "Order 11904, your 1080p webcam, is with SwiftShip; order 10689 was delivered."
    msgs = two_call_step({"role": "assistant", "content": reply})
    enc = tokenize(msgs, tok, tools=tools)
    assert trained_text(enc, tok) == reply + END
    # Every trained token is one the model generates: the labels equal the inputs where trained.
    assert all(l in (IGNORE, t) for t, l in zip(enc["input_ids"], enc["labels"]))
