# Zone4 — air-fryer buying guides and affiliate research

**Live site:** [kanlerxz87-cyber.github.io/Zone4](https://kanlerxz87-cyber.github.io/Zone4/)
**Published source:** GitHub Pages serves the repository root, which redirects to `docs/`. `scripts/build_site.py` is the only generator that writes the published pages. The separate research engine renders a private preview under `build/site-preview/`.

Zone4 is a small editorial buying-guide site backed by a source register. It publishes product facts only where the repository records an official source, leaves unsupported values blank, and keeps review questions and unresolved risks visible rather than presenting them as findings.

## Executive summary

- The currently verified product register contains **three** earlier supplied products: ASINs `B0CDY277D3`, `B09B7SB46R`, and `B08DKYBTPH`. Their link and listing checks are recorded in the dated verification data; the latest prior re-check is 2026-11-16.
- The latest brief repeats the three earlier URLs and adds two more: [`B0c8moW59`](https://link.amazon/B0c8moW59) and [`B0f3GKalj`](https://link.amazon/B0f3GKalj). All five were re-resolved to listings on 2026-11-19 (`data/intent-links.json` keeps the intended ASIN and the observed redirect in separate fields). The two later links open meat-thermometer listings and are published in their own category under decision **D-46**; resolution is not a finding that any supplied link is valid or invalid.
- The user supplied `shopnow047c-20` as the selected tracking ID. Decisions **D-01/D-14** (recorded 2026-11-17 under the owner's brief) publish every outbound product link as the tagged Special Link `https://www.amazon.com/dp/<ASIN>?tag=shopnow047c-20` — the final destination URL with the tag as its parameter (Participation Requirements 2(b)), no shortener. The supplied short links stay recorded verbatim in `data/intent-links.json` and are not judged valid or invalid (Zone3 FLG-003 unresolved). What remains unconfirmed is the tag's registration in Associates Central (**F-57**); the one-link-per-product test protocol (`data/associates.json`, S-45) gates attribution claims and scaling, not publication. See **Q-01 / Q-50 / F-03 / F-58** and the official [Amazon Associates policies](https://affiliate-program.amazon.com/help/operating/policies).
- Prices, ratings, review counts, product-level commission assignments, search demand, orders and revenue are not invented or forecast. The public category commission table is a reference only; no per-ASIN mapping is confirmed.
- The site includes a three-question product chooser, four categories with scale-drawn footprint diagrams, eight question-led articles plus four published question-shaped guides, a product comparison and source-backed tables. A generated RSS feed is at [`docs/feed.xml`](https://kanlerxz87-cyber.github.io/Zone4/docs/feed.xml); the sitemap and `robots.txt` are also generated.
- The review gate is now one page: **Review what to change** (`docs/review.html`, data `data/redesign.json`) files **13 proposals** and **12 gating questions**, each with cost, risk, the check that proves it worked and an official source. Four proposals carry a dated application from 2026-11-19: RD-01 complete; RD-03, RD-06 and RD-08 partly, each naming what still waits; the rest are proposals only. The older registers are unchanged beside it: **50 suggestions**, **51 questions**, **46 decisions** (34 recorded, 12 open) and **72 flags**. Unresolved and access-dependent work is not reported as complete.

## Important limits and next checks

| Topic | Current state | What would establish it |
|---|---|---|
| Product intent / two new links | `data/intent-links.json` records the product-intent confirmation (intended ASIN and official listing URL vs. observed redirect targets, kept separate) for all five submitted links. The two meat-thermometer links (P4, P5) were re-resolved on 2026-11-19 to the ASINs recorded and are published as tagged Special Links under decision D-46 (F-55 resolved on identity; F-56 resolved by D-46). The link path codes are not ASINs (F-67). | Confirm each product's Special Link in Associates Central (one-link test, F-58); confirm the tracking ID (F-57). The thermometer scope can be reversed by the owner (D-46). |
| Tracking ID / Special Links | `shopnow047c-20` applied: the published outbound links are the tagged Special Links, each destination-verified (data/intent-links.json); the tag's registration is unconfirmed (F-57) and the Associates Central one-link-per-product test has not run (F-58). | Confirm account enrollment and Partner Tag in Associates Central with the five-step protocol in `data/associates.json` (S-45); validate one destination and reporting event per product before scaling. |
| Product prices, ratings, reviews | Withheld | Confirm applicable Creators API access and permitted use under the current program terms; do not publish scraped or guessed values. |
| Click and conversion measurement | Existing browser-only click logger stores in local storage; no server endpoint, shared analytics, or Amazon conversion feed is connected. S-38 proposes five event names for review. | Choose compliant hosting, retention, consent and privacy terms, then connect authorized reports. The proposed events are not running instrumentation; the local logger is not an endpoint and does not prove purchases. |
| Search Console | No property verification or query data is recorded here | Verify the property with Google Search Console and report only its dated first-party observations. |
| Reader capture | No email/signup collection is deployed | Choose a lawful provider, purpose, retention and consent flow before collecting personal data. |
| Publishing cadence | Question-led topic calendar exists; no dated cadence is evidenced | Set an editorial frequency and review it against Search Console queries after data is available. |
| RSS | Static feed generated from the published article records | Article dates are omitted because the source records do not contain verified publication dates. |
| Campaign ledger | `data/ledger.json` is intentionally empty | Append only timestamped, authorized reports with provenance; never estimate orders or revenue. |

The full repository executive summary is [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md). For owners reviewing next steps, begin with the [Suggestions](https://kanlerxz87-cyber.github.io/Zone4/docs/suggestions.html), [Open questions](https://kanlerxz87-cyber.github.io/Zone4/docs/questions.html), [Decision log](https://kanlerxz87-cyber.github.io/Zone4/docs/decisions.html), and [Flagged for Review](https://kanlerxz87-cyber.github.io/Zone4/docs/flagged.html) pages.

## Site map

| Page | Purpose |
|---|---|
| `docs/index.html` | Shop-front publication front page: hero, lead guide, article shelf, category tiles, chooser, buyer comparison and a question-shaped content roadmap. |
| `docs/articles/index.html` | Article hub and the question-led topic calendar. |
| `docs/articles/*.html` | Seven individual buyer guides and product-format articles. |
| `docs/categories/*.html` | Dual-basket, single-basket and air-fry toaster-oven category pages. |
| `docs/products.html` | Three verified product records and a derived counter-space comparison. |
| `docs/requirements.html` | All 35 request requirements, with status, evidence and source. |
| `docs/review.html` | The review gate: 13 storefront proposals with cost, risk and proof, beside the 12 questions that must be answered before any is built. |
| `docs/about.html` | Who writes the site, how each number is checked, what it will not publish, and how to correct it. |
| `docs/imagery.html` | Every picture on the site and where it comes from; why no listing photography is copied. |
| `docs/suggestions.html` | Costed proposals awaiting review or marked by their actual status. |
| `docs/questions.html` | Known facts, missing information, who can provide it, and discovery steps. |
| `docs/decisions.html` | Options and recorded decisions; open decisions remain visible. |
| `docs/design.html` and `DESIGN_PROMPT.md` | Three design directions, anti-filler guidance, topic ideas and a prompt assembled from the design data. Slots are filled from the recorded decisions (D-12/17/18/19/35/37); only the audience slot stays open. |
| `docs/analytics.html` | Local-only click log; no network endpoint or conversion attribution. |
| `docs/verification.html`, `docs/sources.html`, `docs/policy-compliance.html` | Field-level verification, sources, and policy checklist. |
| `docs/flagged.html` | Unverified facts, unresolved link identities and review items. |
| `docs/feed.xml`, `docs/sitemap.xml`, `docs/robots.txt` | RSS 2.0 article feed, sitemap, and crawler guidance. |
The disclosure appears beneath the masthead and again in every page footer. All site pages are reachable from one flat navigation group and the footer directory (the proposal to split the primary bar from the footer directory is RD-02 on the Review page, and is not applied). Product purchase links are marked `rel="sponsored"`; this attribute does not replace the visible disclosure or prove that a link is an Amazon Special Link.

## Data and code map

| Path | Contents |
|---|---|
| `data/products.json` | Current product records (three) and cited listing fields. |
| `data/marketing.json` | Eight articles, their fact rows and editorial metadata. |
| `data/redesign.json` | The 13 storefront proposals and 12 gating questions behind `docs/review.html`; nothing in it is applied by the build. |
| `data/imagery.json` | The imagery record: every asset, what it was drawn from, and the policy that keeps listing photography off the site. |
| `data/sources.json` | Official-source registry. |
| `data/flags.json` | 72 flags; F-55/F-56 record the two additional link destinations (resolved 2026-11-19 and published under D-46), F-57 the unverified tracking ID, F-58 the pending Special Link validation, F-68/F-69 the parallel session's P4 title-drift and untagged-link findings, F-70/F-71/F-72 the 2026-11-19 register and documentation corrections. |
| `data/associates.json` | The owner-selected tracking ID, the three tagged Special Links and the five-step one-link-per-product Associates Central test protocol (2026-11-17). |
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
