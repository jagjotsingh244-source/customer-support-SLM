"""The agent loop: ask the model, run the tools it calls, repeat until it answers.

Plain code on purpose, no agent framework: with a 2B model every token in and
out has to be visible. The loop only talks to an OpenAI-compatible chat API, so
the prompted 2B model (vLLM) and a frontier model run through the same code;
switching is a change of base_url and model, nothing else.
"""

import json
import time

from agent.grounding import grounding_issues, tool_contents_before

FALLBACK_REPLY = "Let me connect you with a teammate."
# Tool-call markup the server's parser should have turned into tool_calls (Qwen3.5's qwen3_coder format).
# Seen in the reply text, it means the model tried to call a tool and the parser could not read the call.
TOOL_MARKUP = ("<tool_call>", "<function=")


def has_tool_markup(content: str | None) -> bool:
    return bool(content) and any(m in content for m in TOOL_MARKUP)


def run_turn(client, model, messages, tools, registry, session, max_steps=4, temperature=0.2, sampling=None):
    """Answer the last user message in `messages` (appended to in place).

    Returns (reply, trace). The trace keeps what the scorecard needs: every tool
    call with its raw argument string, whether it parsed, and its result; every
    model call with its latency and token counts; and the reply's grounding
    issues (agent/grounding.py), logged, never fixed. `sampling` adds extra
    request settings (e.g. top_p, presence_penalty) on top of temperature.

    A reply that contains tool-call markup is a format error, not a text reply:
    the model meant to call a tool and the parser could not read it. It is
    counted in trace["format_errors"], never shown to the customer, and the
    turn ends with the hand-off reply.
    """
    trace = {"tool_calls": [], "model_calls": [], "escalated": False, "format_errors": 0}
    for _ in range(max_steps):
        t0 = time.perf_counter()
        r = client.chat.completions.create(model=model, messages=messages, tools=tools,
                                           temperature=temperature, max_tokens=512, **(sampling or {}))
        trace["model_calls"].append({
            "latency_s": round(time.perf_counter() - t0, 3),
            "prompt_tokens": r.usage.prompt_tokens if r.usage else None,
            "completion_tokens": r.usage.completion_tokens if r.usage else None,
            "finish_reason": r.choices[0].finish_reason,
            "served_model": r.model,                # recorded per call: what actually answered
        })
        msg = r.choices[0].message
        if has_tool_markup(msg.content):
            trace["format_errors"] += 1
            trace["model_calls"][-1]["format_error"] = True
            if not msg.tool_calls:                  # nothing parsed: the raw call must not reach the customer
                trace["raw_reply"] = msg.content
                return _hand_off(messages, trace)
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            trace["grounding"] = grounding_issues(msg.content, tool_contents_before(messages, len(messages)))
            return msg.content, trace
        for call in msg.tool_calls:
            raw = call.function.arguments
            try:
                args = json.loads(raw)
                parsed = True
            except (json.JSONDecodeError, TypeError):
                args, parsed = None, False
            try:
                if not parsed:
                    raise ValueError("arguments are not valid JSON")
                result = registry[call.function.name](session=session, **args)
            except Exception as e:                  # v0: record, don't fix
                result = {"error": type(e).__name__, "detail": str(e)[:200]}
            if call.function.name == "escalate_to_human":
                trace["escalated"] = True
            trace["tool_calls"].append({"name": call.function.name, "args": raw, "parsed": parsed,
                                        "result": result})
            # ensure_ascii=False: the model reads "1–3 days" and "₹49", not "1\u20133" and "\u20b949".
            messages.append({"role": "tool", "tool_call_id": call.id,
                             "content": json.dumps(result, default=str, ensure_ascii=False)})
    return _hand_off(messages, trace)               # ran out of steps


def _hand_off(messages, trace):
    trace["escalated"] = True
    trace["grounding"] = []                         # the fixed fallback states no facts
    messages.append({"role": "assistant", "content": FALLBACK_REPLY})
    return FALLBACK_REPLY, trace
