# Zone4 — air-fryer buying guides and affiliate research

**Live site:** [kanlerxz87-cyber.github.io/Zone4](https://kanlerxz87-cyber.github.io/Zone4/)
**Published source:** GitHub Pages serves the repository root, which redirects to `docs/`. `scripts/build_site.py` is the only generator that writes the published pages. The separate research engine renders a private preview under `build/site-preview/`.

Zone4 is a small editorial buying-guide site backed by a source register. It publishes product facts only where the repository records an official source, leaves unsupported values blank, and keeps review questions and unresolved risks visible rather than presenting them as findings.

## Executive summary

- The currently verified product register contains **three** earlier supplied products: ASINs `B0CDY277D3`, `B09B7SB46R`, and `B08DKYBTPH`. Their link and listing checks are recorded in the dated verification data; the latest prior re-check is 2026-11-16.
- The latest brief repeats the three earlier URLs and adds two new candidates: [`B0c8moW59`](https://link.amazon/B0c8moW59) and [`B0f3GKalj`](https://link.amazon/B0f3GKalj). The first three destinations have historical dated verification records; the two new destinations were **not independently resolved in this session**, are not treated as ASINs, and are excluded from product pages under **F-55**. This is not a claim that either new link is invalid. Product-intent confirmation records are still needed for all five distinct links.
- The user supplied `shopnow047c-20` as the selected tracking ID. Its association with an enrolled Associates account, its application to valid Special Links, and a tracking-report test remain unconfirmed. Do not infer compliance by appending the ID to the current short links; see **Q-01 / D-01 / F-03** and the official [Amazon Associates policies](https://affiliate-program.amazon.com/help/operating/policies).
- Prices, ratings, review counts, product-level commission assignments, search demand, orders and revenue are not invented or forecast. The public category commission table is a reference only; no per-ASIN mapping is confirmed.
- The site includes a three-question product chooser, format categories, seven question-led articles, product comparison and source-backed tables. A generated RSS feed is at [`docs/feed.xml`](https://kanlerxz87-cyber.github.io/Zone4/docs/feed.xml); the sitemap and `robots.txt` are also generated.
- The suggestion and decision pages are the review gate: **38 suggestions**, **46 questions**, **41 decisions** (26 recorded, 15 open), and **55 flags** are maintained in the JSON registers and published to their matching pages. Unresolved and access-dependent work does not get reported as complete.

## Important limits and next checks

| Topic | Current state | What would establish it |
|---|---|---|
| Product intent / two new links | Three links have historical destination checks but no separate product-intent record; two new candidate destinations are unverified (F-55). | Confirm intended ASIN and official listing URL for each of the five distinct candidates in the enrolled Associates workflow; record intent, date and source separately from the observed redirect. |
| Tracking ID / Special Links | `shopnow047c-20` supplied, not independently confirmed or applied | Confirm account enrollment and Partner Tag in Associates Central; validate one destination and reporting event per product before scaling. |
| Product prices, ratings, reviews | Withheld | Confirm applicable Creators API access and permitted use under the current program terms; do not publish scraped or guessed values. |
| Click and conversion measurement | Existing browser-only click logger stores in local storage; no server endpoint, shared analytics, or Amazon conversion feed is connected. S-38 proposes five event names for review. | Choose compliant hosting, retention, consent and privacy terms, then connect authorized reports. The proposed events are not running instrumentation; the local logger is not an endpoint and does not prove purchases. |
| Search Console | No property verification or query data is recorded here | Verify the property with Google Search Console and report only its dated first-party observations. |
| Reader capture | No email/signup collection is deployed | Choose a lawful provider, purpose, retention and consent flow before collecting personal data. |
| Publishing cadence | Question-led topic calendar exists; no dated cadence is evidenced | Set an editorial frequency and review it against Search Console queries after data is available. |
| RSS | Static feed generated from the published article records | Article dates are omitted because the source records do not contain verified publication dates. |
| Campaign ledger | `data/tracking.jsonl` is intentionally empty | Append only timestamped, authorized reports with provenance; never estimate orders or revenue. |

The full repository executive summary is [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md). For owners reviewing next steps, begin with the [Suggestions](https://kanlerxz87-cyber.github.io/Zone4/docs/suggestions.html), [Open questions](https://kanlerxz87-cyber.github.io/Zone4/docs/questions.html), [Decision log](https://kanlerxz87-cyber.github.io/Zone4/docs/decisions.html), and [Flagged for Review](https://kanlerxz87-cyber.github.io/Zone4/docs/flagged.html) pages.

## Site map

| Page | Purpose |
|---|---|
| `docs/index.html` | Publication front page: chooser, featured guides, categories and comparison. |
| `docs/articles/index.html` | Article hub and the question-led topic calendar. |
| `docs/articles/*.html` | Seven individual buyer guides and product-format articles. |
| `docs/categories/*.html` | Dual-basket, single-basket and air-fry toaster-oven category pages. |
| `docs/products.html` | Three verified product records and a derived counter-space comparison. |
| `docs/requirements.html` | All 35 request requirements, with status, evidence and source. |
| `docs/suggestions.html` | Costed proposals awaiting review or marked by their actual status. |
| `docs/questions.html` | Known facts, missing information, who can provide it, and discovery steps. |
| `docs/decisions.html` | Options and recorded decisions; open decisions remain visible. |
| `docs/design.html` and `DESIGN_PROMPT.md` | Three design directions, anti-filler guidance, topic ideas and a prompt assembled from the design data. Open slots are deliberate where a decision remains open. |
| `docs/analytics.html` | Local-only click log; no network endpoint or conversion attribution. |
| `docs/verification.html`, `docs/sources.html`, `docs/policy-compliance.html` | Field-level verification, sources, and policy checklist. |
| `docs/flagged.html` | Unverified facts, unresolved link identities and review items. |
| `docs/feed.xml`, `docs/sitemap.xml`, `docs/robots.txt` | RSS 2.0 article feed, sitemap, and crawler guidance. |

The disclosure appears beneath the masthead and again in every page footer. All site pages are reachable from one flat navigation group and the footer directory. Product purchase links are marked `rel="sponsored"`; this attribute does not replace the visible disclosure or prove that a link is an Amazon Special Link.

## Data and code map

| Path | Contents |
|---|---|
| `data/products.json` | Current product records (three) and cited listing fields. |
| `data/marketing.json` | Seven articles, their fact rows and editorial metadata. |
| `data/sources.json` | Official-source registry. |
| `data/flags.json` | 55 flags; F-55 records the two new unverified link destinations and the missing product-intent confirmation. |
| `data/suggestions.json`, `data/questions.json`, `data/decisions.json` | Review-before-implementation decision-support registers. |
| `data/requirements.json`, `data/policies.json` | Requirement status and compliance register. |
| `data/tracking.jsonl` | Empty-by-design campaign/event ledger; append only authorized, provenance-backed data. |
| `data/verification-session-*.json` | Dated verification records; read each record for its exact scope and limits. |
| `scripts/build_site.py` | Static Pages-site builder, including RSS, sitemap and robots.txt generation. |
| `scripts/verify.py` | Deterministic data, disclosure, source, link, SEO and page-directory checks. |
| `qa/audit_site.py` | Independent audit of committed HTML. |
| `engine/`, `tests/`, `ENGINE.md` | Separate research-engine prototype, its tests and its operational limits. |
| `COORDINATION.md` | Shared task board and verification/merge history. |

## Build and checks

Run from a clean checkout with Python 3:

```bash
python3 scripts/build_site.py
python3 scripts/render_design_prompt.py
python3 scripts/verify.py
python3 qa/audit_site.py
python3 -m engine.cli build
python3 -m unittest discover -s tests
python3 tools/check_links.py
python3 -m engine.cli audit
```

The engine's final audit is expected to **block** drafts containing unverified fields, missing disclosures or policy gates. A blocked preview is not a failed public-site build; it is the intended safety behavior. The static site checks do not connect to Associates Central, Search Console, an analytics backend or a reader-capture provider.

## Official references

- [Amazon Associates Operating Agreement](https://affiliate-program.amazon.com/help/operating/agreement)
- [Amazon Associates Program Policies](https://affiliate-program.amazon.com/help/operating/policies)
- [FTC Disclosures 101](https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers)
- [FTC Endorsements, Influencers, and Reviews](https://www.ftc.gov/business-guidance/advertising-marketing/endorsements-influencers-reviews)
- [Google Search Central: helpful, people-first content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)
- [Google Search Central: qualify outbound links](https://developers.google.com/search/docs/crawling-indexing/qualify-outbound-links)
