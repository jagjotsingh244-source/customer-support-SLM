"""The conversation state, the history trimmer, and a 15-turn chat that stays inside the budget.

The 15-turn chat uses a scripted customer, a stand-in model and the real tool results of customer 416's two
orders (tests/fixtures/long_chat_results.json, taken from the seeded database with agent/tools_v2.py). The
stand-in model sees only what is sent to it, so once older messages are trimmed away the only way it can
know which order "it" is, is the state block. Prompts are counted with Qwen3.5-2B's tokenizer on the rendered
chat template, with the real tool schemas.

    uv run --group dev --group local-model pytest tests/test_state.py
"""

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent.state import PROMPT_BUDGET, Context, ContextOverflow, State, fit  # noqa: E402
from evals.long_chat import SCRIPT, TOTE, WEBCAM  # noqa: E402

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "long_chat_results.json").read_text())
RESULTS = FIXTURE["results"]


# State ------------------------------------------------------------------------------------------------------

def test_state_follows_tool_results():
    s = State()
    assert "No order looked up yet." in s.render()
    s.update("get_tracking", {"order_id": WEBCAM}, RESULTS[f"get_tracking:{WEBCAM}"])
    s.update("get_order_status", {"order_id": TOTE}, RESULTS[f"get_order_status:{TOTE}"])
    text = s.render()
    assert s.focus_order == TOTE and "Last order looked up: 10689 (Screen protector, Tote bag)." in text
    assert "- 1080p webcam = order 11904: in transit, tracking SwiftShip SS70001836" in text
    assert "Nagpur hub" in text and "- Screen protector, Tote bag = order 10689: delivered, total ₹947.00" in text
    assert text.index("order 11904") < text.index("order 10689")         # most recent last


def test_errors_and_lists_do_not_move_the_focus():
    s = State()
    s.update("get_tracking", {"order_id": WEBCAM}, RESULTS[f"get_tracking:{WEBCAM}"])
    s.update("get_tracking", {"order_id": 12578}, {"error": "not_found", "detail": "No order..."})
    s.update("list_my_orders", {"limit": 5}, RESULTS["list_my_orders"])
    s.update("get_tracking", None, {"error": "invalid_arguments", "detail": "..."})
    assert s.focus_order == WEBCAM and list(s.facts) == [WEBCAM]


def test_a_status_lookup_keeps_the_tracking_found_earlier():
    s = State()
    s.update("get_tracking", {"order_id": WEBCAM}, RESULTS[f"get_tracking:{WEBCAM}"])
    s.update("get_order_status", {"order_id": WEBCAM}, RESULTS[f"get_order_status:{WEBCAM}"])
    line = [x for x in s.render().splitlines() if f"order {WEBCAM}:" in x][0]
    assert "SS70001836" in line and "₹2799.00" in line


def test_open_proposal_is_shown():
    s = State()
    s.update("propose_return", {"order_id": 11360, "line_no": 1, "reason": "faulty"},
             {"order_id": 11360, "line_no": 1, "item": "Air fryer", "eligible": True, "proposal_id": 900017,
              "refund_estimate_inr": "5999.00", "note": "..."})
    text = s.render()
    assert "Return waiting for the customer's Confirm: #900017: Air fryer from order 11360" in text
    assert text.count("900017") == 1


def test_a_handoff_is_remembered():
    s = State()
    s.update("escalate_to_human", {"reason": "lost_parcel", "summary": "No scan since 12 Nov."},
             {"handed_off": True, "ticket_id": 900049, "note": "..."})
    s.update("escalate_to_human", {"reason": "other", "summary": "x"}, {"error": "invalid_arguments", "detail": "."})
    assert "Already handed to the support team: ticket 900049 (lost parcel)." in s.render()
    assert s.focus_order is None


def test_only_the_last_four_facts_are_rendered():
    s = State()
    for oid in range(10001, 10007):
        s.update("get_tracking", {"order_id": oid}, {"order_id": oid, "shipped": False, "note": f"note {oid}"})
    text = s.render()
    assert "order 10002" not in text and "order 10003" in text and "order 10006" in text


# The trimmer -------------------------------------------------------------------------------------------------

def chars(msgs):                                    # a stand-in count: one token per character
    return sum(len(m.get("content") or "") + 10 for m in msgs)


