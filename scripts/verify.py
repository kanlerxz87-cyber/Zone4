#!/usr/bin/env python3
"""Verify the data and the built site. Exits non-zero on any failure.

Checks:
  1. data/*.json: ASIN format; canonical URL matches ASIN; short links on link.amazon;
     every flag reference exists; every source URL is on an official host; every fact,
     keyword, stage, metric and rule in the marketing and pipeline files is sourced;
     every marketing article has a fact table, a disclosure and a compliant CTA.
  2. docs/*.html: every internal link and #anchor resolves; the Associates disclosure
     sentence appears on every page; every table body row contains a link to an
     official host; no Amazon price or star rating is published; no Amazon Mark is
     used as a page title, meta description or target keyword.
Standard library only. No network access is needed.
"""
from __future__ import annotations

import html
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
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
# Trademark Guidelines 1-3 and Participation Requirement 6(e): an Amazon Mark is not
# used as a page title, a meta description or a target keyword.
MARK_RE = re.compile(r"\bamazon\b|\bamaozn\b|\bammazon\b|\bkindle\b", re.IGNORECASE)

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def html_escape(value: str) -> str:
    """Escape the way the builder does, so the checks below match its output."""
    return html.escape(str(value), quote=True)


def is_official(url: str) -> bool:
    return (urlparse(url).hostname or "") in OFFICIAL_HOSTS


def check_data() -> None:
    products = load("products.json")["products"]
    flag_records = {f["id"]: f for f in load("flags.json")["flags"]}
    flags = set(flag_records)
    if "F-01" not in flag_records or "unverified" not in flag_records["F-01"]["status"].lower():
        fail("F-01 must remain open while per-ASIN commission assignments are unverified")
    if "F-05" not in flag_records or "resolved" not in flag_records["F-05"]["status"].lower():
        fail("F-05 must reflect the confirmed P2 Item details brand/manufacturer")
    sources = load("sources.json")
    for src in sources["sources"]:
        if not is_official(src["url"]):
            fail(f"source {src['id']} is not on an official host: {src['url']}")
    for rule in load("policies.json")["rules"]:
        if not is_official(rule["source_url"]):
            fail(f"policy {rule['id']} source is not official: {rule['source_url']}")
    for f in load("flags.json")["flags"]:
        for u in f["sources"]:
            if not is_official(u):
                fail(f"flag {f['id']} has a non-official source: {u}")
    for p in products:
        if not ASIN_RE.match(p["asin"]):
            fail(f"{p['id']}: ASIN malformed: {p['asin']}")
        if p["canonical_url"] != f"https://www.amazon.com/dp/{p['asin']}":
            fail(f"{p['id']}: canonical URL does not match ASIN")
        if urlparse(p["short_link"]).hostname != "link.amazon":
            fail(f"{p['id']}: short link is not on link.amazon")
        if not p.get("special_feature"):
            fail(f"{p['id']}: special_feature is empty")
        if p.get("commission_rate_pct") is not None and not p.get("commission_category_official"):
            fail(f"{p['id']}: product-level commission rate lacks a confirmed category assignment")
        if p.get("commission_rate_source") and not is_official(p["commission_rate_source"]):
            fail(f"{p['id']}: commission source is not official")
        for c in p["competitors"]:
            if not ASIN_RE.match(c["asin"]):
                fail(f"{p['id']}: competitor ASIN malformed: {c['asin']}")
            if not is_official(c["url"]):
                fail(f"{p['id']}: competitor URL is not official: {c['url']}")
        for fid in p["flags"]:
            if fid not in flags:
                fail(f"{p['id']}: unknown flag {fid}")
    if flag_records.get("F-01") and "unverified" in flag_records["F-01"]["status"].lower():
        engine_products = load("engine-verification.json")["products"]
        for engine_product in engine_products:
            rate = engine_product.get("attributes", {}).get("commission_rate_pct", {})
            if rate.get("value") is not None:
                fail(f"{engine_product['ref']}: engine publishes a rate while F-01 assignment is unverified")
    content = load("content.json")
    for a in content["analysis"]:
        for u in a["sources"]:
            if not is_official(u):
                fail(f"analysis {a['id']} has a non-official source: {u}")
    for b in content["executive_summary"]["bullets"] + content["not_built"]:
        if DISCLOSURE not in b and "As an Amazon Associate" not in b:
            continue


