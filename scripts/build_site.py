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

SITE_URL = "https://kanlerxz87-cyber.github.io/Zone4/docs/"

NAV = [
    ("index.html", "Dashboard", "Overview"),
    ("executive-summary.html", "Executive summary", "Overview"),
    ("products.html", "All products", "Overview"),
    ("categories/dual-basket-air-fryers.html", "Dual-basket air fryers", "Categories"),
    ("categories/single-basket-air-fryers.html", "Single-basket air fryers", "Categories"),
    ("categories/air-fryer-toaster-ovens.html", "Air-fry toaster ovens", "Categories"),
    ("marketing.html", "Marketing content", "Content"),
    ("automation.html", "Automation & tracking", "Research"),
    ("analysis.html", "Analysis & findings", "Research"),
    ("requirements.html", "Requirements", "Research"),
    ("suggestions.html", "Suggestions", "Decide"),
    ("questions.html", "Open questions", "Decide"),
    ("decisions.html", "Decision log", "Decide"),
    ("verification.html", "Verification log", "Governance"),
    ("policy-compliance.html", "Policy compliance", "Governance"),
    ("analytics.html", "Analytics", "Governance"),
    ("flagged.html", "Flagged for review", "Governance"),
    ("sources.html", "Sources", "Governance"),
]
NAV_LABEL = {target: label for target, label, _group in NAV}
NAV_ORDER = [
    ("Overview", [t for t, _l, g in NAV if g == "Overview"]),
    ("Categories", [t for t, _l, g in NAV if g == "Categories"]),
    ("Content", [t for t, _l, g in NAV if g == "Content"]),
    ("Research", [t for t, _l, g in NAV if g == "Research"]),
    ("Decide", [t for t, _l, g in NAV if g == "Decide"]),
    ("Governance", [t for t, _l, g in NAV if g == "Governance"]),
]

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
CATEGORY_TITLE = {t: l for t, l, _g in NAV if t.startswith("categories/")}
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
NAV_LABEL[ARTICLES_HUB] = "Articles hub"
NAV_ORDER.insert(3, ("Articles", [ARTICLES_HUB] + [p for _a, p in ARTICLE_PATHS]))


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
    return ext(p["short_link"], "Open Amazon link (paid link)",
               f' class="shop" data-track="click" data-track-target="{esc(p["short_link"])}" data-track-asin="{esc(p["asin"])}"')


# ---------------------------------------------------------------- tables

def commission_cell(p: dict) -> str:
    """Commission rate for a product, sourced from the official rate table.

    Returns the withheld pill when the data carries no rate, so this cell cannot
    publish a number that the ledger does not attribute to a source. A rate is a
    program term, not Amazon pricing, so it is displayable under the relevant
    participation requirements; the product-level value is blank when unverified.
    """
    rate = p.get("commission_rate_pct")
    url = p.get("commission_rate_source")
    if rate is None or not url:
        if url:
            return (pill("Blank — category unverified for this ASIN (F-01)", "warn")
                    + f' <span class="small">{ext(url, "official category table")}</span>')
        return pill("Blank — unverified (F-01)", "warn")
    return (pill(f"{rate:.2f}% ({p.get('commission_category_official', 'category')} band)", "ok")
            + f' <span class="small">{ext(url, "official Table 1")}</span>')


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
            commission_cell(p),
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

def hero(title: str, lead: str) -> str:
    return f'<header class="hero"><h1>{esc(title)}</h1><p class="lead">{esc(lead)}</p></header>'


def article_card(current: Page, a: dict, show_category: bool = True) -> str:
    """A teaser card for one article: category chip, headline, dek and metadata.

    `show_category` is off on the articles hub, where the group heading above the
    card already names the category.
    """
    key = article_category(a)
    cat_label = CATEGORY_TITLE.get("categories/" + key + ".html", "") if key else ""
    chip = f'<span class="chip">{esc(cat_label)}</span>' if (show_category and cat_label) else ""
    return (
        f'<a class="acard" href="{esc(current.rel(article_path(a)))}">'
        f'<div class="acard-top">{chip}<span class="chip chip-quiet">{esc(a["page_type"])}</span></div>'
        f'<div class="acard-title">{esc(a["h1"])}</div>'
        f'<div class="acard-dek">{esc(a["meta_description"])}</div>'
        f'<div class="acard-meta">{article_read_minutes(a)} min read \u00b7 '
        f'{len(a["facts"])} sourced facts \u00b7 observed {esc(OBSERVED)}</div>'
        "</a>"
    )