def turn(n, with_tool=True):
    """One customer turn: question, optionally a call and its result, then the reply."""
    out = [{"role": "user", "content": f"question {n}"}]
    if with_tool:
        out += [{"role": "assistant", "content": None, "tool_calls": [{"id": f"c{n}", "type": "function",
                 "function": {"name": "get_tracking", "arguments": "{}"}}]},
                {"role": "tool", "tool_call_id": f"c{n}", "content": "x" * 50}]
    return out + [{"role": "assistant", "content": f"answer {n}"}]


def reply_only(n):
    return [{"role": "user", "content": f"question {n}"}, {"role": "assistant", "content": f"answer {n}"}]


def test_fit_keeps_two_earlier_turns_as_message_and_reply():
    msgs = [{"role": "system", "content": "s"}] + turn(1) + turn(2) + turn(3) + [{"role": "user", "content": "q4"}]
    out = fit(msgs, budget=10_000, count_tokens=chars, keep_turns=3)
    assert out[0]["role"] == "system" and out[1]["role"] == "user"
    # Turns 2 and 3 without their calls and results, then the current turn; turn 1 is past keep_turns.
    assert out[1:] == reply_only(2) + reply_only(3) + [{"role": "user", "content": "q4"}]


def test_the_last_reply_survives_a_turn_with_many_calls():
    """The case that broke the message count: a lookup turn of six messages hid Nova's own answer."""
    busy = turn(1)[:3] + turn(2)[1:3] + [{"role": "assistant", "content": "I'll check that.",
                                          "tool_calls": turn(3)[1]["tool_calls"]}, turn(3)[2], turn(1)[3]]
    msgs = [{"role": "system", "content": "s"}] + busy + [{"role": "user", "content": "and the other one?"}]
    out = fit(msgs, budget=10_000, count_tokens=chars)
    assert out[1:] == reply_only(1) + [{"role": "user", "content": "and the other one?"}]


def test_the_current_turn_keeps_every_call_and_result():
    msgs = [{"role": "system", "content": "s"}] + turn(1) + turn(2)
    out = fit(msgs, budget=10_000, count_tokens=chars)
    assert out[1:] == reply_only(1) + turn(2)
    calls = {c["id"] for m in out if m.get("tool_calls") for c in m["tool_calls"]}
    assert all(m["tool_call_id"] in calls for m in out if m["role"] == "tool")


def test_fit_drops_oldest_turns_until_it_fits():
    msgs = [{"role": "system", "content": "s"}] + turn(1, False) + turn(2, False) + [{"role": "user", "content": "q3"}]
    full = fit(msgs, budget=10_000, count_tokens=chars, keep_turns=3)
    assert len(full) == 6
    tight = fit(msgs, budget=chars(msgs[:1] + msgs[3:]), count_tokens=chars, keep_turns=3)
    assert tight == msgs[:1] + msgs[3:]                                 # turn 1 dropped, turn 2 kept


def test_current_turn_is_never_dropped():
    long_turn = [{"role": "user", "content": "q"}] + turn(9)[1:3] * 3     # three calls and results in one turn
    msgs = [{"role": "system", "content": "s"}] + turn(1) + long_turn
    out = fit(msgs, budget=10_000, count_tokens=chars, keep_turns=3)
    assert out[1:] == reply_only(1) + long_turn                          # the current turn whole, however long
    with pytest.raises(ContextOverflow):
        fit(msgs, budget=50, count_tokens=chars)


# Fifteen turns ------------------------------------------------------------------------------------------------

TRACKING_WORDS = ("where", "courier", "arrive", "scanned", "tracking", "delayed", "wait", "delivered")