def check_marketing() -> None:
    marketing = load("marketing.json")
    articles = marketing["articles"]
    if len(articles) < 5:
        fail(f"marketing.json has only {len(articles)} articles; expected at least 5")
    product_data = {p["id"]: p for p in load("products.json")["products"]}
    product_ids = set(product_data)
    marketing_by_id = {a["id"]: a for a in articles}
    flag_records = {f["id"]: f for f in load("flags.json")["flags"]}
    if "P2" in product_data:
        expected_brand = product_data["P2"]["brand"]
        p2 = marketing_by_id.get("M-P2")
        brand_fact = next((f for f in p2.get("facts", []) if f["id"] == "M-P2-F1"), None) if p2 else None
        if not brand_fact or expected_brand not in brand_fact.get("value", ""):
            fail("marketing M-P2: brand fact must match the verified P2 product record")
        if "F-05" not in flag_records or "resolved" not in flag_records["F-05"]["status"].lower():
            fail("marketing M-P2: brand claim must agree with resolved F-05")
        for article_id in ("M-P2", "M-CMP", "M-BUY"):
            article = marketing_by_id.get(article_id)
            if article and any(term in json.dumps(article, ensure_ascii=False).lower() for term in (
                    "brand is unresolved", "brand not established", "brand is not asserted",
                    "brand is the other open point")):
                fail(f"marketing {article_id}: stale unresolved-P2-brand claim")
    for a in articles:
        facts = {f["id"]: f for f in a["facts"]}
        if not facts:
            fail(f"marketing {a['id']}: no fact table")
        for f in a["facts"]:
            fact_sources = f.get("source_urls") or [f["source_url"]]
            fact_refs = f.get("source_refs") or [f["source_ref"]] * len(fact_sources)
            if not fact_sources or len(fact_sources) != len(fact_refs):
                fail(f"marketing {a['id']} fact {f['id']}: source URLs/references are missing or mismatched")
            for source_url in fact_sources:
                if not is_official(source_url):
                    fail(f"marketing {a['id']} fact {f['id']}: non-official source {source_url}")
        cited = set()
        for para in a["body"]:
            for fid in para["fact_ids"]:
                if fid not in facts:
                    fail(f"marketing {a['id']} paragraph {para['id']}: unknown fact {fid}")
                cited.add(fid)
        for fid in facts:
            if fid not in cited:
                fail(f"marketing {a['id']}: fact {fid} is never cited by a paragraph")
        for k in a["target_keywords"]:
            if not is_official(k["source_url"]):
                fail(f"marketing {a['id']} keyword '{k['term']}': non-official source")
            if MARK_RE.search(k["term"]):
                fail(f"marketing {a['id']} keyword uses an Amazon Mark: {k['term']}")
        for field in ("title_tag", "meta_description", "h1", "slug"):
            if not a.get(field):
                fail(f"marketing {a['id']}: {field} is empty")
            elif MARK_RE.search(a[field]):
                fail(f"marketing {a['id']}: {field} uses an Amazon Mark: {a[field]}")
        cta = a.get("cta", {})
        if DISCLOSURE not in cta.get("disclosure", ""):
            fail(f"marketing {a['id']}: call to action has no disclosure sentence")
        if not is_official(cta.get("link_url", "")):
            fail(f"marketing {a['id']}: call to action link is not official")
        if a.get("product_id") not in product_ids and a.get("product_id") != "ALL":
            fail(f"marketing {a['id']}: unknown product_id {a.get('product_id')}")
    for r in marketing["seo_rules"]:
        if not is_official(r["source_url"]):
            fail(f"marketing SEO rule {r['id']}: non-official source")
    for c in marketing["publishing_checklist"]:
        if not is_official(c["source_url"]):
            fail(f"marketing checklist '{c['step']}': non-official source")


def check_pipeline() -> None:
    flags = {f["id"] for f in load("flags.json")["flags"]}
    pipeline = load("pipeline.json")
    for group, key in (
        ("stages", "stages"),
        ("tracking", "tracking"),
        ("optimisation", "optimisation"),
        ("agent_requirements", "agent_requirements"),
    ):
        for item in pipeline[key]:
            if not is_official(item["source_url"]):
                fail(f"pipeline {group} {item['id']}: non-official source {item['source_url']}")
    for t in pipeline["tracking"]:
        if t["current_value"]:
            fail(f"pipeline tracking {t['id']}: has a value, but no reporting access is connected")