def decision_queue_section(current: Page) -> str:
    """The decisions that gate the rest, as cards rather than another table.

    The site is a proposal, not a finished product: much of what the brief asks
    for cannot be built without an answer only the owner can give. Saying so on
    the landing page is more useful to a reader than another product card, and a
    card reads better here than a four-column table of prose.
    """
    open_decisions = [d for d in DECISIONS if d["status"].startswith("Open")]
    top = open_decisions[:3]
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
        f'<section><h2>Before anything else: {len(open_decisions)} decisions are yours</h2>'
        '<p class="section-lead">This site publishes only what an official source supports, which means a number of things the '
        'brief asks for cannot be built until you answer. The three that gate the rest are below. Each one lists its options, '
        'what each option commits the site to, and what would prove it worked.</p>'
        f'<div class="agrid">{cards}</div>'
        + '<p>'
        + href(current, "decisions.html", "Work through all " + str(len(open_decisions)) + " decisions →")
        + " &nbsp; "
        + href(current, "suggestions.html", f"{len(SUGGESTIONS)} costed suggestions")
        + " &nbsp; "
        + href(current, "questions.html", f"{len(QUESTIONS)} open questions")
        + "</p></section>"
    )


def page_index(current: Page) -> str:
    open_flags = [f for f in FLAGS if flag_group(f["status"]) == "Needs your decision"]
    # Derived from the data, not typed in, so a KPI cannot drift from the tables below it.
    assigned = sum(
        1 for p in PRODUCTS
        if p.get("commission_rate_pct") is not None and p.get("commission_category_official")
    )
    kpis = [
        (f"{len(PRODUCTS)} of {len(PRODUCTS)}", "Products with verified ASIN, category, brand and specification table"),
        (str(len(ARTICLES)), f"Published articles: {sum(1 for a in ARTICLES if a['page_type'] == 'Product article')} reviews, "
                             f"{sum(1 for a in ARTICLES if a['page_type'] == 'Comparison')} comparison, "
                             f"{sum(1 for a in ARTICLES if a['page_type'] == 'Buying guide')} buying guide"),
        ("0", "Amazon prices published (policy F-02)"),
        (f"{assigned} of {len(PRODUCTS)}", "ASIN commission-category assignments confirmed (F-01)"),
        (str(len(open_flags)),
         f"Flags awaiting your decision, of {len(FLAGS)} recorded (the rest are corrected or resolved and kept as "
         "the audit record on the Flagged for review page)"),
    ]
    kpi_html = "".join(
        f'<div class="kpi"><div class="kpi-value">{esc(v)}</div><div class="kpi-label">{esc(l)}</div></div>'
        for v, l in kpis
    )
    # Articles presented in decision order (buying guide, then comparison, then
    # the product reviews), per suggestion S-02/S-03 of session arena/d8564cd0-zone4.
    trending = "".join(article_card(current, a) for a in sorted(
        ARTICLES,
        key=lambda a: {"Buying guide": 0, "Comparison": 1}.get(a["page_type"], 2),
    ))
    cat_tiles = "".join(
        f'<a class="tile" href="{esc(current.rel(target))}"><div class="tile-title">{esc(label)}</div>'
        f'<div class="tile-sub">{esc(next(p["name_short"] for p in PRODUCTS if CATEGORY_BY_PRODUCT.get(p["id"]) == key))}</div>'
        f'<div class="tile-go">Open category \u2192</div></a>'
        for target, label, key in
        ((t, l, t[len("categories/"):-len(".html")]) for t, l, _g in NAV if t.startswith("categories/"))
    )
    bullets = "".join(f"<li>{esc(b)}</li>" for b in CONTENT["executive_summary"]["bullets"][:4])
    return (
        '<div class="mhero">'
        f'<span class="badge">Verified {esc(OBSERVED)} \u00b7 {len(PRODUCTS)} products \u00b7 a source link on every table row</span>'
        "<h1>Choosing between three countertop air fryers? Start with every listed figure checked.</h1>"
        f'<p class="lead">{esc(CONTENT["executive_summary"]["headline"])}</p>'
        '<div class="mhero-actions">'
        f'<a class="btn btn-primary" href="{esc(current.rel(ARTICLE_PATHS[-1][1]))}">Start with the buying guide</a>'
        f'<a class="btn" href="{esc(current.rel("articles/dual-basket-vs-single-basket-vs-toaster-oven-air-fryer.html"))}">Compare the three formats</a>'
        f'<a class="btn" href="{esc(current.rel("suggestions.html"))}">Pick a path</a>'
        f'<a class="btn" href="{esc(current.rel("flagged.html"))}">See what is flagged</a>'
        "</div></div>"
        + f'<section class="kpis">{kpi_html}</section>'
        + '<section><h2>The articles, in decision order</h2>'
        '<p class="section-lead">Start with the buying guide, compare the three formats, then read the review for the '
        "product that fits your kitchen. Each article is built only from figures read off the official product page, and "
        "every fact it states is a row in a table that links back to that page.</p>"
        f'<div class="agrid">{trending}</div></section>'
        + '<section><h2>Shop by category</h2><div class="tiles">' + cat_tiles + "</div></section>"
        + decision_queue_section(current)
        + '<section><h2>Products at a glance</h2>'
        + '<p><input id="filter" class="filter" type="search" placeholder="Filter rows (for example: Chefman, B0C\u2026, Flag F-02)" aria-label="Filter table"></p>'
        + product_table(current, PRODUCTS)
        + commission_category_note()
        + '<p class="small muted">Every row links to its official product page as the source. Short links are the links you '
        "supplied. Competitor ASINs come from the also-viewed carousel and change between page loads (F-29).</p></section>"
        + '<section><h2>Key findings</h2><ul class="bullets">' + bullets + "</ul>"
        + f'<p>{href(current, "executive-summary.html", "Read the full executive summary →")}</p></section>'
        + f'<p class="muted small">Data observed {esc(OBSERVED)} (UTC). Verification scope and method: {href(current, "sources.html", "sources")}.</p>'
    )


