"""SEO content generation that cannot publish an unverified fact.

Generated blocks come in two kinds:

* **verified** — sourced, rendered as prose;
* **placeholder** — ``[[UNVERIFIED: <field> — <reason>]]``; the publish gate
  treats any surviving placeholder as a hard failure, so a draft can only ship
  once a human has resolved (or consciously removed) every gap.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .claims import Entity, Status
from .datastore import Datastore
from .policy import AMAZON_TEXT_NOTICE, register_program_text  # noqa: E402
from .policy import REQUIRED_DISCLOSURE

PLACEHOLDER_RE = re.compile(r"\[\[UNVERIFIED: .*?\]\]", re.S)
TITLE_MAX, DESC_MAX = 60, 158

PEOPLE_FIRST_CHECKS = [
    "Content provides original information, reporting, research, or analysis",
    "Substantial, complete, or comprehensive description of the topic",
    "Insightful analysis or information beyond the obvious",
    "Draws on sources without simply copying or rewriting them",
    "Heading/title is a descriptive, helpful summary",
    "Heading/title is not exaggerated or shocking",
]


@dataclass
class SeoDoc:
    slug: str
    title: str
    description: str
    h1: str
    body_html: str
    keywords: list[str] = field(default_factory=list)
    canonical: str = ""
    entity_ref: str | None = None

    @property
    def disclosures_present(self) -> bool:
        return REQUIRED_DISCLOSURE.lower() in self.body_html.lower()

    @property
    def placeholders(self) -> list[str]:
        return PLACEHOLDER_RE.findall(self.body_html)

    def title_length_ok(self) -> bool:
        return 10 <= len(self.title) <= TITLE_MAX

    def description_length_ok(self) -> bool:
        return 50 <= len(self.description) <= DESC_MAX

    def json_ld(self, rating: float | None = None, review_count: int | None = None) -> dict:
        """Article schema. Rating/review fields are emitted only when verified —
        a fabricated aggregateRating is exactly what this project must not do."""
        data: dict = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": self.title,
            "description": self.description,
            "inLanguage": "en",
        }
        if self.canonical:
            data["mainEntityOfPage"] = {"@type": "WebPage", "@id": self.canonical}
        if rating is not None and review_count is not None:
            data["about"] = {
                "@type": "Product",
                "name": self.h1,
                "aggregateRating": {
                    "@type": "AggregateRating",
                    "ratingValue": rating,
                    "reviewCount": review_count,
                },
            }
        return data

    def head(self, stylesheet: str = "styles.css") -> str:
        ld = json.dumps(self.json_ld(), ensure_ascii=False)
        return (
            "<!doctype html>\n<html lang=\"en\">\n<head>\n"
            "<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
            f"<title>{self.title}</title>\n"
            f'<meta name="description" content="{self.description}">\n'
            + (f'<link rel="canonical" href="{self.canonical}">\n' if self.canonical else "")
            + '<meta property="og:type" content="article">\n'
            f'<meta property="og:title" content="{self.title}">\n'
            f'<meta property="og:description" content="{self.description}">\n'
            '<meta name="twitter:card" content="summary_large_image">\n'
            f'<link rel="stylesheet" href="{stylesheet}">\n'
            f'<script type="application/ld+json">{ld}</script>\n'
            "</head>\n"
        )

    def to_html(self, stylesheet: str = "styles.css", nav: str = "") -> str:
        return (self.head(stylesheet) + "<body>\n" + nav + "\n<main class=\"main\">\n"
                + self.body_html + "\n</main>\n</body>\n</html>\n")


def _ph(field_name: str, claim) -> str:
    reason = getattr(claim, "reason", "") or getattr(claim, "flag", "") or "no official source"
    return f"[[UNVERIFIED: {field_name} — {reason}]]"


def _value_or_placeholder(label: str, claim) -> str:
    if claim is None:
        return _ph(label, type("x", (), {"reason": "not captured by this workspace"})())
    if claim.status is Status.VERIFIED and claim.value is not None:
        return str(claim.value)
    return _ph(label, claim)


def spec_table(entity: Entity, fields: list[str], labels: dict[str, str]) -> str:
    rows = []
    for f in fields:
        claim = entity.get(f)
        val = _value_or_placeholder(labels.get(f, f), claim)
        cls = "pill ok" if claim is not None and claim.status is Status.VERIFIED else "pill warn"
        state = "Verified" if cls.endswith("ok") else "Unverified"
        rows.append(f"<tr><td>{labels.get(f, f)}</td><td>{val}</td><td><span class='{cls}'>{state}</span></td></tr>")
    return ("<div class='table-wrap'><table><thead><tr><th>Attribute</th><th>Value</th>"
            "<th>State</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>")


def disclosure_block(extra: str = "") -> str:
    """The two notices a page must carry, in one block.

    Both are placement duties, so they travel with the draft rather than being
    assumed from a template: the Operating Agreement identification sentence, and
    the IP License 2(k) notice required in plain view whenever Amazon-sourced
    text (a listing title) is reproduced. A draft published on its own therefore
    stays compliant even if no page shell is wrapped around it.
    """
    return ("<aside class=\"notice amber\"><b>Affiliate disclosure</b><span>"
            + (extra or "We may earn a commission from qualifying purchases made through links on this page.")
            + f" {REQUIRED_DISCLOSURE}</span>"
            + f"<span><b>Amazon content notice</b> {AMAZON_TEXT_NOTICE}"
            + " (required in plain view by IP License 2(k) where Amazon-sourced text is displayed)</span>"
            + "</aside>")


def product_review(store: Datastore, entity: Entity, site_base: str = "") -> SeoDoc:
    register_program_text(entity.name)
    name = _value_or_placeholder("product name", entity.get("product_name"))
    price = entity.get("price")
    rate = entity.get("star_rating")
    cat = entity.get("category")
    title = f"{name}: honest review before you buy"[:TITLE_MAX]
    desc = (f"An evidence-led review of {name}. Every field lists its source; anything "
            "unconfirmed is marked unverified rather than guessed.")[:DESC_MAX]
    body = f"""<article>
