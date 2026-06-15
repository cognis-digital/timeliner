"""TIMELINER MCP server — exposes timeline building as an MCP tool for Cognis.Studio."""
from __future__ import annotations

import json
from pathlib import Path

from timeliner.core import build


def serve() -> int:
    """Start an MCP stdio server.

    Requires the optional 'mcp' extra:
        pip install "cognis-timeliner[mcp]"
    """
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception:
        print("Install the MCP extra: pip install 'cognis-timeliner[mcp]'")
        return 1

    app = FastMCP("timeliner")

    @app.tool()
    def timeliner_scan(target: str) -> str:
        """Build a forensic super-timeline from a file or directory of logs/CSVs.

        Returns JSON findings.
        """
        target_path = Path(target)
        if not target_path.exists():
            return json.dumps({"error": f"path not found: {target}"})
        if target_path.is_dir():
            candidates = [
                p for p in target_path.rglob("*")
                if p.is_file() and p.suffix in {".csv", ".log", ".txt", ""}
            ]
        else:
            candidates = [target_path]
        if not candidates:
            return json.dumps({"error": "no log/CSV files found", "target": target})
        file_pairs = [
            (p.name, p.read_text(encoding="utf-8", errors="replace"))
            for p in candidates
        ]
        return json.dumps(build(file_pairs), indent=2)

    app.run()
    return 0
