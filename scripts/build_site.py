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

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "docs"

DISCLOSURE_SENTENCE = "As an Amazon Associate I earn from qualifying purchases."
DISCLOSURE_SOURCE = "https://affiliate-program.amazon.com/help/operating/agreement"
SITE_TITLE_SUFFIX = "Zone4 affiliate research"
SITE_DESCRIPTION = (
    "Verified affiliate research on three countertop air fryers: product records, marketing content, "
    "analysis, policy checks and an official source link on every table row."
)


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
MARKETING = load("marketing.json")
PIPELINE = load("pipeline.json")
REQUIREMENTS_DOC = load("requirements.json")
REQUIREMENTS = REQUIREMENTS_DOC["requirements"]
OBSERVED = CONTENT["observed_date"]

NAV = [
    ("index.html", "Dashboard"),
    ("executive-summary.html", "Executive summary"),
    ("products.html", "All products"),
    ("categories/dual-basket-air-fryers.html", "Dual-basket air fryers"),
    ("categories/single-basket-air-fryers.html", "Single-basket air fryers"),
    ("categories/air-fryer-toaster-ovens.html", "Air-fry toaster ovens"),
    ("marketing.html", "Marketing content"),
    ("automation.html", "Automation & tracking"),
    ("analysis.html", "Analysis & findings"),
    ("requirements.html", "Requirements"),
    ("verification.html", "Verification log"),
    ("policy-compliance.html", "Policy compliance"),
    ("analytics.html", "Analytics"),
    ("flagged.html", "Flagged for review"),
    ("sources.html", "Sources"),
]


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def pill(label: str, kind: str) -> str:
    return f'<span class="pill pill-{kind}">{esc(label)}</span>'


def status_pill(status: str) -> str:
    s = status.lower()
    if s.startswith("verified") or s.startswith("implemented") or s.startswith("informational"):
        kind = "ok"
    elif "withheld" in s or "not applicable" in s:
        kind = "muted"
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
    ids = [s["id"] for s in SOURCES.values() if s["url"] == url]
    if ids:
        return ", ".join(ids)
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
    return ext(p["short_link"], "Open Amazon link",
               f' class="shop" data-track="click" data-track-target="{esc(p["short_link"])}" data-track-asin="{esc(p["asin"])}"')


# ---------------------------------------------------------------- tables

def product_table(current: Page, products: list[dict]) -> str:
    headers = [
        "ID", "Product (source link)", "ASIN", "Brand (as shown)", "Subcategory", "Category (Amazon path)",
        "Capacity (as listed)", "Dimensions (as listed)", "Colour / material / special features (as listed)",
        "Price", "Star rating", "Commission rate", "Trend / conversion",
        "Competition: also-viewed ASINs", "Affiliate link", "Flags",
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
            esc(p["color"]) + "<br>" + esc(p["material"]) + "<br>" + esc(p.get("special_feature", "")),
            pill("Withheld (F-02)", "muted"),
            pill("Withheld (F-02)", "muted"),
            pill("Unverified (F-01)", "warn"),
            pill("Unverified (F-15)", "warn"),
            competitor_links(p),
            shop_link(p) + f'<div class="note">{esc(DISCLOSURE_SENTENCE)}</div>',
            " ".join(flag_chip(current, f) for f in p["flags"]),
        ])
    return table(headers, rows, "products")


# Per-product flag mapping for the verification log.
PRODUCT_FLAGS = {
    "P1": {"capacity": "F-06", "colour": "F-07", "competitors": "F-10", "variant": ""},
    "P2": {"capacity": "F-06", "colour": "", "competitors": "F-10", "variant": "F-26"},
    "P3": {"capacity": "F-08", "colour": "", "competitors": "F-10", "variant": ""},
}


