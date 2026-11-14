"""Load, validate, and expose ``data/*.json`` — the workspace's only data source.

The loader is deliberately strict: a row that claims to be verified without a
resolvable official source id is a hard error, not a warning. That is what makes
"verify line by line" an enforced property of the build instead of a promise in
prose.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .claims import Claim, Entity, Source, Status, VerificationReport

#: Review queue order, most urgent first. An unknown severity sorts last
#: rather than raising, so a new label can never break a build.
SEVERITY_ORDER = ["blocker", "high", "medium", "low", "info"]

PRODUCT_FIELDS: list[tuple[str, str]] = [
    ("product_name", "Product name"),
    ("brand", "Brand"),
    ("category", "Category"),
    ("browse_node", "Browse node"),
    ("price", "Price"),
    ("currency", "Currency"),
    ("availability", "Availability"),
    ("star_rating", "Star rating"),
    ("review_count", "Review count"),
    ("best_sellers_rank", "Best Sellers rank"),
    ("coupon_or_deal", "Coupon / deal"),
    ("shipping_promise", "Shipping promise"),
    ("commission_rate_pct", "Commission rate %"),
    ("estimated_earning_per_unit", "Est. earning per unit (USD)"),
    ("demand_trend", "Demand trend"),
    ("competition_level", "Competition level"),
    ("review_velocity", "Review velocity"),
    ("excluded_product_check", "Excluded-Products check"),
]

CHECK_LABELS: dict[str, str] = {
    "identifier_length": "ASIN format check",
    "product_page_probe": "Amazon product-page probe",
    "host_resolution": "Supplied host resolution",
    "link_followed_from_sandbox": "Redirect followed from sandbox",
}


class DataError(RuntimeError):
    """Raised when the data layer would let an unsupported value through."""


def _read(path: Path) -> Any:
    if not path.exists():
        raise DataError(f"Missing required data file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover
        raise DataError(f"{path} is not valid JSON: {exc}") from exc


class Datastore:
    """Verified facts for the site, the engine, and CI checks."""

    def __init__(self, data_dir: Path | str) -> None:
        self.data_dir = Path(data_dir)
        self.sources_raw = _read(self.data_dir / "engine-sources.json")
        self.program = _read(self.data_dir / "engine-program.json")
        self.findings = _read(self.data_dir / "engine-verification.json")
        self.sources: dict[str, Source] = self._load_sources()
        self.audit()

    # -- loading ---------------------------------------------------------
    def _load_sources(self) -> dict[str, Source]:
        out: dict[str, Source] = {}
        for s in self.sources_raw.get("sources", []):
            out[s["id"]] = Source(
                id=s["id"],
                title=s.get("title", ""),
                url=s.get("url", ""),
                publisher=s.get("publisher", ""),
                retrieved=s.get("retrieved", ""),
                note=s.get("note", ""),
            )
        if not out:
            raise DataError("engine-sources.json contains no sources; nothing can be verified.")
        return out

    def source_for(self, source_id: str | None) -> Source | None:
        if not source_id:
            return None
        return self.sources.get(source_id)

    # -- integrity gate --------------------------------------------------
    def audit(self) -> list[str]:
        """Check every row that asserts a fact points at a real source id.

        Returns the list of problems found (also raised as ``DataError`` so a
        build cannot pass with a broken citation).
        """
        problems: list[str] = []

        for section in ("commission_caps", "attribution_rules", "legal_clauses",
                        "data_access", "identity_rules", "payment_and_account"):
            rows = self.program.get(section, [])
            if isinstance(rows, dict):
                rows = rows.get("prerequisites", []) + rows.get("technical", []) + rows.get("identity_rules", [])
            for row in rows:
                self._check_row(section, row, problems)

        for row in self.program.get("prohibitions", []):
            if not row.get("source_id") or row["source_id"] not in self.sources:
                problems.append(f"prohibitions/{row.get('id')}: no resolvable source_id")

        for table_key in ("commission_table", "bounty_events"):
            table = self.program.get(table_key, {})
            sid = table.get("source_id")
            if sid not in self.sources:
                problems.append(f"{table_key}: source_id {sid!r} not in sources.json")
            for row in table.get("rows", []):
                for key, val in row.items():
                    if val is None and key != "rate_usd":
                        problems.append(f"{table_key} row {row}: blank value {key!r}")

        for probe in self.findings.get("products", []):
            for check, detail in probe.get("checks", {}).items():
                if detail.get("status") in ("PASS", "FAIL") and detail.get("source_id") and \
                        detail["source_id"] not in self.sources:
                    problems.append(f"{probe['ref']}/{check}: unknown source_id")

        for flag in self.findings.get("flags", []):
            if not flag.get("evidence"):
                problems.append(f"flag {flag.get('id')}: no evidence URL recorded")

        if problems:
            raise DataError("Data integrity check failed:\n  - " + "\n  - ".join(problems))
        return problems

    def _check_row(self, section: str, row: dict, problems: list[str]) -> None:
        status = row.get("status", "unverified")
        sid = row.get("source_id")
        if status.startswith("verified") and (not sid or sid not in self.sources):
            problems.append(f"{section}/{row.get('id')}: status {status} without a resolvable source")
        if status == "unverified" and row.get("value") is not None:
            problems.append(f"{section}/{row.get('id')}: marked unverified but carries a value")

    # -- product entities ------------------------------------------------
    def products(self) -> list[Entity]:
        entities: list[Entity] = []
        for probe in self.findings.get("products", []):
            attrs = probe.get("attributes", {})
            # The display name is itself a claim: use it only when the probe
            # recorded the official page it came from, otherwise fall back to
            # the bare identifier rather than a title nobody sourced.
            named = attrs.get("product_name")
            title = None
            if isinstance(named, dict) and named.get("value") and named.get("source_id") in self.sources:
                title = named["value"]
            ent = Entity(ref=probe["ref"], name=title or f"Product {probe['identifier']}",
                         notes=probe.get("why_blank", ""))
            ent.resolved_asin = probe.get("resolved_asin")
            ent.notes = probe.get("why_blank", "")
            for key, label in PRODUCT_FIELDS:
                value = attrs.get(key)
                # A value only reaches a published page when the probe recorded
                # the official page it was read from. Two shapes are accepted:
                #   {"value": X, "source_id": "S15"}  -> verified, publishes X
                #   {"withheld": true, "reason": ...}  -> blank on purpose
                # Anything else (a bare value, or None) stays withheld so a
                # guess can never flow through this path.
                if isinstance(value, dict) and value.get("source_id") in self.sources \
                        and value.get("value") is not None:
                    ent.add(Claim(
                        key=key, label=label, value=value["value"], status=Status.VERIFIED,
                        source=self.sources[value["source_id"]],
                        quote=value.get("quote", "Read from the official Amazon product page."),
                        flag=value.get("flag"), reason=value.get("reason", ""),
                    ))
                    continue
                withheld = value if isinstance(value, dict) else {}
                ent.add(Claim(
                    key=key, label=label, value=None, status=Status.UNVERIFIED,
                    flag=withheld.get("flag") or probe.get("flag"),
                    reason=withheld.get("reason") or probe.get("why_blank", ""),
                ))
            ent.add(Claim(
                key="identifier", label="Identifier from supplied URL",
                value=probe["identifier"], status=Status.VERIFIED,
                source=self.sources["S13"], quote="Parsed from the path of the supplied link.",
            ))
            ent.add(Claim(
                key="supplied_url", label="Supplied link",
                value=probe["supplied_url"], status=Status.VERIFIED,
                source=self.sources["S13"], quote="Recorded exactly as provided by the user.",
            ))
            for check, detail in probe.get("checks", {}).items():
                st = {
                    "PASS": Status.VERIFIED, "FAIL": Status.VERIFIED, "BLOCKED": Status.BLOCKED,
                }.get(detail["status"], Status.UNVERIFIED)
                ent.add(Claim(
                    key=f"check_{check}", label=CHECK_LABELS.get(check, check),
                    value=None if st is Status.BLOCKED else detail["status"],
                    status=Status.VERIFIED if st is not Status.BLOCKED else Status.BLOCKED,
                    source=self.source_for(detail.get("source_id")) if st is not Status.BLOCKED else None,
                    quote=detail.get("detail", ""),
                    flag=probe.get("flag"),
                    reason=detail.get("detail", ""),
                ))
            entities.append(ent)
        return entities

    def report(self) -> VerificationReport:
        rep = VerificationReport()
        for ent in self.products():
            rep.add(ent)
        return rep

    # -- program lookups -------------------------------------------------
    def commission_rows(self) -> list[dict]:
        return self.program["commission_table"]["rows"]

    def rate_for_category(self, category: str | None) -> float | None:
        """Exact-match lookup against the official table.

        Returns ``None`` when the category is unknown or absent — never a
        default rate, never a guess. Callers must handle ``None``.
        """
        if not category:
            return None
        needle = category.strip().lower()
        for row in self.commission_rows():
            for part in row["categories"].split(","):
                if part.strip().lower() == needle:
                    return float(row["rate_pct"])
        # Do not apply the table's catch-all rate to an unknown or broad browse
        # path. It is only available when the caller explicitly names the
        # official "All Other Categories" band, which was handled above.
        return None

    def bounties(self) -> list[dict]:
        return self.program["bounty_events"]["rows"]

    def flags(self) -> list[dict]:
        return sorted(self.findings.get("flags", []),
                      key=lambda f: (SEVERITY_ORDER.index(f.get("severity", "low"))
                          if f.get("severity", "low") in SEVERITY_ORDER else len(SEVERITY_ORDER),
                          f["id"]))

    def flag(self, flag_id: str) -> dict | None:
        for f in self.findings.get("flags", []):
            if f["id"] == flag_id:
                return f
        return None

    def source_url(self, source_id: str | None) -> str:
        s = self.source_for(source_id)
        return s.url if s else ""

    def niche_scoring(self) -> dict:
        return self.findings.get("niche_scoring", {})
