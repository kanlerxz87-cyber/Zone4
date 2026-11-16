# Executive Summary — Zone4 Amazon Affiliate Research Site

**Date:** 2026-11-16 (UTC) — design brief, traffic programme and decision-ordering added; links and cited official pages re-verified 2026-11-16; decision-support layer 2026-11-15; product facts observed 2026-11-14 (UTC) · **Live site:** https://kanlerxz87-cyber.github.io/Zone4/ · **Scope of truth:** `data/*.json` → built into `docs/` by `scripts/build_site.py`, checked by `scripts/verify.py`

---

## 1. Mandate

Build an Amazon affiliate research and marketing platform that identifies products, analyses pricing, reviews, competition and commission potential, generates SEO content, manages affiliate links, tracks clicks and conversions, and optimises campaigns — with full compliance with Amazon Associates policies and disclosure requirements, and no manual input from the owner. Marketing was requested for three supplied product links.

**Constraint that shapes everything below:** only values confirmed from official, trusted sources may be published. Anything that cannot be confirmed officially is left blank and published on **Flagged for Review** with its source link. Nothing is inferred, modelled or simulated.

## 2. What the repository delivers

1. **A live, evidence-first research site** on GitHub Pages — 25 generated pages: a marketing landing page (`docs/index.html`), executive summary, **requirements**, product catalogue, three category subpages (dual-basket air fryers / single-basket air fryers / air-fry toaster ovens), **marketing content**, an **articles hub**, **five individual article pages**, **automation & tracking**, analysis & findings, **suggestions**, **open questions**, **design brief**, **decision log**, field-by-field **verification log**, **policy compliance**, **clicks & conversions** (Analytics), **Flagged for review**, and **sources**. Every table row carries a link to its official source; withheld values are labelled, never inferred.
2. **Verified product identities** for all three submitted links (ASINs, listing titles, brands, manufacturers, model numbers, category paths, listed specifications, competitor ASINs) — `data/products.json`, `docs/verification.html`.
3. **A marketing content kit, published as real pages** — three product articles, one comparison page and one buying guide, each with a title tag, meta description, keyword targets, an outline, finished copy, a call to action and a fact table in which every row links to its official source (`data/marketing.json`). Each article is also published as its own page under `docs/articles/` with its own title tag and meta description, and is grouped by product format in the hub at `docs/articles/index.html`; `docs/marketing.html` carries the same five pieces on one page.
4. **An automation and tracking plan** — 13 pipeline stages, 10 tracking metrics (every value deliberately blank), five optimisation steps and seven Agent Terms requirements (`data/pipeline.json`, `docs/automation.html`).
5. **A compliance framework** quoting the official Operating Agreement, Program Policies, disclosure guidance, FTC guidance, Conditions of Use and the PA-API 5 → Creators API deprecation notice — `data/policies.json` (30 rules), `data/sources.json` (32 sources), `docs/policy-compliance.html`.
6. **A requirements register** — all 30 items from the brief, one row each, with what the site delivers, what blocks it, and the official source that governs the status (`data/requirements.json`, `docs/requirements.html`).
7. **A first-party click tracker** — `docs/analytics.html` + `docs/tracker.js`. Starts at zero, stores events in the visitor's own browser only, records only real clicks plus one explicitly labelled test event, exports as JSON or CSV. It generates no click of its own and sends nothing to any server.
8. **Automated checks** — `scripts/verify.py` (data validity, official-host-only links, per-page disclosure, per-row sources, no prices or ratings published, no Amazon Mark in titles or keywords, per-fact citation traceability, requirement-status evidence) runs in CI (`.github/workflows/site-checks.yml`) and confirms that the committed `docs/` matches a fresh build. An independent audit of the committed HTML, `qa/audit_site.py`, runs separately in CI (`.github/workflows/qa.yml`).
9. **Coordination across parallel sessions** via `COORDINATION.md` (task board, claims, conflict log, merge and deployment records).

## 2a. Decision support (added 2026-11-15)

The brief asks for a section where suggestions can be reviewed and a path chosen **before** anything is implemented, and for a
clear list of the questions and missing information that block a reasonable decision. Three pages now do that, and nothing in
them has been applied:

| Page | What it holds | Count |
|---|---|---|
| `docs/suggestions.html` | Every change worth making, with the problem, the proposal, the effort, the risk, the check that would prove it worked and the official rule that constrains it. A scannable summary table plus one card per proposal. | 36 suggestions, in three priority bands |
| `docs/questions.html` | What must be answered before any of them can be acted on: what is already known from an official source, what is missing, how the missing piece is discovered and who can supply it. | 44 questions: 18 already answered from an official source, 4 discoverable, 4 not discoverable from here, 18 owner decisions |
| `docs/decisions.html` | The choice itself: every open decision with its options, what each option commits the site to, its cost and whether it is reversible, plus a recommendation labelled as an argument rather than a decision. A log records decisions actually taken. | 39 open decisions, 0 recorded, shown in dependency order |

**The three that decide whether this project can earn at all**, in order of dependency:

1. **D-01 / Q-01 — the Associates tag.** The three supplied links resolve correctly but carry no `tag=` parameter, so no click can be
   attributed. Until this is answered the site's own disclosure sentence describes an earning relationship that the links cannot
   deliver (F-03, F-04).
2. **D-02 / Q-02 — API access for prices and ratings.** Associates rules permit prices and star ratings only through an Amazon-served
   link or an approved Amazon API (Participation Requirements 2(b), 6(t)). Amazon's stated prerequisite is 10 qualifying sales in 30
   days. Without it the site cannot show a price or a rating, which is what a buyer arrives for (F-02).
3. **D-08 / Q-03 — the per-ASIN commission category.** The public Table 1 lists Kitchen at 4.50%, but no public source maps an ASIN to
   a commission band. A category figure sitting next to a product it may not apply to invites a wrong calculation (F-01, F-36).

**Three more decide whether the site can honestly describe itself:** who reviews the copy before publishing (D-03 / Q-05), whether any
product is actually tested (D-06 / Q-06), and whether the automated collection and AI-assisted writing need a legal opinion before the
site takes traffic (Q-07). The remaining decisions are presentation and operations choices with named owners.

**What this layer deliberately does not do:** it does not action anything. No suggestion has been implemented, no question has been
closed by inference, and the decision log states explicitly that no owner decision has been recorded. The site's content and its
withheld values are exactly as they were; the build gate now fails if a suggestion points at a decision that does not exist, if a
recorded decision is missing from the log, or if two pages share a meta description.

**Design & marketing polish (added 2026-11-15 by `arena/d8564cd0-zone4`).** In the same decision-support direction, that session also shipped the no-decision-needed first steps: a warm-identity stylesheet refresh (all prior class names preserved, including the decision-support classes), a decision-first landing hero with the articles presented in decision order, article copy rewritten with subheadings and decision-led hooks while every fact and fact_id stayed exactly as verified, Article/WebSite JSON-LD that states only what each page visibly shows, a generated `docs/sitemap.xml`, and a paste-ready design brief at the end of `docs/suggestions.html`. Its same-day verification pass is in `data/verification-session-d8564cd0.json` (flag F-44). The two sessions' registers were reconciled rather than duplicated: that session dropped its own parallel question/suggestion drafts and kept this register canonical — the superseded commits remain in the branch reflog and are described in `COORDINATION.md`.

## 2b. Independent re-verification and the marketing layer (arena/f87cc71f-zone4, 2026-11-15)

**Independent re-verification (second session, later date).** The three short links re-resolved to the same ASINs (B0CDY277D3, B09B7SB46R, B08DKYBTPH) with no `tag=` parameter in any resolved URL (F-03 stands). Listing-title tags matched the stored records verbatim for P1 and P3; P2's title-tag prefix matched while its subtitle differs from the stored listing title (Amazon's meta title and on-page title can differ; recorded, not smoothed). Category breadcrumbs matched for all three. The also-viewed carousels showed the first two stored entries in order on each page, while the third slots had rotated to `B0D1BGLW25` (P2) and `B09MR7QWKZ` (P3) — direct, later-date evidence for the carousel instability already flagged in F-29. Commission Table 1 was re-read and matches the published category bands (Kitchen 4.50%, Home 3.00%), and Operating Agreement Section 5's disclosure sentence was re-read and matches the site's disclosure verbatim. The specification tables could **not** be re-read again (advertising modules / bot checkpoint), so F-38 stands with a second failing attempt recorded. Full record: `data/verification-session-f87cc71f.json`.

