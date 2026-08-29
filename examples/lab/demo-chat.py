from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self._json({"ok": True})
            return
        self.send_error(404)

    def do_POST(self) -> None:
        length = int(self.headers.get("content-length", "0"))
        json.loads(self.rfile.read(length) or b"{}")
        text = "AEGISFORGE_OK"
        if self.path == "/v1/chat/completions":
            self._json({"choices": [{"message": {"role": "assistant", "content": text}}]})
        elif self.path == "/v1/responses":
            self._json({"output_text": text, "output": [{"content": [{"type": "output_text", "text": text}]}]})
        else:
            self.send_error(404)

    def _json(self, payload: dict) -> None:
        data = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8081), Handler).serve_forever()
