"""Personas, openers and the coverage grid for simulated customers (synth/personas.py). No database, no model.

    uv run --group dev pytest tests/test_synth_personas.py
"""

import random
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from synth.personas import BY_NAME, PERSONAS, Grid, Openers, _fill  # noqa: E402
from synth.scenarios import SCENARIOS, Scenario  # noqa: E402


def test_the_grid_follows_the_shares_and_reaches_every_cell():
    grid, rng = Grid(), random.Random(1)
    cells = Counter(grid.next(rng) for _ in range(len(SCENARIOS) * 40))
    assert len(cells) == len(SCENARIOS) * len(PERSONAS)                    # 128 cells, none empty
    per_persona = Counter(p for _, p in cells.elements())
    for p in PERSONAS:
        assert abs(per_persona[p.name] / sum(per_persona.values()) - p.share) < 0.01
    per_scenario = Counter(s for s, _ in cells.elements())
    assert max(per_scenario.values()) - min(per_scenario.values()) <= 1


def test_the_grid_fills_the_emptiest_cell_first():
    frustrated = [BY_NAME["frustrated"]]
    counts = {(s, "frustrated"): 5 for s in SCENARIOS} | {("split_shipment", "frustrated"): 0}
    assert Grid(personas=frustrated, counts=counts).next(random.Random(0)) == ("split_shipment", "frustrated")


def test_a_small_run_already_has_every_persona():
    grid, rng = Grid(), random.Random(3407)
    assert {p for _, p in (grid.next(rng) for _ in range(30))} == {p.name for p in PERSONAS}


def openers(rows):
    o = Openers.__new__(Openers)
    o.rows = [SimpleNamespace(instruction=t, intent=i, flags=f) for t, i, f in rows]
    return o


def test_openers_match_intent_and_flags():
    o = openers([("where is order {{Order Number}}", "track_order", "BL"),
                 ("wher is my ordr", "track_order", "BZ"),
                 ("track order", "track_order", "BK"),
                 ("refund pls", "get_refund", "BZ")])
    rng = random.Random(0)
    assert {o.pick(["track_order"], BY_NAME["typo"], rng) for _ in range(20)} == {"wher is my ordr"}
    assert {o.pick(["track_order"], BY_NAME["keyword"], rng) for _ in range(20)} == {"track order"}
    # Direct excludes typos and keywords; no flag match at all falls back to the intent.
    assert {o.pick(["track_order"], BY_NAME["direct"], rng) for _ in range(20)} == {"where is order {{Order Number}}"}
    assert o.pick(["get_refund"], BY_NAME["polite_long"], rng) == "refund pls"


def test_only_a_known_order_number_is_filled_in():
    sc = Scenario("in_transit", 1, 12732, "goal", ["Your order number is 12732. Give it only if asked for it."],
                  {}, ["track_order"])
    assert _fill("status of {{Order Number}} please", sc) == "status of 12732 please"
    # Slots the customer has no value for become neutral words, never a made-up amount.
    assert _fill("I paid {{Currency Symbol}}{{Refund Amount}} for it", sc) == "I paid money for it"
    assert _fill("refunding {{Refund Amount}}  dollars", sc) == "refunding money"
    unknown = Scenario("in_transit", 1, 12732, "goal", ["You ordered: Cap."], {}, ["track_order"])
    assert _fill("status of {{Order Number}}", unknown) == "status of my order"
