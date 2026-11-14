#!/usr/bin/env python3
"""Build the static GitHub Pages site in docs/ from data/*.json.

Standard library only. Output is deterministic, so CI can confirm that the
committed docs/ matches the data (see scripts/verify.py and the Site checks workflow).
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import sys
from types import SimpleNamespace

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pages_extra import build_pages  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "docs"

DISCLOSURE_SENTENCE = "As an Amazon Associate I earn from qualifying purchases."
DISCLOSURE_SOURCE = "https://affiliate-program.amazon.com/help/operating/agreement"
PUBLISHER_SOURCE = "https://affiliate-program.amazon.com/help/operating/policies"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


PRODUCTS = load("products.json")["products"]
SOURCES_DOC = load("sources.json")
SOURCES = {s["id"]: s for s in SOURCES_DOC["sources"]}
NON_OFFICIAL = SOURCES_DOC["non_official_reference_only"]
RULES = load("policies.json")["rules"]
FLAGS_DOC = load("flags.json")
FLAGS = FLAGS_DOC["flags"]
FLAG_BY_ID = {f["id"]: f for f in FLAGS}
CONTENT = load("content.json")
REQUIREMENTS_DOC = load("requirements.json")
REQUIREMENTS = REQUIREMENTS_DOC["requirements"]
OBSERVED = CONTENT["observed_date"]
MARKETING = CONTENT["marketing"]
BRIEF_COVERAGE = CONTENT["requirements"]
PLATFORM = CONTENT["platform"]
NICHE = CONTENT["niche"]
REVERIF = CONTENT["reverification"]
AMAZON_DISCLAIMER = CONTENT["amazon_text_disclaimer"]

NAV = [
    ("index.html", "Dashboard"),
    ("executive-summary.html", "Executive summary"),
    ("requirements.html", "Requirements"),
    ("products.html", "All products"),
    ("categories/dual-basket-air-fryers.html", "Dual-basket air fryers"),
    ("categories/single-basket-air-fryers.html", "Single-basket air fryers"),
    ("categories/air-fryer-toaster-ovens.html", "Air-fry toaster ovens"),
    ("analysis.html", "Analysis & findings"),
    ("analytics.html", "Analytics"),
    ("marketing.html", "Marketing content (drafts)"),
    ("platform.html", "Platform & automation"),
    ("brief-coverage.html", "Brief coverage (Q-trace)"),
    ("verification.html", "Verification log"),
    ("reverification.html", "Re-verification pass"),
    ("policy-compliance.html", "Policy compliance"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
]


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def pill(label: str, kind: str) -> str:
    return f'<span class="pill pill-{kind}">{esc(label)}</span>'


def status_pill(status: str) -> str:
    s = status.lower()
    if s.startswith("delivered"):
        kind = "ok"
    elif s.startswith("not built"):
        kind = "bad" if "needs access" in s else "muted"
    elif s.startswith("unverifiable"):
        kind = "warn"
    elif s.startswith("verified") or s.startswith("implemented") or s.startswith("informational"):
        kind = "ok"
    elif "withheld" in s or "not applicable" in s:
        kind = "muted"
    elif s.startswith("not met"):
        kind = "bad"
    elif s.startswith("unverified") or "not verifiable" in s:
        kind = "warn"
    elif "needs" in s or "open" in s or "review" in s:
        kind = "bad"
    else:
        kind = "muted"
    return pill(status, kind)


class Page:
    def __init__(self, path: str, title: str, active: str, body: str):
        self.path = path
        self.title = title
        self.active = active
        self.body = body

    @property
    def depth(self) -> int:
        return self.path.count("/")

    def rel(self, target: str) -> str:
        return "../" * self.depth + target


def href(current: Page, target: str, text: str | None = None, extra: str = "") -> str:
    """Link to another site page from `current`, relative to its folder."""
    label = esc(text if text is not None else target)
    return f'<a href="{esc(current.rel(target))}"{extra}>{label}</a>'


def ext(url: str, text: str | None = None, extra: str = "") -> str:
    label = esc(text if text is not None else url)
    return f'<a href="{esc(url)}" rel="noopener noreferrer"{extra}>{label}</a>'


def source_label(url: str) -> str:
    for s in SOURCES.values():
        if s["url"] == url:
            return s["id"]
    return url.rstrip("/").split("/")[-1].split("?")[0] or url


def table(headers: list[str], rows: list[list[str]], klass: str = "") -> str:
    head = "".join(f"<th scope=\"col\">{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return (
        f'<div class="table-wrap"><table class="{esc(klass)}"><thead><tr>{head}</tr></thead>'
        f"<tbody>{body}</tbody></table></div>"
    )


def flag_chip(current: Page, fid: str) -> str:
    return f'<a class="flag-chip" href="{esc(current.rel("flagged.html"))}#{esc(fid)}">{esc(fid)}</a>'


def competitor_links(p: dict) -> str:
    return "<br>".join(ext(c["url"], c["asin"]) for c in p["competitors"])


def shop_link(p: dict) -> str:
    return ext(p["short_link"], "Open Amazon link", ' class="shop"')


# ---------------------------------------------------------------- tables

def draft_anchor(current: Page, pid: str) -> str:
    """Link from a product row to its marketing draft anchor on the content page."""
    return f'<a href="{esc(current.rel("marketing.html"))}#C-{esc(pid)}">C-{esc(pid)} draft</a>'


def product_table(current: Page, products: list[dict]) -> str:
    headers = [
        "ID", "Product (source link)", "ASIN", "Brand (as shown)", "Subcategory", "Category (Amazon path)",
        "Capacity (as listed)", "Dimensions (as listed)", "Price", "Star rating", "Commission rate",
        "Trend / conversion", "Competition: also-viewed ASINs", "Affiliate link", "Marketing draft", "Flags",
    ]
    rows = []
    for p in products:
        rows.append([
            esc(p["id"]),
            ext(p["canonical_url"], p["name_short"]),
            esc(p["asin"]),
            esc(p["brand"]),
            esc(p["subcategory"]),
            esc(p["category_path"]),
            esc(p["capacity"]),
            esc(p["dimensions"]),
            pill("Withheld (F-02)", "muted"),
            pill("Withheld (F-02)", "muted"),
            pill("Unverified (F-01)", "warn"),
            pill("Unverified (F-15)", "warn"),
            competitor_links(p),
            shop_link(p) + f'<div class="note">{esc(DISCLOSURE_SENTENCE)}</div>',
            draft_anchor(current, p["id"]),
            " ".join(flag_chip(current, f) for f in p["flags"]),
        ])
    return table(headers, rows, "products")


# What the independent second pass (reverification.html) concluded for each field.
RECHECK = {
    "Listing title": "V-04/V-05/V-06 re-confirmed",
    "ASIN": "V-01/V-02/V-03 re-confirmed",
    "Brand (Item details)": "Byline not re-read; Item details value carried (F-18)",
    "Manufacturer (Item details)": "Carried forward (F-18)",
    "Category path": "V-07 re-confirmed",
    "Capacity (as listed)": "Carried forward (F-18)",
    "Dimensions (as listed)": "Carried forward (F-18)",
    "Colour (as listed)": "Carried forward (F-18)",
    "Material (as listed)": "Carried forward (F-18)",
    "Also-viewed ASINs": "V-08/V-09/V-10 re-confirmed",
    "Price": "Re-confirmed withheld",
    "Star rating / review count": "Re-confirmed withheld",
    "Category commission rate": "V-20 still behind sign-in",
    "Trend / conversion": "No official source found",
    "Associates tag in site link": "Re-confirmed: source links carry no tag",
    "Associates tag in link": "V-11 re-confirmed: no tag",
}


def recheck_pill(text: str) -> str:
    if text.startswith("Carried forward") or "carried" in text:
        return pill(text, "warn")
    if text.startswith("Re-confirmed") or text.startswith("V-"):
        return pill(text, "ok")
    return pill(text, "muted")


def verification_rows(current: Page) -> list[list[str]]:
    rows = []
    for p in PRODUCTS:
        src = ext(p["canonical_url"], "Amazon page")
        short = ext(p["short_link"], "Short link")
        sched = ext(SOURCES["S-SCHED"]["url"], "Commission schedule (sign-in)")
        items = [
            ("Listing title", p["name_listing"], "Verified", src, ""),
            ("ASIN", p["asin"], "Verified (from resolved URL)", short, "F-04"),
            ("Brand (Item details)", p["brand"], "Verified (Item details)" if p["id"] == "P2" else "Verified (earlier session; Item details not re-read, F-18)", src, "F-05" if p["id"] == "P2" else "F-18"),
            ("Manufacturer (Item details)", p.get("manufacturer") or "Blank", "Verified (Item details)" if p.get("manufacturer") else "Unverified (blank)", src, "" if p.get("manufacturer") else "F-21"),
            ("Category path", p["category_path"], "Verified", src, ""),
            ("Capacity (as listed)", p["capacity"], "Verified as listed (earlier session; not re-read, F-18)", src, "F-06" if p["id"] in ("P1", "P2") else ("F-08" if p["id"] == "P3" else "F-18")),
            ("Dimensions (as listed)", p["dimensions"], "Verified as listed", src, ""),
            ("Colour (as listed)", p["color"], "Verified as listed", src, "F-07" if p["id"] == "P1" else ""),
            ("Material (as listed)", p["material"], "Verified as listed", src, ""),
            ("Also-viewed ASINs", ", ".join(c["asin"] for c in p["competitors"]), "Verified as shown (re-read 2026-11-14)" + ("; Sponsored label on some reads" if p["id"] in ("P2", "P3") else ""), src, "F-10" if p["id"] in ("P2", "P3") else ""),
            ("Price", "Not published", "Withheld (policy)", src, "F-02"),
            ("Star rating / review count", "Not published", "Withheld (policy)", src, "F-02"),
            ("Category commission rate", "Blank", "Unverified", sched, "F-01"),
            ("Trend / conversion", "Blank", "Unverified", src, "F-15"),
            ("Associates tag in link", "Not visible in resolved URL", "Unverified", short, "F-03"),
        ]
        for field, value, status, source, flag in items:
            flag_html = flag_chip(current, flag) if flag else ""
            recheck = RECHECK.get(field, "")
            rows.append([esc(p["id"]), esc(field), esc(value), status_pill(status), recheck_pill(recheck), source, flag_html])
    return rows


def policy_rows(current: Page) -> list[list[str]]:
    rows = []
    for r in RULES:
        rows.append([
            esc(r["id"]),
            esc(r["requirement"]),
            ext(r["source_url"], r["source_ref"]),
            status_pill(r["status"]),
            (f'<blockquote class="quote">{esc(r["verified_quote"])}</blockquote>'
             f'<div class="note">{esc(r["reverified"])}</div>' if r.get("verified_quote")
             else '<span class="muted small">No verbatim quote recorded for this row.</span>'),
            esc(r["site_implementation"]),
        ])
    return rows


def requirement_rows(current: Page) -> list[list[str]]:
    rows = []
    for r in REQUIREMENTS:
        sources = "<br>".join(ext(u, source_label(u)) for u in r["sources"])
        flags = r.get("flags") or []
        rows.append([
            f'<span id="{esc(r["id"])}"><strong>{esc(r["id"])}</strong></span>',
            esc(r["area"]),
            esc(r["requirement"]),
            status_pill(r["status"]),
            esc(r["delivered"]) or '<span class="muted">Nothing published yet.</span>',
            esc(r["blocker"]) or '<span class="muted">None.</span>',
            sources,
            " ".join(flag_chip(current, f) for f in flags) or '<span class="muted">-</span>',
        ])
    return rows


def page_requirements(current: Page) -> str:
    counts: dict[str, int] = {}
    for r in REQUIREMENTS:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    order = sorted(counts, key=lambda k: (-counts[k], k))
    kpi_html = "".join(
        f'<div class="kpi"><div class="kpi-value">{esc(str(counts[k]))}</div><div class="kpi-label">{esc(k)}</div></div>'
        for k in order
    )
    meaning = "".join(
        f"<li><strong>{esc(k)}</strong> - {esc(v)}</li>"
        for k, v in REQUIREMENTS_DOC["_meta"]["status_meanings"].items()
    )
    return (
        hero("Requirements", "Every requirement in the project brief, one row each, with what this site actually delivers, what blocks it, and the official source for that status. Nothing is marked Delivered unless it is live on the site.")
        + f'<section class="kpis">{kpi_html}</section>'
        + f'<section><h2>What the statuses mean</h2><ul class="small">{meaning}</ul></section>'
        + table(["ID", "Area", "Requirement", "Status", "Delivered on this site", "Blocker or gap (official rule)", "Official sources", "Flags"], requirement_rows(current), "requirements")
        + f'<p class="small muted">Assessed {esc(REQUIREMENTS_DOC["_meta"]["as_of_utc"])} (UTC). Blocked does not mean skipped without reason: each blocked row names the official rule that gates it.</p>'
    )


def flag_table(current: Page) -> str:
    rows = []
    for f in FLAGS:
        sources = "<br>".join(ext(u, source_label(u)) for u in f["sources"])
        rows.append([
            f'<span id="{esc(f["id"])}"><strong>{esc(f["id"])}</strong></span>',
            pill(f["severity"], {"High": "bad", "Medium": "warn"}.get(f["severity"], "muted")),
            esc(f["title"]),
            esc(f["detail"]),
            sources,
            status_pill(f["status"]),
            esc(f["action"]),
        ])
    return table(["ID", "Severity", "Issue", "Detail", "Source links", "Status", "Action requested"], rows, "flags")


def analysis_rows() -> list[list[str]]:
    rows = []
    for a in CONTENT["analysis"]:
        sources = "<br>".join(ext(u, source_label(u)) for u in a["sources"])
        rows.append([esc(a["id"]), esc(a["finding"]), esc(a["basis"]), status_pill(a["confidence"]), sources])
    return rows


def source_rows() -> list[list[str]]:
    rows = []
    for s in SOURCES.values():
        rows.append([
            esc(s["id"]),
            ext(s["url"], s["title"]),
            esc(s["publisher"]),
            pill("Yes" if s["accessible"] else "No", "ok" if s["accessible"] else "warn"),
            esc(s["used_for"]),
            esc(s.get("reverified", "Not re-read in the second pass")),
            esc(s.get("notes", "")),
        ])
    return rows


def non_official_note() -> str:
    items = "".join(
        f"<li>{esc(n['title'])} ({esc(n['url'])}): {esc(n['reason'])}</li>" for n in NON_OFFICIAL
    )
    return (
        '<section><h2>Non-official references (not used as data)</h2>'
        '<p class="small muted">Shown as plain text, not links, because they are not official sources.</p>'
        f"<ul class=\"small\">{items}</ul></section>"
    )


# ---------------------------------------------------------------- page bodies

def hero(title: str, lead: str) -> str:
    return f'<header class="hero"><h1>{esc(title)}</h1><p class="lead">{esc(lead)}</p></header>'


def page_index(current: Page) -> str:
    open_flags = len([f for f in FLAGS if "review" in f["status"].lower() and "resolved" not in f["status"].lower()])
    kpis = [
        ("3 of 3", "Products with verified ASIN and category (P2 brand from Item details, F-05)"),
        (str(len(REVERIF["checks"])), "Checks in the second, independent verification pass"),
        (str(len(MARKETING["articles"]) + 2), "Marketing drafts written (3 articles, comparison, buying guide)"),
        (str(len(REQUIREMENTS)), "Requirements from the brief traced to evidence"),
        ("0", "Amazon prices or star ratings published (policy F-02)"),
        (str(open_flags), f"Open items in the {len(FLAGS)} flags for your review"),
    ]
    kpi_html = "".join(f'<div class="kpi"><div class="kpi-value">{esc(v)}</div><div class="kpi-label">{esc(l)}</div></div>' for v, l in kpis)
    cards = [
        ("categories/dual-basket-air-fryers.html", "Dual-basket air fryers", "P1: CHEFMAN 6 Quart Dual Basket Air Fryer Oven"),
        ("categories/single-basket-air-fryers.html", "Single-basket air fryers", "P3: Chefman Air Fryer 8 Qt TurboFry 4-in-1"),
        ("categories/air-fryer-toaster-ovens.html", "Air-fry toaster ovens", "P2: Emeril Lagasse 26QT French Door Air Fryer Toaster Oven"),
        ("requirements.html", "Requirements", "All 30 brief items: delivered, blocked or unverifiable"),
        ("products.html", "All products (table)", "Every row links to its Amazon source"),
        ("analysis.html", "Analysis & findings", "Niche, competition, what can and cannot be concluded"),
        ("verification.html", "Verification log", "Field-by-field check with source and status"),
        ("marketing.html", "Marketing content (drafts)", "Articles, comparison and buying guide, sentence by sentence"),
        ("platform.html", "Platform & automation", "Pipeline stages, gates, guardrails, niche method"),
        ("brief-coverage.html", "Brief coverage (Q-01 to Q-26)", "This session's trace of the brief, item by item, in data/content.json"),
        ("reverification.html", "Re-verification pass", "Second, independent check of every published value"),
        ("flagged.html", "Flagged for review", "Irregularities and unverified items, with sources"),
    ]
    card_html = "".join(
        f'<a class="card" href="{esc(current.rel(t))}"><div class="card-title">{esc(name)}</div><div class="card-sub">{esc(sub)}</div></a>'
        for t, name, sub in cards
    )
    bullets = "".join(f"<li>{esc(b)}</li>" for b in CONTENT["executive_summary"]["bullets"][:6])
    return (
        hero("Amazon affiliate product research", CONTENT["executive_summary"]["headline"])
        + f'<section class="kpis">{kpi_html}</section>'
        + '<section><h2>Key findings</h2><ul class="bullets">' + bullets + "</ul>"
        + f'<p>{href(current, "executive-summary.html", "Read the full executive summary →")}</p></section>'
        + '<section><h2>Explore</h2><div class="cards">' + card_html + "</div></section>"
        + f'<p class="muted small">Data observed {esc(OBSERVED)} (UTC). Verification scope and method: {href(current, "sources.html", "sources")}.</p>'
    )


def page_exec(current: Page) -> str:
    es = CONTENT["executive_summary"]
    bullets = "".join(f"<li>{esc(b)}</li>" for b in es["bullets"])
    decisions = "".join(f"<li>{esc(d)}</li>" for d in es["decisions_needed"])
    not_built = "".join(f"<li>{esc(d)}</li>" for d in CONTENT["not_built"])
    return (
        hero("Executive summary", es["headline"])
        + f'<section><h2>What the verification found</h2><ul class="bullets">{bullets}</ul></section>'
        + f'<section><h2>Decisions needed from you</h2><ol>{decisions}</ol></section>'
        + f'<section><h2>Not built, and why</h2><ul>{not_built}</ul></section>'
        + f'<section><h2>Detail</h2><p>See {href(current, "analysis.html", "Analysis & findings")}, {href(current, "flagged.html", "Flagged for review")} and {href(current, "sources.html", "Sources")}.</p></section>'
    )


def page_products(current: Page) -> str:
    return (
        hero("All products", "One row per user-supplied link. Prices and ratings are withheld under the Associates policy. Commission rates and trend data are unverified and blank.")
        + '<p><input id="filter" class="filter" type="search" placeholder="Filter rows (for example: Chefman, B0C…, Flag F-02)" aria-label="Filter table"></p>'
        + product_table(current, PRODUCTS)
        + '<p class="small muted">Every row links to its Amazon product page as the source. Short links are the links you supplied.</p>'
    )


def page_category(current: Page, key: str) -> str:
    cat = CONTENT["categories"][key]
    prods = [p for p in PRODUCTS if p["id"] in cat["product_ids"]]
    headers = ["ID", "Product (source link)", "ASIN", "Brand (as shown)", "Capacity (as listed)", "Dimensions (as listed)", "Competition: also-viewed ASINs", "Affiliate link", "Flags"]
    rows = []
    for p in prods:
        rows.append([
            esc(p["id"]), ext(p["canonical_url"], p["name_listing"]), esc(p["asin"]), esc(p["brand"]),
            esc(p["capacity"]), esc(p["dimensions"]), competitor_links(p),
            shop_link(p) + f'<div class="note">{esc(DISCLOSURE_SENTENCE)}</div>',
            " ".join(flag_chip(current, f) for f in p["flags"]),
        ])
    return (
        hero(cat["title"], cat["intro"])
        + table(headers, rows, "products")
        + f'<section><h2>Category notes</h2><p>All products here sit under the Amazon path <em>{esc(prods[0]["category_path"])}</em>. See {href(current, "analysis.html", "Analysis & findings")} for the cross-category view.</p></section>'
    )


def page_analysis(current: Page) -> str:
    return (
        hero("Analysis & findings", "Every finding states its basis and confidence. Where a value is unverified, the finding says so instead of estimating it.")
        + table(["ID", "Finding", "Basis", "Confidence", "Source links"], analysis_rows(), "analysis")
        + f'<p class="small muted">Niche scoring method and its blank inputs: {href(current, "platform.html", "Platform & automation")}. '
        + f'Marketing drafts built on these findings: {href(current, "marketing.html", "Marketing content")}.</p>'
    )


def page_verification(current: Page) -> str:
    return (
        hero("Verification log", "Field-by-field check for each product. Each row links to the official source it was checked against. Blank or withheld values are flagged.")
        + '<p><input id="filter" class="filter" type="search" placeholder="Filter rows (for example: P2, Unverified, F-02)" aria-label="Filter table"></p>'
        + table(["Product", "Field", "Value", "Status", "Second-pass re-check", "Source link", "Flag"], verification_rows(current), "verification")
        + f'<p class="small muted">Observed {esc(OBSERVED)} (UTC). The verified fields are as shown on the Amazon page at that time. Re-check before publishing.</p>'
    )


def page_policy(current: Page) -> str:
    return (
        hero("Policy compliance", "Amazon Associates and FTC requirements checked against this site. Each row links to its official source section.")
        + table(["ID", "Requirement", "Source (official)", "Status on this site", "Verbatim text from the source", "How the site complies"], policy_rows(current), "policy")
    )


def page_flagged(current: Page) -> str:
    return (
        '<header class="hero flagged-hero"><h1>Flagged for Review</h1>'
        '<p class="lead">These irregularities and unverified items are published for your review after the site is live. '
        "They do not block the merge. Each one links to its source, and the action column says what is needed.</p></header>"
        + flag_table(current)
    )


def page_sources(current: Page) -> str:
    return (
        hero("Sources", "Every source used, with whether it was read during this verification pass. Unread sources are marked No and nothing is inferred from them.")
        + table(["ID", "Source (link)", "Publisher", "Read?", "Used for", "Second-pass re-check", "Notes"], source_rows(), "sources")
        + non_official_note()
    )


BODIES = {
    "index.html": page_index,
    "executive-summary.html": page_exec,
    "requirements.html": page_requirements,
    "products.html": page_products,
    "categories/dual-basket-air-fryers.html": lambda c: page_category(c, "dual-basket-air-fryers"),
    "categories/single-basket-air-fryers.html": lambda c: page_category(c, "single-basket-air-fryers"),
    "categories/air-fryer-toaster-ovens.html": lambda c: page_category(c, "air-fryer-toaster-ovens"),
    "analysis.html": page_analysis,
    "verification.html": page_verification,
    "policy-compliance.html": page_policy,
    "flagged.html": page_flagged,
    "sources.html": page_sources,
}


SITE_CTX = SimpleNamespace(
    esc=esc, ext=ext, table=table, pill=pill, hero=hero, href=href, flag_chip=flag_chip,
    status_pill=status_pill, products=PRODUCTS, marketing=MARKETING, requirements=BRIEF_COVERAGE,
    platform=PLATFORM, niche=NICHE, reverif=REVERIF, disclosure=DISCLOSURE_SENTENCE,
    policies_url=PUBLISHER_SOURCE,
)
BODIES.update(build_pages(SITE_CTX))


def render(page: Page) -> str:
    nav_items = []
    for target, label in NAV:
        cls = ' class="active" aria-current="page"' if target == page.path else ""
        nav_items.append(f'<a href="{esc(page.rel(target))}"{cls}>{esc(label)}</a>')
    nav = "".join(nav_items)
    disclosure = (
        f'<div class="disclosure" role="note"><strong>Disclosure:</strong> {esc(DISCLOSURE_SENTENCE)} '
        f'<span class="small">(Source: '
        f'{ext(DISCLOSURE_SOURCE, "Associates Operating Agreement, Section 5")}) '
        "This site is not endorsed by or affiliated with Amazon.</span></div>"
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(page.title)} | Amazon affiliate product research</title>
<meta name="description" content="Verified research on three Amazon air-fryer product links, with sources, flags and policy checks.">
<link rel="stylesheet" href="{esc(page.rel('styles.css'))}">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="layout">
<aside class="sidebar">
  <a class="brand" href="{esc(page.rel('index.html'))}">Affiliate research</a>
  <nav aria-label="Main">{nav}</nav>
</aside>
<div class="content">
{disclosure}
<main id="main">
{page.body}
</main>
<footer>
  <p class="small disclaimer">{esc(AMAZON_DISCLAIMER["text"])} <span class="muted">({ext(AMAZON_DISCLAIMER["source"], AMAZON_DISCLAIMER["source_ref"])})</span></p>
  <p class="small">Data observed {esc(OBSERVED)} (UTC). Source of truth: the data/ folder in the repository. Build: scripts/build_site.py. Checks: scripts/verify.py.</p>
</footer>
</div>
</div>
<script src="{esc(page.rel('app.js'))}"></script>
</body>
</html>
"""


def build() -> list[pathlib.Path]:
    OUT.mkdir(exist_ok=True)
    (OUT / "categories").mkdir(exist_ok=True)
    written = []
    for path, body_fn in BODIES.items():
        title = next(label for target, label in NAV if target == path)
        page = Page(path, title, path, "")
        page.body = body_fn(page)
        out = OUT / path
        out.write_text(render(page), encoding="utf-8")
        written.append(out)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    return written


if __name__ == "__main__":
    for p in build():
        print("wrote", p.relative_to(ROOT))