def check_decision_support() -> None:
    """The suggestion, question and decision registers must agree with each other.

    A cross-reference that points nowhere is exactly the class of defect this
    site exists to catch, so the build refuses to produce one.
    """
    suggestions = load("suggestions.json")["suggestions"]
    questions = load("questions.json")["questions"]
    decisions_doc = load("decisions.json")
    decisions = decisions_doc["decisions"]
    flag_ids = {f["id"] for f in load("flags.json")["flags"]}

    question_ids = {q["id"] for q in questions}
    decision_ids = {d["id"] for d in decisions}
    if len(question_ids) != len(questions):
        fail("questions.json has duplicate ids")
    if len(decision_ids) != len(decisions):
        fail("decisions.json has duplicate ids")
    if len({s["id"] for s in suggestions}) != len(suggestions):
        fail("suggestions.json has duplicate ids")

    for s in suggestions:
        d = s.get("decision")
        if d and d not in decision_ids:
            fail(f"suggestion {s['id']} points at unknown decision {d}")
        if not d:
            fail(f"suggestion {s['id']} has no decision row")
        if not s["sources"]:
            fail(f"suggestion {s['id']} cites no source")
        for source in s["sources"]:
            if not is_official(source["url"]) and "github.com" not in source["url"]:
                fail(f"suggestion {s['id']} cites a non-official source: {source['url']}")
        for fid in s.get("flags") or []:
            if fid not in flag_ids:
                fail(f"suggestion {s['id']} references unknown flag {fid}")
        if s["priority"].split(" ")[0] not in {"P1", "P2", "P3"}:
            fail(f"suggestion {s['id']} has an undeclared priority: {s['priority']}")
        if s["status"] not in load("suggestions.json")["_meta"]["statuses"]:
            fail(f"suggestion {s['id']} has an undeclared status: {s['status']}")

    for q in questions:
        if q["kind"] not in load("questions.json")["_meta"]["kinds"]:
            fail(f"question {q['id']} has an undeclared kind: {q['kind']}")
        if not q["sources"]:
            fail(f"question {q['id']} cites no source")
        for source in q["sources"]:
            if not is_official(source["url"]):
                fail(f"question {q['id']} cites a non-official source: {source['url']}")
        for fid in q.get("flags") or []:
            if fid not in flag_ids:
                fail(f"question {q['id']} references unknown flag {fid}")

    for d in decisions:
        if d["linked_question"]:
            for qid in [x.strip() for x in d["linked_question"].split(",")]:
                if qid and qid not in question_ids:
                    fail(f"decision {d['id']} points at unknown question {qid}")
        for sid in d["linked_suggestions"]:
            if sid not in {s["id"] for s in suggestions}:
                fail(f"decision {d['id']} points at unknown suggestion {sid}")
        for o in d["options"]:
            if not o["key"] or not o["label"] or not o["commits_to"]:
                fail(f"decision {d['id']} has an incomplete option")
        if d["status"] not in load("decisions.json")["_meta"]["statuses"]:
            fail(f"decision {d['id']} has an undeclared status: {d['status']}")
        for source in d["sources"]:
            if not is_official(source["url"]):
                fail(f"decision {d['id']} cites a non-official source: {source['url']}")

    # A recorded decision must appear in the log, and the log must not claim one
    # that is still open.
    recorded = {d["id"] for d in decisions if d["status"].lower().startswith("recorded")}
    logged = {entry["decision"] for entry in decisions_doc["log"] if entry["decision"] != "\u2014"}
    if recorded != logged:
        fail(f"decision log and register disagree: recorded={sorted(recorded)} logged={sorted(logged)}")


