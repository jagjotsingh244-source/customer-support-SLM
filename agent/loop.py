"""The agent loop: ask the model, run the tools it calls, repeat until it answers.

Plain code on purpose, no agent framework: with a 2B model every token in and
out has to be visible. The loop only talks to an OpenAI-compatible chat API, so
the prompted 2B model (vLLM) and a frontier model run through the same code;
switching is a change of base_url and model, nothing else.
"""

import json
import logging
import time
import uuid
from contextlib import contextmanager

from agent.grounding import grounding_issues, tool_contents_before
from agent.privacy import redact
from agent.state import MAX_CALLS_PER_STEP, parse_args

log = logging.getLogger("nova.tools")
FALLBACK_REPLY = "Let me connect you with a teammate."
SKIPPED = {"error": "skipped", "detail": "Only two tool calls run at a time. Call one tool, read its result, then the next."}
# Tool-call markup the server's parser should have turned into tool_calls (Qwen3.5's qwen3_coder format).
# Seen in the reply text, it means the model tried to call a tool and the parser could not read the call.
TOOL_MARKUP = ("<tool_call>", "<function=")


def has_tool_markup(content: str | None) -> bool:
    return bool(content) and any(m in content for m in TOOL_MARKUP)


def unusable(msg) -> bool:
    """A model pass that produced nothing the loop can use: a call left as text, or no text and no call.

    The second happens when the parser swallows a call it was told not to return: vLLM with the
    parser on and tool_choice="none" drops the model's 31-token call and returns an empty message
    (notes/tool-call-anatomy/vllm_with_parser.json).
    """
    return has_tool_markup(msg.content) or (not msg.tool_calls and not (msg.content or "").strip())


class _NoStep:
    def update(self, **_):
        return self


@contextmanager
def _no_span(*_args, **_kw):
    yield _NoStep()


def compact(result, width: int = 80):
    """A tool result as a trace keeps it: top-level fields, long text cut, lists and nested objects counted. Enough
    to see what came back without copying database rows into the tracer."""
    def one(v):
        if isinstance(v, str):
            return v if len(v) <= width else v[:width] + "…"
        if isinstance(v, list):
            return f"[{len(v)} items]"
        if isinstance(v, dict):
            return "{" + ", ".join(list(v)[:8]) + "}"
        return v if isinstance(v, (int, float, bool)) or v is None else str(v)[:width]
    return {k: one(v) for k, v in list(result.items())[:16]} if isinstance(result, dict) else one(result)


def legacy_dispatch(registry: dict):
    """The first tools' calling convention (agent/tools_v0.py, tools_v1.py): a name -> function map, raw
    exceptions recorded as they are. Kept so old runs can be repeated exactly."""
    def call(name, raw, session, attempts):
        try:
            args = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {"error": "ValueError", "detail": "arguments are not valid JSON"}
        try:
            return registry[name](session=session, **args)
        except Exception as e:                      # record, don't fix
            return {"error": type(e).__name__, "detail": str(e)[:200]}
    return call


