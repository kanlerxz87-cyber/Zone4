"""Fail-closed activation and generated-client -> HTTP collector contracts.

All fabricated events are isolated test fixtures, never real affiliate traffic
or campaign-ledger entries. Node is also exercised directly by the existing CI job.
"""
import copy
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import tempfile
import threading
import unittest
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


extras = module("zone4_publication_measurement", "scripts/build_extras.py")
collector = module("zone4_collector_contract", "analytics-endpoint/server.py")


class ActivationTests(unittest.TestCase):
    def settings(self, approved=False):
        rec = copy.deepcopy(extras.MEASUREMENT)
        rec["enabled"] = True
        rec["endpoint_url"] = "https://collector.example/event"
        if approved:
            # Deliberately synthetic completeness fixtures. Never written to data/.
            for check in rec["launch_checks"]:
                check.update(confirmed_utc="2026-11-20", evidence_reference="isolated test fixture", reviewed_by="fixture")
        return rec

    def test_shipped_configuration_is_disabled_and_has_no_fabricated_launch_evidence(self):
        self.assertFalse(extras.MEASUREMENT["enabled"])
        self.assertEqual(extras.MEASURE_ENDPOINT, "")
        self.assertEqual(extras.MEASUREMENT["endpoint_url"], "")
        for check in extras.MEASUREMENT["launch_checks"]:
            for field in ("confirmed_utc", "evidence_reference", "reviewed_by"):
                self.assertIsNone(check[field])

    def test_disabled_configuration_emits_no_endpoint_even_if_a_url_is_staged(self):
        rec = self.settings()
        rec["enabled"] = False
        self.assertEqual(extras.measure_endpoint(rec), "")

    def test_a_url_without_dated_reviewed_evidence_is_not_enough(self):
        with self.assertRaises(ValueError):
            extras.measure_endpoint(self.settings())

    def test_every_gate_requires_a_date_evidence_reference_and_reviewer(self):
        for index in range(5):
            for field in ("confirmed_utc", "evidence_reference", "reviewed_by"):
                rec = self.settings(approved=True)
                rec["launch_checks"][index][field] = None
                with self.subTest(index=index, field=field), self.assertRaises(ValueError):
                    extras.measure_endpoint(rec)

    def test_missing_duplicate_and_invalid_date_checks_fail_closed(self):
        for mutation in ("missing", "duplicate", "bad_date", "basic_date"):
            rec = self.settings(approved=True)
            if mutation == "missing":
                rec["launch_checks"].pop()
            elif mutation == "duplicate":
                rec["launch_checks"][0]["id"] = "MC-02"
            else:
                rec["launch_checks"][0]["confirmed_utc"] = "2026-99-99" if mutation == "bad_date" else "20261120"
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                extras.measure_endpoint(rec)

    def test_invalid_urls_and_non_boolean_activation_are_refused(self):
        for endpoint in ("", "http://collector.example/event", "https://collector.example/other", "/event",
                         "https://collector.example/event?secret=1", "https://collector.example/event#secret",
                         "https://user:secret@collector.example/event", "https://collector.example:bad/event",
                         "https://localhost/event", "https://127.0.0.2/event", "https://[::1]/event",
                         "https://2130706433/event", "https://127.1/event", "https://0x7f.0.0.1/event",
                         "https://0177.0.0.1/event", "https://collector.local/event", "https://collector.internal/event",
                         "https://kanlerxz87-cyber.github.io/event", "https://example.github.io./event",
                         "https://collector.example/event\n"):
            rec = self.settings(approved=True)
            rec["endpoint_url"] = endpoint
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                extras.measure_endpoint(rec)
        rec = self.settings(approved=True)
        rec["enabled"] = "true"
        with self.assertRaises(ValueError):
            extras.measure_endpoint(rec)

    def test_complete_reference_fixture_passes_completeness_gate_not_a_live_verification(self):
        self.assertEqual(extras.measure_endpoint(self.settings(approved=True)), "https://collector.example/event")

    def test_all_built_pages_keep_empty_endpoint_meta_and_disclosure(self):
        for page in (ROOT / "docs").rglob("*.html"):
            text = page.read_text()
            self.assertIn('<meta name="zone4-measure-endpoint" content="">', text, page)
            self.assertGreaterEqual(text.count("As an Amazon Associate I earn from qualifying purchases."), 2, page)


class GeneratedClientContractTests(unittest.TestCase):
    def test_browser_and_collector_have_identical_public_route_and_catalog_allowlists(self):
        client = (ROOT / "docs/measure.js").read_text()
        config = json.loads(re.search(r"var CONFIG = (\{[^\n]+\});", client).group(1))
        base = "/Zone4/docs/"
        self.assertEqual({base + p for p in config["paths"]}, collector.ALLOWED_PATHS)
        self.assertEqual({base + p for p in config["categories"]}, collector.CATEGORY_PATHS)
        self.assertEqual({base + p for p in config["guides"]}, collector.GUIDE_PATHS)
        self.assertEqual(set(config["asins"]), collector.KNOWN_ASINS)
        source = (ROOT / "analytics-endpoint/client.js").read_text()
        self.assertIn("referrerPolicy: 'no-referrer'", source)
        self.assertIn("credentials: 'omit'", source)
        for forbidden in ("document.referrer", "document.cookie", "navigator.userAgent"):
            self.assertNotIn(forbidden, source)

    def test_actual_generated_client_payloads_are_accepted_over_http_in_temporary_counts_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload_file = pathlib.Path(tmp) / "fixture-payloads.json"
            result = subprocess.run(
                ["node", "--test", "tests/measure_client.test.js"], cwd=ROOT,
                env=dict(os.environ, ZONE4_TEST_PAYLOAD_FILE=str(payload_file)),
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payloads = json.loads(payload_file.read_text())
            self.assertEqual({p["event"] for p in payloads}, collector.EVENT_NAMES)
            counts = pathlib.Path(tmp) / "counts.json"
            server = collector.serve("127.0.0.1", 0, counts, collector.DEFAULT_ORIGIN)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                for payload in payloads:
                    self.assertTrue(collector.validate(payload)[0], payload)
                    request = urllib.request.Request(
                        f"http://127.0.0.1:{server.server_address[1]}/event", data=json.dumps(payload).encode(),
                        headers={"Origin": collector.DEFAULT_ORIGIN, "Content-Type": "application/json"}, method="POST",
                    )
                    with urllib.request.urlopen(request, timeout=5) as response:
                        self.assertEqual(response.status, 204)
                day = next(iter(json.loads(counts.read_text()).values()))
                self.assertEqual(day["category_click_target"], {"/Zone4/docs/categories/meat-thermometers.html": 1})
                self.assertEqual(day["outbound_click_asin"], {"B0CDY277D3": 1})
                self.assertNotIn("order", day)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)
        # The fixture path was private and deleted. The authorized-report ledger remains untouched.
        self.assertEqual(json.loads((ROOT / "data/ledger.json").read_text())["rows"], [])


if __name__ == "__main__":
    unittest.main()