<header class="topbar"><div><span class="eyebrow">PRODUCT REVIEW</span><h1>{name}</h1></div>
<span class="status"><i></i> {entity.verified_count()}/{len(entity.claims)} fields verified</span></header>
{disclosure_block()}
<section class="panel"><div class="panel-head"><div><h3>What we can and cannot confirm</h3>
<p>Amazon's product detail page is the only acceptable source for price, rating and availability.
{entity.notes or 'No product detail page could be matched to the supplied reference.'}</p></div></div>
{spec_table(entity, ["brand", "category", "price", "star_rating", "review_count", "availability", "best_sellers_rank"],
            {"brand": "Brand", "category": "Category", "price": "Price", "star_rating": "Star rating",
             "review_count": "Review count", "availability": "Availability", "best_sellers_rank": "Best Sellers rank"})}
</section>
<section class="two-col">
<article class="panel compact"><div class="eyebrow">PRICING</div><h3>What you would pay today</h3>
<p>Listed price: {_value_or_placeholder("price", price)}. Prices on Amazon change continuously; this page does not
cache or alert on prices (Participation Requirements §6(y)).</p></article>
<article class="panel compact"><div class="eyebrow">RECEPTION</div><h3>What buyers report</h3>
<p>Rating {_value_or_placeholder("star rating", rate)} across {_value_or_placeholder("review count", entity.get('review_count'))}
reviews. Review content is only usable when obtained through the approved API (Participation Requirements §6(t)).</p></article>
</section>
<section class="panel"><div class="panel-head"><div><h3>Buying decision</h3>
<p>Recommendation withheld: the available sources confirm identity and listed fields, but no independent performance testing or first-hand use is recorded, so this research does not rank or endorse the product.</p></div>
<span class="pill warn">Do not publish</span></div>
<p>Amazon browse category as listed: {_value_or_placeholder("category", cat)}. The browse path does not confirm the Associates commission category applied to this ASIN, so the product-specific rate stays blank pending item-specific official evidence (ENG-F-016). The public <a href="{store.source_url('S1')}">Standard Commission Income Statement</a> lists category bands, not an ASIN assignment.</p>
</section>
{people_first_block()}
<footer><a href="index.html">← Overview</a><span>Generated by the Zone4 platform; every gap is visible.</span></footer>
</article>"""
    return SeoDoc(slug=f"review-{entity.ref.lower()}", title=title, description=desc, h1=str(name),
                  body_html=body, canonical=f"{site_base}/content/{entity.ref.lower()}.html", entity_ref=entity.ref)


def comparison(store: Datastore, entities: list[Entity], site_base: str = "") -> SeoDoc:
    for _e in entities:
        register_program_text(_e.name)
    labels = [(_value_or_placeholder("product name", e.get("product_name")), e) for e in entities]
    cols = "".join(f"<th>{n}</th>" for n, _ in labels)
    fields = ["price", "star_rating", "review_count", "category", "availability"]
    labels_map = {"price": "Price", "star_rating": "Rating", "review_count": "Reviews",
                  "category": "Category", "availability": "Availability"}
    rows = []
    for f in fields:
        cells = "".join(f"<td>{_value_or_placeholder(labels_map[f], e.get(f))}</td>" for _, e in labels)
        rows.append(f"<tr><th>{labels_map[f]}</th>{cells}</tr>")
    title = "Side-by-side comparison: what is actually verifiable"[:TITLE_MAX]
    desc = "Comparison table for the requested products, showing verified values and explicit unverified markers."[:DESC_MAX]
    body = f"""<article>
