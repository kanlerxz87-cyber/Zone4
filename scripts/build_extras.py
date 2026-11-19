"""Publication extras for the Zone4 site.

Called from scripts/build_site.py during its build, so `docs/` is still written by
exactly one pipeline (CI rebuilds and diffs it). This module writes:

* the products-first section for the landing page (shop_section);
* the guide hub and one page per question-shaped guide in data/guides.json;
* the meat-thermometer category page for the two added products;
* the product-intent confirmation record (docs/links.html);
* the measurement definitions and the empty campaign ledger (docs/measurement.html);
* an RSS 2.0 feed of every guide and article (docs/feed.xml);
* docs/measure.js, the five-event sender, which stays inert until an endpoint is set.

Every figure printed here is read from a data/ file, and every product link is a
sponsored link to the official listing page or the supplied short link. Added by
arena/3d2ad125-zone4 on 2026-11-17.
"""
from __future__ import annotations

import datetime as dt
import email.utils
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# Set to the URL of a self-hosted analytics endpoint (analytics-endpoint/server.py)
# once the owner hosts it. Empty means the site sends no measurement request at all.
MEASURE_ENDPOINT = ""

# Held candidates. Empty since 2026-11-19 (decision D-46, arena/4cfacb30-zone4): P4 and P5 were
# re-resolved from their short links to the recorded ASINs and are published as tagged Special Links
# with the same status as P1-P3 (D-01/D-14). To hold them again, set this to {"P4", "P5"} and rebuild.
HELD_PRODUCT_IDS: set[str] = set()


def is_held(pid: str) -> bool:
    return pid in HELD_PRODUCT_IDS


def is_queued(g: dict) -> bool:
    """A guide whose publication_status says it is queued waits for its cadence date (data/publishing.json)."""
    return str(g.get("publication_status", "")).startswith("Queued")


def published_guides() -> list[dict]:
    return [g for g in _load("guides.json")["guides"]
            if not any(is_held(pid) for pid in g["product_ids"]) and not is_queued(g)]

# The five defined events. Anything else the page script sends is refused by the endpoint.
EVENTS = [
    ("page_view", "Once per page load", "The page path only (no query string, no referrer, no identifier)", "Daily count per path"),
    ("outbound_click", "A click on any sponsored product link", "Path, product ID and ASIN from the link's own attributes", "Daily count per path and ASIN"),
    ("guide_read_75", "The reader scrolls past 75% of a guide, once per page load", "Path only", "Daily count per guide"),
    ("category_click", "A click on a category link in the navigation or on the home page", "Path and target category", "Daily count per target"),
    ("feed_click", "A click on the RSS feed link", "Path only", "Daily count"),
]


PAID_NOTE = '<span class="small">Paid link. As an Amazon Associate I earn from qualifying purchases.</span>'
POLICY_URL = "https://affiliate-program.amazon.com/help/operating/policies"


def _load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def _shop_link(url: str, label: str, asin: str = "", extra_cls: str = "shop") -> str:
    # rel="sponsored" is required on every product link (Google's guidance for paid links);
    # the data-track attributes let the local tracker count the click as before.
    return (f'<a href="{_e(url)}" rel="sponsored noopener noreferrer" class="{extra_cls}" '
            f'data-track="click" data-track-target="{_e(url)}" data-track-asin="{_e(asin)}">{_e(label)}</a>')


def _e(value) -> str:
    import html as _html
    return _html.escape("" if value is None else str(value), quote=True)


def _tagged_for(pid: str, asin: str) -> str:
    """The published outbound href: the tagged Special Link (decisions D-01/D-14, 2026-11-17).

    Sourced from the product-intent record's candidate URL so the record and the
    rendered href cannot drift; falls back to building the URL from the ASIN.
    """
    for l in _load("intent-links.json")["links"]:
        if l["product_id"] == pid:
            return l["tracking_id_candidate_url"]
    return f"https://www.amazon.com/dp/{asin}?tag=" + _load("intent-links.json")["_meta"]["tracking_id"]


