from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/mcp/tools":
            self._json({"tools": [{"name": "read_note", "description": "Read demo note", "read_only": True}]})
        elif self.path == "/health":
            self._json({"ok": True})
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.path == "/mcp/tools/read_note":
            self._json({"content": "demo note"})
        else:
            self.send_error(403)

    def _json(self, payload: dict) -> None:
        data = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8083), Handler).serve_forever()

