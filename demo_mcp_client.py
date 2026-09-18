"""Minimal current-MCP smoke client using only stdlib; useful without installing the MCP SDK."""
import json
import urllib.request

URL = "http://127.0.0.1:8787/mcp"

def call(method, params=None, req_id=1, headers=None):
    body = json.dumps({"jsonrpc":"2.0","id":req_id,"method":method,"params":params or {}}).encode()
    h={"Content-Type":"application/json","Accept":"application/json","MCP-Protocol-Version":"2026-07-28","Mcp-Method":method}
    if headers: h.update(headers)
    req=urllib.request.Request(URL,data=body,headers=h,method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

meta={"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientInfo":{"name":"irr-smoke","version":"0.1"},"io.modelcontextprotocol/clientCapabilities":{}}}
print(json.dumps(call("server/discover",meta,1),ensure_ascii=False,indent=2))
print(json.dumps(call("tools/list",meta,2),ensure_ascii=False,indent=2))