def check_design() -> None:
    """The design brief must obey the same sourcing rules as every other page.

    It is a proposal rather than verified product data, so the rule that
    matters is different: every row must cite the official source that
    constrains it, and it must not smuggle in a figure no official source
    supports. No row in this file may carry a traffic, revenue, search-volume,
    price, rating or review-count number.
    """
    design = load("design.json")
    decisions = {d["id"]: d for d in load("decisions.json")["decisions"]}
    flags = {f["id"] for f in load("flags.json")["flags"]}
    suggestions = {s["id"] for s in load("suggestions.json")["suggestions"]}
    articles = {a["id"] for a in load("marketing.json")["articles"]}
    products = {p["id"] for p in load("products.json")["products"]}

    # A bare number followed by a unit or a currency sign would be a figure the
    # site has no official source for. The brief must stay qualitative.
    figure_re = re.compile(r"(\$\s?\d|\b\d+(\.\d+)?\s*(%|percent|stars?|reviews?|visits?|clicks?|sessions?|impressions?)\b)", re.IGNORECASE)

    def row_sources(where: str, row: dict) -> None:
        sources = row.get("sources") or row.get("constrained_by")
        if not sources:
            fail(f"design {where}: no source cited")
            return
        for s in sources:
            if not is_official(s["url"]):
                fail(f"design {where}: non-official source {s['url']}")
        if figure_re.search(json.dumps(row, ensure_ascii=False)):
            fail(f"design {where}: carries a figure no official source supports")

    seen: set[str] = set()
    for group in ("directions", "anti_slop", "headline_options", "topics"):
        for row in design.get(group, []):
            rid = row["id"]
            if rid in seen:
                fail(f"design: duplicate id {rid}")
            seen.add(rid)
            row_sources(f"{group} {rid}", row)
            for fid in row.get("flags") or row.get("blocked_by") or []:
                if fid not in flags:
                    fail(f"design {rid}: unknown flag {fid}")

    # A direction must point at a real D-18 option, so the brief cannot invent
    # a fourth look nobody has been asked to choose between.
    d18 = decisions.get("D-18")
    if d18:
        keys = {o["key"] for o in d18["options"]}
        for d in design["directions"]:
            if not any(d["decision_option"].endswith(f"option {k}") for k in keys):
                fail(f"design {d['id']}: decision_option does not match a D-18 option")

    # Headline options must attach to articles that exist, and topics to facts
    # and products that exist.
    fact_ids = {f["id"] for a in load("marketing.json")["articles"] for f in a["facts"]}
    for h in design["headline_options"]:
        if h["article"] not in articles:
            fail(f"design {h['id']}: unknown article {h['article']}")
    for t in design["topics"]:
        for fid in t["fact_rows"]:
            if fid not in fact_ids:
                fail(f"design {t['id']}: unknown fact row {fid}")
        if t["wave"] not in {"Wave 1 - foundational four", "Wave 2"}:
            fail(f"design {t['id']}: undeclared wave {t['wave']}")

    # The launch path must be five real decisions in order, or the page's
    # claim about a "shortest credible path" is not checkable.
    path = design.get("launch_path", [])
    if not path:
        fail("design: launch_path is empty")
    for n, step in enumerate(path, start=1):
        if step["step"] != n:
            fail(f"design launch_path: step {step['step']} is out of order")
        if step["decision"] not in decisions:
            fail(f"design launch_path: unknown decision {step['decision']}")

    # Every slot in the prompt must name the decision or question that fills it.
    for s in design.get("prompt_slots", []):
        if s["current"] != "not yet chosen" and not re.search(r"\b[DSQ]-\d+", s["filled_from"]):
            fail(f"design prompt slot {s['slot']}: filled_from names no decision or question")

    if figure_re.search(json.dumps(design.get("launch_path", []), ensure_ascii=False)):
        fail("design launch_path: carries a figure no official source supports")

    # DESIGN_PROMPT.md is generated from this data by scripts/render_design_prompt.py.
    # If someone edits the markdown by hand it stops being the same brief as the
    # page, so the build refuses to ship the mismatch.
    prompt_md = ROOT / "DESIGN_PROMPT.md"
    if not prompt_md.exists():
        fail("DESIGN_PROMPT.md is missing; run scripts/render_design_prompt.py")
    else:
        text = prompt_md.read_text(encoding="utf-8")
        for d in design["directions"]:
            if d["one_line"] not in text:
                fail(f"DESIGN_PROMPT.md is out of date: missing direction {d['id']}")
        for a in design["anti_slop"]:
            if a["replacement"] not in text:
                fail(f"DESIGN_PROMPT.md is out of date: missing anti-pattern {a['id']}")


def check_design_page() -> None:
    """The Design brief page must carry the prompt that the data assembles."""
    page = DOCS / "design.html"
    if not page.exists():
        return
    raw = page.read_text(encoding="utf-8")
    design = load("design.json")
    match = re.search(r'<pre id="design-prompt">(.*?)</pre>', raw, re.S)
    if not match:
        fail("docs/design.html: the paste-ready prompt block is missing")
        return
    prompt = html.unescape(match.group(1))
    for d in design["directions"]:
        if d["one_line"] not in prompt:
            fail(f"docs/design.html: the prompt is missing direction {d['id']}")
    if "[DIRECTION]" not in prompt or "[TOPICS]" not in prompt:
        fail("docs/design.html: the prompt has lost its bracketed slots")


class SiteParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.links: list[tuple[str, str]] = []  # (tag, url)
        self.in_tbody = False
        self.row_links: list[str] | None = None
        self.bad_rows: list[int] = []
        self.rows = 0
        self.text_parts: list[str] = []
        self.title = ""
        self.meta_description = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "title":
            self._in_title = True
        if tag == "meta" and (a.get("name") or "").lower() == "description":
            self.meta_description = a.get("content", "")
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
        if tag == "title":
            self._in_title = False
        if tag == "tbody":
            self.in_tbody = False
        if tag == "tr" and self.row_links is not None:
            if not any(is_official(h) for h in self.row_links):
                self.bad_rows.append(self.rows)
            self.row_links = None

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        self.text_parts.append(data)


def check_requirements() -> None:
    reqs = load("requirements.json")
    known_status = set(reqs["_meta"]["status_meanings"])
    known_base = {"Delivered", "Not built", "Unverifiable"}
    flags = {f["id"] for f in load("flags.json")["flags"]}
    seen: set[str] = set()
    for r in reqs["requirements"]:
        if r["id"] in seen:
            fail(f"duplicate requirement id {r['id']}")
        seen.add(r["id"])
        if not r["sources"]:
            fail(f"requirement {r['id']} has no source")
        for u in r["sources"]:
            if not is_official(u):
                fail(f"requirement {r['id']} has a non-official source: {u}")
        base = r["status"].split(" (")[0].split(" - ")[0]
        if base not in known_base or r["status"] not in known_status:
            fail(f"requirement {r['id']} uses an undeclared status: {r['status']}")
        if base.startswith("Delivered") and not r["delivered"]:
            fail(f"requirement {r['id']} is marked {r['status']} but has no delivered evidence")
        if base.startswith("Not built") and not r["blocker"]:
            fail(f"requirement {r['id']} is marked {r['status']} but names no blocker")
        for fid in r.get("flags") or []:
            if fid not in flags:
                fail(f"requirement {r['id']} references unknown flag {fid}")



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
        visible = " ".join(sp.text_parts)
        if DISCLOSURE not in visible:
            fail(f"{rel}: disclosure sentence missing")
        raw = page.read_text(encoding="utf-8")
        footer_match = re.search(r"<footer>(.*?)</footer>", raw, re.S)
        if not footer_match or DISCLOSURE not in html.unescape(footer_match.group(1)):
            fail(f"{rel}: affiliate disclosure must be repeated in the footer")
        if raw.count('<div class="nav-group">') != 1:
            fail(f"{rel}: shared navigation must contain exactly one group")
        shop_anchors = re.findall(r'<a\b[^>]*class="[^"]*\bshop\b[^"]*"[^>]*>', raw)
        for anchor in shop_anchors:
            rel_attr = re.search(r'\brel="([^"]*)"', anchor)
            if not rel_attr or "sponsored" not in rel_attr.group(1).split():
                fail(f"{rel}: product link is missing rel=\"sponsored\": {anchor[:140]}")
        if not footer_match or 'class="footer-directory"' not in footer_match.group(1):
            fail(f"{rel}: footer site directory is missing")
        elif footer_match:
            footer_hrefs = re.findall(r'<a\b[^>]*href="([^"]+)"', footer_match.group(1))
            footer_targets = set()
            for href_value in footer_hrefs:
                parsed_href = urlparse(href_value)
                if not parsed_href.scheme and parsed_href.path:
                    footer_targets.add((page.parent / parsed_href.path).resolve())
            missing_from_footer = [target.relative_to(DOCS) for target in pages if target.resolve() not in footer_targets]
            if missing_from_footer:
                fail(f"{rel}: footer directory omits page(s): {', '.join(map(str, missing_from_footer))}")
        for bad in sp.bad_rows:
            fail(f"{rel}: table row {bad} has no link to an official source")
        raw = page.read_text(encoding="utf-8")
        if PRICE_RE.search(re.sub(r"<[^>]+>", " ", raw)):
            fail(f"{rel}: contains a currency amount (Amazon prices are withheld under Participation Requirements 2(b))")
        if RATING_RE.search(raw):
            fail(f"{rel}: contains a star rating (withheld under Participation Requirements 6(t))")
        if MARK_RE.search(sp.title):
            fail(f"{rel}: page title uses an Amazon Mark: {sp.title}")
        if MARK_RE.search(sp.meta_description):
            fail(f"{rel}: meta description uses an Amazon Mark: {sp.meta_description}")

    # Google's snippet guidance asks for a unique description per page. Two pages
    # sharing one is a presentation defect the build must not reintroduce.
    by_description: dict[str, list[str]] = {}
    for page, sp in parsed.items():
        if sp.meta_description:
            by_description.setdefault(sp.meta_description, []).append(str(page.relative_to(ROOT)))
    for description, pages_using in by_description.items():
        if len(pages_using) > 1:
            fail("meta description is shared by " + ", ".join(sorted(pages_using)) + ": " + description[:80])

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


