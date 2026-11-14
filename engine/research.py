"""Product intake: identifier checks, live probes, and the Creators API client.

Offline by default. With no OAuth credentials the client raises rather than
returning stand-in data, and the probe path degrades to ``BLOCKED`` — the
difference between "Amazon has no such page" (a verified FAIL) and "this
environment cannot reach the network" (BLOCKED) is preserved on purpose.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from .claims import (Claim, Entity, Status, extract_identifier, validate_asin_format)
from .config import Config
from .datastore import PRODUCT_FIELDS, Datastore
from .links import build_link

AMAZON_404_MARKER = "Sorry! We couldn't find that page"
# IP License Section 4(c): any agent that accesses Program Content must put
# "Agent/[agent name]" in the user agent string of every HTTP and HTTPS request,
# and must not conceal that it is an agent. Flag F-21.
USER_AGENT = "Agent/zone4-research (evidence-first affiliate research)"


@dataclass
class ProbeResult:
    url: str
    status: Status
    detail: str
    source_url: str | None = None

    @property
    def found_product_page(self) -> bool:
        return self.status is Status.VERIFIED


class AmazonProber:
    """Checks whether an identifier maps to a real product detail page."""

    def __init__(self, host: str = "www.amazon.com", timeout: float = 10.0,
                 allow_network: bool = False) -> None:
        self.host = host
        self.timeout = timeout
        self.allow_network = allow_network

    def url_for(self, identifier: str) -> str:
        return f"https://{self.host}/dp/{identifier}"

    def probe(self, identifier: str) -> ProbeResult:
        url = self.url_for(identifier)
        if not self.allow_network:
            return ProbeResult(url, Status.BLOCKED,
                               "Network probe disabled in this environment; not re-run here.")
        try:  # pragma: no cover - exercised only with network access
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read(200_000).decode("utf-8", "replace")
            if AMAZON_404_MARKER in body:
                return ProbeResult(url, Status.VERIFIED,
                                   "Amazon returned its 'Page Not Found' error document for this identifier.", url)
            if 'id="productTitle"' in body or "productTitle" in body:
                return ProbeResult(url, Status.VERIFIED, "Amazon returned a product detail page.", url)
            return ProbeResult(url, Status.UNVERIFIED,
                               "Response received but it did not match a product page or Amazon's error page; "
                               "treat as unverified.", url)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return ProbeResult(url, Status.VERIFIED, "Amazon returned HTTP 404 for this identifier.", url)
            return ProbeResult(url, Status.BLOCKED, f"HTTP {exc.code} from Amazon; inconclusive.", url)
        except Exception as exc:  # noqa: BLE001 - any transport failure is BLOCKED, not FAIL
            return ProbeResult(url, Status.BLOCKED, f"Transport failure ({type(exc).__name__}); no conclusion.", url)


class CreatorsAPIClient:
    """Minimal, credentials-first wrapper over the four documented operations.

    Documented shape (sources S4, S14): OAuth 2.0 client-credentials, then
    ``GetItems`` / ``SearchItems`` / ``GetVariations`` / ``GetBrowseNodes``, with
    batching of up to 10 ids per call, and ``x-marketplace`` selecting the locale.
    Quotas are deliberately not assumed here — see flag F-007.
    """

    OPS = ("SearchItems", "GetItems", "GetVariations", "GetBrowseNodes")
    MAX_BATCH = 10

    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self._token: str | None = None

    @property
    def available(self) -> bool:
        return self.cfg.has_api_credentials

    def _require(self) -> None:
        if not self.available:
            raise RuntimeError(
                "Creators API credentials are not configured (ZONE4_OAUTH_CLIENT_ID / "
                "ZONE4_OAUTH_CLIENT_SECRET). This platform will not substitute scraped or "
                "invented product data. Access also requires an approved Associates account "
                "with at least 10 qualifying sales in the past 30 days for this marketplace."
            )

    def get_items(self, asins: list[str]) -> dict[str, Any]:  # pragma: no cover
        self._require()
        if len(asins) > self.MAX_BATCH:
            raise ValueError(f"GetItems accepts at most {self.MAX_BATCH} item ids per call (source S14).")
        for a in asins:
            ok, why = validate_asin_format(a)
            if not ok:
                raise ValueError(f"Refusing API call: {why}")
        raise RuntimeError(
            "Live API transport is intentionally not enabled in this workspace: no OAuth token "
            "endpoint or credential set has been validated here. Configure credentials and re-run "
            "with network access to complete the wiring."
        )


def intake_links(store: Datastore, cfg: Config | None = None, prober: AmazonProber | None = None,
                 allow_network: bool = False) -> list[Entity]:
    """Rebuild product entities, optionally re-probing Amazon live."""
    entities = store.products()
    if not allow_network or prober is None:
        return entities
    for ent in entities:
        ident = ent.get("identifier")
        if not ident or ident.value is None:
            continue
        res = prober.probe(str(ident.value))
        ent.add(Claim(key="live_probe", label="Live product-page probe",
                      value=res.status.value,
                      status=Status.VERIFIED if res.status is not Status.BLOCKED else Status.BLOCKED,
                      reason=res.detail))
    return entities


def build_links_for(entities: list[Entity], cfg: Config) -> list[dict]:
    """Attempt compliant Special Links for any entity with a *valid* ASIN."""
    out: list[dict] = []
    for ent in entities:
        ident = ent.get("identifier")
        value = str(ident.value) if ident and ident.value else ""
        ok, why = validate_asin_format(value)
        if not ok:
            out.append({"ref": ent.ref, "ok": False, "detail": why, "url": None})
            continue
        try:
            link = build_link(value, host=cfg.marketplace.host, tag=cfg.marketplace.partner_tag or "")
            out.append({"ref": ent.ref, "ok": True, "detail": "Link built from a 10-character ASIN.",
                        "url": link.url})
        except Exception as exc:  # noqa: BLE001
            out.append({"ref": ent.ref, "ok": False, "detail": str(exc), "url": None})
    return out


def run(store: Datastore, cfg: Config | None = None, allow_network: bool = False) -> dict:
    """Full research pass → JSON-safe report consumed by the site build."""
    cfg = cfg or Config.load()
    entities = intake_links(store, cfg,
                            prober=AmazonProber(cfg.marketplace.host, allow_network=allow_network),
                            allow_network=allow_network)
    total = sum(len(e.claims) for e in entities)
    verified = sum(e.verified_count() for e in entities)
    report = {
        "entities": [e.ref for e in entities],
        "summary": {
            "entities": len(entities),
            "claims_total": total,
            "claims_verified": verified,
            "claims_withheld": total - verified,
            "verification_rate": round(verified / total, 4) if total else 0.0,
            "publishable": bool(entities) and all(
                c.status.publishable for e in entities for c in e.claims.values()),
        },
        "links": build_links_for(entities, cfg),
        "api_available": CreatorsAPIClient(cfg).available,
        "config": cfg.redacted(),
        "field_labels": dict(PRODUCT_FIELDS),
    }
    return json.loads(json.dumps(report, default=str))
