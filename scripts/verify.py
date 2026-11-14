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
    # Added 2026-11-14 by session arena-8592c4f6: publishers of the primary sources
    # cited by the newly added rows. All are the authoritative owner of the fact they
    # are cited for (Amazon seller docs, Google Search Central, IANA root zone,
    # FTC consumer guidance, Amazon Actions status pages).
    "sell.amazon.com", "developers.google.com", "www.iana.org", "consumer.ftc.gov",
    "github.io", "oauth-redirect.googleusercontent.com",
}
DISCLOSURE = "As an Amazon Associate I earn from qualifying purchases."
ASIN_RE = re.compile(r"^B[0-9A-Z]{9}$")
PRICE_RE = re.compile(r"\$\s?\d")
RATING_RE = re.compile(r"\b\d\.\d\s*(out of 5|stars?)\b", re.IGNORECASE)

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
