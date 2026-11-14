# Executive Summary — Zone4 Amazon Affiliate Research Site

**Date:** 2026-11-14 (UTC) · **Live site:** https://kanlerxz87-cyber.github.io/Zone4/ · **Scope of truth:** `data/*.json` → built into `docs/` by `scripts/build_site.py`, checked by `scripts/verify.py`

---

## 1. Mandate

Build an Amazon affiliate research and marketing platform that identifies products, analyses pricing, reviews, competition and commission potential, generates SEO content, manages affiliate links, tracks clicks and conversions, and optimises campaigns — with full compliance with Amazon Associates policies and disclosure requirements, and no manual input from the owner. Marketing was requested for three supplied product links.

**Constraint that shapes everything below:** only values confirmed from official, trusted sources may be published. Anything that cannot be confirmed officially is left blank and published on **Flagged for Review** with its source link. Nothing is inferred, modelled or simulated.

## 2. What the repository delivers

1. **A live, evidence-first research site** on GitHub Pages — 21 generated pages: a marketing landing page (`docs/index.html`), executive summary, **requirements**, product catalogue, three category subpages (dual-basket air fryers / single-basket air fryers / air-fry toaster ovens), **marketing content**, an **articles hub**, **five individual article pages**, **automation & tracking**, analysis & findings, field-by-field **verification log**, **policy compliance**, **clicks & conversions** (Analytics), **Flagged for review**, and **sources**. Every table row carries a link to its official source; withheld values are labelled, never inferred.
2. **Verified product identities** for all three submitted links (ASINs, listing titles, brands, manufacturers, model numbers, category paths, listed specifications, competitor ASINs) — `data/products.json`, `docs/verification.html`.
3. **A marketing content kit, published as real pages** — three product articles, one comparison page and one buying guide, each with a title tag, meta description, keyword targets, an outline, finished copy, a call to action and a fact table in which every row links to its official source (`data/marketing.json`). Each article is also published as its own page under `docs/articles/` with its own title tag and meta description, and is grouped by product format in the hub at `docs/articles/index.html`; `docs/marketing.html` carries the same five pieces on one page.
4. **An automation and tracking plan** — 13 pipeline stages, 10 tracking metrics (every value deliberately blank), five optimisation steps and seven Agent Terms requirements (`data/pipeline.json`, `docs/automation.html`).
5. **A compliance framework** quoting the official Operating Agreement, Program Policies, disclosure guidance, FTC guidance, Conditions of Use and the PA-API 5 → Creators API deprecation notice — `data/policies.json` (30 rules), `data/sources.json` (20 sources), `docs/policy-compliance.html`.
6. **A requirements register** — all 30 items from the brief, one row each, with what the site delivers, what blocks it, and the official source that governs the status (`data/requirements.json`, `docs/requirements.html`).
7. **A first-party click tracker** — `docs/analytics.html` + `docs/tracker.js`. Starts at zero, stores events in the visitor's own browser only, records only real clicks plus one explicitly labelled test event, exports as JSON or CSV. It generates no click of its own and sends nothing to any server.
8. **Automated checks** — `scripts/verify.py` (data validity, official-host-only links, per-page disclosure, per-row sources, no prices or ratings published, no Amazon Mark in titles or keywords, per-fact citation traceability, requirement-status evidence) runs in CI (`.github/workflows/site-checks.yml`) and confirms that the committed `docs/` matches a fresh build. An independent audit of the committed HTML, `qa/audit_site.py`, runs separately in CI (`.github/workflows/qa.yml`).
9. **Coordination across parallel sessions** via `COORDINATION.md` (task board, claims, conflict log, merge and deployment records).

## 3. Product verification results (official Amazon sources, observed 2026-11-14)

