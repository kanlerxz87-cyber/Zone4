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


PRODUCTS_DOC = load("products.json")
PRODUCTS = PRODUCTS_DOC["products"]
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
# Decision-support layer: the backlog a reviewer chooses from, the questions that
# must be answered first, and the record of decisions actually taken.
SUGGESTIONS_DOC = load("suggestions.json")
SUGGESTIONS = SUGGESTIONS_DOC["suggestions"]
QUESTIONS_DOC = load("questions.json")
QUESTIONS = QUESTIONS_DOC["questions"]
DECISIONS_DOC = load("decisions.json")
DECISIONS = DECISIONS_DOC["decisions"]
DECISION_LOG = DECISIONS_DOC["log"]
OBSERVED = CONTENT["observed_date"]
# The date the three supplied links and the cited official policy pages were last
# re-read from their official sources. Kept separate from OBSERVED, which is the
# date of the product-page snapshot the records hold.
RECHECKED = CONTENT.get("rechecked_utc", OBSERVED)

SITE_URL = "https://kanlerxz87-cyber.github.io/Zone4/docs/"

#: Human labels for every page. The reader-facing navigation itself is defined
#: further down (NAV and NAV_INDEX), together with the renderer, so this map is
#: the single place a page's short name is written.
NAV_LABEL = {
    "index.html": "Home",
    "executive-summary.html": "Executive summary",
    "products.html": "The products",
    "categories/dual-basket-air-fryers.html": "Dual-basket air fryers",
    "categories/single-basket-air-fryers.html": "Single-basket air fryers",
    "categories/air-fryer-toaster-ovens.html": "Air-fry toaster ovens",
    "articles/index.html": "Guides & reviews",
    "decision-centre.html": "Decision centre",
    "information-gaps.html": "Information gaps",
    "marketing.html": "Marketing content",
    "automation.html": "Automation & tracking",
    "analysis.html": "Analysis & findings",
    "requirements.html": "Requirements",
    "verification.html": "Verification log",
    "policy-compliance.html": "Policy compliance",
    "suggestions.html": "Suggestions",
    "questions.html": "Open questions",
    "decisions.html": "Decision log",
    "analytics.html": "Clicks & conversions",
    "flagged.html": "Flagged for review",
    "sources.html": "Sources",
}
CATEGORY_TITLE = {
    "categories/dual-basket-air-fryers.html": "Dual-basket air fryers",
    "categories/single-basket-air-fryers.html": "Single-basket air fryers",
    "categories/air-fryer-toaster-ovens.html": "Air-fry toaster ovens",
}

# --- Article pages -------------------------------------------------------
# Each marketing article in data/marketing.json is published as its own page,
# so every piece of content is individually addressable and carries the title
# tag and meta description that were written for it. Pages are derived from the
# data rather than hand-listed: adding an article to the data adds a page, and
# a page can never exist for an article that is not in the data.
CATEGORY_BY_PRODUCT = {
    "P1": "dual-basket-air-fryers",
    "P2": "air-fryer-toaster-ovens",
    "P3": "single-basket-air-fryers",
}
PRODUCT_BY_ID = {p["id"]: p for p in PRODUCTS}
ARTICLES_HUB = "articles/index.html"


def article_path(a: dict) -> str:
    """docs-relative path for an article, taken from its own suggested slug."""
    return "articles/" + a["slug"].strip("/") + ".html"


def article_category(a: dict) -> str:
    return CATEGORY_BY_PRODUCT.get(a.get("product_id"), "")


def article_label(a: dict) -> str:
    p = PRODUCT_BY_ID.get(a.get("product_id"))
    return p["name_short"] if p else a["page_type"]


def article_word_count(a: dict) -> int:
    return sum(len(par["text"].split()) for par in a["body"])


