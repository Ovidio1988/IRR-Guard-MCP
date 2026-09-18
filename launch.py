"""One-command launcher for the talk demo."""
from __future__ import annotations

import threading
import webbrowser
import uvicorn

URL = "http://127.0.0.1:8787"

if __name__ == "__main__":
    threading.Timer(1.1, lambda: webbrowser.open(URL)).start()
    print(f"IRR Guard demo: {URL}")
    print("MCP endpoint: http://127.0.0.1:8787/mcp")
    print("Ctrl+C para detener.")
    uvicorn.run("app:app", host="127.0.0.1", port=8787, reload=False)
