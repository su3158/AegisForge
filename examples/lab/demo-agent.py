from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOOLS = [{"name": "status", "read_only": True}, {"name": "reset", "read_only": False}]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/tools":
            self._json({"tools": TOOLS})
        elif self.path == "/health":
            self._json({"ok": True})
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.path == "/tools/status":
            self._json({"status": "ok"})
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
    ThreadingHTTPServer(("127.0.0.1", 8082), Handler).serve_forever()

