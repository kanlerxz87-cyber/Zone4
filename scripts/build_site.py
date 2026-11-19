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

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_extras  # noqa: E402  (publication extras; same pipeline writes docs/)

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "docs"

DISCLOSURE_SENTENCE = "As an Amazon Associate I earn from qualifying purchases."
DISCLOSURE_SOURCE = "https://affiliate-program.amazon.com/help/operating/agreement"
SITE_TITLE_SUFFIX = "Zone4 - air fryer buying guides"

# ---------------------------------------------------------------- associates
# The owner-selected tracking ID (2026-11-17 brief) and the tagged Special Links
# published as outbound product hrefs (decisions D-01/D-14, recorded 2026-11-17).
# The ID's registration is confirmable only inside Associates Central (F-57);
# the destination of each Special Link was verified on 2026-11-17 (data/intent-links.json).
ASSOCIATES_DOC = json.loads((DATA / "associates.json").read_text(encoding="utf-8"))
TRACKING_ID = ASSOCIATES_DOC["tracking_id"]["value"]
SPECIAL_LINKS = {s["product_id"]: s["special_link_url"] for s in ASSOCIATES_DOC["special_links"]}


def tagged_url(url: str) -> str:
    """Append the tracking tag as a URL parameter unless the URL already carries it."""
    if f"tag={TRACKING_ID}" in url:
        return url
    return url + ("&" if "?" in url else "?") + f"tag={TRACKING_ID}"


SITE_DESCRIPTION = (
    "Spec-checked buying guides for three countertop air fryers: product records, sourced articles, "
    "and a receipt behind every number. What we cannot verify is flagged, not hidden."
)
# The front page leads with the shop, not the audit: its own marketing title and
# meta description, distinct from the dashboard label used in the navigation.
# No Amazon Mark appears in either (Participation Requirement 6(e)).
INDEX_TITLE_TAG = "Find the air fryer that fits your kitchen"
INDEX_DESCRIPTION = (
    "Compare three countertop air fryers on the numbers their listings actually state. A three-question "
    "chooser, eight sourced buying guides and a receipt behind every figure - no prices, ratings or guesses."
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
# The choose-a-path triage (added 2026-11-19, SG-36): the open decisions
# presented as three coherent orders. Presentations of the register, not
# recorded choices; the queue itself stays the source of truth.
DECISION_PATHS = DECISIONS_DOC.get("paths", {}).get("paths", [])
# The design brief: three specified visual directions, the anti-"AI slop"
# checklist, the organic-traffic topic programme and the headline options.
# Like the other registers it is a proposal surface, and every row in it cites
# the official source that constrains it.
DESIGN_DOC = load("design.json")
DIRECTIONS = DESIGN_DOC["directions"]
ANTI_SLOP = DESIGN_DOC["anti_slop"]
HEADLINE_OPTIONS = DESIGN_DOC["headline_options"]
TOPICS = DESIGN_DOC["topics"]
LAUNCH_PATH = DESIGN_DOC["launch_path"]
PROMPT_SLOTS = DESIGN_DOC["prompt_slots"]
OBSERVED = CONTENT["observed_date"]
# The date the three supplied links and the cited official policy pages were last
# re-read from their official sources. Kept separate from OBSERVED, which is the
# date of the product-page snapshot the records hold.
RECHECKED = CONTENT.get("rechecked_utc", OBSERVED)

SITE_URL = "https://kanlerxz87-cyber.github.io/Zone4/docs/"

NAV = [
    ("index.html", "Home", "Overview"),
    ("executive-summary.html", "Executive summary", "Overview"),
    ("products.html", "All products", "Overview"),
    ("guides/index.html", "Guides", "Overview"),
    ("categories/dual-basket-air-fryers.html", "Dual-basket air fryers", "Categories"),
    ("categories/single-basket-air-fryers.html", "Single-basket air fryers", "Categories"),
    ("categories/air-fryer-toaster-ovens.html", "Air-fry toaster ovens", "Categories"),
    ("categories/meat-thermometers.html", "Meat thermometers", "Categories"),
    ("marketing.html", "Marketing content", "Content"),
    ("automation.html", "Automation & tracking", "Research"),
    ("analysis.html", "Analysis & findings", "Research"),
    ("requirements.html", "Requirements", "Research"),
    ("decision-centre.html", "Decision centre", "Decide"),
    ("suggestions.html", "Suggestions", "Decide"),
    ("questions.html", "Open questions", "Decide"),
    ("information-gaps.html", "Information gaps", "Decide"),
    ("design.html", "Design brief", "Decide"),
    ("decisions.html", "Decision log", "Decide"),
    ("verification.html", "Verification log", "Governance"),
    ("links.html", "Product-intent record", "Governance"),
    ("measurement.html", "Measurement & ledger", "Governance"),
    ("policy-compliance.html", "Policy compliance", "Governance"),
    ("analytics.html", "Analytics", "Governance"),
    ("flagged.html", "Flagged for review", "Governance"),
    ("sources.html", "Sources", "Governance"),
]
NAV_LABEL = {target: label for target, label, _group in NAV}
# One flat navigation group keeps the storefront easy to scan. The same page
# directory is repeated in the footer for readers who reach the end of an article.
NAV_ORDER = [("Explore", [t for t, _label, _group in NAV])]

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
    # Added with decision D-46 (2026-11-19): the two submitted meat-thermometer listings.
    "P4": "meat-thermometers",
    "P5": "meat-thermometers",
}


def _category_product_name(key: str) -> str:
    """Short product name for a category tile: P1-P3 from products.json, P4-P5 from products-extra.json."""
    extra = json.loads((DATA / "products-extra.json").read_text(encoding="utf-8"))["products"]
    for p in list(PRODUCTS) + list(extra):
        if CATEGORY_BY_PRODUCT.get(p["id"]) == key:
            return p["name_short"]
    return ""
CATEGORY_TITLE = {t: l for t, l, _g in NAV if t.startswith("categories/")}
PRODUCT_BY_ID = {p["id"]: p for p in PRODUCTS}
# Canonical listing URLs, used by the chooser's plain-text routing table so every
# row of it links to the official page its figures were read from.
P1_URL = PRODUCT_BY_ID["P1"]["canonical_url"]
P2_URL = PRODUCT_BY_ID["P2"]["canonical_url"]
P3_URL = PRODUCT_BY_ID["P3"]["canonical_url"]
CATEGORY_PATH_URL = PRODUCT_BY_ID["P1"]["category_url"]
ARTICLES_HUB = "articles/index.html"


def article_path(a: dict) -> str:
    """docs-relative path for an article, taken from its own suggested slug."""
    return "articles/" + a["slug"].strip("/") + ".html"


def article_category(a: dict) -> str:
    return CATEGORY_BY_PRODUCT.get(a.get("product_id"), "")


def article_label(a: dict) -> str:
    if a.get("nav_label"):
        return a["nav_label"]
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
GUIDE_PATHS = []
for _g in build_extras.published_guides():  # held guides are not listed (see scripts/build_extras.py)
    GUIDE_PATHS.append("guides/" + _g["slug"] + ".html")
    NAV_LABEL["guides/" + _g["slug"] + ".html"] = _g["h1"]
NAV_ORDER[0] = ("Explore", NAV_ORDER[0][1] + GUIDE_PATHS + [ARTICLES_HUB] + [p for _a, p in ARTICLE_PATHS])


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


def link_rel(url: str, rel: str = "noopener noreferrer") -> str:
    """rel for an outbound link: Amazon product pages are always sponsored (2026-11-17)."""
    if ("amazon.com/dp/" in url or url.startswith("https://link.amazon/")) and "sponsored" not in rel.split():
        return "sponsored " + rel
    return rel


_SHORT_LINK_MAP: dict[str, dict] | None = None


def _short_link_targets() -> dict[str, dict]:
    """Submitted short link -> its product-intent record (data/intent-links.json)."""
    global _SHORT_LINK_MAP
    if _SHORT_LINK_MAP is None:
        data = json.loads((ROOT / "data" / "intent-links.json").read_text(encoding="utf-8"))
        _SHORT_LINK_MAP = {r["submitted_url"]: r for r in data["links"]}
    return _SHORT_LINK_MAP