def all_products(bs) -> list[dict]:
    """P1-P3 from data/products.json (via build_site) plus P4-P5 from data/products-extra.json."""
    extra = _load("products-extra.json")["products"]
    return list(bs.PRODUCTS) + list(extra)


def _category_for(p: dict) -> str:
    if p["id"] in ("P4", "P5"):
        return "meat-thermometers"
    return {"P1": "dual-basket-air-fryers", "P2": "air-fryer-toaster-ovens", "P3": "single-basket-air-fryers"}[p["id"]]


CATEGORY_LABEL = {
    "dual-basket-air-fryers": "Dual-basket air fryers",
    "single-basket-air-fryers": "Single-basket air fryers",
    "air-fryer-toaster-ovens": "Air-fry toaster ovens",
    "meat-thermometers": "Meat thermometers",
}


def _guide_for_product(guides: list[dict], pid: str) -> dict | None:
    for g in guides:
        if pid in g["product_ids"]:
            return g
    return None


def extra_products_section(bs, current) -> str:
    """Candidate listings on the All products page: tagged Special Links (decision D-46), or text only if held."""
    rows = []
    for p in _load("products-extra.json")["products"]:
        if is_held(p["id"]):
            # Held: the record is listed as text only. No link, no sponsored link (F-55 on main).
            rows.append(
                f'<tr><td class="mono">{_e(p["id"])}</td>'
                f'<td><a href="{_e(p["canonical_url"])}" rel="sponsored noopener noreferrer">{_e(p["name_short"])}</a> '
                f'<span class="small muted">(official listing, source only)</span></td>'
                f'<td class="mono">{_e(p["asin"])}</td><td>{_e(p["category_path"])}</td>'
                f'<td class="mono">{_e(p["short_link"])}<div class="small muted">Held: not published as a link until F-55 is resolved.</div></td></tr>'
            )
            continue
        rows.append(
            f'<tr><td class="mono">{_e(p["id"])}</td>'
            f'<td><a href="{_e(p["canonical_url"])}" rel="sponsored noopener noreferrer">{_e(p["name_short"])}</a></td>'
            f'<td class="mono">{_e(p["asin"])}</td><td>{_e(p["category_path"])}</td>'
            f'<td>{_shop_link(_tagged_for(p["id"], p["asin"]), "View on Amazon", p["asin"])}<br>' + PAID_NOTE
            + f'<div class="small muted">Supplied short link (recorded, not judged): <span class="mono">{_e(p["short_link"])}</span></div></td></tr>'
        )
    if not rows:
        return ""
    return ('<section><h2>Other submitted listings</h2>'
            '<p class="section-lead">Published under decision D-46 (2026-11-19): each short link was re-resolved to the ASIN '
            'shown, and each outbound link is the tagged Special Link. Attribution is pending the Associates Central test (F-58).</p>'
            '<div class="tablewrap"><table class="data"><thead><tr><th scope="col">ID</th><th scope="col">Product (source link)</th><th scope="col">ASIN</th>'
            '<th scope="col">Category (Amazon path, as read)</th><th scope="col">Affiliate link (tagged Special Link)</th></tr></thead><tbody>' + "".join(rows)
            + '</tbody></table></div></section>')