| # | Submitted link | Resolved ASIN | Official listing title | Category (breadcrumb) | Brand | Manufacturer | Price / rating / reviews | Commission |
|---|---|---|---|---|---|---|---|---|
| P1 | https://link.amazon/B04G1MEwY | `B0CDY277D3` | CHEFMAN 6 Quart Dual Basket Air Fryer Oven with Easy View Windows, Sync Finish, Hi-Fry, Auto Shutoff, 2 Independent 3Qt Nonstick Dishwasher Safe Frying Baskets, Digital Double Air Fryer - Black | Home & Kitchen › Kitchen & Dining › Small Appliances › Fryers › Air Fryers | Chefman | Chefman | **Withheld** (F-02) | **Blank** — ASIN commission category unconfirmed (F-01) |
| P2 | https://link.amazon/B02NbDxp3 | `B09B7SB46R` | Emeril Lagasse 26QT French Door Multi-Function Air Fryer Toaster Oven \| 26QT air fryer oven with French doors, 24 cooking functions, dual-speed fan and rotisserie for easy family meals. | Home & Kitchen › Kitchen & Dining › Small Appliances › Fryers › Air Fryers | Emeril (F-05, resolved) | Emeril Lagasse | **Withheld** (F-02) | **Blank** — ASIN commission category unconfirmed (F-01) |
| P3 | https://link.amazon/B00hJ57DV | `B08DKYBTPH` | Chefman Air Fryer 8 Qt \| TurboFry® 4-in-1 with 450°F Hi-Fry Option for Crispier Results \| Bake, Dehydrate, Frozen \| XL Nonstick Dishwasher-Safe Basket \| Stainless Steel | Home & Kitchen › Kitchen & Dining › Small Appliances › Fryers › Air Fryers | Chefman | Chefman | **Withheld** (F-02) | **Blank** — ASIN commission category unconfirmed (F-01) |

