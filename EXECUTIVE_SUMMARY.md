# Executive summary — Zone4 affiliate buying-guide site

**Purpose:** turn the product research register into a reader-facing publication, while keeping the facts, policy gates, missing information and decisions reviewable.
**Current Pages site:** [kanlerxz87-cyber.github.io/Zone4](https://kanlerxz87-cyber.github.io/Zone4/)
**Source of truth:** `data/*.json` → `docs/` via `scripts/build_site.py`; checked by `scripts/verify.py` and `qa/audit_site.py`.

## At a glance

- **Three existing product records** are carried from prior verification sessions: `B0CDY277D3`, `B09B7SB46R` and `B08DKYBTPH`. The verification files record the exact dates, fields read and limits; the last prior re-check was 2026-11-16.
- The latest request repeats the three previously checked URLs and adds two candidates: `https://link.amazon/B0c8moW59` and `https://link.amazon/B0f3GKalj`. The first three destinations have historical dated verification records; the two new destinations were not independently verified in this session and are excluded from product pages under **F-55**. This does not mean either is invalid. Separate product-intent confirmation records are still needed for all five distinct links.
- The user supplied **`shopnow047c-20`** as the selected tracking ID. Decisions **D-01/D-14** (recorded 2026-11-17 under the owner's brief) publish the outbound product links as the tagged Special Links `https://www.amazon.com/dp/<ASIN>?tag=shopnow047c-20` — final destination URLs, each destination-verified on 2026-11-17, no shortener (2(b); 6(v)–(w)). What is not confirmed is the tag's registration in Associates Central (**F-57**); the one-link-per-product test protocol (`data/associates.json`, S-45) gates attribution claims and scaling, not publication (**Q-01, Q-50, F-03, F-58**).
- The site is an editorial affiliate publication: one flat navigation group, product chooser, format category pages, comparison, seven question-led articles, source-linked fact tables, and a site directory in every footer. The affiliate disclosure appears below the masthead and again in every footer; product links use `rel="sponsored"`.
- The decision-support system contains **44 suggestions**, **49 questions**, and **42 decisions** (30 recorded; 12 open). **F-55** makes the two new unverified destinations visible on the Flagged for Review page.
- The static site includes `docs/feed.xml`, `docs/sitemap.xml`, and `docs/robots.txt`. RSS items are generated from article records; publication dates are omitted because none are supplied in the source data.

## Product and content status

The current reader experience centers on comparing formats and listed dimensions rather than simulated “deals” or trend rankings. Existing article topics include:

- Basket or oven-style air fryer: what should you compare?
- A no-hype checklist for comparing air-fryer capacity.
- How to assess cleanup and counter-space trade-offs.
- Questions to ask before buying a multi-function kitchen appliance.

These are editorial working hypotheses, not claims about popularity, search volume or product superiority. The design brief (`docs/design.html` and `DESIGN_PROMPT.md`) contains the visual options, writing-pattern replacements, article headline alternatives and organic-traffic topic plan. Suggestions remain reviewable before implementation; open prompt slots represent unresolved decisions rather than fabricated preferences.

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

1. Confirm account enrollment and that `shopnow047c-20` is the account’s Partner Tag (F-57), then run the five-step one-link-per-product protocol in `data/associates.json` (S-45) and verify the destination and reporting signal. The tagged Special Links are already the published outbound links; the test gates attribution and scaling, not publication (D-01/D-14, F-58).
2. Create a product-intent confirmation record for each of the five distinct intended products: intended ASIN, official listing URL, confirmation date and source. Store observed redirect targets separately. Keep the two new links out of product content until confirmed.
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


---

## Session notes — 2026-11-17 (arena/cc32105d-zone4): integration and anti-slop finish

This session's brief overlapped two parallel sessions that landed first on `main` (`arena/68d67712-zone4`, PRs
#79/#81; `arena/3d2ad125-zone4`, PRs #80/#83). Their publication build — `data/intent-links.json`, `data/ledger.json`,
`data/publishing.json`, `data/guides.json`, `analytics-endpoint/`, `docs/measure.js`, `docs/links.html`,
`docs/measurement.html`, the footer directory and the RSS feed — is kept as canonical. This session merged their work
and re-applied only its unique delta:

- **F-53 corrected** (the last machine-output defect: identifiers printed as prose in the three product openers):
  the openers are rewritten across all eight articles under recorded decision **D-36**. D-35 (warm-editorial
  specification), D-37 (steady headline register) and D-38 (storefront reading order) were recorded the same day.
- **F-67 added**: the identifier-format check behind the product-intent record. Amazon's published ASIN guide
  (read live 2026-11-17) defines an ASIN as a 10-character code appearing after `/dp/`; the three published link
  path codes are nine characters and appear in the short-link path, so they are not ASINs. The check is cited in
  `data/intent-links.json` and in the flag.
- **2026-11-17 re-verification** (15-row record: `data/verification-session-cc32105d.json`): the three links
  re-resolve to the recorded ASINs with no tag (F-03 stands); P2's second title segment again reads the later
  variant (F-44, fifth agreeing read; F-26, F-50 stand); the rotated carousel slots each showed the originally
  stored ASIN again (F-29); Table 1 and the OA (2025-10-15) / Policies (2026-04-14) dates re-read unchanged.
- **New register rows**: Q-47 (reader email consent), Q-48 (Search Console verification), Q-49 (first-party
  reports for the ledger); S-39 (validated Special Links replacement workflow), S-40 (Search Console property);
  D-42 (Search Console verification, open). This session's duplicate rows and flags were dropped in favour of the
  merged register (its session-local F-55 was renumbered to F-67; its planned F-56 duplicates F-59 on main).

Open after this session: 12 decisions (D-01, D-02, D-08, D-13, D-14, D-15, D-16, D-22, D-39, D-40, D-41, D-42).
The named blocker is unchanged: an Associates account and the tracking ID first, because nothing can earn until
the links carry a tag.

## Session notes — 2026-11-17 (arena/1f4a7a22-zone4): tracking-ID integration and the two merge reconciliations

This session recorded decisions **D-01/D-14** under the owner's 2026-11-17 brief and implemented them: the published outbound links are the tagged Special Links (`data/associates.json` holds the ID, the three Special Links and the five-step Associates Central test protocol; S-45, Q-50). It re-verified the three links against their official pages (2026-11-17, `data/verification-session-1f4a7a22.json`: same ASINs, still no `tag=` in the supplied links — F-03 stands), folded the brief's five event definitions with their official attribution windows and the provenance trail into `data/ledger.json`, added the optional `channel` field to `engine.tracking`, completed the anti-slop copy pass (D-36: the M-P3 opener and the three product articles' ASIN-and-category-path paragraphs, F-52/F-53), and appended the Associates-record and measurement gates to `scripts/verify.py` and `qa/audit_site.py`.

**Two merge reconciliations** (after PRs #79–#83, then after PRs #84–#86): three other sessions worked overlapping slices of the same brief. Each time, main's register rows kept their numbers; this session's rows were renumbered to the next free ids (final state: D-43 endpoint hosting, D-44 measurement surfaces in the design brief, D-45 keep the shipped feed, S-45 test protocol, S-46 feed, Q-50 tag registration); rows duplicated by peers' shipped work were withdrawn (following the established duplicate-drop precedent); the parallel intent/ledger files were withdrawn in favour of the canonical ones with their unique content folded in additively; and the "hold tagged links" gate was updated with dated notes — the owner's brief directs replacing ambiguous outbound links with validated Special Links, so the tagged links are published and the Associates Central test gates attribution and scaling, not publication. Flag citations point at main's numbering (F-57 unverified tracking ID, F-58 pending validation; F-55/F-56 are the two held thermometer candidates).

## Full source list

1. Associates Program Operating Agreement (updated 2025-10-15) — https://affiliate-program.amazon.com/help/operating/agreement
2. Associates Program Policies (updated 2026-04-14; Commission Income Statement, Participation Requirements, IP License, Trademark Guidelines) — https://affiliate-program.amazon.com/help/operating/policies
3. Public Associates Standard Commission Income Statement (Table 1, category rates) — https://affiliate-program.amazon.com/help/node/topic/GRXPHT8U84RAYDXZ
4. Historic Appendix schedule link (redirects to sign-in; superseded for category rates) — https://affiliate-program.amazon.com/help/operating/schedule
5. Amazon Associates disclosure help page — https://affiliate-program.amazon.com/help/node/topic/GPXFHVYZMTGPUMPE
6. Amazon ASIN guide (10-character standard) — https://sell.amazon.com/blog/what-is-an-asin
7. PA-API 5 deprecation / Creators API notice — https://affiliate-program.amazon.com/creatorsapi/docs/en-us/paapiv5-deprecation
8. Amazon Conditions of Use (updated 2026-08-14) — https://www.amazon.com/gp/help/customer/display.html?nodeId=508088
9. Amazon product pages — https://www.amazon.com/dp/B0CDY277D3 · https://www.amazon.com/dp/B09B7SB46R · https://www.amazon.com/dp/B08DKYBTPH (plus the three submitted `link.amazon` URLs)
10. Amazon 404 evidence for slug-as-ASIN lookups — https://www.amazon.com/dp/B04G1MEwY (and the other two slugs)
11. FTC Disclosures 101 for Social Media Influencers — https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers
12. Third-party, non-official corroboration of the `link.amazon` domain — https://linktw.in/link-amazon-vs-linktwin (flagged as non-official)
13. Google Search Central — Creating helpful, reliable, people-first content (who/how/why, effort, originality, the caution against fabricated authorship) — https://developers.google.com/search/docs/fundamentals/creating-helpful-content *(read 2026-11-15)*
14. Google Search Central — Spam policies for Google web search (thin affiliation, scaled content abuse, paid-link qualification) — https://developers.google.com/search/docs/essentials/spam-policies *(read 2026-11-15)*
15. Google Search Central — Control your snippets in search results (unique meta description per page) — https://developers.google.com/search/docs/appearance/snippet *(read 2026-11-15)*
16. Google Search Central — Qualify outbound links (`rel="sponsored"` for paid links) — https://developers.google.com/search/docs/crawling-indexing/qualify-outbound-links *(read 2026-11-15)*
17. Google Search Central — Understanding page experience in Google Search results — https://developers.google.com/search/docs/appearance/page-experience *(read 2026-11-15)*
18. Google Search Central — Google Search and AI-generated content: automation used to manipulate rankings is a spam violation, appropriate use of automation is not against the guidelines, AI gives content no special gains, and bylines and automation disclosures are worth considering — https://developers.google.com/search/blog/2023/02/google-search-and-ai-content *(read in full 2026-11-15; quoted verbatim in the questions register as Q-23…Q-37 — `S-GSC-AI` in `data/sources.json`)*

**A note on why Google's documentation is cited here.** Amazon's rules govern whether this site may publish a fact. Google's
documentation governs whether the page can be found and whether it is the kind of page a search engine wants to rank. The two are
different questions and both matter to the brief, which asks for organic traffic. Only Google's own documentation is used for the
second, and no ranking, traffic or growth figure is published anywhere on the site.

*Every table row above carries its source; values that could not be confirmed from an official source are blank, withheld, or flagged — never inferred.*