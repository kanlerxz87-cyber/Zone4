"""The orchestrator: research → verify → model → draft → gate → publish queue.

Run it and it produces a report of what is publishable and what is blocked, with
reasons. It never publishes past a blocking gate, and it never writes an
invented number into a page.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .claims import Status
from .config import Config
from .content import buying_guide, comparison, product_review, seo_audit
from .datastore import Datastore
from .economics import revenue_model, rate_for
from .policy import Draft, blocking, evaluate
from .research import run as research_run
from .scoring import score_all
from .tracking import Ledger


@dataclass
class PublishItem:
    doc_slug: str
    path: str
    ready: bool
    reasons: list[str] = field(default_factory=list)
    seo: list[dict] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"slug": self.doc_slug, "path": self.path, "ready": self.ready,
                "reasons": self.reasons, "seo": self.seo, "findings": self.findings}


class Agent:
    def __init__(self, store: Datastore | None = None, cfg: Config | None = None,
                 ledger_path: Path | None = None, site_base: str = "https://kanlerxz87-cyber.github.io/Zone4") -> None:
        self.cfg = cfg or Config.load()
        self.store = store or Datastore(self.cfg.data_dir)
        self.ledger = Ledger(ledger_path or (self.cfg.data_dir / "tracking.jsonl"))
        self.site_base = site_base

    # -- stages ----------------------------------------------------------
    def stage_research(self, allow_network: bool = False) -> dict:
        return research_run(self.store, self.cfg, allow_network=allow_network)

    def stage_economics(self, entities) -> dict:
        out = {}
        for ent in entities:
            cat_claim = ent.get("category")
            price_claim = ent.get("price")
            category = cat_claim.value if cat_claim and cat_claim.status is Status.VERIFIED else None
            price = price_claim.value if price_claim and price_claim.status is Status.VERIFIED else None
            out[ent.ref] = revenue_model(self.store, category, price)
        return out

    def stage_scoring(self, entities) -> dict:
        return score_all(self.store, entities)

    def stage_tracking(self) -> dict:
        return self.ledger.rollup()

    def stage_content(self, entities) -> list:
        docs = []
        for ent in entities:
            docs.append(product_review(self.store, ent, self.site_base))
            docs.append(buying_guide(self.store, ent, self.site_base))
        if len(entities) > 1:
            docs.append(comparison(self.store, entities, self.site_base))
        return docs

    def stage_gate(self, docs) -> list[PublishItem]:
        items: list[PublishItem] = []
        for doc in docs:
            draft = Draft(
                name=doc.slug,
                html=doc.to_html(),
                text="",
                verified_sources=[s.url for s in self.store.sources.values()],
                price_display_enabled=self.cfg.price_display_allowed,
            )
            findings = evaluate(draft)
            hard = blocking(findings)
            placeholders = doc.placeholders
            reasons = []
            if placeholders:
                # Keep the marker token out of published copy: a page that describes the
                # gate must not itself contain the token the gate searches for.
                first = placeholders[0].replace("[[UNVERIFIED:", "pending:").replace("]]", "")[:90]
                reasons.append(f"{len(placeholders)} unverified field(s) must be resolved or removed "
                               f"(first: {first})")
            for f in hard:
                reasons.append(f"{f.rule_id}: {f.message}")
            for chk in seo_audit(doc):
                if not chk["pass"]:
                    reasons.append(f"SEO gate: {chk['check']} (value {chk['value']})")
            items.append(PublishItem(
                doc_slug=doc.slug, path=f"content/{doc.slug}.html",
                ready=not reasons,          # any open reason blocks publication
                reasons=reasons, seo=seo_audit(doc),
                findings=[f"{f.rule_id}·{f.severity}" for f in findings],
            ))
        return items

    # -- pipeline --------------------------------------------------------
    def run(self, allow_network: bool = False) -> dict:
        research = self.stage_research(allow_network=allow_network)
        entities = self.store.products()
        items = self.stage_gate(self.stage_content(entities))
        report = {
            "generated_note": "Deterministic build: figures come from data/*.json, not from run time.",
            "verified_at_utc": self.store.findings.get("verified_at_utc"),
            "research": research,
            "verification": self.store.report().summary(),
            "economics": self.stage_economics(entities),
            "scoring": self.stage_scoring(entities),
            "tracking": self.stage_tracking(),
            "publish_queue": [i.to_dict() for i in items],
            "publish_gate": {
                "open": all(i.ready for i in items) and self.store.report().publishable(),
                "blocked_items": sum(1 for i in items if not i.ready),
                "policy": "require_clean_verification="
                          f"{self.cfg.require_clean_verification}, price_display_allowed="
                          f"{self.cfg.price_display_allowed}",
            },
            "flags_open": len(self.store.flags()),
        }
        return report

    def write_report(self, dest: Path | None = None) -> Path:
        dest = dest or (self.cfg.data_dir / "report.json")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(self.run(), indent=2, sort_keys=True))
        return dest


def cli_snapshot() -> dict:  # pragma: no cover - convenience for notebooks
    return {"now": datetime.now(timezone.utc).isoformat(timespec="seconds")}