class StandInModel:
    """Decides from the sent messages only: an order number in the question, else an item named in the
    question and found in the state or a tool result that was sent, else the order in focus, else the
    last order seen in the sent tool results. Answers with the order it looked up."""

    def __init__(self):
        self.chat = self.completions = self
        self.sent = []

    def create(self, *, messages, **_):
        from openai.types.chat import ChatCompletion
        self.sent.append(messages)
        state = messages[0]["content"]
        tool_text = " ".join(m["content"] for m in messages if m["role"] == "tool")
        last = messages[-1]
        if last["role"] == "tool":
            result = json.loads(last["content"])
            oid = result.get("order_id")
            content = f"Order {oid}: {result.get('order_status') or result.get('status')}." if oid else \
                "Card refunds take a few days. [kb:refunds-payment-methods#card]"
            return self._reply(content=content)
        q = last["content"].lower()
        if "refund" in q and "how long" in q:
            return self._reply(call=("search_help_center", {"query": "refund time card"}))
        oid = None
        if m := re.search(r"\b(\d{5})\b", q):
            oid = int(m.group(1))
        for word in ("webcam", "tote"):
            if oid is None and word in q:
                for line in state.splitlines() + [tool_text]:
                    if word in line.lower() and (m := re.search(r"\b(1\d{4})\b", line)):
                        oid = int(m.group(1))
                        break
        if oid is None and (m := re.search(r"Last order looked up: (\d{5})", state)):
            oid = int(m.group(1))
        if oid is None and (seen := re.findall(r'"order_id": (\d{5})', tool_text)):
            oid = int(seen[-1])
        if oid is None:
            return self._reply(content="Which order do you mean?")
        tool = "get_tracking" if any(w in q for w in TRACKING_WORDS) else "get_order_status"
        return self._reply(call=(tool, {"order_id": oid}))

    @staticmethod
    def _reply(content=None, call=None):
        from openai.types.chat import ChatCompletion
        calls = [{"id": f"c{abs(hash(str(call))) % 10_000}", "type": "function",
                  "function": {"name": call[0], "arguments": json.dumps(call[1])}}] if call else None
        return ChatCompletion.model_validate({
            "id": "x", "object": "chat.completion", "created": 0, "model": "m",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "choices": [{"index": 0, "finish_reason": "tool_calls" if calls else "stop",
                         "message": {"role": "assistant", "content": content, "tool_calls": calls}}]})


def fixture_tools(name, raw, session, attempts):
    args = json.loads(raw)
    key = f"{name}:{args['order_id']}" if "order_id" in args else (
        f"{name}:{args['query']}" if "query" in args else name)
    return RESULTS[key]


class Frozen(State):
    """A state that never learns anything: the same trimming, nothing carried over."""
    def update(self, *_):
        pass


def chat(state):
    pytest.importorskip("transformers")
    from agent.loop import run_turn
    from agent.prompts import system_prompt
    from agent.state import token_counter
    from agent.tools_v2 import TOOLS
    from config import now
    model, count = StandInModel(), token_counter(TOOLS)
    ctx = Context(count_tokens=count, state=state)
    messages = [{"role": "system", "content": system_prompt(now(), FIXTURE["customer_name"], "v2")}]
    replies = []
    for text, _ in SCRIPT:
        messages.append({"role": "user", "content": text})
        reply, trace = run_turn(model, "m", messages, TOOLS, fixture_tools, None, context=ctx)
        replies.append((reply, trace))
    return replies, model, count, messages


def test_fifteen_turns_stay_in_budget_and_on_the_right_order():
    replies, model, count, messages = chat(State())
    sizes = [count(sent) for sent in model.sent]
    assert max(sizes) <= PROMPT_BUDGET, max(sizes)
    for (text, want), (reply, _) in zip(SCRIPT, replies):
        if want:
            assert reply.startswith(f"Order {want}:"), (text, reply)
    # The trimming really happened: late in the chat, the messages that named the orders were not sent.
    late = model.sent[-1]
    assert not any("11904" in (m.get("content") or "") for m in late if m["role"] == "user")
    assert len(messages) > 40 and len(late) <= 8
    # No sent history starts mid-turn or holds a result without its call.
    for sent in model.sent:
        assert sent[1]["role"] == "user"
        calls = {c["id"] for m in sent if m.get("tool_calls") for c in m["tool_calls"]}
        assert all(m["tool_call_id"] in calls for m in sent if m["role"] == "tool")
    print(f"\nprompt tokens per model call: min {min(sizes)}, max {max(sizes)} (budget {PROMPT_BUDGET}); "
          f"full history would be {count(messages)}")


def test_without_the_state_the_same_trimming_loses_the_order():
    replies, *_ = chat(Frozen())
    wrong = [text for (text, want), (reply, _) in zip(SCRIPT, replies) if want and not reply.startswith(f"Order {want}:")]
    assert wrong, "without state every turn was still right: the test no longer shows what the state is for"
    assert "going back to the webcam order, where was it last scanned?" in wrong