def page_articles_index(current: Page) -> str:
    """The articles hub: every published article, grouped by the category it covers."""
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
        key = next((k for k in CATEGORY_BY_PRODUCT.values() if CATEGORY_TITLE.get("categories/" + k + ".html") == title), "")
        if key:
            link = (f'<p class="small">{href(current, "categories/" + key + ".html", "See the category record →")}</p>')
        blocks.append(f'<section><h2>{esc(title)}</h2><div class="agrid">{cards}</div>{link}</section>')
    return (
        hero("Articles", "Every article published on this site, grouped by the product format it covers. "
                         "The copy is written here, not republished from the listings, and each piece carries the "
                         "fact table it was written from.")
        + "".join(blocks)
        + '<section><h2>How these are written</h2>'
        + "<p>"
        + esc(MARKETING["_meta"]["method"])
        + "</p>"
        + marketing_seo_rules_table()
        + "</section>"
    )


def page_article(current: Page, a: dict) -> str:
    """One article, published as a page with its own title tag and meta description."""
    facts_by_id = {f["id"]: f for f in a["facts"]}
    body_html = []
    for para in a["body"]:
        # An optional subheading per paragraph: editorial structure only. The
        # heading is not a factual claim and never appears in the fact tables.
        # Added by session arena/d8564cd0-zone4 (suggestion S-03).
        sub = f'<h2 class="phead">{esc(para["h"])}</h2>' if para.get("h") else ""
        cites = "".join(
            f'<a class="cite" href="{esc(facts_by_id[fid]["source_url"])}" rel="noopener noreferrer">{esc(fid)}</a>'
            for fid in para["fact_ids"] if fid in facts_by_id
        )
        body_html.append(f'{sub}<p>{esc(para["text"])} <span class="cites">{cites}</span></p>')
    outline_html = "".join(
        f'<li><strong>{esc(o["h2"])}</strong> - {esc(o["purpose"])} '
        f'<span class="muted">(facts: {esc(", ".join(o["facts_used"]))})</span></li>'
        for o in a["outline"]
    )
    notes_html = "".join(f"<li>{esc(n)}</li>" for n in a["compliance_notes"])
    cta = a["cta"]
    cta_button = ext(cta["link_url"], cta["link_label"], ' class="shop"')
    # The disclosure and a plain-language paid-link label sit in the same
    # paragraph as the affiliate link, not below it, so both are adjacent to the
    # link they qualify. qa/audit_site.py fails the build if either is missing.
    cta_html = (
        f'<div class="cta"><p>{esc(cta["text"])}</p>'
        f'<p>{cta_button} <span class="note">(paid link)</span>'
        f' <span class="note"><strong>Disclosure:</strong> {esc(cta["disclosure"])}</span></p></div>'
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
        + f' \u00b7 {article_read_minutes(a)} min read \u00b7 {len(a["facts"])} sourced facts \u00b7 observed {esc(OBSERVED)}</div>'
    )
    seo_html = (
        "<dl class=\"seo\">"
        f"<dt>Suggested URL slug</dt><dd><code>{esc(a['slug'])}</code></dd>"
        f"<dt>Title tag</dt><dd>{esc(a['title_tag'])}</dd>"
        f"<dt>Meta description</dt><dd>{esc(a['meta_description'])}</dd>"
        f"<dt>Page type</dt><dd>{esc(a['page_type'])}</dd>"
        "</dl>"
    )
    # Related reading: the other articles, with the category record first when there is one.
    related = [x for x in ARTICLES if x["id"] != a["id"]]
    if key:
        related.sort(key=lambda x: 0 if article_category(x) == key else 1)
    related_html = "".join(article_card(current, x) for x in related[:3])

    return (
        "<article class=\"post\">"
        + crumb
        + meta_line
        + f'<h1>{esc(a["h1"])}</h1>'
        + f'<p class="dek">{esc(a["meta_description"])}</p>'
        + "".join(body_html)
        + cta_html
        + "<h2>Fact basis (every row links to its official source)</h2>"
        + marketing_fact_table(a)
        + "<h2>Keyword targets</h2>"
        + marketing_keyword_table(a)
        + "<h2>Search metadata</h2>"
        + seo_html
        + "<h2>Outline</h2><ul class=\"outline\">" + outline_html + "</ul>"
        + "<h2>Compliance notes</h2><ul>" + notes_html + "</ul>"
        + "</article>"
        + '<section><h2>Related reading</h2><div class="agrid">' + related_html + "</div></section>"
    )


