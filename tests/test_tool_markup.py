"""A tool call the parser could not read is counted as a format error and never reaches the customer.

    uv run --group dev pytest tests/test_tool_markup.py
"""

import json
import sys
from pathlib import Path

from openai.types.chat import ChatCompletion

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent.loop import FALLBACK_REPLY, has_tool_markup, run_turn  # noqa: E402

RAW_CALL = "<tool_call>\n<function=get_tracking>\n<parameter=order_id>\n11904\n</parameter>\n</function>\n</tool_call>"


def completion(content=None, calls=None) -> ChatCompletion:
    return ChatCompletion.model_validate({
        "id": "x", "object": "chat.completion", "created": 0, "model": "m",
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        "choices": [{"index": 0, "finish_reason": "tool_calls" if calls else "stop",
                     "message": {"role": "assistant", "content": content, "tool_calls": calls}}]})


class Scripted:
    """Answers each model call with the next prepared completion."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.chat = self
        self.completions = self

    def create(self, **_):
        return self.replies.pop(0)


def tracking(session, order_id):
    return {"order_id": order_id, "shipped": True}


def turn(client):
    messages = [{"role": "system", "content": "s"}, {"role": "user", "content": "Where is my order 11904?"}]
    reply, trace = run_turn(client, "m", messages, tools=[], registry={"get_tracking": tracking}, session=None)
    return reply, trace, messages


def test_markup_detection():
    assert has_tool_markup(RAW_CALL)
    assert has_tool_markup("Let me check. <function=get_tracking>")      # unclosed, no wrapper
    assert not has_tool_markup("Your order 11904 is at the Nagpur hub.")
    assert not has_tool_markup(None) and not has_tool_markup("")


def test_parsed_call_is_not_a_format_error():
    call = {"id": "c0", "type": "function", "function": {"name": "get_tracking", "arguments": '{"order_id": 11904}'}}
    reply, trace, _ = turn(Scripted(completion(calls=[call]), completion("It is at the Nagpur hub.")))
    assert reply == "It is at the Nagpur hub."
    assert trace["format_errors"] == 0 and not trace["escalated"]
    assert trace["tool_calls"][0]["result"] == {"order_id": 11904, "shipped": True}


def test_call_left_as_text_is_a_format_error_not_a_reply():
    reply, trace, messages = turn(Scripted(completion(RAW_CALL)))
    assert reply == FALLBACK_REPLY and trace["escalated"]
    assert trace["format_errors"] == 1 and trace["model_calls"][0]["format_error"]
    assert trace["raw_reply"] == RAW_CALL                                  # kept for the trace
    assert not any(has_tool_markup(m.get("content")) for m in messages)    # not in the history the customer sees
    assert trace["tool_calls"] == []


def test_markup_next_to_a_parsed_call_is_counted_and_the_call_still_runs():
    call = {"id": "c0", "type": "function", "function": {"name": "get_tracking", "arguments": '{"order_id": 11904}'}}
    reply, trace, _ = turn(Scripted(completion("<function=get_tracking>", calls=[call]), completion("Shipped.")))
    assert reply == "Shipped." and trace["format_errors"] == 1 and len(trace["tool_calls"]) == 1


def test_mac_client_leaves_a_malformed_call_in_content():
    """The in-process client parses like vLLM's qwen3_coder: no closing </tool_call>, no parsed call."""
    import pytest
    pytest.importorskip("torch")
    from agent.local_client import parse_tool_calls

    tools = [{"type": "function", "function": {"name": "get_tracking",
              "parameters": {"type": "object", "properties": {"order_id": {"type": "integer"}}}}}]
    content, calls = parse_tool_calls(RAW_CALL, tools)
    assert content is None and json.loads(calls[0]["function"]["arguments"]) == {"order_id": 11904}
    broken = RAW_CALL.removesuffix("</tool_call>")
    content, calls = parse_tool_calls(broken, tools)
    assert calls == [] and has_tool_markup(content)