The official [Standard Commission Income Statement, Table 1](https://affiliate-program.amazon.com/help/node/topic/GRXPHT8U84RAYDXZ) lists the Kitchen category at **4.50%**. This is a category-level reference only: no official source reviewed confirms Amazon’s commission category assignment for any of these ASINs. The product-level cells above therefore remain blank rather than inferring that the storefront breadcrumb determines the Associates commission category.

**Key finding (confirmed independently by several sessions):** the 9-character strings in the submitted links (`B04G1MEwY`, `B02NbDxp3`, `B00hJ57DV`) are **short-link slugs, not ASINs** — using them as ASINs returns Amazon's official "Page Not Found" page (e.g. https://www.amazon.com/dp/B04G1MEwY). Amazon's own guide defines ASINs as **10-character alphanumeric** codes (https://sell.amazon.com/blog/what-is-an-asin). All three `link.amazon` URLs resolved to live Amazon.com product pages on 2026-11-14, and none of the resolved URLs carried an Associates `tag=` parameter.

**P2 brand resolved (F-05).** An earlier reading had recorded the P2 byline as "Innovation IQ". Re-reading the official page on 2026-11-14 showed the Item details table gives **Brand Name "Emeril"**, **Manufacturer "Emeril Lagasse"**, Model Name "Extra Large 26 QT French Door Air Fryer Oven", Model Number `4-00675-02X-VN`, UPC `752356835682`; the brand byline link reads "Visit the Emeril Store" and the page carries a "Top Brand: Emeril" module. "Innovation IQ" appears as the creator associated with a customer-review video and links to Amazon Influencer information — it is not the brand or a product byline.

**Withholding rationale (F-02):** the Participation Requirements permit displaying prices and availability only via Amazon-served links or Creators API / PA API data (§2(b)), and customer reviews or star ratings only via API content (§6(t)). Amazon prices and ratings **were observed** during verification but are deliberately not published. The ambiguous buy-box amounts observed for P1/P3 are recorded as session observations, not published.

## 4. Compliance status

- **Required disclosure** (on every page of the site): *"As an Amazon Associate I earn from qualifying purchases."* — Operating Agreement §5; link-level disclosure must additionally be clear ("(paid link)", "#ad", "#CommissionsEarned") and conspicuous near links and reviews (https://affiliate-program.amazon.com/help/node/topic/GPXFHVYZMTGPUMPE; FTC Disclosures 101).
- **Special Links** must "properly use the special 'tagged' link formats" (Agreement §1) and carry the Associates tag as a URL parameter (§2(b)); purchases via improperly formatted links are **disqualified** (Commission Income Statement §2). No Associates tag was supplied, so the supplied links are published as plain product links and no earnings are claimed (F-03).
- Participation Requirements as numbered on the current Program Policies page (updated 2026-04-14): §1(g) trademarks in domains and tags; §2(b) prices, availability and the Associates tag; §5 no machine-learning use of Program Content without prior express written approval; §6(e)–(f) Amazon marks as search keywords; §6(g) incentives; §6(p) Special Links in customer content; §6(s) artificial clicks; §6(t) reviews and star ratings; §6(w) link shortening; §6(y) price tracking and alerting; §6(z) promoting non-Amazon-Site products.
- **IP License** §§1–4: no data-mining or extraction tools (§1), no repurposing or model training on API content without express prior written approval (§2(e)), price timestamps and disclaimers if API prices are ever shown (§2(i), §2(k)), and the **Agent Terms** (§4) — any automated agent must identify itself as `Agent/[agent name]`, must not conceal that it is an agent, and must not solve CAPTCHAs or work around access limits.
- **PA-API 5 is officially deprecated** in favour of the **Creators API** (https://affiliate-program.amazon.com/creatorsapi/docs/en-us/paapiv5-deprecation); license terms not yet reviewed (F-16).
- The **Standard Commission Income Statement is published at a public URL that needs no sign-in** (https://affiliate-program.amazon.com/help/node/topic/GRXPHT8U84RAYDXZ). Its Table 1 lists "Physical Books, Kitchen, Automotive" at **4.50%**. That is a category-level reference only; no official source reviewed confirms which band Amazon assigns to these individual ASINs, so each product-level rate is left blank (F-01).
- Amazon Conditions of Use (updated 2026-08-14) additionally constrain scraping/data mining and the use of Amazon content to improve models (F-11, F-12).
- The complete flag register (**F-01 … F-38**, 38 items, all used) is published at `docs/flagged.html` with sources.

## 5. Flagged for review — headline items (complete register: `docs/flagged.html`)

- **F-01** Official Table 1 lists a 4.50% Kitchen category rate; individual ASIN category assignments are unconfirmed, so product-level cells are blank. **F-02** Prices and star ratings withheld by policy. **F-03** No Associates tag in the resolved links. **F-04** Short-link codes are not the resolved ASINs.
- **F-05** P2 brand/manufacturer confirmed. **F-06/F-07** listed capacity/color inconsistencies. **F-08** P3 is a size-variant family. **F-09** Snapshot used a US delivery-location display; no user-location claim is made. **F-10/F-29** competitor carousels and Sponsored labels vary between reads.
- **F-11/F-12/F-21** one-off verification and automated research/content are constrained by Amazon's Conditions of Use and Agent Terms. **F-13/F-14** prior deployment/prototype records are historical and superseded. **F-15** trend/popularity/conversion signals unverified. **F-16** Creators API license terms not reviewed. **F-17** policy-number corrections are recorded. **F-18** product-page field re-read matched; resolved. **F-19** local click log exists; attributed reporting is not connected. **F-20** competitor-label correction is retained as audit history.
- **F-22** price tracking/alerting restrictions. **F-23** Amazon Marks cannot be search keywords. **F-24/F-25** API reuse/model-training limits and the conservative Amazon-content notice. **F-26** P2's 24 vs. 25 cooking-function count discrepancy. **F-27** offline/email use restrictions. **F-28** manufacturers confirmed for all three products; resolved. **F-29** the "also viewed" carousel is an advertising slot and changes between loads — re-read on 2026-11-14 it reproduced exactly, and the one label that had been blank (`B0CNSB81V6`, "Nutrichef Double Basket Air Fryer 8.8 QT") was then read verbatim and filled, so no label is blank. **F-30** Conditions of Use help URL changed node ID — **resolved** 2026-11-14: the cited `nodeId=508088` still resolves through a redirect to the canonical `nodeId=GLSBYFE9MGKKQXXM`, and the wording was re-read on that fetch. **F-31** product specifications lack an approved content source. **F-32** short-link host confirmation is empirical; codes remain tokens. **F-33** API quota/price-timestamp rules not adopted. **F-34** duplicate Pages/CI configuration. **F-35** Creators API documentation differs on marketplace access. **F-36** the per-product commission rate was published without an official source for the per-ASIN category step; product cells are now blank (resolved). **F-37** carousel-instability notes cited F-27 where they meant F-29 (corrected). **F-38** the specification-table rows rest on the 2026-11-14 reads recorded by earlier sessions: the final integration session re-read identities, titles, breadcrumbs and competitor sets for all three products, but the lower part of each page returned advertising modules instead of the details table, so those rows were not re-confirmed in that session and are flagged rather than glossed over. **F-36** the site had published a per-product commission rate that no official source confirms for these ASINs — found independently by two sessions on 2026-11-14; the product-level cells are now blank and the category-level rate is stated with its source. **F-37** the carousel-instability notes cited F-27 where they meant F-29; corrected.

**Additional finding (parallel session):** no official Amazon documentation for the `link.amazon` domain was located; its resolution to Amazon.com was verified empirically on 2026-11-14 by several independent sessions, and a third-party description (https://linktw.in/link-amazon-vs-linktwin, **non-official**) says it routes via `amzlinks.in` (Button). Treat `link.amazon` links as leads until Amazon documents the domain.

## 5a. Requirement register

Every item in the brief, one row each, is published at `docs/requirements.html` with its delivery status and the official source that governs it. Summary of that register (full detail on the page):

| Status | Count | What it covers |
|---|---|---|
| Delivered | 16 | Site, verification discipline, disclosure, compliance, scalability, data-driven decisions, the marketing content kit, publishing on Pages |
| Delivered (partial) | 7 | Competition analysis, niche research, marketing content, link management, click tracking, category-rate reference (ASIN mapping pending), delivery for the three products |
| Not built — blocked (policy) | 5 | The AI-powered platform, automated research, price analysis, review analysis, full content automation |
| Not built — needs access | 2 | Campaign optimisation, attributed conversion reporting |
| Unverifiable (blank + flagged) | 2 | Trend analysis, conversion analysis |

Nothing is simulated in place of a blocked or unverified requirement.

## 6. Recommended next steps (owner, when ready)

1. Join or confirm the Amazon Associates Program for the final site and provide the Associates tag; generate Special Links for `B0CDY277D3`, `B09B7SB46R`, `B08DKYBTPH`.
2. Keep the site-wide and per-link disclosures (already templated) and re-verify the current policy pages at launch.
3. Commission product content only from verified data; target the Creators API (not PA-API 5) once eligible, and review its license terms first (F-16).
4. Decide whether the research agent may be automated at all; if so, implement the Agent Terms user-agent string and transparency rules first (F-21, F-11).
5. Enable the first-party tracker on real traffic, add a cookie or consent notice, and reconcile local clicks against Associates Central reporting (F-19, F-03).
6. Ask the seller for P2's correct cooking-function count (F-26). The Conditions of Use citation has been re-confirmed (F-30, resolved) — re-check it at the next policy review.
7. Re-verify volatile values and confirm the intended marketplace/storefront (F-09).

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

*Every table row above carries its source; values that could not be confirmed from an official source are blank, withheld, or flagged — never inferred.*
