"""Runtime configuration.

Everything optional stays optional: the platform must run with no credentials,
no network and no Associates account, and in that state it must refuse to
produce claims rather than fabricate them.

Set real values through environment variables — never commit them.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("ZONE4_DATA_DIR", REPO_ROOT / "data"))

#: Locale hostnames Amazon Associates registers separately (source S5 locale
#: reference table). Add the marketplace only when you hold an approved tag
#: for it — see flag F-008 about the differing official wording.
KNOWN_MARKETPLACES = {
    "US": "www.amazon.com",
    "CA": "www.amazon.ca",
    "UK": "www.amazon.co.uk",
    "DE": "www.amazon.de",
    "FR": "www.amazon.fr",
    "IT": "www.amazon.it",
    "ES": "www.amazon.es",
    "NL": "www.amazon.nl",
    "PL": "www.amazon.pl",
    "SE": "www.amazon.se",
    "JP": "www.amazon.co.jp",
}

#: Hosts that are legitimately Amazon destinations. ``link.amazon`` is
#: deliberately absent: the ".amazon" gTLD is Amazon's (source S12) but a
#: shortener/redirect host must never be embedded as the final href, because
#: Participation Requirements P-w bars link shortening used so that the Amazon
#: destination is unclear (source S2).
ALLOWED_DESTINATION_HOSTS = {
    "www.amazon.com",
    "smile.amazon.com",
    "www.amazon.co.uk",
    "www.amazon.de",
    "www.amazon.fr",
    "www.amazon.it",
    "www.amazon.es",
}


@dataclass
class MarketplaceConfig:
    """One Associates locale. ``partner_tag`` must be your own registered tag."""

    code: str = "US"
    host: str = "www.amazon.com"
    partner_tag: str | None = None
    store_id: str | None = None
    #: Creators API access threshold, verified from source S4: "at least 10
    #: qualifying sales within the past 30 days". Kept as config because the
    #: official API-rates page was not retrieved (flag F-007).
    api_sales_required: int = 10
    api_tps: int | None = None      # unverified on purpose — see F-007
    api_tpd: int | None = None      # unverified on purpose — see F-007
    price_cache_max_seconds: int | None = None  # unverified on purpose — F-006


@dataclass
class Config:
    root: Path = field(default_factory=lambda: REPO_ROOT)
    data_dir: Path = field(default_factory=lambda: DATA_DIR)
    marketplace: MarketplaceConfig = field(default_factory=MarketplaceConfig)
    #: Publishing gate: when False, ``agent.publish_queue`` refuses to emit any
    #: draft that carries an unresolved flag.
    require_clean_verification: bool = True
    #: Price display is gated off until F-006 is resolved against the official
    #: Participation Requirements text.
    price_display_allowed: bool = False
    #: OAuth client-credentials only (source S14). No secrets in this file.
    creators_api_base: str = "https://creatorsapi.amazon"
    oauth_client_id: str | None = field(
        default_factory=lambda: os.environ.get("ZONE4_OAUTH_CLIENT_ID")
    )
    oauth_client_secret: str | None = field(
        default_factory=lambda: os.environ.get("ZONE4_OAUTH_CLIENT_SECRET")
    )

    @property
    def has_api_credentials(self) -> bool:
        return bool(self.oauth_client_id and self.oauth_client_secret)

    @property
    def has_partner_tag(self) -> bool:
        return bool(self.marketplace.partner_tag)

    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        """Read ``config.json`` if present, then apply environment overrides.

        Missing config file is normal — the platform runs credential-less.
        """
        cfg = cls()
        candidate = path or (REPO_ROOT / "config.json")
        if Path(candidate).exists():
            raw = json.loads(Path(candidate).read_text())
            mp = raw.pop("marketplace", {})
            for k, v in raw.items():
                if hasattr(cfg, k):
                    setattr(cfg, k, v)
            for k, v in mp.items():
                if hasattr(cfg.marketplace, k):
                    setattr(cfg.marketplace, k, v)
        # Tag resolution order, most explicit first:
        #   1. ZONE4_PARTNER_TAG in the environment (never committed);
        #   2. config.json (gitignored);
        #   3. the tag published on the site, data/products.json -> associates_tag.
        # Step 3 exists so the engine and the published pages cannot disagree
        # about which tag is in use. It is a published identifier, not a secret:
        # it appears in every outbound link on the site by design.
        tag = os.environ.get("ZONE4_PARTNER_TAG")
        if tag:
            cfg.marketplace.partner_tag = tag
        elif not cfg.marketplace.partner_tag:
            try:
                products = json.loads((cfg.data_dir / "products.json").read_text(encoding="utf-8"))
                published = (products.get("products") or [{}])[0].get("associates_tag")
            except (OSError, ValueError, KeyError):
                published = None
            if published:
                cfg.marketplace.partner_tag = published
        host = os.environ.get("ZONE4_AMAZON_HOST")
        if host:
            cfg.marketplace.host = host
        return cfg

    def redacted(self) -> dict:
        """Config safe to print in reports/CI logs."""
        return {
            "marketplace": {
                "code": self.marketplace.code,
                "host": self.marketplace.host,
                "partner_tag": "***" if self.has_partner_tag else None,
                "api_sales_required": self.marketplace.api_sales_required,
                "api_tps": self.marketplace.api_tps,
                "api_tpd": self.marketplace.api_tpd,
                "price_cache_max_seconds": self.marketplace.price_cache_max_seconds,
            },
            "require_clean_verification": self.require_clean_verification,
            "price_display_allowed": self.price_display_allowed,
            "api_credentials_present": self.has_api_credentials,
        }
