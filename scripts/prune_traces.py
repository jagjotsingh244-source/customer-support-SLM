"""Trace retention: raw traces are kept for 30 days, a redacted copy for a year.

Production traces are written one file per day, as JSON lines, in two folders of a traces directory:

    logs/traces/raw/2026-11-25.jsonl        every message, tool call and result, as it happened
    logs/traces/redacted/2026-11-25.jsonl   the same lines with every string passed through
                                            agent.privacy.redact_obj (phones masked to the last four digits,
                                            card numbers and email addresses replaced)

For each raw file older than --keep-days (by the date in its name, against --today), this script makes sure the
redacted copy exists and has every line (it writes it if not), and only then deletes the raw file. Redacted
files older than --keep-redacted-days are deleted too. Files whose name is not a date are left alone.

It is a dry run unless --apply is given: it prints what it would do and changes nothing.

    uv run python scripts/prune_traces.py                      # dry run on logs/traces
    uv run python scripts/prune_traces.py --apply
    uv run python scripts/prune_traces.py --dir /var/nova/traces --keep-days 30 --today 2026-11-25 --apply

Safety: the directory must be named `traces` or sit inside one, and nothing outside it is read, written or
deleted (symlinks are skipped, and every path is checked after resolving it).
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from agent.privacy import redact, redact_obj  # noqa: E402

DEFAULT_DIR = ROOT / "logs" / "traces"
KEEP_DAYS, KEEP_REDACTED_DAYS = 30, 365
DAY_FILE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.jsonl$")


@dataclass(frozen=True)
class Action:
    kind: str          # "write_redacted", "delete_raw", "delete_redacted"
    path: Path
    note: str = ""

    def __str__(self) -> str:
        return f"{self.kind:16s} {self.path}" + (f"  ({self.note})" if self.note else "")


def check_dir(path: Path) -> Path:
    """The resolved traces directory, or ValueError if it is not one this script may touch."""
    d = Path(path).resolve()
    if "traces" not in d.parts:
        raise ValueError(f"{d} is not a traces directory: it must be named 'traces' or sit inside one")
    if not d.is_dir():
        raise ValueError(f"{d} does not exist or is not a directory")
    return d


def _inside(p: Path, d: Path) -> bool:
    return not p.is_symlink() and p.resolve().is_relative_to(d)


def day_files(folder: Path, base: Path) -> list[tuple[date, Path]]:
    """(date, path) for every YYYY-MM-DD.jsonl regular file directly in `folder`, oldest first."""
    if not folder.is_dir() or not _inside(folder, base):
        return []
    out = []
    for p in folder.iterdir():
        m = DAY_FILE.match(p.name)
        if not m or not p.is_file() or not _inside(p, base):
            continue
        try:
            out.append((date.fromisoformat(m.group(1)), p))
        except ValueError:                           # 2026-13-40.jsonl: not a date, not ours
            continue
    return sorted(out)


def redact_line(line: str) -> str:
    """One trace line as it may be kept: every string inside the JSON redacted; a line that is not JSON is
    redacted as text."""
    try:
        return json.dumps(redact_obj(json.loads(line)), ensure_ascii=False, default=str)
    except json.JSONDecodeError:
        return redact(line)


def write_redacted(raw: Path, dest: Path) -> int:
    """Write the redacted copy of `raw` to `dest` (through a temporary file, so a crash never leaves half a
    copy that looks complete). Returns the number of lines."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".tmp")
    n = 0
    with raw.open(encoding="utf-8") as src, tmp.open("w", encoding="utf-8") as out:
        for line in src:
            line = line.rstrip("\n")
            if line.strip():
                out.write(redact_line(line) + "\n")
                n += 1
    os.replace(tmp, dest)
    return n


def _lines(p: Path) -> int:
    with p.open(encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def plan(traces: Path, today: date, keep_days: int = KEEP_DAYS,
         keep_redacted_days: int = KEEP_REDACTED_DAYS) -> list[Action]:
    """What a run would do, in order. Reads files, changes nothing."""
    d = check_dir(traces)
    raw_dir, red_dir = d / "raw", d / "redacted"
    actions = []
    for day, raw in day_files(raw_dir, d):
        age = (today - day).days
        if age <= keep_days:
            continue
        copy = red_dir / raw.name
        if copy.is_symlink() or (copy.exists() and not _inside(copy, d)):
            raise ValueError(f"{copy} is a link or points outside {d}; not touching it")
        if not copy.exists():
            actions.append(Action("write_redacted", copy, f"from {raw.name}, missing"))
        elif _lines(copy) != _lines(raw):
            actions.append(Action("write_redacted", copy, f"from {raw.name}, line count differs"))
        actions.append(Action("delete_raw", raw, f"{age} days old"))
    for day, red in day_files(red_dir, d):
        age = (today - day).days
        if age > keep_redacted_days:
            actions.append(Action("delete_redacted", red, f"{age} days old"))
    return actions


def apply(actions: list[Action], traces: Path) -> None:
    """Carry out a plan. A raw file is deleted only if its redacted copy now has every one of its lines."""
    d = check_dir(traces)
    for a in actions:
        if not a.path.resolve().is_relative_to(d):
            raise ValueError(f"{a.path} is outside {d}")
        if a.kind == "write_redacted":
            write_redacted(d / "raw" / a.path.name, a.path)
        elif a.kind == "delete_raw":
            copy = d / "redacted" / a.path.name
            if not copy.exists() or _lines(copy) != _lines(a.path):
                raise RuntimeError(f"redacted copy of {a.path.name} is missing or incomplete; raw file kept")
            a.path.unlink()
        elif a.kind == "delete_redacted":
            a.path.unlink()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--dir", type=Path, default=DEFAULT_DIR, help="the traces directory (holds raw/ and redacted/)")
    p.add_argument("--keep-days", type=int, default=KEEP_DAYS, help="days a raw trace file is kept (default 30)")
    p.add_argument("--keep-redacted-days", type=int, default=KEEP_REDACTED_DAYS,
                   help="days a redacted trace file is kept (default 365)")
    p.add_argument("--today", type=date.fromisoformat,
                   default=datetime.now(ZoneInfo("Asia/Kolkata")).date(), help="YYYY-MM-DD (default: today in IST)")
    p.add_argument("--apply", action="store_true", help="make the changes; without it, only print them")
    a = p.parse_args(argv)
    if a.keep_days < 0 or a.keep_redacted_days < a.keep_days:
        p.error("need 0 <= --keep-days <= --keep-redacted-days: the redacted copy must outlive the raw file")
    try:
        actions = plan(a.dir, a.today, a.keep_days, a.keep_redacted_days)
    except ValueError as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    print(f"{'Applying' if a.apply else 'Dry run (nothing changes; --apply to do it)'}: {check_dir(a.dir)}, "
          f"today {a.today}, raw kept {a.keep_days} days, redacted kept {a.keep_redacted_days} days")
    for act in actions:
        print(" ", act)
    if not actions:
        print("  nothing to do")
    if a.apply:
        apply(actions, a.dir)
        print(f"done: {len(actions)} actions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