def verification_rows(current: Page) -> list[list[str]]:
    rows = []
    for p in PRODUCTS:
        src = ext(p["canonical_url"], "Amazon page")
        short = ext(p["short_link"], "Short link")
        sched = ext(SOURCES["S-SCHED"]["url"], "Commission schedule (sign-in)")
        fl = PRODUCT_FLAGS[p["id"]]
        items = [
            ("Listing title", p["name_listing"], "Verified", src, ""),
            ("ASIN", p["asin"], "Verified (from resolved URL)", short, "F-04"),
            ("Brand", p["brand"], "Verified", src, ""),
            ("Manufacturer", p.get("manufacturer") or "Blank", "Verified (Item details)" if p.get("manufacturer") else "Unverified (blank)", src, "" if p.get("manufacturer") else "F-28"),
            ("Model number", p.get("model_number") or "Blank", "Verified (Item details)" if p.get("model_number") else "Unverified (blank)", src, "" if p.get("model_number") else "F-28"),
            ("Category path", p["category_path"], "Verified", src, ""),
            ("Capacity (as listed)", p["capacity"], "Verified as listed", src, fl["capacity"]),
            ("Dimensions (as listed)", p["dimensions"], "Verified as listed", src, ""),
            ("Colour (as listed)", p["color"], "Verified as listed", src, fl["colour"]),
            ("Material (as listed)", p["material"], "Verified as listed", src, ""),
            ("Special features (as listed)", p.get("special_feature", ""), "Verified as listed", src, ""),
            ("Also-viewed ASINs", ", ".join(c["asin"] for c in p["competitors"]), "Verified as shown", src, fl["competitors"]),
            ("Price", "Not published", "Withheld (policy)", src, "F-02"),
            ("Star rating / review count", "Not published", "Withheld (policy)", src, "F-02"),
            ("Category commission rate", "Blank", "Unverified", sched, "F-01"),
            ("Trend / conversion", "Blank", "Unverified", src, "F-15"),
            ("Associates tag in link", "Not visible in resolved URL", "Unverified", short, "F-03"),
        ]
        if fl["variant"]:
            items.append(("Cooking function count", "Two counts stated on the page", "Unresolved", src, fl["variant"]))
        if p.get("brand_note"):
            items.append(("Brand / manufacturer note", p["brand_note"], "Verified note", src, ""))
        for field, value, status, source, flag in items:
            flag_html = flag_chip(current, flag) if flag else ""
            rows.append([esc(p["id"]), esc(field), esc(value), status_pill(status), source, flag_html])
    return rows


def policy_rows(current: Page) -> list[list[str]]:
    rows = []
    for r in RULES:
        rows.append([
            esc(r["id"]),
            esc(r["requirement"]),
            ext(r["source_url"], r["source_ref"]),
            status_pill(r["status"]),
            esc(r["site_implementation"]),
        ])
    return rows


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


def marketing_fact_table(article: dict) -> str:
    rows = []
    for f in article["facts"]:
        note = f'<div class="note">{esc(f["note"])}</div>' if f.get("note") else ""
        rows.append([
            esc(f["id"]),
            esc(f["field"]),
            esc(f["value"]) if f["value"] else '<span class="muted">Blank - withheld or unverified</span>',
            ext(f["source_url"], f["source_ref"]),
            note,
        ])
    return table(["ID", "Field", "Value as listed", "Source (official)", "Note"], rows, "facts")


def marketing_keyword_table(article: dict) -> str:
    rows = []
    for k in article["target_keywords"]:
        rows.append([
            esc(k["term"]),
            esc(k["intent"]),
            '<span class="muted">Not published</span>',
            esc(k["volume_status"]),
            ext(k["source_url"], "Official source for the term's category"),
        ])
    return table(["Target keyword", "Search intent", "Search volume", "Volume status", "Source (official)"], rows, "keywords")


