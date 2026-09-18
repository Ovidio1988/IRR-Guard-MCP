from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from irr_core import IRRStore
from mcp_tools import TOOLS

BASE = Path(__file__).resolve().parent
store = IRRStore(BASE / "data" / "irr_demo.sqlite3")
app = FastAPI(title="IRR Guard MCP Demo", version="0.1.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

SERVER_INFO = {"name": "IRR Guard MCP", "version": "0.1.0"}
INSTRUCTIONS = (
    "Capa de trazabilidad IRR para asistencia judicial. No evalúa la competencia del juez, "
    "no usa tiempos/clics como métricas y no sustituye la motivación de la resolución. "
    "Use irr_create_case y conserve el irr_id para las llamadas posteriores."
)


def modern_meta() -> Dict[str, Any]:
    return {"io.modelcontextprotocol/serverInfo": SERVER_INFO}


def mcp_result(req_id: Any, result: Dict[str, Any], modern: bool) -> JSONResponse:
    if modern:
        result.setdefault("resultType", "complete")
        result.setdefault("_meta", modern_meta())
    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": result})


def mcp_error(req_id: Any, code: int, message: str, data: Any = None) -> JSONResponse:
    error: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return JSONResponse({"jsonrpc": "2.0", "id": req_id, "error": error}, status_code=200)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(BASE / "static" / "index.html")


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "service": SERVER_INFO, "mcp": "/mcp", "wizard": "/"}


@app.post("/api/cases")
async def api_create_case(request: Request) -> Dict[str, Any]:
    body = await request.json()
    try:
        return store.create_case(**body)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@app.get("/api/cases/{irr_id}")
def api_get_case(irr_id: str) -> Dict[str, Any]:
    try:
        return store.get_case(irr_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc


@app.post("/api/cases/{irr_id}/assistance")
async def api_assistance(irr_id: str, request: Request) -> Dict[str, Any]:
    body = await request.json()
    try:
        return store.register_assistance(irr_id=irr_id, **body)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/cases/{irr_id}/materiality")
async def api_materiality(irr_id: str, request: Request) -> Dict[str, Any]:
    body = await request.json()
    try:
        return store.set_materiality(irr_id, body.get("factors", {}), body.get("domain"))
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/cases/{irr_id}/sources")
async def api_source(irr_id: str, request: Request) -> Dict[str, Any]:
    body = await request.json()
    try:
        return store.check_source(irr_id=irr_id, **body)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/cases/{irr_id}/alerts")
async def api_alert(irr_id: str, request: Request) -> Dict[str, Any]:
    body = await request.json()
    try:
        return store.register_alert(irr_id=irr_id, **body)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/cases/{irr_id}/alerts/{alert_id}/resolve")
async def api_resolve_alert(irr_id: str, alert_id: str, request: Request) -> Dict[str, Any]:
    body = await request.json()
    try:
        return store.resolve_alert(irr_id=irr_id, alert_id=alert_id, **body)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/cases/{irr_id}/ratification")
async def api_ratification(irr_id: str, request: Request) -> Dict[str, Any]:
    body = await request.json()
    try:
        return store.set_ratification(irr_id, body)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/api/cases/{irr_id}/close")
def api_close(irr_id: str) -> Dict[str, Any]:
    try:
        result = store.close(irr_id)
        return {"closed": result.closed, "blockers": result.blockers, "report": result.report}
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc


@app.post("/mcp")
async def mcp_endpoint(request: Request) -> Response:
    """Small self-contained MCP HTTP implementation for the demo.

    Implements the tools subset for current 2026-07-28 stateless requests plus
    the 2025-06-18 initialization flow for compatibility. Production deployment
    should switch to the official MCP SDK and add institutional authentication.
    """
    try:
        message = await request.json()
    except Exception:
        return mcp_error(None, -32700, "Parse error")

    req_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}
    protocol_header = request.headers.get("MCP-Protocol-Version", "")
    modern = protocol_header == "2026-07-28" or method == "server/discover" or "io.modelcontextprotocol/protocolVersion" in (params.get("_meta") or {})

    # Legacy notification: no JSON-RPC response body.
    if method == "notifications/initialized":
        return Response(status_code=202)

    if method == "server/discover":
        result = {
            "supportedVersions": ["2026-07-28", "2025-06-18"],
            "capabilities": {"tools": {}},
            "instructions": INSTRUCTIONS,
            "ttlMs": 300000,
            "cacheScope": "private",
        }
        return mcp_result(req_id, result, modern=True)

    if method == "initialize":
        return mcp_result(
            req_id,
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": SERVER_INFO,
                "instructions": INSTRUCTIONS,
            },
            modern=False,
        )

    if method == "tools/list":
        result: Dict[str, Any] = {"tools": TOOLS}
        if modern:
            result.update({"ttlMs": 300000, "cacheScope": "private"})
        return mcp_result(req_id, result, modern=modern)

    if method == "tools/call":
        name = params.get("name")
        arguments = dict(params.get("arguments") or {})
        try:
            payload = store.process_tool(name, arguments)
            text = json.dumps(payload, ensure_ascii=False, indent=2)
            result = {
                "content": [{"type": "text", "text": text}],
                "structuredContent": payload,
                "isError": False,
            }
            return mcp_result(req_id, result, modern=modern)
        except KeyError as exc:
            return mcp_result(
                req_id,
                {"content": [{"type": "text", "text": str(exc)}], "isError": True},
                modern=modern,
            )
        except Exception as exc:
            return mcp_result(
                req_id,
                {"content": [{"type": "text", "text": f"Error de ejecución: {exc}"}], "isError": True},
                modern=modern,
            )

    return mcp_error(req_id, -32601, f"Method not found: {method}")
