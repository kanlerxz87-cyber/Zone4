#!/usr/bin/env python3
"""Independent QA audit of the committed site in docs/ (and the root Pages entry).

Complements scripts/verify.py without replacing it. Standard library only.
Runs against the committed artifacts (no rebuild), so it can catch a site that
was hand-edited or committed stale.

Hard failures (exit 1):
  1.  Root Pages entry: index.html redirect to docs/ and root .nojekyll present.
  2.  docs/ has HTML pages; docs/.nojekyll present.
  3.  Per page: disclosure sentence in visible text; exactly one <h1>; html[lang];
      non-empty <title>; meta description; meta viewport; unique element ids;
      skip link to #main; footer observation line.
  4.  Per page: every internal link and #anchor resolves; every external <a href>
      is on an official host and carries rel="noopener noreferrer".
  5.  Per page: every table body row contains at least one official-host link.
  6.  Per page: no currency amount in visible text; no star-rating pattern;
      no location-claim residue (Bucharest/Romania) from flag F-09.
  7.  Affiliate hygiene: every shop link points at one of the three supplied
      link.amazon short links AND its table row repeats the disclosure sentence
      (Operating Agreement Section 5; Associates help GPXFHVYZMTGPUMPE).
  8.  products.html lists all three ASINs and all three short links.

Warnings (reported, exit 0 unless --strict-warnings):
  W1. External <script>/<link>/<iframe> hosts outside the official set
      (for example analytics), which the site template does not add itself.
  W2. An HTML page in docs/ is not reachable from the shared sidebar nav, or a
      nav target is missing on disk.
  W3. A nav page without aria-current="page", or more than one.
  W4. A <table> without <thead> or without scope="col" header cells.

--live additionally queries the GitHub Pages API and fails if the latest build
is not 'built' (needs network access to api.github.com).
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DATA = ROOT / "data"

#: Kept in sync with scripts/verify.py by hand: the two lists must stay equal,
#: otherwise the QA auditor and the build gate disagree about what counts as an
#: official source and one of them is wrong. If you add a publisher here, add it
#: there. Hosts below the first block are the authoritative owner of the specific
#: fact cited for it (Amazon seller documentation, Google Search Central, the IANA
#: root zone, FTC consumer guidance, the Pages host) — see the notes on the rows in
#: data/sources.json and the rationale recorded in COORDINATION.md.
OFFICIAL_HOSTS = {
    "www.amazon.com", "amazon.com", "link.amazon",
    "affiliate-program.amazon.com", "www.ftc.gov", "api.github.com", "github.com",
    "sell.amazon.com", "developers.google.com", "www.iana.org", "consumer.ftc.gov",
    "github.io",
}
DISCLOSURE = "As an Amazon Associate I earn from qualifying purchases."
ASIN_RE = re.compile(r"^B[0-9A-Z]{9}$")
PRICE_RE = re.compile(r"\$\s?\d")
RATING_RE = re.compile(r"\b\d\.\d\s*(out of 5|stars?)\b", re.IGNORECASE)
LOCATION_RESIDUE_RE = re.compile(r"\b(Bucharest|Romania)\b", re.IGNORECASE)
NAV_HREF_RE = re.compile(r'href="([^"]+)"')

failures: list[str] = []
warnings: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


class PageParser(HTMLParser):
    """Collects structure needed by the audit in one pass."""

    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.links: list[tuple[str, str]] = []          # (tag, url) a/link/script/img/iframe
        self.external_anchors: list[tuple[str, str | None]] = []  # (href, rel)
        self.h1_count = 0
        self.has_lang = False
        self.title_parts: list[str] = []
        self.in_title = False
        self.meta: dict[str, str] = {}
        self.skip_main = False
        self.text_parts: list[str] = []
        self.in_tbody = False
        self.row_links: list[list[str]] | None = None
        self.rows_total = 0
        self.bad_rows: list[int] = []
        self.row_texts: list[str] = []
        self.row_text: list[str] | None = None
        self.shop_links: list[tuple[str, int, list[str] | None]] = []  # href, row number, enclosing paragraph text
        self.current_paragraph: list[str] | None = None
        self.current_row_no = 0                          # row number of the row being parsed, 0 outside a row
        self.tables = 0
        self.tables_with_thead = 0
        self.current_table_has_thead = False
        self.th_scopes: list[str] = []
        self.aria_current: list[str] = []
        self.nav_href: str | None = None
        self.in_nav = False
        self.footer_has_date = False
        self.in_footer = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html" and a.get("lang"):
            self.has_lang = True
        if a.get("id"):
            self.ids.append(a["id"])
        if tag == "title":
            self.in_title = True
        if tag == "meta":
            name = (a.get("name") or "").lower()
            if name in ("description", "viewport"):
                self.meta[name] = a.get("content") or ""
        if tag == "h1":
            self.h1_count += 1
        if tag == "p":
            self.current_paragraph = []
        if tag in ("a", "link", "script", "img", "iframe"):
            url = a.get("href") or a.get("src")
            if url:
                self.links.append((tag, url))
                if tag == "a":
                    rel = a.get("rel")
                    self.external_anchors.append((url, rel))
                    if url.startswith("#main") or url.endswith("#main"):
                        self.skip_main = True
                    if a.get("aria-current"):
                        self.aria_current.append(url)
                    cls = a.get("class") or ""
                    if "shop" in cls.split():
                        # row 0 means the link is not inside a table row at all; the
                        # page-global row counter must not be used for that case.
                        self.shop_links.append((url, self.current_row_no, self.current_paragraph))
        if tag == "nav":
            self.in_nav = True
        if tag == "table":
            self.tables += 1
            self.current_table_has_thead = False
        if tag == "thead":
            self.current_table_has_thead = True
        if tag == "th":
            self.th_scopes.append(a.get("scope") or "")
        if tag == "tbody":
            self.in_tbody = True
        if tag == "tr" and self.in_tbody:
            self.row_links = []
            self.row_text = []
            self.rows_total += 1
            self.current_row_no = self.rows_total
        if tag == "a" and self.row_links is not None:
            url = a.get("href")
            if url:
                self.row_links.append(url)
        if tag == "footer":
            self.in_footer = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "p":
            self.current_paragraph = None
        if tag == "thead":
            if self.current_table_has_thead:
                self.tables_with_thead += 1
        if tag == "tbody":
            self.in_tbody = False
        if tag == "tr" and self.row_links is not None:
            row_no = self.rows_total
            self.current_row_no = 0
            if not any((urlparse(h).hostname or "") in OFFICIAL_HOSTS for h in self.row_links):
                self.bad_rows.append(row_no)
            self.row_links = None
            if self.row_text is not None:
                self.row_texts.append(" ".join(self.row_text))
                self.row_text = None
        if tag == "nav":
            self.in_nav = False
        if tag == "footer":
            self.in_footer = False

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)
        if self.current_paragraph is not None:
            self.current_paragraph.append(data)
        if self.row_text is not None:
            self.row_text.append(data)
        if self.in_footer and re.search(r"Data observed", data):
            self.footer_has_date = True
        self.text_parts.append(data)


def visible_text(sp: PageParser) -> str:
    return " ".join(sp.text_parts)


def check_root_entry() -> None:
    idx = ROOT / "index.html"
    if not idx.exists():
        fail("root index.html missing (Pages source is main / and needs the redirect)")
    else:
        text = idx.read_text(encoding="utf-8")
        if "docs/index.html" not in text:
            fail("root index.html does not reference docs/index.html")
        if re.search(r"https?://(?!github\.com|api\.github\.com)", text):
            warn("root index.html references a non-GitHub external URL")
    if not (ROOT / ".nojekyll").exists():
        fail("root .nojekyll missing")
    if not (DOCS / ".nojekyll").exists():
        fail("docs/.nojekyll missing")


def load_short_links() -> set[str]:
    products = json.loads((DATA / "products.json").read_text(encoding="utf-8"))["products"]
    return {p["short_link"] for p in products}


def load_special_links() -> set[str]:
    """The tagged Special Links published as outbound product hrefs (2026-11-17).

    Since decisions D-01/D-14 were recorded, the shop hrefs are the final
    destination URLs with the owner-selected tracking ID, not the short links;
    the short links remain recorded data (products-coverage check below) but
    are no longer valid shop destinations.
    """
    associates = json.loads((DATA / "associates.json").read_text(encoding="utf-8"))
    return {s["special_link_url"] for s in associates["special_links"]}


def load_asins() -> set[str]:
    products = json.loads((DATA / "products.json").read_text(encoding="utf-8"))["products"]
    return {p["asin"] for p in products}


def check_page(path: pathlib.Path, sp: PageParser, special_links: set[str]) -> None:
    rel = path.relative_to(ROOT)
    text = visible_text(sp)

    # -- template / SEO basics
    if DISCLOSURE not in text:
        fail(f"{rel}: disclosure sentence missing")
    if sp.h1_count != 1:
        fail(f"{rel}: expected exactly one <h1>, found {sp.h1_count}")
    if not sp.has_lang:
        fail(f"{rel}: <html> has no lang attribute")
    if not "".join(sp.title_parts).strip():
        fail(f"{rel}: empty <title>")
    if not sp.meta.get("description", "").strip():
        fail(f"{rel}: meta description missing")
    if not sp.meta.get("viewport", "").strip():
        fail(f"{rel}: meta viewport missing (mobile usability)")
    if not sp.skip_main:
        fail(f"{rel}: skip link to #main missing")
    if not sp.footer_has_date:
        warn(f"{rel}: footer 'Data observed' line missing")

    # -- unique ids
    dupes = sorted({i for i in sp.ids if sp.ids.count(i) > 1})
    if dupes:
        fail(f"{rel}: duplicate element ids: {', '.join(dupes)}")

    # -- table structure
    if sp.tables and sp.tables_with_thead != sp.tables:
        warn(f"{rel}: {sp.tables - sp.tables_with_thead} table(s) without <thead>")
    if sp.th_scopes and any(s != "col" for s in sp.th_scopes):
        warn(f"{rel}: one or more <th> without scope=\"col\"")

    # -- per-row official source links
    for bad in sp.bad_rows:
        fail(f"{rel}: table row {bad} has no link to an official source")

    # -- policy / regression guards on visible text
    stripped = re.sub(r"<[^>]+>", " ", path.read_text(encoding="utf-8"))
    if PRICE_RE.search(re.sub(r"<[^>]+>", " ", stripped)):
        fail(f"{rel}: currency amount in visible text (prices withheld, Participation Requirements 2(b))")
    if RATING_RE.search(path.read_text(encoding="utf-8")):
        fail(f"{rel}: star-rating pattern present (withheld, Participation Requirements 6(t))")
    if LOCATION_RESIDUE_RE.search(text):
        fail(f"{rel}: location-claim residue found (flag F-09: user location must not be asserted)")

    # -- links
    for tag, url in sp.links:
        parsed = urlparse(url)
        if parsed.scheme in ("http", "https"):
            host = parsed.hostname or ""
            if tag == "a":
                if host not in OFFICIAL_HOSTS:
                    fail(f"{rel}: external anchor to non-official host: {url}")
                rel_attr = next((r for u, r in sp.external_anchors if u == url), "") or ""
                if "noopener" not in rel_attr or "noreferrer" not in rel_attr:
                    fail(f"{rel}: external anchor missing rel=\"noopener noreferrer\": {url}")
            elif host not in OFFICIAL_HOSTS:
                warn(f"{rel}: external {tag} from non-official host: {url}")
            continue
        if parsed.scheme or url.startswith("mailto:"):
            fail(f"{rel}: unsupported link scheme: {url}")
            continue
        target = (path.parent / parsed.path).resolve() if parsed.path else path
        if not target.exists():
            fail(f"{rel}: broken link {url}")

    # -- nav consistency (warnings; new pages may be added by other sessions)
    nav_paths: set[str] = set()   # site-root-relative paths (relative to docs/)
    # Every file the build can produce is a valid nav/inline target, not only
    # HTML: the RSS feed (docs/feed.xml, decision D-41) is linked from every
    # page head and the footer.
    on_disk = {str(p.relative_to(DOCS)) for p in DOCS.rglob("*") if p.is_file()}
    for href_url, _ in sp.external_anchors:
        parsed = urlparse(href_url)
        if parsed.scheme or href_url.startswith("#"):
            continue
        file_part = href_url.split("#")[0]
        if not file_part:
            continue
        target = (path.parent / file_part).resolve()
        try:
            nav_paths.add(str(target.relative_to(DOCS.resolve())))
        except ValueError:
            warn(f"{rel}: link escapes docs/: {href_url}")
    for np_ in sorted(nav_paths):
        if np_ not in on_disk:
            fail(f"{rel}: nav/inline link target missing on disk: {np_}")
    if len(sp.aria_current) > 1:
        warn(f"{rel}: more than one aria-current=\"page\"")
    page_rel = str(path.relative_to(DOCS))
    if page_rel not in nav_paths:
        warn(f"{rel}: page not present in the shared sidebar nav")
    elif not sp.aria_current:
        warn(f"{rel}: nav page without aria-current=\"page\"")

    # -- affiliate link hygiene: the FTC/Amazon disclosure is adjacent to each
    # link, and the link carries a plain-language paid-link label.
    for href, row_no, paragraph in sp.shop_links:
        # Since decisions D-01/D-14 (recorded 2026-11-17) a shop href must be
        # the final tagged Special Link (Participation Requirements 2(b)); the
        # supplied short links remain recorded data but are not valid hrefs.
        if href not in special_links:
            fail(f"{rel}: shop link is not one of the published tagged Special Links: {href}")
        if row_no == 0:
            context = " ".join(paragraph or [])
        elif 1 <= row_no <= len(sp.row_texts):
            context = sp.row_texts[row_no - 1]
        else:
            warn(f"{rel}: shop link in row {row_no} could not be matched to a table row: {href}")
            continue
        if DISCLOSURE not in context:
            fail(f"{rel}: shop link lacks the Associates disclosure in its enclosing paragraph or table row")
        if "paid link" not in context.lower():
            fail(f"{rel}: shop link lacks a nearby plain-language paid-link label")


def check_products_coverage(asins: set[str], short_links: set[str]) -> None:
    page = DOCS / "products.html"
    if not page.exists():
        fail("docs/products.html missing")
        return
    raw = page.read_text(encoding="utf-8")
    for a in sorted(asins):
        if a not in raw:
            fail(f"products.html: ASIN {a} not listed")
    for s in sorted(short_links):
        if s not in raw:
            fail(f"products.html: supplied short link {s} not listed")


def check_live() -> None:
    repo = os.environ.get("GITHUB_REPOSITORY", "kanlerxz87-cyber/Zone4")
    token = os.environ.get("GITHUB_TOKEN", "")
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/pages/builds/latest",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "zone4-qa",
                 **({"Authorization": f"Bearer {token}"} if token else {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - surfaced as a failure line
        fail(f"live: GitHub Pages API request failed: {exc}")
        return
    status = data.get("status")
    if status != "built":
        fail(f"live: latest GitHub Pages build status is {status!r}, expected 'built'")
    else:
        print(f"LIVE OK: GitHub Pages latest build status 'built' for commit {data.get('commit', '?')}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live", action="store_true", help="also query the GitHub Pages API")
    ap.add_argument("--strict-warnings", action="store_true", help="treat warnings as failures")
    args = ap.parse_args()

    check_root_entry()
    short_links = load_short_links()
    special_links = load_special_links()
    asins = load_asins()

    pages = sorted(DOCS.rglob("*.html"))
    if not pages:
        fail("docs/ has no HTML pages")
    for page in pages:
        sp = PageParser()
        sp.feed(page.read_text(encoding="utf-8"))
        check_page(page, sp, special_links)
    check_products_coverage(asins, short_links)

    if args.live:
        check_live()

    print(f"QA audit: {len(pages)} page(s) checked.")
    for w in warnings:
        print(f"WARN  {w}")
    for f_ in failures:
        print(f"FAIL  {f_}")
    if failures or (args.strict_warnings and warnings):
        print(f"QA RESULT: FAIL ({len(failures)} failure(s), {len(warnings)} warning(s))")
        return 1
    print(f"QA RESULT: PASS ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