def marketing_article(current: Page, article: dict) -> str:
    facts_by_id = {f["id"]: f for f in article["facts"]}
    body_html = []
    for para in article["body"]:
        cites = "".join(
            f'<a class="cite" href="{esc(facts_by_id[fid]["source_url"])}" rel="noopener noreferrer">{esc(fid)}</a>'
            for fid in para["fact_ids"] if fid in facts_by_id
        )
        body_html.append(f'<p>{esc(para["text"])} <span class="cites">{cites}</span></p>')
    outline_html = "".join(
        f'<li><strong>{esc(o["h2"])}</strong> - {esc(o["purpose"])} '
        f'<span class="muted">(facts: {esc(", ".join(o["facts_used"]))})</span></li>'
        for o in article["outline"]
    )
    seo_html = (
        "<dl class=\"seo\">"
        f"<dt>Suggested URL slug</dt><dd><code>{esc(article['slug'])}</code></dd>"
        f"<dt>Title tag</dt><dd>{esc(article['title_tag'])}</dd>"
        f"<dt>Meta description</dt><dd>{esc(article['meta_description'])}</dd>"
        f"<dt>H1</dt><dd>{esc(article['h1'])}</dd>"
        f"<dt>Page type</dt><dd>{esc(article['page_type'])}</dd>"
        "</dl>"
    )
    notes_html = "".join(f"<li>{esc(n)}</li>" for n in article["compliance_notes"])
    cta = article["cta"]
    cta_button = ext(cta["link_url"], cta["link_label"], ' class="shop"')
    # The disclosure sits in the same paragraph as the affiliate link, so it is
    # unmistakable and adjacent rather than separated by a line break.
    cta_html = (
        f'<div class="cta"><p>{esc(cta["text"])}</p>'
        f'<p>{cta_button} <span class="note"><strong>Disclosure:</strong> {esc(cta["disclosure"])}</span></p></div>'
    )
    return (
        f'<article class="doc" id="{esc(article["id"])}">'
        f'<h3>{esc(article["id"])} - {esc(article["h1"])}</h3>'
        f"{seo_html}"
        f"<h4>Keyword targets</h4>{marketing_keyword_table(article)}"
        f"<h4>Outline</h4><ul class=\"outline\">{outline_html}</ul>"
        f"<h4>Draft copy</h4>{''.join(body_html)}"
        f"<h4>Call to action</h4>{cta_html}"
        f"<h4>Fact basis (every row links to its official source)</h4>{marketing_fact_table(article)}"
        f"<h4>Compliance notes</h4><ul>{notes_html}</ul>"
        "</article>"
    )


def marketing_seo_rules_table() -> str:
    rows = []
    for r in MARKETING["seo_rules"]:
        rows.append([esc(r["id"]), esc(r["rule"]), ext(r["source_url"], r["source_ref"]), esc(r["applied"])])
    return table(["ID", "Rule (official)", "Source (official)", "How this site applies it"], rows, "seo-rules")


def marketing_checklist_table() -> str:
    rows = []
    for c in MARKETING["publishing_checklist"]:
        rows.append([esc(c["step"]), esc(c["detail"]), ext(c["source_url"], c["source_ref"])])
    return table(["Step", "What to do", "Source (official)"], rows, "checklist")


# ---------------------------------------------------------------- page bodies

def hero(title: str, lead: str) -> str:
    return f'<header class="hero"><h1>{esc(title)}</h1><p class="lead">{esc(lead)}</p></header>'