<header class="topbar"><div><span class="eyebrow">COMPARISON</span><h1>Head-to-head, evidence only</h1></div>
<span class="status"><i></i> {len(entities)} entries</span></header>
{disclosure_block()}
<section class="panel"><div class="panel-head"><div><h3>Comparison matrix</h3>
<p>Blank means unverified — not zero, not 'average'. Fill a cell only from the product's own Amazon detail page or the API.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Attribute</th>{cols}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>
</section>
<section class="panel compact"><div class="eyebrow">VERDICT POLICY</div><h3>No winner declared</h3>
<p>A 'best of' verdict requires first-hand testing or cited evidence per Google's people-first guidance; neither exists for these
entries, so no ranking is published.</p></section>
{people_first_block()}
<footer><a href="index.html">← Overview</a><span>Comparison generated without inferred data</span></footer>
</article>"""
    return SeoDoc(slug="comparison", title=title, description=desc, h1="Head-to-head, evidence only",
                  body_html=body, canonical=f"{site_base}/content/comparison.html")


def buying_guide(store: Datastore, entity: Entity, site_base: str = "") -> SeoDoc:
    register_program_text(entity.name)
    name = _value_or_placeholder("product name", entity.get("product_name"))
    title = f"Buying guide: what to check before ordering {name}"[:TITLE_MAX]
    desc = "A checklist-driven buying guide that names each verification step and its official source."[:DESC_MAX]
    checks = [
        ("Confirm the product identity", "Open the official Amazon product page and match the ASIN shown in the Product Details block.", "https://sell.amazon.com/blog/what-is-an-asin"),
        ("Confirm price and shipping at checkout", "Do not cache or alert on prices; show the price Amazon returns for your locale.", "https://affiliate-program.amazon.com/help/operating/policies"),
        ("Confirm the seller and format", "Products sold by third parties through sites linked from Amazon are outside the Program's Products Statement.", "https://affiliate-program.amazon.com/help/operating/policies"),
        ("Confirm the tag on your link", "Use your own registered tag for the marketplace you are linking to.", "https://affiliate-program.amazon.com/creatorsapi/docs/en-us/onboarding/sign-up-as-an-amazon-associate"),
        ("Confirm your disclosure", "Place the required statement and a clear link-level disclosure on the page itself.", "https://affiliate-program.amazon.com/help/node/topic/GHQNZAU6669EZS98"),
    ]
    lis = "".join(f"<li><b>{t}</b> — {d} <a href='{u}' rel='noopener'>official source ↗</a></li>" for t, d, u in checks)
    body = f"""<article>
<header class="topbar"><div><span class="eyebrow">BUYING GUIDE</span><h1>Before you buy: a five-step check</h1></div></header>
{disclosure_block()}
<section class="panel"><div class="panel-head"><div><h3>Applies to: {name}</h3>
<p>Each step below is a verification action with the official page that defines the requirement.</p></div></div>
<ol class="checklist">{lis}</ol></section>
<section class="two-col"><article class="panel compact"><div class="eyebrow">WHAT THIS GUIDE DOES NOT DO</div>
<h3>No claims about quality, value or safety</h3><p>Those require testing or substantiation. Nothing here asserts performance for
{name}.</p></article><article class="panel compact"><div class="eyebrow">ATTRIBUTION WINDOW</div>
<h3>24 hours, plus an 89-day cart</h3><p>A Session ends 24 hours after the click, or when the customer orders or clicks another
publisher's link; a cart order must complete within 89 days of the click.
<a href="{store.source_url('S2')}">Program Policies ↗</a></p></article></section>
{people_first_block()}
<footer><a href="index.html">← Overview</a><span>Guide generated from policy text, not product claims</span></footer>
</article>"""
    return SeoDoc(slug=f"guide-{entity.ref.lower()}", title=title, description=desc,
                  h1="Before you buy: a five-step check", body_html=body,
                  canonical=f"{site_base}/content/guide-{entity.ref.lower()}.html", entity_ref=entity.ref)


def people_first_block() -> str:
    items = "".join(f"<li>{c}</li>" for c in PEOPLE_FIRST_CHECKS)
    return ("<section class=\"panel\"><div class=\"panel-head\"><div><h3>People-first self-assessment</h3>"
            "<p>Google's published questions, applied to this draft before publication "
            "(<a href='https://developers.google.com/search/docs/fundamentals/creating-helpful-content'>source</a>).</p>"
            f"</div></div><ul class='checklist'>{items}</ul></section>")


def seo_audit(doc: SeoDoc) -> list[dict]:
    """Deterministic on-page checks used by CI and by the content page."""
    out = [
        {"check": "Title length 10–60 chars", "pass": doc.title_length_ok(), "value": len(doc.title)},
        {"check": "Meta description 50–158 chars", "pass": doc.description_length_ok(), "value": len(doc.description)},
        {"check": "Single H1 present", "pass": len(re.findall(r"<h1[\s>]", doc.body_html)) == 1,
         "value": len(re.findall(r"<h1[\s>]", doc.body_html))},
        {"check": "Amazon disclosure statement present", "pass": doc.disclosures_present, "value": ""},
        {"check": "No unverified placeholders left", "pass": not doc.placeholders, "value": len(doc.placeholders)},
        {"check": "Canonical set", "pass": bool(doc.canonical), "value": doc.canonical},
    ]
    return out
