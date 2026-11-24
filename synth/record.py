"""Recording a teacher conversation as the student will see it.

The teacher answers with Nova's prompt plus its extra rules (synth/teacher_rules.py). What is recorded is what the
student would have been sent at that moment in serving: Nova's own prompt, the conversation state block, and the
history trimmed by the same fit() serving uses (agent/state.py), with the same tokenizer and budget. One model
call is one training step: the request as the student would see it, and the teacher's message as the target.

Why per step, not one long conversation: the state block changes after every tool result, and fit() drops old
turns, so no single transcript is what the student saw at every call. The chat template also renders only the
last assistant turn the way the model generates it (with the empty think block), so the target is always the
last message of its step.

The teacher sees exactly the history the student record keeps: fit() is decided on the student's view, and the
teacher gets the same kept messages under its longer prompt. So nothing the teacher relied on is cut from the
record.
"""

import json
from dataclasses import dataclass, field

from agent.state import Context, fit

KEEP_KEYS = ("role", "content", "tool_calls", "tool_call_id")


def clean(m: dict) -> dict:
    """Only what the chat template reads: drops reasoning text, refusal fields and anything else the server adds.

    Text written alongside a tool call ("Let me check your orders...") is dropped too. The loop never shows it
    to the customer (only the final reply is), so it would only teach the student to write words nobody reads
    before every call. The teacher wrote it with 28 of 67 calls even when its rules said not to."""
    out = {k: m[k] for k in KEEP_KEYS if k in m and m[k] is not None}
    if out.get("tool_calls"):
        out.pop("content", None)
        out["tool_calls"] = [{"id": c["id"], "type": "function",
                              "function": {"name": c["function"]["name"], "arguments": c["function"]["arguments"]}}
                             for c in out["tool_calls"]]
    return out


def with_student_prompt(messages: list[dict], state_block: str, budget: int, count_tokens,
                        keep_turns: int) -> list[dict]:
    """The request the student would get: messages[0] is Nova's serving prompt; the state block goes after it,
    as in serving (agent/state.Context.prepare), and the history is trimmed by the same fit()."""
    system = {"role": "system", "content": messages[0]["content"] + "\n\n" + state_block}
    return fit([system] + [clean(m) for m in messages[1:]], budget, count_tokens, keep_turns)


CALL_BUDGET = 3   # tool calls per customer message before the reply must come (the loop allows 4 model calls)
# Teacher-only, never recorded. Two pilots ran out of calls in 22 and 27 of about 200 conversations although the
# rules named the limit; told at the moment, the teacher answers with what it has, and the student learns from
# the recording that the fourth step is a reply.
LAST_STEP = ("You have used your three tool calls for this message. Reply to the customer now with what the "
             "results show; do not call another tool.")


def calls_this_turn(messages: list[dict]) -> int:
    """Tool calls made since the last customer message."""
    n = 0
    for m in reversed(messages):
        if m["role"] == "user":
            break
        n += len(m.get("tool_calls") or [])
    return n


@dataclass
class RecordingContext(Context):
    """A Context for the teacher: sends the teacher its prompt, and records the student's view of every call."""
    teacher_system: str = ""
    steps: list[dict] = field(default_factory=list)
    last_sent: list[dict] = field(default_factory=list)      # the teacher's last request, for a rewrite

    def prepare(self, messages: list[dict]) -> list[dict]:
        state = self.state.render()
        student = with_student_prompt(messages, state, self.budget, self.count_tokens, self.keep_turns)
        self.steps.append({"at": len(messages), "messages": student})
        teacher = self.teacher_system + "\n\n" + state
        if calls_this_turn(student) >= CALL_BUDGET:
            teacher += "\n\n" + LAST_STEP
        self.last_sent = [{"role": "system", "content": teacher}] + student[1:]
        return self.last_sent


def finish_steps(steps: list[dict], messages: list[dict], model_calls: list[dict]) -> list[dict]:
    """Pair each recorded request with the teacher message it produced. A call that ended in a format error
    (a raw tool call, an empty reply) is kept, marked, so the verifiers can count it; it is never a target."""
    out = []
    for step, call in zip(steps, model_calls, strict=True):
        target = messages[step["at"]] if step["at"] < len(messages) else None
        ok = (target is not None and target.get("role") == "assistant" and not call.get("format_error"))
        out.append({"messages": step["messages"], "target": clean(target) if target else None, "ok": ok,
                    "prompt_tokens": call.get("prompt_tokens"), "completion_tokens": call.get("completion_tokens")})
    return out


class RunFile:
    """One file per generation run, never overwritten; each conversation is appended as soon as it is finished,
    so a stopped run keeps everything it produced."""

    def __init__(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.f = open(path, "x", encoding="utf-8")       # "x": fails if the file exists
        self.path = path

    def write(self, conv: dict) -> None:
        self.f.write(json.dumps(conv, ensure_ascii=False, default=str) + "\n")
        self.f.flush()

    def close(self) -> None:
        self.f.close()