def page_index(current: Page) -> str:
    open_flags = [f for f in FLAGS if "review" in f["status"].lower() and "resolved" not in f["status"].lower()]
    kpis = [
        ("3 of 3", "Products with verified ASIN, category and specification table (P2 brand unresolved, F-05)"),
        ("5", "Marketing pages built: 3 articles, 1 comparison, 1 buying guide"),
        ("0", "Amazon prices published (policy F-02)"),
        ("0 of 3", "Commission rates verified (F-01)"),
        (str(len(open_flags)), "Open items for your review (Flagged for review page)"),
    ]
    kpi_html = "".join(
        f'<div class="kpi"><div class="kpi-value">{esc(v)}</div><div class="kpi-label">{esc(l)}</div></div>'
        for v, l in kpis
    )
    cards = [
        ("categories/dual-basket-air-fryers.html", "Dual-basket air fryers", "P1: CHEFMAN 6 Quart Dual Basket Air Fryer Oven"),
        ("categories/single-basket-air-fryers.html", "Single-basket air fryers", "P3: Chefman Air Fryer 8 Qt TurboFry 4-in-1"),
        ("categories/air-fryer-toaster-ovens.html", "Air-fry toaster ovens", "P2: Emeril Lagasse 26QT French Door Air Fryer Toaster Oven"),
        ("products.html", "All products (table)", "Every row links to its Amazon source"),
        ("marketing.html", "Marketing content", "Articles, a comparison and a buying guide, ready to publish"),
        ("automation.html", "Automation & tracking", "The pipeline, the metrics and what blocks each stage"),
        ("analysis.html", "Analysis & findings", "Niche, competition, what can and cannot be concluded"),
        ("verification.html", "Verification log", "Field-by-field check with source and status"),
        ("flagged.html", "Flagged for review", "Irregularities and unverified items, with sources"),
    ]
    card_html = "".join(
        f'<a class="card" href="{esc(current.rel(t))}"><div class="card-title">{esc(name)}</div>'
        f'<div class="card-sub">{esc(sub)}</div></a>'
        for t, name, sub in cards
    )
    bullets = "".join(f"<li>{esc(b)}</li>" for b in CONTENT["executive_summary"]["bullets"][:5])
    return (
        hero("Affiliate product research", CONTENT["executive_summary"]["headline"])
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
        + '<section><h2>Detail</h2><p>See '
        + href(current, "analysis.html", "Analysis & findings") + ", "
        + href(current, "marketing.html", "Marketing content") + ", "
        + href(current, "automation.html", "Automation & tracking") + ", "
        + href(current, "flagged.html", "Flagged for review") + " and "
        + href(current, "sources.html", "Sources") + ".</p></section>"
    )


def page_products(current: Page) -> str:
    return (
        hero("All products", "One row per user-supplied link. Prices and ratings are withheld under the Associates policy. Commission rates and trend data are unverified and blank.")
        + '<p><input id="filter" class="filter" type="search" placeholder="Filter rows (for example: Chefman, B0C…, Flag F-02)" aria-label="Filter table"></p>'
        + product_table(current, PRODUCTS)
        + '<p class="small muted">Every row links to its Amazon product page as the source. Short links are the links you supplied. '
        'Competitor labels are short paraphrases; the exact listing titles are on the linked pages (F-20).</p>'
    )


def page_category(current: Page, key: str) -> str:
    cat = CONTENT["categories"][key]
    prods = [p for p in PRODUCTS if p["id"] in cat["product_ids"]]
    headers = ["ID", "Product (source link)", "ASIN", "Brand (as shown)", "Capacity (as listed)",
               "Dimensions (as listed)", "Special features (as listed)",
               "Competition: also-viewed ASINs", "Affiliate link", "Flags"]
    rows = []
    for p in prods:
        rows.append([
            esc(p["id"]), ext(p["canonical_url"], p["name_listing"]), esc(p["asin"]), esc(p["brand"]),
            esc(p["capacity"]), esc(p["dimensions"]), esc(p.get("special_feature", "")),
            competitor_links(p),
            shop_link(p) + f'<div class="note">{esc(DISCLOSURE_SENTENCE)}</div>',
            " ".join(flag_chip(current, f) for f in p["flags"]),
        ])
    return (
        hero(cat["title"], cat["intro"])
        + table(headers, rows, "products")
        + f'<section><h2>Category notes</h2><p>All products here sit under the Amazon path <em>{esc(prods[0]["category_path"])}</em>. '
        f'See {href(current, "analysis.html", "Analysis & findings")} for the cross-category view and '
        f'{href(current, "marketing.html", "Marketing content")} for the copy written for this category.</p></section>'
    )


