# Executive Summary — Zone4 Amazon Affiliate Marketing Platform

**Date:** 2026-11-14 (UTC) · **Live site:** https://kanlerxz87-cyber.github.io/Zone4/ · **Scope of truth:** `data/*.json` → built into `docs/` by `scripts/build_site.py`, checked by `scripts/verify.py`

---

## 1. Mandate

Build an AI-powered Amazon affiliate marketing platform that automates product research, identifies trending and high-converting products, analyzes pricing, reviews, competition and commission potential, generates SEO content, manages affiliate links, tracks clicks and conversions, and continuously optimizes campaigns — with full compliance with Amazon Associates policies and disclosure requirements, and no manual input from the owner. Marketing was requested for three supplied product links.

## 2. What the repository delivers

1. **A live, evidence-first research site** on GitHub Pages: dashboard (`docs/index.html`), executive summary, product catalog, category pages (dual-basket air fryers / single-basket air fryers / air-fry toaster ovens), analysis & findings, field-by-field **verification log**, **policy compliance** page, **Flagged for Review** register, **sources** page, and a **first-party clicks & conversions tracker** (`docs/analytics.html` + `docs/tracker.js`). Every table row carries a link to its official source; withheld values are labeled, never inferred.
2. **Verified product identities** for all three submitted links (ASINs, listing titles, brands, category paths, listed specs, competitor ASINs) — see `data/products.json` and `docs/verification.html`.
3. **A compliance framework** quoting the official Associates Operating Agreement (updated 2025-10-15), Program Policies (updated 2026-04-14), disclosure guidance, Conditions of Use, and the PA-API 5 → Creators API deprecation notice — see `docs/policy-compliance.html`, `data/policies.json`, `data/sources.json`.
4. **A first-party click tracker** that starts at zero, stores events locally only, records only real or explicitly labeled test events, and exports/clears them. Conversion attribution is explicitly marked unavailable until an Associates account is connected.
5. **Automated checks**: `scripts/verify.py` (data validity, official-host-only links, per-page disclosure, per-row sources, no prices/ratings published, root redirect) runs in CI (`.github/workflows/site-checks.yml`) before GitHub Pages deploys.
6. **Coordination across parallel sessions** via `COORDINATION.md` (task board, claims, conflict log, merge and deployment records).

## 3. Product verification results (official Amazon sources, observed 2026-11-14)

| # | Submitted link | Resolved ASIN | Official listing title | Category (breadcrumb) | Brand | Price / rating / reviews | Commission |
|---|---|---|---|---|---|---|---|
| P1 | https://link.amazon/B04G1MEwY | `B0CDY277D3` | CHEFMAN 6 Quart Dual Basket Air Fryer Oven with Easy View Windows, Sync Finish, Hi-Fry, Auto Shutoff, 2 Independent 3Qt Nonstick Dishwasher Safe Frying Baskets, Digital Double Air Fryer - Black | Home & Kitchen › Kitchen & Dining › Small Appliances › Fryers › Air Fryers | Chefman | **Withheld** (flag F-02) | **Blank** (flag F-01) |
| P2 | https://link.amazon/B02NbDxp3 | `B09B7SB46R` | Emeril Lagasse 26QT French Door Multi-Function Air Fryer Toaster Oven (24 cooking functions, dual-speed fan, rotisserie) | Home & Kitchen › Kitchen & Dining › Small Appliances › Fryers › Air Fryers | Unresolved — store 'Emeril Store', byline 'Innovation IQ' (flag F-05) | **Withheld** (flag F-02) | **Blank** (flag F-01) |
| P3 | https://link.amazon/B00hJ57DV | `B08DKYBTPH` | Chefman Air Fryer 8 Qt \| TurboFry® 4-in-1 with 450°F Hi-Fry Option \| XL Nonstick Dishwasher-Safe Basket \| Stainless Steel | Home & Kitchen › Kitchen & Dining › Small Appliances › Fryers › Air Fryers | Chefman | **Withheld** (flag F-02) | **Blank** (flag F-01) |