**Marketing and presentation layer.** This session refreshed the five articles' headline fields and previewed a warm theme layer; the parallel session `arena/d8564cd0-zone4` then shipped its own fact-traceable copy refresh, the warm-identity stylesheet, JSON-LD and a sitemap. Where the two overlapped, its merged versions were kept in the reconciliation — its copy is as source-traceable as this session's (the "200-450°F" line in the P1 meta description is fact M-P1-F8) and it landed on `main` first. Suggestion **S-12** (the deeper voice decision) and **S-15** (visual direction and brand, decision **D-18**) remain open, and two redesign-brief drafts now exist: the paste-ready one at the end of the Suggestions page (`arena/d8564cd0-zone4`) and the extended repo draft `DESIGN_PROMPT.md` (suggestion **S-14**, decision **D-20**). The topic calendar proposal — eight catchy, format-first working titles built from verified fields — is suggestion **S-13** (decision **D-17**), and the written evidence rule for "trending" claims is **S-16** (decision **D-19**).

## 3. Product verification results (official Amazon sources, observed 2026-11-14)

| # | Submitted link | Resolved ASIN | Official listing title | Category (breadcrumb) | Brand | Manufacturer | Price / rating / reviews | Commission |
|---|---|---|---|---|---|---|---|---|
| P1 | https://link.amazon/B04G1MEwY | `B0CDY277D3` | CHEFMAN 6 Quart Dual Basket Air Fryer Oven with Easy View Windows, Sync Finish, Hi-Fry, Auto Shutoff, 2 Independent 3Qt Nonstick Dishwasher Safe Frying Baskets, Digital Double Air Fryer - Black | Home & Kitchen › Kitchen & Dining › Small Appliances › Fryers › Air Fryers | Chefman | Chefman | **Withheld** (F-02) | **Blank** — ASIN category unconfirmed (F-01; [official category table](https://affiliate-program.amazon.com/help/node/topic/GRXPHT8U84RAYDXZ)) |
| P2 | https://link.amazon/B02NbDxp3 | `B09B7SB46R` | Emeril Lagasse 26QT French Door Multi-Function Air Fryer Toaster Oven \| 26QT air fryer oven with French doors, 24 cooking functions, dual-speed fan and rotisserie for easy family meals. | Home & Kitchen › Kitchen & Dining › Small Appliances › Fryers › Air Fryers | Emeril (F-05, resolved) | Emeril Lagasse | **Withheld** (F-02) | **Blank** — ASIN category unconfirmed (F-01; [official category table](https://affiliate-program.amazon.com/help/node/topic/GRXPHT8U84RAYDXZ)) |
| P3 | https://link.amazon/B00hJ57DV | `B08DKYBTPH` | Chefman Air Fryer 8 Qt \| TurboFry® 4-in-1 with 450°F Hi-Fry Option for Crispier Results \| Bake, Dehydrate, Frozen \| XL Nonstick Dishwasher-Safe Basket \| Stainless Steel | Home & Kitchen › Kitchen & Dining › Small Appliances › Fryers › Air Fryers | Chefman | Chefman | **Withheld** (F-02) | **Blank** — ASIN category unconfirmed (F-01; [official category table](https://affiliate-program.amazon.com/help/node/topic/GRXPHT8U84RAYDXZ)) |