def page_marketing(current: Page) -> str:
    excluded = "".join(f"<li>{esc(e)}</li>" for e in MARKETING["_meta"]["excluded"])
    articles = "".join(marketing_article(current, a) for a in MARKETING["articles"])
    return (
        hero("Marketing content", "Ready-to-publish pages for the three supplied products: one article each, a comparison page and a buying guide. "
             "Every factual statement is a row in a fact table with an official source link. Copy is original and republishes no Amazon listing prose.")
        + f'<section><h2>Method</h2><p>{esc(MARKETING["_meta"]["method"])}</p>'
        + f'<h3>Deliberately excluded</h3><ul>{excluded}</ul></section>'
        + '<section><h2>SEO rules that apply to these pages</h2>'
        + marketing_seo_rules_table() + "</section>"
        + '<section><h2>The pages</h2>' + articles + "</section>"
        + '<section><h2>Publishing checklist</h2>' + marketing_checklist_table() + "</section>"
        + '<p class="small muted">These pages are drafts for the publisher. They are not published to a public storefront, and no affiliate link is live '
        'until the Associate tag is confirmed (F-03).</p>'
    )


def page_automation(current: Page) -> str:
    stage_rows = []
    for s in PIPELINE["stages"]:
        stage_rows.append([
            esc(s["id"]), esc(s["stage"]), esc(s["what_it_does"]), status_pill(s["status"]),
            esc(s["output"]), ext(s["source_url"], s["source_ref"]),
        ])
    track_rows = []
    for t in PIPELINE["tracking"]:
        track_rows.append([
            esc(t["id"]), esc(t["metric"]), esc(t["how_obtained"]),
            esc(t["current_value"]) if t["current_value"] else '<span class="muted">Blank - not connected</span>',
            status_pill(t["status"]), ext(t["source_url"], t["source_ref"]), esc(t["notes"]),
        ])
    opt_rows = []
    for o in PIPELINE["optimisation"]:
        opt_rows.append([esc(o["id"]), esc(o["step"]), esc(o["detail"]), ext(o["source_url"], o["source_ref"])])
    agent_rows = []
    for a in PIPELINE["agent_requirements"]:
        agent_rows.append([esc(a["id"]), esc(a["requirement"]), ext(a["source_url"], a["source_ref"])])
    return (
        hero("Automation & tracking", "The affiliate platform described in the brief, stage by stage: what this repository already does, what is blocked and which "
             "official rule blocks it. Every metric is blank because no Associates account, reporting access or API key is connected. Nothing is simulated.")
        + '<section><h2>Pipeline</h2>'
        + table(["ID", "Stage", "What it does", "Status", "Output", "Source (official)"], stage_rows, "stages")
        + "</section>"
        + '<section><h2>Click, conversion and revenue metrics</h2>'
        + table(["ID", "Metric", "How it is obtained", "Current value", "Status", "Source (official)", "Notes"], track_rows, "tracking")
        + "</section>"
        + '<section><h2>Optimisation loop</h2>'
        + table(["ID", "Step", "What to do", "Source (official)"], opt_rows, "optimisation")
        + "</section>"
        + '<section><h2>Rules for an automated research agent</h2>'
        + '<p class="small muted">These are the Agent Terms in the Associates Program IP License, Section 4. They apply to any software that takes automatic or '
        'semi-automatic action on Program Content, which includes the research agent in the brief.</p>'
        + table(["ID", "Requirement", "Source (official)"], agent_rows, "agents")
        + "</section>"
    )


def page_analysis(current: Page) -> str:
    return (
        hero("Analysis & findings", "Every finding states its basis and confidence. Where a value is unverified, the finding says so instead of estimating it.")
        + table(["ID", "Finding", "Basis", "Confidence", "Source links"], analysis_rows(), "analysis")
    )


def page_verification(current: Page) -> str:
    return (
        hero("Verification log", "Field-by-field check for each product. Each row links to the official source it was checked against. Blank or withheld values are flagged.")
        + '<p><input id="filter" class="filter" type="search" placeholder="Filter rows (for example: P2, Unverified, F-02)" aria-label="Filter table"></p>'
        + table(["Product", "Field", "Value", "Status", "Source link", "Flag"], verification_rows(current), "verification")
        + f'<p class="small muted">Observed {esc(OBSERVED)} (UTC). Every row was re-read against the official source on that date. Re-check before publishing.</p>'
    )