def article_read_minutes(a: dict) -> int:
    """Reading time derived from the article's own word count at 220 wpm.

    This is arithmetic on the site's own copy, not a claim about the product,
    so it needs no external source. It is rounded up to keep it stable.
    """
    return max(1, -(-article_word_count(a) // 220))


ARTICLES = MARKETING["articles"]
ARTICLE_PATHS = [(a, article_path(a)) for a in ARTICLES]
ARTICLE_BY_PATH = {path: a for a, path in ARTICLE_PATHS}

for _a, _path in ARTICLE_PATHS:
    NAV_LABEL[_path] = article_label(_a)
NAV_LABEL[ARTICLES_HUB] = "Guides & reviews"


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
    def __init__(self, path: str, title: str, active: str, body: str,
                 description: str | None = None, title_tag: str | None = None,
                 head_extra: str = ""):
        self.path = path
        self.title = title
        self.active = active
        self.body = body
        # Per-page SEO fields. Article pages supply their own title tag and meta
        # description from data/marketing.json; every other page keeps the
        # site-wide defaults so nothing changes for them.
        self.description = description
        self.title_tag = title_tag
        # Optional extra <head> content (JSON-LD). Kept inline so no external
        # host is ever added to the page. Added by session arena/d8564cd0-zone4.
        self.head_extra = head_extra

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
    return "<br>".join(
        ext(c["url"], c["asin"])
        + (f' <span class="small muted">{esc(c["label"])} (as listed)</span>' if c.get("label") else "")
        for c in p["competitors"]
    )


def shop_link(p: dict) -> str:
    """The affiliate link, labelled as a paid link in its own visible text.

    The label carries the plain-language token because the FTC disclosure
    guidance asks for the qualification to be hard to miss and adjacent to the
    link; the disclosure sentence follows it in the same paragraph.
    """
    return ext(p["short_link"], "Check the current listing",
               f' class="shop" data-track="click" data-track-target="{esc(p["short_link"])}" data-track-asin="{esc(p["asin"])}"')


# ---------------------------------------------------------------- tables

def commission_verification_item(p: dict, sched: str) -> tuple[str, str, str, str, str]:
    """The verification-ledger row for the commission rate.

    Falls back to the blank/unverified row when the data carries no sourced
    rate, so this cell can never publish a percentage the ledger has not
    attributed to an official page.
    """
    rate = p.get("commission_rate_pct")
    url = p.get("commission_rate_source")
    if rate is None or not url:
        source = ext(url, "Official category rate table") if url else sched
        return ("Product-level commission rate", "Blank", "Unverified for this ASIN (F-01)", source, "F-01")
    return ("Product-level commission rate", f"{rate:.2f}% ({p.get('commission_category_official', 'category')} band)",
            "Verified from the official rate table", ext(url, "Standard Commission Income Statement"), "F-01")


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
            ("Also-viewed ASINs and listing titles",
             "; ".join(c["asin"] + (": " + c["label"] if c.get("label") else "") for c in p["competitors"]),
             "Verified as shown (title segment as listed)", src, fl["competitors"]),
            ("Price", "Not published", "Withheld (policy)", src, "F-02"),
            ("Star rating / review count", "Not published", "Withheld (policy)", src, "F-02"),
            commission_verification_item(p, sched),
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


def flag_group(status: str) -> str:
    """Sort a flag into the group a reviewer needs it in.

    Resolved and corrected items are kept (they are the audit trail) but they
    must not sit in the same list as the items still waiting on a decision.
    """
    s = status.lower()
    if s.startswith("resolved"):
        return "Resolved"
    if s.startswith("corrected"):
        return "Corrected (kept as the audit record)"
    return "Needs your decision"


FLAG_GROUPS = [
    ("Needs your decision",
     "Open items. Some need a value only you can supply (an account, a tag, a seller's answer); others need a decision. "
     "None of them blocks the site from being live."),
    ("Corrected (kept as the audit record)",
     "Defects that were found and fixed. They stay listed so the correction is visible rather than quietly disappearing."),
    ("Resolved",
     "Items closed by a later verification pass, with the resolving session named in the status."),
]


def flag_table(current: Page, flags: list[dict]) -> str:
    rows = []
    for f in flags:
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
        urls = f.get("source_urls") or [f["source_url"]]
        refs = f.get("source_refs") or [f["source_ref"]] * len(urls)
        source_links = "<br>".join(ext(url, ref) for url, ref in zip(urls, refs))
        rows.append([
            esc(f["id"]),
            esc(f["field"]),
            esc(f["value"]) if f["value"] else '<span class="muted">Blank - withheld or unverified</span>',
            source_links,
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
        citations = []
        for fid in para["fact_ids"]:
            fact = facts_by_id.get(fid)
            if not fact:
                continue
            sources = fact.get("source_urls") or [fact["source_url"]]
            citations.extend(
                f'<a class="cite" href="{esc(url)}" rel="noopener noreferrer">{esc(fid)}</a>'
                for url in sources
            )
        cites = "".join(citations)
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
        f'<p>{cta_button} <span class="note">(paid link)</span> <span class="note"><strong>Disclosure:</strong> {esc(cta["disclosure"])}</span></p></div>'
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
# Rewritten 2026-11-16 by session arena/6554fead-zone4.
#
# Design brief for this pass: the site should read like a kitchen publication
# that happens to be scrupulous, not like a compliance dashboard. That means a
# reader-facing home page (what to buy, in what order, and why), articles that
# open with the decision instead of the metadata, and the research layer kept
# one click away rather than in the reader's face. Nothing about the evidence
# rules changed: every published value still carries its official source, and
# anything unconfirmed is still blank and flagged.
#
# Editorial copy added in this pass is written against facts already recorded in
# data/ and cited in the same paragraph. No new product claim is introduced.

BRAND_NAME = "The Countertop Edit"
BRAND_TAGLINE = "Verified buying notes for countertop air fryers"
EDITORIAL_DATE = RECHECKED
PRODUCT_BY_FORMAT_ARTICLE = {
    "dual-basket-air-fryers": "articles/chefman-6-quart-dual-basket-air-fryer-oven.html",
    "single-basket-air-fryers": "articles/chefman-8-quart-single-basket-air-fryer.html",
    "air-fryer-toaster-ovens": "articles/26qt-french-door-air-fryer-toaster-oven.html",
}
ARTICLE_BY_ID = {a["id"]: a for a in ARTICLES}
BUYING_GUIDE = "articles/air-fryer-buying-guide-2026.html"
COMPARISON = "articles/dual-basket-vs-single-basket-vs-toaster-oven-air-fryer.html"


def hero(title: str, lead: str) -> str:
    return f'<header class="hero"><h1>{esc(title)}</h1><p class="lead">{esc(lead)}</p></header>'


def section_h2(title: str) -> str:
    return f"<h2>{esc(title)}</h2>"


def format_label(product: dict) -> str:
    return CATEGORY_TITLE.get("categories/" + CATEGORY_BY_PRODUCT.get(product["id"], "") + ".html",
                              product.get("subcategory", ""))


def product_article(product: dict) -> dict | None:
    return next((a for a in ARTICLES if a.get("product_id") == product["id"]), None)


def open_flags() -> list[dict]:
    return [f for f in FLAGS if flag_group(f["status"]) == "Needs your decision"]


def open_decisions() -> list[dict]:
    return [d for d in DECISIONS if d["status"].startswith("Open")]


def cited_sources(*ids: str) -> str:
    return " ".join(ext(SOURCES[i]["url"], SOURCES[i]["id"]) for i in ids if i in SOURCES)


# ---------------------------------------------------------------- teasers

def article_card(current: Page, a: dict, show_category: bool = True, lead: bool = False) -> str:
    """A teaser card for one article: category chip, headline, dek and metadata."""
    key = article_category(a)
    cat_label = CATEGORY_TITLE.get("categories/" + key + ".html", "") if key else ""
    chip = f'<span class="chip">{esc(cat_label)}</span>' if (show_category and cat_label) else ""
    cls = "acard acard-lead" if lead else "acard"
    return (
        f'<a class="{cls}" href="{esc(current.rel(article_path(a)))}">'
        f'<div class="acard-top">{chip}<span class="chip chip-quiet">{esc(a["page_type"])}</span></div>'
        f'<div class="acard-title">{esc(a["h1"])}</div>'
        f'<div class="acard-dek">{esc(a["meta_description"])}</div>'
        f'<div class="acard-meta">{article_read_minutes(a)} min read \u00b7 '
        f'{len(a["facts"])} sourced facts \u00b7 observed {esc(OBSERVED)}</div>'
        "</a>"
    )


def product_card(current: Page, p: dict) -> str:
    """One product as a shopper-facing card: format, listed specs, one shop link.

    Everything on the card is a field already recorded in data/products.json with
    its official page; the card adds no claim of its own.
    """
    article = product_article(p)
    why = {
        "P1": "Two independent 3-quart baskets and a Sync Finish option, per the listing title: "
              "shortlist it if a main and a side cook at the same time in your kitchen.",
        "P2": "French doors, a dual-speed fan, rotisserie and an interior light in the largest "
              "listed footprint of the three: the multi-function route.",
        "P3": "One basket, four presets and the smallest listed footprint of the three: the "
              "everyday fryer, and the cheapest to place on a counter.",
    }.get(p["id"], p.get("subcategory", ""))
    specs = (
        f'<div class="pcard-spec"><dt>Capacity as listed</dt><dd>{esc(p["capacity"])}</dd></div>'
        f'<div class="pcard-spec"><dt>Footprint as listed</dt><dd>{esc(p["dimensions"])}</dd></div>'
        f'<div class="pcard-spec"><dt>Colour as listed</dt><dd>{esc(p["color"])}</dd></div>'
        f'<div class="pcard-spec"><dt>ASIN</dt><dd>{esc(p["asin"])}</dd></div>'
    )
    read = ""
    if article:
        read = (f'<a class="btn btn-quiet" href="{esc(current.rel(article_path(article)))}">Read the full review</a>')
    return (
        f'<article class="pcard" id="card-{esc(p["id"])}">'
        f'<div class="pcard-format">{esc(format_label(p))}</div>'
        f'<h2 class="pcard-name"><a href="{esc(current.rel("products.html"))}#{esc(p["id"])}">'
        f'{esc(p["name_short"])}</a></h2>'
        f'<div class="pcard-brand">{esc(p["brand"])} \u00b7 <a href="{esc(p["canonical_url"])}" '
        f'rel="noopener noreferrer">official listing page</a></div>'
        f'<dl class="pcard-specs">{specs}</dl>'
        f'<p class="pcard-why">{esc(why)}</p>'
        f'<div class="pcard-foot"><p class="pcard-cta">{shop_link(p)} '
        f'<span class="note">(paid link) {esc(DISCLOSURE_SENTENCE)}</span></p>{read}</div>'
        f'</article>'
    )


# ---------------------------------------------------------------- landing page

CATEGORY_PRODUCT = {"dual-basket-air-fryers": "P1", "single-basket-air-fryers": "P3",
                    "air-fryer-toaster-ovens": "P2"}


def format_depth(product_id: str) -> str:
    """The listed depth of a product, taken from its own dimensions field.

    The dimensions are stored exactly as the seller writes them ("13.38\"D x
    11.81\"W x 10.63\"H"), so this reads the D value out of that string rather
    than restating it: a single source of truth for the figure, and no chance of
    the hero drifting from the card.
    """
    dims = PRODUCT_BY_ID[product_id]["dimensions"]
    depth = dims.split('"D')[0].strip()
    return depth + " in"


def editorial_promise_section() -> str:
    """The editorial promise, rendered from data/content.json.

    Six lines that state what a reader can rely on. Each one is a claim about how
    this site works rather than about a product, and each is enforced by a check
    documented on the policy page: the per-paragraph citation rule by the fact
    tables, the no-price rule by scripts/verify.py, the no-testing-claim rule by
    the FTC guidance cited there.
    """
    ed = CONTENT.get("editorial") or {}
    promise = ed.get("promise") or []
    if not promise:
        return ""
    items = "".join(f"<li>{esc(x)}</li>" for x in promise)
    counts = ed.get("counts") or {}
    strip = ""
    if counts:
        strip = (
            '<div class="kpis">'
            f'<div class="kpi"><div class="kpi-value">{counts.get("products", "")}</div>'
            '<div class="kpi-label">Products, each with a sourced record</div></div>'
            f'<div class="kpi"><div class="kpi-value">{counts.get("articles", "")}</div>'
            '<div class="kpi-label">Articles, each with its fact table</div></div>'
            f'<div class="kpi"><div class="kpi-value">{counts.get("open_flags", "")}</div>'
            f'<div class="kpi-label">Open flags, of {counts.get("flags", "")} recorded</div></div>'
            f'<div class="kpi"><div class="kpi-value">{counts.get("decisions", "")}</div>'
            '<div class="kpi-label">Decisions waiting on the owner</div></div>'
            '</div>'
        )
    return (
        '<section>' + section_h2("What you can rely on here") +
        '<p class="section-lead">Six commitments, each one enforced by something you can check rather '
        'than asserted on a page.</p>'
        f'<ul class="bullets">{items}</ul>{strip}</section>'
    )


def page_index(current: Page) -> str:
    """The reader-facing front page: the decision, the three products, the guides."""
    n_open_flags = len(open_flags())
    n_open_decisions = len(open_decisions())
    featured = ARTICLE_BY_ID.get("M-BUY")
    if not featured:
        featured = ARTICLES[0]
    reviews = [product_article(p) for p in PRODUCTS]
    cards_html = "".join(product_card(current, p) for p in PRODUCTS)
    guide_card = article_card(current, featured, lead=True)
    other_cards = "".join(
        article_card(current, a) for a in ARTICLES if a["id"] != featured["id"]
    )

    steps = (
        '<div class="steps">'
        '<div class="step"><h3>Pick the format</h3><p>Dual basket, single basket or a French-door '
        'toaster oven. This choice decides everything else, and it is the one the listings cannot '
        'make for you.</p></div>'
        '<div class="step"><h3>Carry the unit</h3><p>The listings disagree with themselves: a title '
        'says 6 quart while the details table says 6 liters. Both are shown as written, never '
        'converted.</p></div>'
        '<div class="step"><h3>Measure the counter</h3><p>All three listed footprints are published '
        'exactly as the seller wrote them, so the tape measure happens before the checkout.</p></div>'
        '<div class="step"><h3>Read the small print</h3><p>Function counts, size variants and brand '
        'fields are on the reviews, with the listing\u2019s own inconsistencies kept rather than '
        'tidied away.</p></div>'
        '</div>'
    )

    return (
        '<div class="mhero">'
        f'<span class="badge">Verified {esc(OBSERVED)} \u00b7 re-checked {esc(RECHECKED)}</span>'
        '<h1>Three air fryers, one honest shortlist.</h1>'
        '<p class="lead">Two baskets, one basket, or French doors? Start with the format question, '
        'then read the specifications exactly as the seller lists them \u2014 including the places '
        'where the listing contradicts itself. Every figure on this site links back to the page it '
        'came from, and nothing that could not be checked is filled in.</p>'
        '<div class="mhero-actions">'
        f'<a class="btn btn-primary" href="{esc(current.rel(BUYING_GUIDE))}">Start with the buying guide</a>'
        f'<a class="btn" href="{esc(current.rel(COMPARISON))}">Compare the three formats</a>'
        f'</div>'
        '<div class="mhero-foot">'
        f'<span>{len(PRODUCTS)} product records, all three sourced</span>'
        f'<span>{len(ARTICLES)} articles, each with its fact table</span>'
        '<span>No prices or star ratings published (F-02)</span>'
        '<span>No hands-on testing claimed</span>'
        '</div>'
        '<div class="formats">'
        + "".join(
            f'<a class="format" href="{esc(current.rel(t))}">'
            f'<span class="format-name">{esc(l)}</span>'
            f'<span class="format-spec">{esc(PRODUCT_BY_ID[CATEGORY_PRODUCT[key]]["capacity"])} listed · '
            f'{esc(format_depth(CATEGORY_PRODUCT[key]))} deep</span>'
            f'<span class="format-arrow" aria-hidden="true">→</span></a>'
            for key, t, l in ((k, "categories/" + k + ".html", CATEGORY_TITLE["categories/" + k + ".html"])
                              for k in ("dual-basket-air-fryers", "single-basket-air-fryers",
                                        "air-fryer-toaster-ovens"))
        )
        + '</div></div>'

        '<section>' + section_h2("The three products, side by side") +
        '<p class="section-lead">Each card carries only listed fields \u2014 capacity, footprint, '
        'colour and ASIN \u2014 and one clearly labelled affiliate link. Prices and ratings are '
        'deliberately absent: the rules that govern this site allow them only through an '
        'Amazon-served route that is not connected yet.</p>'
        f'<div class="pgrid">{cards_html}</div>'
        f'<p class="small muted">Full specification tables, including the also-viewed competitors '
        f'and the flags: {href(current, "products.html", "all product records")} \u00b7 '
        f'{href(current, "verification.html", "field-by-field verification log")}.</p>'
        '</section>'

        '<section>' + section_h2("Four questions that settle it") +
        '<p class="section-lead">The buying guide is built around these, in this order. They are '
        'answerable from the listings without a single published price.</p>'
        + steps + '</section>'

        '<section>' + section_h2("Read next") +
        f'<div class="agrid">{guide_card}{other_cards}</div></section>'

        + decision_queue_section(current)

        + editorial_promise_section()
        + '<section>' + section_h2("How this site earns, and what it will not do") +
        '<p>Every product link on this site is an affiliate link. If you buy through one, this site '
        'may earn a commission at no extra cost to you; the required disclosure sits at the top of '
        'every page. What that does <em>not</em> buy is a claim: nobody here has cooked in these '
        f'appliances, no price or star rating is republished, and no trend or earnings figure is '
        f'invented. The {href(current, "flagged.html", "Flagged for Review")} page lists every gap '
        f'that is still open, and the {href(current, "sources.html", "sources")} page shows which '
        f'official document each rule comes from.</p>'
        '<ul class="bullets">'
        '<li><strong>Prices and star ratings</strong> \u2014 withheld until an approved Amazon API '
        'or an Amazon-served link supplies them (F-02).</li>'
        '<li><strong>Per-product commission rate</strong> \u2014 blank: no public source states '
        'which commission category these ASINs sit in (F-01).</li>'
        '<li><strong>Hands-on testing</strong> \u2014 none claimed, anywhere.</li>'
        '<li><strong>Traffic or earnings forecasts</strong> \u2014 none published; the Associates '
        'Operating Agreement says Amazon makes no representation about either.</li>'
        '</ul>'
        f'<p class="small muted">The editorial rules this site works to are on '
        f'{href(current, "policy-compliance.html", "policy compliance")}; the one-line summary is on '
        f'{href(current, "executive-summary.html", "the executive summary")}.</p></section>'

        '<section>' + section_h2("The research behind the pages") +
        f'<p class="section-lead">This site is also the audit trail for itself: {len(FLAGS)} flags, '
        f'{len(SUGGESTIONS)} costed suggestions, {len(QUESTIONS)} open questions and '
        f'{len(DECISIONS)} decisions, all published so a claim can be traced or challenged.</p>'
        f'<div class="kpis">'
        f'<div class="kpi"><div class="kpi-value">{n_open_flags}</div><div class="kpi-label">Flags still '
        f'awaiting a decision, of {len(FLAGS)} recorded</div></div>'
        f'<div class="kpi"><div class="kpi-value">{n_open_decisions}</div><div class="kpi-label">Open '
        f'decisions, none of them taken on your behalf</div></div>'
        f'<div class="kpi"><div class="kpi-value">{len(SUGGESTIONS)}</div><div class="kpi-label">Costed '
        f'suggestions waiting in the queue</div></div>'
        f'<div class="kpi"><div class="kpi-value">{len(QUESTIONS)}</div><div class="kpi-label">Questions '
        f'that must be answered before a change is made</div></div>'
        '</div>'
        f'<div class="btnrow">'
        f'<a class="btn" href="{esc(current.rel("decision-centre.html"))}">Open the decision centre</a>'
        f'<a class="btn btn-quiet" href="{esc(current.rel("flagged.html"))}">See what is flagged</a>'
        f'<a class="btn btn-quiet" href="{esc(current.rel("verification.html"))}">Read the verification log</a>'
        f'</div></section>'
    )


def decision_queue_section(current: Page) -> str:
    """The three decisions that gate everything else, as cards."""
    top = open_decisions()[:3]
    if not top:
        return ""
    cards = "".join(
        f'<a class="dcard" href="{esc(current.rel("decisions.html"))}#{esc(d["id"])}">'
        f'<div class="dcard-top"><span class="dcard-id">{esc(d["id"])}</span>'
        f'<span class="chip chip-quiet">Gate</span></div>'
        f'<div class="dcard-q">{esc(d["question"])}</div>'
        f'<div class="dcard-rec"><strong>Recommended.</strong> {esc(d["recommendation"])}</div>'
        f'<div class="dcard-go">Open the options &rarr;</div></a>'
        for d in top
    )
    return (
        f'<section><h2>Three things only you can decide</h2>'
        '<p class="section-lead">The site can be finished without them. It cannot earn without them, '
        'and this repository will not pretend otherwise: an untagged link is not an affiliate link, '
        'and an unpublished price is not a missing feature. Each card opens the options.</p>'
        f'<div class="agrid">{cards}</div>'
        + '<p>'
        + href(current, "decision-centre.html", "The decision centre")
        + " &nbsp; "
        + href(current, "suggestions.html", f"{len(SUGGESTIONS)} costed suggestions")
        + " &nbsp; "
        + href(current, "questions.html", f"{len(QUESTIONS)} open questions")
        + "</p></section>"
    )


# ---------------------------------------------------------------- products

def page_products(current: Page) -> str:
    """All three records, one row each, with the shop link and every flag."""
    rows = []
    for p in PRODUCTS:
        article = product_article(p)
        review = href(current, article_path(article), "Review") if article else pill("—", "muted")
        rows.append([
            f'<span id="{esc(p["id"])}"><strong>{esc(p["id"])}</strong></span>',
            ext(p["canonical_url"], p["name_short"]),
            esc(p["asin"]),
            esc(p["brand"]),
            esc(p["subcategory"]),
            esc(p["capacity"]),
            esc(p["dimensions"]),
            esc(p["color"]) + " / " + esc(p["material"]),
            review,
            shop_link(p) + f'<div class="note">(paid link) {esc(DISCLOSURE_SENTENCE)}</div>',
            " ".join(flag_chip(current, f) for f in p["flags"]),
        ])
    return (
        '<header class="hero"><h1>All three products, on one page</h1>'
        '<p class="lead">One row per supplied link, with the listed fields, the official page each '
        'one came from, a clearly labelled affiliate link and the flags that apply. Prices, star '
        'ratings and per-product commission rates are blank on purpose; the reasons sit under the '
        'table.</p></header>'
        '<p><input id="filter" class="filter" type="search" '
        'placeholder="Filter rows (for example: Chefman, B0C\u2026, F-02)" aria-label="Filter table"></p>'
        + table(["ID", "Product (official page)", "ASIN", "Brand (as shown)", "Format",
                 "Capacity (as listed)", "Footprint (as listed)", "Colour / material (as listed)",
                 "Review", "Affiliate link", "Flags"], rows, "products")
        + commission_category_note()
        + '<section><h2>Why some cells are blank</h2>'
        '<ul class="bullets">'
        '<li><strong>Price and star rating</strong>: Participation Requirements 2(b) and 6(t) allow '
        'those figures only through Amazon-served links or approved API data. Nothing is '
        f'approximated in their place ({flag_chip(current, "F-02")}).</li>'
        '<li><strong>Commission rate</strong>: the public Table 1 lists category rates, but no '
        'official source maps these ASINs to a commission category, so the product cells stay empty '
        f'({flag_chip(current, "F-01")}).</li>'
        '<li><strong>Trend and conversion</strong>: no reporting access is connected, so no click, '
        f'order or revenue figure is published ({flag_chip(current, "F-15")}).</li>'
        '<li><strong>Associates tag</strong>: the supplied short links resolve correctly but carry '
        f'no visible tag parameter ({flag_chip(current, "F-03")}).</li>'
        '</ul>'
        f'<p class="small muted">The full field-by-field record, including the specification table '
        f'and the also-viewed competitors, is on the {href(current, "verification.html", "verification log")}.</p>'
        '</section>'
    )


def page_category(current: Page, key: str) -> str:
    cat = CONTENT["categories"][key]
    prods = [p for p in PRODUCTS if p["id"] in cat["product_ids"]]
    headers = ["ID", "Product (official page)", "ASIN", "Brand (as shown)",
               "Capacity (as listed)", "Footprint (as listed)", "Special features (as listed)",
               "Competition: also-viewed ASINs", "Affiliate link", "Flags"]
    rows = []
    for p in prods:
        rows.append([
            esc(p["id"]), ext(p["canonical_url"], p["name_listing"]), esc(p["asin"]), esc(p["brand"]),
            esc(p["capacity"]), esc(p["dimensions"]), esc(p.get("special_feature", "")),
            competitor_links(p),
            shop_link(p) + f'<div class="note">(paid link) {esc(DISCLOSURE_SENTENCE)}</div>',
            " ".join(flag_chip(current, f) for f in p["flags"]),
        ])
    review = PRODUCT_BY_FORMAT_ARTICLE.get(key)
    review_link = (
        f'<p><a class="btn btn-primary" href="{esc(current.rel(review))}">Read the full review</a></p>'
        if review else ""
    )
    return (
        hero(cat["title"], cat["intro"])
        + f'<div class="pgrid">{"".join(product_card(current, p) for p in prods)}</div>'
        + review_link
        + table(headers, rows, "products")
        + f'<section><h2>Category notes</h2><p>All products here sit under the official category '
          f'path <em>{esc(prods[0]["category_path"])}</em>. For the cross-format view see '
          f'{href(current, COMPARISON, "the comparison")} and {href(current, BUYING_GUIDE, "the buying guide")}; '
          f'for how the category figures were checked see '
          f'{href(current, "verification.html", "the verification log")}.</p></section>'
    )


# ---------------------------------------------------------------- articles

def page_article(current: Page, a: dict) -> str:
    """One article, published as a page with its own title tag and meta description.

    The reading experience is the point: headline, standfirst, subheaded copy with
    its citations, one call to action, then the evidence in a collapsed panel.
    """
    facts_by_id = {f["id"]: f for f in a["facts"]}
    body_html = []
    for para in a["body"]:
        sub = f'<h2 class="phead">{esc(para["h"])}</h2>' if para.get("h") else ""
        cites = "".join(
            f'<a class="cite" href="{esc(facts_by_id[fid]["source_url"])}" '
            f'rel="noopener noreferrer">{esc(fid)}</a>'
            for fid in para["fact_ids"] if fid in facts_by_id
        )
        body_html.append(f'{sub}<p>{esc(para["text"])} <span class="cites">{cites}</span></p>')
    outline_html = "".join(
        f'<li><strong>{esc(o["h2"])}</strong> \u2014 {esc(o["purpose"])} '
        f'<span class="muted">(facts: {esc(", ".join(o["facts_used"]))})</span></li>'
        for o in a["outline"]
    )
    notes_html = "".join(f"<li>{esc(n)}</li>" for n in a["compliance_notes"])
    cta = a["cta"]
    cta_button = ext(cta["link_url"], cta["link_label"], ' class="shop btn btn-primary"')
    # The link, the plain-language paid-link label and the Associates disclosure
    # sit in one sentence, in one paragraph, so the qualification travels with the
    # link rather than sitting under it. qa/audit_site.py fails the build otherwise.
    cta_html = (
        f'<div class="cta"><p><strong>{esc(cta["text"])}</strong></p>'
        f'<p>{cta_button} <span class="note">(paid link) {esc(cta["disclosure"])}</span></p></div>'
    )

    key = article_category(a)
    cat_label = CATEGORY_TITLE.get("categories/" + key + ".html", "") if key else ""
    crumb = (
        f'<nav class="crumbs" aria-label="Breadcrumb">{href(current, "index.html", "Home")} \u203a '
        f'{href(current, ARTICLES_HUB, "Articles")}'
        + (f' \u203a {href(current, "categories/" + key + ".html", cat_label)}' if key else "")
        + f" \u203a <span>{esc(a['page_type'])}</span></nav>"
    )
    meta_line = (
        f'<div class="ameta">{esc(a["page_type"])}'
        + (f' \u00b7 <span class="chip">{esc(cat_label)}</span>' if cat_label else "")
        + f' \u00b7 {article_read_minutes(a)} min read \u00b7 {len(a["facts"])} sourced facts \u00b7 '
          f'observed {esc(OBSERVED)}</div>'
    )
    seo_html = (
        '<dl class="seo">'
        f"<dt>Suggested URL slug</dt><dd><code>{esc(a['slug'])}</code></dd>"
        f"<dt>Title tag</dt><dd>{esc(a['title_tag'])}</dd>"
        f"<dt>Meta description</dt><dd>{esc(a['meta_description'])}</dd>"
        f"<dt>Page type</dt><dd>{esc(a['page_type'])}</dd>"
        "</dl>"
    )

    # "What this review covers": a three-line verdict built from fields that are
    # already in the fact table, so the box adds emphasis and no claim.
    highlights: list[tuple[str, str]] = []
    if a.get("product_id") in PRODUCT_BY_ID:
        p = PRODUCT_BY_ID[a["product_id"]]
        highlights = [
            ("Format", f'{format_label(p)} \u2014 {p["subcategory"]}'),
            ("Capacity as listed", p["capacity"]),
            ("Footprint as listed", p["dimensions"]),
            ("Brand as shown", f'{p["brand"]} (official Item details / byline, see the fact table)'),
        ]
    verdict = ""
    if highlights:
        verdict = (
            '<div class="verdict"><h2 class="verdict-h">The short version</h2><ul>'
            + "".join(f"<li><strong>{esc(k)}:</strong> {esc(v)}</li>" for k, v in highlights)
            + "</ul></div>"
        )

    related = [x for x in ARTICLES if x["id"] != a["id"]]
    if key:
        related.sort(key=lambda x: 0 if article_category(x) == key else 1)
    related_html = "".join(article_card(current, x) for x in related[:3])

    return (
        '<article class="post">'
        + crumb
        + meta_line
        + f'<h1>{esc(a["h1"])}</h1>'
        + f'<p class="dek">{esc(a["meta_description"])}</p>'
        + verdict
        + "".join(body_html)
        + cta_html
        + '<details class="evidence"><summary>Evidence: the fact table this article was written '
          f'from ({len(a["facts"])} rows, each with its official source)</summary>'
        + marketing_fact_table(a)
        + '<h3>Search metadata</h3>' + seo_html
        + '<h3>Outline the article was built to</h3><ul class="outline">' + outline_html + '</ul>'
        + '<h3>Compliance notes</h3><ul class="small">' + notes_html + '</ul>'
        + '</details>'
        + '<h2>Keyword targets</h2>'
        + marketing_keyword_table(a)
        + '</article>'
        + '<section><h2>Related reading</h2><div class="agrid">' + related_html + "</div></section>"
    )


def page_articles_index(current: Page) -> str:
    """The articles hub: every published article, grouped by the format it covers."""
    groups: list[tuple[str, list[dict]]] = []
    for key in ("dual-basket-air-fryers", "single-basket-air-fryers", "air-fryer-toaster-ovens"):
        items = [a for a in ARTICLES if article_category(a) == key]
        if items:
            groups.append((CATEGORY_TITLE.get("categories/" + key + ".html", key), items))
    cross = [a for a in ARTICLES if not article_category(a)]
    if cross:
        groups.append(("Comparisons and guides", cross))

    blocks = []
    for title, items in groups:
        cards = "".join(article_card(current, a, show_category=False) for a in items)
        link = ""
        key = next((k for k in CATEGORY_BY_PRODUCT.values()
                    if CATEGORY_TITLE.get("categories/" + k + ".html") == title), "")
        if key:
            link = f'<p class="small">{href(current, "categories/" + key + ".html", "See the format record →")}</p>'
        blocks.append(f'<section><h2>{esc(title)}</h2><div class="agrid">{cards}</div>{link}</section>')
    return (
        hero("Articles", "Five pieces, written here rather than syndicated: three product reviews, "
                         "one format comparison and one buying guide. Each opens with the decision it "
                         "helps you make and closes with the evidence it was built from.")
        + "".join(blocks)
        + '<section><h2>How these are written</h2>'
        + f"<p>{esc(MARKETING['_meta']['method'])}</p>"
        + marketing_seo_rules_table()
        + "</section>"
    )


def marketing_article(current: Page, article: dict) -> str:
    """The same article as one block on the single-page marketing kit."""
    facts_by_id = {f["id"]: f for f in article["facts"]}
    body_html = []
    for para in article["body"]:
        citations = []
        for fid in para["fact_ids"]:
            fact = facts_by_id.get(fid)
            if not fact:
                continue
            sources = fact.get("source_urls") or [fact["source_url"]]
            citations.extend(
                f'<a class="cite" href="{esc(url)}" rel="noopener noreferrer">{esc(fid)}</a>'
                for url in sources
            )
        cites = "".join(citations)
        body_html.append(f'<p>{esc(para["text"])} <span class="cites">{cites}</span></p>')
    outline_html = "".join(
        f'<li><strong>{esc(o["h2"])}</strong> - {esc(o["purpose"])} '
        f'<span class="muted">(facts: {esc(", ".join(o["facts_used"]))})</span></li>'
        for o in article["outline"]
    )
    seo_html = (
        '<dl class="seo">'
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
    cta_html = (
        f'<div class="cta"><p>{esc(cta["text"])}</p>'
        f'<p>{cta_button} <span class="note">(paid link)</span> '
        f'<span class="note"><strong>Disclosure:</strong> {esc(cta["disclosure"])}</span></p></div>'
    )
    return (
        f'<article class="doc" id="{esc(article["id"])}">'
        f'<h3>{esc(article["id"])} - {esc(article["h1"])}</h3>'
        f"{seo_html}"
        f"<h4>Keyword targets</h4>{marketing_keyword_table(article)}"
        f'<h4>Outline</h4><ul class="outline">{outline_html}</ul>'
        f"<h4>Draft copy</h4>{''.join(body_html)}"
        f"<h4>Call to action</h4>{cta_html}"
        f"<h4>Fact basis (every row links to its official source)</h4>{marketing_fact_table(article)}"
        f"<h4>Compliance notes</h4><ul>{notes_html}</ul>"
        "</article>"
    )


def page_marketing(current: Page) -> str:
    excluded = "".join(f"<li>{esc(e)}</li>" for e in MARKETING["_meta"]["excluded"])
    articles = "".join(marketing_article(current, a) for a in MARKETING["articles"])
    return (
        hero("Marketing content kit",
             "The publishing pack for the three products: one article each, a comparison page and a "
             "buying guide, every factual statement a row in a fact table with an official source "
             "link. Copy is original and republishes no listing prose.")
        + f'<p><a class="btn btn-primary" href="{esc(current.rel(ARTICLES_HUB))}">Read them as '
          f'published articles instead</a></p>'
        + f'<section><h2>Method</h2><p>{esc(MARKETING["_meta"]["method"])}</p>'
        + f"<h3>Deliberately excluded</h3><ul>{excluded}</ul></section>"
        + "<section><h2>SEO rules that apply to these pages</h2>"
        + marketing_seo_rules_table() + "</section>"
        + "<section><h2>The pages</h2>" + articles + "</section>"
        + "<section><h2>Publishing checklist</h2>" + marketing_checklist_table() + "</section>"
        + '<p class="small muted">These pages are drafts for the publisher. They are not published '
          'to a public storefront, and no affiliate link is live until the Associate tag is '
          'confirmed (F-03).</p>'
    )


# ---------------------------------------------------------------- analysis & research

def page_analysis(current: Page) -> str:
    findings = CONTENT["analysis"]
    verified = sum(1 for a in findings if a["confidence"].lower().startswith(("verified", "official")))
    return (
        hero("Analysis & findings",
             "What the research actually establishes, what it only partly establishes, and what it "
             "cannot establish at all. Each finding states its basis and confidence, and links the "
             "official page an opinion would have to be checked against.")
        + f'<div class="kpis">'
          f'<div class="kpi"><div class="kpi-value">{len(findings)}</div><div class="kpi-label">Findings recorded</div></div>'
          f'<div class="kpi"><div class="kpi-value">{verified}</div><div class="kpi-label">Whose confidence line begins '
          f'&ldquo;verified&rdquo; or &ldquo;official&rdquo;</div></div>'
          f'<div class="kpi"><div class="kpi-value">0</div><div class="kpi-label">Prices, ratings or earnings '
          f'estimates among them</div></div></div>'
        + table(["ID", "Finding", "Basis", "Confidence", "Source links"], analysis_rows(), "analysis")
    )


def page_verification(current: Page) -> str:
    rows = verification_rows(current)
    total = len(rows)
    unverified = sum(1 for r in rows if "Unverified" in r[3] or "Withheld" in r[3] or "Unresolved" in r[3])
    return (
        hero("Verification log",
             "One row per published field: the value, the official page it was read from, and the "
             "flag when it could not be confirmed. Anything that could not be confirmed is blank on "
             "the site and listed here rather than guessed.")
        + f'<div class="kpis">'
          f'<div class="kpi"><div class="kpi-value">{total}</div><div class="kpi-label">Fields checked across the three '
          f'products</div></div>'
          f'<div class="kpi"><div class="kpi-value">{total - unverified}</div><div class="kpi-label">Confirmed against '
          f'the official page</div></div>'
          f'<div class="kpi"><div class="kpi-value">{unverified}</div><div class="kpi-label">Blank, withheld or '
          f'unresolved \u2014 every one flagged</div></div></div>'
        '<p><input id="filter" class="filter" type="search" '
        'placeholder="Filter rows (for example: P2, Unverified, F-02)" aria-label="Filter table"></p>'
        + table(["Product", "Field", "Value", "Status", "Source link", "Flag"], rows, "verification")
        + f'<p class="small muted">Observed {esc(OBSERVED)} (UTC); the supplied links and cited '
          f'policy pages were re-read {esc(RECHECKED)} (UTC). Re-check before publishing. The '
          f'session-by-session records are in <code>data/verification-session-*.json</code> and are '
          f'listed on the {href(current, "sources.html", "sources")} page.</p>'
    )


def requirement_rows(current: Page) -> list[list[str]]:
    """One row per brief requirement: status, what delivers it, what blocks it, sources."""
    rows = []
    for r in REQUIREMENTS:
        srcs = "<br>".join(ext(u, source_label(u)) for u in r["sources"])
        rows.append([
            esc(r["id"]),
            esc(r["area"]),
            esc(r["requirement"]),
            status_pill(r["status"]),
            esc(r["delivered"]) if r["delivered"] else pill("\u2014", "muted"),
            esc(r["blocker"]) if r["blocker"] else pill("\u2014", "muted"),
            srcs,
            " ".join(flag_chip(current, f) for f in r.get("flags") or []),
        ])
    return rows


def page_requirements(current: Page) -> str:
    counts: dict[str, int] = {}
    for r in REQUIREMENTS:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    delivered = sum(v for k, v in counts.items() if k.startswith("Delivered"))
    summary = " \u00b7 ".join(f"{esc(k)}: {v}" for k, v in sorted(counts.items()))
    return (
        '<header class="hero"><h1>Requirements</h1>'
        '<p class="lead">Every requirement in the project brief, one row each, with what this site '
        'actually delivers, what blocks it, and the official source that governs or evidences the '
        'status. Nothing is marked delivered unless it is live.</p>'
        f'<p class="muted small">{summary}</p></header>'
        f'<div class="kpis">'
        f'<div class="kpi"><div class="kpi-value">{len(REQUIREMENTS)}</div><div class="kpi-label">Requirements in the brief</div></div>'
        f'<div class="kpi"><div class="kpi-value">{delivered}</div><div class="kpi-label">Delivered, wholly or in part, '
        f'on this site</div></div>'
        f'<div class="kpi"><div class="kpi-value">{len(REQUIREMENTS) - delivered}</div><div class="kpi-label">Blocked or '
        f'unverifiable, with the rule or the missing access named</div></div></div>'
        "<section><h2>Requirement register</h2>"
        + table(["ID", "Area", "Requirement", "Status", "Delivered on this site",
                 "Blocker or gap (official rule)", "Official sources", "Flags"],
                requirement_rows(current), "requirements")
        + '<p class="note">Statuses are defined in <code>data/requirements.json</code>. A requirement '
          'marked <em>Delivered</em> names the page or feature that delivers it; one marked '
          '<em>Not built</em> names the official rule or the missing access, and nothing is simulated '
          'in its place. Unverifiable values are blank on the site and listed on the '
        + href(current, "flagged.html", "Flagged for Review") + " page.</p></section>"
    )


def page_automation(current: Page) -> str:
    stage_rows = [[
        esc(s["id"]), esc(s["stage"]), esc(s["what_it_does"]), status_pill(s["status"]),
        esc(s["output"]), ext(s["source_url"], s["source_ref"]),
    ] for s in PIPELINE["stages"]]
    track_rows = [[
        esc(t["id"]), esc(t["metric"]), esc(t["how_obtained"]),
        esc(t["current_value"]) if t["current_value"] else '<span class="muted">Blank - not connected</span>',
        status_pill(t["status"]), ext(t["source_url"], t["source_ref"]), esc(t["notes"]),
    ] for t in PIPELINE["tracking"]]
    opt_rows = [[esc(o["id"]), esc(o["step"]), esc(o["detail"]), ext(o["source_url"], o["source_ref"])]
                for o in PIPELINE["optimisation"]]
    agent_rows = [[esc(a["id"]), esc(a["requirement"]), ext(a["source_url"], a["source_ref"])]
                  for a in PIPELINE["agent_requirements"]]
    return (
        hero("Automation & tracking",
             "The affiliate platform the brief describes, stage by stage: what this repository "
             "already does, what is blocked and which official rule blocks it. Every metric is blank "
             "because no Associates account, reporting access or API key is connected. Nothing is "
             "simulated.")
        + f'<p class="note">{len(PIPELINE["stages"])} pipeline stages \u00b7 '
          f'{len(PIPELINE["tracking"])} tracking metrics, all blank \u00b7 '
          f'{len(PIPELINE["optimisation"])} optimisation steps \u00b7 '
          f'{len(PIPELINE["agent_requirements"])} Agent Terms requirements.</p>'
        + "<section><h2>Pipeline</h2>"
        + table(["ID", "Stage", "What it does", "Status", "Output", "Source (official)"], stage_rows, "stages")
        + "</section><section><h2>Click, conversion and revenue metrics</h2>"
        + table(["ID", "Metric", "How it is obtained", "Current value", "Status", "Source (official)", "Notes"],
                track_rows, "tracking")
        + "</section><section><h2>Optimisation loop</h2>"
        + table(["ID", "Step", "What to do", "Source (official)"], opt_rows, "optimisation")
        + "</section><section><h2>Rules for an automated research agent</h2>"
        + '<p class="small muted">These are the Agent Terms in the Associates Program IP License, '
          "Section 4. They apply to any software that takes automatic or semi-automatic action on "
          "Program Content, which includes the research agent in the brief.</p>"
        + table(["ID", "Requirement", "Source (official)"], agent_rows, "agents")
        + "</section>"
        + f'<p class="small muted">The local first-party click log is on the '
          f'{href(current, "analytics.html", "Analytics")} page. It starts at zero and publishes no '
          f'attributed figure.</p>'
    )


# ---------------------------------------------------------------- governance

def page_policy(current: Page) -> str:
    ok = sum(1 for r in RULES if r["status"].lower().startswith(("implemented", "verified", "compliant", "informational")))
    return (
        hero("Policy compliance",
             "Every Amazon Associates and FTC requirement this site checked itself against, the "
             "official section it comes from, and how the site complies. Where compliance depends on "
             "something outside this repository, the row says so.")
        + f'<div class="kpis">'
          f'<div class="kpi"><div class="kpi-value">{len(RULES)}</div><div class="kpi-label">Rules checked</div></div>'
          f'<div class="kpi"><div class="kpi-value">{ok}</div><div class="kpi-label">Implemented or informational as '
          f'built</div></div>'
          f'<div class="kpi"><div class="kpi-value">{len(RULES) - ok}</div><div class="kpi-label">Dependent on the owner, '
          f'an approval or an account connection</div></div></div>'
        + table(["ID", "Requirement", "Source (official)", "Status on this site", "How the site complies"],
                policy_rows(current), "policy")
        + '<p class="note">The two sentences that must appear on every page are the Associates '
          'disclosure (Operating Agreement, Section 5) and the Amazon content notice (IP License, '
          'Section 2(k)); both are rendered by the page template and both are checked by the build.</p>'
    )


def page_flagged(current: Page) -> str:
    grouped: dict[str, list[dict]] = {name: [] for name, _blurb in FLAG_GROUPS}
    for f in FLAGS:
        grouped[flag_group(f["status"])].append(f)
    counts = "".join(
        f'<div class="kpi"><div class="kpi-value">{len(grouped[name])}</div>'
        f'<div class="kpi-label">{esc(name)}</div></div>'
        for name, _blurb in FLAG_GROUPS
    )
    sections = []
    for name, blurb in FLAG_GROUPS:
        items = grouped[name]
        if not items:
            continue
        sections.append(
            f'<section><h2>{esc(name)} <span class="muted">({len(items)})</span></h2>'
            f'<p class="section-lead">{esc(blurb)}</p>'
            + flag_table(current, items)
            + "</section>"
        )
    return (
        '<header class="hero flagged-hero"><h1>Flagged for Review</h1>'
        '<p class="lead">Every irregularity and unverified item found while building this site, '
        'grouped by what it needs from you. Each one links to its source and the action column says '
        'what is needed. None of these blocks the site from being live, and none of them has been '
        'quietly hidden.</p></header>'
        f'<section class="kpis">{counts}</section>'
        + "".join(sections)
        + f'<p class="small muted">Every flag is also a row in <code>data/flags.json</code>. Where a '
          f'flag points at a change worth making, the {href(current, "suggestions.html", "Suggestions")} '
          f'page costs it and the {href(current, "decisions.html", "Decision log")} page records the '
          f'choice.</p>'
        + '<section><h2>Flag index</h2>'
        + '<p class="section-lead">Every flag recorded, by id and severity, so a chip anywhere on the '
          'site resolves to a row above. Each row repeats the official source the flag was checked '
          'against.</p>'
        + table(["Flag", "Severity", "What it is about", "Status", "Source link"],
                [[f'<a href="#{esc(f["id"])}">{esc(f["id"])}</a>',
                  pill(f["severity"], {"High": "bad", "Medium": "warn"}.get(f["severity"], "muted")),
                  esc(f["title"]), status_pill(f["status"]),
                  "<br>".join(ext(u, source_label(u)) for u in f["sources"])] for f in FLAGS],
                "compact")
        + '</section>'
    )


def page_sources(current: Page) -> str:
    return (
        hero("Sources",
             "Every source used, whether it was actually read during a verification pass, and what "
             "it was used for. Unread sources are marked and nothing is inferred from them.")
        + table(["ID", "Source (link)", "Publisher", "Read?", "Used for", "Notes"], source_rows(), "sources")
        + non_official_note()
    )


def page_exec(current: Page) -> str:
    es = CONTENT["executive_summary"]
    bullets = "".join(f"<li>{esc(b)}</li>" for b in es["bullets"])
    decisions = "".join(f"<li>{esc(d)}</li>" for d in es["decisions_needed"])
    not_built = "".join(f"<li>{esc(d)}</li>" for d in CONTENT["not_built"])
    return (
        hero("Executive summary", es["headline"])
        + f'<div class="kpis">'
          f'<div class="kpi"><div class="kpi-value">{len(PRODUCTS)}</div><div class="kpi-label">Products verified from the '
          f'supplied links</div></div>'
          f'<div class="kpi"><div class="kpi-value">{len(ARTICLES)}</div><div class="kpi-label">Articles written and '
          f'published here</div></div>'
          f'<div class="kpi"><div class="kpi-value">{len(open_decisions())}</div><div class="kpi-label">Decisions waiting on '
          f'the owner; none taken on their behalf</div></div>'
          f'<div class="kpi"><div class="kpi-value">{len(open_flags())}</div><div class="kpi-label">Open flags, all published '
          f'rather than buried</div></div></div>'
        + f'<section><h2>What the verification found</h2><ul class="bullets">{bullets}</ul></section>'
        + f'<section><h2>Decisions needed from you</h2><ol>{decisions}</ol>'
        + f'<p class="small muted">Each of these is written up on the '
          f'{href(current, "decisions.html", "Decision log")} with its options, cost and '
          f'reversibility, and each one unlocks a costed entry on the '
          f'{href(current, "suggestions.html", "Suggestions")} page. The unknowns behind them are on '
          f'{href(current, "questions.html", "Open questions")}.</p></section>'
        + f'<section><h2>Not built, and why</h2><ul class="bullets">{not_built}</ul></section>'
        + "<section><h2>Detail</h2><p>See "
        + href(current, "analysis.html", "Analysis & findings") + ", "
        + href(current, "marketing.html", "Marketing content") + ", "
        + href(current, "automation.html", "Automation & tracking") + ", "
        + href(current, "flagged.html", "Flagged for review") + " and "
        + href(current, "sources.html", "Sources") + ".</p></section>"
    )


# ---------------------------------------------------------------- decision support

def _decision_status_pill(status: str) -> str:
    s = status.lower()
    if s.startswith("recorded"):
        return pill(status, "ok")
    if "blocked" in s:
        return pill(status, "bad")
    if s.startswith("needs"):
        return pill(status, "warn")
    if s.startswith("recommended"):
        return pill(status, "ok")
    return pill(status, "warn")


def _priority_chip(priority: str) -> str:
    key = priority.split(" ")[0]
    return f'<span class="prio prio-{esc(key.lower())}">{esc(key)}</span>'


def _link_flags(current: Page, ids: list[str]) -> str:
    return " ".join(flag_chip(current, f) for f in ids) if ids else ""


def suggestion_summary_rows(current: Page) -> list[list[str]]:
    rows = []
    for s in SUGGESTIONS:
        src = s["sources"][0]
        rows.append([
            f'<span id="{esc(s["id"])}"><strong>{esc(s["id"])}</strong></span>',
            _priority_chip(s["priority"]),
            esc(s["title"]),
            _decision_status_pill(s["status"]),
            href(current, "decisions.html", s["decision"]) if s.get("decision") else "&mdash;",
            ext(src["url"], src["ref"]),
            _link_flags(current, s.get("flags") or []),
        ])
    return rows


def suggestion_card(current: Page, s: dict, number: int) -> str:
    srcs = "".join(f'<li>{ext(x["url"], x["ref"])}</li>' for x in s["sources"])
    return (
        f'<article class="scard" id="detail-{esc(s["id"])}">'
        f'<div class="scard-head"><div><span class="scard-id">{esc(s["id"])}</span>'
        f'{_priority_chip(s["priority"])}</div>'
        f'{_decision_status_pill(s["status"])}</div>'
        f'<h3>{esc(s["title"])}</h3>'
        f'<p class="scard-problem">{esc(s["problem"])}</p>'
        f'<p><strong>What to change.</strong> {esc(s["proposal"])}</p>'
        f'<p><strong>Why it is worth doing.</strong> {esc(s["why"])}</p>'
        f'<dl class="sgrid">'
        f'<dt>Cost</dt><dd>{esc(s["effort"])}</dd>'
        f'<dt>Risk</dt><dd>{esc(s["risk"])}</dd>'
        f'<dt>How you would know it worked</dt><dd>{esc(s["check"])}</dd>'
        f'</dl>'
        f'<p class="scard-foot"><span>Decision: '
        f'{href(current, "decisions.html", s["decision"]) if s.get("decision") else "&mdash;"}</span>'
        f'<span>Flags: {_link_flags(current, s.get("flags") or []) or "&mdash;"}</span></p>'
        f'<ul class="scard-src">{srcs}</ul>'
        f'</article>'
    )


def page_suggestions(current: Page) -> str:
    open_count = sum(1 for s in SUGGESTIONS if s["status"].startswith("Awaiting"))
    first = sum(1 for s in SUGGESTIONS if s["priority"].startswith("P1"))
    cards = [
        ("What this page is",
         "A backlog you approve before anything is built. Each entry states the problem, the proposed "
         "change, what it costs, what it risks and the check that would prove it worked. Nothing here "
         "has been implemented."),
        (f"{first} decisions come first",
         "The P1 entries change what the other suggestions are even possible: the link tag, the API "
         "route, the editorial note and the per-page metadata. Working up from P3 would waste the effort."),
        (f"{open_count} of {len(SUGGESTIONS)} await your answer",
         "The rest are corrections with one right answer, listed so the change is visible rather than "
         "silent. They are recorded as recommended, not as decided."),
    ]
    card_html = "".join(
        f'<div class="kpi"><div class="kpi-value kpi-text">{esc(title)}</div>'
        f'<div class="kpi-label">{esc(body)}</div></div>' for title, body in cards
    )
    groups = [
        ("P1 - Decide first", "Decisions that gate everything else."),
        ("P2 - Adds real value", "The site works without these; adding them is what makes it worth reading."),
        ("P3 - Housekeeping", "Accuracy and consistency of the records."),
    ]
    blocks = []
    number = 0
    for key, blurb in groups:
        items = [s for s in SUGGESTIONS if s["priority"] == key]
        if not items:
            continue
        inner = []
        for s in items:
            number += 1
            inner.append(suggestion_card(current, s, number))
        blocks.append(
            f'<section><h2>{esc(key)}</h2>'
            f'<p class="section-lead">{esc(blurb)} {len(items)} suggestion{"s" if len(items) != 1 else ""}.</p>'
            f'<div class="scards">{"".join(inner)}</div></section>'
        )
    return (
        '<header class="hero"><h1>Suggestions</h1>'
        '<p class="lead">Every change worth making to this site, costed and risk-assessed, waiting on '
        'a decision rather than already applied. Pick a path here before anything is built.</p></header>'
        f'<section class="kpis kpis-stack">{card_html}</section>'
        "<section><h2>At a glance</h2>"
        '<p class="section-lead">One line per suggestion. The full case for each is in the section below it.</p>'
        + '<p><input id="filter" class="filter" type="search" '
          'placeholder="Filter suggestions (for example: P1, tag, commission)" aria-label="Filter suggestions"></p>'
        + table(["ID", "Priority", "Suggestion", "Status", "Decision", "Primary source (official)", "Flags"],
                suggestion_summary_rows(current), "suggestions")
        + '<p class="note">Every row links to the official source that constrains it. Where a '
          'suggestion has no external rule behind it, the source column names the repository file the '
          'problem was observed in.</p></section>'
        + "".join(blocks)
        + f'<p class="small muted">Choosing a path happens on the '
          f'{href(current, "decisions.html", "Decision log")} page. The unknowns that gate these '
          f'entries are on {href(current, "questions.html", "Open questions")}. Defects already found '
          f'in the published site are on {href(current, "flagged.html", "Flagged for review")}.</p>'
        + design_prompt_block(current)
    )


def design_prompt_block(current: Page) -> str:
    """A paste-ready design brief for whoever runs the next site-design pass."""
    return (
        "<section><h2>A prompt-ready design brief</h2>"
        '<p class="section-lead">For whoever runs the next design pass: a brief that can be pasted '
        "into a design prompt as-is. It encodes the constraints above rather than replacing them; "
        "edit it freely before use.</p>"
        '<div class="promptblock">'
        "<pre>Redesign the Zone4 affiliate research site as a polished, trustworthy buying-advice "
        "site for countertop air fryers, without changing its verification rules.\n\n"
        "Audience: shoppers choosing between a dual-basket air fryer, a single-basket air fryer and "
        "a French-door air fryer toaster oven, who want honest, sourced specifications before they "
        "click through to a store.\n\n"
        "Visual direction: warm kitchen palette (terracotta accent and verification green on warm "
        "paper), serif display type with a system sans for data, card-based layout, generous "
        "whitespace, prominent verification badge. No external fonts or frameworks; one stylesheet; "
        "system font stack.\n\n"
        "Structure: decision-first landing page (who this is for, what to do next, one primary "
        "action); buying guide as the top-of-funnel page linking to a comparison and three product "
        "reviews; each review with scannable subheadings, a short-version box built only from cited "
        "facts, and one clearly labelled call to action after the substance, with the affiliate "
        "disclosure adjacent.\n\n"
        "Hard constraints: every table row keeps a link to its official source; no prices, no star "
        "ratings, no review counts; no Amazon marks in page titles or keywords; the disclosure stays "
        "on every page; no product images unless they come from an approved Amazon-served route; the "
        "site never claims testing, ranking or trends it cannot evidence.\n\n"
        "Trust layer: keep the Flagged for Review, Open questions, Decision log and Verification "
        "pages one click from the homepage; a reader should be able to trace any published number to "
        "its official source in one click.</pre>"
        '<p class="note">Proposal prepared by session arena/d8564cd0-zone4 (2026-11-15), copy updated '
        "in the 2026-11-16 editorial pass. First steps already shipped in the current build with no "
        "decision needed: the warm-identity stylesheet, subheaded article copy (facts unchanged), "
        "Article/WebSite JSON-LD that states only what each page visibly shows, and a generated "
        "<code>docs/sitemap.xml</code>. Everything else waits on a decision on the "
        + href(current, "decisions.html", "Decision log") + " page; the compliance constraints it "
        "encodes live on the " + href(current, "policy-compliance.html", "policy page") +
        " and in the " + href(current, "flagged.html", "flag register") + ".</p>"
        "</div></section>"
    )


def question_rows(current: Page) -> list[list[str]]:
    rows = []
    for q in QUESTIONS:
        rows.append([
            f'<span id="{esc(q["id"])}"><strong>{esc(q["id"])}</strong></span>',
            esc(q["area"]),
            esc(q["question"]),
            esc(q["why_it_matters"]),
            pill(q["kind"], {"Known": "ok", "Owner decision": "warn"}.get(
                q["kind"], "bad" if q["kind"].startswith("Unknown") else "muted")),
            f'<span class="muted">{esc(q["known"])}</span>',
            esc(q["how_to_discover"]),
            esc(q["answerable_by"]),
            "<br>".join(ext(x["url"], x["ref"]) for x in q["sources"]),
        ])
    return rows


def page_questions(current: Page) -> str:
    kinds = {
        k: sum(1 for q in QUESTIONS if q["kind"] == k)
        for k in QUESTIONS_DOC["_meta"]["kinds"]
        if any(q["kind"] == k for q in QUESTIONS)
    }
    summary = " &middot; ".join(f"<strong>{esc(k)}</strong>: {v}" for k, v in kinds.items())
    return (
        '<header class="hero"><h1>Open questions</h1>'
        '<p class="lead">What has to be answered before any suggestion can reasonably be acted on, '
        'separated into what is already known, what is missing, and who can supply it. Most of these '
        'are not research problems: they need an account, a seller or a lawyer, and no further '
        'reading will close them.</p>'
        f'<p class="muted small">{len(QUESTIONS)} questions &middot; {summary}</p></header>'
        "<section><h2>The register</h2>"
        '<p class="section-lead">The &ldquo;known&rdquo; column states what the repository can already '
        'support, so a reviewer does not have to re-derive it. The &ldquo;how to discover&rdquo; '
        "column is the shortest route to an answer, not a guess at one.</p>"
        + table(["ID", "Area", "Question", "Why it blocks a decision", "Kind", "What is already known",
                 "How the missing piece is discovered", "Answerable by", "Sources (official)"],
                question_rows(current), "questions")
        + '<p class="note">A question closes only on a named source, a named party&rsquo;s answer, or '
          "an owner decision recorded in the Decision log. It is never closed by inference.</p>"
        "</section>"
        "<section><h2>Why this page exists</h2>"
        "<p>Three of these gaps decide whether this project can earn at all: the Associates tag "
        "(Q-01), API access for prices and ratings (Q-02), and the per-ASIN commission category "
        "(Q-03). Three more decide whether it can honestly describe itself: who reviews the copy "
        "(Q-05), whether anything was tested (Q-06), and whether automated collection needs a legal "
        "opinion (Q-07). The rest are presentation and operations choices with named owners.</p>"
        f'<p class="small muted">Related: {href(current, "suggestions.html", "Suggestions")} for what '
        f'each answer would unlock, {href(current, "decisions.html", "Decision log")} for the choices '
        f'already recorded (none, as of {esc(OBSERVED)}).</p>'
        "</section>"
    )


def page_decisions(current: Page) -> str:
    open_items = [d for d in DECISIONS if d["status"].startswith("Open")]
    cards = [
        (str(len(open_items)), "Decisions waiting on you"),
        (str(len(DECISIONS) - len(open_items)), "Decisions recorded"),
        (str(len(SUGGESTIONS)), "Suggestions these decisions unlock"),
    ]
    kpi_html = "".join(
        f'<div class="kpi"><div class="kpi-value">{esc(v)}</div><div class="kpi-label">{esc(l)}</div></div>'
        for v, l in cards
    )
    blocks = []
    for d in DECISIONS:
        opts = []
        for o in d["options"]:
            opts.append(
                f'<div class="opt"><div class="opt-key">{esc(o["key"])}</div><div>'
                f'<div class="opt-label">{esc(o["label"])}</div>'
                f'<div class="opt-body">{esc(o["commits_to"])}</div>'
                f'<div class="opt-meta"><span>Effort: {esc(o["effort"])}</span>'
                f'<span>Reversible: {esc(o["reversible"])}</span></div></div></div>'
            )
        links = " ".join(
            f'<a class="flag-chip" href="{esc(current.rel("suggestions.html"))}#{esc(sid)}">{esc(sid)}</a>'
            for sid in d["linked_suggestions"]
        )
        q = d.get("linked_question")
        qlink = ""
        if q:
            qlink = " ".join(
                f'<a class="flag-chip" href="{esc(current.rel("questions.html"))}#{esc(x.strip())}">{esc(x.strip())}</a>'
                for x in q.split(",")
            )
        blocks.append(
            f'<section class="decision" id="{esc(d["id"])}">'
            f'<div class="decision-head"><h2>{esc(d["id"])} &middot; {esc(d["question"])}</h2>'
            f'{_decision_status_pill(d["status"])}</div>'
            f'<div class="optrow">{"".join(opts)}</div>'
            f'<p class="rec"><strong>Recommendation.</strong> {esc(d["recommendation"])}</p>'
            f'<p class="small">Unlocks: {links}'
            + (f" &middot; Gated by: {qlink}" if qlink else "")
            + f' &middot; Source: {ext(d["sources"][0]["url"], d["sources"][0]["ref"])}'
            + (f' {ext(d["sources"][1]["url"], d["sources"][1]["ref"])}' if len(d["sources"]) > 1 else "")
            + "</p></section>"
        )
    log_rows = []
    register = "https://github.com/kanlerxz87-cyber/Zone4/blob/main/data/decisions.json"
    for n, entry in enumerate(DECISION_LOG, start=1):
        log_rows.append([
            esc(entry["date_utc"]), esc(entry["decision"]), esc(entry["choice"]),
            esc(entry["recorded_by"]), esc(entry["evidence"]),
            ext(register, f"data/decisions.json, log entry {n}"),
        ])
    return (
        '<header class="hero"><h1>Decision log</h1>'
        '<p class="lead">The queue you work through before any suggestion is built, and the record of '
        'what has actually been decided. Nothing in this repository acts on an option by itself: the '
        'site stays exactly as it is until a choice is recorded here.</p></header>'
        f'<section class="kpis">{kpi_html}</section>'
        '<p class="small muted">Pick an option and the site owner records it in the log at the bottom '
        "of this page, with the date. The recommendation is an argument, not a decision, and it is "
        "labelled as one.</p>"
        + "".join(blocks)
        + "<section><h2>Recorded decisions</h2>"
        + table(["Date (UTC)", "Decision", "Choice", "Recorded by", "Evidence", "Where it is recorded"],
                log_rows, "decision-log")
        + '<p class="note">Empty is a valid and honest state. As of this build no owner decision has '
          "been recorded, so every row above is still open and no suggestion has been implemented.</p></section>"
    )


# ---------------------------------------------------------------- decision centre

def page_decision_centre(current: Page) -> str:
    """One hub page: what to read, in what order, and where each answer gets recorded.

    The brief asked for a place where suggestions can be reviewed and a path chosen
    before anything is implemented, plus a clear list of what must be answered
    first. Those pieces existed on three separate pages; this page is the index
    that tells a reviewer which one to open, in which order.
    """
    n_open_d = len(open_decisions())
    hub = (
        f'<div class="hub-grid">'
        f'<a class="hub-card" href="{esc(current.rel("suggestions.html"))}">'
        f'<div class="hub-count">{len(SUGGESTIONS)}</div>'
        f'<div class="hub-title">Suggestions</div>'
        f'<div class="hub-body">Every change worth making, costed and risk-assessed. Read this first: '
        f'it is the menu.</div><div class="hub-go">Open the register &rarr;</div></a>'
        f'<a class="hub-card" href="{esc(current.rel("questions.html"))}">'
        f'<div class="hub-count">{len(QUESTIONS)}</div>'
        f'<div class="hub-title">Open questions</div>'
        f'<div class="hub-body">What is known, what is missing, how the gap is closed and who can close '
        f'it. Read this second: some menu items cannot be ordered yet.</div>'
        f'<div class="hub-go">Open the questions &rarr;</div></a>'
        f'<a class="hub-card" href="{esc(current.rel("decisions.html"))}">'
        f'<div class="hub-count">{n_open_d}</div>'
        f'<div class="hub-title">Decision log</div>'
        f'<div class="hub-body">The choice itself, with its options, cost and reversibility, plus the '
        f'record of decisions taken. Nothing is acted on until it appears here.</div>'
        f'<div class="hub-go">Open the queue &rarr;</div></a>'
        f'<a class="hub-card" href="{esc(current.rel("flagged.html"))}">'
        f'<div class="hub-count">{len(open_flags())}</div>'
        f'<div class="hub-title">Flagged for review</div>'
        f'<div class="hub-body">Defects, gaps and unverified items found while building the site, each '
        f'with its source and the action needed.</div><div class="hub-go">Open the flag register &rarr;</div></a>'
        f'</div>'
    )
    path = (
        '<div class="path">'
        '<div class="path-item"><div class="path-num"></div><div>'
        '<h3>Read the suggestions, P1 first</h3>'
        '<p>Each carries the problem, the proposal, the cost, the risk and the check that would prove '
        'it worked. P3 items are housekeeping and can wait.</p></div></div>'
        '<div class="path-item"><div class="path-num"></div><div>'
        '<h3>Answer the questions each one depends on</h3>'
        '<p>A suggestion that needs a Partner Tag cannot be built before the tag exists. The questions '
        'page names the owner of each answer, so nothing sits in the wrong queue.</p></div></div>'
        '<div class="path-item"><div class="path-num"></div><div>'
        '<h3>Record the choice in the decision log</h3>'
        '<p>Options, cost and reversibility are already written out. Recording a choice is a one-line '
        'entry, and the site keeps behaving exactly as it does now until it is recorded.</p></div></div>'
        '<div class="path-item"><div class="path-num"></div><div>'
        '<h3>Only then does anything change</h3>'
        '<p>Changes are made through a pull request that must pass the build, the verifier and the QA '
        'audit: links, per-row sourcing, disclosure, no prices or ratings, no Amazon marks in titles. '
        'A broken build cannot be published.</p></div></div>'
        "</div>"
    )
    first = open_decisions()[:3]
    gate_rows = [[
        href(current, "decisions.html", d["id"]) + f' &middot; {esc(d["question"])}',
        esc(d["recommendation"]),
        " ".join(href(current, "suggestions.html", sid) for sid in d["linked_suggestions"]) or "&mdash;",
        ext(d["sources"][0]["url"], d["sources"][0]["ref"]),
    ] for d in first]
    return (
        hero("Decision centre",
             "One place to review what could change, see what is still unknown, and choose a path "
             "before anything is implemented. Nothing on this site is actioned by a suggestion: a "
             "change happens only after a decision is recorded and a checked build replaces the page.")
        + hub
        + '<section><h2>The order to work in</h2><p class="section-lead">Four steps, in this order. '
          'Skipping to step four is what produces sites that look finished and cannot earn.</p>'
        + path + "</section>"
        + '<section><h2>The three that gate the rest</h2>'
        + '<p class="section-lead">Each of these blocks a group of suggestions, and each needs an '
          'answer only the owner or Amazon can give.</p>'
        + table(["Decision", "Recommendation (an argument, not a decision)", "Unlocks", "Official source"],
                gate_rows, "compact")
        + "</section>"
        + f'<section><h2>What this site does with an answer</h2><p>A recorded decision becomes a '
          f'suggestion marked for implementation, then a pull request, then a build that has to pass '
          f'the same gates as every page here: every table row sourced to an official page, the '
          f'Associates disclosure on every page, no price or star rating, no Amazon mark in a title '
          f'or a target keyword, and no unverified value published. The gates are listed on '
          f'{href(current, "policy-compliance.html", "policy compliance")} and enforced by '
          f'<code>scripts/verify.py</code> and <code>qa/audit_site.py</code>.</p>'
        + f'<p class="small muted">The full audit trail of this project, including the sessions that '
          f'built it, is in <code>COORDINATION.md</code> in the repository. Every flag published on '
          f'this site names the source it was checked against.</p></section>'
    )


def page_analytics(current: Page) -> str:
    """Local-only first-party click log. Records real clicks in the visitor's own browser."""
    kpis = "".join(
        f'<div class="kpi"><div class="kpi-value" id="{esc(kpi_id)}">{esc(value)}</div>'
        f'<div class="kpi-label">{esc(label)}</div></div>'
        for kpi_id, value, label in (
            ("m-clicks", "0", "Real user clicks recorded in this browser"),
            ("m-events", "0", "Clicks plus explicitly labelled test events"),
            ("m-conv", "\u2014", "Conversions / orders \u2014 needs Associates reporting (not connected, F-19)"),
            ("m-last", "\u2014", "Timestamp of the most recent local event (UTC)"),
        )
    )
    return (
        '<header class="hero"><h1>Clicks &amp; conversions</h1>'
        '<p class="lead">A first-party, local-only click tracker. It starts at zero, records only '
        'real clicks on tracked links plus one clearly labelled test event, and never invents a '
        'figure. Authoritative click, order and commission numbers come from the official Associates '
        'reporting and are not connected here.</p></header>'
        f'<section class="kpis">{kpis}</section>'
        "<section><h2>Click event log</h2>"
        "<p>Events are stored in this browser only (<code>localStorage</code>). This page sends "
        "nothing anywhere. Export the log before clearing browser data.</p>"
        '<p id="log-empty" class="small muted">No events recorded yet. Rows appear below when the '
        "tracker records a real click or the labelled test event.</p>"
        '<div class="table-wrap"><table><thead><tr><th scope="col">Timestamp (UTC)</th><th scope="col">Type</th>'
        '<th scope="col">Target</th><th scope="col">ASIN</th></tr></thead><tbody id="event-rows"></tbody></table></div>'
        '<div class="btnrow"><button class="btn" id="btn-test" type="button">Add labelled test event</button>'
        '<button class="btn" id="btn-export-json" type="button">Export JSON</button>'
        '<button class="btn" id="btn-export-csv" type="button">Export CSV</button>'
        '<button class="btn danger" id="btn-clear" type="button">Clear log</button></div>'
        '<p class="note">The test button writes an event explicitly marked <b>test</b> so the mechanism '
        "can be checked end to end. It is never counted as a product click. Real clicks are recorded "
        "automatically when a visitor activates a link carrying the tracking attributes, which the "
        "product links on this site do.</p>"
        '<p class="note">The tracked links are the supplied short links. They currently carry no '
        "visible Associates tag, so a click recorded here cannot yet be attributed to an Associates "
        "account or reconciled against Amazon reporting (see " + flag_chip(current, "F-03") + ").</p>"
        "</section>"
        "<section><h2>Connecting real measurement</h2>"
        '<ul class="bullets">'
        f'<li>Join the Amazon Associates Program and receive an Associates ID, then use the tagged '
        f'Special Link formats (see {href(current, "policy-compliance.html", "Policy compliance")}).</li>'
        f'<li>Confirm the tag on the supplied short links before relying on any earnings (see '
        f'{href(current, "flagged.html", "F-03")}).</li>'
        f'<li>Authoritative click, order and commission figures come from the official '
        f'{ext("https://affiliate-program.amazon.com/", "Associates Central reporting")}.</li>'
        f'<li>Product data served from Amazon must come through the Creators API, and reusing or '
        f'fine-tuning on API content needs express prior written approval (see '
        f'{href(current, "flagged.html", "F-24")}).</li>'
        f'<li>Price tracking and price alerting are prohibited unless Amazon agrees otherwise, so no '
        f'price history is collected here (see {href(current, "flagged.html", "F-22")}).</li>'
        "<li>Add a cookie or consent notice appropriate to your audience before enabling measurement "
        "on real traffic, consistent with the disclosure expectations in the official Program Policies "
        "and applicable law.</li>"
        "</ul></section>"
        f'<p class="muted small">This page displays no prices, ratings or review counts (withheld under '
        f'{href(current, "flagged.html", "F-02")}). Verified product facts live in the '
        f'{href(current, "verification.html", "verification log")}.</p>'
    )


def page_information_gaps(current: Page) -> str:
    """The requested 'what we know / do not know / how to discover it' page.

    This is a companion to the questions register, not a duplicate of it: it
    groups the same recorded items by decision area, states plainly which are
    answered, which are not, and what evidence would close each one, so a reader
    can see the shape of the gap without reading 37 rows.
    """
    by_area: dict[str, list[dict]] = {}
    for q in QUESTIONS:
        by_area.setdefault(q["area"], []).append(q)
    areas_rows = []
    for area, items in sorted(by_area.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        known = [q for q in items if q["kind"] == "Known"]
        unknown = [q for q in items if q["kind"].startswith("Unknown")]
        owner = [q for q in items if q["kind"] == "Owner decision"]
        # Every row links the official source of the first question in the area,
        # because the counts summarise rows that are themselves sourced.
        urls = list(dict.fromkeys(s["url"] for q in items for s in q["sources"]))
        src_html = "<br>".join(ext(u, source_label(u)) for u in urls[:3])
        areas_rows.append([
            f"<strong>{esc(area)}</strong>",
            f'<span class="num">{len(known)}</span>',
            f'<span class="num">{len(unknown)}</span>',
            f'<span class="num">{len(owner)}</span>',
            " ".join(href(current, "questions.html", q["id"]) for q in items),
            src_html,
        ])
    prod_src = cited_sources("S-P1", "S-P2", "S-P3")
    have = [
        ("The three product identities", "ASINs resolved from the supplied short links, and the "
         "official product page behind each one.", prod_src, "products.html"),
        ("The brand and manufacturer fields", "Read from the official Item details tables, not from "
         "store links or reviewer blocks.", prod_src, "verification.html"),
        ("The listed specifications", "Capacity, footprint, colour, material and special features, "
         "quoted as written \u2014 including the listings' own unit mismatches.", prod_src, "products.html"),
        ("The rules that govern the site", "Operating Agreement, Program Policies, IP License, "
         "Trademark Guidelines, Conditions of Use, FTC guidance and Google's content guidance, each "
         "cited to the section relied on.", cited_sources("S-OA", "S-POL", "S-IPL", "S-FTC"),
         "policy-compliance.html"),
        ("The category-level commission rate", "The public Table 1 lists Kitchen at 4.50% and Home "
         "at 3.00%. This is a category reference only.", cited_sources("S-COMM"), "analysis.html"),
        ("A first-party click log", "A local-only tracker that starts at zero and publishes no "
         "attributed figure.", cited_sources("S-OA"), "analytics.html"),
    ]
    missing = [
        ("An Associates Partner Tag on the links", "Until the links carry a tag, a click cannot be "
         "attributed and no commission can be earned. Only the account holder can supply it.",
         "Q-01", "F-03"),
        ("Prices and star ratings on the public pages", "Permitted only through Amazon-served links or "
         "approved API data. Amazon's stated prerequisite for the API is 10 qualifying sales in 30 "
         "days, so this is downstream of the tag.", "Q-02", "F-02"),
        ("A per-ASIN commission category", "The public table gives category rates; no public source "
         "maps an ASIN to a band. It is visible in Associates Central to the account holder.",
         "Q-03", "F-01"),
        ("Any search-volume or traffic figure", "No official source for it exists in this environment, "
         "and inventing one is the defect this site exists to avoid.", "Q-19", "F-15"),
        ("Product photography", "The only honest routes are the owner's own photographs or images "
         "served through an approved Amazon tool. Neither exists yet.", "Q-21", "F-31"),
        ("Whether anything has been hands-on tested", "Nothing has. A claim otherwise would breach the "
         "FTC endorsement guidance cited on the policy page.", "Q-06", "F-12"),
    ]
    # Every row carries an official source, because a "what we have" row is itself
    # an assertion and this site's rule is that an assertion links out.
    have_rows = [[esc(a), esc(b), src_html, href(current, d, "See")] for a, b, src_html, d in have]
    # Each missing item names the specific rule its absence turns on, not a blanket
    # product page, so a reader can check the reason rather than take it.
    rule_for = {
        "Q-01": "S-OA", "Q-02": "S-POL", "Q-03": "S-COMM",
        "Q-19": "S-GOOGLE", "Q-21": "S-POL", "Q-06": "S-FTC",
    }
    missing_rows = [[esc(a), esc(b), href(current, "questions.html", q), flag_chip(current, f),
                     cited_sources(rule_for.get(q, "S-POL"))]
                    for a, b, q, f in missing]
    return (
        hero("Information gaps & questions",
             "What this project can already prove, what it cannot, and what would close each gap. "
             "Every row below points at a recorded question or an official source; none of it is "
             "estimated.")
        + '<section><h2>Where the gaps are, by area</h2>'
        + '<p class="section-lead">The same register as the Open questions page, counted by the '
          'subject a reviewer is deciding on. &ldquo;Owner&rdquo; rows are choices, not facts.</p>'
        + table(["Area", "Answered", "Unknown", "Owner decision", "Rows", "Source cited by the rows"],
                areas_rows, "compact")
        + "</section>"
        + '<section><h2>What we have</h2>'
        + '<p class="section-lead">Each item is live on this site and traceable to the official '
          'document named in the third column.</p>'
        + table(["What is established", "How it was established", "Source (official)", "Detail"], have_rows, "compact")
        + "</section>"
        + '<section><h2>What we do not have, and what would close it</h2>'
        + '<p class="section-lead">A gap stays a gap until a named party answers it. Nothing on this '
          'list is closed by inference, and no placeholder value stands in for one.</p>'
        + table(["Missing", "Why it matters, and what would close it", "Question", "Flag",
                 "Official rule the gap turns on"],
                [[r[0], r[1], r[2], r[3], r[4]] for r in missing_rows], "compact")
        + "</section>"
        + '<section><h2>The questions that need your answer first</h2>'
        + '<ol>' + "".join(
            f'<li><strong>{href(current, "questions.html", q["id"])}</strong> {esc(q["question"])} '
            f'<span class="muted small">&mdash; {esc(q["answerable_by"])}</span></li>'
            for q in QUESTIONS if q["kind"] == "Owner decision"
        ) + "</ol></section>"
        + f'<p class="small muted">This page is a summary. The full register, with each row\'s '
          f'&ldquo;what is already known&rdquo; and &ldquo;how the missing piece is discovered&rdquo; '
          f'columns, is on {href(current, "questions.html", "Open questions")}. The choices that '
          f'follow from those answers are on {href(current, "decisions.html", "Decision log")}.</p>'
    )


def commission_category_note() -> str:
    """The verified category-level rate, published without attaching it to an ASIN."""
    note = PRODUCTS_DOC.get("_meta", {}).get("commission_note")
    if not note:
        return ""
    url = next((p.get("commission_rate_source") for p in PRODUCTS if p.get("commission_rate_source")), None)
    link = ext(url, "Associates Program Standard Commission Income Statement") if url else ""
    return (
        '<div class="cta"><p><strong>Commission, at category level only.</strong> '
        f"{esc(note)} {link} "
        f'{flag_chip(Page("products.html", "", "", ""), "F-01")}</p></div>'
    )


PAGE_DESCRIPTIONS = {
    "index.html": "Three countertop air fryers, one honest shortlist: the format decision, the listed "
                   "specifications with their traps, and an official source link behind every figure.",
    "executive-summary.html": "What the verification found, the decisions that need an owner, and what "
                              "is deliberately not built. Each statement links to the official source behind it.",
    "products.html": "Three air-fryer product records side by side: brand, format, listed capacity, "
                     "footprint and the flags that apply, with price, rating and commission cells deliberately blank.",
    "categories/dual-basket-air-fryers.html": "The dual-basket format: the Chefman 6 quart record, its "
                                              "listed specifications, the competing ASINs shown beside it, and the review written from those facts.",
    "categories/single-basket-air-fryers.html": "The single-basket format: the Chefman 8 quart record, "
                                                "its listed presets and footprint, the 6/8/9 quart variant family, and the review written from those facts.",
    "categories/air-fryer-toaster-ovens.html": "The air-fry toaster oven format: the Emeril Lagasse 26 "
                                               "quart record, its listed functions and footprint, and the two specification inconsistencies disclosed rather than resolved.",
    "marketing.html": "The full marketing content kit on one page: three product articles, a comparison "
                      "and a buying guide, each with the fact table it was written from and a disclosure-carrying call to action.",
    "automation.html": "The affiliate pipeline stage by stage, with the status of each stage, the "
                       "official rule that constrains it, and every click, conversion and revenue metric left blank because nothing is connected.",
    "analysis.html": f"{len(CONTENT['analysis'])} findings on the three products and the programme "
                     "rules, each stating its basis, its confidence, and the official source an opinion would have to be checked against.",
    "requirements.html": f"All {len(REQUIREMENTS)} items in the project brief, one row each, with what "
                         "the site actually delivers, what blocks it and the official source that governs the status.",
    "verification.html": "A field-by-field verification log for all three products: every published "
                         "value, the official page it was read from, and a flag wherever it could not be confirmed.",
    "policy-compliance.html": f"{len(RULES)} Associates-programme and FTC requirements checked against "
                              "this site, each linked to the official section it comes from and to the way the site complies.",
    "analytics.html": "A first-party click log that lives only in your browser and starts at zero. No "
                      "network call, no estimate, and no attributed figure until Associates reporting is connected.",
    "flagged.html": "Every irregularity and unverified item found while building this site, each with "
                    "its severity, the source links behind it, and the action needed from the owner.",
    "sources.html": "Every source used, whether it was actually read, and what it was used for. Unread "
                    "sources are marked and nothing is inferred from them.",
    "articles/index.html": "Five articles grouped by product format: three reviews, one comparison and "
                           "one buying guide, each built from a fact table that links to the official page it was read from.",
    "suggestions.html": f"{len(SUGGESTIONS)} changes worth making to this site, costed, risk-assessed "
                        "and waiting on a decision rather than already applied, each tied to the official rule that constrains it.",
    "questions.html": f"{len(QUESTIONS)} questions that must be answered before any change can "
                      "reasonably be made: what is already known, what is missing, and who can supply it.",
    "decisions.html": "The decision queue for this site: every open choice with its options, cost and "
                      "reversibility, plus the record of decisions actually taken (currently none).",
    "decision-centre.html": "The review-before-you-build hub: the suggestions menu, the questions that "
                            "gate it, the decision queue and the flag register, with the order to work in and where each answer gets recorded.",
    "information-gaps.html": "What this project can already prove about the three air fryers, what it "
                             "cannot, and what would close each gap, with every row pointing at a recorded question or an official source.",
}

BODIES = {
    "index.html": page_index,
    "executive-summary.html": page_exec,
    "products.html": page_products,
    "categories/dual-basket-air-fryers.html": lambda c: page_category(c, "dual-basket-air-fryers"),
    "categories/single-basket-air-fryers.html": lambda c: page_category(c, "single-basket-air-fryers"),
    "categories/air-fryer-toaster-ovens.html": lambda c: page_category(c, "air-fryer-toaster-ovens"),
    "articles/index.html": page_articles_index,
    "decision-centre.html": page_decision_centre,
    "information-gaps.html": page_information_gaps,
    "marketing.html": page_marketing,
    "automation.html": page_automation,
    "analysis.html": page_analysis,
    "requirements.html": page_requirements,
    "verification.html": page_verification,
    "policy-compliance.html": page_policy,
    "suggestions.html": page_suggestions,
    "questions.html": page_questions,
    "decisions.html": page_decisions,
    "analytics.html": page_analytics,
    "flagged.html": page_flagged,
    "sources.html": page_sources,
}


#: The reader-facing navigation: five words and one action. The research layer
#: is one click away from every page (the fifth item) and listed in full in the
#: footer index, so a shopper never has to walk through a compliance register to
#: reach a review.
NAV = [
    ("index.html", "Home", "index.html"),
    ("articles/index.html", "Guides & reviews", "articles/index.html"),
    ("products.html", "The products", "products.html"),
    ("decision-centre.html", "Decision centre", "decision-centre.html"),
    ("flagged.html", "Flagged", "flagged.html"),
]
NAV_ACTIVE_OF = {target: active for target, _label, active in NAV}

#: The full index, rendered in the footer of every page: every page on the site,
#: grouped, so no page is orphaned and nothing is more than two clicks away.
NAV_INDEX = [
    ("Start here", [
        ("index.html", "Home"),
        ("articles/index.html", "Articles hub"),
        ("products.html", "All three products"),
    ]),
    ("Guides & reviews", [
        (BUYING_GUIDE, "Air fryer buying guide"),
        (COMPARISON, "Dual basket vs single basket vs toaster oven"),
        ("articles/chefman-6-quart-dual-basket-air-fryer-oven.html", "Review: Chefman 6 quart dual basket"),
        ("articles/chefman-8-quart-single-basket-air-fryer.html", "Review: Chefman 8 quart single basket"),
        ("articles/26qt-french-door-air-fryer-toaster-oven.html", "Review: Emeril Lagasse 26QT French door"),
    ]),
    ("By format", [
        ("categories/dual-basket-air-fryers.html", "Dual-basket air fryers"),
        ("categories/single-basket-air-fryers.html", "Single-basket air fryers"),
        ("categories/air-fryer-toaster-ovens.html", "Air-fry toaster ovens"),
    ]),
    ("Decide", [
        ("decision-centre.html", "Decision centre"),
        ("suggestions.html", "Suggestions"),
        ("questions.html", "Open questions"),
        ("information-gaps.html", "Information gaps"),
        ("decisions.html", "Decision log"),
    ]),
    ("Research & governance", [
        ("executive-summary.html", "Executive summary"),
        ("analysis.html", "Analysis & findings"),
        ("verification.html", "Verification log"),
        ("policy-compliance.html", "Policy compliance"),
        ("requirements.html", "Requirements"),
        ("automation.html", "Automation & tracking"),
        ("analytics.html", "Clicks & conversions"),
        ("flagged.html", "Flagged for review"),
        ("sources.html", "Sources"),
        ("marketing.html", "Marketing content kit"),
    ]),
]


def _nav_active(page: Page) -> str:
    """Which top-level nav item to highlight for a page."""
    path = page.path
    if path == "index.html":
        return "index.html"
    if path.startswith("articles/") or path == "marketing.html":
        return "articles/index.html"
    if path.startswith("categories/"):
        return "products.html"
    if path in ("suggestions.html", "questions.html", "decisions.html", "information-gaps.html"):
        return "decision-centre.html"
    if path in ("flagged.html", "verification.html", "sources.html", "policy-compliance.html",
                "requirements.html", "analytics.html", "executive-summary.html", "analysis.html",
                "automation.html"):
        return "flagged.html"
    return path


def render(page: Page) -> str:
    active = _nav_active(page)
    nav_items = "".join(
        f'<a href="{esc(page.rel(target))}"'
        + (' class="active" aria-current="page"' if target == active else "")
        + f">{label}</a>"
        for target, label, _active in NAV
    )
    disclosure = (
        f'<div class="disclosure" role="note"><div class="disclosure-inner"><strong>Disclosure:</strong> '
        f"{esc(DISCLOSURE_SENTENCE)} "
        f'<span class="small">(Source: '
        f'{ext(DISCLOSURE_SOURCE, "Associates Operating Agreement, Section 5")}) '
        "This site is not endorsed by or affiliated with Amazon.</span></div></div>"
    )
    # IP License Section 2(k) requires this text in plain view when Product
    # Advertising Content consisting of text (here, listing titles) is displayed.
    # It is data-driven so it can be withdrawn without touching the template.
    amazon_text = ""
    notice = CONTENT.get("site_disclaimer") or {}
    if notice.get("text"):
        amazon_text = (
            f'\n<div class="disclosure" role="note"><div class="disclosure-inner">'
            f'<strong>Amazon content notice:</strong> {esc(notice["text"])}'
            f' <span class="small">(Source: {ext(notice["source_url"], notice.get("source_ref", "IP License"))}'
            f")</span></div></div>"
        )
    footer_groups = "".join(
        f'<div><div class="footer-head">{esc(html.unescape(group))}</div>'
        + "".join(
            f'<a href="{esc(page.rel(t))}">{esc(l)}</a>' for t, l in items
        )
        + "</div>"
        for group, items in NAV_INDEX
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(page.title_tag or page.title)} | {esc(SITE_TITLE_SUFFIX)}</title>
<meta name="description" content="{esc(page.description or SITE_DESCRIPTION)}">
{page.head_extra}
<link rel="stylesheet" href="{esc(page.rel('styles.css'))}">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="layout">
<header class="masthead">
  <div class="masthead-inner">
    <a class="wordmark" href="{esc(page.rel('index.html'))}">
      <span class="wordmark-name">{esc(BRAND_NAME)}</span>
      <span class="wordmark-dot" aria-hidden="true"></span>
      <span class="wordmark-tag">{esc(BRAND_TAGLINE)}</span>
    </a>
    <nav class="topnav" aria-label="Main">{nav_items}</nav>
  </div>
</header>
<div class="content">
{disclosure}{amazon_text}
<main id="main">
{page.body}
</main>
<footer>
  <div class="footer-inner">
    <div class="footer-index">{footer_groups}</div>
    <p class="footer-note small">
      Data observed {esc(OBSERVED)} (UTC). {esc(BRAND_NAME)} publishes only values that were read
      from an official page and linked here; the supplied links and the cited policy pages were
      re-read {esc(RECHECKED)} (UTC). Prices, star ratings and per-product commission rates are
      deliberately withheld or blank (F-01, F-02), and no hands-on testing is claimed. Source of truth:
      the <code>data/</code> folder in the repository. Built by <code>scripts/build_site.py</code> and
      checked by <code>scripts/verify.py</code>, <code>qa/audit_site.py</code> and the engine tests.
    </p>
    <p class="footer-note small">
      <strong>As an Amazon Associate I earn from qualifying purchases.</strong>
      This site is not endorsed by or affiliated with Amazon. Every gap and every unverified item is
      published on the <a href="{esc(page.rel('flagged.html'))}">Flagged for Review</a> page rather than hidden.
    </p>
  </div>
</footer>
</div>
</div>
<script src="{esc(page.rel('app.js'))}"></script>
</body>
</html>
"""


def article_jsonld(a: dict) -> str:
    """JSON-LD Article metadata for one article page.

    States only what the page visibly shows: the article's own headline,
    description and dates, and the site itself. No ratings, no prices, no
    offers - the site publishes none, and structured-data guidelines forbid
    marking up content the user cannot see. Added by session arena/d8564cd0-zone4.
    """
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": a["h1"],
        "description": a["meta_description"],
        "datePublished": OBSERVED,
        "dateModified": RECHECKED,
        "inLanguage": "en",
        "author": {"@type": "Organization", "name": BRAND_NAME},
        "publisher": {"@type": "Organization", "name": BRAND_NAME},
        "mainEntityOfPage": SITE_URL + "articles/" + a["slug"].strip("/") + ".html",
    }
    return (
        '<script type="application/ld+json">'
        + json.dumps(data, ensure_ascii=False)
        + "</script>"
    )


def website_jsonld() -> str:
    """JSON-LD WebSite metadata for the landing page (own-site facts only)."""
    data = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": BRAND_NAME,
        "url": SITE_URL,
        "description": SITE_DESCRIPTION,
        "inLanguage": "en",
    }
    return (
        '<script type="application/ld+json">'
        + json.dumps(data, ensure_ascii=False)
        + "</script>"
    )


def collect_pages() -> list[Page]:
    """Every page on the site, in navigation order.

    The article pages are derived from data/marketing.json, so a page can only
    exist for an article that is actually in the data.
    """
    pages: list[Page] = []
    for path, body_fn in BODIES.items():
        page = Page(path, NAV_LABEL.get(path, path), path, "",
                    description=PAGE_DESCRIPTIONS.get(path))
        page.body = body_fn(page)
        if path == "index.html":
            page.head_extra = website_jsonld()
        pages.append(page)
    hub = Page(ARTICLES_HUB, NAV_LABEL[ARTICLES_HUB], ARTICLES_HUB, "")
    hub.body = page_articles_index(hub)
    pages.append(hub)
    for a, path in ARTICLE_PATHS:
        page = Page(path, article_label(a), path, "",
                    description=a["meta_description"], title_tag=a["title_tag"])
        page.body = page_article(page, a)
        page.head_extra = article_jsonld(a)
        pages.append(page)
    return pages


def build() -> list[pathlib.Path]:
    OUT.mkdir(exist_ok=True)
    (OUT / "categories").mkdir(exist_ok=True)
    (OUT / "articles").mkdir(exist_ok=True)
    written = []
    for page in collect_pages():
        html_text = render(page)
        if page.path == "analytics.html":
            html_text = html_text.replace(
                "</body>",
                f'<script src="{esc(page.rel("tracker.js"))}"></script>\n</body>',
            )
        out = OUT / page.path
        out.write_text(html_text, encoding="utf-8")
        written.append(out)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    # A generated sitemap of the site's own pages: every URL in it is one this
    # build produced, on the Pages host for this repository. Nothing here is a
    # claim about products; submission to a search console is a user decision
    # (suggestion S-06 / open questions register). Added by arena/d8564cd0-zone4.
    site_urls = [SITE_URL + p.path for p in collect_pages()]
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in site_urls)
        + "</urlset>\n"
    )
    (OUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    return written


if __name__ == "__main__":
    for p in build():
        print("wrote", p.relative_to(ROOT))