def ext(url: str, text: str | None = None, extra: str = "", rel: str = "noopener noreferrer") -> str:
    if url.startswith("https://link.amazon/"):
        # 2026-11-19 (F-73): a supplied short link is never published as the outbound target.
        # Citations point to the official listing that the recorded product-intent record
        # names (intended ASIN, official_listing_url), and the short link stays visible as text.
        rec = _short_link_targets().get(url)
        if rec is not None:
            target = rec["official_listing_url"]
            label = f"{text or url} (opens to ASIN {rec['intended_asin']})"
            rel = link_rel(target, rel)
            return f'<a href="{esc(target)}" rel="{esc(rel)}"{extra}>{esc(label)}</a>'
        return f"<code>{esc(url)}</code>"
    rel = link_rel(url, rel)
    label = esc(text if text is not None else url)
    return f'<a href="{esc(url)}" rel="{esc(rel)}"{extra}>{label}</a>'


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
    # The published outbound product link is the tagged Special Link
    # https://www.amazon.com/dp/<ASIN>?tag=shopnow047c-20 (decisions D-01/D-14,
    # recorded 2026-11-17 under the owner's brief): the final destination URL
    # with the tag as its parameter (Participation Requirements 2(b)), no
    # shortener (6(v)-(w)). rel="sponsored" marks the affiliate link for search
    # engines (decision D-05, recorded 2026-11-16); the visible disclosure and
    # "(paid link)" label stay. The supplied short link stays recorded data in
    # data/intent-links.json; it is not judged valid or invalid (FLG-003 unresolved).
    url = SPECIAL_LINKS.get(p["id"], tagged_url(f"https://www.amazon.com/dp/{p['asin']}"))
    return ext(url, "Open Amazon link (paid link)",
               f' class="shop" data-track="click" data-track-target="{esc(url)}" data-track-asin="{esc(p["asin"])}"',
               rel="sponsored noopener noreferrer")


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
        "Competition: also-viewed ASINs", "Affiliate link (published Special Link; supplied short link, recorded)", "Flags",
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
            shop_link(p) + f'<div class="note">{esc(DISCLOSURE_SENTENCE)}</div>'
            + f'<div class="note mono">Supplied short link, recorded: {esc(p["short_link"])}</div>',
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
        sched = ext(SOURCES["S-SCHED"]["url"], "Commission schedule (sign-in)")
        fl = PRODUCT_FLAGS[p["id"]]
        items = [
            ("Listing title", p["name_listing"], "Verified", src, ""),
            ("ASIN", p["asin"], "Verified (from resolved URL)", src, "F-04"),
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
            ("Associates tag in link", "Tagged Special Link published (shopnow047c-20)", "Published; registration unverified", src, "F-57"),
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


def not_verified_block(current: Page) -> str:
    """What this article does not show and why (suggestion S-22, decision D-25).

    Every competitor hides these gaps. Publishing them pre-empts the reader's
    doubt and turns the site's biggest constraint into its most distinctive
    feature. Each line names the flag that explains it.
    """
    return (
        '<div class="unverified" role="note"><strong>What this article does not show, and why</strong>'
        '<ul>'
        '<li><strong>Prices</strong> \u2014 withheld site-wide until an approved API supplies them; the listing always '
        'carries the live number. ' + flag_chip(current, "F-02") + '</li>'
        '<li><strong>Star ratings and review counts</strong> \u2014 withheld for the same reason. ' + flag_chip(current, "F-02") + '</li>'
        '<li><strong>Per-product commission rate</strong> \u2014 blank: no official source maps these ASINs to a '
        'commission category. ' + flag_chip(current, "F-01") + '</li>'
        '<li><strong>Hands-on testing</strong> \u2014 none claimed; nobody on this project has cooked in these '
        'appliances. ' + href(current, "decisions.html#D-06", "Decision D-06") + '</li>'
        '</ul></div>'
    )


def where_next_block(current: Page, a: dict) -> str:
    """Standing internal-navigation block on every article (suggestion S-24,
    decision D-27). scripts/verify.py fails the build if an article omits it.
    """
    key = article_category(a)
    items = []
    if key:
        items.append(href(current, "categories/" + key + ".html",
                          CATEGORY_TITLE.get("categories/" + key + ".html", "The category record")))
    if a["id"] != "M-CMP":
        items.append(href(current, "articles/dual-basket-vs-single-basket-vs-toaster-oven-air-fryer.html",
                          "The three-format comparison"))
    if a["id"] != "M-BUY":
        items.append(href(current, "articles/air-fryer-buying-guide-2026.html", "The buying guide"))
    items.append(href(current, "index.html#chooser", "The three-question chooser"))
    items.append(href(current, ARTICLES_HUB, "All articles and the topic calendar"))
    return ('<nav class="wherenext" aria-label="Where next"><strong>Where next</strong><ul>'
            + "".join(f"<li>{x}</li>" for x in items) + "</ul></nav>")


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
                f'<a class="cite" href="{esc(url)}" rel="{esc(link_rel(url))}">{esc(fid)}</a>'
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
    cta_button = ext(tagged_url(cta["link_url"]), cta["link_label"], ' class="shop"', rel="sponsored noopener noreferrer")
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


def chooser_section(current: Page) -> str:
    """The three-question 'which one is for you' chooser (suggestion S-19,
    decision D-23 recorded 2026-11-16).

    Built only from values already published from the official listings; the
    routing logic is shown as a plain-text table so the answer is checkable
    without the script, and every row links to the listing it draws on.
    """
    rows = [
        ["Two dishes finishing at the same time is the weekly need",
         href(current, "articles/chefman-6-quart-dual-basket-air-fryer-oven.html", "The 6-quart dual basket"),
         ext(P1_URL, "2 independent 3-quart baskets; Sync Finish named in the title")],
        ["One big dish at a time, and the shallowest footprint you can get",
         href(current, "articles/chefman-8-quart-single-basket-air-fryer.html", "The 8-quart single basket"),
         ext(P3_URL, "8 quarts; 12.75\"D as listed - the shallowest of the three")],
        ["Feeding a crowd (or hosting), and the counter is deep",
         href(current, "articles/26qt-french-door-air-fryer-toaster-oven.html", "The 26QT French-door oven"),
         ext(P2_URL, "24.6 liters listed; 16.9\"D as listed - the largest and deepest")],
    ]
    fallback = table(["When the need is", "The format that answers it", "Listed figures behind the route (official)"],
                     rows, "chooser-fallback")
    return (
        '<section id="chooser"><h2>Which air fryer is for you? Three questions</h2>'
        '<p class="section-lead">Answer three questions and the chooser routes you to the format that fits - using only '
        'listed specifications, with the reasoning shown. It is editorial routing, not a market claim: every figure it '
        'uses is a sourced row on the product records.</p>'
        '<div class="chooser" id="chooser-form">'
        '<fieldset><legend>1. How many people are you cooking for?</legend>'
        '<label><input type="radio" name="cook-for" value="small"> One or two</label>'
        '<label><input type="radio" name="cook-for" value="mid" checked> Three or four</label>'
        '<label><input type="radio" name="cook-for" value="large"> Five or more, or you host</label></fieldset>'
        '<fieldset><legend>2. How much counter depth do you have? (measure front to back)</legend>'
        '<label><input type="radio" name="depth" value="shallow"> Under 13.5 inches</label>'
        '<label><input type="radio" name="depth" value="mid" checked> 13.5 to 15.5 inches</label>'
        '<label><input type="radio" name="depth" value="deep"> More than 15.5 inches</label></fieldset>'
        '<fieldset><legend>3. Do you want two different foods finishing at the same time?</legend>'
        '<label><input type="radio" name="sync" value="yes" checked> Yes, often</label>'
        '<label><input type="radio" name="sync" value="no"> No, one dish at a time is fine</label></fieldset>'
        '<button class="btn btn-primary" type="button" id="chooser-go">Show my match</button>'
        '</div>'
        '<div class="chooser-result" id="chooser-result" role="status" aria-live="polite"></div>'
        '<h3>The routing, in plain text</h3>'
        '<p class="small muted">The same logic the chooser runs, in a table you can check without scripts.</p>'
        + fallback
        + "</section>"
    )


def shop_section_hook(current: Page) -> str:
    """Products first on the landing page (see scripts/build_extras.py)."""
    return build_extras.shop_section(sys.modules[__name__], current)


def featured_section(current: Page) -> str:
    """The shop window: one lead guide, then the rest of the shelf.

    Leads with the reader's decision, not the site's checking process (anti-slop
    patterns AS-01, AS-02 and AS-08). The buying guide is the natural entry
    point; the format comparison and the three product articles follow.
    """
    buy = next((a for a in ARTICLES if a["id"] == "M-BUY"), ARTICLES[0])
    rest = [a for a in ARTICLES if a["id"] != buy["id"]]
    rest.sort(key=lambda a: {"Comparison": 0, "Product article": 1}.get(a["page_type"], 2))
    feature = (
        f'<a class="feature" href="{esc(current.rel(article_path(buy)))}">'
        f'<div class="feature-top"><span class="chip">Buying guide</span>'
        f'<span class="chip chip-quiet">Start here</span></div>'
        f'<div class="feature-title">{esc(buy["h1"])}</div>'
        f'<div class="feature-dek">{esc(buy["meta_description"])}</div>'
        f'<div class="feature-meta">{article_read_minutes(buy)} min read \u00b7 '
        f'{len(buy["facts"])} sourced facts \u00b7 observed {esc(OBSERVED)}</div>'
        f'<div class="feature-go">Read the guide \u2192</div></a>'
    )
    grid = "".join(article_card(current, a) for a in rest)
    return (
        '<section id="articles"><h2>Start here, then read deeper</h2>'
        '<p class="section-lead">Begin with the format-first buying guide, then compare the three formats or read the '
        'review for the one that fits your kitchen. Every figure in every guide is a row in a table that links back to '
        'the listing it was read from.</p>'
        f'<div class="feature-wrap">{feature}</div>'
        f'<div class="agrid">{grid}</div></section>'
    )


def product_comparison_table(current: Page) -> str:
    """A buyer-facing comparison on the fields a shopper actually decides on.

    Each row links the product to its official listing and carries the rel="sponsored"
    shop link. Prices, ratings and per-product commission stay off this table by rule
    (F-02, F-01); the full verified record lives on products.html. This is the shop
    window, not the audit.
    """
    best_for = {
        "P1": "Two dishes finishing at the same time",
        "P3": "One big dish, shallowest counter footprint",
        "P2": "Feeding a crowd on a deep counter",
    }
    rows = []
    for p in PRODUCTS:
        depth = esc(str(p["dimensions"]).split(" x ")[0])
        rows.append([
            ext(p["canonical_url"], p["name_short"]),
            esc(CATEGORY_TITLE.get("categories/" + CATEGORY_BY_PRODUCT[p["id"]] + ".html", p["subcategory"])),
            esc(p["capacity"]),
            depth,
            esc(best_for[p["id"]]),
            shop_link(p) + f'<div class="note">{esc(DISCLOSURE_SENTENCE)}</div>',
        ])
    return table(
        ["Product (source link)", "Format", "Listed capacity", "Listed depth", "Best for", "Shop"],
        rows, "comparison",
    )


def content_roadmap_section(current: Page) -> str:
    """The content roadmap: catchy, question-shaped titles the site is writing next.

    Built from data/design.json topics (decision D-17). A topic is marked Written
    when a published article carries it; otherwise it is Planned. Every row links
    the official listing the topic draws on, so a planned title is a promise backed
    by verified figures rather than filler (D-19: no trend claim without a dated
    official snapshot).
    """
    rows = []
    for t in TOPICS:
        pub = t.get("published_article")
        article = next((a for a in ARTICLES if a["id"] == pub), None) if pub else None
        if article:
            link = href(current, article_path(article), "Read it")
            status = '<span class="pill pill-ok">Written</span>'
        else:
            link = '<span class="muted">On the calendar</span>'
            wave = re.search(r"Wave (\d)", t.get("wave", ""))
            status = '<span class="pill pill-muted">Planned \u00b7 wave ' + (wave.group(1) if wave else "2") + "</span>"
        src = t["sources"][0]
        rows.append([
            esc(t.get("working_title", "")),
            esc(t.get("question_it_answers", "")),
            status,
            link,
            ext(src["url"], src.get("ref", "official listing")),
        ])
    return (
        '<section id="roadmap"><h2>What we are writing next</h2>'
        '<p class="section-lead">A content roadmap of question-shaped guides (decision D-17). Each title is a question a '
        'buyer actually types, and each is answerable from figures already verified against official listings - so a '
        'planned title is a promise, not filler. No popularity or trend claim is made (D-19); every row links the '
        'listing it draws on.</p>'
        + table(["Working title", "The reader's question", "Status", "Link", "The official facts it draws on"],
                rows, "roadmap")
        + "</section>"
    )


def transparency_band(current: Page) -> str:
    """The dashboard surfaces, kept reachable but out of the shop window.

    Every governance page is one click from here and from the footer, in a single
    group (the brief's "single navigation group"). The counts are derived from the
    data so they cannot drift from the registers they summarise.
    """
    recorded = sum(1 for d in DECISIONS if d["status"] == "Recorded")
    counts = (
        f'<div class="tcount"><span class="tcount-n">{len(PRODUCTS)}</span> verified products</div>'
        f'<div class="tcount"><span class="tcount-n">{len(ARTICLES)}</span> sourced guides</div>'
        f'<div class="tcount"><span class="tcount-n">0</span> prices or ratings published</div>'
        f'<div class="tcount"><span class="tcount-n">{recorded}</span> decisions recorded</div>'
    )
    links = [
        ("Verification log", "Every published value and the listing it was read from.", "verification.html"),
        ("Policy compliance", "The programme and FTC rules this site is checked against.", "policy-compliance.html"),
        ("Flagged for review", "Every irregularity and unverified item, with its source.", "flagged.html"),
        ("Sources", "Every source used, and whether it was actually read.", "sources.html"),
        ("Suggestions", "The costed change backlog, to choose from before anything ships.", "suggestions.html"),
        ("Open questions", "What must be answered before a change can be made.", "questions.html"),
        ("Decision log", "The choices recorded and the ones still open.", "decisions.html"),
        ("Analytics", "A local-only click log that starts at zero.", "analytics.html"),
    ]
    cards = "".join(
        f'<a class="tcard" href="{esc(current.rel(target))}"><div class="tcard-t">{esc(label)}</div>'
        f'<div class="tcard-s">{esc(blurb)}</div></a>'
        for label, blurb, target in links
    )
    withheld = (
        '<ul class="bullets">'
        '<li><strong>Prices and star ratings</strong> \u2014 withheld until an approved API supplies them '
        f'{flag_chip(current, "F-02")}</li>'
        '<li><strong>Per-product commission rate</strong> \u2014 blank: no official source maps these ASINs to a '
        f'commission category {flag_chip(current, "F-01")}</li>'
        '<li><strong>Hands-on testing</strong> \u2014 none claimed; nobody here has cooked in these appliances.</li>'
        '<li><strong>Traffic or earnings forecasts</strong> \u2014 none published; the programme makes no representation '
        'about either.</li>'
        "</ul>"
    )
    return (
        '<section id="transparency"><h2>The data behind the shop</h2>'
        '<p class="section-lead">This site publishes only what an official listing or policy page states. Everything below '
        'is the receipt: the verification log, the policy checks, the open flags and the decision surface. It is one click '
        'away and never in the way of the buying decision.</p>'
        f'<div class="tcounts">{counts}</div>'
        f'<div class="transgrid">{cards}</div>'
        '<h3>What this site deliberately does not publish</h3>'
        '<p class="section-lead">Stated here rather than buried, each naming the rule or flag behind it.</p>'
        + withheld
        + '</section>'
    )


def page_index(current: Page) -> str:
    """The front page as a shop, not an audit: hero, the shelf, categories, the
    chooser, a buyer comparison, the content roadmap, then the receipts.

    Governance apparatus (KPI counters, the decision queue, the full verified
    table) is moved out of the shop window into the transparency band and the
    footer, where it is still one click away. Implements suggestion S-21 (public
    magazine / research appendix split) and completes D-21's "amend" decision.
    """
    cat_tiles = "".join(
        f'<a class="tile" href="{esc(current.rel(target))}"><div class="tile-title">{esc(label)}</div>'
        f'<div class="tile-sub">{esc(_category_product_name(key))}</div>'
        f'<div class="tile-go">Open category \u2192</div></a>'
        for target, label, key in
        ((t, l, t[len("categories/"):-len(".html")]) for t, l, _g in NAV if t.startswith("categories/"))
    )
    buying_guide_path = next(
        (path for a, path in ARTICLE_PATHS if a["id"] == "M-BUY"), ARTICLE_PATHS[-1][1]
    )
    return (
        shop_section_hook(current)
        + '<div class="mhero">'
        '<span class="badge">A practical guide to three very different countertop formats \u00b7 every figure links to the listing it was read from</span>'
        "<h1>Find the air fryer that fits your counter \u2014 with every number fact-checked.</h1>"
        '<p class="lead">Three countertop air fryers \u2014 a dual-basket, a single-basket and a French-door toaster oven \u2014 '
        'compared on the numbers their makers actually list. Start with the chooser to find your format in under a '
        'minute, then read the guide that answers the question you arrived with.</p>'
        '<div class="mhero-actions">'
        '<a class="btn btn-primary" href="#chooser">Which one is for me?</a>'
        f'<a class="btn" href="{esc(current.rel(buying_guide_path))}">Read the buying guide</a>'
        f'<a class="btn" href="{esc(current.rel("articles/dual-basket-vs-single-basket-vs-toaster-oven-air-fryer.html"))}">Compare the formats</a>'
        '</div>'
        '<div class="trust"><span>Receipts on every figure</span><span>Gaps flagged, never hidden</span>'
        '<span>Written in plain sentences, checked line by line</span></div>'
        '</div>'
        + featured_section(current)
        + '<section><h2>Shop by category</h2><div class="tiles">' + cat_tiles + "</div></section>"
        + chooser_section(current)
        + '<section><h2>The three, side by side</h2>'
        '<p class="section-lead">The decision fields a shopper actually compares, taken straight from the listings. '
        'Prices, ratings and per-product commission stay off this table by rule \u2014 see the full verified record for '
        'what is withheld and why.</p>'
        + product_comparison_table(current)
        + f'<p class="small muted">Full verified record, with every withheld cell and its flag: '
        f'{href(current, "products.html", "All products")}.</p></section>'
        + content_roadmap_section(current)
        + transparency_band(current)
        + '<p class="muted small">'
        + "Product records observed " + esc(OBSERVED) + " (UTC); supplied links and cited policy pages re-read "
        + esc(RECHECKED) + " (UTC). Verification scope and method: "
        + href(current, "sources.html", "sources") + '.</p>'
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
    # The topic calendar (suggestion S-13, decision D-17): catchy, question-shaped
    # headlines, each written from the verified field set already in the repo.
    # Written rows link the article; every row links the official facts it draws on.
    cal_rows = [
        ["Air Fryer Sizes Explained: 6QT vs 8QT vs 26QT", "Written",
         href(current, "articles/air-fryer-sizes-explained-6qt-vs-8qt-vs-26qt.html", "Open the guide"),
         ext(P1_URL, "Listed capacities and dimensions of all three products")],
        ["Choosing an Air Fryer in 2026: The Format-First Method", "Written",
         href(current, "articles/air-fryer-buying-guide-2026.html", "Open the guide"),
         ext(CATEGORY_PATH_URL, "The shared category path and the three format records")],
        ["Holiday 2026: Gift an Air Fryer by the Counter They Have", "Written (seasonal)",
         href(current, "articles/holiday-2026-air-fryer-gift-guide.html", "Open the guide"),
         ext(P2_URL, "Format and footprint figures; price rule from the Programme Policies")],
        ["Hi-Fry, Sync Finish, Shake Reminder: An Air Fryer Feature Glossary", "Planned (wave 1)", "<span class=\"muted\">On the calendar</span>",
         ext(P3_URL, "Named features across the three listings")],
        ["The First-Air-Fryer Checklist: Seven Numbers to Check Before You Buy", "Written",
         href(current, "articles/first-air-fryer-checklist-seven-numbers.html", "Open the guide"),
         ext(P1_URL, "The verified field set: capacity, dimensions, range, presets")],
        ["Two Baskets or One? The Sync-Finish Question, Answered With Specs", "Planned (wave 2)", "<span class=\"muted\">On the calendar</span>",
         ext(P1_URL, "Dual-basket format fields (Sync Finish, 2 x 3QT)")],
        ["French Door Air Fryer Ovens: Big Capacity, Bigger Footprint?", "Planned (wave 2)", "<span class=\"muted\">On the calendar</span>",
         ext(P2_URL, "26QT oven capacity and dimensions")],
        ["Compact Countertop Cooking: The Small-Kitchen Air Fryer Format", "Planned (wave 2)", "<span class=\"muted\">On the calendar</span>",
         ext(P3_URL, "8-quart single-basket dimensions")],
        ["What \u201c24 Cooking Functions\u201d Really Means (and Why Titles Disagree)", "Planned (wave 2)", "<span class=\"muted\">On the calendar</span>",
         ext(P2_URL, "The two function-count readings recorded in F-26")],
    ]
    calendar = table(["Working title", "Status", "Link", "The verified facts it draws on (official)"], cal_rows, "calendar")
    return (
        hero("Articles", "Every article published on this site, grouped by the product format it covers. "
                         "The copy is written here, not republished from the listings, and each piece carries the "
                         "fact table it was written from.")
        + "".join(blocks)
        + '<section><h2>The topic calendar</h2>'
        '<p class="section-lead">Catchy, question-shaped topics are the plan (decision D-17); the difference from a content '
        'farm is that every one of them is answerable from figures already verified against official listings \u2014 so a '
        'planned title is a promise, not filler. No popularity or trend claim is made anywhere in the program (D-19).</p>'
        + calendar + "</section>"
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
        cites = ""
        for fid in para["fact_ids"]:
            fact = facts_by_id.get(fid)
            if not fact:
                continue
            for url in (fact.get("source_urls") or [fact.get("source_url")]):
                if url:
                    cites += f'<a class="cite" href="{esc(url)}" rel="{esc(link_rel(url))}">{esc(fid)}</a>'
        body_html.append(f'{sub}<p>{esc(para["text"])} <span class="cites">{cites}</span></p>')
    outline_html = "".join(
        f'<li><strong>{esc(o["h2"])}</strong> - {esc(o["purpose"])} '
        f'<span class="muted">(facts: {esc(", ".join(o["facts_used"]))})</span></li>'
        for o in a["outline"]
    )
    notes_html = "".join(f"<li>{esc(n)}</li>" for n in a["compliance_notes"])
    cta = a["cta"]
    cta_button = ext(tagged_url(cta["link_url"]), cta["link_label"], ' class="shop"', rel="sponsored noopener noreferrer")
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
        # The required disclosure sits directly under the headline, in byline
        # size, as well as at the page top and beside each link (decision D-32;
        # FTC Disclosures 101: disclosures are missed when they trail the post).
        + f'<p class="disclosure-inline"><strong>Disclosure:</strong> {esc(DISCLOSURE_SENTENCE)} '
          "This article reports listed specifications; no unit was tested, and the shop links are paid links.</p>"
        + not_verified_block(current)
        + "".join(body_html)
        + cta_html
        + where_next_block(current, a)
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
    # The editorial position statement (adopted from PR #69, 2026-11-19): six
    # promises that state only editorial choices, every factual claim behind
    # them already published with a source elsewhere on the site.
    editorial = CONTENT.get("editorial") or {}
    editorial_html = ""
    if editorial.get("promise"):
        editorial_html = (
            '<section><h2>What this publication promises</h2>'
            f'<p class="section-lead">{esc(editorial.get("note", ""))}</p>'
            '<ul class="bullets">'
            + "".join(f"<li>{esc(p)}</li>" for p in editorial["promise"])
            + "</ul></section>"
        )
    return (
        hero("Executive summary", es["headline"])
        + f'<section><h2>What the verification found</h2><ul class="bullets">{bullets}</ul></section>'
        + editorial_html
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


def counter_space_rows() -> list[list[str]]:
    """Capacity per inch of listed counter depth (suggestion S-23, decision D-26).

    Pure arithmetic on the published capacity and depth fields, computed here so
    it cannot drift from the table above it, and labelled as derived rather than
    as a listing claim. Units are kept as listed - no conversion is made - so the
    liters row is not a like-for-like ratio against the quart rows.
    """
    rows = []
    for p in PRODUCTS:
        dm = re.match(r'([\d.]+)"D', p.get("dimensions", ""))
        cm = re.match(r"([\d.]+)\s*(\w+)", p.get("capacity", ""))
        if not dm or not cm:
            continue
        depth = float(dm.group(1))
        cap = float(cm.group(1))
        unit = cm.group(2)
        per = cap / depth
        rows.append([
            ext(p["canonical_url"], p["name_short"]),
            f"{cap:g} {unit} (as listed)",
            f'{depth:g} in (as listed)',
            f"<strong>{per:.2f}</strong> {unit} per inch (derived)",
            f"{cap:g} {unit} &divide; {depth:g} in = {per:.2f}",
            ext(p["canonical_url"], "Official listing (capacity and dimensions)"),
        ])
    return rows


def page_products(current: Page) -> str:
    return (
        hero("All products",
         "One row per user-supplied link. Prices and ratings are withheld under the Associates policy. The "
         "commission category Amazon assigns to each ASIN is not confirmed by any official source, so the "
         "product-level rate cells are blank and only the official category-level Kitchen rate (4.50%) is "
         "quoted, with its source; all trend data remains unverified and blank.")
        + '<p><input id="filter" class="filter" type="search" placeholder="Filter rows (for example: Chefman, B0C…, Flag F-02)" aria-label="Filter table"></p>'
        + product_table(current, PRODUCTS)
        + build_extras.extra_products_section(sys.modules[__name__], current)
        + commission_category_note()
        + '<p class="small muted">Every row links to its Amazon product page as the source. Short links are the links you supplied. '
        'Also-viewed entries are identified by ASIN; the stored labels are the exact listing-title prefixes as read '
        'on the official pages (F-20), and the carousel changes between loads (F-29). The full title is on each linked page.</p>'
        + '<section><h2>Counter space per inch of depth (derived)</h2>'
        '<p class="section-lead">A question no listing answers: how much cooking capacity does each unit give back for the '
        'counter depth it takes? The arithmetic is shown in full, the inputs are the listed values above, and the result is '
        'labelled derived - it is this site&rsquo;s calculation, not a claim made by any listing (decision D-26).</p>'
        + table(["Product", "Capacity as listed", "Counter depth as listed", "Capacity per inch of depth",
                 "The arithmetic", "Source of the inputs (official)"], counter_space_rows(), "derived")
        + '<p class="note">Units are kept exactly as listed and never converted (F-10): the French-door oven&rsquo;s row is '
        'in liters, the other two in quarts, so read the ratio within each row rather than ranking the rows against each '
        'other. Depth is the first dimension as listed; the unit&rsquo;s own footprint also includes its width and height '
        'on the rows above.</p></section>'
    )


def page_category(current: Page, key: str) -> str:
    cat = CONTENT["categories"][key]
    prods = [p for p in PRODUCTS if p["id"] in cat["product_ids"]]
    headers = ["ID", "Product (source link)", "ASIN", "Brand (as shown)", "Capacity (as listed)",
               "Dimensions (as listed)", "Special features (as listed)",
               "Competition: also-viewed ASINs", "Affiliate link (published Special Link; supplied short link, recorded)", "Flags"]
    rows = []
    for p in prods:
        rows.append([
            esc(p["id"]), ext(p["canonical_url"], p["name_listing"]), esc(p["asin"]), esc(p["brand"]),
            esc(p["capacity"]), esc(p["dimensions"]), esc(p.get("special_feature", "")),
            competitor_links(p),
            shop_link(p) + f'<div class="note">{esc(DISCLOSURE_SENTENCE)}</div>'
            + f'<div class="note mono">Supplied short link, recorded: {esc(p["short_link"])}</div>',
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
        'and the outbound links carry the owner-selected tracking ID; what stays unverified is the tag\'s registration in Associates Central (F-57).</p>'
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
        '<p class="note">Since 2026-11-17 the tracked links are tagged Special Links: the final destination URL with the owner-selected tracking ID '
        '(' + esc(TRACKING_ID) + ') as its parameter. A click recorded here can therefore be reconciled against Associates reporting once the '
        'account connection exists; whether the tag is registered and active is confirmed only by the one-link-per-product test in Associates '
        'Central (' + href(current, "links.html", "product-intent record") + '; ' + flag_chip(current, "F-57") + ', ' + flag_chip(current, "F-58") + ').</p>'
        '</section>'
        '<section>'
        '<h2>Connecting real measurement</h2>'
        '<ul class="bullets">'
        f'<li>The owner-selected tracking ID ({esc(TRACKING_ID)}) is already on every outbound product link; confirm its registration in Associates Central with the {href(current, "links.html", "one-link-per-product test protocol")} before relying on any earnings (see {href(current, "flagged.html", "F-57")}).</li>'
        f'<li>The rollup ledger that turns local clicks into reported figures stays empty until an authorised first-party report exists (see {href(current, "measurement.html", "Measurement & ledger")}).</li>'
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
    open_count = sum(1 for s in SUGGESTIONS if s["status"].startswith(("Awaiting", "Needs")))
    done_count = sum(1 for s in SUGGESTIONS if s["status"].startswith(("Implemented", "Partly")))
    cards = [
        ("What this page is",
         "The change register. Every entry states the problem, the proposed change, what it costs, what it risks and the "
         "check that would prove it worked. A reviewer chooses here first; the Decision log records the choice; only then "
         "does anything ship."),
        (f"{done_count} shipped or staged",
         "Under the recorded decisions of 2026-11-16 and 2026-11-17. Each shipped item names the decision that released it; "
         "the fact rule never moved."),
        (f"{open_count} still need you",
         "These wait on a fact only the owner has - an Associates account, an API application, a budget or a lawyer. They "
         "are recorded as recommended, never as decided."),
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
    need_owner = [s for s in SUGGESTIONS if s["status"].startswith(("Awaiting", "Needs"))]
    shipped = [s for s in SUGGESTIONS if s["status"].startswith(("Implemented", "Partly"))]
    staged = [s for s in SUGGESTIONS if s["status"].startswith(("Decision recorded", "Not adopted", "Confirmed"))]
    blocked = [s for s in SUGGESTIONS if s["status"].startswith("Blocked")]

    def _ids(items):
        return " ".join(
            f'<a class="flag-chip" href="#{esc(s["id"])}">{esc(s["id"])}</a>' for s in items
        ) or "<span class=\"muted\">none</span>"

    path_html = (
        '<section><h2>The recommended path</h2>'
        '<p class="section-lead">If you only look at one thing on this page, look at this: what to do next, in order, and '
        'what has already been done on your behalf under the 2026-11-16 delegation.</p>'
        '<div class="pathgrid">'
        f'<div class="pathcard"><h3>1. Unlock these - only you can</h3><p>{_ids(need_owner)}</p>'
        '<p class="small">Each one waits on a fact no official page can supply: your Associates account (S-01, S-02), '
        'the commission category Amazon assigned (S-08) or a photography decision (S-18). Answer '
        + href(current, "questions.html", "Q-01 to Q-03") + ' and this column empties.</p></div>'
        f'<div class="pathcard"><h3>2. Shipped on 2026-11-16 - watch the checks</h3><p>{_ids(shipped)}</p>'
        '<p class="small">Voice, headline and topic work, the chooser, the disclosure placement, the mobile pass and the '
        'policy guardrails. Each has a \u201chow you would know it worked\u201d line in its card below.</p></div>'
        f'<div class="pathcard"><h3>3. Staged, deferred or refused</h3><p>{_ids(staged)} {_ids(blocked)}</p>'
        '<p class="small">Partly staged (Search Console, topic wave two, documentation), deferred with a reason (the '
        'magazine/research split), confirmed as standing guardrails (single retailer, no deals, manual research), or '
        'refused by policy (S-27).</p></div>'
        '</div></section>'
    )
    review_html = (
        '<section><h2>How to review this register</h2>'
        '<ol class="steps">'
        '<li><strong>Scan the table below</strong> in priority order (P1 first). The status chip shows what is already '
        'decided and what is not.</li>'
        '<li><strong>Open the card</strong> for the full case: the problem, the change, the cost, the risk and the check '
        'that would prove it worked.</li>'
        '<li><strong>Choose before anything changes.</strong> Record the option on the ' + href(current, "decisions.html", "Decision log") +
        ', or reply with the decision id and option key. Reversible choices are marked as such.</li>'
        '<li><strong>Implementation follows the record.</strong> Nothing here is built before its decision is logged; '
        'shipped items name the decision that released them.</li>'
        '</ol></section>'
    )
    return (
        '<header class="hero"><h1>Suggestions</h1>'
        '<p class="lead">Every change worth making to this site, costed and risk-assessed, with a decision recorded before '
        'anything is built. Choose the path here; the Decision log is the receipt.</p></header>'
        f'<section class="kpis kpis-stack">{card_html}</section>'
        + path_html + review_html
        + '<section><h2>At a glance</h2>'
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
        '<p class="note">Prepared by session arena/d8564cd0-zone4 (2026-11-15) and adopted as the working brief on '
        '2026-11-16 by decision D-20 (recorded under the owner\'s delegation); the design was implemented the same day '
        'under decisions D-18 and D-21. The longer, slot-filled final brief is '
        '<a href="https://github.com/kanlerxz87-cyber/Zone4/blob/main/DESIGN_PROMPT.md" rel="noopener noreferrer">DESIGN_PROMPT.md</a> '
        'in the repository. The compliance constraints it encodes live on the '
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
        '<section><h2>How the gaps get closed</h2>'
        '<p class="section-lead">A discovery plan, grouped by who can actually supply the answer. No amount of reading closes '
        'a gap that only a person or an account can.</p>'
        '<ul class="bullets">'
        '<li><strong>From your Associates account</strong> \u2014 the tag on the links (Q-01), API eligibility (Q-02) and, '
        'once signed in, the commission category behind Q-03. Five minutes in Associates Central answers three of the '
        'four gating gaps.</li>'
        '<li><strong>From Amazon&rsquo;s official pages, by re-reading</strong> \u2014 every \u201cKnown\u201d row above. The '
        're-read dates and the method are recorded in the sources registry; drift shows up as flags (F-29, F-44, F-47).</li>'
        '<li><strong>From a seller or the brand</strong> \u2014 the P2 function-count discrepancy (Q-15) and product intent '
        '(Q-09) need a question asked of a person, not a page read.</li>'
        '<li><strong>From counsel</strong> \u2014 automated collection (Q-07) and liability for listed specs (Q-08). Until '
        'then the engine stays offline and research stays manual (D-34).</li>'
        '<li><strong>From you, as decisions</strong> \u2014 audience, success measures, budget and consent (Q-10, Q-14, '
        'Q-16, Q-18). These are choices, not facts; the Decision log records each one when it is made.</li>'
        '</ul></section>'
        '<section><h2>Why this page exists</h2>'
        '<p>Three of these gaps decide whether this project can earn at all: the Associates tag (Q-01), API access for prices and '
        'ratings (Q-02), and the per-ASIN commission category (Q-03). Two were closed on 2026-11-16 by recorded decisions: the '
        'site is a specification tool with no testing claims (Q-06, decision D-06), and it grows on organic search only (Q-21, '
        'decision D-29). What remains decides whether it can honestly describe itself: who reviews the copy (Q-05) and whether '
        'automated collection needs a legal opinion (Q-07).</p>'
        f'<p class="small muted">Related: {href(current, "suggestions.html", "Suggestions")} for what each answer would unlock, '
        f'{href(current, "decisions.html", "Decision log")} for the choices already recorded '
        f'({sum(1 for d in DECISIONS if d["status"] == "Recorded")} recorded on 2026-11-16 under the owner&rsquo;s delegation).</p>'
        '</section>'
    )


def design_prompt_text() -> str:
    """Assemble the paste-ready design prompt from the same data the page shows.

    It is built from data/design.json rather than typed out here, so the
    brief on the site, DESIGN_PROMPT.md in the repository root and the
    register underneath them cannot drift apart. Slots stay bracketed until
    the decision that fills them is recorded; the slot table below the prompt
    names the decision for each one.
    """
    lines: list[str] = []
    add = lines.append
    add("Design a polished affiliate-marketing website for three countertop air fryers")
    add("whose every published figure is checked against an official source.")
    add("")
    add("GOAL. A site that earns organic search traffic and converts informed readers")
    add("through clearly disclosed affiliate links, and that reads like a human-edited")
    add("kitchen-technology publication. It must not read like generated filler.")
    add("")
    add("BRAND & DIRECTION. Brand [BRAND]. Visual direction [DIRECTION].")
    add("Editorial voice [VOICE]. Audience and market [AUDIENCE].")
    add("")
    add("DIRECTION OPTIONS (pick one; each is fully specified on the Design brief page):")
    for d in DIRECTIONS:
        add(f"  - {d['id']} {d['name']} ({d['decision_option']}): {d['one_line']}")
        add(f"    Display type: {d['type']['display']}")
        add(f"    Body type: {d['type']['body']}")
        add(f"    Palette: " + ", ".join(
            f"{k} {v}" for k, v in d["colour"].items() if k != "rule_text"))
        add(f"    Hero: {d['hero_pattern']}")
        add(f"    Disclosure: {d['disclosure_component']}")
        if d["blocked_by"]:
            add(f"    Constrained by flags: {', '.join(d['blocked_by'])}")
    add("")
    add("PRODUCTS. (1) A 6-quart dual-basket air fryer with two independent 3-quart")
    add("baskets and a listed Sync Finish feature. (2) A 26QT French-door air fryer")
    add("toaster oven whose listing states two different cooking-function counts.")
    add("(3) An 8-quart single-basket air fryer with a 450F high-heat option, part of a")
    add("6/8/9-quart variant family. Present them by format - dual-basket,")
    add("single-basket, toaster-oven - because format is the reader's real decision.")
    add("Every product fact must come from a cited listing field; never invent a")
    add("specification, a price, a rating or a review count.")
    add("")
    add("REQUIRED PAGES. A marketing landing page with a story-led hero; one category")
    add("page per format; a products-at-a-glance comparison table; five long-form")
    add("articles (three reviews, one format comparison, one buying guide); a topics hub")
    add("for the approved content calendar [TOPICS]; and a governance section")
    add("(verification log, policy compliance, flagged for review, sources, suggestions,")
    add("questions, decision log) designed with the same care as the marketing pages.")
    add("")
    add("HEADLINES. Use register [HEADLINES]. A headline names the reader's decision or a")
    add("number the page can prove. Never let a headline describe the site's own checking")
    add("process, and never repeat one construction across several articles - that is the")
    add("single clearest signal that a page was generated rather than written.")
    add("")
    add("TRAFFIC PROGRAMME. SEO-first and people-first. Build the approved topic calendar")
    add("[TOPICS] with question-shaped headlines and internal links from every topic to")
    add("the format pages and the reviews. Trendy language is allowed only under the")
    add("evidence rule [TREND_RULE], which requires a dated official snapshot behind every")
    add("popularity claim; otherwise write timeless format advice. Target")
    add("featured-snippet-shaped answers - size tables, checklists, glossaries - without")
    add("writing for machines.")
    add("")
    add("ANTI-PATTERNS. Do not ship any of these; each is a documented defect on the")
    add("current site:")
    for a in ANTI_SLOP:
        add(f"  - {a['id']}: {a['pattern']} -> {a['replacement']}")
    add("")
    add("COMPLIANCE HARD CONSTRAINTS (non-negotiable; they override any visual idea).")
    add("  - The affiliate disclosure sentence appears clearly at the top of every page,")
    add("    placed with the endorsement, never behind a click and never inside a group")
    add("    of links or hashtags.")
    add("  - Do not publish prices, star ratings or review counts unless the approved API")
    add("    route is in place.")
    add("  - Do not use marketplace trademarks in page titles, meta descriptions or")
    add("    target keywords.")
    add("  - Every table row that states a fact links to the official source it was read")
    add("    from. Anything unverified is left blank and visibly flagged, never inferred.")
    add("  - Make no hands-on performance claim without real testing, and claim no")
    add("    experience with a product nobody here has used.")
    add("  - No price tracking and no price alerts.")
    add("  - No traffic, click, conversion or revenue figure may appear anywhere: no")
    add("    official source supplies one for these products.")
    add("")
    add("DECISION WORKFLOW. Design the review workflow as a first-class part of the")
    add("product: a suggestions register where every change is proposed, costed and")
    add("risk-assessed, a questions register that separates what is known from what is")
    add("missing, and a decision queue in dependency order that the owner works through")
    add("before anything is implemented.")
    add("")
    add("OUTPUT. A complete design system (type scale, colour tokens, spacing, card and")
    add("table components, disclosure component, decision-queue component), page")
    add("templates for every required page, and two example article mockups built from")
    add("real verified facts. State which compliance constraint shaped each design")
    add("decision.")
    return "\n".join(lines)


def design_prompt_page_block(current: Page) -> str:
    """The prompt, with a copy button, and the slots that still need filling."""
    slot_source = "https://github.com/kanlerxz87-cyber/Zone4/blob/main/data/design.json"
    slot_rows = [
        [
            f"<code>{esc(s['slot'])}</code>",
            esc(s["filled_from"]),
            esc(s["current"]),
            ext(slot_source, "data/design.json, prompt_slots"),
        ]
        for s in PROMPT_SLOTS
    ]
    return (
        '<section><h2>The paste-ready prompt</h2>'
        '<p class="section-lead">Assembled from the tables above, so it cannot disagree with them. '
        'Copy it, fill the bracketed slots from your recorded decisions, and hand it to a designer '
        'or a design tool. The same text is written to <code>DESIGN_PROMPT.md</code> in the '
        'repository root, so the document and this page are the same brief.</p>'
        '<div class="promptblock">'
        '<div class="promptbar"><button type="button" id="copy-prompt" class="copybtn">Copy prompt</button>'
        '<span class="small muted" id="copy-status" role="status"></span></div>'
        f'<pre id="design-prompt">{esc(design_prompt_text())}</pre>'
        '</div>'
        + table(["Slot", "Filled from", "Current value", "Where the slot lives"],
                slot_rows, "prompt-slots")
        + '<p class="wide-note">Every slot is a decision, not a fact. Until one is recorded the prompt '
        'carries the bracket rather than a guess, because guessing at a brand name or a voice is '
        'exactly the kind of inventory this site refuses to publish.</p></section>'
    )


def page_design(current: Page) -> str:
    """The design brief: directions, anti-slop checklist, headlines, topics, prompt."""
    dir_rows = []
    for d in DIRECTIONS:
        dir_rows.append([
            f'<span id="{esc(d["id"])}"><strong>{esc(d["id"])}</strong></span>',
            esc(d["name"]) + f'<div class="small muted">{esc(d["decision_option"])}</div>',
            esc(d["one_line"]),
            esc(d["best_for"]),
            esc(d["effort"]),
            pill("Blocked" if d["blocked_by"] else "Clear", "bad" if d["blocked_by"] else "ok")
            + ("<br>" + " ".join(flag_chip(current, f) for f in d["blocked_by"]) if d["blocked_by"] else ""),
            "<br>".join(ext(s["url"], s["ref"]) for s in d["constrained_by"]),
        ])
    dir_cards = []
    for d in DIRECTIONS:
        tokens = "".join(
            f'<div class="opt"><div class="opt-key">{esc(k.replace("_", " "))}</div>'
            f'<div class="opt-body">{esc(v)}</div></div>'
            for k, v in d["type"].items()
        )
        swatches = "".join(
            f'<span class="swatch" style="background:{esc(v)}" title="{esc(k)}"></span>'
            for k, v in d["colour"].items() if k != "rule_text"
        )
        dir_cards.append(
            f'<section class="decision" id="spec-{esc(d["id"])}">'
            f'<div class="decision-head"><h2>{esc(d["id"])} &middot; {esc(d["name"])}</h2>'
            f'{pill(d["decision_option"], "muted")}</div>'
            f'<p class="section-lead">{esc(d["one_line"])}</p>'
            f'<div class="swatches">{swatches}</div>'
            f'<div class="optrow">{tokens}</div>'
            f'<p class="small"><strong>Grid.</strong> {esc(d["grid"])}</p>'
            f'<p class="small"><strong>Spacing.</strong> {esc(d["spacing"])}</p>'
            f'<p class="small"><strong>Hero.</strong> {esc(d["hero_pattern"])}</p>'
            f'<p class="small"><strong>Cards.</strong> {esc(d["card"])}</p>'
            f'<p class="small"><strong>Tables.</strong> {esc(d["table"])}</p>'
            f'<p class="small"><strong>Disclosure.</strong> {esc(d["disclosure_component"])}</p>'
            f'<p class="small"><strong>Imagery.</strong> {esc(d["imagery"])}</p>'
            f'<p class="rec"><strong>Risk.</strong> {esc(d["risk"])}</p>'
            f'<p class="small muted">Constrained by: '
            + " &middot; ".join(ext(s["url"], s["ref"]) for s in d["constrained_by"])
            + "</p></section>"
        )
    slop_rows = []
    for a in ANTI_SLOP:
        slop_rows.append([
            f'<span id="{esc(a["id"])}"><strong>{esc(a["id"])}</strong></span>',
            esc(a["pattern"]),
            esc(a["evidence"]),
            esc(a["why_it_reads_machine_generated"]),
            esc(a["replacement"]),
            esc(a["check"]),
            (" ".join(flag_chip(current, f) for f in a["flags"]) if a["flags"] else "")
            + "<br>" + "<br>".join(ext(s["url"], s["ref"]) for s in a["sources"]),
        ])
    head_rows = []
    for h in HEADLINE_OPTIONS:
        head_rows.append([
            f'<span id="{esc(h["id"])}"><strong>{esc(h["article"])}</strong></span>',
            esc(h["current_h1"]),
            esc(h["option_steady"]),
            esc(h["option_punchy"]),
            esc(h["note"]),
            "<br>".join(ext(s["url"], s["ref"]) for s in h["sources"]),
        ])
    topic_rows = []
    for t in TOPICS:
        topic_rows.append([
            f'<span id="{esc(t["id"])}"><strong>{esc(t["id"])}</strong></span>',
            esc(t["wave"]),
            esc(t["working_title"]),
            esc(t["question_it_answers"]),
            esc(t["intent"]),
            esc(t["built_from"]),
            esc(", ".join(t["fact_rows"])),
            esc(t["links_to"][0]) + ("<br>" + "<br>".join(esc(x) for x in t["links_to"][1:])
                                     if len(t["links_to"]) > 1 else ""),
            esc(t["evidence_note"]),
            esc(t["status"]),
            "<br>".join(ext(s["url"], s["ref"]) for s in t["sources"]),
        ])
    decision_by_id = {d["id"]: d for d in DECISIONS}
    path_rows = [
        [
            str(s["step"]),
            f'<a class="flag-chip" href="{esc(current.rel("decisions.html"))}#{esc(s["decision"])}">'
            f'{esc(s["decision"])}</a>',
            esc(s["choice"]),
            esc(s["what_it_unblocks"]),
            esc(s["cost"]),
            ext(decision_by_id[s["decision"]]["sources"][0]["url"],
                decision_by_id[s["decision"]]["sources"][0]["ref"]),
        ]
        for s in LAUNCH_PATH
    ]
    return (
        '<header class="hero"><h1>Design brief</h1>'
        '<p class="lead">Three visual directions specified far enough to build, the ten writing '
        'patterns that make this site read as machine output with a replacement for each, two '
        'finished headline options for every published article, an eight-topic organic-traffic '
        'programme, and the prompt that assembles all of it. Nothing on this page has been applied.</p>'
        '<p class="muted small">'
        f'{len(DIRECTIONS)} directions &middot; {len(ANTI_SLOP)} anti-patterns &middot; '
        f'{len(HEADLINE_OPTIONS)} headline rewrites &middot; {len(TOPICS)} topics &middot; '
        '0 traffic, revenue or search-volume figures published</p></header>'
        '<section class="kpis kpis-stack">'
        '<div class="kpi"><div class="kpi-value kpi-text">A proposal, not a changelog</div>'
        '<div class="kpi-label">Each section is bound to a decision row. When that decision is '
        'recorded, the change is made and the register is updated. Until then the site is '
        'unchanged, and that is deliberate.</div></div>'
        '<div class="kpi"><div class="kpi-value kpi-text">Two directions are free; one is narrowed</div>'
        '<div class="kpi-label">The bold deal-finder look is only viable in an evidence-only form, '
        'because the price, rating and price-tracking rules bar the tactics the look normally '
        'depends on. The page says so rather than letting a designer discover it.</div></div>'
        '<div class="kpi"><div class="kpi-value kpi-text">Every row constrained by an official source</div>'
        '<div class="kpi-label">Google Search Central for the writing standards, the FTC for '
        'disclosure placement, the Associates Operating Agreement and Program Policies for what '
        'may be said. No third-party SEO or marketing blog is cited for any rule or figure.</div></div>'
        '</section>'
        '<section><h2>The shortest credible path</h2>'
        '<p class="section-lead">The decision queue holds ' + str(len(DECISIONS)) + ' open choices. '
        'These five are ordered by what each one unblocks, so answering them in this order avoids '
        'doing the expensive one twice.</p>'
        + table(["Step", "Decision", "What to choose", "What it unblocks", "Cost",
                 "Source behind the step (official)"],
                path_rows, "launch-path")
        + '<p class="wide-note">A recommendation, not a rule. The full queue is on the '
        + href(current, "decisions.html", "Decision log") + ' page.</p></section>'
        '<section><h2>Three directions</h2>'
        '<p class="section-lead">These are the executable detail for the three options already in '
        'D-18. They add no options; they give each existing one the type stack, tokens and '
        'component rules a designer needs. Full specifications follow the table.</p>'
        + table(["ID", "Direction", "In one line", "Best for", "Effort", "Status",
                 "Constrained by (official)"], dir_rows, "design-directions")
        + "</section>"
        + "".join(dir_cards)
        + '<section><h2>What makes the current site read as machine output</h2>'
        '<p class="section-lead">Read line by line on 2026-11-16. Each row names the pattern, the '
        'evidence for it on this site, why it reads as generated, the replacement and the check '
        'that proves the fix. None of the ten adds a claim, so none needs a new source.</p>'
        + table(["ID", "Pattern", "Evidence on this site", "Why it reads as generated",
                 "Replacement", "How to check the fix", "Flags and sources (official)"],
                slop_rows, "anti-slop")
        + '</section>'
        '<section><h2>Headline options for the five published articles</h2>'
        '<p class="section-lead">Three of the five current headlines describe the site\'s own '
        'checking process rather than the reader\'s problem, and two of those differ only by the '
        'words &ldquo;two baskets&rdquo; and &ldquo;one basket&rdquo; (F-52). Two finished '
        'alternatives for each, so the choice is four fields per article and one rebuild.</p>'
        + table(["Article", "Current H1", "Option A: steady", "Option B: punchy", "Note",
                 "Sources (official)"], head_rows, "headline-options")
        + '<p class="wide-note">The punchy options make a claim only where the page can prove it. Two of '
        'them make a comparison claim, so they wait on D-12 letting the comparison page conclude.</p>'
        '</section>'
        '<section><h2>The organic-traffic topic programme</h2>'
        '<p class="section-lead">Eight topics, each with the question it answers, the intent behind '
        'it, the verified fact rows it is built from and the pages it must link to. No row carries a '
        'search-volume, traffic or revenue estimate: no official source supplies one (F-15), and '
        'the Operating Agreement makes no representation about the traffic any site can expect.</p>'
        + table(["ID", "Wave", "Working title", "Question it answers", "Intent",
                 "Built from", "Fact rows", "Links to", "Evidence note", "Status",
                 "Sources (official)"], topic_rows, "topics")
        + '<p class="wide-note">Google\'s helpful-content guidance lists &ldquo;writing about things '
        'simply because they seem trending&rdquo; among the warning signs of search-engine-first '
        'content, so every topic here is one a buyer of these three formats actually asks and is '
        'answerable from a field already verified. That tension is recorded as F-51 and decided by '
        'D-17 and D-19.</p></section>'
        + design_prompt_page_block(current)
        + '<p class="small muted">Related: '
        + href(current, "suggestions.html", "Suggestions")
        + ' for the costed backlog, '
        + href(current, "questions.html", "Open questions")
        + ' for what is still unknown, '
        + href(current, "decisions.html", "Decision log")
        + ' for the choices, and '
        + href(current, "flagged.html", "Flagged for review")
        + ' for the defects this page records.</p>'
    )


def decision_dependency_rows(current: Page) -> list[list[str]]:
    """Order the decision queue by what each choice unblocks.

    The dependency is derived, not authored: two decisions are linked when they
    share a question in the register, so the order falls out of data that
    already exists and cannot be forgotten in one place. Decisions attached to
    a P1 suggestion sort first, then by how many other decisions they touch.
    """
    by_id = {d["id"]: d for d in DECISIONS}
    p1_decisions = {s["decision"] for s in SUGGESTIONS if s["priority"].startswith("P1")}
    question_to_decisions: dict[str, list[str]] = {}
    for d in DECISIONS:
        for qid in [x.strip() for x in (d.get("linked_question") or "").split(",") if x.strip()]:
            question_to_decisions.setdefault(qid, []).append(d["id"])
    touches: dict[str, set[str]] = {}
    for d in DECISIONS:
        related: set[str] = set()
        for qid in [x.strip() for x in (d.get("linked_question") or "").split(",") if x.strip()]:
            related.update(x for x in question_to_decisions.get(qid, []) if x != d["id"])
        touches[d["id"]] = related
    # Only the open ones belong in a queue: a recorded decision is not waiting
    # on anything, and listing it would make the page's own KPI (13 waiting,
    # 26 recorded) disagree with the table beneath it.
    open_only = [d for d in DECISIONS if not d["status"].lower().startswith("recorded")]
    ordered = sorted(
        open_only,
        key=lambda d: (
            0 if d["id"] in p1_decisions else 1,
            -len(touches[d["id"]]),
            d["id"],
        ),
    )
    rows = []
    for n, d in enumerate(ordered, start=1):
        related = sorted(touches[d["id"]])
        rows.append([
            str(n),
            f'<a class="flag-chip" href="#{esc(d["id"])}">{esc(d["id"])}</a>',
            esc(d["question"]),
            " ".join(
                f'<a class="flag-chip" href="#{esc(r)}">{esc(r)}</a>' for r in related
            ) if related else '<span class="muted">Unblocks nothing else directly</span>',
            " ".join(
                f'<a class="flag-chip" href="{esc(current.rel("questions.html"))}#{esc(x.strip())}">'
                f'{esc(x.strip())}</a>'
                for x in (d.get("linked_question") or "").split(",") if x.strip()
            ) or '<span class="muted">&mdash;</span>',
            pill("P1 gate", "bad") if d["id"] in p1_decisions else pill("Open", "warn"),
            ext(d["sources"][0]["url"], d["sources"][0]["ref"]),
        ])
    return rows


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
            + (f'<p class="recorded"><strong>Recorded {esc(d.get("recorded_date_utc", ""))}.</strong> '
               f'{esc(d.get("recorded_choice", ""))}</p>'
               if d["status"] == "Recorded" and d.get("recorded_choice") else "")
            + f'<p class="rec"><strong>Recommendation.</strong> {esc(d["recommendation"])}</p>'
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
        '<p class="small muted">Pick an option and it is recorded in the log at the bottom of this page, with the date. The '
        'recommendation is an argument, not a decision, and it is labelled as one. Decisions dated 2026-11-16 were recorded '
        'under the owner&rsquo;s written delegation for this session ("no manual input... work on your own"); they are '
        'reversible, and each log entry says so.</p>'
        + '<section><h2>Suggested order, and the shortest credible path</h2>'
        '<p class="section-lead">The ' + str(len([d for d in DECISIONS if not d["status"].lower().startswith("recorded")]))
        + ' decisions still open, ordered by what each choice unblocks, so working top-down avoids doing the expensive '
        'step twice. The order is derived, not authored: two decisions are linked when they share a question in the '
        'register, and a decision attached to a P1 suggestion sorts first. The recorded ones are in the log below, '
        'not in this queue.</p>'
        + table(["Order", "Decision", "Question", "Also unblocks", "Gated by", "Weight",
                 "Primary source (official)"],
                decision_dependency_rows(current), "decision-order")
        + '<p class="wide-note">The steps above are set out on the '
        + href(current, "design.html", "Design brief")
        + ' page. The full queue, in the order it was written, follows.</p></section>'
        + "".join(blocks)
        + '<section><h2>Recorded decisions</h2>'
        + table(["Date (UTC)", "Decision", "Choice", "Recorded by", "Evidence", "Where it is recorded"],
                log_rows, "decision-log")
        + f'<p class="note">{sum(1 for d in DECISIONS if d["status"] == "Recorded")} decisions are recorded and '
          f'{sum(1 for d in DECISIONS if d["status"].startswith("Open"))} remain open. The open ones are not waiting on '
          'more research: each needs a fact only the owner has - an Associates account, a tracking ID, a budget, a seller '
          'or a lawyer - so they are listed with exactly what they block rather than guessed at. Reopening any recorded '
          'decision is one entry in this log.</p></section>'
    )


def page_decision_centre(current: Page) -> str:
    """The review-before-you-build hub: suggestions, questions, decisions, flags.

    Adopted 2026-11-19 from the editorial pass of stale PR #69
    (arena/6554fead-zone4, taken over under the 60-minute handoff rule) and
    re-based on this builder's template and the live registers: the hub counts
    and the gating-decision rows are derived from the data, so the page cannot
    drift from the registers it summarises. This is the page the owner brief
    asks for - a place to review the suggestions and choose a path before
    anything is implemented.

    The choose-a-path triage (SG-36, 2026-11-19) renders the open decisions as
    three coherent orders from `data/decisions.json`'s `paths` key. It is a
    presentation of the register, not a recorded choice: the build refuses a
    path step that names an unknown or no-longer-open decision, so the section
    cannot claim a decision that the queue no longer carries as open.
    """
    open_decisions = [d for d in DECISIONS if d["status"].startswith("Open")]
    hub = [
        (str(len(SUGGESTIONS)), "Suggestions", "Every change worth making, costed and risk-assessed. Read this first: it is the menu.",
         "suggestions.html", "Open the register &rarr;"),
        (str(len(QUESTIONS)), "Open questions", "What is known, what is missing, how the gap is closed and who can close it. Read this second: some menu items cannot be ordered yet.",
         "questions.html", "Open the questions &rarr;"),
        (str(len(open_decisions)), "Decisions waiting", f"{len(DECISIONS) - len(open_decisions)} recorded, {len(open_decisions)} open. The choice itself, with its options, cost and reversibility. Nothing is acted on until it appears here.",
         "decisions.html", "Open the queue &rarr;"),
        (str(len(FLAGS)), "Flagged for review", "Defects, gaps and unverified items found while building the site, each with its source and the action needed.",
         "flagged.html", "Open the flag register &rarr;"),
    ]
    hub_html = "".join(
        f'<a class="hub-card" href="{esc(current.rel(target))}"><div class="hub-count">{esc(count)}</div>'
        f'<div class="hub-title">{esc(title)}</div><div class="hub-body">{esc(body)}</div>'
        f'<div class="hub-go">{go}</div></a>'
        for count, title, body, target, go in hub
    )
    steps = [
        ("Read the suggestions, P1 first",
         "Each carries the problem, the proposal, the cost, the risk and the check that would prove it worked. P3 items are housekeeping and can wait."),
        ("Answer the questions each one depends on",
         "A suggestion that needs a Partner Tag cannot be built before the tag exists. The questions page names the owner of each answer, so nothing sits in the wrong queue."),
        ("Record the choice in the decision log",
         "Options, cost and reversibility are already written out. Recording a choice is a one-line entry, and the site keeps behaving exactly as it does now until it is recorded."),
        ("Only then does anything change",
         "Changes ship through a pull request that must pass the build, the verifier and the QA audit: links, per-row sourcing, disclosure, no prices or ratings, no Amazon marks in titles. A broken build cannot be published."),
    ]
    path_html = "".join(
        f'<div class="path-item"><div class="path-num"></div><div><h3>{esc(h)}</h3><p>{esc(p)}</p></div></div>'
        for h, p in steps
    )
    # The three open decisions whose answers unlock the largest visible groups.
    # Rendered from the register (question, recommendation, unlocks, source), so
    # the table cannot quote a decision the register no longer carries.
    gate_ids = ("D-02", "D-16", "D-42")
    gate_rows = []
    by_id = {d["id"]: d for d in DECISIONS}
    for gid in gate_ids:
        d = by_id.get(gid)
        if not d:
            continue
        unlocks = " ".join(
            f'<a class="flag-chip" href="{esc(current.rel("suggestions.html"))}#{esc(s)}">{esc(s)}</a>'
            for s in d.get("linked_suggestions") or []
        ) or '<span class="muted">none</span>'
        src = d["sources"][0] if d.get("sources") else None
        gate_rows.append([
            f'<a href="{esc(current.rel("decisions.html"))}#{esc(d["id"])}"><strong>{esc(d["id"])}</strong></a> &middot; {esc(d["question"])}',
            esc(d.get("recommendation") or ""),
            unlocks,
            ext(src["url"], src.get("ref", "official source")) if src else "",
        ])
    recorded_tag = next((d for d in DECISIONS if d["id"] == "D-01"), None)
    tag_note = (
        f'The outbound-tagging decision ({href(current, "decisions.html#D-01", "D-01")}/{href(current, "decisions.html#D-14", "D-14")}) is already '
        f'recorded: the published product links are the tagged Special Links. What remains on that thread is account-side confirmation '
        f'({flag_chip(current, "F-57")}) and the one-link-per-product test, not a design choice.'
        if recorded_tag else ""
    )
    # The choose-a-path triage (SG-36, 2026-11-19): the open decisions presented
    # as three coherent orders, rendered from data/decisions.json's paths key.
    # Guard: a path may only present decisions the register still carries as
    # open, so the section cannot outlive the queue it summarises.
    dec_by_id = {d["id"]: d for d in DECISIONS}
    path_sections = []
    for path in DECISION_PATHS:
        path_rows = []
        for n, step in enumerate(path["steps"], start=1):
            did = step["decision"]
            d = dec_by_id.get(did)
            if d is None:
                raise SystemExit(f"decision-centre paths: {path['id']} names unknown decision {did}")
            if not d["status"].startswith("Open"):
                raise SystemExit(
                    f"decision-centre paths: {path['id']} names decision {did}, "
                    f"whose status is now '{d['status']}' - update the path or remove the step"
                )
            src = d["sources"][0] if d.get("sources") else None
            path_rows.append([
                str(n),
                f'<a href="{esc(current.rel("decisions.html"))}#{esc(did)}"><strong>{esc(did)}</strong></a> &middot; {esc(d["question"])}',
                esc(step["why"]),
                esc(step["unblocks"]),
                ext(src["url"], src.get("ref", "official source")) if src else "",
            ])
        path_sections.append(
            f'<h3>{esc(path["name"])}</h3>'
            f'<p class="section-lead">{esc(path["one_line"])} <em>Best for: {esc(path["best_for"])}</em></p>'
            + table(["Step", "Decision (open)", "Why it comes at this point", "What it unblocks", "Official source"],
                    path_rows, "compact")
            + f'<p class="small muted">Deliberately delays: {esc(path["delays"])} &middot; Cost: {esc(path["cost_note"])}</p>'
        )
    paths_html = (
        '<section id="choose-a-path"><h2>Choose a path: the open decisions as three coherent orders</h2>'
        '<p class="section-lead">Three ways to work through the same queue, each a recommendation assembled from the register at build time - '
        'not a recorded choice. Every step names a decision that is open right now (the build refuses to render one that is not), and each row '
        'carries the decision\'s own official source. Pick one path and answer it top to bottom, or ignore all three and work the numeric queue '
        f'on the {href(current, "decisions.html", "Decision log")}; the queue, not this section, is the source of truth.</p>'
        + "".join(path_sections)
        + f'<p class="small muted">Derived from suggestion {href(current, "suggestions.html#SG-36", "SG-36")} under recorded decision '
        f'{href(current, "decisions.html#D-38", "D-38")} (option A: publish the queue in dependency order). The paths present strategy, '
        'not outcomes: nothing changes on the site because a path is read, and no step is treated as decided until it is recorded on the Decision log.</p></section>'
    )
    return (
        hero("Decision centre",
             "One place to review what could change, see what is still unknown, and choose a path before anything is implemented. "
             "Nothing on this site is actioned by a suggestion: a change happens only after a decision is recorded and a checked "
             "build replaces the page.")
        + f'<div class="hub-grid">{hub_html}</div>'
        + '<section><h2>The order to work in</h2>'
          '<p class="section-lead">Four steps, in this order. Skipping to step four is what produces sites that look finished and cannot earn.</p>'
          f'<div class="path">{path_html}</div></section>'
        + '<section><h2>The open decisions that gate the rest</h2>'
          '<p class="section-lead">Each of these blocks a group of suggestions, and each needs an answer only the owner or Amazon can give. '
          f'The full list of {len(open_decisions)} open decisions is on the {href(current, "decisions.html", "Decision log")}.</p>'
          + table(["Decision", "Recommendation (an argument, not a decision)", "Unlocks", "Official source"], gate_rows, "compact")
          + f'<p class="small muted">{tag_note}</p></section>'
        + paths_html
        + '<section><h2>What this site does with an answer</h2>'
          f'<p>A recorded decision becomes a suggestion marked for implementation, then a pull request, then a build that has to pass the same '
          f'gates as every page here: every table row sourced to an official page, the Associates disclosure on every page, no price or star rating, '
          f'no Amazon mark in a title or a target keyword, and no unverified value published. The gates are listed on '
          f'{href(current, "policy-compliance.html", "policy compliance")} and enforced by <code>scripts/verify.py</code> and '
          f'<code>qa/audit_site.py</code>.</p>'
          f'<p class="small muted">The full audit trail of this project, including the sessions that built it, is in <code>COORDINATION.md</code> in '
          f'the repository. Every flag published on the site names the source it was checked against; the summaries of what is still missing are on '
          f'{href(current, "information-gaps.html", "Information gaps")}.</p></section>'
    )


def page_information_gaps(current: Page) -> str:
    """What this project can prove, what it cannot, and who can close each gap.

    Adopted 2026-11-19 from stale PR #69 (arena/6554fead-zone4) and re-based on
    this builder's template. Every row pulls its question text, flag chip and
    official source from the registers at build time, so a corrected register
    row corrects this page with it. This is the brief's "clear list of
    questions, information and answers that need to be addressed before any
    decision can be made".
    """
    q_by = {q["id"]: q for q in QUESTIONS}
    # (what is missing, why it matters and what would close it, question id, flag id)
    gaps = [
        ("A confirmed Associates Partner Tag on the published links",
         "Until the tag is confirmed active in the account, a click cannot be attributed and no commission can be earned. Only the account holder can supply it.",
         "Q-01", "F-03"),
        ("Whether shopnow047c-20 is a registered, active tag",
         "The ID arrived as owner input, not as a value any official page states. Associates Central is the only place that answers yes or no (S-39's test protocol is ready).",
         "Q-50", "F-57"),
        ("Prices and star ratings on the public pages",
         "Permitted only through Amazon-served links or approved API data. Amazon's stated prerequisite for the API is 10 qualifying sales in 30 days, so this is downstream of the tag.",
         "Q-02", "F-02"),
        ("The per-ASIN commission category",
         "The public table gives category rates; no public source maps an ASIN to a band. It is visible in Associates Central to the account holder.",
         "Q-03", "F-01"),
        ("Search demand for each candidate topic",
         "No official source supplies a search-volume figure, so topic choice is editorial until Search Console reports measured queries (SG-29).",
         "Q-40", "F-15"),
        ("Product photography",
         "The only honest routes are the owner's own photographs or images served through an approved Amazon tool. Neither exists yet (D-22).",
         "Q-20", "F-31"),
        ("Search Console verification and measured queries",
         "No account has verified the property, so no impression or click data exists to choose the next topic from (D-42, S-40).",
         "Q-48", "F-61"),
        ("A hosted first-party analytics endpoint",
         "The endpoint code (analytics-endpoint/) and the five defined events exist in the repository, but nothing hosts them, so no event stream flows and the campaign ledger stays empty by rule (D-41, D-43).",
         "Q-46", "F-59"),
    ]
    gap_rows = []
    for missing, why, qid, fid in gaps:
        q = q_by.get(qid)
        src = q["sources"][0] if q and q.get("sources") else None
        gap_rows.append([
            esc(missing),
            esc(why),
            f'<a href="{esc(current.rel("questions.html"))}#{esc(qid)}"><strong>{esc(qid)}</strong></a>',
            flag_chip(current, fid),
            ext(src["url"], src.get("ref", "official source")) if src else "",
        ])
    open_questions = [q for q in QUESTIONS if q["kind"] != "Known"]
    owner_qs = [q for q in open_questions if q["answerable_by"].startswith("The site owner")]
    other_qs = [q for q in open_questions if not q["answerable_by"].startswith("The site owner")]

    def qlist(items):
        return "".join(
            f'<li><strong><a href="{esc(current.rel("questions.html"))}#{esc(q["id"])}">{esc(q["id"])}</strong></a> '
            f'{esc(q["question"])} <span class="muted small">&mdash; {esc(q["answerable_by"])} &middot; {esc(q["kind"])}</span></li>'
            for q in items
        )
    return (
        hero("Information gaps",
             "What this project can already prove, what it still cannot, and exactly who can close each gap. Nothing on this list is closed by "
             "inference, and no placeholder value stands in for a missing answer.")
        + '<section><h2>What this project can already prove</h2>'
          '<p class="section-lead">Three supplied links resolved to three verified air-fryer listings, and every value published about them was read '
          'from an official page and is linked to it in the same row. The proof lives in the '
          f'{href(current, "verification.html", "verification log")} and the {href(current, "products.html", "product records")}; the '
          f'{href(current, "flagged.html", "Flagged for Review")} page lists everything that could not be confirmed.</p></section>'
        + '<section><h2>What we do not have, and what would close it</h2>'
          '<p class="section-lead">A gap stays a gap until a named party answers it. Each row links the question that tracks it, the flag that '
          'publishes it, and the official rule the gap turns on.</p>'
          + table(["Missing", "Why it matters, and what would close it", "Question", "Flag", "Official rule the gap turns on"],
                  gap_rows, "compact")
          + "</section>"
        + f'<section><h2>The {len(open_questions)} questions that are not answered yet</h2>'
          f'<p class="section-lead">{len(owner_qs)} of them need an answer only the site owner can give; {len(other_qs)} are discoverable but have '
          f'not been discovered from an official source yet. The full register, with each row\'s "what is already known" and "how the missing piece '
          f'is discovered" columns, is on {href(current, "questions.html", "Open questions")}.</p>'
          f'<h3>Answerable by the site owner</h3><ol>{qlist(owner_qs)}</ol>'
          + (f'<h3>Discoverable, not yet discovered</h3><ol>{qlist(other_qs)}</ol>' if other_qs else "")
          + f'<p class="small muted">The choices that follow from those answers are on {href(current, "decisions.html", "Decision log")}; the menu '
            f'they unlock is on {href(current, "suggestions.html", "Suggestions")}; the review order is '
            f'{href(current, "decision-centre.html", "Decision centre")}.</p></section>'
    )


# Every page states what it contains, in its own words. Google's snippet
# guidance asks for a unique description per page; the article pages already
# carried their own, and these cover the rest. The build fails if two pages
# share one (see scripts/verify.py), so this cannot silently regress.
PAGE_DESCRIPTIONS = {
    "index.html": INDEX_DESCRIPTION,
    "executive-summary.html": f"What the verification found, the {sum(1 for d in DECISIONS if d['status'].startswith('Open'))} decisions that still need the owner and the {sum(1 for d in DECISIONS if d['status'] == 'Recorded')} recorded on 2026-11-16, and what is deliberately not built. Each statement links to the official source behind it.",
    "products.html": "Three air-fryer product records side by side: brand, category path, listed capacity, dimensions and also-viewed competitors, with prices, ratings and commission cells deliberately blank.",
    "categories/dual-basket-air-fryers.html": "The dual-basket air-fryer category: the Chefman 6 quart record, its listed specifications, the competing ASINs shown beside it on the listing, and the article written from those facts.",
    "categories/single-basket-air-fryers.html": "The single-basket air-fryer category: the Chefman 8 quart record, its listed presets and footprint, the size variants on the same page, and the article written from those facts.",
    "categories/air-fryer-toaster-ovens.html": "The air-fry toaster oven category: the Emeril Lagasse 26 quart record, its listed functions and footprint, and the two specification inconsistencies disclosed rather than resolved.",
    "marketing.html": f"The full marketing content kit on one page: {len(ARTICLES)} articles - product spec checks, a format comparison and buying guides - each with the fact table it was written from and a disclosure-carrying call to action.",
    "automation.html": "The affiliate pipeline stage by stage, with the status of each stage, the official rule that constrains it, and every click, conversion and revenue metric left blank because nothing is connected.",
    "analysis.html": "" + str(len(CONTENT["analysis"])) + " findings on the three products and the programme rules, each stating its basis, its confidence, and the official source an opinion would have to be checked against.",
    "requirements.html": f"All {len(REQUIREMENTS)} items in the project brief, one row each, with what the site actually delivers, what blocks it and the official source that governs the status.",
    "verification.html": "A field-by-field verification log for all three products: every published value, the official page it was read from, and a flag wherever it could not be confirmed.",
    "policy-compliance.html": f"{len(RULES)} Associates-programme and FTC requirements checked against this site, each linked to the official section it comes from and to the way the site complies.",
    "analytics.html": "A first-party click log that lives only in your browser and starts at zero. No network call, no estimate, and no attributed figure until Associates reporting is connected.",
    "flagged.html": "Every irregularity and unverified item found while building this site, each with its severity, the source links behind it, and the action needed from the owner.",
    "sources.html": "Every source used, whether it was actually read, and what it was used for. Unread sources are marked and nothing is inferred from them.",
    "articles/index.html": "Every article on the site grouped by product format, plus the topic calendar: catchy planned titles, each answerable from already-verified figures, with every fact row linked to its source.",
    "suggestions.html": f"{len(SUGGESTIONS)} changes worth making to this site, costed and risk-assessed, each tied to its decision and to the official rule that constrains it: what shipped on 2026-11-16, what waits on the owner, and in which order.",
    "questions.html": f"{len(QUESTIONS)} questions that must be answered before any change can reasonably be made: what is already known, what is missing, and who can supply it.",
    "decision-centre.html": f"The review-before-you-build hub: the {len(SUGGESTIONS)} suggestions, {len(QUESTIONS)} questions, {sum(1 for d in DECISIONS if d['status'].startswith('Open'))} open decisions and {len(FLAGS)} flags in one place, with the order to work in, three ready-weighed paths through the open decisions, and what happens to an answer.",
    "information-gaps.html": f"What this project can already prove about the three air fryers, the {len([q for q in QUESTIONS if q['kind'] != 'Known'])} questions that are not answered yet, and the named party who can close each gap.",
    "design.html": f"The design brief for this site: {len(DIRECTIONS)} specified visual directions, the {len(ANTI_SLOP)} writing patterns that make it read as machine output with a replacement for each, two headline options for every published article, {len(TOPICS)} organic-traffic topics and the paste-ready prompt that assembles them. Nothing on it has been applied.",
    "decisions.html": f"The decision queue for this site: every open choice with its options, cost and reversibility, shown in the order each unblocks the others, plus the {sum(1 for d in DECISIONS if d['status'] == 'Recorded')} decisions recorded on 2026-11-16 under the owner's delegation.",
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
    "decision-centre.html": page_decision_centre,
    "information-gaps.html": page_information_gaps,
    "design.html": page_design,
    "decisions.html": page_decisions,
    "analytics.html": page_analytics,
    "flagged.html": page_flagged,
    "sources.html": page_sources,
}


def _tag_amazon_hrefs(doc: str) -> str:
    """Add the Associates tag to every www.amazon.com link on a page (Program Policies 2(b)).

    Participation Requirement 2(b): "you must include your Associates ID or "tag" ... as a parameter in
    the URL of each link you place on your Site to an Amazon Site." Before 2026-11-19 most source and
    competitor links on the site were untagged (F-69). Links that already carry a tag are left as they
    are. Only the www.amazon.com host is changed; affiliate-program.amazon.com (Associates pages) is not.
    """
    def repl(m: "re.Match[str]") -> str:
        url = m.group(1)
        base, hash_part = (url.split("#", 1) + [""])[:2] if "#" in url else (url, "")
        if "tag=" in base:
            return m.group(0)
        sep = "&amp;" if "?" in base else "?"
        return f'href="{base}{sep}tag={TRACKING_ID}' + (f"#{hash_part}" if hash_part else "") + '"'
    doc = re.sub(r'href="(https://www\.amazon\.com/[^"]*)"', repl, doc)
    return _sponsor_amazon_anchors(doc)


def _sponsor_amazon_anchors(doc: str) -> str:
    """Mark every www.amazon.com anchor rel="sponsored" (Google: paid and affiliate links).

    Every such link now carries the Associates tag (see _tag_amazon_hrefs), so every one is an
    affiliate link. Before 2026-11-19 the tagging pass ran after rendering and never set rel, so
    63 tagged Associates help and category links went out without it (F-74). The click counter
    (docs/measure.js) also selects on rel="sponsored", so untagged-rel links were not counted.
    """
    def repl(m: "re.Match[str]") -> str:
        attrs = m.group(1)
        if not re.search(r'\bhref="https://www\.amazon\.com/', attrs):
            return m.group(0)
        rel = re.search(r'\brel="([^"]*)"', attrs)
        if rel:
            if "sponsored" in rel.group(1).split():
                return m.group(0)
            attrs = attrs.replace(rel.group(0), f'rel="sponsored {rel.group(1)}"', 1)
        else:
            attrs = attrs + ' rel="sponsored"'
        return f"<a{attrs}>"
    return re.sub(r"<a\b([^>]*)>", repl, doc)


def render(page: Page) -> str:
    return _tag_amazon_hrefs(_render_page_raw(page))


def _render_page_raw(page: Page) -> str:
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
        # The feed is a first-class publication surface: it is linked from the
        # sidebar, the footer directory and every page head (SG-27, 2026-11-17
        # parallel pass; added to the sidebar 2026-11-19 so the nav check on
        # that row holds literally, not just through the footer). It is appended
        # inside the single navigation group - scripts/verify.py enforces that
        # the sidebar holds exactly one nav-group.
        if nav.endswith("</div>"):
            nav = (
                nav[: -len("</div>")]
                + f'<a href="{esc(page.rel("feed.xml"))}">RSS feed</a></div>'
            )
    directory_targets = list(dict.fromkeys(target for _group, targets in NAV_ORDER for target in targets))
    footer_links = "".join(
        f'<a href="{esc(page.rel(target))}">{esc(NAV_LABEL.get(target, target))}</a>'
        for target in directory_targets
    )
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
<meta property="og:title" content="{esc(page.title_tag or page.title)}">
<meta property="og:description" content="{esc(page.description or SITE_DESCRIPTION)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{esc(SITE_URL + page.path)}">
<meta property="og:site_name" content="{esc(SITE_TITLE_SUFFIX)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(page.title_tag or page.title)}">
<meta name="twitter:description" content="{esc(page.description or SITE_DESCRIPTION)}">
{page.head_extra}
<link rel="stylesheet" href="{esc(page.rel('styles.css'))}">
<meta name="zone4-measure-endpoint" content="{esc(build_extras.MEASURE_ENDPOINT)}">
<link rel="alternate" type="application/rss+xml" title="Zone4 articles" href="{esc(page.rel('feed.xml'))}">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<div class="layout">
<aside class="sidebar">
  <a class="brand" href="{esc(page.rel('index.html'))}"><span class="brand-name">Zone4</span><span class="brand-tag">air fryer buying guides</span></a>
  <nav aria-label="Main">{nav}</nav>
</aside>
<div class="content">
{disclosure}{amazon_text}
<main id="main">
{page.body}
</main>
<footer>
  <p class="footer-disclosure"><strong>Disclosure:</strong> {esc(DISCLOSURE_SENTENCE)} <span class="small">(Source: {ext(DISCLOSURE_SOURCE, "Associates Operating Agreement, Section 5")}) This site is not endorsed by or affiliated with Amazon.</span></p>
  <nav class="footer-directory" aria-label="Site directory"><strong>Explore the site</strong><div class="footer-links">{footer_links}<a href="{esc(page.rel('feed.xml'))}">RSS feed</a></div></nav>
  <nav aria-label="Footer" class="footer-nav">
    <div class="footer-col">
      <div class="footer-t">Transparency</div>
      <a href="{esc(page.rel('verification.html'))}">Verification log</a>
      <a href="{esc(page.rel('policy-compliance.html'))}">Policy compliance</a>
      <a href="{esc(page.rel('flagged.html'))}">Flagged for review</a>
      <a href="{esc(page.rel('sources.html'))}">Sources</a>
    </div>
    <div class="footer-col">
      <div class="footer-t">Decide</div>
      <a href="{esc(page.rel('suggestions.html'))}">Suggestions</a>
      <a href="{esc(page.rel('questions.html'))}">Open questions</a>
      <a href="{esc(page.rel('decisions.html'))}">Decision log</a>
      <a href="{esc(page.rel('design.html'))}">Design brief</a>
    </div>
    <div class="footer-col">
      <div class="footer-t">Research</div>
      <a href="{esc(page.rel('analytics.html'))}">Analytics</a>
      <a href="{esc(page.rel('automation.html'))}">Automation &amp; tracking</a>
      <a href="{esc(page.rel('executive-summary.html'))}">Executive summary</a>
      <a href="{esc(page.rel('requirements.html'))}">Requirements</a>
    </div>
  </nav>
  <p class="small">Data observed {esc(OBSERVED)} (UTC). Source of truth: the data/ folder in the repository. Build: scripts/build_site.py. Checks: scripts/verify.py.</p>
</footer>
</div>
</div>
<script src="{esc(page.rel('app.js'))}"></script>
<script src="{esc(page.rel('measure.js'))}" defer></script>
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
            page.title_tag = INDEX_TITLE_TAG
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
        if page.path == "design.html":
            html_text = html_text.replace(
                "</body>",
                f'<script src="{esc(page.rel("design.js"))}"></script>\n</body>',
            )
        out = OUT / page.path
        out.write_text(html_text, encoding="utf-8")
        written.append(out)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    extra_written = build_extras.write_all(sys.modules[__name__])
    written += [OUT / p for p in extra_written]
    # A generated sitemap of the site's own pages: every URL in it is one this
    # build produced, on the Pages host for this repository. Nothing here is a
    # claim about products; submission to a search console is a user decision
    # (suggestion S-06 / open questions register). Added by arena/d8564cd0-zone4.
    site_urls = [SITE_URL + p.path for p in collect_pages()]
    site_urls += [SITE_URL + p for p in extra_written if p.endswith(".html")]
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in site_urls)
        + "</urlset>\n"
    )
    (OUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    # RSS is generated from the same article records as the site. Publication dates
    # are deliberately omitted because the source data has no verified per-article
    # dates; subscribers still get canonical links and the editorial descriptions.
    feed_items = []
    for article, article_url in ARTICLE_PATHS:
        item_url = SITE_URL + article_url.lstrip("/")
        feed_items.append(
            "  <item>\n"
            f"    <title>{html.escape(article['h1'])}</title>\n"
            f"    <link>{html.escape(item_url)}</link>\n"
            f"    <guid isPermaLink=\"true\">{html.escape(item_url)}</guid>\n"
            f"    <description>{html.escape(article['meta_description'])}</description>\n"
            "  </item>\n"
        )
    feed_items += build_extras.feed_items(sys.modules[__name__])
    feed = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>\n'
        f"  <title>{html.escape(SITE_TITLE_SUFFIX)} articles</title>\n"
        f"  <link>{html.escape(SITE_URL)}</link>\n"
        "  <description>Question-led air-fryer guides built from sourced product facts.</description>\n"
        "  <language>en-us</language>\n"
        + "".join(feed_items)
        + "</channel></rss>\n"
    )
    (OUT / "feed.xml").write_text(feed, encoding="utf-8")
    # robots.txt: mechanical SEO hygiene that points crawlers at the sitemap this
    # build just wrote (suggestion S-09 shipped the sitemap; the pointer costs
    # nothing and decides nothing). Added by arena/f9f20f21-zone4 (2026-11-16).
    (OUT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n"
        f"Sitemap: {SITE_URL}sitemap.xml\n",
        encoding="utf-8",
    )
    return written


if __name__ == "__main__":
    for p in build():
        print("wrote", p.relative_to(ROOT))
