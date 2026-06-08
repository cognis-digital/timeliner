"""timeliner core — merge heterogeneous CSV/log files into a normalized forensic timeline."""
from __future__ import annotations
import csv, io, re, json
from datetime import datetime
TOOL_NAME = "timeliner"; TOOL_VERSION = "1.0.0"

_TS_PATTERNS = [
    "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S",
    "%m/%d/%Y %H:%M:%S", "%d/%b/%Y:%H:%M:%S", "%b %d %H:%M:%S",
]
_TS_RE = re.compile(r"\d{4}[-/]\d{2}[-/]\d{2}[ T]\d{2}:\d{2}:\d{2}")

def parse_ts(s):
    s = s.strip()
    m = _TS_RE.search(s)
    cand = m.group(0) if m else s
    for fmt in _TS_PATTERNS:
        try: return datetime.strptime(cand.replace("T", " ").replace("/", "-")[:19], "%Y-%m-%d %H:%M:%S")
        except Exception: pass
    for fmt in _TS_PATTERNS:
        try: return datetime.strptime(s, fmt)
        except Exception: pass
    return None

def from_csv(text, source):
    rows = []
    rdr = csv.DictReader(io.StringIO(text))
    for row in rdr:
        ts = None
        for k in row:
            if k and any(t in k.lower() for t in ("time", "date", "ts", "@timestamp")):
                ts = parse_ts(str(row[k] or ""))
                if ts: break
        rows.append({"ts": ts.isoformat() if ts else None, "source": source,
                     "event": " ".join(f"{k}={v}" for k, v in row.items() if v)[:300]})
    return rows

def from_lines(text, source):
    rows = []
    for line in text.splitlines():
        if not line.strip(): continue
        ts = parse_ts(line)
        rows.append({"ts": ts.isoformat() if ts else None, "source": source, "event": line.strip()[:300]})
    return rows

def build(files):
    """files: list of (name, text). Returns sorted timeline (events with ts first)."""
    events = []
    for name, text in files:
        events += from_csv(text, name) if ("," in text.splitlines()[0] if text.strip() else False) else from_lines(text, name)
    dated = [e for e in events if e["ts"]]
    undated = [e for e in events if not e["ts"]]
    dated.sort(key=lambda e: e["ts"])
    return dated + undated
