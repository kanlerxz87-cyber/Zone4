#!/usr/bin/env python3
"""Reference collector for Zone4's five aggregate-only reader counters.

Not a production web server: Python's http.server is a local/reference runtime.
Production collection stays disabled in data/measurement.json until hosting,
HTTPS, privacy, retention and deployment evidence pass the launch checklist.
The transport/hosting layer still receives connection metadata; only this
application's stored data and request logging are controlled here.

Run locally: python3 analytics-endpoint/server.py --port 8787
Prune only:  python3 analytics-endpoint/server.py --prune-only
Standard library only. Counts and temporary files must never be committed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import tempfile
import threading
import time
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parent.parent
SETTINGS = json.loads((ROOT / "data/measurement.json").read_text(encoding="utf-8"))
SITE = urlsplit(SETTINGS["site_url"])
DEFAULT_ORIGIN = f"{SITE.scheme}://{SITE.netloc}"
EVENT_NAMES = frozenset({"page_view", "outbound_click", "guide_read_75", "category_click", "feed_click"})
PATH_RE = re.compile(r"/[A-Za-z0-9._~/\-]{0,200}")
ASIN_RE = re.compile(r"B[0-9A-Z]{9}")
MAX_BODY = 512
RETENTION_DAYS = SETTINGS["retention_days"]
if type(RETENTION_DAYS) is not int or not 1 <= RETENTION_DAYS <= 90:
    raise ValueError("measurement.retention_days must be an integer from 1 to 90")

# Fixed public routes from the shipped sitemap bound storage cardinality. Never
# retain arbitrary user-entered paths, IDs, URLs, query strings or category names.
_NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
ALLOWED_PATHS = frozenset(
    parsed.path
    for loc in ET.parse(ROOT / "docs/sitemap.xml").findall("s:url/s:loc", _NS)
    if loc.text
    for parsed in [urlsplit(loc.text)]
    if parsed.scheme == SITE.scheme and parsed.netloc == SITE.netloc
    and parsed.path.startswith(SITE.path) and parsed.path.endswith(".html")
    and not parsed.query and not parsed.fragment
)
if not ALLOWED_PATHS:
    raise ValueError("collector needs a nonempty, built sitemap")
CATEGORY_PATHS = frozenset(p for p in ALLOWED_PATHS if p.startswith(SITE.path + "categories/"))
GUIDE_PATHS = frozenset(p for p in ALLOWED_PATHS
                        if p.startswith((SITE.path + "guides/", SITE.path + "articles/"))
                        and not p.endswith("/index.html"))
KNOWN_ASINS = frozenset(
    link["intended_asin"]
    for link in json.loads((ROOT / "data/intent-links.json").read_text(encoding="utf-8"))["links"]
    if link.get("published_outbound_url")
)
DIMENSIONS = {name: ALLOWED_PATHS for name in EVENT_NAMES}
DIMENSIONS["guide_read_75"] = GUIDE_PATHS
DIMENSIONS["outbound_click_asin"] = KNOWN_ASINS
DIMENSIONS["category_click_target"] = CATEGORY_PATHS
_lock = threading.Lock()  # one process, multiple request threads; not a distributed datastore


def validate(payload: object) -> tuple[bool, str]:
    """Exactly one event's bounded schema. Unknown fields are refused, not retained."""
    if not isinstance(payload, dict):
        return False, "body must be a JSON object"
    event = payload.get("event")
    if not isinstance(event, str) or event not in EVENT_NAMES:
        return False, "unknown event"
    expected = {"event", "path"}
    if event == "outbound_click":
        expected.add("asin")
    if event == "category_click":
        expected.add("target")
    if set(payload) != expected:
        return False, "unexpected or missing fields"
    path = payload.get("path")
    if not isinstance(path, str) or not PATH_RE.fullmatch(path) or path not in ALLOWED_PATHS:
        return False, "unknown public page path"
    if event == "guide_read_75" and path not in GUIDE_PATHS:
        return False, "not a published guide"
    if event == "outbound_click":
        asin = payload.get("asin")
        if not isinstance(asin, str) or not ASIN_RE.fullmatch(asin) or asin not in KNOWN_ASINS:
            return False, "unknown catalog asin"
    if event == "category_click":
        target = payload.get("target")
        if not isinstance(target, str) or target not in CATEGORY_PATHS:
            return False, "unknown category target"
    return True, ""


def _day(today: str | None = None) -> dt.date:
    return dt.date.fromisoformat(today) if today is not None else dt.datetime.now(dt.timezone.utc).date()


