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

def measure_endpoint(settings: dict | None = None) -> str:
    """Fail closed: a URL alone is not evidence that production collection is ready.

    The checklist is reviewed deployment evidence, not automatic policy approval.
    Disabled builds always emit an empty endpoint and send no network events.
    """
    from urllib.parse import urlsplit
    rec = settings if settings is not None else json.loads((DATA / "measurement.json").read_text(encoding="utf-8"))
    if not isinstance(rec.get("enabled"), bool):
        raise ValueError("measurement.enabled must be a boolean")
    if not rec["enabled"]:
        return ""
    endpoint = rec.get("endpoint_url")
    if not isinstance(endpoint, str):
        raise ValueError("measurement endpoint must be an HTTPS /event URL")
    import ipaddress
    url = urlsplit(endpoint)
    host = (url.hostname or "").lower().rstrip(".")
    try:
        public_host = ipaddress.ip_address(host).is_global
    except ValueError:
        public_host = bool(host) and host != "localhost" and not host.endswith(".localhost")
    try:
        url.port  # reject malformed port strings rather than emitting a broken client URL
    except ValueError:
        public_host = False
    if (url.scheme != "https" or not public_host or url.username or url.password
            or url.path != "/event" or url.query or url.fragment
            or host == "github.io" or host.endswith(".github.io")
            or any(c.isspace() or ord(c) < 32 for c in endpoint)):
        raise ValueError("measurement endpoint must be a durable HTTPS /event URL, not Pages or a local address")
    checks = rec.get("launch_checks") or []
    if {c.get("id") for c in checks} != {f"MC-{n:02d}" for n in range(1, 6)} or len(checks) != 5:
        raise ValueError("measurement launch checklist is incomplete")
    for check in checks:
        try:
            date = check.get("confirmed_utc") or ""
            if dt.date.fromisoformat(date).isoformat() != date:
                raise ValueError("not an ISO calendar date")
        except (TypeError, ValueError):
            raise ValueError(f"measurement {check.get('id')}: dated launch evidence is missing") from None
        for key in ("evidence_reference", "reviewed_by"):
            if not isinstance(check.get(key), str) or not check[key].strip():
                raise ValueError(f"measurement {check.get('id')}: {key} is missing")
    return endpoint


# Single configuration surface; a hand-edited URL cannot bypass the evidence gate.
MEASURE_ENDPOINT = measure_endpoint()

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


# --- Publication counts, computed once -------------------------------------
# Every count the site prints about its own catalogue is computed here and
# nowhere else. Recorded as decision D-54 and flag F-95 on 2026-11-20 after the
# front page and the social preview card were found asserting three air fryers
# and eight guides while five products and fourteen guides were published.
#
# A count that is typed into a page, a meta description or an image is a claim
# like any other: it has to come from the register, or it drifts silently.
def _product_records() -> list[dict]:
    """The five published product records: three air fryers, then two thermometers."""
    return list(_load("products.json")["products"]) + list(_load("products-extra.json")["products"])


def _article_records() -> list[dict]:
    return _load("marketing.json")["articles"]


def _text_number(n: int) -> str:
    """Spell out a small count for prose, but never round it: 5 stays 'five'.

    Only the words the copy already uses are mapped, and the mapping is exact
    (not a range lookup), so an unexpected count falls back to the numeral
    rather than inventing a near-miss word.
    """
    words = {0: "no", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
             6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
             11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen",
             15: "fifteen", 16: "sixteen", 17: "seventeen", 18: "eighteen",
             19: "nineteen", 20: "twenty"}
    return words.get(n, str(n))


def publication_counts() -> dict:
    """Counts of what the site actually publishes, each read from its register."""
    products = _product_records()
    articles = _article_records()
    guides = published_guides()
    air_fryers = [p for p in products if "air fryer" in str(p.get("subcategory", "")).lower()]
    thermometers = [p for p in products if "thermometer" in str(p.get("subcategory", "")).lower()]
    return {
        "products": len(products),
        "products_word": _text_number(len(products)),
        "air_fryers": len(air_fryers),
        "air_fryers_word": _text_number(len(air_fryers)),
        "thermometers": len(thermometers),
        "thermometers_word": _text_number(len(thermometers)),
        "articles": len(articles),
        "guides": len(guides),
        # A reader-facing "guide" is either a long-form article or a question-led
        # guide page: the guides hub and the article hub both call their pages
        # guides, so the published total is the sum.
        "published_guides": len(articles) + len(guides),
        "published_guides_word": _text_number(len(articles) + len(guides)),
        "categories": len({p["subcategory"] for p in products}),
    }

# Names and table definitions are read from the same launch record as the endpoint.
MEASUREMENT = json.loads((DATA / "measurement.json").read_text(encoding="utf-8"))
EVENTS = [(ev["name"], ev["when"], ev["payload"], ev["aggregate"]) for ev in MEASUREMENT["events"]]


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


def _card_facts(p: dict) -> list[str]:
    """The two or three figures a shopper compares, worded for the product's category.

    Air fryers are compared on capacity and counter footprint; a meat thermometer
    has neither, so printing a "capacity" line on its card was a defect (F-77,
    fixed 2026-11-19). Everything printed here is a value an official listing
    states and the data file records; nothing is inferred.
    """
    facts: list[str] = []
    if _category_for(p) == "meat-thermometers":
        if p.get("brand"):
            facts.append(f"Brand as listed: {_e(p['brand'])}")
        if p.get("special_feature"):
            facts.append(f"Features as listed: {_e(p['special_feature'])}")
        if p.get("model_number"):
            facts.append(f"Model as listed: {_e(p['model_number'])}")
        if not facts:
            facts.append("<span class=\"spec-note\">Listing figures not yet recorded for this product (F-60).</span>")
        return facts
    if p.get("capacity"):
        facts.append(f"Capacity as listed: {_e(p['capacity'])}")
    if p.get("dimensions"):
        facts.append(f"Dimensions as listed: {_e(p['dimensions'])}")
    return facts


