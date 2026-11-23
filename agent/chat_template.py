"""OpenAI-style chat history -> the shape Qwen3.5's chat template expects. No model, no torch: used by the
in-process client (agent/local_client.py) and by prompt token counting (agent/state.py)."""

import json


def for_template(messages: list[dict]) -> list[dict]:
    """OpenAI-style history -> what the Qwen template expects (tool-call arguments as a mapping)."""
    out = []
    for m in messages:
        m = {k: v for k, v in m.items() if k in ("role", "content", "tool_calls", "tool_call_id")}
        if m.get("content") is None:
            m["content"] = ""
        if m.get("tool_calls"):
            m["tool_calls"] = [{"type": "function", "id": c.get("id"), "function": {
                "name": c["function"]["name"], "arguments": _arguments(c["function"]["arguments"])}}
                for c in m["tool_calls"]]
        out.append(m)
    return out


def _arguments(raw: str | None) -> dict:
    """The template iterates over the arguments, so they must be a mapping. Arguments that are not a JSON
    object (a malformed call the tools refused) are kept as text under one key rather than crashing."""
    try:
        args = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {"arguments": raw}
    return args if isinstance(args, dict) else {"arguments": raw}
