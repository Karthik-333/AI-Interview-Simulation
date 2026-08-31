"""MCP server for AI Interview Simulation.

Tries to use the official `mcp` SDK (FastMCP) if available; otherwise exposes
the same tools via plain functions for REST fallback. Run with stdio:

    python -m app.mcp.server

Or import `mcp_server` to embed.
"""
from typing import Any

from app.mcp.tools import TOOL_REGISTRY

# --- Try native MCP (model-context-protocol) -------------------------------------------------
try:
    from mcp.server.fastmcp import FastMCP  # type: ignore

    mcp_server = FastMCP("AI Interview Simulation")

    for name, meta in TOOL_REGISTRY.items():
        # register each tool dynamically
        mcp_server.tool(name=name, description=meta["description"])(meta["fn"])

    def run_stdio():
        mcp_server.run(transport="stdio")

except ImportError:  # pragma: no cover - lightweight fallback when mcp not installed
    mcp_server = None  # type: ignore

    def run_stdio():  # type: ignore
        # Fallback: simple REPL for manual testing without mcp SDK
        import json
        import sys

        print(json.dumps({"tools": list(TOOL_REGISTRY.keys())}))
        for line in sys.stdin:
            try:
                req = json.loads(line)
                tool = req.get("tool")
                args = req.get("arguments", {})
                fn = TOOL_REGISTRY[tool]["fn"]
                result = fn(**args)
                print(json.dumps({"result": result}))
            except Exception as exc:
                print(json.dumps({"error": str(exc)}))
            sys.stdout.flush()


# --- Helpers for REST API -------------------------------------------------------------------
def list_tools() -> list[dict[str, Any]]:
    return [
        {"name": name, "description": meta["description"], "input_schema": meta["input_schema"]}
        for name, meta in TOOL_REGISTRY.items()
    ]


def call_tool(name: str, arguments: dict[str, Any]) -> Any:
    if name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {name}")
    return TOOL_REGISTRY[name]["fn"](**arguments)


if __name__ == "__main__":
    run_stdio()