def _read_counts(counts_file: pathlib.Path) -> dict:
    if not counts_file.exists():
        return {}
    data = json.loads(counts_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("invalid aggregate file")
    for day, bucket in data.items():
        if not isinstance(day, str) or dt.date.fromisoformat(day).isoformat() != day or not isinstance(bucket, dict):
            raise ValueError("invalid daily bucket")
        for dimension, values in bucket.items():
            if dimension not in DIMENSIONS or not isinstance(values, dict):
                raise ValueError("invalid aggregate dimension")
            for key, count in values.items():
                if key not in DIMENSIONS[dimension] or type(count) is not int or count < 1:
                    raise ValueError("invalid aggregate counter")
    return data


def _retained(data: dict, today: dt.date) -> dict:
    cutoff = (today - dt.timedelta(days=RETENTION_DAYS - 1)).isoformat()
    return {day: bucket for day, bucket in data.items() if cutoff <= day <= today.isoformat()}


def _save(counts_file: pathlib.Path, data: dict) -> None:
    counts_file.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(counts_file.parent), prefix=".counts-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, counts_file)  # private temp-file permissions are preserved
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def prune(counts_file: pathlib.Path, today: str | None = None) -> int:
    """Delete expired/future day buckets without adding an event; do not invent a file."""
    with _lock:
        data = _read_counts(counts_file)
        retained = _retained(data, _day(today))
        if data != retained:
            _save(counts_file, retained)
        return len(data) - len(retained)


def record(counts_file: pathlib.Path, payload: dict, today: str | None = None) -> None:
    """Atomically add validated counts. No raw payload or visitor identifier is saved."""
    ok, reason = validate(payload)
    if not ok:
        raise ValueError(reason)
    now = _day(today)
    with _lock:
        data = _retained(_read_counts(counts_file), now)
        bucket = data.setdefault(now.isoformat(), {})
        by_path = bucket.setdefault(payload["event"], {})
        by_path[payload["path"]] = by_path.get(payload["path"], 0) + 1
        for event, field, dimension in (("outbound_click", "asin", "outbound_click_asin"),
                                         ("category_click", "target", "category_click_target")):
            if payload["event"] == event:
                counters = bucket.setdefault(dimension, {})
                counters[payload[field]] = counters.get(payload[field], 0) + 1
        _save(counts_file, data)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def make_handler(counts_file: pathlib.Path, allowed_origin: str):
    class Handler(BaseHTTPRequestHandler):
        server_version = "zone4-measure"
        sys_version = ""
        timeout = 5  # local/reference protection only; production limits belong at the reviewed edge

        def log_message(self, format, *args):
            return  # no application request log or client address output

        def _cors(self) -> None:
            self.send_header("Vary", "Origin")
            if self.headers.get("Origin") == allowed_origin:
                self.send_header("Access-Control-Allow-Origin", allowed_origin)
                self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def _send(self, code: int) -> None:
            self.send_response(code)
            self._cors()
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_OPTIONS(self):
            if self.path != "/event":
                self._send(404)
            elif self.headers.get("Origin") != allowed_origin:
                self._send(403)
            elif self.headers.get("Access-Control-Request-Method") != "POST":
                self._send(405)
            elif any(h.strip().lower() not in {"content-type"}
                     for h in self.headers.get("Access-Control-Request-Headers", "").split(",") if h.strip()):
                self._send(400)
            else:
                self._send(204)

        def do_GET(self):
            if self.path == "/health":
                body = b"ok" if self.server.storage_ok else b"unavailable"
                self.send_response(200 if self.server.storage_ok else 503)
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self._send(404)  # no public count export

        def do_POST(self):
            if self.path != "/event":
                self._send(404)
                return
            # Keep PR #115's server-side origin gate: CORS alone is not a write gate.
            if self.headers.get("Origin") != allowed_origin:
                self._send(403)
                return
            if self.headers.get("DNT") == "1" or self.headers.get("Sec-GPC") == "1":
                self._send(204)  # independently honor opt-out; do not record an event
                return
            if self.headers.get_content_type() != "application/json":
                self._send(415)
                return
            if self.headers.get("Transfer-Encoding") or len(self.headers.get_all("Content-Length", [])) != 1:
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
            except TimeoutError:
                self._send(408)
                return
            try:
                payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
            except (UnicodeDecodeError, ValueError, RecursionError):
                self._send(400)
                return
            ok, _reason = validate(payload)
            if not ok:
                self._send(400)
                return
            try:
                record(counts_file, payload)
            except (OSError, ValueError):
                self.server.storage_ok = False
                self._send(503)  # never replace a corrupt store with invented empty counts
                return
            self.server.storage_ok = True
            self._send(204)

    return Handler


class CollectorServer(ThreadingHTTPServer):
    """Single-process reference runtime with quiet-period retention maintenance."""
    def handle_error(self, request, client_address):
        # BaseServer's default traceback includes the client address. Do not turn
        # disconnects or malformed traffic into an identifying application log.
        return

    def service_actions(self):
        if time.monotonic() < self.next_prune:
            return
        try:
            prune(self.counts_file)
            self.storage_ok = True
        except (OSError, ValueError):
            self.storage_ok = False
        self.next_prune = time.monotonic() + (3600 if self.storage_ok else 60)


def serve(host: str, port: int, counts_file: pathlib.Path, allowed_origin: str) -> CollectorServer:
    prune(counts_file)  # fail startup rather than silently overwrite a corrupt store
    server = CollectorServer((host, port), make_handler(counts_file, allowed_origin))
    server.counts_file = counts_file
    server.storage_ok = True
    server.next_prune = time.monotonic() + 3600
    return server


def main() -> None:
    here = pathlib.Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--counts", default=str(here / "counts.json"))
    ap.add_argument("--origin", default=os.environ.get("ZONE4_ALLOWED_ORIGIN", DEFAULT_ORIGIN))
    ap.add_argument("--prune-only", action="store_true", help="expire count buckets without starting a server")
    args = ap.parse_args()
    counts = pathlib.Path(args.counts)
    if args.prune_only:
        print(f"expired day buckets: {prune(counts)}")
        return
    server = serve(args.host, args.port, counts, args.origin)
    print(f"reference collector on {args.host}:{args.port}; production launch remains gated", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