def _recheck_line(bs, p) -> str:
    """'Figures read <date> · listing page re-checked <date>' for one product record.

    Both dates come out of the product registers rather than being typed here: the figures-read date
    is the record's own read field, and the re-check date is taken from the dated
    _meta.reverification_* keys the re-reading pass writes into data/products.json and
    data/products-extra.json. A card therefore cannot advertise a fresher check than the data
    supports, and a record with no dated read says so instead of going quiet.
    """
    read = p.get("read_on") or p.get("observed_utc") or p.get("verification_date") or ""
    recheck = ""
    for name in ("products.json", "products-extra.json"):
        meta = _load(name).get("_meta", {})
        for key in meta:
            if not key.startswith("reverification_"):
                continue
            tail = key.split("reverification_", 1)[1]
            date = tail.replace("_", "-") if len(tail) == 10 else ""
            if date and date > recheck:
                recheck = date
    parts = []
    if read:
        parts.append(f"figures read {read}")
    if recheck:
        parts.append(f"listing page re-checked {recheck}")
    if not parts:
        return "no dated read recorded for this record yet"
    return " · ".join(parts)


def shop_section(bs, current) -> str:
    """Product-first cards. Original diagrams are labelled, never product photographs."""
    guides = published_guides()
    air_fryers, thermometers = [], []
    for p in all_products(bs):
        if is_held(p["id"]):
            continue
        cat = _category_for(p)
        facts = _card_facts(p)
        facts_html = "".join(f"<li>{f}</li>" for f in facts) or '<li>Listing figures not recorded yet.</li>'
        guide = _guide_for_product(guides, p["id"])
        guide_html = (f'<a href="{_e(current.rel("guides/" + guide["slug"] + ".html"))}">What to compare →</a>'
                      if guide else f'<a href="{_e(current.rel("categories/" + cat + ".html"))}">Compare the types →</a>')
        # Footprint diagrams already shipped on the category tiles. No listing
        # image is copied and the caption prevents a diagram looking like a photo.
        visual = '<div class="shop-visual">' + footprint_figure(cat) + '</div>'
        card = (
            f'<article class="shop-card">{visual}<div class="shop-card-copy">'
            f'<div class="shop-cat">{_e(CATEGORY_LABEL[cat])}</div><h3>{_e(p["name_short"])}</h3>'
            f'<ul class="small">{facts_html}</ul><p>{guide_html}</p>'
            f'<p class="shop-actions">{_shop_link(_tagged_for(p["id"], p["asin"]), "View on Amazon →", p["asin"], "shop sun")}'
            + PAID_NOTE + '</p>'
            f'<p class="small muted shop-dates">{_e(_recheck_line(bs, p))} · '
            f'<a href="{_e(current.rel("products.html"))}">Source record</a></p></div></article>'
        )
        (thermometers if cat == "meat-thermometers" else air_fryers).append(card)
    extra = ('<h3 class="shop-subhead">For the roast, the grill & the temperature check</h3>'
             '<p class="section-lead">Two thermometer formats. Compare the listing claims, '
             'then check the type of monitoring you need.</p>'
             '<div class="shop-grid shop-grid-tools">' + "".join(thermometers) + '</div>') if thermometers else ''
    return (
        '<section class="shop-section" id="shop"><div class="front-section-head"><div>'
        '<span class="front-kicker">The product edit</span><h2>Meet your countertop options.</h2></div>'
        f'<a href="{_e(current.rel("products.html"))}">All product details →</a></div>'
        '<p class="section-lead">Three air fryer formats, with the listed dimensions close at hand. '
        'Follow a guide to compare, or open the current listing. All Amazon product links are paid links.</p>'
        '<div class="shop-grid">' + "".join(air_fryers) + '</div>' + extra + '</section>'
    )


def _page_html(bs, page, body: str):
    return bs.render_page(page, body)


def _guide_body(bs, page, g: dict) -> str:
    # Short-answer block (suggestion S-59, decision D-53, SG-44 partial):
    # one paragraph naming the formats compared, from the products' own
    # subcategories, pointing to the fact table for every figure. It carries
    # no number at all, so it cannot restate a figure without its source.
    _prods = [next(x for x in all_products(bs) if x["id"] == pid) for pid in g["product_ids"]]
    _formats = []
    for _p in _prods:
        _f = _p.get("subcategory", "")
        if _f and _f not in _formats:
            _formats.append(_f)
    _formats_text = ", ".join(_formats) if _formats else "the listings named below"
    _short_answer = (
        f'<section><h2>Short answer</h2><p>This guide compares {_e(_formats_text)} on the points '
        f'their listings state. Every figure it uses is a row in the fact table at the end of the guide, '
        f'each linked to the official listing it was read from.</p></section>'
    )
    sections = [_short_answer]
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
        + '<section><h2>The guides so far</h2>'
        + f'<div class="agrid">{"".join(cards)}</div></section>'
        f'<p class="small muted">Earlier articles, grouped by format, are on the '
        f'<a href="{_e(page.rel("articles/index.html"))}">articles hub</a>. The publishing rule is in '
        f'<code>data/publishing.json</code>.</p>'
    )


def _thermometer_chooser(page) -> str:
    """Two questions that separate the two thermometer listings on stated facts only.

    The air-fryer chooser answers 'which format for my kitchen'; two thermometers
    raise a different question - how many things are you tracking at once, and
    how much range do you need. Both facts are read from the listings' own Item
    details (2026-11-19) and the title claims recorded for each product, so the
    routing is checkable. No popularity, rating or accuracy claim is used to rank
    them: both brands claim NIST certification in their titles and this site has
    tested neither.
    """
    fallback = (
        '<div class="tablewrap"><table class="data chooser-fallback"><thead><tr>'
        '<th scope="col">When the need is</th><th scope="col">The listing that states it</th>'
        '<th scope="col">The listed text behind the route (official)</th></tr></thead><tbody>'
        '<tr><td>One probe is enough: a roast, a steak, frying oil or candy</td>'
        '<td><a href="#P4">ThermoMaven instant-read (P4)</a></td>'
        '<td><a href="https://www.amazon.com/dp/B0DHZTCNR5" rel="sponsored noopener noreferrer">'
        'Official listing (B0DHZTCNR5)</a>: the title lists a 1-second read and &plusmn;0.5&deg;F; '
        'Item details list Auto Off, Fast Reading System and an ultra-clear screen</td></tr>'
        '<tr><td>Several probes at once, or a long range away from the grill</td>'
        '<td><a href="#P5">CHEF iQ Sense (P5)</a></td>'
        '<td><a href="https://www.amazon.com/dp/B0DZFD6R9Z" rel="sponsored noopener noreferrer">'
        'Official listing (B0DZFD6R9Z)</a>: Item details list 5 sensors and unlimited range; '
        'the title lists 3 ultra-thin probes and WiFi</td></tr>'
        '</tbody></table></div>'
    )
    return (
        '<section id="therm-chooser"><h2>Which thermometer is for you? Two questions</h2>'
        '<p class="section-lead">Answer two questions and this routes you to the listing whose stated features answer them. '
        'It is editorial routing on the listings\' own text, not a rating: neither unit has been tested here, and no '
        'star rating is published (F-02).</p>'
        '<div class="chooser" id="therm-form">'
        '<fieldset><legend>1. How many things do you want to track at once?</legend>'
        '<label><input type="radio" name="tprobes" value="one" checked> One cut or one pan of oil</label>'
        '<label><input type="radio" name="tprobes" value="several"> Several pieces at once (roasts, multiple steaks)</label>'
        '</fieldset>'
        '<fieldset><legend>2. Do you need to watch it from far away?</legend>'
        '<label><input type="radio" name="trange" value="close" checked> I am standing right there</label>'
        '<label><input type="radio" name="trange" value="far"> Away from the grill, indoors, or in another room</label>'
        '</fieldset>'
        '<button class="btn btn-primary" type="button" id="therm-go">Show my match</button>'
        '</div>'
        '<div class="chooser-result" id="therm-result" role="status" aria-live="polite"></div>'
        '<h3>The routing, in plain text</h3>'
        '<p class="small muted">The same logic, in a table you can check without scripts.</p>'
        + fallback + '</section>'
    )


