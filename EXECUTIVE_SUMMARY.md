# Executive summary — Zone4 affiliate buying-guide site

**Purpose:** make a source-grounded buying publication from the supplied product links, with questions, decisions, suggestions and unresolved evidence visible to reviewers.
**Current Pages site:** [Zone4](https://kanlerxz87-cyber.github.io/Zone4/)
**Source of truth:** `data/*.json` → `docs/` via `scripts/build_site.py`; checked by `scripts/verify.py` and `qa/audit_site.py`.

## At a glance

- **Five supplied product links are represented:** three air-fryer listings and two meat-thermometer listings. The product-intent register stores intended ASIN, official listing URL, confirmation date and source independently from observed redirect targets. The dated verification records describe what was actually re-read and where page fields were unavailable. A 2026-11-20 re-read compares titles and category breadcrumbs only (data/verification-session-ba03ce6b.json); other specifications keep their earlier dates; no claim is made that the supplied short links are invalid. See [product-intent records](https://github.com/kanlerxz87-cyber/Zone4/blob/main/data/intent-links.json), [verification sessions](https://github.com/kanlerxz87-cyber/Zone4/tree/main/data), and the official listing pages: [P1](https://www.amazon.com/dp/B0CDY277D3), [P2](https://www.amazon.com/dp/B09B7SB46R), [P3](https://www.amazon.com/dp/B08DKYBTPH), [P4](https://www.amazon.com/dp/B0DHZTCNR5), [P5](https://www.amazon.com/dp/B0DZFD6R9Z).
- **Tracking ID:** `shopnow047c-20` was supplied by the user and used in the published tagged Special Links under D-01/D-14/D-46. Its registration and activity in the Associates account are not confirmed here (F-57). The five-step, one-link-per-product Associates Central check has not been performed (F-58); do not treat tagged URLs as proof of account attribution. The supplied short links remain recorded without a validity judgment, consistent with [FLG-003](https://kanlerxz87-cyber.github.io/Zone3/flagged.html#FLG-003) and the [Amazon Program Policies](https://affiliate-program.amazon.com/help/operating/policies).
- **Reader-facing publication:** a products-first landing page, three air-fryer format categories, a meat-thermometer category, product comparison and chooser, ten articles and four question-led guides. Titles are editorial hypotheses—not verified claims about popularity, search volume, conversion or superiority. The cadence is one guide every 14 days; the next recorded due date is 2026-12-01. New guides enter the generated sitemap and RSS feed through the same build.
- **Review before implementation:** the site has dedicated [Suggestions](https://kanlerxz87-cyber.github.io/Zone4/docs/suggestions.html), [Open questions](https://kanlerxz87-cyber.github.io/Zone4/docs/questions.html), [Decision centre](https://kanlerxz87-cyber.github.io/Zone4/docs/decision-centre.html), [Information gaps](https://kanlerxz87-cyber.github.io/Zone4/docs/information-gaps.html) and [Flagged for review](https://kanlerxz87-cyber.github.io/Zone4/docs/flagged.html) pages. The registers distinguish known facts from missing inputs, give discovery steps, and label owner-only gates. Current register counts: **85 suggestions**, **67 questions**, **57 decisions** (43 recorded; 14 open), and **99 flags**. Counts and details are read from the registers by the site build.
- **Disclosure and links:** the Associates disclosure appears directly under the masthead on every page and repeats in every footer. Product purchase links use `rel="sponsored"`. Source-linked fact tables leave unconfirmed values blank and link the row to the official listing or policy source. Prices, ratings and review counts are withheld; no unverified trend or revenue claims are presented.
- **Search readiness, not measured reach:** canonical metadata, structured data, `robots.txt`, sitemap and RSS feed are present. Search Console is not verified; no search queries, impressions or rankings are known. Search demand must not be invented.
- The decision-support system contains **85 suggestions**, **67 questions**, and **57 decisions** (43 recorded; 14 open), with **99 flags**. The [Decision centre](https://kanlerxz87-cyber.github.io/Zone4/docs/decision-centre.html) additionally renders the open decisions as three ready-weighed paths (SG-36, shipped 2026-11-19) and an "Only the account holder can do these" panel (D-51, shipped 2026-11-19). The question-led topic calendar extends to the two published thermometer listings as Wave 3 (D-50: T-09 "Instant-read or wireless? Matching the thermometer to the way you cook", T-10 "Stocking stuffer or serious tool? What each thermometer listing promises on its own title line"; the guides are written on their 14-day cadence dates, next due 2026-12-01; the gift-window front-load question is open as D-52). **F-55** and **F-56** are resolved: both additional supplied links were re-resolved on 2026-11-19 to their recorded meat-thermometer ASINs and are published as tagged Special Links in their own category under **D-46**. The adopted DIR-A warm-editorial presentation layer is applied to the storefront and articles under **D-48** (masthead, palette/typography, editorial cards, mono figures, paper hero, sticky disclosure, byline method link); the sticky evidence rail (SG-45) remains proposed, not built; the guide short-answer block (SG-44 partial) shipped under D-53. The safe storefront polish that needs no owner account - ItemList structured data (S-57), a dated gift-season front-page section (S-58), guide short-answer blocks (S-59) and a decision-centre summary (S-60) - shipped under recorded decision D-53 (2026-11-19); the measurement questions it raises are Q-60..Q-63, and the gift-window cadence question stays open as D-52 (F-91).

## Product-intent distinction

The records now contain an intended ASIN, official listing URL, confirmation date and source for each of the five URLs, with observed redirect targets in a separate field. This satisfies the data-record requirement; it does **not** independently prove a personal product preference beyond the links in the brief. D-13 and D-40 remain open in the decision register, so the unresolved question is whether any supplied destination was not actually the product the owner wanted—not whether a record field is missing. A replacement requires an identified intended product and a fresh official-source check; the site must not guess.

## Measurement and automation limits

| Capability | Implemented / recorded | Not established |
|---|---|---|
| Browser-local click log | The Analytics page has a local-only log; it stores no server-side copy. | A shared click count or traffic total is not available. |
| First-party event instrumentation | The five site events remain `page_view`, `outbound_click`, `guide_read_75`, `category_click`, and `feed_click`. The client/collector now share public-route, category and ASIN allowlists, omit credentials/Referer, and aggregate category destinations separately. Staged retention is 30 UTC day buckets. [Implementation and launch record](https://github.com/kanlerxz87-cyber/Zone4/blob/main/data/measurement.json). | Collection is disabled. Every MC-01..MC-05 confirmation remains blank, so the build emits no endpoint; setting a URL alone fails. Local contracts are tested, not production hosting, consent or live delivery (F-59/F-97). Counts are not unique visitors or reported Amazon activity. |
| Hosting and privacy readiness | A source-linked launch checklist names known facts, missing evidence and discovery steps. The collector stores no visitor identifiers; this does not control infrastructure logs. [GitHub Pages limits](https://github.com/github/docs/blob/main/content/pages/getting-started-with-github-pages/github-pages-limits.md), [Pages security IP logging](https://github.com/github/docs/blob/main/content/pages/getting-started-with-github-pages/what-is-github-pages.md), [Python production warning](https://github.com/python/cpython/blob/3.11/Doc/library/http.server.rst). | A Pages deployment is not commercial-use permission, and the reference Python runtime is not production hosting. Resolve D-56/Q-66/Q-67: permitted hosting, secure HTTPS runtime, controller/consent, every logging layer, deletion and isolated deployed contract evidence (F-98). No host purchase, migration or legal conclusion is made. |
| Amazon campaign ledger | `data/ledger.json` defines a separate five-event reporting vocabulary (`impression`, `click`, `session`, `order`, `refund`) and authorized-report provenance fields. | The ledger has zero rows because no authorized Associates report is connected. These five report event types are not the same as the five site analytics events. No conversion score or revenue forecast is published. |
| Search Console | Sitemap, feed and crawl metadata are shipped. | Property verification and query/impression data require account-holder action (D-42). |
| Product research automation | A tested engine prototype and policy gates are in the repository. | No Amazon product-content retrieval or optimization is enabled; API access, authorization and policy review remain prerequisites. |
| Reader capture | No signup form is active and no personal information is collected. | Provider, consent, retention and privacy review have not been selected. |

## Priority questions and the next evidence to collect

1. **Attribution (F-57/F-58):** is `shopnow047c-20` active in the enrolled Associates account? An account holder must confirm it in Associates Central, test one Special Link per product, verify each destination, then confirm clicks in the account report. No attribution is claimed before that report exists.
2. **Product intent (D-13/D-40):** do the five destinations supplied in the brief represent the intended products? The records are complete for those destinations; only the owner can say if a different product was meant. If so, identify the desired item; the listing identifier and source will be re-verified before publication.
3. **Hosting and analytics activation (D-41/D-43/D-56):** does the host permit this intended commercial use, and what production runtime/privacy boundary is established? Obtain hosting-use clarification or permitted commercial hosting; review logging, consent and deletion and complete the dated MC-01..MC-05 evidence gate before enabling. A static deployment or passing local tests is not proof of production readiness (F-59/F-98).
4. **Search measurement (D-42):** who can verify the property in Search Console and submit the sitemap? Until then, topic titles remain editorial hypotheses; query-led prioritization is unavailable.
5. **API / prices / commission:** what approved data access and explicit authorization exist, and which exact commission category applies to each ASIN? Keep prices, ratings and per-product rates blank until official evidence and required access are available.
6. **Photography and reader capture:** are owner photographs available, and should any opt-in channel be created? Decide image rights, provider, consent, retention and deletion before implementing either.

The [question register](https://kanlerxz87-cyber.github.io/Zone4/docs/questions.html) provides the current known/unknown answer and a discovery method for each question. The [Suggestions page](https://kanlerxz87-cyber.github.io/Zone4/docs/suggestions.html) offers options with effort, risk and a success check so a reviewer can compare paths before implementation. These registers preserve current unknowns rather than filling them by inference.

## Publishing and organic discovery

The published titles lead with buyer questions—format, capacity, cleanup, counter space and multi-function choices—rather than claims that a product is trending or a “best” pick. The editorial calendar is deliberately question-shaped and evergreen until authorized query data exists. Each new guide should be sourced, dated from its own publication record, linked to its product/category pages, and added to the sitemap and feed in the same build. Do not use fabricated authorship, popularity, performance or demand claims to make the site appear more established.

## Sources and verification

The 2026-11-20 measurement pass reviewed the client/collector/build contract and official GitHub Pages limits/overview, Python production warning, MDN transport controls, and Associates privacy/artificial-activity rules. It did not re-read product specification tables or gain account access. Existing product values and their earlier read dates are unchanged. Local test fixtures are never counted as traffic or imported as reports.

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

**2026-11-19 update (arena/4cfacb30-zone4).** All five submitted links are now published. The two meat-thermometer links were re-resolved from their short links; each opens to the ASIN recorded (B0DHZTCNR5, B0DZFD6R9Z), and the listing titles and breadcrumbs were read. Under decision D-46, taken by the agent under the owner's standing no-manual-input brief, they sit in a Meat thermometers category with the same tagged Special Link status as the three air-fryer listings. Their thermometer guide waits for its cadence date (2026-12-01). Two findings from the same session need review: the P4 title on the live page differs from the 2026-11-17 record (F-68), and most Amazon links on the site were untagged, which Program Policies 2(b) does not allow; every www.amazon.com link now carries the tag and the build fails if one does not (F-69). The Associates Central tests (F-57, F-58) remain owner-side and unrun.

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

## Session notes — 2026-11-19 (arena/eb90e04d-zone4): decision-support integrity and the thermometer calendar

**The integrity pass.** A line-by-line review of the suggestion register against the decision log found **eleven** rows whose statuses disagreed with their linked decisions: the five 2026-11-16/17 rows (S-32, S-34, S-35, S-39, S-44), PR #97's four (SG-32, SG-33, SG-35, SG-37) and PR #101's two (SG-44, SG-45 — pointing at recorded D-48 whose own recommendation defers them to a separate decision). All corrected; `scripts/verify.py` gained a status-agreement gate that fails the build if any suggestion says "Awaiting decision" while its linked decision is recorded. Recorded as **F-89**. A second pass found two publication texts lagging D-46 (the Information-gaps proof line still said "three verified air-fryer listings"; the design prompt's topic slot said "one guide per week" against the recorded 14-day cadence) — corrected and recorded as **F-90**. The thermometer search-demand gap was added to the Information-gaps table as **Q-59**.

**The duplicate flags.** Two renumbering sweeps left the sponsored-rel finding under two ids: F-74 (PR #98's sweep) and F-88 (PR #102's sweep re-appended it, and code comments cited their pre-renumber ids for date defects). Both F-74 and F-88 were rewritten as retired pointers under the register's duplicate-row precedent (F-72's Q-50 rewrite); stale internal comment citations were re-pointed or neutralized to the decisions they were about.

**New work.** **D-50** (recorded, standing brief) extends the question-shaped topic calendar to the two published thermometer listings as Wave 3 (T-09/T-10, proposal **S-55**), built only from the listings' own title claims (both listings re-read 2026-11-19, `data/verification-session-eb90e04d.json`) and the recorded special-feature rows — no popularity, demand or superiority claim (D-19, F-15, F-60 stated in the rows). **D-51** (recorded, standing brief) ships the Decision centre's owner-only-actions panel (proposal **S-56**), derived from the registers at build time. **D-52 stays open**: whether to front-load the 2026 gift window (two pieces inside 2026-11-27..2026-12-25, then back to 14 days in January) is recorded with weighed options and no recommendation; **SG-35** now points at it.

**Parallel-session reconciliation (five renumbering rounds).** While this branch worked, six PRs merged (#97–#102) and took Q-52..Q-58, SG-31..SG-45, F-74..F-88 and D-47/D-48/D-49. This session's rows were renumbered five times, to the next free ids each time (final: **S-55/S-56, Q-59, D-50/D-51/D-52, F-89/F-90**), before any published row collided; the board and logs of all sessions were kept in full (each repeated `COORDINATION.md` conflict was resolved by keeping every row; no row or log entry from either session was dropped). `data/redesign.json`'s reserved-range note, which had become false, carries a dated update: the reserved range for that register's proposals starts at D-53.

**Gates on the final tree.** `python3 scripts/build_site.py` (41 pages; a second build is byte-identical) → `python3 scripts/verify.py` PASS (including the new status-agreement gate and the Wave-3 claim-basis rule) → `python3 qa/audit_site.py --strict-warnings` PASS (0 warnings) → `python3 -m unittest discover -s tests` OK → `python3 -m engine.cli build` + `python3 tools/check_links.py` PASS → `python3 -m engine.cli audit` 0/7 ready (the designed refusal on unverified fields) → `python3 scripts/render_design_prompt.py` no-diff.

## Session notes — 2026-11-19 (arena/d696a32c-zone4): fresh re-verification and the safe storefront polish

**Re-verification.** All five listing pages plus the Operating Agreement (Updated October 15, 2025) and Program Policies (Updated April 14, 2026) were re-read from their official pages (`data/verification-session-d696a32c.json`). All five titles match the stored records except P2's second segment, which again shows the variant already recorded under F-66 (stored record kept). All five breadcrumbs match. Also-viewed churn is the already-flagged F-29 pattern (P1 slots 2/3 swapped; P3 slot 2 shows B09MR7QWKZ, the same sighting as arena/0272d56e-zone4); stored snapshots were not overwritten. The Section 5 disclosure sentence was re-read verbatim and matches the published sentence; Section 4's no-representation sentence and the Commission Income Statement session windows match the ledger definitions. No stored product value was changed; prices and ratings visible on the pages were not copied (F-02).

**What shipped (D-53, recorded under the standing no-manual-input brief, reversible by revert).** ItemList JSON-LD on the front page and the products page with name, tagged Special Link URL, brand and category only - no offers, price or ratings (S-57, F-92). A dated gift-season section on the front page for the 2026 window (27 November to 25 December, calendar dates only) linking the published holiday guide and the five shop links, quoting the P4 gift wording only as titled (S-58, F-91); it does not decide the open cadence question D-52. A short-answer block at the top of each published guide naming the formats compared, with no new figure (S-59). A five-that-matter-now list on the Decision centre derived from the open decisions at build time (S-60). New decision-support rows: S-57..S-60, Q-60..Q-63 (chooser distribution, first attributed click, gift-season queries, guide scroll rates - each with its discovery step), F-91/F-92, D-53. Register totals after this session: 79 suggestions, 63 questions, 53 decisions (40 recorded, 13 open), 92 flags.

**Irregularities for review (none block the merge).** No new unresolved values. Carried forward unchanged: F-57 (tag registration), F-58 (one-link test), F-59 (endpoint hosting), F-61 (Search Console), F-78 (P4 newer-model notice), F-02 (prices/ratings withheld), F-60 (thermometer blanks), D-52 (gift-window cadence, open).

## Release note — 2026-11-20 publication and measurement reliability

- **Buyer-facing improvement:** shorter homepage with compact native menus, products split into air fryers and thermometers, an edited existing-article shelf, clearly labelled editorial artwork and source-derived footprint diagrams. Research registers remain reachable from the footer and one navigation group. No new article, product fact or performance claim was generated.
- **Measurement hardening:** retained the parallel session’s tested trusted/middle-click transport, exact Origin and type guards. Added allowlisted published paths/intended ASINs/category slugs, per-category aggregate totals, no-referrer requests, bounded request bodies, error handling and 90-day aggregate pruning. Deployment still requires a permanent HTTPS service, persistent disk, request limits, logging/privacy review and scheduled maintenance. It is not turned on: GitHub Pages cannot run the Python service and no durable host was available.
- **Review queue:** SG-47 proposes production acceptance before optimization; SG-48 proposes anonymous buyer-task observations before another design change. Q-65 asks which denominator and abuse controls could make a later metric defensible. F-96 records the unclosed measurement boundary. No purchase, commission, revenue, trend or ranking is inferred from the interface.
- **Source scope:** five listing page titles and breadcrumbs were read again; nine of ten comparisons match, with the existing P2 title variation (F-44) preserved. Amazon Operating Agreement Section 5, the Program Policies opening/qualifying-purchase section, FTC disclosure guidance and GitHub’s static-hosting/data-collection documentation were read directly. Full product tables were not re-verified in this limited pass. Sources and exact observations: [dated verification record](data/verification-session-ba03ce6b.json).

**Priority order remains:** validate permanent collection and authorized reporting; verify the tracking ID and one Special Link per product inside Associates Central; verify Search Console; review real queries and task outcomes; only then choose the next topic or automation. Account-side gates are published openly, not silently bypassed.
