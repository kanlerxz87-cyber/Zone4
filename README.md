# Zone4 — air-fryer buying guides and affiliate research

**Live site:** [kanlerxz87-cyber.github.io/Zone4](https://kanlerxz87-cyber.github.io/Zone4/)
**Published source:** GitHub Pages serves the repository root, which redirects to `docs/`. `scripts/build_site.py` is the only generator that writes the published pages. The separate research engine renders a private preview under `build/site-preview/`.

Zone4 is a small editorial buying-guide site backed by a source register. It publishes product facts only where the repository records an official source, leaves unsupported values blank, and keeps review questions and unresolved risks visible rather than presenting them as findings.

## Executive summary

- The currently verified product register contains **three** earlier supplied products: ASINs `B0CDY277D3`, `B09B7SB46R`, and `B08DKYBTPH`. Their link and listing checks are recorded in the dated verification data; the latest prior re-check is 2026-11-16.
- The latest brief repeats the three earlier URLs and adds two more: [`B0c8moW59`](https://link.amazon/B0c8moW59) and [`B0f3GKalj`](https://link.amazon/B0f3GKalj). All five were re-resolved to listings on 2026-11-19 (`data/intent-links.json` keeps the intended ASIN and the observed redirect in separate fields). The two later links open meat-thermometer listings and are published in their own category under decision **D-46**; resolution is not a finding that any supplied link is valid or invalid.
- The user supplied `shopnow047c-20` as the selected tracking ID. Decisions **D-01/D-14** (recorded 2026-11-17 under the owner's brief) publish every outbound product link as the tagged Special Link `https://www.amazon.com/dp/<ASIN>?tag=shopnow047c-20` — the final destination URL with the tag as its parameter (Participation Requirements 2(b)), no shortener. The supplied short links stay recorded verbatim in `data/intent-links.json` and are not judged valid or invalid (Zone3 FLG-003 unresolved). What remains unconfirmed is the tag's registration in Associates Central (**F-57**); the one-link-per-product test protocol (`data/associates.json`, S-45) gates attribution claims and scaling, not publication. See **Q-01 / Q-50 / F-03 / F-58** and the official [Amazon Associates policies](https://affiliate-program.amazon.com/help/operating/policies).
- Prices, ratings, review counts, product-level commission assignments, search demand, orders and revenue are not invented or forecast. The public category commission table is a reference only; no per-ASIN mapping is confirmed.
- The site includes a three-question product chooser, format categories, ten articles and four published question-led guides, product comparison and source-backed tables, an [About page](https://kanlerxz87-cyber.github.io/Zone4/docs/about.html) and an [imagery policy page](https://kanlerxz87-cyber.github.io/Zone4/docs/imagery.html). A generated RSS feed is at [`docs/feed.xml`](https://kanlerxz87-cyber.github.io/Zone4/docs/feed.xml); the sitemap and `robots.txt` are also generated. Feed items carry `pubDate` only where the record names a dated publication source (decision D-49), and every page declares a `rel="canonical"` URL.
- The storefront review gate is one page: **Review what to change** (`docs/review.html`, data `data/redesign.json`) files the proposals for the shop, each with cost, risk, the check that proves it worked and an official source, beside the questions that must be answered before any is built. Four carry a dated application (RD-01 complete; RD-03, RD-06 and RD-08 partly). Every count on that page is printed from its register, so it cannot drift.
- **Measurement first:** the five-event client and reference collector are built, with route/category/ASIN allowlists, credential-free/no-Referer delivery, 30-day staged aggregate retention and isolated contract tests. Collection stays **off**: `data/measurement.json` has no endpoint or deployment evidence. The [launch checklist](https://kanlerxz87-cyber.github.io/Zone4/docs/measurement.html#launch-checklist) shows the known facts, missing information and discovery steps; a URL alone cannot enable it (D-55, F-97). Hosting-use and production/privacy review remain open (D-56, F-98). No simulated test traffic is a reported click or order.
- The suggestion and decision pages are the review gate: **85 suggestions**, **67 questions**, **57 decisions** (43 recorded, 14 open), and **99 flags** are maintained in the JSON registers and published to their matching pages. The [Decision centre](https://kanlerxz87-cyber.github.io/Zone4/docs/decision-centre.html) renders the open decisions as three ready-weighed paths (SG-36) so a reviewer can choose a path before anything is implemented, and an "Only the account holder can do these" panel (D-51) that aggregates the account-side gates. The safe storefront polish that needs no owner account (ItemList structured data, a dated gift-season front-page section, guide short-answer blocks and a decision-centre summary) shipped under recorded decision D-53 (S-57..S-60); the measurement questions it raises are Q-60..Q-63. Unresolved and access-dependent work does not get reported as complete.

## Important limits and next checks

| Topic | Current state | What would establish it |
|---|---|---|
| Product intent / two new links | `data/intent-links.json` records the product-intent confirmation (intended ASIN and official listing URL vs. observed redirect targets, kept separate) for all five submitted links. The two meat-thermometer links (P4, P5) were re-resolved on 2026-11-19 to the ASINs recorded and are published as tagged Special Links under decision D-46 (F-55 resolved on identity; F-56 resolved by D-46). The link path codes are not ASINs (F-67). | Confirm each product's Special Link in Associates Central (one-link test, F-58); confirm the tracking ID (F-57). The thermometer scope can be reversed by the owner (D-46). |
| Tracking ID / Special Links | `shopnow047c-20` applied: the published outbound links are the tagged Special Links, each destination-verified (data/intent-links.json); the tag's registration is unconfirmed (F-57) and the Associates Central one-link-per-product test has not run (F-58). | Confirm account enrollment and Partner Tag in Associates Central with the five-step protocol in `data/associates.json` (S-45); validate one destination and reporting event per product before scaling. |
| Product prices, ratings, reviews | Withheld | Confirm applicable Creators API access and permitted use under the current program terms; do not publish scraped or guessed values. |
| Click and conversion measurement | Five site-side counters and a bounded reference collector are implemented but disabled. `data/measurement.json` requires dated launch evidence; the local browser log is separate. No production analytics or Amazon conversion feed is connected. [Implementation and launch record](data/measurement.json). | Resolve MC-01..MC-05: permitted hosting, secure runtime, privacy/logging/consent, deletion and deployed contract checks. The reference Python server is not a production service; counts are best-effort events, not visitors, sessions or orders. |
| Commercial hosting | A Pages build is not hosting-use approval. [GitHub Pages limits](https://github.com/github/docs/blob/main/content/pages/getting-started-with-github-pages/github-pages-limits.md) and [Python's production warning](https://github.com/python/cpython/blob/3.11/Doc/library/http.server.rst) require a review path (F-98). | Obtain hosting-use clarification or permitted commercial hosting and a secure runtime. Review infrastructure logs too; the collector's aggregate-only storage cannot establish whole-service anonymity. D-56/Q-66/Q-67 remain open. |
| Search Console | No property verification or query data is recorded here | Verify the property with Google Search Console and report only its dated first-party observations. |
| Reader capture | No email/signup collection is deployed | Choose a lawful provider, purpose, retention and consent flow before collecting personal data. |
| Publishing cadence | A 14-day question-led cadence is recorded (2026-11-17) and the calendar extends to the thermometer listings as Wave 3 (D-50); whether to front-load the 2026-11-27..2026-12-25 gift window is open (D-52); search-demand review waits on Search Console (Q-59) | Review it against Search Console queries after data is available. |
| RSS | Static feed generated from the published article records | Article dates are omitted because the source records do not contain verified publication dates. |
| Campaign ledger | `data/ledger.json` is intentionally empty | Append only timestamped, authorized reports with provenance; never estimate orders or revenue. |

The full repository executive summary is [`EXECUTIVE_SUMMARY.md`](EXECUTIVE_SUMMARY.md). For owners reviewing next steps, begin with the [Suggestions](https://kanlerxz87-cyber.github.io/Zone4/docs/suggestions.html), [Open questions](https://kanlerxz87-cyber.github.io/Zone4/docs/questions.html), [Decision log](https://kanlerxz87-cyber.github.io/Zone4/docs/decisions.html), and [Flagged for Review](https://kanlerxz87-cyber.github.io/Zone4/docs/flagged.html) pages.

## Site map

| Page | Purpose |
|---|---|
| `docs/index.html` | Shop-front publication front page: hero, the five listings as shop cards, lead guide, article shelf, category tiles, the three-question chooser, buyer comparison and a question-shaped content roadmap. |
| `docs/articles/index.html` | Article hub and the question-led topic calendar. |
| `docs/articles/*.html` | Eight individual buyer guides and product-format articles. |
| `docs/guides/*.html` | Four question-shaped buying guides and the guides hub. |
| `docs/categories/*.html` | Dual-basket, single-basket, air-fry toaster-oven and meat-thermometer category pages. The thermometer page carries its own two-question chooser with a no-script fallback table. |
| `docs/products.html` | Five product records and a derived counter-space comparison. |
| `docs/requirements.html` | All 36 request requirements, with status, evidence and source. |
| `docs/review.html` | The review gate: every storefront proposal with its cost, risk and proof, beside the questions that must be answered before any is built. Counts are printed on the page from the register. |
| `docs/about.html` | Who writes the site, how each number is checked, what it will not publish, and how to correct it. |
| `docs/imagery.html` | Every picture on the site and where it comes from; why no listing photography is copied. |
| `docs/suggestions.html` | Costed proposals awaiting review or marked by their actual status. |
| `docs/questions.html` | Known facts, missing information, who can provide it, and discovery steps. |
| `docs/decisions.html` | Options and recorded decisions; open decisions remain visible. |
| `docs/decision-centre.html` | The review-before-you-build hub: the registers in one place, the order to work in, and three ready-weighed paths through the open decisions. |
| `docs/information-gaps.html` | What the project can prove, what it cannot, and who can close each gap. |
| `docs/links.html`, `docs/measurement.html` | Product-intent links and measurement: five site-side counters, a source-linked five-question launch checklist with blank evidence, retention, and a separate empty authorized-report ledger. |
| `docs/design.html` and `DESIGN_PROMPT.md` | Three design directions, anti-filler guidance, topic ideas and a prompt assembled from the design data. Slots are filled from the recorded decisions (D-12/17/18/19/35/37); only the audience slot stays open. The adopted DIR-A warm-editorial presentation layer is applied to the storefront and articles under D-48 (2026-11-19); the directions and topic programme remain a proposal register. The ten-topic calendar extends to the two published thermometer listings as Wave 3 (D-50, topics T-09/T-10, guides due on their cadence dates from 2026-12-01). |
| `docs/analytics.html` | Local-only click log; no network endpoint or conversion attribution. |
| `docs/verification.html`, `docs/sources.html`, `docs/policy-compliance.html` | Field-level verification, sources, and policy checklist. |
| `docs/flagged.html` | Unverified facts, unresolved link identities and review items. |
| `docs/feed.xml`, `docs/sitemap.xml`, `docs/robots.txt` | RSS 2.0 article feed, sitemap, and crawler guidance. |
The disclosure appears beneath the masthead and again in every page footer. All site pages are reachable from one flat navigation group and the footer directory (the proposal to split the primary bar from the footer directory is RD-02 on the Review page, and is not applied). Product purchase links are marked `rel="sponsored"`; this attribute does not replace the visible disclosure or prove that a link is an Amazon Special Link.

## Data and code map

| Path | Contents |
|---|---|
| `data/products.json` | Current product records (three) and cited listing fields. |
| `data/marketing.json` | Ten articles, their fact rows and editorial metadata. Five records carry `published_utc` with a dated `published_source`; the five earliest carry no date at all, because no dated record in this checkout fixes their first publication (decision D-49, question Q-57). |
| `data/sources.json` | Official-source registry. |
| `data/flags.json` | 99 flags; F-55/F-56 record the two additional link destinations (resolved 2026-11-19 and published under D-46), F-57 the unverified tracking ID, F-58 the pending Special Link validation, F-68/F-69 the parallel session's P4 title-drift and untagged-link findings, F-70/F-71/F-72 the 2026-11-19 register and documentation corrections, F-81 the 2026-11-19 correction of four flags that still described the pre-D-01 link state, F-73 the short-link citations (arena/79fe1c8d-zone4), F-74 a retired duplicate pointer of F-76 (the PR #98 renumbering sweep left the same finding under two ids; rewritten 2026-11-19), F-75 the 'AI slop' claim recorded as unverified, F-76 the 63 tagged links missing rel="sponsored" (corrected), F-77 the thermometer shop cards' air-fryer capacity line (corrected), F-78 the P4 newer-model notice (owner decision), F-79 the missing social preview image (corrected), F-80 the front-page h1 rendered below the product cards (corrected), F-82 the undefined `.mono` class (arena/d7393cc0-zone4, fixed under D-48), F-83 the mis-cited flag reference in an article fact note (arena/0272d56e-zone4, corrected), F-84 the five feed items with no pubDate (arena/0272d56e-zone4, corrected under D-49), F-85 the verification page's field-by-field log claim and its whole-table date (arena/0272d56e-zone4), F-86 the missing canonical URLs (arena/0272d56e-zone4, corrected), F-87 the flag-text duplication audit (arena/0272d56e-zone4), F-88 a retired duplicate pointer of F-76 (the PR #102 sweep re-appended the sponsored-rel finding; rewritten 2026-11-19), F-89 eleven suggestion rows whose statuses their linked decisions had already resolved (corrected 2026-11-19; the build now checks suggestion-decision status agreement), F-90 two publication texts that lagged D-46 (corrected 2026-11-19), F-91 the gift-season section's calendar-dates-only scope (owner may change the cadence, D-52), F-92 the ItemList's omission of offers, price and ratings (corrected 2026-11-19), F-94 hand-typed documentation counts that disagreed with the registers (corrected 2026-11-19; counts are now generated and gated by scripts/check_doc_counts.py), F-95 the computed catalogue-count fix, F-96 the earlier deployment/attribution boundary, F-97 the evidence-gated measurement-contract corrections, F-98 the unresolved commercial-hosting/runtime/logging review, and F-99 the browser-verified navigation regression. |
| `data/measurement.json` | Disabled endpoint configuration, the five site-side counter definitions and the five evidence-gated launch questions. Source reads are technical/hosting reads, not fresh product verification. |
| `analytics-endpoint/client.js`, `analytics-endpoint/server.py` | Single browser source and aggregate-only reference collector. Standard-library Python collector, not a production server; Node browser contracts are also required by the test suite. |
| `data/associates.json` | The owner-selected tracking ID, the three tagged Special Links and the five-step one-link-per-product Associates Central test protocol (2026-11-17). |
| `data/suggestions.json`, `data/questions.json`, `data/decisions.json` | Review-before-implementation decision-support registers; `data/decisions.json` also carries the three-path triage the Decision centre renders (SG-36). |
| `data/requirements.json`, `data/policies.json` | Requirement status and compliance register. |
| `data/tracking.jsonl` | Empty-by-design campaign/event ledger; append only authorized, provenance-backed data. |
| `data/verification-session-*.json` | Dated verification records; read each record for its exact scope and limits. The latest, `verification-session-713e855d.json` (2026-11-20), re-read all five listing titles and breadcrumbs and recomputed the catalogue counts; the 2026-11-19 record `verification-session-d696a32c.json` also re-read the Operating Agreement and Program Policies. |
| `scripts/build_site.py` | Static Pages-site builder, including RSS, sitemap, robots.txt, the grouped sidebar and the per-page `BreadcrumbList`/`Article`/`WebSite`/`ItemList` structured data. |
| `scripts/build_extras.py` | Guides, the product-intent record, the measurement page, the feed and the shop/article surfaces the builder calls. |
| `scripts/make_social_card.sh` | Builds `docs/social-card.png`, the 1200x630 preview image behind `og:image`/`twitter:image`. Text and shapes only: no product photography (S-18 is still open). |
| `scripts/verify.py` | Deterministic data, disclosure, source, link, SEO and page-directory checks. |
| `qa/audit_site.py` | Independent audit of committed HTML. |
| `engine/`, `tests/`, `ENGINE.md` | Separate research-engine prototype, its tests and its operational limits. |
| `COORDINATION.md` | Shared task board and verification/merge history. |
## Build and checks

Run from a clean checkout with Python 3.11+ and Node 22:

```bash
bash scripts/make_social_card.sh      # a bash + ImageMagick script, not Python; only after changing the card's copy. Its numerals now come from the registers (D-54).
python3 scripts/build_site.py
python3 scripts/render_design_prompt.py
python3 scripts/verify.py
python3 qa/audit_site.py
python3 -m engine.cli build
python3 -m unittest discover -s tests
node --test tests/measure_client.test.js
python3 scripts/check_doc_counts.py
python3 tools/check_links.py --root docs
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

## Publication and measurement release — 2026-11-20

The homepage now uses a compact native-menu masthead, an edited article shelf, five product cards split between air fryers and thermometers, original footprint diagrams, and the parallel sessions’ editorial food artwork (explicitly not product/test photography). The calendar and audit counters no longer occupy the shop window; every register remains in the footer and Research & review menu. SG-47/SG-48 and Q-65 add a measurement acceptance plan and qualitative usability-review proposal before further optimization.

Fresh verification is limited to the five official listing titles and breadcrumbs, plus the named policy excerpts in [`data/verification-session-ba03ce6b.json`](data/verification-session-ba03ce6b.json). P2’s known title variant (F-44) remains flagged; all other product facts retain their earlier dated verification. No claim of a full fresh spec check, live analytics, approved tag, verified conversion or guaranteed organic traffic is made. See the [measurement checklist](analytics-endpoint/README.md), [executive summary](EXECUTIVE_SUMMARY.md), and [Flagged for Review](https://kanlerxz87-cyber.github.io/Zone4/docs/flagged.html#F-96).