The official [Standard Commission Income Statement, Table 1](https://affiliate-program.amazon.com/help/node/topic/GRXPHT8U84RAYDXZ) lists the Kitchen category at **4.50%**. This is a category-level reference only: no official source reviewed confirms Amazon’s commission category assignment for any of these ASINs. The product-level cells above therefore remain blank rather than inferring that the storefront breadcrumb determines the Associates commission category.

**Key finding (confirmed independently by several sessions):** the 9-character strings in the submitted links (`B04G1MEwY`, `B02NbDxp3`, `B00hJ57DV`) are **short-link slugs, not ASINs** — using them as ASINs returns Amazon's official "Page Not Found" page (e.g. https://www.amazon.com/dp/B04G1MEwY). Amazon's own guide defines ASINs as **10-character alphanumeric** codes (https://sell.amazon.com/blog/what-is-an-asin). All three `link.amazon` URLs resolved to live Amazon.com product pages on 2026-11-14, and none of the resolved URLs carried an Associates `tag=` parameter.

**P2 brand resolved (F-05).** An earlier draft misidentified the separate "Innovation IQ" creator/review block as a product byline. Re-reading the official page on 2026-11-14 showed the Item details table gives **Brand Name "Emeril"**, **Manufacturer "Emeril Lagasse"**, Model Name "Extra Large 26 QT French Door Air Fryer Oven", Model Number `4-00675-02X-VN`, UPC `752356835682`; the page has a store link reading "Visit the Emeril Store" and the page carries a "Top Brand: Emeril" module. "Innovation IQ" appears as the creator associated with a customer-review video and links to Amazon Influencer information — it is not the brand or a product byline.

**Withholding rationale (F-02):** the Participation Requirements permit displaying prices and availability only via Amazon-served links or Creators API / PA API data (§2(b)), and customer reviews or star ratings only via API content (§6(t)). Amazon prices and ratings **were observed** during verification but are deliberately not published. The ambiguous buy-box amounts observed for P1/P3 are recorded as session observations, not published.

## 4. Compliance status

- **Required disclosure** (on every page of the site): *"As an Amazon Associate I earn from qualifying purchases."* — Operating Agreement §5; link-level disclosure must additionally be clear ("(paid link)", "#ad", "#CommissionsEarned") and conspicuous near links and reviews (https://affiliate-program.amazon.com/help/node/topic/GPXFHVYZMTGPUMPE; FTC Disclosures 101).
- **Special Links** must "properly use the special 'tagged' link formats" (Agreement §1) and carry the Associates tag as a URL parameter (§2(b)); purchases via improperly formatted links are **disqualified** (Commission Income Statement §2). No Associates tag was supplied, so the supplied links are published as plain product links and no earnings are claimed (F-03).
- Participation Requirements as numbered on the current Program Policies page (updated 2026-04-14): §1(g) trademarks in domains and tags; §2(b) prices, availability and the Associates tag; §5 no machine-learning use of Program Content without prior express written approval; §6(e)–(f) Amazon marks as search keywords; §6(g) incentives; §6(p) Special Links in customer content; §6(s) artificial clicks; §6(t) reviews and star ratings; §6(w) link shortening; §6(y) price tracking and alerting; §6(z) promoting non-Amazon-Site products.
- **IP License** §§1–4: no data-mining or extraction tools (§1), no repurposing or model training on API content without express prior written approval (§2(e)), price timestamps and disclaimers if API prices are ever shown (§2(i), §2(k)), and the **Agent Terms** (§4) — any automated agent must identify itself as `Agent/[agent name]`, must not conceal that it is an agent, and must not solve CAPTCHAs or work around access limits.
- **PA-API 5 is officially deprecated** in favour of the **Creators API** (https://affiliate-program.amazon.com/creatorsapi/docs/en-us/paapiv5-deprecation); license terms not yet reviewed (F-16).
- The **Standard Commission Income Statement is published at a public URL that needs no sign-in** (https://affiliate-program.amazon.com/help/node/topic/GRXPHT8U84RAYDXZ). Its Table 1 lists "Physical Books, Kitchen, Automotive" at **4.50%**. That is a category-level reference only; no official source reviewed confirms which band Amazon assigns to these individual ASINs, so each product-level rate is left blank (F-01).
- Amazon Conditions of Use (updated 2026-08-14) additionally constrain scraping/data mining and the use of Amazon content to improve models (F-11, F-12).
- The complete flag register (**F-01 … F-46**, 46 items) is published at `docs/flagged.html` with sources, grouped into the items that need a decision, those corrected in the session that found them and the resolved items kept as the audit record. **F-44** (added 2026-11-15 by `arena/d8564cd0-zone4`): the P2 listing title's second segment differed on a 2026-11-15 read, and two carousels changed membership again — both recorded verbatim in `data/verification-session-d8564cd0.json` with the stored records kept; first numbered F-39 in that session's superseded commits and renumbered on rebase because `arena/00ba6c2e-zone4` had taken F-39…F-43 concurrently. A second session, `arena/d2a62d6b-zone4`, read the same drift independently on the same day and recorded it as its own F-44 before the merge; the duplicate was dropped rather than published twice, and the two reads agree. **F-45** (same session): a second dated attempt to re-read the product-details tables returned advertising modules plus one automated-traffic interstitial, which was **not** circumvented, because the Agent Terms (IP License §4) prohibit working around access limits (F-38, F-11). **F-46**: the editorial redesign and navigation split that session shipped are a proposed path until the owner signs them off, so they are recorded rather than assumed (S-17, S-21, D-21).

## 5. Flagged for review — headline items (complete register: `docs/flagged.html`)

- **F-01** Official Table 1 lists a 4.50% Kitchen category rate; individual ASIN category assignments are unconfirmed, so product-level cells are blank. **F-02** Prices and star ratings withheld by policy. **F-03** No Associates tag in the resolved links. **F-04** Short-link codes are not the resolved ASINs.
- **F-05** P2 brand/manufacturer confirmed. **F-06/F-07** listed capacity/color inconsistencies. **F-08** P3 is a size-variant family. **F-09** Snapshot used a US delivery-location display; no user-location claim is made. **F-10/F-29** competitor carousels and Sponsored labels vary between reads.
- **F-11/F-12/F-21** one-off verification and automated research/content are constrained by Amazon's Conditions of Use and Agent Terms. **F-13/F-14** prior deployment/prototype records are historical and superseded. **F-15** trend/popularity/conversion signals unverified. **F-16** Creators API license terms not reviewed. **F-17** policy-number corrections are recorded. **F-18** product-page field re-read matched; resolved. **F-19** local click log exists; attributed reporting is not connected. **F-20** competitor-label correction is retained as audit history.
- **F-22** price tracking/alerting restrictions. **F-23** Amazon Marks cannot be search keywords. **F-24/F-25** API reuse/model-training limits and the conservative Amazon-content notice. **F-26** P2's 24 vs. 25 cooking-function count discrepancy. **F-27** offline/email use restrictions. **F-28** manufacturers confirmed for all three products; resolved. **F-29** the "also viewed" carousel is an advertising slot and changes between loads — re-read on 2026-11-14 it reproduced exactly, and the one label that had been blank (`B0CNSB81V6`, "Nutrichef Double Basket Air Fryer 8.8 QT") was then read verbatim and filled, so no label is blank. **F-30** Conditions of Use help URL changed node ID — **resolved** 2026-11-14: the cited `nodeId=508088` still resolves through a redirect to the canonical `nodeId=GLSBYFE9MGKKQXXM`, and the wording was re-read on that fetch. **F-31** product specifications lack an approved content source. **F-32** short-link host confirmation is empirical; codes remain tokens. **F-33** API quota/price-timestamp rules not adopted. **F-34** duplicate Pages/CI configuration. **F-35** Creators API documentation differs on marketplace access. **F-36** the per-product commission rate was published without an official source for the per-ASIN category step; product cells are now blank (resolved). **F-37** carousel-instability notes cited F-27 where they meant F-29 (corrected). **F-38** the specification-table rows rest on the 2026-11-14 reads recorded by earlier sessions: the final integration session re-read identities, titles, breadcrumbs and competitor sets for all three products, but the lower part of each page returned advertising modules instead of the details table, so those rows were not re-confirmed in that session and are flagged rather than glossed over. **F-36** the site had published a per-product commission rate that no official source confirms for these ASINs — found independently by two sessions on 2026-11-14; the product-level cells are now blank and the category-level rate is stated with its source. **F-37** the carousel-instability notes cited F-27 where they meant F-29; corrected.

**Additional finding (parallel session):** no official Amazon documentation for the `link.amazon` domain was located; its resolution to Amazon.com was verified empirically on 2026-11-14 by several independent sessions, and a third-party description (https://linktw.in/link-amazon-vs-linktwin, **non-official**) says it routes via `amzlinks.in` (Button). Treat `link.amazon` links as leads until Amazon documents the domain.

## 5a. Requirement register

Every item in the brief, one row each, is published at `docs/requirements.html` with its delivery status and the official source that governs it. Summary of that register (full detail on the page):

| Status | Count | What it covers | Source |
|---|---|---|---|
| Delivered | 15 | Site, verification discipline, disclosure, compliance, scalability, data-driven decisions, the marketing content kit, publishing on Pages | [requirements register](https://github.com/kanlerxz87-cyber/Zone4/blob/main/data/requirements.json) |
| Delivered (partial) | 7 | Competition analysis, niche research, marketing content, link management, click tracking, category-rate reference (ASIN mapping pending), delivery for the three products | [requirements register](https://github.com/kanlerxz87-cyber/Zone4/blob/main/data/requirements.json) |
| Not built — blocked (policy) | 5 | The AI-powered platform, automated research, price analysis, review analysis, full content automation | [requirements register](https://github.com/kanlerxz87-cyber/Zone4/blob/main/data/requirements.json) |
| Not built — needs access | 1 | Campaign optimisation | [requirements register](https://github.com/kanlerxz87-cyber/Zone4/blob/main/data/requirements.json) |
| Unverifiable (blank + flagged) | 2 | Trend analysis, conversion analysis | [requirements register](https://github.com/kanlerxz87-cyber/Zone4/blob/main/data/requirements.json) |

Nothing is simulated in place of a blocked or unverified requirement.

## 5b. Re-verification performed on 2026-11-15 by `arena/d2a62d6b-zone4`

| Item checked | Result | Source |
|---|---|---|
| P1 title, identity, breadcrumb | Matched the stored record; no change made | [P1 official page](https://www.amazon.com/dp/B0CDY277D3) |
| P2 title | **Drifted** again on this session's read: the official page begins "Emeril Lagasse 26QT French Door Multi-Function Air Fryer Toaster Oven \| Countertop Convection Cooker, 24 One-Touch Preset Options, Extra Large Interior, Six Cooking Accessories Included", not the stored 2026-11-14 string. Identity unchanged; the stored record was **not** overwritten. Recorded independently as F-44 by `arena/d8564cd0-zone4` | [P2 official page](https://www.amazon.com/dp/B09B7SB46R) |
| P3 title, identity, breadcrumb | Matched the stored record; no change made | [P3 official page](https://www.amazon.com/dp/B08DKYBTPH) |
| "Also viewed" carousel, all three | Drifted again (P2 slot 3, P3 slot 3), as F-29 records it does between loads | Same three pages |
| Product-details (specification) tables | Not renderable on a second dated attempt: advertising modules returned instead, plus one automated-traffic interstitial, which was not circumvented (F-45) | Same three pages |
| Operating Agreement §1, §4, §5 | Re-read: tagged link formats; no representation about traffic or earnings; the required disclosure sentence | [Operating Agreement](https://affiliate-program.amazon.com/help/operating/agreement) |
| Programme Policies 6(f), 6(y), 6(z), 2(b), 6(t) | Re-read: paid-search restriction, price-tracking prohibition, single-retailer rule, price and rating display limits | [Programme Policies](https://affiliate-program.amazon.com/help/operating/policies) |
| Public Standard Commission Income Statement | Kitchen category **4.50%**; still no public mapping from ASIN to band, so product cells stay blank (F-01) | [Table 1](https://affiliate-program.amazon.com/help/node/topic/GRXPHT8U84RAYDXZ) |
| FTC Disclosures 101 | Re-read: disclosure must be hard to miss and placed with the endorsement; no claimed experience with an untried product | [FTC](https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers) |
| Google: AI-generated content | Read in full; quoted verbatim into the questions register (Q-23…Q-37) | [Google Search Central](https://developers.google.com/search/blog/2023/02/google-search-and-ai-content) |
| Google: creating helpful content | Read; the standard the editorial suggestions are judged against | [Google Search Central](https://developers.google.com/search/docs/fundamentals/creating-helpful-content) |

## 5c. Design brief, traffic programme and 2026-11-16 re-verification (`arena/89900251-zone4`)

The brief asks for **suggestions that feed a prompt to design the site as a polished marketing affiliate website**, for
**catchy, trendy articles and topics that earn organic traffic**, and for the site to stop reading like machine output. A new
`docs/design.html` page, generated from `data/design.json`, answers all three — and nothing on it has been applied.

| What it holds | Detail |
|---|---|
| Three visual directions | The executable detail for the three options already in D-18: named display and body type stacks with fallbacks, five colour tokens with hex values, a spacing scale, a grid, and a rule for the hero, the cards, the tables, the disclosure component and the imagery. Two are free; the bold deal-finder look is narrowed to an evidence-only form because the price, rating and price-tracking rules (F-02, F-15, F-22) bar the tactics that look normally depends on. |
| Ten anti-patterns | Each names a writing habit on the current site, the evidence for it, why it reads as generated, the replacement and the check that proves the fix. |
| Ten headline options | Two finished alternatives for each of the five published articles, so the choice is four fields per article and one rebuild. |
| Eight topics | Each with the question it answers, the intent, the verified fact rows it is built from, the pages it must link to and the evidence note that limits it. |
| Paste-ready prompt | Assembled from the same data, so the page, `DESIGN_PROMPT.md` and the register cannot disagree. Seven bracketed slots, each naming the decision that fills it. |
| Shortest credible path | Five of the 39 open decisions, ordered by what each unblocks. |

**Re-verification, 2026-11-16.** All three supplied short links were re-resolved from their official pages:

| Item checked | Result | Source |
|---|---|---|
| `B04G1MEwY`, `B02NbDxp3`, `B00hJ57DV` | Still resolve to `B0CDY277D3`, `B09B7SB46R`, `B08DKYBTPH`. No `tag=` parameter in any resolved URL (F-03 stands) | [P1](https://www.amazon.com/dp/B0CDY277D3) · [P2](https://www.amazon.com/dp/B09B7SB46R) · [P3](https://www.amazon.com/dp/B08DKYBTPH) |
| P1 title, breadcrumb, also-viewed | Matched the stored record on every field read; no change made | [P1 official page](https://www.amazon.com/dp/B0CDY277D3) |
| P3 title, breadcrumb | Matched; the third also-viewed slot rotated to `B09MR7QWKZ` — the same substitution recorded on 2026-11-15 (F-29) | [P3 official page](https://www.amazon.com/dp/B08DKYBTPH) |
| P2 title | The **fourth consecutive later read** returned the same alternative string. Four reads on 2026-11-15 and 2026-11-16 now agree with each other and differ from the stored 2026-11-14 record, so which string the site publishes is an owner decision rather than a note: **F-44**. Stored record not overwritten | [P2 official page](https://www.amazon.com/dp/B09B7SB46R) |
| P2 function count | The live title again states 24, a third dated sighting of the "24" side of the discrepancy (F-26 stays open) | [P2 official page](https://www.amazon.com/dp/B09B7SB46R) |
| Operating Agreement §1, §4, §5 | Re-read verbatim: tagged link formats; no representation about traffic or commission income; the required disclosure sentence | [Operating Agreement](https://affiliate-program.amazon.com/help/operating/agreement) |
| Disclosure help topic | Re-read: a link-level disclosure must be clear and conspicuous and placed near the link | [Associates help](https://affiliate-program.amazon.com/help/node/topic/GPXFHVYZMTGPUMPE) |
| Commission Table 1 | Kitchen **4.50%** confirmed; still no ASIN-to-band mapping, so product cells stay blank (F-01) | [Table 1](https://affiliate-program.amazon.com/help/node/topic/GRXPHT8U84RAYDXZ) |
| FTC Disclosures 101 | Re-read: hard to miss, placed with the endorsement, not behind a click, not mixed with links; no claimed experience with an untried product | [FTC](https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers) |
| Google AI-content guidance | Re-read; the byline and automation-disclosure sentences quoted verbatim into Q-39 | [Google Search Central](https://developers.google.com/search/blog/2023/02/google-search-and-ai-content) |
| Google helpful-content guidance | Re-read; the "simply because they seem trending" warning sign is the constraint on the topic programme (F-51, Q-38) | [Google Search Central](https://developers.google.com/search/docs/fundamentals/creating-helpful-content) |

Full row-by-row record: `data/verification-session-89900251.json`.

**Irregularities found by reading the published records line by line, and what was done about them:**

| Flag | What it is | Disposition |
|---|---|---|
| **F-51** | The brief asks for trendy topics and for traffic that converts. Google's guidance lists trend-chasing as a warning sign of search-engine-first content, and the Operating Agreement (§4) makes no representation about traffic or commission income. | Recorded as an open tension with the rule that resolves it. No traffic, revenue or search-volume figure is published anywhere on the site. Decided by D-17, D-19 and D-37. |
| **F-44** | P2's published listing title is contradicted by four consecutive later official reads on 2026-11-15 and 2026-11-16. | Stored record left in place; the choice of which string to publish is now explicitly the owner's. |
| **F-52** | Three of five headlines describe the site's own checking process; two differ only by "two baskets" / "one basket"; four of five title tags contain "Verified". | Two finished replacement options per article, waiting on D-37. |
| **F-53** | The second paragraph of each product article prints the ASIN and a five-level category path as prose the sourced fact table already carries. | Replacement written (ASIN-02); waiting on D-36. |
| **F-54** | Ten cross-references pointed at flag numbers that were renumbered when three sessions' registers merged — three sentences about the P2 title cited F-39 where it is now F-44, one cited F-40 for the unreadable specification tables where it is F-38, and three cited F-41 for the redesign sign-off where it is F-46. | All ten corrected. The class of defect is recorded because `scripts/verify.py` checks that a reference **exists**, not that it points at the right finding. |

**The honest tension in the brief.** "Catchy trendy articles" and "generate organic traffic so real people click and buy"
are requests for outcomes, and no official source supports a number for either. The topic programme is therefore built
from the questions a buyer of these three formats actually asks and answered from fields already verified; the headlines
lead with a number or a tension the page can prove; and the one place the site really can out-rank a big review site —
the listing that contradicts itself on its own page — is where the strongest headline points. That is recorded as F-51
rather than hidden, because the alternative was to publish a forecast.

## 6. Recommended next steps (owner, when ready)

Steps 1–7 below are the same actions, restated as twelve numbered decisions with options, costs and reversibility on `docs/decisions.html`. Work them from D-01 downward rather than in the order listed here.


1. Join or confirm the Amazon Associates Program for the final site and provide the Associates tag; generate Special Links for `B0CDY277D3`, `B09B7SB46R`, `B08DKYBTPH`.
2. Keep the site-wide and per-link disclosures (already templated) and re-verify the current policy pages at launch.
3. Commission product content only from verified data; target the Creators API (not PA-API 5) once eligible, and review its license terms first (F-16).
4. Decide whether the research agent may be automated at all; if so, implement the Agent Terms user-agent string and transparency rules first (F-21, F-11).
5. Enable the first-party tracker on real traffic, add a cookie or consent notice, and reconcile local clicks against Associates Central reporting (F-19, F-03).
6. Ask the seller for P2's correct cooking-function count (F-26). The Conditions of Use citation has been re-confirmed (F-30, resolved) — re-check it at the next policy review.
7. Re-verify volatile values and confirm the intended marketplace/storefront (F-09).
8. Decide on the editorial redesign: D-21 and Q-37 exist because a redesign and a navigation split were shipped on the owner's
   behalf before they were approved, so they need a decision (accept, amend or revert) rather than being treated as settled
   (F-46, S-17, S-21).
9. Decide where product photography comes from (D-22, S-18). No generated or copied photograph of a specific product may be used,
   because that is a claim about that product.
10. Work the fifteen suggestions ported from `arena/d2a62d6b-zone4` (S-17…S-31, decisions D-21…D-34) in priority order: the
    "which one is for you" chooser, the mobile pass and the "what we could not verify" block change what a reader gets from the
    site; the paid-search, deals-section and single-retailer rows are guardrails that keep it inside the Programme Policies.
11. Work the five-step shortest credible path on `docs/design.html`, in this order: **D-01** (tag the links — nothing can earn
    until this is true), **D-03** (say who writes the site), **D-12** (let the copy take positions inside the fact rule), **D-36**
    (run the anti-slop pass, or at least the F-52 and F-53 fixes), **D-35** (pick the visual direction). The order is by what each
    step unblocks, so doing the expensive one third means doing it once.
12. Choose the headline register (D-37) and the visual direction (D-35) from the ten and three finished options on the Design brief
    page; both are four-field or one-file changes, not writing jobs. Decide the P2 title question (F-44) the same day.
13. If the design tokens should be previewable before the overhaul, take D-39 first — it is half a day and turns a choice between
    three descriptions into a choice between three things you can see.

## 7. Official sources used (fetched live 2026-11-14 unless noted)

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
