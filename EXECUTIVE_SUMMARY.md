# Executive summary — Zone4 affiliate buying-guide site

**Purpose:** turn the product research register into a reader-facing publication, while keeping the facts, policy gates, missing information and decisions reviewable.
**Current Pages site:** [kanlerxz87-cyber.github.io/Zone4](https://kanlerxz87-cyber.github.io/Zone4/)
**Source of truth:** `data/*.json` → `docs/` via `scripts/build_site.py`; checked by `scripts/verify.py` and `qa/audit_site.py`.

## At a glance

- **Three existing product records** are carried from prior verification sessions: `B0CDY277D3`, `B09B7SB46R` and `B08DKYBTPH`. The verification files record the exact dates, fields read and limits; the last prior re-check was 2026-11-16.
- The latest request repeats the three previously checked URLs and adds two candidates: `https://link.amazon/B0c8moW59` and `https://link.amazon/B0f3GKalj`. The first three were re-verified on 2026-11-17 (all sessions' reads agree on the ASINs); the two new destinations remain unverified and are excluded from product pages under **F-55/F-56**. This does not mean either is invalid. The product-intent confirmation record (`data/intent-links.json`, rendered at `docs/links.html`) covers the three verified links — intended ASIN, official listing URL, confirmation date and source, observed redirect targets in a separate field that is never merged; the two remaining candidates still need their own records.
- The user supplied **`shopnow047c-20`** as the selected tracking ID. Decisions **D-01/D-14** (recorded 2026-11-17 under the owner's brief) publish the outbound product links as the tagged Special Links `https://www.amazon.com/dp/<ASIN>?tag=shopnow047c-20` — final destination URLs, each destination-verified on 2026-11-17, no shortener (2(b); 6(v)–(w)). What is not confirmed is the tag's registration in Associates Central (**F-57**); the one-link-per-product test protocol (`data/associates.json`) gates attribution claims and scaling, not publication (**Q-01, Q-47, F-03, F-58**).
- The site is an editorial affiliate publication: one flat navigation group, product chooser, format category pages, comparison, seven question-led articles, source-linked fact tables, and a site directory in every footer. The affiliate disclosure appears below the masthead and again in every footer; product links use `rel="sponsored"`.
- The decision-support system contains **43 suggestions**, **48 questions**, and **43 decisions** (32 recorded; 11 open). **F-55…F-66** make the new unverified destinations, the unverified tracking ID, the pending Special Link validation and the not-hosted endpoint visible on the Flagged for Review page.
- The static site includes `docs/feed.xml`, `docs/sitemap.xml`, and `docs/robots.txt`. RSS items are generated from article records; publication dates are omitted because none are supplied in the source data.

## Product and content status

The current reader experience centers on comparing formats and listed dimensions rather than simulated “deals” or trend rankings. Existing article topics include:

- Basket or oven-style air fryer: what should you compare?
- A no-hype checklist for comparing air-fryer capacity.
- How to assess cleanup and counter-space trade-offs.
- Questions to ask before buying a multi-function kitchen appliance.

These are editorial working hypotheses, not claims about popularity, search volume or product superiority. The design brief (`docs/design.html` and `DESIGN_PROMPT.md`) contains the visual options, writing-pattern replacements, article headline alternatives and organic-traffic topic plan. Suggestions remain reviewable before implementation; open prompt slots represent unresolved decisions rather than fabricated preferences.

## 2026-11-17 sessions (tracking-ID integration and publication build)

Two agent sessions worked the 2026-11-17 brief in parallel and their branches were merged with neither session's data discarded:

- **arena/3d2ad125-zone4 (PRs #80/#83)** shipped the publication build: question-led guides, the product-intent record (`data/intent-links.json`), the empty campaign ledger (`data/ledger.json`), the endpoint prototype (built, not hosted — F-59), the local five-event counter taxonomy and the links/measurement pages.
- **arena/68d67712-zone4 (PRs #79/#81)** shipped the navigation/footer polish, the RSS feed and decision records (D-40/D-41, S-37/S-38, Q-45/Q-46, F-55).
- **arena/1f4a7a22-zone4 (this branch)** recorded decisions D-01/D-14 under the owner's brief and published the tagged Special Links as the outbound hrefs, added the five-step Associates Central test protocol (`data/associates.json`), folded the brief's five event definitions and official attribution windows plus the provenance trail into `data/ledger.json`, added the optional `channel` field to `engine.tracking`, re-verified the three links against their official pages (2026-11-17, `data/verification-session-1f4a7a22.json`), and completed the anti-slop copy pass (D-36): the M-P3 opener no longer describes its own composition and the ASIN-and-category-path prose (F-53) is rewritten out of the three product articles.

**Merge reconciliation.** Both sessions had appended register rows at the same numbers (D-40/D-41, S-37/S-38, Q-45/Q-46) and both had produced a feed and intent/ledger records. Main's rows kept their numbers; the incoming session's rows were renumbered (D-42/D-43, S-39–S-43, Q-47/Q-48), its duplicate endpoint question, intent-record file and campaign-ledger file were withdrawn in favour of the shipped ones, and the "hold tagged links" gate was updated with a dated note: the owner's brief directs replacing ambiguous outbound links with validated Special Links, so the tagged links are published and the Associates Central test gates attribution and scaling, not publication. Flag numbering follows the board's claim order (F-55…F-66 on main; the incoming session's tracking-ID flag was withdrawn as a duplicate of F-57).

## Measurement and automation limits

| Capability | What exists | What is not yet established |
|---|---|---|
| Outbound clicks | Browser-local event log on `docs/analytics.html`; starts at zero, stores no server-side copy. | A self-hosted analytics endpoint and shared event stream are not deployed. GitHub Pages is static hosting. |
| Amazon conversions | The campaign ledger (`data/ledger.json`): the brief's five defined events (impression, click, session, order, refund) with their official attribution windows, the rollup columns (including `channel`, also an optional `engine.tracking` field), zero rows and a dated provenance trail; the raw event file is `data/tracking.jsonl`. | No Associates account reporting is connected, so orders, commissions and revenue remain unreported. No conversion score or revenue forecast is published anywhere. |
| Five-event analytics taxonomy | A proposed taxonomy is in S-38: `article_view`, `chooser_complete`, `outbound_product_click`, `reader_capture_opt_in`, and `reported_order`. | It is a review proposal, not running instrumentation. The endpoint, consent flow and reader signup are not implemented; `reported_order` must only come from authorized aggregate Associates reports. |
| Search Console | SEO metadata, generated sitemap, robots file and RSS feed. | No property verification or query/impression data is recorded. Search demand and outcomes are unknown. |
| Reader capture | No signup form is active. | No email or other personal information is collected; a provider, consent basis, retention and privacy review would be needed first. |
| Product research automation | A separate, gated engine prototype with tests. | Automated Amazon product-content retrieval and optimization are not enabled; access, API approval and policy review are prerequisites. |
| Prices, ratings and reviews | Explicitly withheld from public pages. | Display depends on authorized Amazon-served/API data and applicable terms. No price tracking or forecast is presented. |

## Decision path

1. Confirm account enrollment and that `shopnow047c-20` is the account’s Partner Tag; generate and validate one Special Link per intended product, then verify the destination and reporting signal.
2. Extend the product-intent confirmation record (`data/intent-links.json`) to the two remaining candidates: intended ASIN, official listing URL, confirmation date and source, with observed redirect targets stored separately. Keep the two new links out of product content until confirmed.
3. Decide what privacy-preserving measurement infrastructure can be hosted, and review consent, retention and event definitions before collecting visitor-level data.
4. Verify the site in Search Console and start a dated publishing cadence. Choose future topics from actual first-party query data only after it exists.
5. Review the remaining suggestions and open questions in the site’s decision queue before adopting further design, account, photography or automation changes.

These steps are recommendations, not completed owner actions. An agent without the Associates account, property verification and privacy decisions cannot truthfully finish those account-specific tasks on the owner’s behalf.

## Sources and verification

Product-specific findings link to the official listing URLs in the verification register. Policy and editorial guardrails are linked to:

- [Amazon Associates Operating Agreement](https://affiliate-program.amazon.com/help/operating/agreement)
- [Amazon Associates Program Policies](https://affiliate-program.amazon.com/help/operating/policies)
- [FTC Disclosures 101](https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers)
- [FTC Endorsements, Influencers, and Reviews](https://www.ftc.gov/business-guidance/advertising-marketing/endorsements-influencers-reviews)
- [Google Search Central: helpful, people-first content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)
- [Google Search Central: qualifying outbound links](https://developers.google.com/search/docs/crawling-indexing/qualify-outbound-links)

Start with [Suggestions](https://kanlerxz87-cyber.github.io/Zone4/docs/suggestions.html), [Open questions](https://kanlerxz87-cyber.github.io/Zone4/docs/questions.html), [Decision log](https://kanlerxz87-cyber.github.io/Zone4/docs/decisions.html), and [Flagged for Review](https://kanlerxz87-cyber.github.io/Zone4/docs/flagged.html). `COORDINATION.md` records task scopes, checks and integration history.
