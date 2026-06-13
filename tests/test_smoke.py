"""Smoke tests for TIMELINER."""
from timeliner.core import build, from_csv, from_lines, parse_ts, TOOL_NAME, TOOL_VERSION


def test_identity():
    assert TOOL_NAME and TOOL_VERSION


def test_parse_ts_iso():
    ts = parse_ts("2024-03-15T10:22:33")
    assert ts is not None
    assert ts.year == 2024 and ts.month == 3 and ts.day == 15


def test_parse_ts_space_sep():
    ts = parse_ts("2024-03-15 10:22:33")
    assert ts is not None
    assert ts.hour == 10


def test_parse_ts_invalid():
    ts = parse_ts("not a timestamp at all")
    assert ts is None


def test_from_lines_basic():
    text = "2024-01-02 03:04:05 server started\n2024-01-02 03:04:10 request received\n"
    rows = from_lines(text, "syslog")
    assert len(rows) == 2
    assert all(r["source"] == "syslog" for r in rows)
    assert rows[0]["ts"] == "2024-01-02T03:04:05"
    assert "server started" in rows[0]["event"]


def test_from_lines_undated():
    text = "no timestamp here\nalso no timestamp\n"
    rows = from_lines(text, "misc")
    assert len(rows) == 2
    assert all(r["ts"] is None for r in rows)


def test_from_csv_basic():
    text = "timestamp,action,user\n2024-06-01 08:00:00,login,alice\n2024-06-01 08:05:00,logout,alice\n"
    rows = from_csv(text, "audit.csv")
    assert len(rows) == 2
    assert rows[0]["ts"] == "2024-06-01T08:00:00"
    assert "action=login" in rows[0]["event"]


def test_build_sorts_by_timestamp():
    log_a = "2024-01-01 09:00:00 event A\n"
    log_b = "2024-01-01 08:00:00 event B\n"
    timeline = build([("a.log", log_a), ("b.log", log_b)])
    # dated events should be sorted; event B (earlier) must come first
    dated = [e for e in timeline if e["ts"]]
    assert len(dated) >= 2
    assert dated[0]["ts"] < dated[1]["ts"]


def test_build_undated_at_end():
    log_dated = "2024-01-01 09:00:00 timed event\n"
    log_undated = "no timestamp line\n"
    timeline = build([("a.log", log_dated), ("b.log", log_undated)])
    assert timeline[0]["ts"] is not None
    assert timeline[-1]["ts"] is None


def test_build_mixed_sources():
    csv_text = "time,msg\n2024-05-01 12:00:00,csv event\n"
    log_text = "2024-05-01 11:00:00 log event\n"
    timeline = build([("events.csv", csv_text), ("app.log", log_text)])
    sources = {e["source"] for e in timeline}
    assert "events.csv" in sources
    assert "app.log" in sources


def test_cli_importable():
    from timeliner.cli import main
    assert callable(main)
