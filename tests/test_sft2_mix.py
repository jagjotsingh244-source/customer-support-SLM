"""The second fine-tune's mix (training/sft2_mix.py): what is kept from a conversation the fact-check judge failed.

    uv run --group dev pytest tests/test_sft2_mix.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from training.sft2_mix import prefix_examples  # noqa: E402

CALL, REPLY = {"tool_calls": [{"function": {"name": "get_tracking"}}]}, {"content": "a reply"}


def conv(targets, fact_reply):
    steps = [{"messages": [{"role": "user", "content": "hi"}], "target": t} for t in targets]
    return {"id": "c", "scenario": "delayed", "persona": "direct", "steps": json.dumps(steps), "fact_reply": fact_reply}


def test_steps_before_the_first_bad_reply_are_kept():
    kept = prefix_examples(conv([CALL, REPLY, CALL, REPLY, REPLY], fact_reply=2))
    assert [e["target"] for e in kept] == ["call", "reply", "call"]     # the second reply and after are dropped
    assert all(e["source"] == "trajectory_prefix" for e in kept)


def test_a_slip_in_the_first_reply_keeps_only_the_lookups_before_it():
    assert [e["target"] for e in prefix_examples(conv([CALL, CALL, REPLY, REPLY], fact_reply=1))] == ["call", "call"]


def test_no_reply_named_keeps_nothing():
    assert prefix_examples(conv([CALL, REPLY], fact_reply=0)) == []
