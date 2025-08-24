"""TIMELINER MCP server — exposes scan() as an MCP tool for Cognis.Studio."""
from __future__ import annotations
from timeliner.core import scan, to_json

def serve() -> int:
    """Start an MCP stdio server. Requires the optional 'mcp' extra:
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
        """Build a forensic super-timeline by merging & normalizing log/artifact CSVs. Returns JSON findings."""
        return to_json(scan(target))

    app.run()
    return 0