def page_policy(current: Page) -> str:
    return (
        hero("Policy compliance", "Amazon Associates and FTC requirements checked against this site. Each row links to its official source section.")
        + table(["ID", "Requirement", "Source (official)", "Status on this site", "How the site complies"], policy_rows(current), "policy")
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
        hero("Sources", "Every source used, with whether it was read during a verification pass. Unread sources are marked No and nothing is inferred from them.")
        + table(["ID", "Source (link)", "Publisher", "Read?", "Used for", "Notes"], source_rows(), "sources")
        + non_official_note()
    )


def page_analytics(current: Page) -> str:
    """Local-only first-party click log. Records real clicks in the visitor's own browser."""
    rows = [
        ("Clicks on tracked links", "0", "Real user clicks recorded in this browser"),
        ("All local events", "0", "Clicks plus explicitly labelled test events"),
        ("Conversions / orders", "\u2014", "Requires Associates reporting (not connected). See " + "F-19"),
        ("Commission earned", "\u2014", "Requires Associates reporting (not connected). See F-01"),
        ("Last event (UTC)", "\u2014", "Timestamp of the most recent local event"),
    ]
    kpis = "".join(
        f'<div class="kpi"><div class="kpi-value" id="{esc(kpi_id)}">{esc(value)}</div>'
        f'<div class="kpi-label">{esc(label)}</div></div>'
        for kpi_id, value, label in (
            ("m-clicks", rows[0][1], rows[0][2]),
            ("m-events", rows[1][1], rows[1][2]),
            ("m-conv", rows[2][1], rows[2][2]),
            ("m-last", rows[4][1], rows[4][2]),
        )
    )
    return (
        '<header class="hero"><h1>Clicks &amp; conversions</h1>'
        '<p class="lead">A first-party, local-only click tracker. It starts at zero, records only real clicks on tracked links plus one clearly '
        'labelled test event, and never invents a figure. Authoritative click, order and commission numbers come from the official Associates '
        'reporting and are not connected here.</p></header>'
        f'<section class="kpis">{kpis}</section>'
        '<section>'
        '<h2>Click event log</h2>'
        '<p>Events are stored in this browser only (<code>localStorage</code>). This page sends nothing anywhere. Export the log before clearing '
        'browser data.</p>'
        '<p id="log-empty" class="small muted">No events recorded yet. Rows appear below when the tracker records a real click or the labelled '
        'test event.</p>'
        '<div class="table-wrap"><table><thead><tr><th scope="col">Timestamp (UTC)</th><th scope="col">Type</th>'
        '<th scope="col">Target</th><th scope="col">ASIN</th></tr></thead><tbody id="event-rows"></tbody></table></div>'
        '<div class="btnrow"><button class="btn" id="btn-test" type="button">Add labelled test event</button>'
        '<button class="btn" id="btn-export-json" type="button">Export JSON</button>'
        '<button class="btn" id="btn-export-csv" type="button">Export CSV</button>'
        '<button class="btn danger" id="btn-clear" type="button">Clear log</button></div>'
        '<p class="note">The test button writes an event explicitly marked <b>test</b> so the mechanism can be checked end to end. It is never counted '
        'as a product click. Real clicks are recorded automatically when a visitor activates a link carrying the tracking attributes, which the '
        'product links on this site do.</p>'
        '<p class="note">The tracked links are the supplied short links. They currently carry no visible Associates tag, so a click recorded here '
        'cannot yet be attributed to an Associates account or reconciled against Amazon reporting (see ' + flag_chip(current, "F-03") + ').</p>'
        '</section>'
        '<section>'
        '<h2>Connecting real measurement</h2>'
        '<ul class="bullets">'
        f'<li>Join the Amazon Associates Program and receive an Associates ID, then use the tagged Special Link formats (see {href(current, "policy-compliance.html", "Policy compliance")}).</li>'
        f'<li>Confirm the tag on the supplied short links before relying on any earnings (see {href(current, "flagged.html", "F-03")}).</li>'
        f'<li>Authoritative click, order and commission figures come from the official {ext("https://affiliate-program.amazon.com/", "Associates Central reporting")}.</li>'
        f'<li>Product data served from Amazon must come through the Creators API, and reusing or fine-tuning on API content needs express prior written approval (see {href(current, "flagged.html", "F-24")}).</li>'
        f'<li>Price tracking and price alerting are prohibited unless Amazon agrees otherwise, so no price history is collected here (see {href(current, "flagged.html", "F-22")}).</li>'
        '<li>Add a cookie or consent notice appropriate to your audience before enabling measurement on real traffic, consistent with the disclosure '
        'expectations in the official Program Policies and applicable law.</li>'
        '</ul>'
        '</section>'
        f'<p class="muted small">This page displays no prices, ratings or review counts (withheld under {href(current, "flagged.html", "F-02")}). '
        f'Verified product facts live in the {href(current, "verification.html", "verification log")}.</p>'
    )