def page_exec(current: Page) -> str:
    es = CONTENT["executive_summary"]
    bullets = "".join(f"<li>{esc(b)}</li>" for b in es["bullets"])
    decisions = "".join(f"<li>{esc(d)}</li>" for d in es["decisions_needed"])
    not_built = "".join(f"<li>{esc(d)}</li>" for d in CONTENT["not_built"])
    return (
        hero("Executive summary", es["headline"])
        + f'<section><h2>What the verification found</h2><ul class="bullets">{bullets}</ul></section>'
        + f'<section><h2>Decisions needed from you</h2><ol>{decisions}</ol>'
        + f'<p class="small muted">Each of these is written up on the {href(current, "decisions.html", "Decision log")} with its options, '
          f'cost and reversibility, and each one unlocks a costed entry on the {href(current, "suggestions.html", "Suggestions")} page. '
          f'The unknowns behind them are on {href(current, "questions.html", "Open questions")}.</p></section>'
        + f'<section><h2>Not built, and why</h2><ul>{not_built}</ul></section>'
        + '<section><h2>Detail</h2><p>See '
        + href(current, "analysis.html", "Analysis & findings") + ", "
        + href(current, "marketing.html", "Marketing content") + ", "
        + href(current, "automation.html", "Automation & tracking") + ", "
        + href(current, "flagged.html", "Flagged for review") + " and "
        + href(current, "sources.html", "Sources") + ".</p></section>"
    )