**Key finding (confirmed independently by three sessions):** the 9-character strings in the submitted links (`B04G1MEwY`, `B02NbDxp3`, `B00hJ57DV`) are **short-link slugs, not ASINs** — using them as ASINs returns Amazon's official “Page Not Found” page (e.g., https://www.amazon.com/dp/B04G1MEwY). Amazon's own guide defines ASINs as **10-character alphanumeric** codes (https://sell.amazon.com/blog/what-is-an-asin). All three `link.amazon` URLs resolved to live Amazon.com product pages on 2026-11-14, and none of the resolved URLs carried an Associates `tag=` parameter.

**Withholding rationale (flag F-02):** the Associates Participation Requirements permit displaying prices/availability only via Amazon-served links or Creators API/PA API data (Section 6-area rules as numbered on the current Program Policies page), and star ratings/reviews only via API content. Amazon prices and ratings **were observed** during verification but are deliberately not published on this site. The ambiguous buy-box amounts observed for P1/P3 (Amazon Resale offers; lower “New & Used” offers existed) are recorded as session observations, not published.

## 4. Compliance status

- **Required disclosure** (displayed on every page of the site): *“As an Amazon Associate I earn from qualifying purchases.”* — required by the Operating Agreement; link-level disclosure must additionally be **clear** (“(paid link)”, “#ad”, “#CommissionsEarned”) and **conspicuous** near links/reviews. Source: https://affiliate-program.amazon.com/help/node/topic/GPXFHVYZMTGPUMPE
- **Special Links** must “properly use the special ‘tagged’ link formats” (Agreement §1) and carry the Associates tag (`XXXXX-##` format) as a URL parameter (Participation Requirements, Section 2(b) on the current Program Policies page); purchases via improperly formatted links are **disqualified** (Commission Income Statement §2). No Associates tag was supplied, so **no affiliate links are published** (flag F-03).
- Price/availability display requires Amazon-served or Creators/PA-API data; reviews/ratings display requires API content (6(t)); price-tracking/alerting functionality is prohibited; cloaking and unclear shorteners are prohibited (6(v)–(w)); artificial clicks are prohibited (6(s)); incentivized clicks and customer-content placement are restricted (6(g), 6(p)); search-engine bidding on Amazon marks is prohibited (6(e)–(f)); machine-learning use of Program Content requires prior express written approval (Participation Requirements §5). Sources: https://affiliate-program.amazon.com/help/operating/policies
- **PA-API 5 is officially deprecated** in favor of the **Creators API** (https://affiliate-program.amazon.com/creatorsapi/docs/en-us/paapiv5-deprecation) — any automation must target the Creators API; license terms not yet reviewed (flag F-16).
- Commission rates live behind the Associates sign-in schedule (https://affiliate-program.amazon.com/help/operating/schedule); the correct category row has not been confirmed, so **no rate is asserted** (flag F-01).
- Amazon Conditions of Use (updated 2026-08-14) additionally constrain scraping/data mining and AI use of Amazon content (flags F-11, F-12).
- The complete flag register (**F-01 … F-20**, 20 items) is published at `docs/flagged.html` with sources.

## 5. Flagged for review — headline items (complete register: `docs/flagged.html`)

- **F-01** Category commission rate unverified (schedule behind sign-in). **F-02** Prices and star ratings withheld by policy. **F-03** No Associates tag in resolved links.
- **F-04** Short-link slugs ≠ ASINs. **F-05** P2 brand ambiguous. **F-06/F-07/F-08** listed-spec inconsistencies and variant-family notes.
- **F-09** Snapshots used a US delivery location; no user-location or marketplace claim is made. **F-10** Competitor carousel “Sponsored” labels vary by snapshot (P2 earlier; P3 on one read).
- **F-11/F-12** Verification method and AI content automation are constrained by Amazon Conditions of Use. **F-13** Historic Pages-workflow failure (resolved; root redirect serves the site). **F-14** Prior prototype records superseded. **F-15** Trend/popularity/conversion signals unverified — no such claims are made. **F-16** Creators API license terms not reviewed.
- **F-17** Policy section numbers in earlier records were corrected (ratings rule is 6(t), shortening 6(w), keywords 6(e)–(f), incentives 6(g), customer content 6(p), trademarks-in-identifiers 1(g)). **F-18** Brand bylines and specification tables were not re-read in the final pass and are marked as such. **F-19** The brief's automation goals conflict with Program Policies unless PA-API/Creators API access exists — no automation built, nothing simulated. **F-20** Competitor labels are paraphrases (ASINs authoritative); the standalone participation page uses different numbering, so citations point to the Program Policies page.

**Additional finding (session `sess-cd6113ca`):** no official Amazon documentation for the `link.amazon` domain was located; its resolution to Amazon.com was verified empirically on 2026-11-14 by three independent sessions, and a third-party description (https://linktw.in/link-amazon-vs-linktwin, **non-official**) says it routes via `amzlinks.in` (Button). Treat `link.amazon` links as leads until Amazon documents the domain.

## 6. Recommended next steps (owner, when ready)

1. Join/confirm the Amazon Associates Program for the final site and provide the Associates tag; generate Special Links for ASINs B0CDY277D3, B09B7SB46R, B08DKYBTPH.
2. Keep the site-wide and per-link disclosures (already templated) and re-verify current policy pages at launch.
3. Commission product content only from verified data; use the Creators API (not PA-API 5) once eligible; review its license terms first (F-16).
4. Enable the first-party tracker (`docs/analytics.html`) on real traffic and reconcile clicks against Associates Central reporting.
5. Re-verify volatile values (F-18 items) and confirm the intended marketplace/storefront (F-09).

## 7. Official sources used (fetched live 2026-11-14 unless noted)

1. Associates Program Operating Agreement (updated 2025-10-15) — https://affiliate-program.amazon.com/help/operating/agreement
2. Associates Program Policies (updated 2026-04-14; Commission Income Statement, Participation Requirements, IP License, Trademark Guidelines) — https://affiliate-program.amazon.com/help/operating/policies
3. Associates commission schedule (redirects to sign-in) — https://affiliate-program.amazon.com/help/operating/schedule
4. Amazon Associates disclosure help page — https://affiliate-program.amazon.com/help/node/topic/GPXFHVYZMTGPUMPE
5. Amazon ASIN guide (10-character standard) — https://sell.amazon.com/blog/what-is-an-asin
6. PA-API 5 deprecation / Creators API notice — https://affiliate-program.amazon.com/creatorsapi/docs/en-us/paapiv5-deprecation
7. Amazon Conditions of Use (updated 2026-08-14) — https://www.amazon.com/gp/help/customer/display.html?nodeId=508088
8. Amazon product pages — https://www.amazon.com/dp/B0CDY277D3 · https://www.amazon.com/dp/B09B7SB46R · https://www.amazon.com/dp/B08DKYBTPH (plus the three submitted `link.amazon` URLs)
9. Amazon 404 evidence for slug-as-ASIN lookups — https://www.amazon.com/dp/B04G1MEwY (and the other two slugs)
10. FTC Endorsement Guides FAQ — https://www.ftc.gov/business-guidance/resources/ftcs-endorsement-guides-what-people-are-asking · FTC Disclosures 101 — https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers
11. Third-party, non-official corroboration of the `link.amazon` domain — https://linktw.in/link-amazon-vs-linktwin (flagged as non-official)

*Every table row above carries its source; values that could not be confirmed from an official source are blank, withheld, or flagged — never inferred.*
