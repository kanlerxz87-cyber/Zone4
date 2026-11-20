"""Tests for analytics-endpoint/server.py: five events only, counts only, no identifiers.

Added by arena/3d2ad125-zone4 on 2026-11-17.
"""
import importlib.util
import json
import pathlib
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("zone4_measure", ROOT / "analytics-endpoint" / "server.py")
srv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(srv)

ORIGIN = "https://kanlerxz87-cyber.github.io"


class ValidateTests(unittest.TestCase):
    def test_five_events_are_exactly_the_defined_set(self):
        self.assertEqual(
            sorted(srv.EVENT_NAMES),
            sorted(["page_view", "outbound_click", "guide_read_75", "category_click", "feed_click"]),
        )

    def test_accepts_each_defined_event(self):
        for name in srv.EVENT_NAMES:
            ok, _ = srv.validate({"event": name, "path": "/guides/x.html"})
            self.assertTrue(ok, name)

    def test_rejects_unknown_event_and_bad_paths(self):
        self.assertFalse(srv.validate({"event": "purchase", "path": "/"})[0])
        self.assertFalse(srv.validate({"event": "page_view", "path": "/a?utm=1"})[0])
        self.assertFalse(srv.validate({"event": "page_view", "path": "https://evil.example/"})[0])
        self.assertFalse(srv.validate({"event": "page_view", "path": "/a b"})[0])
        self.assertFalse(srv.validate(["not", "an", "object"])[0])

    def test_asin_must_match_amazon_format(self):
        self.assertTrue(srv.validate({"event": "outbound_click", "path": "/", "asin": "B0CDY277D3"})[0])
        self.assertFalse(srv.validate({"event": "outbound_click", "path": "/", "asin": "123"})[0])


class RecordTests(unittest.TestCase):
    def test_counts_only_and_no_identifiers_are_stored(self):
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "counts.json"
            srv.record(f, {"event": "outbound_click", "path": "/products.html", "asin": "B0CDY277D3"}, today="2026-11-17")
            srv.record(f, {"event": "outbound_click", "path": "/products.html", "asin": "B0CDY277D3"}, today="2026-11-17")
            srv.record(f, {"event": "page_view", "path": "/"}, today="2026-11-17")
            data = json.loads(f.read_text(encoding="utf-8"))
            day = data["2026-11-17"]
            self.assertEqual(day["outbound_click"]["/products.html"], 2)
            self.assertEqual(day["outbound_click_asin"]["B0CDY277D3"], 2)
            self.assertEqual(day["page_view"]["/"], 1)
            text = f.read_text(encoding="utf-8").lower()
            for forbidden in ("ip", "user-agent", "referer", "referrer", "cookie", "address", "session"):
                self.assertNotIn(f'"{forbidden}"', text)


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.counts = pathlib.Path(cls.tmp.name) / "counts.json"
        cls.server = srv.serve("127.0.0.1", 0, cls.counts, ORIGIN)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.tmp.cleanup()

    def _post(self, body: bytes, origin: str | None = ORIGIN):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/event", data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        if origin:
            req.add_header("Origin", origin)
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers)

    def test_valid_event_is_counted_with_204_and_cors_for_allowed_origin(self):
        body = json.dumps({"event": "feed_click", "path": "/index.html"}).encode()
        status, headers = self._post(body, origin=ORIGIN)
        self.assertEqual(status, 204)
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), ORIGIN)
        self.assertEqual(headers.get("Cache-Control"), "no-store")

    def test_other_or_missing_origins_cannot_write_counts(self):
        before = self.counts.read_bytes() if self.counts.exists() else None
        for origin in (None, "null", "https://other.example"):
            status, headers = self._post(b'{"event":"feed_click","path":"/"}', origin=origin)
            self.assertEqual(status, 403)
            self.assertNotIn("Access-Control-Allow-Origin", headers)
        self.assertEqual(self.counts.read_bytes() if self.counts.exists() else None, before)

    def test_rejections(self):
        self.assertEqual(self._post(b"{not json")[0], 400)
        self.assertEqual(self._post(b'{"event":[],"path":"/"}')[0], 400)
        self.assertEqual(self._post(json.dumps({"event": "page_view", "path": "/\n"}).encode())[0], 400)
        self.assertEqual(self._post(json.dumps({"event": "nope", "path": "/"}).encode())[0], 400)
        self.assertEqual(self._post(b"x" * (srv.MAX_BODY + 1))[0], 413)
        self.assertEqual(self._post(b"")[0], 400)

    def test_unknown_route_and_health(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            urllib.request.urlopen(f"http://127.0.0.1:{self.port}/nope", timeout=5)
        self.assertEqual(cm.exception.code, 404)
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/health", timeout=5) as r:
            self.assertEqual(r.read(), b"ok")


if __name__ == "__main__":
    unittest.main()