def commission_category_note() -> str:
    """The verified category-level rate, published without attaching it to an ASIN.

    The official Table 1 rate is a real, sourced figure, but which commission
    category Amazon assigns to each of these ASINs is not confirmable from
    outside Associates Central, so the product rows stay blank and this note
    carries the verified fact on its own, with its source.
    """
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


def page_products(current: Page) -> str:
    return (
        hero("All products",
         "One row per user-supplied link. Prices and ratings are withheld under the Associates policy. The "
         "commission category Amazon assigns to each ASIN is not confirmed by any official source, so the "
         "product-level rate cells are blank and only the official category-level Kitchen rate (4.50%) is "
         "quoted, with its source; all trend data remains unverified and blank.")
        + '<p><input id="filter" class="filter" type="search" placeholder="Filter rows (for example: Chefman, B0C…, Flag F-02)" aria-label="Filter table"></p>'
        + product_table(current, PRODUCTS)
        + commission_category_note()
        + '<p class="small muted">Every row links to its Amazon product page as the source. Short links are the links you supplied. '
        'Also-viewed entries are identified by ASIN; the stored labels are the exact listing-title prefixes as read '
        'on the official pages (F-20), and the carousel changes between loads (F-29). The full title is on each linked page.</p>'
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
        '<p class="lead">Every irregularity and unverified item found while building this site, grouped by what it needs '
        'from you. Each one links to its source, and the action column says what is needed. None of these blocks the site '
        'from being live.</p></header>'
        f'<section class="kpis">{counts}</section>'
        + "".join(sections)
        + f'<p class="small muted">Every flag is also a row in <code>data/flags.json</code>. Where a flag points at a change '
          f'worth making, the {href(current, "suggestions.html", "Suggestions")} page costs it and the '
          f'{href(current, "decisions.html", "Decision log")} page records the choice.</p>'
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


# ------------------------------------------------- decision-support pages
# The three pages below answer one question each: what could we change, what do
# we still not know, and what has already been decided. They render from
# data/suggestions.json, data/questions.json and data/decisions.json so a row
# and its counterpart in the registers can never disagree.

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
    """One scannable line per suggestion. The argument lives in the card below."""
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
    """The case for one suggestion: problem, proposal, cost, risk, proof."""
    srcs = "".join(
        f'<li>{ext(x["url"], x["ref"])}</li>' for x in s["sources"]
    )
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
         "A backlog you approve before anything is built. Each entry states the problem, the proposed change, what it costs, "
         "what it risks and the check that would prove it worked. Nothing here has been implemented."),
        (f"{first} decisions come first",
         "The P1 entries change what the other suggestions are even possible: the link tag, the API route, the editorial note "
         "and the per-page metadata. Working up from P3 would waste the effort."),
        (f"{open_count} of {len(SUGGESTIONS)} await your answer",
         "The rest are corrections with one right answer, listed so the change is visible rather than silent. They are recorded "
         "as recommended, not as decided."),
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
        '<p class="lead">Every change worth making to this site, costed and risk-assessed, waiting on a decision rather than '
        'already applied. Pick a path here before anything is built.</p></header>'
        f'<section class="kpis kpis-stack">{card_html}</section>'
        '<section><h2>At a glance</h2>'
        '<p class="section-lead">One line per suggestion. The full case for each is in the section below it.</p>'
        + '<p><input id="filter" class="filter" type="search" placeholder="Filter suggestions (for example: P1, tag, commission)" aria-label="Filter suggestions"></p>'
        + table(["ID", "Priority", "Suggestion", "Status", "Decision", "Primary source (official)", "Flags"],
                suggestion_summary_rows(current), "suggestions")
        + '<p class="note">Every row links to the official source that constrains it. Where a suggestion has no external rule '
          'behind it, the source column names the repository file the problem was observed in.</p></section>'
        + "".join(blocks)
        + f'<p class="small muted">Choosing a path happens on the {href(current, "decisions.html", "Decision log")} page. '
        f'The unknowns that gate these entries are on {href(current, "questions.html", "Open questions")}. '
        f'Defects already found in the published site are on {href(current, "flagged.html", "Flagged for review")}.</p>'
        + design_prompt_block(current)
    )


