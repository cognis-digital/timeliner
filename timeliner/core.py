"""timeliner core — merge heterogeneous CSV/log files into a forensic timeline."""
from __future__ import annotations

import csv
import io
import re
from datetime import datetime

TOOL_NAME = "timeliner"
TOOL_VERSION = "1.0.0"

_TS_PATTERNS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%m/%d/%Y %H:%M:%S",
    "%d/%b/%Y:%H:%M:%S",
]
_TS_RE = re.compile(r"\d{4}[-/]\d{2}[-/]\d{2}[ T]\d{2}:\d{2}:\d{2}")


def parse_ts(s: str) -> datetime | None:
    """Return a datetime for string *s*, or None if no recognisable timestamp."""
    if not s or not s.strip():
        return None
    s = s.strip()
    m = _TS_RE.search(s)
    cand = m.group(0) if m else s
    # Normalise separators and try the canonical format first.
    normalised = cand.replace("T", " ").replace("/", "-")[:19]
    try:
        return datetime.strptime(normalised, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        pass
    # Fall back: try remaining patterns against the original string.
    for fmt in _TS_PATTERNS:
        try:
            return datetime.strptime(s, fmt)
        except (ValueError, TypeError):
            pass
    return None


def from_csv(text: str, source: str) -> list[dict]:
    """Parse *text* as CSV and return a list of normalised event dicts."""
    if not text or not text.strip():
        return []
    rows: list[dict] = []
    try:
        rdr = csv.DictReader(io.StringIO(text))
        for row in rdr:
            if not row:
                continue
            ts = None
            for k in row:
                ts_keys = ("time", "date", "ts", "@timestamp")
                if k and any(t in k.lower() for t in ts_keys):
                    ts = parse_ts(str(row[k] or ""))
                    if ts:
                        break
            rows.append(
                {
                    "ts": ts.isoformat() if ts else None,
                    "source": source,
                    "event": " ".join(
                        f"{k}={v}" for k, v in row.items() if v
                    )[:300],
                }
            )
    except Exception:
        # Unparseable CSV — fall back to line-by-line parsing.
        return from_lines(text, source)
    return rows


def from_lines(text: str, source: str) -> list[dict]:
    """Parse *text* line-by-line and return a list of normalised event dicts."""
    if not text:
        return []
    rows: list[dict] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        ts = parse_ts(line)
        rows.append(
            {
                "ts": ts.isoformat() if ts else None,
                "source": source,
                "event": line.strip()[:300],
            }
        )
    return rows


def _is_csv(text: str) -> bool:
    """Return True when the first non-empty line looks like a CSV row."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return "," in stripped
    return False


def build(files: list[tuple[str, str]]) -> list[dict]:
    """Merge *files* (list of (name, text)) into a sorted forensic timeline.

    Dated events come first, sorted ascending; undated events follow.
    """
    if not files:
        return []
    events: list[dict] = []
    for name, text in files:
        if _is_csv(text):
            events.extend(from_csv(text, name))
        else:
            events.extend(from_lines(text, name))
    dated = [e for e in events if e["ts"]]
    undated = [e for e in events if not e["ts"]]
    dated.sort(key=lambda e: e["ts"])
    return dated + undated
