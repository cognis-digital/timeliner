"""Hardening tests: error handling, edge cases, and validation paths."""
from __future__ import annotations

from timeliner.core import (
    build,
    from_csv,
    from_lines,
    parse_ts,
    _is_csv,
)
from timeliner.cli import main


# ---------------------------------------------------------------------------
# parse_ts edge cases
# ---------------------------------------------------------------------------


def test_parse_ts_none_input():
    """parse_ts must return None for None-like / empty inputs."""
    assert parse_ts("") is None
    assert parse_ts("   ") is None


def test_parse_ts_garbage_string():
    assert parse_ts("not a date at all !!!") is None


# ---------------------------------------------------------------------------
# from_csv edge cases
# ---------------------------------------------------------------------------


def test_from_csv_empty_string():
    assert from_csv("", "x.csv") == []


def test_from_csv_whitespace_only():
    assert from_csv("   \n  \t  ", "x.csv") == []


def test_from_csv_header_only():
    """A CSV with a header but no data rows returns an empty list."""
    result = from_csv("timestamp,action,user\n", "audit.csv")
    assert result == []


def test_from_csv_missing_timestamp_column():
    """CSV with no recognised timestamp column still parses; ts is None."""
    text = "action,user\nlogin,alice\nlogout,alice\n"
    rows = from_csv(text, "no_ts.csv")
    assert len(rows) == 2
    assert all(r["ts"] is None for r in rows)
    assert all(r["source"] == "no_ts.csv" for r in rows)


# ---------------------------------------------------------------------------
# from_lines edge cases
# ---------------------------------------------------------------------------


def test_from_lines_empty_string():
    assert from_lines("", "x.log") == []


def test_from_lines_blank_lines_only():
    assert from_lines("\n\n\n", "x.log") == []


def test_from_lines_long_line_truncated():
    """Lines longer than 300 chars must be truncated in the event field."""
    long = "2024-01-01 10:00:00 " + "X" * 500
    rows = from_lines(long, "big.log")
    assert len(rows) == 1
    assert len(rows[0]["event"]) <= 300


# ---------------------------------------------------------------------------
# build() edge cases
# ---------------------------------------------------------------------------


def test_build_empty_files_list():
    """build() with no files must return an empty list without raising."""
    assert build([]) == []


def test_build_all_empty_texts():
    result = build([("a.log", ""), ("b.csv", "   ")])
    assert result == []


def test_build_single_undated_entry():
    result = build([("x.log", "no timestamps here at all\n")])
    assert len(result) == 1
    assert result[0]["ts"] is None


def test_build_csv_vs_lines_detection():
    """_is_csv helper correctly distinguishes CSV from plain-text logs."""
    assert _is_csv("timestamp,action\n2024-01-01 10:00:00,login\n") is True
    assert _is_csv("2024-01-01 10:00:00 plain log line\n") is False
    assert _is_csv("") is False
    assert _is_csv("   \n   ") is False


# ---------------------------------------------------------------------------
# CLI error paths
# ---------------------------------------------------------------------------


def test_cli_missing_file_returns_exit_2():
    """CLI must exit with code 2 and print to stderr when a file is missing."""
    code = main(["this_file_does_not_exist_xyz.log"])
    assert code == 2


def test_cli_missing_file_message(capsys):
    """CLI must print a human-readable error to stderr for a missing file."""
    main(["ghost_file.log"])
    captured = capsys.readouterr()
    assert "ghost_file.log" in captured.err
    assert captured.out == ""


def test_cli_directory_not_a_file_returns_exit_2(tmp_path):
    """Passing a directory instead of a file must exit with code 2."""
    code = main([str(tmp_path)])
    assert code == 2


def test_cli_valid_file_roundtrip(tmp_path):
    """CLI must succeed (exit 0) and produce output for a valid log file."""
    log = tmp_path / "test.log"
    log.write_text("2024-01-01 09:00:00 startup\n2024-01-01 09:01:00 ready\n")
    code = main([str(log)])
    assert code == 0


def test_cli_json_format_valid(tmp_path, capsys):
    """--format json must emit parseable JSON and exit 0."""
    import json

    log = tmp_path / "test.log"
    log.write_text("2024-03-01 12:00:00 event one\n")
    code = main([str(log), "--format", "json"])
    assert code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) == 1