def requirement_rows(current: Page) -> list[list[str]]:
    rows = []
    for r in REQUIREMENTS:
        srcs = "<br>".join(ext(u, source_label(u)) for u in r["sources"])
        rows.append([
            esc(r["id"]),
            esc(r["area"]),
            esc(r["requirement"]),
            status_pill(r["status"]),
            esc(r["delivered"]) if r["delivered"] else pill("—", "muted"),
            esc(r["blocker"]) if r["blocker"] else pill("—", "muted"),
            srcs,
            " ".join(flag_chip(current, f) for f in r.get("flags") or []),
        ])
    return rows


def page_requirements(current: Page) -> str:
    """Traceability of the project brief: one row per requirement, with its delivery status."""
    counts = {}
    for r in REQUIREMENTS:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    summary = " · ".join(f"{esc(k)}: {v}" for k, v in sorted(counts.items()))
    return (
        '<header class="hero"><h1>Requirements</h1>'
        '<p class="lead">Every requirement in the project brief, one row each, with what this site actually delivers, what blocks it, and the official '
        'source that governs or evidences that status. Nothing is marked Delivered unless it is live on the site.</p>'
        f'<p class="muted small">{summary}</p></header>'
        '<section>'
        '<h2>Requirement register</h2>'
        + table(
            ["ID", "Area", "Requirement", "Status", "Delivered on this site", "Blocker or gap (official rule)", "Official sources", "Flags"],
            requirement_rows(current),
            "requirements",
        )
        + '<p class="note">Statuses are defined in <code>data/requirements.json</code>. A requirement marked <em>Delivered</em> names the page or feature '
          'that delivers it; a requirement marked <em>Not built</em> names the official rule or the missing access, and nothing is simulated in its '
          'place. Unverifiable values are blank on the site and listed on the '
        + href(current, "flagged.html", "Flagged for Review") + ' page.</p>'
        '</section>'
    )


BODIES = {
    "index.html": page_index,
    "executive-summary.html": page_exec,
    "products.html": page_products,
    "categories/dual-basket-air-fryers.html": lambda c: page_category(c, "dual-basket-air-fryers"),
    "categories/single-basket-air-fryers.html": lambda c: page_category(c, "single-basket-air-fryers"),
    "categories/air-fryer-toaster-ovens.html": lambda c: page_category(c, "air-fryer-toaster-ovens"),
    "marketing.html": page_marketing,
    "automation.html": page_automation,
    "analysis.html": page_analysis,
    "requirements.html": page_requirements,
    "verification.html": page_verification,
    "policy-compliance.html": page_policy,
    "analytics.html": page_analytics,
    "flagged.html": page_flagged,
    "sources.html": page_sources,
}


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
<title>{esc(page.title)} | {esc(SITE_TITLE_SUFFIX)}</title>
<meta name="description" content="{esc(SITE_DESCRIPTION)}">
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
        html_text = render(page)
        if path == "analytics.html":
            html_text = html_text.replace(
                "</body>",
                f'<script src="{esc(page.rel("tracker.js"))}"></script>\n</body>',
            )
        out.write_text(html_text, encoding="utf-8")
        written.append(out)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    return written


if __name__ == "__main__":
    for p in build():
        print("wrote", p.relative_to(ROOT))
