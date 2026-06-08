"""timeliner CLI."""
import argparse, json, sys
from pathlib import Path
from timeliner.core import build, TOOL_NAME, TOOL_VERSION
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="timeliner", description="Merge logs/CSVs into one forensic super-timeline.")
    ap.add_argument("--version", action="version", version=f"{TOOL_NAME} {TOOL_VERSION}")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--format", choices=["table", "json"], default="table")
    a = ap.parse_args(argv)
    tl = build([(Path(f).name, Path(f).read_text(encoding="utf-8", errors="ignore")) for f in a.files])
    if a.format == "json": print(json.dumps(tl, indent=2)); return 0
    for e in tl[:500]:
        print(f"{e['ts'] or '(undated)':<20} [{e['source']}] {e['event']}")
    print(f"\n{TOOL_NAME}: {len(tl)} events from {len(a.files)} sources")
    return 0
if __name__ == "__main__": sys.exit(main())
