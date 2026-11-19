"""Tests for the Zone4 affiliate engine.

Stdlib-only (``unittest``) so CI needs no installs. The tests deliberately
assert *refusals* as often as behaviours: the value of this platform is that it
cannot publish an unverified fact, so that must be testable.

Run:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine.agent import Agent                                  # noqa: E402
from engine.claims import (Claim, Entity, Status,               # noqa: E402
                           extract_identifier, validate_asin_format)
from engine.config import Config, MarketplaceConfig             # noqa: E402
from engine.content import buying_guide, product_review, seo_audit  # noqa: E402
from engine.datastore import PRODUCT_FIELDS, DataError, Datastore   # noqa: E402
from engine.economics import (SESSION_HOURS, UnitEconomics,     # noqa: E402
                              epc, rate_for, revenue_model)
from engine.links import LinkError, build_link, is_safe_href, validate_tag  # noqa: E402
from engine.policy import (REQUIRED_DISCLOSURE, Draft, blocking,  # noqa: E402
                           compliance_matrix, evaluate)
from engine.research import AmazonProber, CreatorsAPIClient      # noqa: E402
from engine.scoring import score_product                         # noqa: E402
from engine.sitegen import PAGES, _self_check, page_rates, page_verification  # noqa: E402
from engine.tracking import Event, EventError, Ledger           # noqa: E402


def store() -> Datastore:
    return Datastore(ROOT / "data")


class TestClaimGate(unittest.TestCase):
    def test_unverified_claim_may_not_carry_a_value(self):
        with self.assertRaises(ValueError):
            Claim("price", "Price", value=49.99, status=Status.UNVERIFIED)

    def test_verified_claim_requires_a_source(self):
        with self.assertRaises(ValueError):
            Claim("price", "Price", value=49.99, status=Status.VERIFIED)

    def test_blocked_and_partial_are_not_publishable(self):
        self.assertFalse(Status.BLOCKED.publishable)
        self.assertFalse(Status.VERIFIED_PARTIAL.publishable)
        self.assertTrue(Status.VERIFIED.publishable)

    def test_display_blanks_instead_of_guessing(self):
        c = Claim("price", "Price", value=None, status=Status.UNVERIFIED, flag="F-001")
        self.assertEqual(c.display, "")
        self.assertTrue(c.is_blank)

    def test_verified_display_and_entity_flag_collection(self):
        ent = Entity(ref="P-01", name="x")
        ent.add(Claim("a", "A", value=None, status=Status.UNVERIFIED, flag="F-009"))
        ent.add(Claim("b", "B", value=None, status=Status.UNVERIFIED, flag="F-010"))
        self.assertEqual(ent.flags, ["F-009", "F-010"])
        self.assertFalse(ent.complete)


class TestIdentifiers(unittest.TestCase):
    def test_asin_length_rule_is_enforced(self):
        ok, why = validate_asin_format("B04G1MEwY")
        self.assertFalse(ok)
        self.assertIn("9 characters", why)
        self.assertTrue(validate_asin_format("B0B7C327LK")[0])

    def test_missing_identifier_message(self):
        ok, why = validate_asin_format(None)
        self.assertFalse(ok)
        self.assertIn("No product identifier", why)

    def test_non_alnum_rejected(self):
        self.assertFalse(validate_asin_format("B04G1MEW-")[0])

    def test_extract_from_dp_and_short_links(self):
        self.assertEqual(extract_identifier("https://www.amazon.com/dp/B0B7C327LK"), "B0B7C327LK")
        self.assertEqual(extract_identifier("https://www.amazon.com/dp/B0B7C327LK?tag=x-20"), "B0B7C327LK")
        self.assertEqual(extract_identifier("https://link.amazon/B04G1MEwY"), "B04G1MEWY")
        self.assertEqual(extract_identifier("b0b7c327lk"), "B0B7C327LK")
        self.assertIsNone(extract_identifier("https://www.amazon.com/"))


class TestDataLayer(unittest.TestCase):
    def test_committed_data_passes_integrity_audit(self):
        s = store()
        self.assertEqual(s.audit(), [])

    def test_associates_protocol_covers_every_published_product(self):
        associates = json.loads((ROOT / "data/associates.json").read_text())
        intent = json.loads((ROOT / "data/intent-links.json").read_text())
        intended = {row["product_id"]: row for row in intent["links"]}
        special = associates["special_links"]
        recorded = {row["product_id"]: row for row in special}
        self.assertEqual(len(recorded), len(special), "Associates records must not repeat a product")
        self.assertEqual(set(recorded), set(intended),
                         "one-link-per-product protocol must cover all five published products")
        protocol = "\n".join(associates["test_protocol"]["steps"])
        for product_id, intent_row in intended.items():
            with self.subTest(product=product_id):
                row = recorded[product_id]
                self.assertEqual(row["asin"], intent_row["intended_asin"])
                self.assertEqual(row["submitted_link"], intent_row["submitted_url"])
                self.assertEqual(row["special_link_url"], intent_row["published_outbound_url"])
                self.assertIn(intent_row["intended_asin"], protocol)
                self.assertTrue(row.get("test_status"))

    def test_audit_catches_unverified_row_with_a_value(self):
        tmp = Path(tempfile.mkdtemp())
        shutil.copytree(ROOT / "data", tmp, dirs_exist_ok=True)
        prog = json.loads((tmp / "engine-program.json").read_text())
        prog["attribution_rules"][0]["status"] = "unverified"
        prog["attribution_rules"][0]["value"] = "24 hours"
        (tmp / "engine-program.json").write_text(json.dumps(prog))
        with self.assertRaises(DataError):
            Datastore(tmp)

    def test_audit_catches_missing_evidence_on_a_flag(self):
        tmp = Path(tempfile.mkdtemp())
        shutil.copytree(ROOT / "data", tmp, dirs_exist_ok=True)
        fnd = json.loads((tmp / "engine-verification.json").read_text())
        fnd["flags"][0]["evidence"] = []
        (tmp / "engine-verification.json").write_text(json.dumps(fnd))
        with self.assertRaises(DataError):
            Datastore(tmp)

    def test_every_source_url_is_https_official(self):
        for s in store().sources.values():
            self.assertTrue(s.url.startswith("https://"), s.id)

    #: Fields that policy, not observation, keeps off the page. These must stay
    #: null no matter what a future data pass finds, unless the policy changes.
    NEVER_PUBLISHED = {"price", "currency", "availability", "star_rating", "review_count",
                       "best_sellers_rank", "coupon_or_deal", "shipping_promise",
                       "estimated_earning_per_unit", "demand_trend", "competition_level",
                       "review_velocity", "excluded_product_check"}

    def test_every_field_is_tracked(self):
        s = store()
        prods = s.products()
        self.assertEqual(len(prods), 3)
        for ent in prods:
            for key, _label in PRODUCT_FIELDS:
                claim = ent.get(key)
                self.assertIsNotNone(claim, f"{ent.ref} missing {key}")
                self.assertIsNotNone(claim.flag, f"{ent.ref}.{key} has no flag attached")

    def test_policy_withheld_fields_are_never_published(self):
        for ent in store().products():
            for key in self.NEVER_PUBLISHED:
                claim = ent.get(key)
                if claim is not None:
                    self.assertIsNone(claim.value, f"{ent.ref}.{key} must stay null by policy")

    def test_no_published_value_lacks_an_official_source(self):
        """The core no-fabrication invariant, independent of which fields are filled."""
        official = ("amazon.com", "ftc.gov", "iana.org", "google.com", "github.com", "githubusercontent.com")
        for ent in store().products():
            for claim in ent.claims.values():
                if claim.value is None:
                    continue
                self.assertTrue(claim.status.publishable,
                                f"{ent.ref}.{claim.key} publishes a value without VERIFIED status")
                self.assertIsNotNone(claim.source, f"{ent.ref}.{claim.key} has a value and no source")
                host = claim.source.url.split("/")[2]
                self.assertTrue(any(host == d or host.endswith("." + d) for d in official),
                                f"{ent.ref}.{claim.key} cites a non-official host: {host}")

    def test_flags_are_sorted_and_prefixed(self):
        from engine.datastore import SEVERITY_ORDER
        s = store()
        flags = s.flags()
        self.assertGreaterEqual(len(flags), 20)
        ranks = [SEVERITY_ORDER.index(f["severity"]) if f["severity"] in SEVERITY_ORDER else 99
                 for f in flags]
        self.assertEqual(ranks, sorted(ranks), "flags must be ordered most urgent first")
        ids = [f["id"] for f in flags]
        self.assertEqual(len(ids), len(set(ids)), "flag ids must be unique")
        self.assertTrue(all(i.startswith("ENG-") for i in ids),
                        "engine flags are ENG- prefixed so they cannot collide with the site's F-nn ids")

    def test_every_flag_has_evidence_and_action(self):
        for f in store().flags():
            self.assertTrue(f.get("evidence"), f["id"])
            self.assertTrue(f.get("action"), f["id"])


class TestCliSurface(unittest.TestCase):
    """CI runs these subcommands, so each one must at least execute cleanly.

    A wrong attribute name inside `audit` passed every local run until CI caught
    it; these tests are the regression guard for that class of bug.
    """

    def _run(self, *args, expect=0):
        import subprocess
        res = subprocess.run([sys.executable, "-m", "engine.cli", *args], cwd=str(ROOT),
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, expect,
                         f"engine.cli {' '.join(args)} -> {res.returncode}\n{res.stdout[-900:]}\n{res.stderr[-900:]}")
        return res.stdout

    def test_status_reports_windows_and_rollup(self):
        out = self._run("status")
        self.assertIn("claims_verified", out)
        self.assertIn("publish_gate", out)

    def test_rates_lookup_and_unknown_category(self):
        import json
        kitchen = json.loads(self._run("rates", "--category", "Kitchen"))
        self.assertEqual(kitchen["rate_pct"], 4.5)
        self.assertTrue(kitchen["source"].startswith("https://affiliate-program.amazon.com/"),
                        "a published rate must cite the official table")
        other = json.loads(self._run("rates", "--category", "Something Amazon Does Not List"))
        self.assertIsNone(other["rate_pct"], "unknown categories must remain blank, not inherit the catch-all rate")

    def test_audit_is_not_failed_by_correctly_blocked_drafts(self):
        """Blocking is the intended state; only an unresolved-but-READY draft may fail the gate."""
        self._run("audit")

    def test_audit_strict_flags_incomplete_data(self):
        self._run("audit", "--strict", expect=1)

    def test_content_and_tracking_and_economics_run(self):
        self.assertIn("placeholder", self._run("content"))
        self._run("tracking")
        self._run("economics")

    def test_links_refuses_without_a_partner_tag(self):
        out = self._run("links", "B0CDY277D3")
        self.assertNotIn("yourid-20", out)
        self.assertNotIn("amazon-20", out)

    def test_build_writes_every_page(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            self._run("build", "--out", td)
            self.assertEqual(len(list(Path(td).glob("*.html"))), 6)


class TestAmazonTextNotice(unittest.TestCase):
    """IP License 2(k): displayed Amazon text needs the plain-view notice."""

    def test_every_generated_page_carries_the_notice(self):
        import tempfile
        import subprocess
        with tempfile.TemporaryDirectory() as td:
            res = subprocess.run([sys.executable, "-m", "engine.cli", "build", "--out", td],
                                 cwd=str(ROOT), capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
            pages = list(Path(td).glob("*.html"))
            self.assertEqual(len(pages), 6)
            for page in pages:
                html = page.read_text()
                self.assertIn("COMES FROM AMAZON", html.upper(), f"{page.name}: 2(k) notice missing")
                self.assertIn("As an Amazon Associate I earn from qualifying purchases.", html,
                              f"{page.name}: required disclosure missing")

    def test_detector_only_bites_on_reproduced_titles(self):
        from engine.policy import Draft, evaluate, register_program_text
        register_program_text("CHEFMAN 6 Quart Dual Basket Air Fryer Oven")
        disc = "As an Amazon Associate I earn from qualifying purchases."
        body = ("The CHEFMAN 6 Quart Dual Basket Air Fryer Oven has two baskets. " + disc)
        ids = [f.rule_id for f in evaluate(Draft(name="guide-a", text=body, verified_sources=["S15"]))]
        self.assertIn("TEXT-01", ids, "a reproduced Amazon title without the notice must be flagged")

        with_notice = body + " CERTAIN CONTENT THAT APPEARS ON THIS SITE COMES FROM AMAZON."
        ids = [f.rule_id for f in evaluate(Draft(name="guide-b", text=with_notice, verified_sources=["S15"]))]
        self.assertNotIn("TEXT-01", ids, "the notice satisfies the 2(k) duty")

        plain = "Nothing here reproduces Amazon listing text. " + disc
        ids = [f.rule_id for f in evaluate(Draft(name="guide-c", text=plain, verified_sources=["S2"]))]
        self.assertNotIn("TEXT-01", ids, "the duty must not fire on drafts that quote no Amazon text")

class TestCommission(unittest.TestCase):
    def test_official_rate_rows_present(self):
        rows = store().commission_rows()
        self.assertEqual(len(rows), 11)
        self.assertEqual(rows[0]["rate_pct"], 10.00)
        self.assertEqual(rows[-1]["categories"], "All Other Categories")

    def test_exact_category_lookup(self):
        s = store()
        self.assertEqual(s.rate_for_category("Kitchen"), 4.5)
        self.assertEqual(s.rate_for_category("Luxury Beauty"), 10.0)
        self.assertEqual(s.rate_for_category("Toys"), 3.0)
        self.assertEqual(s.rate_for_category("Televisions"), 2.0)

    def test_catchall_rate_requires_explicit_category_label(self):
        self.assertEqual(store().rate_for_category("All Other Categories"), 4.0)
        self.assertIsNone(store().rate_for_category("Something Else"))

    def test_browse_path_does_not_map_to_commission_band(self):
        s = store()
        browse_path = "Home & Kitchen > Kitchen & Dining > Small Appliances > Fryers > Air Fryers"
        self.assertIsNone(s.rate_for_category(browse_path))
        self.assertIsNone(rate_for(s, browse_path))
        self.assertTrue(all(p.get("commission_rate_pct") is None
                            for p in json.loads((ROOT / "data" / "products.json").read_text())["products"]))
        self.assertTrue(all(p["attributes"]["commission_rate_pct"].get("value") is None
                            for p in s.findings["products"]))

    def test_no_category_returns_nothing_not_zero(self):
        self.assertIsNone(store().rate_for_category(None))
        self.assertIsNone(store().rate_for_category(""))

    def test_games_twenty_pct_is_not_asserted(self):
        caps = {c["id"]: c for c in store().program["commission_caps"]}
        self.assertEqual(caps["amazon-games-20pct"]["status"], "unverified")
        self.assertIsNone(caps["amazon-games-20pct"]["value"])


class TestEconomics(unittest.TestCase):
    def test_math_when_inputs_are_known(self):
        e = UnitEconomics(price=100.0, rate_pct=4.5, quantity=2)
        self.assertEqual(e.gross, 200.0)
        self.assertEqual(e.commission, 9.0)

    def test_missing_price_propagates_none(self):
        e = UnitEconomics(price=None, rate_pct=4.5)
        self.assertIsNone(e.commission)
        self.assertTrue(e.missing[0].startswith("price"))
        self.assertIn("Not calculable", e.explain())

    def test_epc_refuses_one_sided_inputs(self):
        self.assertIsNone(epc(None, 100, 10))
        self.assertIsNone(epc(5.0, 0, 0))
        self.assertEqual(epc(5.0, 200, 100.0), 0.5)

    def test_revenue_model_never_publishable_and_lists_gaps(self):
        s = store()
        m = revenue_model(s, None, None)
        self.assertIsNone(m["commission_per_order"])
        self.assertIsNone(m["projected_revenue_per_month"])
        self.assertFalse(m["publishable"])
        self.assertGreaterEqual(len(m["missing_inputs"]), 3)

    def test_browse_path_does_not_receive_catchall_rate_in_economics(self):
        browse_path = "Home & Kitchen > Kitchen & Dining > Small Appliances > Fryers > Air Fryers"
        model = revenue_model(store(), browse_path, None)
        self.assertIsNone(model["commission_rate_pct"])
        self.assertIsNone(model["commission_per_order"])
        self.assertIn("product-specific commission category/rate (unverified)", model["missing_inputs"])

    def test_attribution_windows_match_policy(self):
        self.assertEqual(SESSION_HOURS, 24)
        s = store()
        rule = {r["id"]: r for r in s.program["attribution_rules"]}
        self.assertIn("89 days", rule["cart-window"]["claim"])
        self.assertIn("180 days", rule["ship-window"]["claim"])

    def test_rate_source_is_recorded(self):
        r = rate_for(store(), "Kitchen")
        self.assertIsNotNone(r)
        self.assertTrue(store().source_url("S1").startswith("https://affiliate-program.amazon.com/"))


class TestLinks(unittest.TestCase):
    def test_refuses_short_identifier(self):
        with self.assertRaises(LinkError):
            build_link("B04G1MEwY", host="www.amazon.com", tag="mine-20")

    def test_refuses_placeholder_and_missing_tags(self):
        with self.assertRaises(LinkError):
            validate_tag("amazon-20")
        with self.assertRaises(LinkError):
            validate_tag(None)
        with self.assertRaises(LinkError):
            validate_tag("not a tag")

    def test_refuses_unapproved_host(self):
        with self.assertRaises(LinkError):
            build_link("B0B7C327LK", host="www.ebay.com", tag="mine-20")

    def test_builds_tagged_link_and_safe_anchor(self):
        link = build_link("B0B7C327LK", host="www.amazon.com", tag="zone4demo-20", subtag="cmp-01")
        self.assertIn("tag=zone4demo-20", link.url)
        self.assertIn("ascsubtag=cmp-01", link.url)
        self.assertIn('rel="nofollow sponsored noopener"', link.anchor)

    def test_redirect_host_is_unsafe_for_affiliate_use(self):
        ok, why = is_safe_href("https://link.amazon/B04G1MEwY?tag=zone4demo-20")
        self.assertFalse(ok)
        self.assertIn("shortener", why)
        self.assertTrue(is_safe_href("https://www.amazon.com/dp/B0B7C327LK?tag=a-20")[0])

    def test_invalid_asin_on_amazon_dp_is_unsafe(self):
        ok, why = is_safe_href("https://www.amazon.com/dp/B04G1MEwY?tag=a-20")
        self.assertFalse(ok)
        self.assertIn("10-character", why)


class TestPolicyEngine(unittest.TestCase):
    def draft(self, body: str, links=None) -> Draft:
        return Draft(name="t", html=body, links=links or [],
                     verified_sources=["https://affiliate-program.amazon.com/help/operating/policies"])

    def test_missing_disclosure_is_blocking(self):
        f = evaluate(self.draft("<p>Buy this now.</p>"))
        self.assertIn("DISC-01", [x.rule_id for x in blocking(f)])

    def test_disclosure_and_link_level_token_pass(self):
        html = (f"<p>{REQUIRED_DISCLOSURE}</p><p>(paid link) "
                '<a href="https://www.amazon.com/dp/B0B7C327LK?tag=a-20">see it</a></p>')
        hard = blocking(evaluate(self.draft(html)))
        self.assertEqual([x.rule_id for x in hard], [])

    def test_price_alert_feature_is_blocked(self):
        f = evaluate(self.draft(f"<p>{REQUIRED_DISCLOSURE}</p><p>Get a notice when we track the price drop.</p>"))
        self.assertIn("PRICE-01", [x.rule_id for x in blocking(f)])

    def test_incentives_bot_traffic_selfpurchase_are_blocked(self):
        for body, rule in [
            ("Enter our sweepstakes to earn points for clicking", "TRAF-03"),
            ("Our script will auto click each link nightly", "TRAF-01"),
            ("Ask your family to buy it through my link to save", "TRAF-02"),
            ("Use this page content to train our model", "DATA-01"),
            ("Install our browser extension for overlays", "CHANNEL-02"),
            ("Bid on the keyword amazon for ads", "SEARCH-01"),
        ]:
            f = evaluate(self.draft(f"<p>{REQUIRED_DISCLOSURE}</p><p>{body}</p>"))
            self.assertIn(rule, [x.rule_id for x in blocking(f)], rule)

    def test_iframe_of_amazon_is_blocked(self):
        f = evaluate(self.draft(f"<p>{REQUIRED_DISCLOSURE}</p>"
                               '<iframe src="https://www.amazon.com/dp/B0B7C327LK"></iframe>'))
        self.assertIn("LINK-03", [x.rule_id for x in blocking(f)])

    def test_performance_claim_is_blocked(self):
        f = evaluate(self.draft(f"<p>{REQUIRED_DISCLOSURE}</p><p>We earn $4,000 per month.</p>"))
        self.assertTrue(any("earnings" in x.message for x in blocking(f)))

    def test_amazon_host_detection_boundaries(self):
        from engine.policy import is_amazon_host, mentions_amazon
        self.assertTrue(is_amazon_host("www.amazon.com"))
        self.assertTrue(is_amazon_host("link.amazon"))      # ".amazon" gTLD, source S12
        self.assertTrue(is_amazon_host("amzn.to"))
        self.assertFalse(is_amazon_host("notamazon.com"))   # must not false-positive
        self.assertFalse(is_amazon_host("amazon.example.org"))
        self.assertTrue(mentions_amazon('<a href="https://www.amazon.com/dp/B0B7C327LK">x</a>'))
        self.assertFalse(mentions_amazon('<a href="https://example.com/notamazon.com">x</a>'))

    def test_superlative_is_advisory_not_blocking(self):
        f = evaluate(self.draft(f"<p>{REQUIRED_DISCLOSURE}</p><p>The best air fryer.</p>"))
        self.assertIn("DATA-02", [x.rule_id for x in f])
        self.assertNotIn("DATA-02", [x.rule_id for x in blocking(f)])

    def test_matrix_covers_every_rule_and_is_cited(self):
        m = compliance_matrix()
        self.assertEqual(len(m), len(compliance_matrix()))
        self.assertGreaterEqual(len(m), 20)
        for row in m:
            self.assertTrue(row["source"].startswith("https://affiliate-program.amazon.com/"), row["id"])
            self.assertTrue(row["clause"], row["id"])


class TestResearchAndApi(unittest.TestCase):
    def test_probe_reports_blocked_without_network(self):
        r = AmazonProber().probe("B04G1MEwY")
        self.assertIs(r.status, Status.BLOCKED)
        self.assertIn("disabled", r.detail)

    def test_probe_url_shape(self):
        self.assertEqual(AmazonProber().url_for("B04G1MEwY"), "https://www.amazon.com/dp/B04G1MEwY")

    def test_api_client_unavailable_without_credentials(self):
        cfg = Config()
        cfg.oauth_client_id = cfg.oauth_client_secret = None
        client = CreatorsAPIClient(cfg)
        self.assertFalse(client.available)
        with self.assertRaises(RuntimeError):
            client.get_items(["B0B7C327LK"])

    def test_api_batch_limit_documented(self):
        cfg = Config()
        cfg.oauth_client_id = "x"
        cfg.oauth_client_secret = "y"
        with self.assertRaises(ValueError):
            CreatorsAPIClient(cfg).get_items([f"B00000000{i}" for i in range(11)])

    def test_api_operations_are_the_documented_four(self):
        self.assertEqual(set(CreatorsAPIClient.OPS),
                         {"SearchItems", "GetItems", "GetVariations", "GetBrowseNodes"})

    def test_no_credentials_no_fabricated_payload(self):
        cfg = Config()
        cfg.oauth_client_id = cfg.oauth_client_secret = None
        self.assertFalse(cfg.has_api_credentials)
        self.assertNotIn("partner_tag", json.dumps(cfg.redacted()).replace('"partner_tag": null', ""))


class TestScoring(unittest.TestCase):
    def test_full_inputs_produce_a_score(self):
        res = score_product("X", {"commission_rate_pct": 4.5, "price": 120, "star_rating": 4.6,
                                  "review_count": 800}, competitor_count=40)
        self.assertTrue(res.publishable)
        self.assertIsNotNone(res.value)
        self.assertTrue(res.rationale.startswith("Weighted sum"))

    def test_missing_inputs_withhold_the_score(self):
        res = score_product("X", {"commission_rate_pct": None, "price": None,
                                  "star_rating": 4.6, "review_count": 10})
        self.assertIsNone(res.value)
        self.assertEqual(res.display(), "")
        self.assertEqual(len(res.missing), 2)
        self.assertIn("Score withheld", res.rationale)

    def test_competition_needs_a_verified_set(self):
        res = score_product("X", {"commission_rate_pct": 3.0, "price": 60, "star_rating": 4.5,
                                  "review_count": 100})
        self.assertIsNone(res.value)
        self.assertTrue(any("competitor" in m for m in res.missing))

    def test_scores_for_the_three_products_are_withheld(self):
        s = store()
        report = Agent(store=s, cfg=Config()).run()
        self.assertTrue(report["scoring"])
        for _ref, v in report["scoring"].items():
            self.assertIsNone(v["score"])
            self.assertTrue(v["missing"])


class TestTracking(unittest.TestCase):
    def test_empty_ledger_yields_nulls_not_zeros(self):
        led = Ledger(None)
        roll = led.rollup()
        self.assertIsNone(roll["clicks"])
        self.assertIsNone(roll["earnings"])
        self.assertFalse(roll["connected"])
        self.assertIn("F-010", roll["empty_state"])

    def test_synthetic_events_are_refused(self):
        with self.assertRaises(EventError):
            Event(ts="2026-11-01T00:00:00Z", type="click", source="synthetic-example")

    def test_unknown_event_type_refused(self):
        with self.assertRaises(EventError):
            Event(ts="2026-11-01T00:00:00Z", type="purchase")

    def test_attribution_window_and_foreign_click_reset(self):
        led = Ledger(None)
        led.events = [
            Event(ts="2026-11-01T00:00:00Z", type="click", ref="P-01"),
            Event(ts="2026-11-02T04:00:00Z", type="order", ref="P-01", amount=9.0,
                  order_status="shipped"),        # 28h later → outside Session, not a cart order
            Event(ts="2026-11-03T00:00:00Z", type="click", ref="P-02"),
            Event(ts="2026-11-03T01:00:00Z", type="click", ref="P-02",
                  other_tag="someone-else-20"),
            Event(ts="2026-11-03T01:30:00Z", type="order", ref="P-02", amount=4.0,
                  order_status="shipped"),
        ]
        chains = led.sessions()
        self.assertEqual(len(chains), 3)
        first = chains[0]
        self.assertEqual([e.type for e in first], ["click", "order"])

    def test_rollup_counts_only_attributed_paid_orders(self):
        led = Ledger(None)
        led.events = [
            Event(ts="2026-11-01T00:00:00Z", type="impression", ref="P-01"),
            Event(ts="2026-11-01T00:05:00Z", type="click", ref="P-01"),
            Event(ts="2026-11-01T00:40:00Z", type="order", ref="P-01", amount=10.0,
                  order_status="shipped"),
            Event(ts="2026-11-01T00:41:00Z", type="order", ref="P-01", amount=5.0,
                  order_status="pending"),
        ]
        roll = led.rollup()
        self.assertEqual(roll["orders_attributed"], 2)
        self.assertEqual(roll["earnings"], 10.0)   # pending excluded
        self.assertEqual(roll["clicks"], 1)
        self.assertEqual(roll["earnings_per_click"], 10.0)

    def test_ledger_roundtrip_and_rejects_bad_line(self):
        tmp = Path(tempfile.mkdtemp()) / "tracking.jsonl"
        led = Ledger(tmp)
        led.append(Event(ts="2026-11-01T00:00:00Z", type="click", ref="P-01"))
        self.assertEqual(Ledger(tmp).load(), 1)
        tmp.write_text(tmp.read_text() + "{not json}\n")
        with self.assertRaises(EventError):
            Ledger(tmp).load()


class TestContentGeneration(unittest.TestCase):
    def setUp(self):
        self.s = store()
        self.ents = self.s.products()

    def test_review_marks_every_gap_as_placeholder(self):
        doc = product_review(self.s, self.ents[0])
        self.assertGreater(len(doc.placeholders), 5)
        self.assertTrue(doc.disclosures_present)
        self.assertNotIn("4.4", doc.body_html)

    def test_guide_cites_official_pages_in_each_step(self):
        doc = buying_guide(self.s, self.ents[0])
        self.assertGreaterEqual(doc.body_html.count("affiliate-program.amazon.com"), 3)
        self.assertIn("24 hours", doc.body_html)

    def test_seo_audit_flags_placeholders(self):
        doc = product_review(self.s, self.ents[0])
        checks = {c["check"]: c["pass"] for c in seo_audit(doc)}
        self.assertFalse(checks["No unverified placeholders left"])
        self.assertTrue(checks["Single H1 present"])
        self.assertTrue(checks["Amazon disclosure statement present"])
        self.assertTrue(checks["Title length 10–60 chars"])

    def test_json_ld_omits_ratings_when_unverified(self):
        doc = product_review(self.s, self.ents[0])
        ld = doc.json_ld()
        self.assertNotIn("about", ld)
        self.assertNotIn("aggregateRating", json.dumps(ld))
        ld2 = doc.json_ld(rating=4.4, review_count=1392)
        self.assertEqual(ld2["about"]["aggregateRating"]["ratingValue"], 4.4)


class TestSiteBuild(unittest.TestCase):
    def test_all_pages_render_and_pass_self_check(self):
        s = store()
        report = Agent(store=s, cfg=Config()).run()
        for fn in PAGES.values():
            html = fn(s, report)
            _self_check(html, fn.__name__)
            self.assertIn("preview.css", html)
            self.assertIn(REQUIRED_DISCLOSURE, html)

    def test_render_is_deterministic(self):
        s = store()
        report = Agent(store=s, cfg=Config()).run()
        self.assertEqual(page_rates(s, report), page_rates(s, report))
        self.assertEqual(page_verification(s, report), page_verification(s, report))

    def test_blank_cells_render_em_dash(self):
        s = store()
        html = page_rates(s, Agent(store=s, cfg=Config()).run())
        self.assertIn("class='blank'", html)
        self.assertNotIn(">None<", html)

    def test_self_check_catches_null_and_placeholder_leaks(self):
        with self.assertRaises(ValueError):
            _self_check("<td>None</td>", "x")
        with self.assertRaises(ValueError):
            _self_check("<p>[[UNVERIFIED: price — nope]]</p>", "x")

    def test_landing_page_puts_its_headline_before_the_shop_grid(self):
        """Document order (2026-11-19): one h1, first in <main>, then the products.

        The 2026-11-17 gate required the shop grid to precede the hero, which left
        the page's only <h1> below the first product card. This pins the corrected
        order so it cannot silently revert.
        """
        index = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        main = index[index.find('<main id="main">'):index.find('</main>')]
        self.assertEqual(main.count("<h1"), 1, "the landing page must carry exactly one h1")
        h1_at, shop_at = main.find("<h1"), main.find('id="shop"')
        self.assertNotEqual(h1_at, -1)
        self.assertNotEqual(shop_at, -1)
        self.assertLess(h1_at, shop_at, "the h1 must open <main>, before the shop grid")
        transparency_at = main.find('id="transparency"')
        if transparency_at != -1:
            self.assertLess(shop_at, transparency_at, "products must come before the audit band")

    def test_social_preview_card_exists_and_is_referenced(self):
        """F-79: the card and its tags had never shipped. Pin both."""
        card = ROOT / "docs" / "social-card.png"
        self.assertTrue(card.exists(), "docs/social-card.png is missing")
        self.assertGreater(card.stat().st_size, 4096)
        for page in sorted((ROOT / "docs").rglob("*.html")):
            text = page.read_text(encoding="utf-8")
            rel = page.relative_to(ROOT / "docs")
            self.assertIn('property="og:image"', text, str(rel))
            self.assertIn("social-card.png", text, str(rel))
            self.assertIn('name="twitter:image"', text, str(rel))

    def test_nav_links_cover_every_page(self):
        s = store()
        html = page_rates(s, Agent(store=s, cfg=Config()).run())
        for name in PAGES:
            self.assertIn(f'href="{name}"', html, name)

    def test_preview_build_passes_the_integrity_checker(self):
        """End-to-end: engine build → site integrity gate (what CI runs)."""
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            built = subprocess.run([sys.executable, "-m", "engine.cli", "build", "--out", td],
                                   cwd=str(ROOT), capture_output=True, text=True)
            self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
            res = subprocess.run([sys.executable, str(ROOT / "tools" / "check_links.py"),
                                  "--quiet", "--root", td],
                                 cwd=str(ROOT), capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_independent_qa_auditor_agrees(self):
        """qa/audit_site.py keeps its own official-host list; drift fails the build.

        It found exactly that when new sources were added to the data layer: the
        build gate passed while the QA auditor called the same rows unsourced.
        """
        import subprocess
        script = ROOT / "qa" / "audit_site.py"
        if not script.exists():
            self.skipTest("qa/audit_site.py not present on this branch yet")
        official = (ROOT / "scripts" / "verify.py").read_text()
        qa_src = script.read_text()
        for host in ("sell.amazon.com", "developers.google.com", "www.iana.org"):
            self.assertIn(host, qa_src, f"QA auditor is missing {host}, which verify.py accepts")
        res = subprocess.run([sys.executable, str(script)], cwd=str(ROOT), capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stdout[-1200:] + res.stderr[-600:])

    def test_published_docs_site_still_verifies(self):
        """The prior sessions' pipeline must stay green alongside the engine."""
        import subprocess
        for cmd in ([sys.executable, "scripts/build_site.py"], [sys.executable, "scripts/verify.py"]):
            if not (ROOT / cmd[1]).exists():
                self.skipTest(f"{cmd[1]} not present on this branch yet")
            res = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"{cmd[1]}: {res.stdout[-800:]}{res.stderr[-800:]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