def shop_section(bs, current) -> str:
    """Products first: one card per listing, above the verification material."""
    guides = published_guides()
    cards = []
    for p in all_products(bs):
        if is_held(p["id"]):
            continue
        cat = _category_for(p)
        facts = []
        if p.get("capacity"):
            facts.append(f"Capacity as listed: {_e(p['capacity'])}")
        if p.get("dimensions"):
            facts.append(f"Dimensions as listed: {_e(p['dimensions'])}")
        facts_html = "".join(f"<li>{f}</li>" for f in facts) or "<li>Capacity and dimensions: not recorded for this listing yet (F-60)</li>"
        guide = _guide_for_product(guides, p["id"])
        guide_html = (f'<a href="{_e(current.rel("guides/" + guide["slug"] + ".html"))}">Read the guide</a>'
                      if guide else "")
        cards.append(
            f'<article class="shop-card"><div class="shop-cat">{_e(CATEGORY_LABEL[cat])}</div>'
            f'<h3>{_e(p["name_short"])}</h3>'
            f'<p class="small mono">ASIN {_e(p["asin"])} · {_e(p["id"])}</p>'
            f'<ul class="small">{facts_html}</ul>'
            f'<p class="shop-actions">{_shop_link(_tagged_for(p["id"], p["asin"]), "View on Amazon", p["asin"])} ' + PAID_NOTE +
            f'<a href="{_e(current.rel("products.html"))}">Source record</a> {guide_html}</p></article>'
        )
    return (
        '<section class="shop-section" id="shop"><h2>Shop the listings</h2>'
        '<p class="section-lead">Each card links to the listing you supplied, marked as a sponsored link. '
        'Prices and star ratings are not shown: the Associates programme withholds them from sites like this one (F-02). '
        'What is shown is the title and the figures the listing states, each with its source.</p>'
        f'<div class="shop-grid">{"".join(cards)}</div>'
        f'<p class="small muted">The verification trail for every figure is on the '
        f'<a href="{_e(current.rel("verification.html"))}">verification log</a>.</p></section>'
    )


def _page_html(bs, page, body: str):
    return bs.render_page(page, body)


def _guide_body(bs, page, g: dict) -> str:
    sections = []
    for s in g["sections"]:
        paras = "".join(f"<p>{_e(t)}</p>" for t in s["paragraphs"])
        sections.append(f"<section><h2>{_e(s['h2'])}</h2>{paras}</section>")
    prod_links = []
    for pid in g["product_ids"]:
        p = next(x for x in all_products(bs) if x["id"] == pid)
        prod_links.append(f'<li><p>{_shop_link(_tagged_for(p["id"], p["asin"]), "View " + p["name_short"] + " on Amazon", p["asin"])}'
                          f' <span class="small mono">ASIN {_e(p["asin"])}</span> ' + PAID_NOTE + '</p></li>')
    rows = []
    for f in g["facts"]:
        rows.append(
            f'<tr><td class="mono">{_e(f["id"])}</td><td class="mono">{_e(f["product"])}</td>'
            f'<td>{_e(f["text"])}</td>'
            f'<td><a href="{_e(f["source"])}" rel="sponsored noopener noreferrer">Official listing</a></td></tr>'
        )
    table = (
        '<div class="tablewrap"><table class="data"><thead><tr><th scope="col">Fact</th><th scope="col">Product</th>'
        '<th scope="col">What the listing states</th><th scope="col">Source</th></tr></thead><tbody>'
        + "".join(rows) + "</tbody></table></div>"
    )
    return (
        f'<header class="hero"><p class="crumbs small">Guide · published {_e(g["published_utc"])} (UTC)</p>'
        f'<h1>{_e(g["h1"])}</h1><p class="lead">{_e(g["dek"])}</p></header>'
        f'<article class="guide">{"".join(sections)}'
        f'<section><h2>Listings in this guide</h2><ul class="bullets">{"".join(prod_links)}</ul></section>'
        f'<section><h2>Facts used in this guide</h2><p class="section-lead">Every figure above is one of these rows. '
        f'A figure without a row is not published.</p>{table}</section>'
        f'<p class="small">{_e(g["disclosure"])} The disclosure is repeated under each product link above.</p>'
        f'<nav class="wherenext" aria-label="Where next"><strong>Where next</strong><ul>'
        f'<li><a href="{_e(page.rel("guides/index.html"))}">All guides</a></li>'
        f'<li><a href="{_e(page.rel("categories/" + _category_for(next(x for x in all_products(bs) if x["id"] == g["product_ids"][0])) + ".html"))}">'
        f'{_e(CATEGORY_LABEL[g["category"]])}</a></li>'
        f'<li><a href="{_e(page.rel("products.html"))}">All listings and their records</a></li>'
        f'<li><a href="{_e(page.rel("flagged.html"))}">Flagged for review</a></li></ul></nav></article>'
    )