def _thermometer_body(bs, page) -> str:
    rows = []
    for p in _load("products-extra.json")["products"]:
        rows.append(
            f'<tr id="{_e(p["id"])}"><td class="mono">{_e(p["id"])}</td>'
            f'<td><a href="{_e(p["canonical_url"])}" rel="sponsored noopener noreferrer">{_e(p["name_short"])}</a>'
            f'<div class="small muted">{_e(p["name_listing"])}</div></td>'
            f'<td class="mono">{_e(p["asin"])}</td>'
            f'<td>{_e(p["category_path"])}</td>'
            f'<td>{_e(p["brand"] or "Not stated")}<div class="small muted">{_e(p["brand_status"])}</div></td>'
            f'<td>{_e(p["special_feature"] or "Not stated")}</td>'
            f'<td>{_shop_link(_tagged_for(p["id"], p["asin"]), "View on Amazon", p["asin"])}<br>' + PAID_NOTE + '</td>'
            f'<td class="mono">{_e(", ".join(p["flags"]))}</td></tr>'
        )
    table = ('<div class="tablewrap"><table class="data"><thead><tr><th scope="col">ID</th><th scope="col">Product (source link)</th>'
             '<th scope="col">ASIN</th><th scope="col">Category (Amazon path, as read)</th>'
             '<th scope="col">Brand (Item details, read 2026-11-19)</th><th scope="col">Special feature (Item details, read 2026-11-19)</th>'
             '<th scope="col">Affiliate link (tagged Special Link)</th><th scope="col">Flags</th>'
             '</tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")
    g = next(x for x in _load("guides.json")["guides"] if x["slug"] == "what-to-check-in-a-meat-thermometer")
    guide_line = (f'<p>Read the guide: <a href="{_e(page.rel("guides/" + g["slug"] + ".html"))}">{_e(g["h1"])}</a>.</p>'
                  if not is_queued(g) else
                  '<p class="small muted">A buying guide for meat thermometers is queued by the publishing cadence '
                  '(next due 2026-12-01).</p>')
    return (
        '<header class="hero"><h1>Meat thermometers</h1><p class="lead">Two listings from the submitted links, published '
        'under decision D-46 (2026-11-19). Each short link was re-resolved to the ASIN shown. On 2026-11-19 the Item '
        'details tables were also read: the brand and the listed special features are recorded from them and shown below. '
        'Model number and dimensions stay blank because neither table states them, and a meat thermometer has no air-fryer '
        'capacity to compare (F-60). Attribution is pending the Associates Central test (F-58).</p></header>'
        f'<section><h2>Listings</h2>{table}</section>'
        + _thermometer_chooser(page)
        + f'<section><h2>What the titles state</h2><p class="section-lead">Claims as titled, not tested by this site.</p>'
        '<ul class="bullets">'
        + "".join(f'<li><strong>{_e(p["name_short"])}</strong>: {_e("; ".join(p["listing_claims_in_title"]))}</li>'
                  for p in _load("products-extra.json")["products"])
        + f'</ul>'
        '<div class="cta"><p><strong>Before you choose the instant-read:</strong> the P4 listing states '
        '&ldquo;There is a newer model of this item&rdquo; and links to ASIN B0GL7Z4KP4 (the same title in Orange). '
        'This site publishes no replacement advice, because that notice compares no features and no unit has been '
        'tested here. It is recorded as '
        '<a href="' + _e(page.rel("flagged.html")) + '#F-78">F-78</a> so you can see it before you click through '
        'rather than after.</p></div>'
        + f'{guide_line}'
        '<p class="small muted">Brand and special-feature values were read from the '
        '&ldquo;Purchase options and add-ons&rdquo; table on each listing on 2026-11-19 and are '
        f'recorded per product in <a href="{_e(page.rel("links.html"))}">the product-intent record</a> '
        'and <code>data/products-extra.json</code>. Nothing else was copied from the listing prose.</p>'
        '</section>'
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
        'scaling). The intended ASIN, official listing URL and observed redirect are recorded separately in the table above. '
        'The account-side destination-and-tracking-report test for each published Special Link has not been run; its protocol '
        'and five pending product rows are in data/associates.json. It gates attribution claims and scaling beyond these '
        'five published products - not publication (F-57, F-58). The supplied short links stay recorded verbatim and '
        'unjudged (Zone3 FLG-003 unresolved).</p>'
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
    rec = _load("measurement.json")
    ev_rows = "".join(
        f'<tr><td class="mono">{_e(ev["name"])}</td><td>{_e(ev["when"])}</td>'
        f'<td>{_e(ev["payload"])}</td><td>{_e(ev["aggregate"])}</td>'
        f'<td><a href="{_e(ev["source_url"])}" rel="noopener noreferrer">First-party implementation</a></td></tr>'
        for ev in rec["events"]
    )
    launch_rows = []
    for check in rec["launch_checks"]:
        # Null evidence remains blank; a status label never masquerades as confirmation.
        proof = _e(check.get("confirmed_utc") or "")
        if proof:
            proof += f'<br>{_e(check.get("reviewed_by") or "")}<br>{_e(check.get("evidence_reference") or "")}'
        launch_rows.append(
            f'<tr id="{_e(check["id"])}"><td><strong>{_e(check["id"])}</strong><br>{_e(check["question"])}</td>'
            f'<td>{_e(check["known"])}</td><td>{_e(check["missing"])}</td><td>{_e(check["discovery"])}</td>'
            f'<td>{proof}</td><td><a href="{_e(check["source_url"])}" rel="noopener noreferrer">'
            f'{_e(check["source_label"])}</a></td></tr>'
        )
    ledger = _load("ledger.json")
    cols = "".join(f'<th scope="col">{_e(c)}</th>' for c in ledger["columns"])
    ledger_table = (f'<div class="tablewrap"><table class="data"><thead><tr>{cols}</tr></thead>'
                    '<tbody></tbody></table></div>')
    endpoint = ("Off — no production collection (F-59)."
                if not MEASURE_ENDPOINT else "Configured — delivery must be checked against the collector's own export.")
    return (
        '<header class="hero"><h1>Measurement and campaign ledger</h1><p class="lead">Measure the questions '
        'people actually arrive with before choosing the next guide. Here is what is ready, what is not connected, '
        'and the evidence needed to switch collection on.</p></header>'
        f'<section class="cta"><h2>Collection status: {_e(endpoint)}</h2>'
        '<p>The client and reference collector are built and covered by automated tests. That is not a live analytics '
        'service. No production host or authorised order report is connected, so this page shows no traffic, '
        'conversion score or revenue forecast. The separate browser-local log is not shared analytics.</p>'
        f'<p><a class="btn" href="{_e(page.rel("decision-centre.html"))}">Review the next decisions</a> '
        '<a class="btn" href="#launch-checklist">What is missing before launch?</a></p></section>'
        '<section id="launch-checklist"><h2>Five questions before collection goes live</h2>'
        '<p class="section-lead">Every confirmation cell below is blank until dated evidence exists. '
        'The build refuses an enabled endpoint unless all five have an evidence reference and reviewer. '
        'This is a publishing gate, not a legal-compliance certificate or a live-uptime check.</p>'
        '<div class="tablewrap"><table class="data"><thead><tr><th scope="col">Question</th>'
        '<th scope="col">What we know</th><th scope="col">What is missing</th><th scope="col">How to find out</th>'
        '<th scope="col">Confirmed (UTC) / evidence</th><th scope="col">Official / first-party source</th>'
        '</tr></thead><tbody>' + "".join(launch_rows) + '</tbody></table></div>'
        '<p class="small muted">Unverified hosting and privacy decisions remain open (F-59, F-98). '
        'No host is purchased, no account verification is asserted, and no personal details are requested here.</p></section>'
        '<section><h2>Five site-side counters</h2><p class="section-lead">DNT and Global Privacy Control stop '
        'the sender. Requests omit credentials and Referer; payloads contain only known public page paths, '
        'category paths and catalog ASINs. The application stores daily aggregates, not visitor identifiers. '
        'Hosts, proxies and network services still receive connection metadata: their logging needs a separate '
        'review, and GitHub documents security IP logging for Pages.</p>'
        '<div class="tablewrap"><table class="data"><thead><tr><th scope="col">Event</th><th scope="col">Fires when</th>'
        '<th scope="col">Payload</th><th scope="col">Stored as</th><th scope="col">Source</th></tr></thead><tbody>'
        + ev_rows + '</tbody></table></div>'
        f'<p><strong>Retention:</strong> {_e(rec["retention_status"])}</p>'
        '<p>These are best-effort event counts, not unique people, sessions, search queries, confirmed Amazon '
        'clicks or orders. Ad blockers, opt-outs and delivery failures mean totals can be incomplete; a caller can '
        'also spoof an Origin header. Do not optimize for sales from these counters alone.</p></section>'
        '<section><h2>Five campaign-report event types</h2><p class="section-lead">A different vocabulary '
        'from the site-side counters above. Session, order and refund records require authorised first-party '
        'reports; a browser click never creates them.</p>'
        + five_events_table(ledger) + '</section>'
        '<section><h2>Campaign ledger</h2><p class="section-lead">Empty by design: no authorised report has '
        'been imported. Eligible sessions, reported clicks and orders stay blank. Each future row needs its '
        'timestamp, source, channel, report reference and provenance.</p>'
        + ledger_table + provenance_html(ledger) + f'<p class="small muted">{_e(ledger["status"])}</p></section>'
        '<section><h2>What will choose the next topic?</h2><ol class="bullets">'
        '<li>Verify Search Console and retain a dated first-party query/page report (F-61). '
        'No query popularity or search-volume claim is made here.</li>'
        '<li>After a permitted collector launch, compare query arrivals with category-target clicks and guide '
        'milestones over the same stated period. Counts are not a conversion funnel or a causal experiment.</li>'
        '<li>Record the question, evidence and editorial choice before adding a guide to the existing '
        '14-day cadence, sitemap and feed. Keep reader email capture as a separate privacy decision.</li>'
        '<li>Confirm the tracking ID and one-link-per-product Associates workflow before scaling '
        'or claiming attribution (F-57/F-58). Do not generate artificial affiliate clicks or test purchases.</li>'
        '</ol></section>'
    )


def feed_items(bs) -> list[str]:
    """RSS items for the published guides, appended by scripts/build_site.py to its single feed.

    Each item carries the guide record's own published_utc - 2026-11-17, the day the four guides
    went live - and never a build clock: decision D-49 lets a page state a date only when its own
    record can name the dated source behind it, and the same rule now governs the feed.
    """
    items = []
    for g in published_guides():
        url = bs.SITE_URL + "guides/" + g["slug"] + ".html"
        pub_date = f"    <pubDate>{bs.rfc822(g['published_utc'])}</pubDate>\n" if g.get("published_utc") else ""
        items.append(
            "  <item>\n"
            f"    <title>{_e(g['h1'])}</title>\n"
            f"    <link>{_e(url)}</link>\n"
            f"    <guid isPermaLink=\"true\">{_e(url)}</guid>\n"
            f"    <description>{_e(g['meta_description'])}</description>\n"
            f"{pub_date}"
            "  </item>\n"
        )
    return items


def measurement_client(bs, extra_paths: list[str]) -> str:
    """One client source, compiled with the same public routes/catalog as this build."""
    if MEASUREMENT["site_url"] != bs.SITE_URL:
        raise ValueError("measurement.site_url must match the site's canonical origin and path")
    paths = sorted({p.path for p in bs.collect_pages()} | {p for p in extra_paths if p.endswith(".html")})
    config = {
        "site_url": bs.SITE_URL,
        "paths": paths,
        "guides": [p for p in paths if p.startswith(("guides/", "articles/")) and not p.endswith("/index.html")],
        "categories": [p for p in paths if p.startswith("categories/")],
        "asins": sorted(p["asin"] for p in all_products(bs) if not is_held(p["id"])),
        "tracking_id": _load("intent-links.json")["_meta"]["tracking_id"],
    }
    source = (ROOT / "analytics-endpoint" / "client.js").read_text(encoding="utf-8")
    if source.count("__ZONE4_CONFIG__") != 1:
        raise ValueError("measurement client must have exactly one configuration slot")
    return source.replace("__ZONE4_CONFIG__", json.dumps(config, sort_keys=True, separators=(",", ":")))




# ---------------------------------------------------------------------------
# The review gate (2026-11-19, arena/6792f800-zone4).
# One page where a person can read every proposed change, its cost, its risk and
# the check that proves it worked, beside the questions that must be answered
# before the change is worth making. Nothing on it is applied. Data: data/redesign.json.
# ---------------------------------------------------------------------------

def review_body_for(bs, page) -> str:
    """Public entry point: the builder renders review.html with this body."""
    return _review_body(bs, page)


def _review_body(bs, page) -> str:
    rec = _load("redesign.json")
    suggestions = rec["suggestions"]
    questions = rec["questions"]
    review = rec["review"]
    e = bs.esc

    def pill(kind: str, text: str) -> str:
        return f'<span class="pill pill-{kind}">{e(text)}</span>'

    prio_kind = {"P1": "bad", "P2": "warn", "P3": "muted"}

    def prio(p: str) -> str:
        return f'<span class="prio prio-{e(p.lower())}">{e(p)}</span>'

    def src_list(items) -> str:
        return "".join(
            f'<li>{bs.ext(s["url"], s["ref"])}</li>' for s in items
        )

    counts = {k: sum(1 for s in suggestions if s["priority"].startswith(k)) for k in ("P1", "P2", "P3")}
    legacy = [s for s in suggestions if not str(s.get("batch", "")).startswith("2026-11-20")]
    batch_rows = [s for s in suggestions if str(s.get("batch", "")).startswith("2026-11-20")]
    kpis = (
        '<div class="kpis">'
        f'<div class="kpi"><div class="kpi-value">{len(suggestions)}</div><div class="kpi-label">proposals filed here</div></div>'
        f'<div class="kpi"><div class="kpi-value">{counts["P1"]}</div><div class="kpi-label">P1 · decide first</div></div>'
        f'<div class="kpi"><div class="kpi-value">{len(questions)}</div><div class="kpi-label">questions to answer first</div></div>'
        f'<div class="kpi"><div class="kpi-value">{sum(1 for s in suggestions if s["status"].startswith(("Applied", "Partly")))}</div>'
        f'<div class="kpi-label">shipped or partly shipped</div></div>'
        '</div>'
    )

    flow = "".join(
        f'<li><strong>{e(s["title"])}.</strong> {e(s["what"])}</li>' for s in review["flow"]
    )

    # --- Proposals, grouped by priority, each a card with its evidence.
    def card_html(s):
        prio_key = s["priority"][:2]
        st = s["status"]
        kind = "ok" if st.startswith("Applied") else ("warn" if st.startswith("Partly") else "muted")
        shipped = (
            f'<p class="small"><strong>What shipped on 2026-11-19.</strong> {e(s["shipped_note"])}</p>'
            if s.get("shipped_note") else ""
        )
        flags_cell = " ".join(bs.flag_chip(page, f) for f in s["flags"]) if s["flags"] else "&mdash;"
        return (
            f'<article class="scard" id="{e(s["id"])}">'
            '<div class="scard-head"><div>'
            f'<span class="scard-id">{e(s["id"])}</span>{prio(prio_key)}'
            '</div>'
            f'{pill(kind, st)}'
            '</div>'
            f'<h3>{e(s["title"])}</h3>'
            f'<p class="scard-problem">{e(s["problem"])}</p>'
            f'<p><strong>What we would change.</strong> {e(s["proposal"])}</p>'
            + shipped
            + f'<p><strong>Why it is worth doing.</strong> {e(s["why"])}</p>'
            '<dl class="sgrid">'
            f'<dt>Cost</dt><dd>{e(s["effort"])}</dd>'
            f'<dt>Risk</dt><dd>{e(s["risk"])}</dd>'
            f'<dt>How you would know it worked</dt><dd>{e(s["check"])}</dd>'
            '</dl>'
            f'<p class="scard-foot"><span>Reserved decision: {e(s["decision"])} '
            '(not written to the decision log until you record a choice)</span>'
            f'<span>Flags: {flags_cell}</span></p>'
            f'<ul class="scard-src">{src_list(s["sources"])}</ul>'
            '</article>'
        )

    cards = []
    for prio_key, heading, lead in (
        ("P1", "P1 · Decide first",
         "These decide whether the rest can work. The first is the tracking-ID test: without it no click can be attributed and no design change earns anything."),
        ("P2", "P2 · Then",
         "High-value presentation and trust work that depends on the P1 answers."),
        ("P3", "P3 · Later",
         "Polish and measurement that is worth doing once the shop reads right."),
    ):
        group = [s for s in legacy if s["priority"].startswith(prio_key)]
        if not group:
            continue
        items = [card_html(s) for s in group]
        cards.append(
            f'<section><h2>{e(heading)}</h2><p class="section-lead">{e(lead)}</p>'
            f'<div class="scards">{"".join(items)}</div></section>'
        )

    # --- The 2026-11-20 batch: the design prompt, organic traffic, anti-slop.
    if batch_rows:
        batch_cards = "".join(card_html(s) for s in batch_rows)
        prompt_lines = [s["prompt_line"] for s in batch_rows if s.get("prompt_line")]
        prompt_block = (
            "Design a warm kitchen buying publication: a benefit-led H1 naming the reader's dinner, "
            "one primary comparison action, a two-line trust row, warm editorial imagery separated from "
            "listing photography, serif display type with a readable body, the disclosure strip above the "
            "fold, a seasonal slot below the fold, and mobile order heading, actions, art.\n\n"
            + "\n".join(f"- {line}" for line in prompt_lines)
            + "\n\nNever: a method statement as the headline, invented prices/ratings/volumes, copied listing photography, or a buried disclosure."
        )
        prompt_list = "".join(f"<li>{e(line)}</li>" for line in prompt_lines)
        cards.append(
            '<section id="polish-batch"><h2>The 2026-11-20 batch — the design prompt, organic traffic and anti-slop</h2>'
            '<p class="section-lead">Twelve proposals filed by arena/97ff545d-zone4 in answer to the owner brief: suggestions '
            'that feed the site-design prompt, trendy question-shaped topics under a dated validation rule, cluster '
            'architecture, an anti-slop gate, freshness, measurement-first ordering, structured data, distribution, '
            'reader capture, decision receipts, a humanised storefront and an adjacent-niche scorecard. None of these '
            'rows is applied. The matching questions (RQ-14 to RQ-25) are in the table below.</p>'
            f'<div class="scards">{batch_cards}</div></section>'
            '<section id="design-prompt-lines"><h2>Design-prompt-ready lines</h2>'
            '<p class="section-lead">One paste-ready consolidated prompt, assembled from the twelve lines above. Reviewers '
            'strike what they reject; whatever survives goes into the design conversation verbatim.</p>'
            f'<ol class="steps">{prompt_list}</ol>'
            f'<div class="aiwrap"><pre>{e(prompt_block)}</pre></div></section>'
        )

    # --- The questions that gate the proposals.
    q_rows = []
    for q in questions:
        q_rows.append([
            f'<span class="mono">{e(q["id"])}</span><div class="small muted">{e(q["area"])}</div>',
            f'<strong>{e(q["question"])}</strong><div class="small">{e(q["why_it_matters"])}</div>'
            f'<div class="small muted">Gates: {e(q["blocks"])}</div>',
            f'{e(q["known"])}<div class="small muted"><strong>Still missing:</strong> {e(q["missing"])}</div>',
            f'{e(q["who"])}<div class="small muted">{e(q["discover"])}</div>',
            "<br>".join(bs.ext(s["url"], s["ref"]) for s in q["sources"]),
        ])
    q_table = bs.table(
        ["Question", "What is already known", "Still missing", "Who can answer it, and how", "Official source"],
        q_rows, "data")

    # --- The register map: what lives where, so nobody edits the wrong file.
    # Rendered as a list, not a table: the site's rule is that every table body row
    # carries a link to an official source, and these rows describe this repository.
    su = _load("suggestions.json")["suggestions"]
    qu = _load("questions.json")["questions"]
    de = _load("decisions.json")["decisions"]
    fl = _load("flags.json")["flags"]
    register_rows = [
        ("The five-format shop question", "Which air fryer fits my kitchen and my cooking: one hub page with the chooser first and a verdict per reader situation (RD-14)", "New P1 proposal"),
        ("This page (data/redesign.json)",
         f"{len(suggestions)} proposals and {len(questions)} questions, each with cost, risk, check and an official source",
         "Proposed \u2014 awaiting your decision"),
        ("Suggestions (data/suggestions.json)", f"The {len(su)} earlier suggestions, each with its recorded status",
         "Unchanged by this pass"),
        ("Questions (data/questions.json)", f"The {len(qu)} earlier questions", "Unchanged by this pass"),
        ("Decision log (data/decisions.json)",
         f"The {len(de)} decisions: {sum(1 for d in de if d['status'] == 'Recorded')} recorded, "
         f"{sum(1 for d in de if d['status'].startswith('Open'))} open",
         "Unchanged \u2014 D-62 to D-73 are reserved for the 2026-11-20 batch, not written (D-48 DIR-A presentation layer, D-49 per-article date rule, D-50 thermometer calendar, D-51 owner-actions panel, D-52 gift-window cadence, D-53 safe storefront polish — all recorded 2026-11-19)"),
        ("Flagged for review (data/flags.json)",
         f"The {len(fl)} open, corrected, resolved and historical items", "Unchanged by this pass"),
    ]
    register_list = '<ul class="bullets">' + "".join(
        f'<li><strong>{e(name)}</strong> \u2014 {e(holds)}. <span class="pill pill-muted">{e(state)}</span></li>'
        for name, holds, state in register_rows
    ) + "</ul>"

    return (
        bs.hero("Review: what we would change, and what must be answered first",
                "A shop is judged in the first screen and earns in the last. This page is the single place "
                "to review both: the presentation and growth proposals that would make this site read like a "
                "publication, and the questions that have to be answered before any of them is worth building.")
        + kpis
        + '<section><h2>How to use this page</h2>'
        + f'<p class="section-lead">Four steps. Step one takes ten minutes: {len(suggestions)} proposals, '
          'each with the problem it solves and the check that proves it worked.</p>'
        + '<ol class="steps">' + flow + '</ol>'
        + f'<p class="aiwrap">{e(review["note"])}</p></section>'
        + "".join(cards)
        + '<section id="questions"><h2>The questions that come before the build</h2>'
        f'<p class="section-lead">{len(questions)} questions, kept short on purpose. Each records what is already known, '
        'what is missing, who can supply it and how to find out. Where a default exists it is named in the '
        'discovery step, so leaving a question unanswered is still a recorded decision rather than a gap.</p>'
        + q_table + "</section>"
        + '<section><h2>Which register holds what</h2>'
        '<p class="section-lead">The review gate only works if the registers cannot drift apart. This pass '
        'files its proposals in their own register so the counts published elsewhere stay correct.</p>'
        + register_list + "</section>"
        + '<section id="superseded"><h2>' + e(review["superseded"]["title"]) + "</h2>"
        + f'<p class="section-lead">{e(review["superseded"]["note"])}</p>'
        + bs.table(["Register", "Row", "What its headline still says", "What is true after 2026-11-19",
                    "Official source"],
                   [[f'<span class="mono">{e(r["register"])}</span>', f'<span class="mono">{e(r["id"])}</span>',
                     e(r["still_says"]), e(r["current_state"]),
                     bs.ext("https://affiliate-program.amazon.com/help/operating/policies", "Program Policies 2(b)")]
                    for r in review["superseded"]["rows"]], "data")
        + "</section>"
        + '<section><h2>The shortest credible path</h2>'
        '<p class="aiwrap">Answer RQ-02 first: sign in to Associates Central and confirm that '
        '<span class="mono">shopnow047c-20</span> is listed and active, then click one Special Link per product '
        'and check the report after 24 to 48 hours (the five steps are in <a href="'
        + e(page.rel("links.html")) + '">the product-intent record</a>). Everything else on this page is '
        'presentation, structure or measurement, and none of it can earn a commission while an unattributed '
        'click is the only thing leaving the site. The second step is the one that makes the shop look like one: '
        'RD-01 and RD-02 together change the first screen and the navigation without touching a single published '
        'value. Sources for both: '
        + bs.ext("https://affiliate-program.amazon.com/help/operating/policies", "Associates Program Policies")
        + ' and '
        + bs.ext("https://developers.google.com/search/docs/fundamentals/creating-helpful-content", "Google Search Central: people-first content")
        + '.</p></section>'
    )



# ---------------------------------------------------------------------------
# Category imagery (2026-11-19, arena/6792f800-zone4).
# A footprint diagram drawn from the dimensions already recorded in
# data/products.json. It is original vector markup generated here - no listing
# image is downloaded, copied or hosted, which is the S-18 / F-43 rule - and it
# carries the values it was drawn from as its caption, so the picture is
# checkable against the same source rows as the tables.
# ---------------------------------------------------------------------------

FOOTPRINT = {
    "dual-basket-air-fryers": {"pid": "P1", "w": 11.81, "d": 13.38},
    "air-fryer-toaster-ovens": {"pid": "P2", "w": 15.8, "d": 16.9},
    "single-basket-air-fryers": {"pid": "P3", "w": 13.5, "d": 12.75},
}


def footprint_svg(category_key: str) -> tuple[str, str]:
    """SVG footprint of one category's product, scaled to a shared axis.

    Returns (svg, caption). The caption repeats the numbers the drawing uses.
    """
    spec = FOOTPRINT.get(category_key)
    if not spec:
        return ("", "")
    p = next(x for x in _load("products.json")["products"] if x["id"] == spec["pid"])
    w, d = spec["w"], spec["d"]
    # Shared scale: 25 inches across, 5px per quarter inch -> 100px per 5in.
    scale = 8.0
    pad = 10
    W, H = int(20 * scale) + 2 * pad, int(20 * scale) + 2 * pad
    rw, rd = w * scale, d * scale
    x, y = (W - rw) / 2, (H - rd) / 2
    svg = (
        f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Footprint diagram: '
        f'{_e(p["name_short"])} is {_e(p["dimensions"])} as listed." '
        'xmlns="http://www.w3.org/2000/svg">'
        f'<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="8" fill="none" stroke="#e7e1d6"/>'
        # 20-inch reference frame, drawn to the same scale as the product
        f'<rect x="{pad}" y="{pad}" width="{20 * scale}" height="{20 * scale}" fill="none" '
        f'stroke="#d9d1c3" stroke-dasharray="4 5"/>'
        f'<text x="{pad + 6}" y="{pad + 15}" font-size="11" fill="#6b6459">20 in reference</text>'
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{rw:.1f}" height="{rd:.1f}" rx="6" '
        'fill="#b45309" fill-opacity="0.18" stroke="#b45309" stroke-width="1.5"/>'
        f'<text x="{W / 2}" y="{H / 2 - 2}" font-size="12" font-weight="700" text-anchor="middle" '
        f'fill="#92400e">{_e(w)}in wide</text>'
        f'<text x="{W / 2}" y="{H / 2 + 14}" font-size="12" text-anchor="middle" '
        f'fill="#92400e">{_e(d)}in deep</text>'
        '</svg>'
    )
    caption = ("Footprint drawn to scale from the listed dimensions: "
               f"{w}in wide by {d}in deep. Source: the product details table on the listing.")
    return (svg, caption)


def footprint_figure(category_key: str) -> str:
    svg, caption = footprint_svg(category_key)
    if not svg:
        return ""
    return (f'<span class="tile-figure">{svg}</span>'
            f'<span class="tile-caption">{_e(caption)}</span>')



def imagery_body_for(bs, page) -> str:
    """The imagery record: every picture on the site, where it came from, and the rule."""
    rec = _load("imagery.json")
    rule = rec["policy"]
    rows = []
    for a in rec["assets"]:
        rows.append([
            bs.esc(a["page"]),
            bs.esc(a["asset"]),
            bs.esc(a["drawn_from"]) or "&mdash;",
            bs.esc(a["alt"]) or "&mdash;",
            bs.esc(a["status"]),
            bs.ext("https://affiliate-program.amazon.com/help/operating/agreement", "Operating Agreement (Program Content)"),
        ])
    table = bs.table(["Where", "What the reader sees", "Drawn from", "Alt text", "Status", "Official source"],
                     rows, "data")
    rule_items = "".join(
        f'<li><strong>{label}:</strong> {bs.esc(value)}</li>'
        for label, value in (
            ("Listing images", rule["listing_images"]),
            ("Generated images", rule["generated_images"]),
            ("Shipped now", rule["shipped_now"]),
        )
    )
    shot = (
        '<div class="cathero"><div class="cathero-figure">'
        + footprint_figure("air-fryer-toaster-ovens")
        + '</div><div class="cathero-lead">'
        + bs.hero("Imagery: every picture on this site, and where it comes from",
                  "A shop needs pictures. This one shows only pictures it can source: original diagrams drawn from "
                  "the dimensions the listings state. Nothing here is downloaded from a listing, and nothing is "
                  "generated to look like the product.")
        + '</div></div>'
    )
    return (
        shot
        + '<section><h2>The rule</h2>'
        + '<p class="aiwrap">Listing photography is Program Content. The Operating Agreement gives the store the '
          'right to the images on its listings; it does not hand that right to a site that copies them, so none is '
          'copied here (suggestion S-18, flag F-43). A generated picture of a real appliance would be worse than no '
          'picture, because it would show something the reader cannot buy. What is left is the honest middle: draw '
          'the one thing a photograph cannot show as clearly as a diagram &mdash; how much counter the appliance '
          'takes.</p>'
        + f'<ul class="bullets">{rule_items}</ul></section>'
        + '<section><h2>Every asset, in one table</h2>'
        + '<p class="section-lead">Each row links the rule it is checked against; the planned row says what it is '
          'waiting for.</p>' + table + "</section>"
        + '<section><h2>What would let a real photograph appear</h2>'
        + '<p class="aiwrap">Either route is an owner decision, not an editorial one: supply original photographs '
          'with a written release, or confirm in writing that the '
        + bs.ext("https://affiliate-program.amazon.com/creatorsapi", "Creators API")
        + " permits live listing images. Both are recorded on the "
        + f'<a href="{bs.esc(page.rel("review.html"))}">Review page</a> as questions RQ-03 and RQ-05.</p></section>'
    )



def register_numbers(bs) -> str:
    """Small, honest counts for the About page: computed, never typed."""
    su = len(_load("suggestions.json")["suggestions"])
    qu = len(_load("questions.json")["questions"])
    de = _load("decisions.json")["decisions"]
    fl = len(_load("flags.json")["flags"])
    rec = sum(1 for d in de if d["status"] == "Recorded")
    return f"{su} suggestions, {qu} questions, {len(de)} decisions ({rec} recorded, {len(de) - rec} open) and {fl} flags"


def about_body_for(bs, page) -> str:
    """Who writes this, how it is made, what it will not say, and how to correct it."""
    editorial = (_load("content.json").get("editorial") or {})
    # Reuse the repository's own published position statement; fall back to the
    # build gate's rule if that statement ever moves.
    promise = editorial.get("promise") or []
    method = " ".join(promise) if promise else (
        "Each page is drafted with automated assistance, then every factual value is read from the official listing "
        "or policy page and recorded as a dated row in data/. A value that cannot be read is left blank and flagged.")
    corr = editorial.get("corrections") or (
        "Send a correction with the URL and the listing or policy page that contradicts it. A corrected value is "
        "re-read from the official page and the row keeps its new date; nothing is silently overwritten.")
    sections = [
        '<section><h2>What this site is</h2>',
        '<p class="aiwrap">Zone4 is a small buying guide for countertop air fryers and, since the 2026-11-19 brief, '
        'two submitted meat-thermometer listings. It covers a handful of products rather than a catalogue, and it '
        'writes about the specification fields a shopper can check against the listing: capacity, footprint, basket '
        'format and the features the page names.</p>',
        '<p class="aiwrap">It earns through the Amazon Associates programme. Every outbound product link is a tagged '
        'Special Link, carries rel=&quot;sponsored&quot;, and sits next to the disclosure sentence that also appears '
        'under the masthead and in every footer.</p></section>',
        '<section><h2>How the content is produced</h2>',
        f'<p class="aiwrap">{bs.esc(method)}</p>',
        '<p class="aiwrap">The site publishes with automated assistance and says so here rather than in a footnote. '
        'What the automation does not do is invent a number: the build refuses to publish a table row without an '
        'official source link, and the checks in the repository fail if one appears.</p></section>',
        '<section><h2>What it will not publish</h2><ul class="bullets">',
        '<li><strong>Prices and star ratings</strong>, until an approved API supplies them (flag F-02).</li>',
        '<li><strong>Per-product commission rates</strong>, because no official source maps these listings to a '
        'commission category (flag F-01).</li>',
        '<li><strong>Hands-on test results.</strong> Nobody here has cooked in these appliances, and the site does '
        'not pretend otherwise.</li>',
        '<li><strong>Trend or popularity claims.</strong> A claim like that needs a dated official snapshot, and none '
        'exists (decision D-19, flag F-15).</li>',
        '<li><strong>Forecasts</strong> of traffic, orders or revenue. The programme makes no representation about '
        'any of them.</li></ul></section>',
        '<section><h2>Corrections</h2>',
        f'<p class="aiwrap">{bs.esc(corr)}</p>',
        '<p class="aiwrap">Every published value, the page it was read from and the date of the read are listed on '
        f'the {bs.href(page, "verification.html", "verification log")}; anything that could not be confirmed is on '
        f'the {bs.href(page, "flagged.html", "Flagged for review")} page.</p></section>',
        '<section><h2>How the site is governed</h2>',
        f'<p class="aiwrap">The editorial and technical backlog is public: {bs.esc(register_numbers(bs))}. The two '
        f'review surfaces are the {bs.href(page, "review.html", "Review page")} (the proposals and the questions '
        f'that gate them) and the {bs.href(page, "decision-centre.html", "Decision centre")} (the same registers in '
        'review order).</p></section>',
    ]
    return (
        bs.hero("About this site",
                "Who writes it, how each number is checked, what it deliberately will not publish, and how to "
                "correct it.")
        + "".join(sections)
    )


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
                   title_tag="Buying guides: answers from the listings",
                   head_extra=bs.breadcrumb_ld([("Home", "index.html"), ("Guides", "guides/index.html")]))
    page.body = _guide_page_body_index(bs, page, guides)
    (out / "guides/index.html").write_text(bs.render(page), encoding="utf-8")
    written.append("guides/index.html")

    for g in guides:
        path = "guides/" + g["slug"] + ".html"
        page = bs.Page(path, g["h1"], path, "", description=g["meta_description"], title_tag=g["title_tag"],
                       head_extra=_article_ld(bs, g) + bs.breadcrumb_ld(
                           [("Home", "index.html"), ("Guides", "guides/index.html"), (g["h1"], path)]))
        page.body = _guide_body(bs, page, g)
        (out / path).write_text(bs.render(page), encoding="utf-8")
        written.append(path)

    # The meat-thermometer category (decision D-46): its two listings are published; its guide waits for the cadence.
    tpath = "categories/meat-thermometers.html"
    page = bs.Page(tpath, "Meat thermometers", tpath, "",
                   description="Meat thermometers: the two submitted listings, with the title and category breadcrumb each page states, and the claims as titled.",
                   title_tag="Meat thermometers: the two listings",
                   head_extra=bs.breadcrumb_ld([("Home", "index.html"), ("All products", "products.html"),
                                                ("Meat thermometers", tpath)]))
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

    # review.html is rendered by scripts/build_site.py (it is part of the shared
    # navigation and needs the page shell); its body comes from review_body_for().
    (out / "review.html").write_text("", encoding="utf-8")
    written.append("review.html")
    (out / "about.html").write_text("", encoding="utf-8")
    written.append("about.html")
    (out / "imagery.html").write_text("", encoding="utf-8")
    written.append("imagery.html")

    # feed.xml is written by scripts/build_site.py, which owns the one RSS feed (guides are added there).
    (out / "measure.js").write_text(measurement_client(bs, written), encoding="utf-8")
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
