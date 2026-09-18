"""IRR Guard MCP over stdio, dependency-free protocol adapter.

Supports the tools subset used by the demo for MCP 2026-07-28, plus legacy
initialize/tools calls. JSON-RPC messages are one JSON object per line.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

from irr_core import IRRStore
from mcp_tools import TOOLS

BASE = Path(__file__).resolve().parent
store = IRRStore(BASE / "data" / "irr_demo.sqlite3")
SERVER_INFO = {"name": "IRR Guard MCP", "version": "0.1.0"}
INSTRUCTIONS = (
    "IRR traceability layer. Use irr_create_case first and carry irr_id explicitly. "
    "The server does not score judicial performance and does not replace judicial reasoning."
)


def result(req_id: Any, payload: Dict[str, Any], modern: bool) -> Dict[str, Any]:
    if modern:
        payload.setdefault("resultType", "complete")
        payload.setdefault("_meta", {"io.modelcontextprotocol/serverInfo": SERVER_INFO})
    return {"jsonrpc": "2.0", "id": req_id, "result": payload}


def dispatch(message: Dict[str, Any]) -> Dict[str, Any] | None:
    req_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}
    meta = params.get("_meta") or {}
    modern = method == "server/discover" or meta.get("io.modelcontextprotocol/protocolVersion") == "2026-07-28"

    if method == "notifications/initialized":
        return None
    if method == "server/discover":
        return result(req_id, {
            "supportedVersions": ["2026-07-28", "2025-06-18"],
            "capabilities": {"tools": {}},
            "instructions": INSTRUCTIONS,
            "ttlMs": 300000,
            "cacheScope": "private",
        }, True)
    if method == "initialize":
        return result(req_id, {
            "protocolVersion": "2025-06-18",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
            "instructions": INSTRUCTIONS,
        }, False)
    if method == "tools/list":
        payload: Dict[str, Any] = {"tools": TOOLS}
        if modern:
            payload.update({"ttlMs": 300000, "cacheScope": "private"})
        return result(req_id, payload, modern)
    if method == "tools/call":
        try:
            data = store.process_tool(params.get("name"), dict(params.get("arguments") or {}))
            return result(req_id, {
                "content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}],
                "structuredContent": data,
                "isError": False,
            }, modern)
        except Exception as exc:
            return result(req_id, {
                "content": [{"type": "text", "text": f"Error de ejecución: {exc}"}],
                "isError": True,
            }, modern)
    return {"jsonrpc":"2.0","id":req_id,"error":{"code":-32601,"message":f"Method not found: {method}"}}


def main() -> None:
    for line in sys.stdin:
        line=line.strip()
        if not line:
            continue
        try:
            message=json.loads(line)
            response=dispatch(message)
            if response is not None:
                sys.stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
                sys.stdout.flush()
        except Exception as exc:
            sys.stdout.write(json.dumps({"jsonrpc":"2.0","id":None,"error":{"code":-32603,"message":str(exc)}}, ensure_ascii=False) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