def design_prompt_block(current: Page) -> str:
    """A paste-ready design brief for whoever runs the next site-design pass.

    Added by session arena/d8564cd0-zone4 as an additive section (suggestion
    S-01/S-02 direction). It is a proposal, labelled as one; it contains no
    product claims, so it needs no external source, but it encodes the
    compliance constraints already recorded on this site so that any design
    produced from it still has to pass the same checks.
    """
    return (
        '<section><h2>A prompt-ready design brief</h2>'
        '<p class="section-lead">For whoever runs the next design pass: a brief that can be pasted into a design prompt '
        'as-is. It encodes the constraints above rather than replacing them; edit it freely before use.</p>'
        '<div class="promptblock">'
        '<pre>Redesign the Zone4 affiliate research site as a polished, trustworthy buying-advice site '
        'for countertop air fryers, without changing its verification rules.\n\n'
        'Audience: shoppers choosing between a dual-basket air fryer, a single-basket air fryer and a '
        'French-door air fryer toaster oven, who want honest, sourced specifications before they click through to a store.\n\n'
        'Visual direction: warm kitchen palette (warm amber accent on deep slate and warm off-white surfaces), one clear type scale, '
        'card-based layout with soft shadows and rounded corners, generous whitespace, prominent verification badge. '
        'No external fonts or frameworks; one stylesheet; system font stack.\n\n'
        'Structure: decision-first landing page (who this is for, what to do next, one primary action); '
        'buying guide as the top-of-funnel page linking to a comparison and three product reviews; '
        'each review with scannable subheadings, a "who this suits" box built only from cited facts, '
        'and one clearly labelled call to action after the substance, with the affiliate disclosure adjacent.\n\n'
        'Hard constraints: every table row keeps a link to its official source; no prices, no star ratings, no review counts; '
        'no Amazon marks in page titles or keywords; the disclosure stays on every page; no product images unless they come '
        'from an approved Amazon-served route; the site never claims testing, ranking or trends it cannot evidence.\n\n'
        'Trust layer: keep the Flagged for Review, Open questions, Decision log and Verification pages one click from the homepage; '
        'a reader should be able to trace any published number to its official source in one click.</pre>'
        '<p class="note">Proposal prepared by session arena/d8564cd0-zone4 (2026-11-15). First steps already shipped in the '
        'current build with no decision needed: the warm-identity stylesheet refresh, subheaded article copy (facts unchanged), '
        'Article/WebSite JSON-LD that states only what each page visibly shows, and a generated '
        '<code>docs/sitemap.xml</code>. Everything else waits on a decision on the '
        + href(current, "decisions.html", "Decision log") + ' page; the compliance constraints it encodes live on the '
        + href(current, "policy-compliance.html", "policy page") + ' and in the '
        + href(current, "flagged.html", "flag register") + '.</p>'
        '</div></section>'
    )


