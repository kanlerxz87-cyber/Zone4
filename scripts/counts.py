#!/usr/bin/env python3
"""Derive every count the README publishes, from the data files themselves.

Why this exists: the README stated 7 articles, 36 suggestions, 44 questions and
51 flags at various points in 2026-11-16/17 while the registers held different
numbers. A count typed into prose drifts the moment a register grows. This script
is the single place a published number comes from, and `scripts/verify.py` checks
that the README table still agrees with its output.

Run: python3 scripts/counts.py [--json]
"""
from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def load(name: str) -> dict[str, Any]:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def flag_is_open(status: str) -> bool:
    """A flag is open unless it is resolved, corrected, or merely informational.

    The register's status field is free text, deliberately: a flag carries what
    actually happened, including the session that fixed it. This function is the
    one place that free text becomes a count, so the rule is stated once instead
    of being re-guessed in prose. Partly-built and needs-review items are OPEN:
    the site still does not do the thing, so hiding them behind a "closed"
    count would be the exact dishonesty the register exists to prevent.
    """
    t = status.strip().lower()
    return not (t.startswith("resolved") or t.startswith("corrected") or t.startswith("informational"))


def gather() -> dict[str, Any]:
    products = load("products.json")["products"]
    articles = load("marketing.json")["articles"]
    flags = load("flags.json")["flags"]
    suggestions = load("suggestions.json")["suggestions"]
    decisions = load("decisions.json")["decisions"]
    questions = load("questions.json")["questions"]
    requirements = load("requirements.json")["requirements"]
    sources = load("sources.json")["sources"]
    policies = load("policies.json")["rules"]
    content = load("content.json")
    events = load("tracking-events.json")["events"]
    pages = sorted((ROOT / "docs").rglob("*.html"))

    kinds = [a.get("page_type", "") for a in articles]
    return {
        "products": len(products),
        "articles": len(articles),
        "product_reviews": sum(1 for k in kinds if "product article" in k.lower()),
        "comparisons": sum(1 for k in kinds if "comparison" in k.lower()),
        "guides": sum(1 for k in kinds if "buying guide" in k.lower()),
        "pages": len(pages),
        "flags": len(flags),
        "flags_open": sum(1 for f in flags if flag_is_open(f["status"])),
        "suggestions": len(suggestions),
        "decisions": len(decisions),
        "decisions_recorded": sum(1 for d in decisions if d["status"].startswith("Recorded")),
        "questions": len(questions),
        "questions_known": sum(1 for q in questions if q["kind"] == "Known"),
        "requirements": len(requirements),
        "sources": len(sources),
        "policies": len(policies),
        "findings": len(content["analysis"]),
        "events": len(events),
    }


def main() -> int:
    stats = gather()
    if "--json" in sys.argv:
        print(json.dumps(stats, indent=2))
        return 0
    width = max(len(k) for k in stats)
    for k, v in stats.items():
        print(f"{k.replace('_', ' '):<{width}}  {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