def _guide_page_body_index(bs, page, guides: list[dict]) -> str:
    cards = []
    for g in guides:
        cards.append(
            f'<article class="acard"><div class="acard-meta">{_e(CATEGORY_LABEL[g["category"]])} · published {_e(g["published_utc"])}</div>'
            f'<h3><a href="{_e(page.rel("guides/" + g["slug"] + ".html"))}">{_e(g["h1"])}</a></h3>'
            f'<p>{_e(g["dek"])}</p></article>'
        )
    pub = _load("publishing.json")
    cad = pub["cadence"]
    return (
        '<header class="hero"><h1>Guides</h1><p class="lead">Questions a buyer types before buying a countertop '
        'appliance, answered from the official listing pages. One new guide every '
        f'{cad["interval_days"]} days; the next is due {_e(cad["next_due_utc"])} (UTC).</p></header>'
        f'<div class="agrid">{"".join(cards)}</div>'
        f'<p class="small muted">Earlier articles, grouped by format, are on the '
        f'<a href="{_e(page.rel("articles/index.html"))}">articles hub</a>. The publishing rule is in '
        f'<code>data/publishing.json</code>.</p>'
    )


def _thermometer_body(bs, page) -> str:
    rows = []
    for p in _load("products-extra.json")["products"]:
        rows.append(
            f'<tr><td class="mono">{_e(p["id"])}</td>'
            f'<td><a href="{_e(p["canonical_url"])}" rel="sponsored noopener noreferrer">{_e(p["name_short"])}</a>'
            f'<div class="small muted">{_e(p["name_listing"])}</div></td>'
            f'<td class="mono">{_e(p["asin"])}</td>'
            f'<td>{_e(p["category_path"])}</td>'
            f'<td>{_e(p["brand_status"])}</td>'
            f'<td>{_shop_link(_tagged_for(p["id"], p["asin"]), "View on Amazon", p["asin"])}<br>' + PAID_NOTE + '</td>'
            f'<td class="mono">{_e(", ".join(p["flags"]))}</td></tr>'
        )
    table = ('<div class="tablewrap"><table class="data"><thead><tr><th scope="col">ID</th><th scope="col">Product (source link)</th>'
             '<th scope="col">ASIN</th><th scope="col">Category (Amazon path, as read)</th><th scope="col">Brand</th><th scope="col">Affiliate link (tagged Special Link)</th><th scope="col">Flags</th>'
             '</tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")
    g = next(x for x in _load("guides.json")["guides"] if x["slug"] == "what-to-check-in-a-meat-thermometer")
    guide_line = (f'<p>Read the guide: <a href="{_e(page.rel("guides/" + g["slug"] + ".html"))}">{_e(g["h1"])}</a>.</p>'
                  if not is_queued(g) else
                  '<p class="small muted">A buying guide for meat thermometers is queued by the publishing cadence '
                  '(next due 2026-12-01).</p>')
    return (
        '<header class="hero"><h1>Meat thermometers</h1><p class="lead">Two listings from the submitted links, published '
        'under decision D-46 (2026-11-19). Each short link was re-resolved to the ASIN shown, and the title and category '
        'breadcrumb were read. Brand, model, capacity and dimensions are blank until the Item details table is read (F-60). '
        'Attribution is pending the Associates Central test (F-58).</p></header>'
        f'<section><h2>Listings</h2>{table}</section>'
        f'<section><h2>What the titles state</h2><p class="section-lead">Claims as titled, not tested by this site.</p>'
        '<ul class="bullets">'
        + "".join(f'<li><strong>{_e(p["name_short"])}</strong>: {_e("; ".join(p["listing_claims_in_title"]))}</li>'
                  for p in _load("products-extra.json")["products"])
        + f'</ul>{guide_line}</section>'
    )


def _links_body(bs, page) -> str:
    rec = _load("intent-links.json")
    rows = []
    for l in rec["links"]:
        r = l["observed_redirect"]
        match = "Yes" if l["intent_match"] else "No"
        held = is_held(l["product_id"])
        submitted_cell = (f'{_e(l["submitted_url"])}<div class="small muted">Held: not published as a link</div>'
                          if held else _e(l["submitted_url"]))
        # The official listing is the row's source link (every row links its official source).
        listing_cell = f'<a href="{_e(l["official_listing_url"])}" rel="sponsored noopener noreferrer">{_e(l["official_listing_url"])}</a>'
        rows.append(
            f'<tr><td class="mono">{_e(l["product_id"])}</td>'
            f'<td class="mono">{submitted_cell}</td>'
            f'<td class="mono">{_e(l["intended_asin"])}<div class="small muted">{_e(l["intent_basis"])}</div></td>'
            f'<td>{listing_cell}'
            f'<div class="small muted">Confirmed {_e(l["confirmation_date_utc"])}: {_e(l["confirmation_source"])}</div></td>'
            f'<td class="mono">{_e(r["observed_asin"])}<div class="small muted">Observed {_e(r["date_utc"])}; query parameters: '
            f'{_e(", ".join(r["observed_query_parameters"]) or "none")}</div></td>'
            f'<td>{match}</td>'
            f'<td class="small">{_e(l["special_link_status"])}</td></tr>'
        )
    table = ('<div class="tablewrap"><table class="data"><thead><tr><th scope="col">Product</th><th scope="col">Submitted link</th>'
             '<th scope="col">Intended ASIN (basis)</th><th scope="col">Official listing URL (confirmation and source)</th>'
             '<th scope="col">Observed redirect target (separate field)</th><th scope="col">Same ASIN?</th><th scope="col">Special Link status</th>'
             '</tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")
    return (
        '<header class="hero"><h1>Product-intent confirmation record</h1><p class="lead">For each submitted link: '
        'the ASIN the site intends to publish, the official listing it belongs to, when and from what that was '
        'confirmed, and the target the link redirected to when it was observed. The two ASIN fields are kept apart '
        'and are never merged. The short-link path code (for example B04G1MEwY) is not an ASIN.</p></header>'
        f'<section><h2>Records</h2>{table}</section>'
        f'<section><h2>Tracking ID</h2><p>Tracking ID supplied by the owner: <code>{_e(rec["_meta"]["tracking_id"])}</code>. '
        f'{_e(rec["_meta"]["tracking_id_source"])}</p>'
        '<p>Since 2026-11-17 the published outbound product links are the tagged Special Links '
        '<code>https://www.amazon.com/dp/&lt;ASIN&gt;?tag=shopnow047c-20</code> - the final destination URL with the '
        'owner-selected tracking ID as its parameter (decisions D-01/D-14, recorded under the owner\'s brief, which '
        'directs: replace ambiguous outbound links with validated Special Links; test one link per product before '
        'scaling). Each tagged URL had already passed a destination check (engine_candidate_url.destination_test). '
        'What the one-link-per-product Associates Central test (data/associates.json) still gates is attribution and '
        'scaling beyond these three links - not publication (F-57, F-58). The supplied short links stay recorded '
        'verbatim and unjudged (Zone3 FLG-003 unresolved).</p>'
        f'<p>Background: <a href="{_e(page.rel("flagged.html"))}">F-03</a> (no Associates tag in the resolved links), '
        f'<a href="{_e(page.rel("flagged.html"))}">F-47</a> (the displayed link form).</p></section>'
    )


def five_events_table(ledger: dict) -> str:
    """The brief's five defined events with their official windows (data/ledger.json)."""
    rows = "".join(
        f'<tr><td class="mono">{_e(ev["event"])}</td><td>{_e(ev["definition"])}</td>'
        f'<td>{_e(ev["window"])}</td>'
        f'<td><a href="{POLICY_URL}" rel="noopener noreferrer">{_e(ev.get("source_ref", "Program Policies"))}</a></td></tr>'
        for ev in ledger.get("five_events", [])
    )
    if not rows:
        return '<p class="small muted">Event definitions pending.</p>'
    return ('<div class="tablewrap"><table class="data"><thead><tr><th scope="col">Event</th>'
            '<th scope="col">Definition</th><th scope="col">Attribution window (official)</th>'
            '<th scope="col">Source (official)</th></tr></thead><tbody>' + rows + '</tbody></table></div>')


def provenance_html(ledger: dict) -> str:
    """Dated provenance trail: who defined the ledger and when (data/ledger.json)."""
    prov = ledger.get("provenance") or []
    if not prov:
        return ""
    rows = "".join(
        f'<tr><td class="small">{_e(p_["date_utc"])}</td><td>{_e(p_["entry"])}</td>'
        f'<td class="small mono"><a href="https://github.com/kanlerxz87-cyber/Zone4/blob/main/{_e(p_.get("record", ""))}" rel="noopener noreferrer">{_e(p_.get("record", ""))}</a></td></tr>'
        for p_ in prov
    )
    return ('<h3>Provenance trail</h3><div class="tablewrap"><table class="data"><thead><tr>'
            '<th scope="col">Date (UTC)</th><th scope="col">Entry</th><th scope="col">Record</th></tr></thead>'
            '<tbody>' + rows + '</tbody></table></div>')


def _measurement_body(bs, page) -> str:
    ev_rows = "".join(
        f'<tr><td class="mono">{_e(name)}</td><td>{_e(when)}</td><td>{_e(stored)}</td><td>{_e(where)}</td>'
        f'<td><a href="{POLICY_URL}" rel="noopener noreferrer">Associates Program Policies</a></td></tr>'
        for name, when, stored, where in EVENTS
    )
    ledger = _load("ledger.json")
    cols = "".join(f'<th scope="col">{_e(c)}</th>' for c in ledger["columns"])
    ledger_table = (f'<div class="tablewrap"><table class="data"><thead><tr>{cols}</tr></thead>'
                    '<tbody></tbody></table></div>')
    endpoint = ("Not hosted. The page script sends nothing until an endpoint is set."
                if not MEASURE_ENDPOINT else f"Set to {_e(MEASURE_ENDPOINT)}.")
    return (
        '<header class="hero"><h1>Measurement and campaign ledger</h1><p class="lead">What the site measures, '
        'what it never stores, and the ledger that stays empty until an authorised first-party report is '
        'imported. No conversion, revenue or traffic figure is published (F-15).</p></header>'
        '<section><h2>Five defined events</h2><p class="section-lead">The page script honours Do Not Track and Global '
        'Privacy Control and sets no cookie. The endpoint keeps counts per day and path only: no IP address, '
        'user agent, referrer or visitor identifier is stored.</p>'
        '<div class="tablewrap"><table class="data"><thead><tr><th scope="col">Event</th><th scope="col">Fires when</th>'
        '<th scope="col">What is stored</th><th scope="col">Aggregated as</th><th scope="col">Source</th></tr></thead><tbody>' + ev_rows + '</tbody></table></div>'
        f'<p><strong>Endpoint status:</strong> {endpoint} The server is in <code>analytics-endpoint/</code>; '
        'it runs anywhere that accepts a Python process, not on GitHub Pages, which only serves static files.</p></section>'
        '<section><h2>The five defined events (campaign ledger)</h2><p class="section-lead">The brief\'s five event types '
        'with the official attribution windows each figure must satisfy before it can enter a ledger row. These are '
        'the Associates measurement events - a different vocabulary from the local counter\'s event names above.</p>'
        + five_events_table(ledger) + '</section>'
        '<section><h2>Campaign ledger</h2><p class="section-lead">Rows are added only from authorised first-party '
        'reports. This ledger has no rows: no report has been imported, so no clicks, eligible sessions or orders '
        'are shown anywhere. The site\'s own click counter is a different measurement and is never an order.</p>'
        + ledger_table + provenance_html(ledger) + f'<p class="small muted">{_e(ledger["status"])}</p></section>'
        '<section><h2>Not connected</h2><ul class="bullets">'
        '<li>Search Console: needs the owner to verify the property. Nothing has been submitted.</li>'
        '<li>Reader capture (email): needs an owner-chosen provider and consent text. Not built.</li>'
        '<li>Associates reporting: needs the owner\'s Associates Central access (F-03, F-58).</li></ul></section>'
    )


def feed_items(bs) -> list[str]:
    """RSS items for the published guides, appended by scripts/build_site.py to its single feed.

    Publication dates are omitted, as in the article items: no per-guide date has been verified
    as an output of the source data (see the note in build_site.build()).
    """
    items = []
    for g in published_guides():
        url = bs.SITE_URL + "guides/" + g["slug"] + ".html"
        items.append(
            "  <item>\n"
            f"    <title>{_e(g['h1'])}</title>\n"
            f"    <link>{_e(url)}</link>\n"
            f"    <guid isPermaLink=\"true\">{_e(url)}</guid>\n"
            f"    <description>{_e(g['meta_description'])}</description>\n"
            "  </item>\n"
        )
    return items


MEASURE_JS = """// Zone4 measurement script: five defined events, inert unless an endpoint is set.
// No cookies, no storage, no identifiers. Honours Do Not Track and Global Privacy Control.
(function () {
  'use strict';
  var meta = document.querySelector('meta[name="zone4-measure-endpoint"]');
  var endpoint = meta ? meta.getAttribute('content') : '';
  if (!endpoint) { return; }
  if (navigator.doNotTrack === '1' || window.doNotTrack === '1' || navigator.globalPrivacyControl === true) { return; }
  var EVENTS = { page_view: 1, outbound_click: 1, guide_read_75: 1, category_click: 1, feed_click: 1 };
  function send(name, extra) {
    if (!EVENTS[name]) { return; }
    var payload = { event: name, path: location.pathname };
    if (extra) { for (var k in extra) { payload[k] = extra[k]; } }
    var body = JSON.stringify(payload);
    try {
      if (navigator.sendBeacon) {
        navigator.sendBeacon(endpoint, new Blob([body], { type: 'application/json' }));
      } else {
        fetch(endpoint, { method: 'POST', body: body, keepalive: true, mode: 'cors' });
      }
    } catch (e) { /* the measurement must never break the page */ }
  }
  send('page_view');
  document.addEventListener('click', function (ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest('a') : null;
    if (!a) { return; }
    var rel = (a.getAttribute('rel') || '');
    if (rel.indexOf('sponsored') !== -1) {
      send('outbound_click', { asin: a.getAttribute('data-track-asin') || '' });
    } else if (a.getAttribute('data-measure') === 'category') {
      send('category_click', { target: a.getAttribute('href') || '' });
    } else if (a.getAttribute('data-measure') === 'feed') {
      send('feed_click');
    }
  }, false);
  var article = document.querySelector('article.guide');
  if (article && 'IntersectionObserver' in window) {
    // Marker sits at 75% of the article's own height, not of the viewport (fixed 2026-11-17).
    article.style.position = 'relative';
    var marker = document.createElement('div');
    marker.setAttribute('aria-hidden', 'true');
    marker.style.cssText = 'position:absolute;top:75%;height:1px;width:1px;pointer-events:none;';
    article.appendChild(marker);
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { send('guide_read_75'); io.disconnect(); } });
    });
    io.observe(marker);
  }
})();
"""


def write_all(bs) -> list[str]:
    """Write every extra page into bs.OUT and return the docs-relative paths written.

    `bs` is scripts/build_site.py (passed in to avoid a circular import). It must expose
    render_page(page, body), Page, OUT, SITE_URL, OBSERVED, ARTICLE_PATHS and PRODUCTS.
    """
    guides = published_guides()
    written: list[str] = []
    out = bs.OUT
    (out / "guides").mkdir(exist_ok=True)

    def emit(path: str, page_title: str, body: str, description: str | None, title_tag: str | None = None,
             head_extra: str = "") -> None:
        page = bs.Page(path, page_title, path, body, description=description, title_tag=title_tag,
                       head_extra=head_extra)
        page.body = body
        (out / path).write_text(bs.render(page), encoding="utf-8")
        written.append(path)

    # The body needs the page object to build relative links, so it is generated after the page exists.
    page = bs.Page("guides/index.html", "Guides", "guides/index.html", "",
                   description="Question-shaped guides, each fact linked to the official listing page it was read from.",
                   title_tag="Buying guides: answers from the listings")
    page.body = _guide_page_body_index(bs, page, guides)
    (out / "guides/index.html").write_text(bs.render(page), encoding="utf-8")
    written.append("guides/index.html")

    for g in guides:
        path = "guides/" + g["slug"] + ".html"
        page = bs.Page(path, g["h1"], path, "", description=g["meta_description"], title_tag=g["title_tag"],
                       head_extra=_article_ld(bs, g))
        page.body = _guide_body(bs, page, g)
        (out / path).write_text(bs.render(page), encoding="utf-8")
        written.append(path)

    # The meat-thermometer category (decision D-46): its two listings are published; its guide waits for the cadence.
    tpath = "categories/meat-thermometers.html"
    page = bs.Page(tpath, "Meat thermometers", tpath, "",
                   description="Meat thermometers: the two submitted listings, with the title and category breadcrumb each page states, and the claims as titled.",
                   title_tag="Meat thermometers: the two listings")
    page.body = _thermometer_body(bs, page)
    (out / tpath).write_text(bs.render(page), encoding="utf-8")
    written.append(tpath)

    for path, title, desc, fn in (
        ("links.html", "Product-intent record", "The intended ASIN, official listing, confirmation date and "
         "observed redirect target for each submitted link, kept as separate fields.", _links_body),
        ("measurement.html", "Measurement and ledger", "The five defined measurement events, what each one stores, "
         "and the campaign ledger that stays empty until an authorised report is imported.", _measurement_body),
    ):
        page = bs.Page(path, title, path, "", description=desc)
        page.body = fn(bs, page)
        (out / path).write_text(bs.render(page), encoding="utf-8")
        written.append(path)

    # feed.xml is written by scripts/build_site.py, which owns the one RSS feed (guides are added there).
    (out / "measure.js").write_text(MEASURE_JS, encoding="utf-8")
    written.append("measure.js")
    return written


def _article_ld(bs, g: dict) -> str:
    import json as _json
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": g["h1"],
        "description": g["meta_description"],
        "datePublished": g["published_utc"],
        "dateModified": g["published_utc"],
        "inLanguage": "en",
        "author": {"@type": "Organization", "name": bs.SITE_TITLE_SUFFIX},
        "publisher": {"@type": "Organization", "name": bs.SITE_TITLE_SUFFIX},
        "mainEntityOfPage": bs.SITE_URL + "guides/" + g["slug"] + ".html",
    }
    return '<script type="application/ld+json">' + _json.dumps(data, ensure_ascii=False) + "</script>"
