#!/usr/bin/env python3
"""Web UI (standard library only):  python server.py  ->  http://localhost:8000"""
import json, os, tempfile, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from docint.pipeline import analyze

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = open(os.path.join(HERE, "ui.html"), encoding="utf-8").read()


class H(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        b = body if isinstance(body, bytes) else body.encode()
        self.send_response(code); self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path == "/":
            self._send(200, PAGE, "text/html")
        elif self.path == "/api/health":
            self._send(200, json.dumps({"ok": True, "claude": bool(os.environ.get("ANTHROPIC_API_KEY"))}))
        else:
            self._send(404, '{"error":"not found"}')

    def do_POST(self):
        if self.path != "/api/analyze":
            return self._send(404, '{"error":"not found"}')
        n = int(self.headers.get("Content-Length", 0))
        if n > 20 * 1024 * 1024:
            return self._send(413, '{"error":"File larger than 20 MB"}')
        name = os.path.basename(urllib.parse.unquote(self.headers.get("X-Filename", "upload.bin")))
        engine = self.headers.get("X-Engine", "auto")
        questions = json.loads(urllib.parse.unquote(self.headers.get("X-Questions", "[]")))
        data = self.rfile.read(n)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, name)
            with open(path, "wb") as fh:
                fh.write(data)
            try:
                self._send(200, json.dumps(analyze(path, questions, engine), ensure_ascii=False))
            except Exception as e:
                self._send(400, json.dumps({"error": str(e)}))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"DocInt running on http://localhost:{port}  (Claude engine: {'ON' if os.environ.get('ANTHROPIC_API_KEY') else 'OFF - using local engine'})")
    ThreadingHTTPServer(("0.0.0.0", port), H).serve_forever()