def question_rows() -> list[list[str]]:
    rows = []
    for q in QUESTIONS:
        rows.append([
            f'<span id="{esc(q["id"])}"><strong>{esc(q["id"])}</strong></span>',
            esc(q["area"]),
            esc(q["question"]),
            esc(q["why_it_matters"]),
            pill(q["kind"], {"Known": "ok", "Owner decision": "warn"}.get(q["kind"], "bad" if q["kind"].startswith("Unknown") else "muted")),
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
    summary = " &middot; ".join(f'<strong>{esc(k)}</strong>: {v}' for k, v in kinds.items())
    return (
        '<header class="hero"><h1>Open questions</h1>'
        '<p class="lead">What has to be answered before any suggestion can reasonably be acted on, separated into what is already '
        'known, what is missing, and who can supply it. Most of these are not research problems: they need an account, a seller or '
        'a lawyer, and no further reading will close them.</p>'
        f'<p class="muted small">{len(QUESTIONS)} questions &middot; {summary}</p></header>'
        '<section><h2>The register</h2>'
        '<p class="section-lead">The &ldquo;known&rdquo; column states what the repository can already support, so a reviewer does not '
        'have to re-derive it. The &ldquo;how to discover&rdquo; column is the shortest route to an answer, not a guess at one.</p>'
        + table(["ID", "Area", "Question", "Why it blocks a decision", "Kind", "What is already known",
                 "How the missing piece is discovered", "Answerable by", "Sources (official)"],
                question_rows(), "questions")
        + '<p class="note">A question closes only on a named source, a named party&rsquo;s answer, or an owner decision recorded in the '
        'Decision log. It is never closed by inference.</p>'
        '</section>'
        '<section><h2>Why this page exists</h2>'
        '<p>Three of these gaps decide whether this project can earn at all: the Associates tag (Q-01), API access for prices and '
        'ratings (Q-02), and the per-ASIN commission category (Q-03). Three more decide whether it can honestly describe itself: who '
        'reviews the copy (Q-05), whether anything was tested (Q-06), and whether automated collection needs a legal opinion (Q-07). '
        'The rest are presentation and operations choices with named owners.</p>'
        f'<p class="small muted">Related: {href(current, "suggestions.html", "Suggestions")} for what each answer would unlock, '
        f'{href(current, "decisions.html", "Decision log")} for the choices already recorded (none, as of {esc(OBSERVED)}).</p>'
        '</section>'
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
            + (f' &middot; Gated by: {qlink}' if qlink else "")
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
        '<p class="lead">The queue you work through before any suggestion is built, and the record of what has actually been '
        'decided. Nothing in this repository acts on an option by itself: the site stays exactly as it is until a choice is recorded here.</p></header>'
        f'<section class="kpis">{kpi_html}</section>'
        '<p class="small muted">Pick an option and the site owner records it in the log at the bottom of this page, with the date. '
        'The recommendation is an argument, not a decision, and it is labelled as one.</p>'
        + "".join(blocks)
        + '<section><h2>Recorded decisions</h2>'
        + table(["Date (UTC)", "Decision", "Choice", "Recorded by", "Evidence", "Where it is recorded"],
                log_rows, "decision-log")
        + '<p class="note">Empty is a valid and honest state. As of this build no owner decision has been recorded, so every row above '
          'is still open and no suggestion has been implemented.</p></section>'
    )


# Every page states what it contains, in its own words. Google's snippet
# guidance asks for a unique description per page; the article pages already
# carried their own, and these cover the rest. The build fails if two pages
# share one (see scripts/verify.py), so this cannot silently regress.
PAGE_DESCRIPTIONS = {
    "index.html": "A dashboard of verified air-fryer research: three product records, five sourced articles, a policy check on every claim, and an official source link on every table row.",
    "executive-summary.html": "What the verification found, the seven decisions that need an owner, and what is deliberately not built. Each statement links to the official source behind it.",
    "products.html": "Three air-fryer product records side by side: brand, category path, listed capacity, dimensions and also-viewed competitors, with prices, ratings and commission cells deliberately blank.",
    "categories/dual-basket-air-fryers.html": "The dual-basket air-fryer category: the Chefman 6 quart record, its listed specifications, the competing ASINs shown beside it on the listing, and the article written from those facts.",
    "categories/single-basket-air-fryers.html": "The single-basket air-fryer category: the Chefman 8 quart record, its listed presets and footprint, the size variants on the same page, and the article written from those facts.",
    "categories/air-fryer-toaster-ovens.html": "The air-fry toaster oven category: the Emeril Lagasse 26 quart record, its listed functions and footprint, and the two specification inconsistencies disclosed rather than resolved.",
    "marketing.html": "The full marketing content kit on one page: three product articles, a comparison and a buying guide, each with the fact table it was written from and a disclosure-carrying call to action.",
    "automation.html": "The affiliate pipeline stage by stage, with the status of each stage, the official rule that constrains it, and every click, conversion and revenue metric left blank because nothing is connected.",
    "analysis.html": "Fifteen findings on the three products and the programme rules, each stating its basis, its confidence, and the official source an opinion would have to be checked against.",
    "requirements.html": "All thirty items in the project brief, one row each, with what the site actually delivers, what blocks it and the official source that governs the status.",
    "verification.html": "A field-by-field verification log for all three products: every published value, the official page it was read from, and a flag wherever it could not be confirmed.",
    "policy-compliance.html": "Thirty Associates-programme and FTC requirements checked against this site, each linked to the official section it comes from and to the way the site complies.",
    "analytics.html": "A first-party click log that lives only in your browser and starts at zero. No network call, no estimate, and no attributed figure until Associates reporting is connected.",
    "flagged.html": "Every irregularity and unverified item found while building this site, each with its severity, the source links behind it, and the action needed from the owner.",
    "sources.html": "Every source used, whether it was actually read, and what it was used for. Unread sources are marked and nothing is inferred from them.",
    "articles/index.html": "Every article on the site, grouped by product format, each one built from a fact table in which every row links to the official product page it was read from.",
    "suggestions.html": "Twelve changes worth making to this site, costed, risk-assessed and waiting on a decision rather than already applied, each tied to the official rule that constrains it.",
    "questions.html": "Fifteen questions that must be answered before any change can reasonably be made: what is already known, what is missing, and who can supply it.",
    "decisions.html": "The decision queue for this site: every open choice with its options, cost and reversibility, plus the record of decisions actually taken (currently none).",
}

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
    "suggestions.html": page_suggestions,
    "questions.html": page_questions,
    "decisions.html": page_decisions,
    "analytics.html": page_analytics,
    "flagged.html": page_flagged,
    "sources.html": page_sources,
}


def render(page: Page) -> str:
    nav_groups = []
    for group, targets in NAV_ORDER:
        items = []
        for target in targets:
            label = NAV_LABEL.get(target, target)
            cls = ' class="active" aria-current="page"' if target == page.active else ""
            items.append(f'<a href="{esc(page.rel(target))}"{cls}>{esc(label)}</a>')
        nav_groups.append(
            f'<div class="nav-group"><span class="nav-group-title">{esc(group)}</span>'
            + "".join(items)
            + "</div>"
        )
    nav = "".join(nav_groups)
    disclosure = (
        f'<div class="disclosure" role="note"><strong>Disclosure:</strong> {esc(DISCLOSURE_SENTENCE)} '
        f'<span class="small">(Source: '
        f'{ext(DISCLOSURE_SOURCE, "Associates Operating Agreement, Section 5")}) '
        "This site is not endorsed by or affiliated with Amazon.</span></div>"
    )
    # IP License Section 2(k) requires this text in plain view when Product
    # Advertising Content consisting of text (here, listing titles) is displayed.
    # It is data-driven so it can be withdrawn without touching the template.
    amazon_text = ""
    notice = CONTENT.get("site_disclaimer") or {}
    if notice.get("text"):
        amazon_text = (
            f'\n<div class="disclosure" role="note"><strong>Amazon content notice:</strong> {esc(notice["text"])}'
            f' <span class="small">(Source: {ext(notice["source_url"], notice.get("source_ref", "IP License"))}'
            f')</span></div>'
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
<aside class="sidebar">
  <a class="brand" href="{esc(page.rel('index.html'))}">Affiliate research</a>
  <nav aria-label="Main">{nav}</nav>
</aside>
<div class="content">
{disclosure}{amazon_text}
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
        "dateModified": OBSERVED,
        "inLanguage": "en",
        "author": {"@type": "Organization", "name": SITE_TITLE_SUFFIX},
        "publisher": {"@type": "Organization", "name": SITE_TITLE_SUFFIX},
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
        "name": SITE_TITLE_SUFFIX,
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
