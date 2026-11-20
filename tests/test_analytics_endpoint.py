"""Reference collector contracts; every event here uses an isolated temporary file.

No fixture is visitor data, an Amazon click, or an authorized campaign report.
The origin/type checks adopted from PR #115 remain regression-tested here.
"""
import concurrent.futures
import importlib.util
import json
import pathlib
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("zone4_measure", ROOT / "analytics-endpoint/server.py")
srv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(srv)
ORIGIN = "https://kanlerxz87-cyber.github.io"
HOME = "/Zone4/docs/index.html"
CATEGORY = "/Zone4/docs/categories/meat-thermometers.html"
GUIDE = "/Zone4/docs/guides/basket-or-oven-style-air-fryer-what-to-compare.html"
ASIN = "B0CDY277D3"


def event(name="page_view", **extra):
    payload = {"event": name, "path": GUIDE if name == "guide_read_75" else HOME}
    if name == "outbound_click":
        payload["asin"] = ASIN
    if name == "category_click":
        payload["target"] = CATEGORY
    payload.update(extra)
    return payload


class ValidateTests(unittest.TestCase):
    def test_five_events_are_exactly_the_defined_set(self):
        expected = {"page_view", "outbound_click", "guide_read_75", "category_click", "feed_click"}
        self.assertEqual(srv.EVENT_NAMES, expected)
        self.assertEqual({row["name"] for row in srv.SETTINGS["events"]}, expected)

    def test_accepts_each_defined_event(self):
        for name in srv.EVENT_NAMES:
            with self.subTest(name=name):
                self.assertTrue(srv.validate(event(name))[0])

    def test_rejects_unknown_event_and_bad_paths(self):
        for path in ("/", "/someone-private", HOME + "?email=private", HOME + "#private",
                     "https://evil.example/", HOME + "\n", "/a b", "/Zone4/docs/missing.html"):
            with self.subTest(path=path):
                self.assertFalse(srv.validate(event(path=path))[0])
        self.assertFalse(srv.validate(event("purchase"))[0])
        self.assertFalse(srv.validate(["not", "an", "object"])[0])

    def test_unhashable_event_values_return_false_without_crashing(self):
        for value in ([], {}, None, 1, True):
            self.assertFalse(srv.validate({"event": value, "path": HOME})[0])

    def test_unknown_fields_and_event_field_mixes_are_refused(self):
        for payload in (event(email="private"), event(asin=ASIN), event("outbound_click", target=CATEGORY),
                        event("category_click", asin=ASIN), {"event": "page_view"}):
            self.assertFalse(srv.validate(payload)[0])

    def test_asin_must_match_a_published_catalog_entry(self):
        self.assertTrue(srv.validate(event("outbound_click"))[0])
        for asin in ("123", "B000000000", "", None, [], {}, ASIN + "\n"):
            self.assertFalse(srv.validate(event("outbound_click", asin=asin))[0])
        payload = event("outbound_click")
        del payload["asin"]
        self.assertFalse(srv.validate(payload)[0])

    def test_category_target_must_be_an_allowlisted_path(self):
        for target in ("../categories/meat-thermometers.html", HOME, CATEGORY + "?private=1", "", [], None):
            self.assertFalse(srv.validate(event("category_click", target=target))[0])
        payload = event("category_click")
        del payload["target"]
        self.assertFalse(srv.validate(payload)[0])

    def test_guide_milestones_cannot_be_counted_for_other_pages(self):
        self.assertTrue(srv.validate(event("guide_read_75", path="/Zone4/docs/articles/air-fryer-buying-guide-2026.html"))[0])
        self.assertFalse(srv.validate(event("guide_read_75", path="/Zone4/docs/articles/index.html"))[0])
        self.assertFalse(srv.validate(event("guide_read_75", path=HOME))[0])
        self.assertFalse(srv.validate(event("guide_read_75", path="/Zone4/docs/guides/index.html"))[0])


class RecordTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.file = pathlib.Path(self.tmp.name) / "counts.json"

    def test_counts_only_and_no_identifiers_are_stored(self):
        for _ in range(2):
            srv.record(self.file, event("outbound_click"), today="2026-11-20")
        srv.record(self.file, event(), today="2026-11-20")
        data = json.loads(self.file.read_text())["2026-11-20"]
        self.assertEqual(data["outbound_click"][HOME], 2)
        self.assertEqual(data["outbound_click_asin"][ASIN], 2)
        self.assertEqual(data["page_view"][HOME], 1)
        text = self.file.read_text().lower()
        for forbidden in ("ip", "user-agent", "referer", "referrer", "cookie", "address", "session", "order"):
            self.assertNotIn(f'"{forbidden}"', text)
        self.assertEqual(self.file.stat().st_mode & 0o777, 0o600)
        self.assertEqual(list(self.file.parent.glob(".counts-*")), [])

    def test_all_five_events_keep_separate_daily_path_totals(self):
        for name in srv.EVENT_NAMES:
            srv.record(self.file, event(name), today="2026-11-20")
            srv.record(self.file, event(name), today="2026-11-20")
        data = json.loads(self.file.read_text())["2026-11-20"]
        for name in srv.EVENT_NAMES:
            self.assertEqual(data[name][event(name)["path"]], 2)
        self.assertEqual(data["outbound_click_asin"][ASIN], 2)
        self.assertEqual(data["category_click_target"][CATEGORY], 2)

    def test_category_target_is_aggregated_separately_from_source_path(self):
        srv.record(self.file, event("category_click"), today="2026-11-20")
        data = json.loads(self.file.read_text())["2026-11-20"]
        self.assertEqual(data["category_click"], {HOME: 1})
        self.assertEqual(data["category_click_target"], {CATEGORY: 1})

    def test_unknown_payload_cannot_be_written_even_by_direct_call(self):
        with self.assertRaises(ValueError):
            srv.record(self.file, event(email="private"))
        self.assertFalse(self.file.exists())

    def test_retention_cutoff_includes_today_and_29_previous_utc_dates(self):
        fixture = {day: {"page_view": {HOME: 1}} for day in
                   ("2026-10-21", "2026-10-22", "2026-11-19", "2026-11-21")}
        self.file.write_text(json.dumps(fixture))
        srv.record(self.file, event(), today="2026-11-20")
        self.assertEqual(set(json.loads(self.file.read_text())), {"2026-10-22", "2026-11-19", "2026-11-20"})

    def test_prune_removes_expired_buckets_without_inventing_events(self):
        self.file.write_text(json.dumps({"2000-01-01": {"page_view": {HOME: 1}}}))
        self.assertEqual(srv.prune(self.file, today="2026-11-20"), 1)
        self.assertEqual(json.loads(self.file.read_text()), {})
        self.assertEqual(srv.prune(self.file, today="2026-11-20"), 0)

    def test_prune_absent_file_does_not_create_synthetic_empty_data(self):
        self.assertEqual(srv.prune(self.file, today="2026-11-20"), 0)
        self.assertFalse(self.file.exists())

    def test_corrupt_or_unknown_dimension_store_fails_without_overwriting(self):
        for raw in ("not json", "[]", '{"bad-date":{}}',
                    json.dumps({"2026-11-20": {"ip": {"private": 1}}}),
                    json.dumps({"2026-11-20": {"page_view": {"/private": 1}}}),
                    json.dumps({"2026-11-20": {"page_view": {HOME: True}}})):
            with self.subTest(raw=raw):
                self.file.write_text(raw)
                with self.assertRaises(ValueError):
                    srv.record(self.file, event(), today="2026-11-20")
                self.assertEqual(self.file.read_text(), raw)

    def test_concurrent_threads_do_not_lose_increments(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda _: srv.record(self.file, event(), today="2026-11-20"), range(40)))
        self.assertEqual(json.loads(self.file.read_text())["2026-11-20"]["page_view"][HOME], 40)

    def test_failed_atomic_replace_does_not_leave_temporary_payloads(self):
        with mock.patch.object(srv.os, "replace", side_effect=OSError("fixture")):
            with self.assertRaises(OSError):
                srv.record(self.file, event())
        self.assertEqual(list(self.file.parent.glob(".counts-*")), [])


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
        cls.thread.join(timeout=5)
        cls.tmp.cleanup()

    def setUp(self):
        with srv._lock:
            self.counts.unlink(missing_ok=True)
        self.server.storage_ok = True

    def _request(self, method="POST", body=None, origin=ORIGIN, path="/event", content_type="application/json", headers=None):
        if body is None and method == "POST":
            body = json.dumps(event()).encode()
        req = urllib.request.Request(self.base + path, data=body, method=method)
        if content_type:
            req.add_header("Content-Type", content_type)
        if origin is not None:
            req.add_header("Origin", origin)
        for key, value in (headers or {}).items():
            req.add_header(key, value)
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status, dict(response.headers), response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers), exc.read()

    def test_valid_event_is_counted_with_204_and_cors_for_allowed_origin(self):
        status, headers, _ = self._request()
        self.assertEqual(status, 204)
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), ORIGIN)
        self.assertEqual(headers.get("Cache-Control"), "no-store")
        self.assertNotIn("Set-Cookie", headers)
        self.assertTrue(self.counts.exists())

    def test_other_or_missing_origins_are_rejected_without_writing(self):
        for origin in ("https://evil.example", ORIGIN + ".evil.example", "null", None):
            status, headers, _ = self._request(origin=origin)
            self.assertEqual(status, 403)
            self.assertNotIn("Access-Control-Allow-Origin", headers)
            self.assertFalse(self.counts.exists())

    def test_preflight_requires_approved_origin_method_and_headers(self):
        allowed = {"Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "Content-Type"}
        self.assertEqual(self._request("OPTIONS", headers=allowed)[0], 204)
        self.assertEqual(self._request("OPTIONS", origin="https://evil.example", headers=allowed)[0], 403)
        self.assertEqual(self._request("OPTIONS", headers={"Access-Control-Request-Method": "GET"})[0], 405)
        disallowed = dict(allowed, **{"Access-Control-Request-Headers": "Authorization"})
        self.assertEqual(self._request("OPTIONS", headers=disallowed)[0], 400)
        self.assertFalse(self.counts.exists())

    def test_server_privacy_signals_suppress_storage(self):
        for headers in ({"DNT": "1"}, {"Sec-GPC": "1"}):
            self.assertEqual(self._request(headers=headers)[0], 204)
            self.assertFalse(self.counts.exists())

    def test_rejections_do_not_write_any_data(self):
        cases = [(b"{not json", 400), (b"[]", 400), (b"\xff", 400),
                 (json.dumps(event("nope")).encode(), 400),
                 (b'{"event":[],"path":"' + HOME.encode() + b'"}', 400),
                 (b'{"event":"page_view","event":"feed_click","path":"' + HOME.encode() + b'"}', 400),
                 (json.dumps(event(email="private")).encode(), 400), (b"x" * (srv.MAX_BODY + 1), 413), (b"", 400)]
        for body, code in cases:
            self.assertEqual(self._request(body=body)[0], code)
            self.assertFalse(self.counts.exists())

    def test_non_json_posts_are_refused(self):
        self.assertEqual(self._request(content_type="text/plain")[0], 415)
        self.assertFalse(self.counts.exists())

    def test_unknown_route_health_and_no_public_count_export(self):
        for path in ("/nope", "/counts.json", "/event?email=private"):
            self.assertEqual(self._request("GET", path=path)[0], 404)
        status, _, body = self._request("GET", path="/health")
        self.assertEqual((status, body), (200, b"ok"))
        self.assertFalse(self.counts.exists())

    def test_storage_error_is_503_without_disclosing_private_paths(self):
        with mock.patch.object(srv, "record", side_effect=OSError("private storage path")):
            status, _, body = self._request()
        self.assertEqual(status, 503)
        self.assertNotIn(b"private", body)
        self.assertFalse(self.counts.exists())

    def test_corrupt_store_returns_503_preserves_data_and_recovers_explicitly(self):
        self.counts.write_text("invalid fixture")
        self.assertEqual(self._request()[0], 503)
        self.assertEqual(self.counts.read_text(), "invalid fixture")
        self.assertEqual(self._request("GET", path="/health")[0], 503)
        self.counts.unlink()
        self.assertEqual(self._request()[0], 204)
        self.assertEqual(self._request("GET", path="/health")[0], 200)

    def test_request_error_handler_does_not_emit_the_client_address(self):
        with mock.patch("sys.stderr") as stderr:
            self.server.handle_error(None, ("192.0.2.7", 1234))
        stderr.write.assert_not_called()

    def test_quiet_period_maintenance_runs_without_a_page_event(self):
        self.counts.write_text(json.dumps({"2000-01-01": {"page_view": {HOME: 1}}}))
        self.server.next_prune = 0
        self.server.service_actions()
        self.assertEqual(json.loads(self.counts.read_text()), {})


if __name__ == "__main__":
    unittest.main()
