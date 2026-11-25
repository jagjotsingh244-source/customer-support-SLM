"""The scenario x persona grid of kept conversations, and the cells still short of a minimum.

    uv run --group data python -m synth.coverage              # print the grid and the thin cells
    uv run --group data python -m synth.coverage --cells-only # scenario:persona pairs, for synth.generate --cells
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from synth.personas import PERSONAS  # noqa: E402
from synth.scenarios import SCENARIOS  # noqa: E402

KEPT = ROOT / "data" / "synthetic" / "nova-trajectories-v2"


def grid() -> Counter:
    from datasets import load_from_disk
    return Counter((r["scenario"], r["persona"]) for r in load_from_disk(str(KEPT)))


def thin(counts: Counter, minimum: int) -> list[tuple[str, str]]:
    """Cells of the 16 scenarios x 8 personas with fewer than `minimum` kept conversations."""
    return [(s, p.name) for s in SCENARIOS for p in PERSONAS if counts[(s, p.name)] < minimum]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minimum", type=int, default=2)
    ap.add_argument("--cells-only", action="store_true")
    a = ap.parse_args()
    counts = grid()
    cells = thin(counts, a.minimum)
    if a.cells_only:
        print(" ".join(f"{s}:{p}" for s, p in cells))
        return
    names = [p.name for p in PERSONAS]
    print(f"{'':26} " + " ".join(f"{n[:4]:>4}" for n in names))
    for s in SCENARIOS:
        print(f"{s:26} " + " ".join(f"{counts[(s, n)]:4}" for n in names))
    empty = sum(1 for s in SCENARIOS for n in names if counts[(s, n)] == 0)
    print(f"{empty} of {len(SCENARIOS) * len(names)} cells empty; {len(cells)} below {a.minimum}")


if __name__ == "__main__":
    main()
