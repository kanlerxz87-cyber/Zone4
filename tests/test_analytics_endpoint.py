"""Collector contract: bounded aggregates, five events, no visitor identifiers."""
import concurrent.futures
import importlib.util
import json
import pathlib
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("zone4_measure", ROOT / "analytics-endpoint/server.py")
srv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(srv)
ORIGIN = srv.DEFAULT_ORIGIN
PATH = "/Zone4/docs/products.html"
CATEGORY = "dual-basket-air-fryers"
ASIN = "B0CDY277D3"


def event(name="page_view", **extra):
    body = {"event": name, "path": PATH}
    if name == "outbound_click":
        body["asin"] = ASIN
    if name == "category_click":
        body["target"] = CATEGORY
    return dict(body, **extra)


class ValidateTests(unittest.TestCase):
    def test_exactly_five_events(self):
        self.assertEqual(srv.EVENT_NAMES, {"page_view", "outbound_click", "guide_read_75", "category_click", "feed_click"})
        for name in srv.EVENT_NAMES:
            self.assertTrue(srv.validate(event(name))[0])

    def test_unhashable_and_wrong_event_types_never_raise(self):
        for value in ([], {}, None, 1, True, "purchase"):
            self.assertFalse(srv.validate({"event": value, "path": PATH})[0])
        for value in (None, [], 1, "x"):
            self.assertFalse(srv.validate(value)[0])

    def test_paths_are_published_and_bounded(self):
        for path in (PATH + "\n", PATH + "?email=private", PATH + "#private", "/a b", "/visitor-id", "https://evil.example/", [], None):
            self.assertFalse(srv.validate(event(path=path))[0])
        self.assertTrue(srv.validate(event(path="/Zone4/docs/"))[0])

    def test_rejects_unexpected_fields_even_when_they_would_be_discarded(self):
        for key in ("email", "ip", "referrer", "visitor", "target", "asin"):
            self.assertFalse(srv.validate(event(**{key: "private"}))[0])

    def test_only_registered_products_and_categories(self):
        for asin in ("B000000000", [], {}, None, "B0CDY277D3\n"):
            self.assertFalse(srv.validate(event("outbound_click", asin=asin))[0])
        for target in ("unknown", "https://evil.example", [], None, CATEGORY + "\n"):
            self.assertFalse(srv.validate(event("category_click", target=target))[0])
        self.assertEqual(len(srv.PRODUCT_ASINS), 5)


class RecordTests(unittest.TestCase):
    def test_aggregate_counts_and_no_identifiers(self):
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "counts.json"
            for name in srv.EVENT_NAMES:
                srv.record(f, event(name), today="2026-11-20")
                srv.record(f, event(name), today="2026-11-20")
            data = json.loads(f.read_text())["2026-11-20"]
            for name in srv.EVENT_NAMES:
                self.assertEqual(data[name][PATH], 2)
            self.assertEqual(data["outbound_click_asin"][ASIN], 2)
            self.assertEqual(data["category_click_target"][CATEGORY], 2)
            for forbidden in ("ip", "user-agent", "referrer", "cookie", "address", "session"):
                self.assertNotIn(f'"{forbidden}"', f.read_text().lower())

    def test_retention_including_inactive_days(self):
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "counts.json"
            for day in ("2026-08-22", "2026-08-23", "2026-11-20"):
                srv.record(f, event(), today=day)
            self.assertEqual(set(json.loads(f.read_text())), {"2026-08-23", "2026-11-20"})
            srv.record(f, None, today="2027-03-01")
            self.assertEqual(json.loads(f.read_text()), {})

    def test_invalid_event_cannot_be_stored_directly(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                srv.record(pathlib.Path(d) / "counts.json", event(email="private"))

    def test_concurrent_writes_keep_counts_and_no_temp_files(self):
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "counts.json"
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(lambda _: srv.record(f, event(), today="2026-11-20"), range(40)))
            self.assertEqual(json.loads(f.read_text())["2026-11-20"]["page_view"][PATH], 40)
            self.assertEqual([p.name for p in f.parent.iterdir()], ["counts.json"])


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.counts = pathlib.Path(cls.tmp.name) / "counts.json"
        cls.server = srv.serve("127.0.0.1", 0, cls.counts, ORIGIN)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.tmp.cleanup()

    def request(self, body=None, origin=ORIGIN, method="POST", path="/event", content_type="application/json"):
        req = urllib.request.Request(self.base + path, data=body, method=method)
        if origin is not None:
            req.add_header("Origin", origin)
        req.add_header("Content-Type", content_type)
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return r.status, dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers)

    def test_valid_events_and_cors(self):
        for name in srv.EVENT_NAMES:
            status, headers = self.request(json.dumps(event(name)).encode())
            self.assertEqual(status, 204)
            self.assertEqual(headers.get("Access-Control-Allow-Origin"), ORIGIN)
            self.assertEqual(headers.get("Cache-Control"), "no-store")
        self.assertEqual(self.request(json.dumps(event()).encode(), content_type="text/plain")[0], 204)

    def test_other_and_missing_origins_cannot_write(self):
        before = self.counts.read_bytes() if self.counts.exists() else None
        for origin in ("https://evil.example", None, ORIGIN + ".evil.example", "null"):
            status, headers = self.request(json.dumps(event()).encode(), origin=origin)
            self.assertEqual(status, 403)
            self.assertNotIn("Access-Control-Allow-Origin", headers)
        self.assertEqual(self.counts.read_bytes() if self.counts.exists() else None, before)

    def test_malformed_events_return_400_not_connection_reset(self):
        for body in (b"{bad", b"[]", b'\xff', json.dumps(event(event=[])).encode(), json.dumps(event(path=[])).encode()):
            self.assertEqual(self.request(body)[0], 400)
        self.assertEqual(self.request(b"x" * (srv.MAX_BODY + 1))[0], 413)
        self.assertEqual(self.request(b"")[0], 400)
        self.assertEqual(self.request(b"{}", content_type="application/x-www-form-urlencoded")[0], 415)

    def test_storage_failure_is_503_and_does_not_erase_counts(self):
        with patch.object(srv, "record", side_effect=OSError("private storage path")):
            self.assertEqual(self.request(json.dumps(event()).encode())[0], 503)

    def test_routes_and_preflight(self):
        self.assertEqual(self.request(method="GET", path="/health")[0], 204)
        self.assertEqual(self.request(method="GET", path="/counts.json")[0], 404)
        self.assertEqual(self.request(method="OPTIONS")[0], 204)
        self.assertEqual(self.request(method="OPTIONS", origin="null")[0], 403)
        self.assertEqual(self.request(b"{}", path="/event?private=1")[0], 404)


if __name__ == "__main__":
    unittest.main()
