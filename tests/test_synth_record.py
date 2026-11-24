"""Recording teacher conversations as the student sees them (synth/record.py), with a scripted stand-in teacher.

No database and no model: the stand-in returns a fixed tool call and a fixed reply, and the tool result is a real
one from the seeded world (tests/fixtures/long_chat_results.json). Prompts are counted one token per character,
so trimming can be forced with a small budget.

    uv run --group dev pytest tests/test_synth_record.py
"""

import json
from types import SimpleNamespace
import sys
from pathlib import Path

import pytest
from openai.types.chat import ChatCompletion

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent.loop import run_turn  # noqa: E402
from synth.record import RecordingContext, RunFile, clean, finish_steps, with_student_prompt  # noqa: E402
from synth.style import style_problems  # noqa: E402
from synth.teacher_rules import HEADER, RULES, teacher_prompt  # noqa: E402

RESULTS = json.loads((Path(__file__).parent / "fixtures" / "long_chat_results.json").read_text())["results"]
WEBCAM = 11904
STUDENT = "You are Nova. Rules: be short."


def chars(msgs):
    return sum(len(m.get("content") or "") + 10 for m in msgs)


def completion(content=None, call=None) -> ChatCompletion:
    msg = {"role": "assistant", "content": content}
    if call:
        msg["tool_calls"] = [{"id": "call_1", "type": "function",
                              "function": {"name": call[0], "arguments": json.dumps(call[1])}}]
    return ChatCompletion.model_validate({
        "id": "x", "object": "chat.completion", "created": 0, "model": "teacher",
        "choices": [{"index": 0, "finish_reason": "tool_calls" if call else "stop", "message": msg}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}})


class Teacher:
    """Answers from a script and keeps every request it was sent."""

    def __init__(self, script):
        self.script, self.sent = list(script), []
        self.chat = self
        self.completions = self

    def create(self, **kw):
        self.sent.append(kw["messages"])
        return self.script.pop(0)


def dispatch(name, raw, session, attempts):
    return RESULTS[f"{name}:{json.loads(raw)['order_id']}"]


def one_turn(teacher, budget=10_000, text="where is my webcam order 11904"):
    ctx = RecordingContext(count_tokens=chars, budget=budget, teacher_system=teacher_prompt(STUDENT))
    messages = [{"role": "system", "content": STUDENT}, {"role": "user", "content": text}]
    reply, trace = run_turn(teacher, "teacher", messages, [], dispatch, None, context=ctx)
    return ctx, messages, reply, trace


def test_steps_carry_the_student_prompt_and_the_teacher_gets_the_rules():
    teacher = Teacher([completion(call=("get_tracking", {"order_id": WEBCAM})),
                       completion("Order 11904, your 1080p webcam, is in transit.")])
    ctx, messages, reply, trace = one_turn(teacher)
    steps = finish_steps(ctx.steps, messages, trace["model_calls"])

    assert len(steps) == 2 and all(s["ok"] for s in steps)
    for s in steps:
        system = s["messages"][0]["content"]
        assert system.startswith(STUDENT) and HEADER not in system and RULES[0] not in system
    for sent in teacher.sent:
        assert sent[0]["content"].startswith(STUDENT + "\n\n" + HEADER)
    # The teacher saw exactly the student's history, under its own longer prompt.
    for s, sent in zip(steps, teacher.sent):
        assert s["messages"][1:] == [clean(m) for m in sent[1:]]
    # The state block: empty before the lookup, the webcam's tracking after it.
    assert "No order looked up yet." in steps[0]["messages"][0]["content"]
    assert "1080p webcam = order 11904" in steps[1]["messages"][0]["content"]
    # Targets: first the call, then the reply; the second request ends with the tool result.
    assert steps[0]["target"]["tool_calls"][0]["function"]["name"] == "get_tracking"
    assert steps[1]["messages"][-1]["role"] == "tool"
    assert steps[1]["target"] == {"role": "assistant", "content": reply}


def test_trimming_is_decided_on_the_student_view():
    teacher = Teacher([completion("Hello again."), completion("Still here.")])
    ctx = RecordingContext(count_tokens=chars, budget=400, keep_turns=3, teacher_system=teacher_prompt(STUDENT))
    long = "x" * 150
    messages = [{"role": "system", "content": STUDENT}, {"role": "user", "content": long},
                {"role": "assistant", "content": long}, {"role": "user", "content": "hi"}]
    run_turn(teacher, "teacher", messages, [], dispatch, None, context=ctx)
    kept = ctx.steps[0]["messages"]
    assert [m["content"] for m in kept[1:]] == ["hi"]              # the long first turn did not fit the student
    assert [m["content"] for m in teacher.sent[0][1:]] == ["hi"]   # so the teacher did not see it either
    assert chars(teacher.sent[0]) > 400                            # its prompt alone is over the student's budget


def test_a_format_error_is_never_a_target():
    teacher = Teacher([completion('<tool_call><function=get_tracking><parameter=order_id>11904')])
    ctx, messages, reply, trace = one_turn(teacher)
    steps = finish_steps(ctx.steps, messages, trace["model_calls"])
    assert trace["format_errors"] == 1 and len(steps) == 1 and not steps[0]["ok"]