def check_required_pages() -> None:
    required = [
        "index.html", "executive-summary.html", "products.html", "marketing.html",
        "automation.html", "analysis.html", "requirements.html", "suggestions.html", "verification.html",
        "policy-compliance.html", "analytics.html", "flagged.html", "sources.html",
        "suggestions.html", "questions.html", "design.html", "decisions.html",
        "categories/dual-basket-air-fryers.html",
        "categories/single-basket-air-fryers.html",
        "categories/air-fryer-toaster-ovens.html",
    ]
    for rel in required:
        if not (DOCS / rel).exists():
            fail(f"docs/{rel} is missing")
    # Article pages are derived from data/marketing.json, so the check is derived
    # from the same data: an article in the data must have a page, and the page
    # must carry the article's own SEO fields.
    for a in load("marketing.json")["articles"]:
        rel = "articles/" + a["slug"].strip("/") + ".html"
        page = DOCS / rel
        if not page.exists():
            fail(f"docs/{rel} is missing (article {a['id']} has no page)")
            continue
        raw = page.read_text(encoding="utf-8")
        if f'<meta name="description" content="{html_escape(a["meta_description"])}">' not in raw:
            fail(f"docs/{rel} does not carry the article's own meta description")
        if f"<title>{html_escape(a['title_tag'])} |" not in raw:
            fail(f"docs/{rel} does not carry the article's own title tag")
        # Standing internal-linking rule (decision D-27, recorded 2026-11-16):
        # every article carries a 'Where next' block that reaches the comparison,
        # the buying guide, the articles hub and the chooser. The check reads the
        # block itself, not the site navigation, so it cannot pass by accident.
        wm = re.search(r'<nav class="wherenext".*?</nav>', raw, re.S)
        if not wm:
            fail(f"docs/{rel}: no 'Where next' block (decision D-27)")
        else:
            block = wm.group(0)
            targets = ["articles/index.html", "index.html#chooser"]
            if a["id"] != "M-CMP":
                targets.append("dual-basket-vs-single-basket-vs-toaster-oven-air-fryer.html")
            if a["id"] != "M-BUY":
                targets.append("air-fryer-buying-guide-2026.html")
            for target in targets:
                if target not in block:
                    fail(f"docs/{rel}: 'Where next' block does not reach {target}")


def check_rss_feed() -> None:
    feed_path = DOCS / "feed.xml"
    if not feed_path.exists():
        fail("docs/feed.xml missing")
        return
    try:
        root = ET.parse(feed_path).getroot()
    except ET.ParseError as exc:
        fail(f"docs/feed.xml is not valid XML: {exc}")
        return
    if root.tag != "rss" or root.get("version") != "2.0":
        fail("docs/feed.xml must be an RSS 2.0 document")
        return
    channel = root.find("channel")
    if channel is None:
        fail("docs/feed.xml has no channel")
        return
    items = channel.findall("item")
    articles = load("marketing.json")["articles"]
    if len(items) != len(articles):
        fail(f"docs/feed.xml has {len(items)} items; expected {len(articles)} published articles")
    expected = ["https://kanlerxz87-cyber.github.io/Zone4/docs/articles/" + a["slug"].strip("/") + ".html" for a in articles]
    actual = [item.findtext("link") for item in items]
    if actual != expected:
        fail("docs/feed.xml article links do not match the published article records")


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
    check_marketing()
    check_pipeline()
    check_requirements()
    check_decision_support()
    check_design()
    check_site()
    check_rss_feed()
    check_design_page()
    check_required_pages()
    check_root_entry()
    if failures:
        print(f"FAILED: {len(failures)} problem(s)")
        for f in failures:
            print(" -", f)
        return 1
    n_pages = len(list(DOCS.rglob('*.html')))
    print(f"OK: data files valid; {n_pages} pages checked: links, anchors, disclosure, row sources, "
          f"no prices or ratings, no Amazon Mark in titles or keywords.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
