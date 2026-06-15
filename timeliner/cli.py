"""timeliner CLI."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from timeliner.core import TOOL_NAME, TOOL_VERSION, build


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="timeliner",
        description="Merge logs/CSVs into one forensic super-timeline.",
    )
    ap.add_argument(
        "--version", action="version", version=f"{TOOL_NAME} {TOOL_VERSION}"
    )
    ap.add_argument("files", nargs="+", help="Log/CSV files to merge")
    ap.add_argument("--format", choices=["table", "json"], default="table")
    a = ap.parse_args(argv)

    # Validate that every supplied path exists and is a file before reading.
    paths = [Path(f) for f in a.files]
    missing = [p for p in paths if not p.exists()]
    if missing:
        for p in missing:
            print(f"timeliner: file not found: {p}", file=sys.stderr)
        return 2

    not_files = [p for p in paths if not p.is_file()]
    if not_files:
        for p in not_files:
            print(f"timeliner: not a regular file: {p}", file=sys.stderr)
        return 2

    try:
        file_pairs = [
            (p.name, p.read_text(encoding="utf-8", errors="replace"))
            for p in paths
        ]
    except OSError as exc:
        print(f"timeliner: error reading file: {exc}", file=sys.stderr)
        return 2

    try:
        tl = build(file_pairs)
    except Exception as exc:  # pragma: no cover — defensive fallback
        print(f"timeliner: unexpected error building timeline: {exc}", file=sys.stderr)
        return 1

    if a.format == "json":
        print(json.dumps(tl, indent=2))
        return 0

    for e in tl[:500]:
        print(f"{e['ts'] or '(undated)':<20} [{e['source']}] {e['event']}")
    print(f"\n{TOOL_NAME}: {len(tl)} events from {len(a.files)} sources")
    return 0


if __name__ == "__main__":
    sys.exit(main())
