#!/usr/bin/env python3
"""Count five editorial events without visitor identifiers. Not a conversion feed.

Deploy separately from GitHub Pages, behind HTTPS and a request-limiting proxy
with access logs disabled. See README.md. No endpoint is enabled by this file.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVENT_NAMES = frozenset({"page_view", "outbound_click", "guide_read_75", "category_click", "feed_click"})
DEFAULT_ORIGIN = "https://kanlerxz87-cyber.github.io"
MAX_BODY = 512
RETENTION_DAYS = 90
_lock = threading.Lock()


def published_paths() -> frozenset[str]:
    """Bound the counter to published pages; arbitrary paths may contain personal data."""
    paths = set()
    for page in (ROOT / "docs").rglob("*.html"):
        path = "/Zone4/docs/" + page.relative_to(ROOT / "docs").as_posix()
        paths.add(path)
        if path.endswith("/index.html"):
            paths.add(path[:-10])
    return frozenset(paths)


PUBLISHED_PATHS = published_paths()
PRODUCT_ASINS = frozenset(
    item["intended_asin"]
    for item in json.loads((ROOT / "data/intent-links.json").read_text())["links"]
)
CATEGORY_TARGETS = frozenset(
    p.stem for p in (ROOT / "docs/categories").glob("*.html")
)


def validate(payload: object) -> tuple[bool, str]:
    """Validate types before membership tests. Never accept free-text dimensions."""
    if not isinstance(payload, dict):
        return False, "body must be an object"
    event = payload.get("event")
    if not isinstance(event, str) or event not in EVENT_NAMES:
        return False, "unknown event"
    allowed = {"event", "path"}
    if event == "outbound_click":
        allowed.add("asin")
    if event == "category_click":
        allowed.add("target")
    if set(payload) - allowed:
        return False, "unexpected field"
    path = payload.get("path")
    if not isinstance(path, str) or path not in PUBLISHED_PATHS:
        return False, "unpublished path"
    if event == "outbound_click":
        asin = payload.get("asin")
        if not isinstance(asin, str) or asin not in PRODUCT_ASINS:
            return False, "unknown product"
    if event == "category_click":
        target = payload.get("target")
        if not isinstance(target, str) or target not in CATEGORY_TARGETS:
            return False, "unknown category"
    return True, ""


def _pruned(data: dict, today: str) -> dict:
    end = dt.date.fromisoformat(today)
    start = end - dt.timedelta(days=RETENTION_DAYS - 1)
    return {day: value for day, value in data.items() if start.isoformat() <= day <= today}


def _write(counts_file: pathlib.Path, data: dict) -> None:
    counts_file.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(counts_file.parent), prefix=".counts-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
        os.replace(tmp, counts_file)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def record(counts_file: pathlib.Path, payload: dict | None, today: str | None = None) -> None:
    """Validate, increment daily aggregate counts and prune. None means prune only."""
    if payload is not None and not validate(payload)[0]:
        raise ValueError("invalid event")
    day = today or dt.datetime.now(dt.timezone.utc).date().isoformat()
    with _lock:
        data = json.loads(counts_file.read_text(encoding="utf-8")) if counts_file.exists() else {}
        data = _pruned(data, day)
        if payload is not None:
            bucket = data.setdefault(day, {})
            by_path = bucket.setdefault(payload["event"], {})
            by_path[payload["path"]] = by_path.get(payload["path"], 0) + 1
            if payload["event"] == "outbound_click":
                by_asin = bucket.setdefault("outbound_click_asin", {})
                by_asin[payload["asin"]] = by_asin.get(payload["asin"], 0) + 1
            if payload["event"] == "category_click":
                by_target = bucket.setdefault("category_click_target", {})
                by_target[payload["target"]] = by_target.get(payload["target"], 0) + 1
        _write(counts_file, data)


def make_handler(counts_file: pathlib.Path, allowed_origin: str):
    class Handler(BaseHTTPRequestHandler):
        server_version = "zone4-measure"
        sys_version = ""
        timeout = 5

        def log_message(self, format, *args):
            return  # no client addresses or request payloads in application logs

        def _send(self, code: int) -> None:
            self.send_response(code)
            if self.headers.get("Origin") == allowed_origin:
                self.send_header("Access-Control-Allow-Origin", allowed_origin)
                self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Vary", "Origin")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_OPTIONS(self):
            self._send(404 if self.path != "/event" else
                       204 if self.headers.get("Origin") == allowed_origin else 403)

        def do_GET(self):
            self._send(204 if self.path == "/health" else 404)

        def do_POST(self):
            if self.path != "/event":
                self._send(404)
                return
            # CORS headers alone do not prevent cross-origin writes.
            if self.headers.get("Origin") != allowed_origin:
                self._send(403)
                return
            if self.headers.get_content_type() not in ("application/json", "text/plain"):
                self._send(415)
                return
            if self.headers.get("Transfer-Encoding"):
                self._send(400)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._send(400)
                return
            if length <= 0 or length > MAX_BODY:
                self._send(413 if length > MAX_BODY else 400)
                return
            try:
                raw = self.rfile.read(length)
                if len(raw) != length:
                    self._send(400)
                    return
                payload = json.loads(raw.decode("utf-8"))
            except (TimeoutError, UnicodeDecodeError, json.JSONDecodeError, RecursionError):
                self._send(400)
                return
            if not validate(payload)[0]:
                self._send(400)
                return
            try:
                record(counts_file, payload)
            except (OSError, ValueError, TypeError, AttributeError):
                self._send(503)  # do not disclose storage paths or corrupt data
                return
            self._send(204)

    return Handler


def serve(host: str, port: int, counts_file: pathlib.Path, allowed_origin: str) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(counts_file, allowed_origin))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--counts", default=str(pathlib.Path(__file__).parent / "counts.json"))
    ap.add_argument("--origin", default=os.environ.get("ZONE4_ALLOWED_ORIGIN", DEFAULT_ORIGIN))
    ap.add_argument("--prune-only", action="store_true", help="Schedule daily, including days with no events")
    args = ap.parse_args()
    counts = pathlib.Path(args.counts)
    record(counts, None)
    if args.prune_only:
        return
    srv = serve(args.host, args.port, counts, args.origin)
    print(f"listening on {args.host}:{args.port}; aggregate retention {RETENTION_DAYS} days", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
