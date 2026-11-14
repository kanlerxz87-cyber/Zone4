#!/usr/bin/env python3
"""Verify the data and the built site. Exits non-zero on any failure.

Checks:
  1. data/*.json: ASIN format; canonical URL matches ASIN; short links on link.amazon;
     every flag reference exists; every source URL is on an official host.
  2. docs/*.html: every internal link and #anchor resolves; the Associates disclosure
     sentence appears on every page; every table body row contains a link to an
     official host; no Amazon price or star rating is published.
Standard library only. No network access is needed.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"

OFFICIAL_HOSTS = {
    "www.amazon.com", "amazon.com", "link.amazon",
    "affiliate-program.amazon.com", "www.ftc.gov", "api.github.com", "github.com",
}
DISCLOSURE = "As an Amazon Associate I earn from qualifying purchases."
# Phrases that only exist in Amazon's own page furniture. Publishing them would reuse
# Amazon-displayed sales, badge or review data (Participation Requirements 6(t), flag F-15).
FORBIDDEN_MARKETING_PHRASES = [
    "Amazon's Choice", "Best Sellers Rank", "bought in past month", "Top Brand:", "Limited time deal",
    "protection plan", "Asurion",
]
# Claiming to have used a product needs FTC substantiation this site does not have (rule R-25).
TESTING_CLAIM_RE = re.compile(
    r"\b(?:we|i)\s+(?:have\s+)?(?:tested|tried|used|reviewed)\b|"
    r"\b(?:our|my)\s+(?:test|testing|review|hands[- ]on)\b|\bafter\s+\d+\s+(?:weeks?|months?)\s+of\s+use\b",
    re.IGNORECASE,
)
ASIN_RE = re.compile(r"^B[0-9A-Z]{9}$")
# Any money figure breaks Participation Requirements 2(b) / flag F-02, whether written with a
# symbol, spelled out, or attached to the words price/cost/discount.
PRICE_RE = re.compile(
    r"\$\s?\d|\bdollars?\b|\bUSD\b|\b€\s?\d|\b£\s?\d|\b(?:price|prices|cost|costs|discount|savings)\s+(?:of\s+)?[\$€£]?\s*\d"
)
RATING_RE = re.compile(r"\b\d\.\d\s*(out of 5|stars?)\b", re.IGNORECASE)

AMAZON_DISCLAIMER = json.loads((DATA / "content.json").read_text(encoding="utf-8"))[
    "amazon_text_disclaimer"]["text"]
content_disclaimer = " ".join(AMAZON_DISCLAIMER.split())

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def check_data() -> None:
    products = load("products.json")["products"]
    flags = {f["id"] for f in load("flags.json")["flags"]}
    sources = load("sources.json")
    for src in sources["sources"]:
        host = urlparse(src["url"]).hostname or ""
        if host not in OFFICIAL_HOSTS:
            fail(f"source {src['id']} is not on an official host: {src['url']}")
    for rule in load("policies.json")["rules"]:
        host = urlparse(rule["source_url"]).hostname or ""
        if host not in OFFICIAL_HOSTS:
            fail(f"policy {rule['id']} source is not official: {rule['source_url']}")
    for f in load("flags.json")["flags"]:
        for u in f["sources"]:
            if (urlparse(u).hostname or "") not in OFFICIAL_HOSTS:
                fail(f"flag {f['id']} has a non-official source: {u}")
    for p in products:
        if not ASIN_RE.match(p["asin"]):
            fail(f"{p['id']}: ASIN malformed: {p['asin']}")
        if p["canonical_url"] != f"https://www.amazon.com/dp/{p['asin']}":
            fail(f"{p['id']}: canonical URL does not match ASIN")
        if urlparse(p["short_link"]).hostname != "link.amazon":
            fail(f"{p['id']}: short link is not on link.amazon")
        for c in p["competitors"]:
            if not ASIN_RE.match(c["asin"]):
                fail(f"{p['id']}: competitor ASIN malformed: {c['asin']}")
        for fid in p["flags"]:
            if fid not in flags:
                fail(f"{p['id']}: unknown flag {fid}")
    content = load("content.json")
    for a in content["analysis"]:
        for u in a["sources"]:
            if (urlparse(u).hostname or "") not in OFFICIAL_HOSTS:
                fail(f"analysis {a['id']} has a non-official source: {u}")
    flag_ids = {f["id"] for f in load("flags.json")["flags"]}
    rule_ids = {r["id"] for r in load("policies.json")["rules"]}
    for text in json.dumps(content, ensure_ascii=False), json.dumps(load("products.json"), ensure_ascii=False):
        for ref in set(re.findall(r"\bF-\d{2}\b", text)):
            if ref not in flag_ids:
                fail(f"data references flag {ref}, which does not exist in data/flags.json")
        for ref in set(re.findall(r"\bR-\d{2}\b", text)):
            if ref not in rule_ids:
                fail(f"data references rule {ref}, which does not exist in data/policies.json")
    ids = {p["id"] for p in products}
    mkt = content["marketing"]
    for art in mkt["articles"]:
        if art["product_id"] not in ids:
            fail(f"marketing draft {art['id']} points at unknown product {art['product_id']}")
        for sec in art["sections"]:
            for para in sec["paras"]:
                if not para.get("source"):
                    fail(f"marketing draft {art['id']} section '{sec['heading']}' has an unsourced sentence")
                elif (urlparse(para["source"]).hostname or "") not in OFFICIAL_HOSTS:
                    fail(f"marketing draft {art['id']} cites a non-official source: {para['source']}")
    for art in mkt["articles"] + [mkt["comparison"], mkt["buying_guide"]]:
        for field in ("seo_title", "meta_description", "slug"):
            if not art.get(field):
                fail(f"marketing draft {art['id']} is missing SEO field {field}")
        if len(art.get("seo_title", "")) > 65:
            fail(f"marketing draft {art['id']} SEO title exceeds 65 characters ({len(art['seo_title'])})")
        if len(art.get("meta_description", "")) > 160:
            fail(f"marketing draft {art['id']} meta description exceeds 160 characters ({len(art['meta_description'])})")
    cmp_ = mkt["comparison"]
    width = len(cmp_["columns"]) - 1
    for row in cmp_["rows"]:
        if len(row["values"]) != width:
            fail(f"comparison row has {len(row['values'])} values, expected {width}")
        if (urlparse(row["source"]).hostname or "") not in OFFICIAL_HOSTS:
            fail(f"comparison row links to a non-official source: {row['source']}")
    for q in content["requirements"]:
        if not q.get("status") or not q.get("delivered") or not q.get("blocker"):
            fail(f"requirement {q['id']} is missing status, delivered text or blocker")
        if (urlparse(q.get("evidence_url", "")).hostname or "") not in OFFICIAL_HOSTS:
            fail(f"requirement {q['id']} evidence is not on an official host: {q.get('evidence_url')}")
    for x in content["platform"]["stages"]:
        if (urlparse(x["source"]).hostname or "") not in OFFICIAL_HOSTS:
            fail(f"platform stage '{x['stage']}' gate source is not official: {x['source']}")
    for chk in content["reverification"]["checks"]:
        if not chk.get("expected") or not chk.get("result"):
            fail(f"re-verification check {chk['id']} is missing the expected value or the observation")
        if (urlparse(chk["source"]).hostname or "") not in OFFICIAL_HOSTS:
            fail(f"re-verification check {chk['id']} cites a non-official source: {chk['source']}")
    if not content.get("amazon_text_disclaimer", {}).get("text"):
        fail("content.json is missing the IP License 2(k) content disclaimer required in plain view (rule R-20)")


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[tuple[str, str]] = []  # (tag, url)
        self.in_tbody = False
        self.row_links: list[list[str]] | None = None
        self.bad_rows: list[int] = []
        self.rows = 0
        self.text_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag in ("a", "link") and a.get("href"):
            self.links.append((tag, a["href"]))
        if tag == "script" and a.get("src"):
            self.links.append((tag, a["src"]))
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.row_links = []
            self.rows += 1
        if tag == "a" and self.row_links is not None and a.get("href"):
            self.row_links.append(a["href"])

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_tbody = False
        if tag == "tr" and self.row_links is not None:
            if not any((urlparse(h).hostname or "") in OFFICIAL_HOSTS for h in self.row_links):
                self.bad_rows.append(self.rows)
            self.row_links = None

    def handle_data(self, data):
        self.text_parts.append(data)


def check_site() -> None:
    pages = sorted(DOCS.rglob("*.html"))
    if not pages:
        fail("docs/ has no HTML pages; run scripts/build_site.py")
        return
    parsed: dict[pathlib.Path, SiteParser] = {}
    for page in pages:
        sp = SiteParser()
        sp.feed(page.read_text(encoding="utf-8"))
        parsed[page] = sp
        rel = page.relative_to(ROOT)
        if DISCLOSURE not in " ".join(sp.text_parts):
            fail(f"{rel}: disclosure sentence missing")
        for bad in sp.bad_rows:
            fail(f"{rel}: table row {bad} has no link to an official source")
        raw = page.read_text(encoding="utf-8")
        if PRICE_RE.search(re.sub(r"<[^>]+>", " ", raw)):
            fail(f"{rel}: contains a currency amount (Amazon prices are withheld under Participation Requirements 2(b))")
        if content_disclaimer not in " ".join(sp.text_parts):
            fail(f"{rel}: the IP License 2(k) content disclaimer is missing from this page (rule R-20)")
        # flagged.html documents which Amazon-displayed figures are withheld, so it may name them;
        # no content page may. Any other page that quotes them fails the build.
        if page.name != "flagged.html":
            for phrase in FORBIDDEN_MARKETING_PHRASES:
                if phrase.lower() in " ".join(sp.text_parts).lower():
                    fail(f"{rel}: reuses Amazon page furniture '{phrase}' (sales, badge or review data, flag F-15)")
        hit = TESTING_CLAIM_RE.search(" ".join(sp.text_parts)) if page.name != "flagged.html" else None
        if hit:
            fail(f"{rel}: claims product testing or first-hand use ('{hit.group(0).strip()}'), which FTC Disclosures 101 bars without it (rule R-25)")
        if RATING_RE.search(raw):
            fail(f"{rel}: contains a star rating (withheld under Participation Requirements 6(t))")

    for page, sp in parsed.items():
        rel = page.relative_to(ROOT)
        for tag, url in sp.links:
            parsed_url = urlparse(url)
            if parsed_url.scheme in ("http", "https"):
                if (parsed_url.hostname or "") not in OFFICIAL_HOSTS:
                    fail(f"{rel}: link to non-official host: {url}")
                continue
            if parsed_url.scheme or url.startswith("mailto:"):
                fail(f"{rel}: unsupported link scheme: {url}")
                continue
            target_path = (page.parent / parsed_url.path).resolve() if parsed_url.path else page
            if not target_path.exists():
                fail(f"{rel}: broken link {url}")
                continue
            if parsed_url.fragment:
                target = parsed[target_path] if target_path in parsed else None
                if target is None or parsed_url.fragment not in target.ids:
                    fail(f"{rel}: anchor not found: {url}")


def check_navigation_and_withheld_columns() -> None:
    """Every generated page must be reachable, and the withheld columns must stay visible."""
    pages = sorted(DOCS.rglob("*.html"))
    total = len(pages)
    for page in pages:
        txt = page.read_text(encoding="utf-8")
        nav = re.search(r'<nav aria-label="Main">(.*?)</nav>', txt, re.S)
        if not nav:
            fail(f"{page.relative_to(ROOT)}: no main navigation block")
            continue
        links = re.findall(r'<a href="([^"]+)"', nav.group(1))
        for target in links:
            clean = target.split("#")[0]
            if clean and not (page.parent / clean).exists():
                fail(f"{page.relative_to(ROOT)}: nav link is broken: {target}")
        if len(links) != total:
            fail(f"{page.relative_to(ROOT)}: the sidebar lists {len(links)} of {total} pages")
    prod = (DOCS / "products.html").read_text(encoding="utf-8")
    for col in ("Price", "Star rating", "Commission rate", "Trend / conversion"):
        if col not in prod:
            fail(f"products.html dropped the '{col}' column; withheld and unverified fields must stay visible")
    if prod.count("Withheld (F-02)") < 6:
        fail("products.html should mark the price and rating columns as withheld on all three rows")


def check_root_entry() -> None:
    """GitHub Pages serves the repo root (legacy source). The root must redirect to docs/."""
    idx = ROOT / "index.html"
    if not idx.exists():
        fail("root index.html missing: Pages source is main / and needs a redirect to docs/")
        return
    text = idx.read_text(encoding="utf-8")
    if "docs/index.html" not in text:
        fail("root index.html does not redirect to docs/index.html")
    if not (ROOT / ".nojekyll").exists():
        fail("root .nojekyll missing")


def main() -> int:
    check_data()
    check_site()
    check_navigation_and_withheld_columns()
    check_root_entry()
    if failures:
        print(f"FAILED: {len(failures)} problem(s)")
        for f in failures:
            print(" -", f)
        return 1
    n_pages = len(list(DOCS.rglob('*.html')))
    print(f"OK: data files valid; {n_pages} pages checked: links, anchors, disclosure, row sources, no prices or ratings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
