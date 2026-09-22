from __future__ import annotations

from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from typing import Any

STATIC_DIR = Path(__file__).resolve().parent / "static"


class ResultHub:
    def __init__(self, history: int = 250):
        self._lock = threading.Lock()
        self.latest: dict[str, Any] | None = None
        self.history: deque[dict[str, Any]] = deque(maxlen=history)

    def publish(self, payload: dict[str, Any]) -> None:
        with self._lock:
            self.latest = payload
            self.history.append(payload)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "latest": self.latest,
                "history": list(self.history),
                "disclaimer": "PoC tham khảo — không phải ACC/AEB, không nối phanh/ga.",
            }


def make_handler(hub: ResultHub):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path in {"/", "/index.html"}:
                return self._send(200, "text/html; charset=utf-8", (STATIC_DIR / "dashboard.html").read_bytes())
            if self.path == "/api/latest":
                payload = hub.snapshot()
                return self._send_json(payload["latest"] or {"message": "chưa có frame"})
            if self.path == "/api/history":
                return self._send_json(hub.snapshot())
            self._send(404, "text/plain; charset=utf-8", b"not found")

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

        def _send_json(self, payload: Any) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._send(200, "application/json; charset=utf-8", body)

        def _send(self, status: int, content_type: str, body: bytes) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

    return Handler


def start_dashboard(hub: ResultHub, host: str, port: int) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), make_handler(hub))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