def run_turn(client, model, messages, tools, registry, session, max_steps=4, temperature=0.2, sampling=None,
             trace_id=None, context=None, guard=None, rules=None, on_event=None, spans=None):
    """Answer the last user message in `messages` (appended to in place).

    Returns (reply, trace). The trace keeps what the scorecard needs: every tool
    call with its raw argument string, whether it parsed, and its result; every
    model call with its latency and token counts; and the reply's grounding
    issues (agent/grounding.py), logged, never fixed. `sampling` adds extra
    request settings (e.g. top_p, presence_penalty) on top of temperature.

    `registry` is either a dispatcher, dispatch(name, raw_args, session, attempts) -> result (the typed
    tools' call_tool, which validates and writes errors for the model), or a name -> function map for the
    first tools.

    A reply that contains tool-call markup is a format error, not a text reply:
    the model meant to call a tool and the parser could not read it. So is an
    empty reply with no call. Both are counted in trace["format_errors"], never
    shown to the customer, and the turn ends with the hand-off reply.

    With a `context` (agent/state.py), each request is the system prompt with the
    conversation state appended plus the history that fits the token budget, the
    state is updated from every tool result, and at most two tool calls run per
    step. `messages` always keeps the whole conversation, for the trace. Without
    one, every message is sent, as in the first runs.

    With a `guard` (agent/guardrails.py), the customer's message is checked for obvious attacks (flags are
    logged in trace["input_flags"], the turn goes on as normal), every tool result has instruction-like text
    cut out and is labelled with its source before the model reads it (trace["scrubbed"]), and the reply is
    checked before the customer sees it: links removed, a prompt echo, an action claim no tool result backs,
    or personal data (agent/privacy.py) replaced, tool names reworded (trace["output_guard"], with the
    original).

    With `rules` (agent/escalation.py HandoffRules), the certain hand-offs are made in code: when the
    customer's message asks for a person, raises a high-risk topic or follows two turns without progress, and
    when a tracking result shows no scan for 7+ days (the loop reads the tracking itself for a shipped order the
    model only checked the status of), the loop calls escalate_to_human itself, with a summary
    built from the conversation state (trace["forced_handoff"]), and the model only tells the customer what
    happens next. A hand-off the model asks for gets the same state-built summary, and every hand-off result
    tells the model what to say for the time of day (support hours 9:00-21:00 IST).

    Without either, everything runs as before.

    `on_event(type, data)`, when given, is called with ("status", {"tool", "args"}) just before each tool call
    runs, the model's and the forced ones alike, so a chat page can say "Checking your orders..." while the
    turn is still going. Nothing of the reply is sent this way: the reply leaves only as the return value,
    after every check above. trace["checks_ms"] is how long those reply checks took.

    `spans(name, **attrs)`, when given, opens one step of the turn's trace (api/tracing.py) as a context manager:
    each model call (prompt size, tokens, what it asked for), each tool call (arguments, a compact result, errors),
    the help-center search inside it (through session.span), the hand-off rules that act on their own, the input
    check and the reply checks. Without it nothing is recorded and nothing changes.
    """
    trace = {"trace_id": trace_id or uuid.uuid4().hex[:8], "tool_calls": [], "model_calls": [], "escalated": False,
             "format_errors": 0}
    dispatch = registry if callable(registry) else legacy_dispatch(registry)
    attempts = {}                                   # failed calls per tool in this turn (agent/tools_v2.call_tool)
    turn = sum(1 for m in messages if m.get("role") == "user")
    user_msg = messages[-1].get("content") or ""
    span = spans or _no_span
    if spans and hasattr(session, "spans"):        # lets the help-center search record its own step
        session.spans = spans

    def run_call(call_id, name, raw, forced=False):
        """Run one tool call and append its result; the same path for the model's calls and forced ones."""
        if rules and not forced:                    # a forced hand-off already carries the state summary
            raw = rules.rewrite(name, raw)
        try:
            parsed = isinstance(json.loads(raw), dict)
        except (json.JSONDecodeError, TypeError):
            parsed = False
        if on_event:
            on_event("status", {"tool": name, "args": parse_args(raw) or {}})
        args = parse_args(raw)
        with span(f"tool:{name}", as_type="tool", input=args if args is not None else {"unparsed": raw},
                  metadata={"by": "rule" if forced else "model"}) as step:
            t0 = time.perf_counter()
            repeat = rules.repeat_handoff(name) if rules else None
            result = repeat or dispatch(name, raw, session, attempts)
            latency_ms = round(1000 * (time.perf_counter() - t0))
            ok = not (isinstance(result, dict) and "error" in result)
            step.update(output=compact(result), level=None if ok else "ERROR",
                        status_message=None if ok else str(result.get("error")))
        if name == "escalate_to_human" and ok:
            trace["escalated"] = True
        if rules and not repeat:
            rules.observe(name, parse_args(raw), result)
            result = rules.note(result)
        seen = result
        if guard:                                   # the model reads the scrubbed, labelled result
            seen, content, hits = guard.tool_content(name, result)
            if hits:
                trace["scrubbed"].append({"tool": name, "hits": hits})
                log.warning(json.dumps({"trace_id": trace["trace_id"], "turn": turn, "tool": name, "scrubbed": hits}))
        else:
            # ensure_ascii=False: the model reads "1–3 days" and "₹49", not "1\u20133" and "\u20b949".
            content = json.dumps(result, default=str, ensure_ascii=False)
        if context:
            context.state.update(name, parse_args(raw), seen)
        trace["tool_calls"].append({"name": name, "args": raw, "parsed": parsed, "result": result,
                                    "ok": ok, "latency_ms": latency_ms})
        # One line per call, the same shape everywhere; dashboards are built from these. Redacted: logs are
        # the most-copied data in the project (agent/privacy.py).
        log.info(json.dumps({"trace_id": trace["trace_id"], "turn": turn, "tool": name, "args": redact(raw or ""),
                             "ok": ok, "latency_ms": latency_ms, "result_bytes": len(content.encode())}))
        messages.append({"role": "tool", "tool_call_id": call_id, "content": content})
        return result

    def force_tracking(order_id):
        """get_tracking called by the loop for a shipped order the model only checked the status of, so the
        lost-parcel rule can see the last scan. Shown to the model as a call it made."""
        raw = json.dumps({"order_id": order_id})
        call_id = f"track-{trace['trace_id']}-{order_id}"
        messages.append({"role": "assistant", "content": "", "tool_calls": [
            {"id": call_id, "type": "function", "function": {"name": "get_tracking", "arguments": raw}}]})
        trace.setdefault("forced_tracking", []).append(order_id)
        with span("rule:check_tracking", as_type="guardrail", input={"order_id": order_id}):
            return run_call(call_id, "get_tracking", raw, forced=True)

    def force_handoff(esc):
        """escalate_to_human called by the loop, shown to the model as a call it made, so it only has to tell
        the customer what happens next."""
        raw = json.dumps(rules.handoff_args(esc), ensure_ascii=False)
        call_id = f"handoff-{trace['trace_id']}"
        messages.append({"role": "assistant", "content": "", "tool_calls": [
            {"id": call_id, "type": "function", "function": {"name": "escalate_to_human", "arguments": raw}}]})
        trace["forced_handoff"] = esc.reason
        log.warning(json.dumps({"trace_id": trace["trace_id"], "turn": turn, "forced_handoff": esc.reason}))
        with span("rule:handoff", as_type="guardrail", input={"reason": esc.reason}):
            run_call(call_id, "escalate_to_human", raw, forced=True)

    def finish(reply):
        if rules:
            rules.end_turn(user_msg, trace["tool_calls"], reply)
        return reply, trace

    if guard:
        with span("input_check", as_type="guardrail") as step:
            trace["input_flags"] = guard.incoming(user_msg)
            step.update(output={"flags": trace["input_flags"]}, level="WARNING" if trace["input_flags"] else None)
        trace["scrubbed"] = []
        if trace["input_flags"]:
            log.warning(json.dumps({"trace_id": trace["trace_id"], "turn": turn, "input_flags": trace["input_flags"]}))
    if rules and (esc := rules.at_turn_start(user_msg)):
        force_handoff(esc)
    for step_no in range(max_steps):
        sent = context.prepare(messages) if context else messages
        t0 = time.perf_counter()
        with span("model_call", as_type="generation", model=model, metadata={"step": step_no + 1},
                  model_parameters={"temperature": temperature, "max_tokens": 512},
                  input={"messages_sent": len(sent), "messages_in_conversation": len(messages)}) as gen:
            r = client.chat.completions.create(model=model, messages=sent, tools=tools,
                                               temperature=temperature, max_tokens=512, **(sampling or {}))
            m = r.choices[0].message
            gen.update(output={"tool_calls": [c.function.name for c in (m.tool_calls or [])],
                               "reply_chars": len(m.content or "")},
                       usage_details={"input": r.usage.prompt_tokens, "output": r.usage.completion_tokens}
                       if r.usage else None,
                       metadata={"served_model": r.model, "finish_reason": r.choices[0].finish_reason,
                                 "format_error": unusable(m)},
                       level="WARNING" if unusable(m) else None)
        if context:
            trace.setdefault("sent", []).append({"messages": len(sent), "of": len(messages),
                                                 "budget_tokens": context.count_tokens(sent),
                                                 "state": sent[0]["content"].split("\n\n")[-1]})
        trace["model_calls"].append({
            "latency_s": round(time.perf_counter() - t0, 3),
            "prompt_tokens": r.usage.prompt_tokens if r.usage else None,
            "completion_tokens": r.usage.completion_tokens if r.usage else None,
            "finish_reason": r.choices[0].finish_reason,
            "served_model": r.model,                # recorded per call: what actually answered
        })
        msg = r.choices[0].message
        if unusable(msg):
            trace["format_errors"] += 1
            trace["model_calls"][-1]["format_error"] = True
            if not msg.tool_calls:                  # nothing parsed: a raw call or a blank must not reach the customer
                trace["raw_reply"] = msg.content
                return finish(_hand_off(messages, trace)[0])
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            reply = msg.content
            t_checks = time.perf_counter()
            with span("reply_checks", as_type="guardrail") as step:
                hits = []
                if guard:
                    reply, hits = guard.outgoing(reply, messages)
                    if hits:
                        trace["output_guard"] = {"hits": hits, "original": msg.content}
                        messages[-1]["content"] = reply      # the history holds what the customer saw
                        log.warning(json.dumps({"trace_id": trace["trace_id"], "turn": turn, "output_guard": hits}))
                trace["grounding"] = grounding_issues(reply, tool_contents_before(messages, len(messages)))
                step.update(output={"output_filter_hits": hits, "grounding_issues": trace["grounding"]},
                            level="WARNING" if hits or trace["grounding"] else None)
            trace["checks_ms"] = round(1000 * (time.perf_counter() - t_checks), 1)
            return finish(reply)
        results = []
        for k, call in enumerate(msg.tool_calls):
            name, raw = call.function.name, call.function.arguments
            if context and k >= MAX_CALLS_PER_STEP:     # one call per step is the rule; two are tolerated
                messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(SKIPPED)})
                trace["tool_calls"].append({"name": name, "args": raw, "parsed": False, "result": SKIPPED,
                                            "ok": False, "latency_ms": 0})
                continue
            results.append(run_call(call.id, name, raw))
        if rules and (oid := rules.tracking_to_check(results)):
            results.append(force_tracking(oid))
        if rules and (esc := rules.after_tools(results)):
            force_handoff(esc)
    return finish(_hand_off(messages, trace)[0])     # ran out of steps


def _hand_off(messages, trace):
    trace["escalated"] = True
    trace["grounding"] = []                         # the fixed fallback states no facts
    messages.append({"role": "assistant", "content": FALLBACK_REPLY})
    return FALLBACK_REPLY, trace