def test_clean_keeps_only_what_the_template_reads():
    m = {"role": "assistant", "content": "Hi", "reasoning_content": "thinking...", "refusal": None,
         "tool_calls": [{"id": "c", "type": "function", "index": 0,
                         "function": {"name": "list_my_orders", "arguments": "{}"}}]}
    # Text written alongside a call is dropped: the customer never sees it.
    assert clean(m) == {"role": "assistant", "tool_calls": [
        {"id": "c", "type": "function", "function": {"name": "list_my_orders", "arguments": "{}"}}]}
    assert clean({"role": "assistant", "content": "Done.", "refusal": None}) == {"role": "assistant",
                                                                                 "content": "Done."}


def test_with_student_prompt_puts_the_state_after_the_prompt():
    msgs = [{"role": "system", "content": STUDENT}, {"role": "user", "content": "hi"}]
    out = with_student_prompt(msgs, "Conversation state: none.", 10_000, chars, 6)
    assert out[0]["content"] == STUDENT + "\n\nConversation state: none." and out[1:] == msgs[1:]


def test_a_run_file_is_never_overwritten(tmp_path):
    path = tmp_path / "raw" / "run.jsonl"
    f = RunFile(path)
    f.write({"id": 1})
    f.close()
    with pytest.raises(FileExistsError):
        RunFile(path)
    assert path.read_text() == '{"id": 1}\n'


# Style rules (synth/style.py), one passing and one failing reply each ----------------------------------------

SOURCES = '{"order_id": 11904, "tracking_no": "SS70001836", "note": "Press Confirm on the card."}'


@pytest.mark.parametrize("reply, problem", [
    ("Order 11904 is in transit. Would you like me to check anything else?", "offer"),
    ("Order 11904 is in transit. Is there anything else I can help you with?", "offer"),
    ("Order 11904 is in transit.\n\nThe last scan was in Nagpur.", "paragraphs"),
    ("word " * 71, "words"),
    ("Your order:\n- 11904 in transit", "list"),
    ("You will get an email with a return label shortly.", "email, label"),
])
def test_style_problems_are_found(reply, problem):
    assert any(problem.split(",")[0] in p for p in style_problems(reply, SOURCES)), style_problems(reply, SOURCES)


@pytest.mark.parametrize("reply", [
    "Order 11904, your 1080p webcam, is in transit with SwiftShip (SS70001836).",
    "I can't change that here. Would you like me to connect you with a teammate?",   # a teammate offer is allowed
    "Which of your two orders do you mean, the webcam or the tote bag?",              # a question that is needed
])
def test_good_replies_pass(reply):
    assert style_problems(reply, SOURCES) == []


def test_after_three_calls_only_the_teacher_is_told_to_reply():
    from synth.record import LAST_STEP
    teacher = Teacher([completion(call=("get_tracking", {"order_id": WEBCAM})) for _ in range(3)] +
                      [completion("Order 11904 is in transit.")])
    ctx, messages, reply, trace = one_turn(teacher)
    assert [LAST_STEP in sent[0]["content"] for sent in teacher.sent] == [False, False, False, True]
    assert not any(LAST_STEP in s["messages"][0]["content"] for s in ctx.steps)       # never recorded


def test_a_late_parcel_hand_off_offer_is_sent_back():
    from synth.generate import policy_problems
    msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "where is my webcam"}]
    offer = "It is still with SwiftShip. Would you like me to connect you with a teammate?"
    assert policy_problems(offer, msgs, "delayed")
    assert policy_problems(offer, msgs, "lost") == []                                  # lost parcels are handed off
    asked = msgs + [{"role": "user", "content": "i want to talk to a person"}]
    assert policy_problems(offer, asked, "delayed") == []


def test_the_last_step_goes_to_the_teacher_without_tools():
    from synth.generate import LastStepWithoutTools
    from synth.record import LAST_STEP
    seen, replies = [], iter(["", "Order 11904 is in transit."])

    def create(**kw):
        seen.append(("tools" in kw, kw["messages"][-1]["content"], kw.get("temperature")))
        content = "Order 11904 is in transit." if "tools" in kw else next(replies)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

    client = LastStepWithoutTools(SimpleNamespace(models=None, chat=SimpleNamespace(
        completions=SimpleNamespace(create=create))))
    client.chat.completions.create(messages=[{"role": "system", "content": "rules"}, {"role": "user", "content": "hi"}],
                                   tools=[{"x": 1}], temperature=0.7)
    r = client.chat.completions.create(messages=[{"role": "system", "content": "rules\n\n" + LAST_STEP},
                                                 {"role": "tool", "content": "{}"}], tools=[{"x": 1}], temperature=0.7)
    assert seen[0] == (True, "hi", 0.7)                                   # an ordinary step is untouched
    assert not seen[1][0] and LAST_STEP in seen[1][1]                     # the last step: no tools, note last
    assert seen[2][2] == 1.0 and r.choices[0].message.content             # an empty reply is asked for again


def test_false_return_and_hand_off_claims_are_sent_back():
    from synth.generate import policy_problems
    msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "return my air fryer"}]
    assert policy_problems("I have initiated the return for your air fryer.", msgs, "return_eligible")
    assert policy_problems("Your return proposal (ID 901920) has been created. Press Confirm.", msgs,
                           "return_eligible") == []
    assert policy_problems("Your return was picked up on 18 November.", msgs, "return_in_progress",
                           had_return=True) == []
    assert policy_problems("I've escalated this to a teammate.", msgs, "lost")
