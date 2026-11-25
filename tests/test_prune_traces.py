"""Trace retention (scripts/prune_traces.py): raw files go after 30 days, only once a redacted copy exists.

    uv run --group dev pytest tests/test_prune_traces.py
"""

import json
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent.privacy import redact_obj  # noqa: E402
from scripts import prune_traces as pt  # noqa: E402

TODAY = date(2026, 11, 25)
OLD, RECENT, ANCIENT = "2026-10-01", "2026-11-20", "2025-10-01"     # 55, 5 and 420 days before TODAY
LINES = [
    {"id": "esc-004-1", "messages": [{"role": "user", "content": "call me on 9876543210 or +91 98765 43210"}],
     "reply": "I've opened ticket 900003 for order 11942.", "latency_s": 1.2},
    {"id": "ret-013-1", "messages": [{"role": "user", "content": "my card 4111 1111 1111 1111, mail asha.k@gmail.com"}],
     "result": {"refunds": [{"amount_inr": "1299.00", "status": "awaiting_bank_details"}]}},
]


@pytest.fixture
def traces(tmp_path):
    d = tmp_path / "logs" / "traces"
    (d / "raw").mkdir(parents=True)
    (d / "redacted").mkdir()
    for day in (OLD, RECENT):
        (d / "raw" / f"{day}.jsonl").write_text("".join(json.dumps(x) + "\n" for x in LINES))
    return d


def files(d: Path) -> set[str]:
    return {str(p.relative_to(d)) for p in d.rglob("*") if p.is_file()}


def test_dry_run_changes_nothing(traces, capsys):
    before = {p: p.read_bytes() for p in traces.rglob("*") if p.is_file()}
    assert pt.main(["--dir", str(traces), "--today", str(TODAY)]) == 0
    assert {p: p.read_bytes() for p in traces.rglob("*") if p.is_file()} == before
    out = capsys.readouterr().out
    assert "Dry run" in out and f"raw/{OLD}.jsonl" in out and f"raw/{RECENT}.jsonl" not in out


def test_old_raw_is_deleted_after_its_redacted_copy_is_written(traces):
    assert pt.main(["--dir", str(traces), "--today", str(TODAY), "--apply"]) == 0
    assert files(traces) == {f"raw/{RECENT}.jsonl", f"redacted/{OLD}.jsonl"}
    kept = [json.loads(line) for line in (traces / "redacted" / f"{OLD}.jsonl").read_text().splitlines()]
    assert kept == [redact_obj(x) for x in LINES]


def test_redacted_copy_has_phones_masked_and_cards_and_emails_removed(traces):
    pt.main(["--dir", str(traces), "--today", str(TODAY), "--apply"])
    text = (traces / "redacted" / f"{OLD}.jsonl").read_text()
    assert "9876543210" not in text and "98765 43210" not in text and "••••••3210" in text
    assert "4111" not in text and "[card]" in text
    assert "asha.k@gmail.com" not in text and "[email]" in text
    assert "11942" in text and "900003" in text and "1299.00" in text      # order facts stay


def test_recent_raw_is_kept(traces):
    pt.main(["--dir", str(traces), "--today", str(TODAY), "--apply"])
    assert (traces / "raw" / f"{RECENT}.jsonl").read_text().count("9876543210") == 1
    assert not (traces / "redacted" / f"{RECENT}.jsonl").exists()


def test_a_complete_redacted_copy_is_not_rewritten(traces):
    copy = traces / "redacted" / f"{OLD}.jsonl"
    copy.write_text('{"kept": 1}\n{"kept": 2}\n')                         # same line count as the raw file
    actions = pt.plan(traces, TODAY)
    assert [a.kind for a in actions] == ["delete_raw"]
    pt.apply(actions, traces)
    assert copy.read_text() == '{"kept": 1}\n{"kept": 2}\n'


def test_an_incomplete_redacted_copy_is_rewritten_before_the_raw_goes(traces):
    (traces / "redacted" / f"{OLD}.jsonl").write_text('{"half": 1}\n')
    assert [a.kind for a in pt.plan(traces, TODAY)] == ["write_redacted", "delete_raw"]
    pt.main(["--dir", str(traces), "--today", str(TODAY), "--apply"])
    assert len((traces / "redacted" / f"{OLD}.jsonl").read_text().splitlines()) == len(LINES)


def test_redacted_files_go_after_a_year(traces):
    (traces / "redacted" / f"{ANCIENT}.jsonl").write_text('{"x": 1}\n')
    pt.main(["--dir", str(traces), "--today", str(TODAY), "--apply"])
    assert not (traces / "redacted" / f"{ANCIENT}.jsonl").exists()
    assert (traces / "redacted" / f"{OLD}.jsonl").exists()


def test_files_not_named_by_date_are_left_alone(traces):
    for name in ("notes.txt", "2026-01-01.json", "2026-13-40.jsonl", "old.jsonl"):
        (traces / "raw" / name).write_text("x 9876543210\n")
    pt.main(["--dir", str(traces), "--today", str(TODAY), "--apply"])
    for name in ("notes.txt", "2026-01-01.json", "2026-13-40.jsonl", "old.jsonl"):
        assert (traces / "raw" / name).exists()


def test_a_link_to_a_file_outside_is_not_followed(traces, tmp_path):
    outside = tmp_path / "elsewhere.jsonl"
    outside.write_text('{"keep": "me"}\n')
    (traces / "raw" / "2026-09-01.jsonl").symlink_to(outside)
    pt.main(["--dir", str(traces), "--today", str(TODAY), "--apply"])
    assert outside.read_text() == '{"keep": "me"}\n'
    assert (traces / "raw" / "2026-09-01.jsonl").is_symlink()


@pytest.mark.parametrize("sub", ["logs", "logs/tracesX", "elsewhere"])
def test_a_directory_not_named_traces_is_refused(tmp_path, sub, capsys):
    d = tmp_path / sub
    (d / "raw").mkdir(parents=True)
    (d / "raw" / f"{OLD}.jsonl").write_text('{"x": 1}\n')
    assert pt.main(["--dir", str(d), "--today", str(TODAY), "--apply"]) == 2
    assert "refused" in capsys.readouterr().err
    assert (d / "raw" / f"{OLD}.jsonl").exists()
    with pytest.raises(ValueError):
        pt.check_dir(d)


def test_a_missing_directory_is_refused(tmp_path):
    with pytest.raises(ValueError):
        pt.check_dir(tmp_path / "traces")


def test_redacted_must_outlive_raw(traces):
    with pytest.raises(SystemExit):
        pt.main(["--dir", str(traces), "--keep-days", "400", "--keep-redacted-days", "365"])
