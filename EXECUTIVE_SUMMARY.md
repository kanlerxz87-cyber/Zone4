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
| P1 | https://link.amazon/B04G1MEwY | `B0CDY277D3` | CHEFMAN 6 Quart Dual Basket Air Fryer Oven with Easy View Windows, Sync Finish, Hi-Fry, Auto Shutoff, 2 Independent 3Qt Nonstick Dishwasher Safe Frying Baskets, Digital Double Air Fryer - Black | Home & Kitchen › Kitchen & Dining › Small Appliances › Fryers › Air Fryers | Chefman | **Withheld** (flag F-02) | **4.50%** Kitchen band — official Table 1; per-ASIN mapping pending (flag F-01) |
| P2 | https://link.amazon/B02NbDxp3 | `B09B7SB46R` | Emeril Lagasse 26QT French Door Multi-Function Air Fryer Toaster Oven (24 cooking functions, dual-speed fan, rotisserie) | Home & Kitchen › Kitchen & Dining › Small Appliances › Fryers › Air Fryers | Emeril — brand confirmed from Item details; byline still to confirm (flag F-05) | **Withheld** (flag F-02) | **4.50%** Kitchen band — official Table 1; per-ASIN mapping pending (flag F-01) |
| P3 | https://link.amazon/B00hJ57DV | `B08DKYBTPH` | Chefman Air Fryer 8 Qt \| TurboFry® 4-in-1 with 450°F Hi-Fry Option \| XL Nonstick Dishwasher-Safe Basket \| Stainless Steel | Home & Kitchen › Kitchen & Dining › Small Appliances › Fryers › Air Fryers | Chefman | **Withheld** (flag F-02) | **4.50%** Kitchen band — official Table 1; per-ASIN mapping pending (flag F-01) |

**Key finding (confirmed independently by three sessions):** the 9-character strings in the submitted links (`B04G1MEwY`, `B02NbDxp3`, `B00hJ57DV`) are **short-link slugs, not ASINs** — using them as ASINs returns Amazon's official “Page Not Found” page (e.g., https://www.amazon.com/dp/B04G1MEwY). Amazon's own guide defines ASINs as **10-character alphanumeric** codes (https://sell.amazon.com/blog/what-is-an-asin). All three `link.amazon` URLs resolved to live Amazon.com product pages on 2026-11-14, and none of the resolved URLs carried an Associates `tag=` parameter.

**Withholding rationale (flag F-02):** the Associates Participation Requirements permit displaying prices/availability only via Amazon-served links or Creators API/PA API data (Section 6-area rules as numbered on the current Program Policies page), and star ratings/reviews only via API content. Amazon prices and ratings **were observed** during verification but are deliberately not published on this site. The ambiguous buy-box amounts observed for P1/P3 (Amazon Resale offers; lower “New & Used” offers existed) are recorded as session observations, not published.

## 4. Compliance status

- **Required disclosure** (displayed on every page of the site): *“As an Amazon Associate I earn from qualifying purchases.”* — required by the Operating Agreement; link-level disclosure must additionally be **clear** (“(paid link)”, “#ad”, “#CommissionsEarned”) and **conspicuous** near links/reviews. Source: https://affiliate-program.amazon.com/help/node/topic/GPXFHVYZMTGPUMPE
- **Special Links** must “properly use the special ‘tagged’ link formats” (Agreement §1) and carry the Associates tag (`XXXXX-##` format) as a URL parameter (Participation Requirements, Section 2(b) on the current Program Policies page); purchases via improperly formatted links are **disqualified** (Commission Income Statement §2). No Associates tag was supplied, so **no affiliate links are published** (flag F-03).
- Price/availability display requires Amazon-served or Creators/PA-API data; reviews/ratings display requires API content (6(t)); price-tracking/alerting functionality is prohibited; cloaking and unclear shorteners are prohibited (6(v)–(w)); artificial clicks are prohibited (6(s)); incentivized clicks and customer-content placement are restricted (6(g), 6(p)); search-engine bidding on Amazon marks is prohibited (6(e)–(f)); machine-learning use of Program Content requires prior express written approval (Participation Requirements §5). Sources: https://affiliate-program.amazon.com/help/operating/policies
- **PA-API 5 is officially deprecated** in favor of the **Creators API** (https://affiliate-program.amazon.com/creatorsapi/docs/en-us/paapiv5-deprecation) — any automation must target the Creators API; license terms not yet reviewed (flag F-16).
- **Commission rates are now sourced.** The `help/operating/schedule` appendix does redirect to a sign-in page, but the same Table 1 is published on a public Associates help topic (https://affiliate-program.amazon.com/help/node/topic/GRXPHT8U84RAYDXZ), read 2026-11-14: Kitchen **4.50%**, Home/Toys/Tools/Beauty 3.00%, All Other Categories 4.00%, the exclusion list 0.00%, top band 10.00%, Fine Art capped at 200 USD per product, Prime bounties 12.00 USD per event. The 4.50% figure is recorded on all three product rows and rendered in the catalog, verification and category tables with the table cited. What flag F-01 still covers is the mapping: Amazon assigns the commission category per item, and the breadcrumb top node *Home & Kitchen* straddles the Kitchen (4.50%) and Home (3.00%) rows, so no per-ASIN rate is asserted and no earning figure is derived.
- Amazon Conditions of Use (updated 2026-08-14) additionally constrain scraping/data mining and AI use of Amazon content (flags F-11, F-12).
- The complete flag register (**F-01 … F-28** plus **F-50 … F-54**; ID F-22 and the F-29…F-49 range intentionally unused) is published at `docs/flagged.html` with sources. The F-50 block was numbered above the sequential range because concurrent sessions allocate F-nn ids as they work; the two ranges must never be renumbered into each other.

## 5. Flagged for review — headline items (complete register: `docs/flagged.html`)

- **F-01** Commission rate now sourced from the public official table (Kitchen 4.50%); what remains open is which band Amazon assigns per ASIN. **F-02** Prices and star ratings withheld by policy. **F-03** No Associates tag in resolved links.
- **F-04** Short-link slugs ≠ ASINs. **F-05** P2 brand ambiguous. **F-06/F-07/F-08** listed-spec inconsistencies and variant-family notes.
- **F-09** Snapshots used a US delivery location; no user-location or marketplace claim is made. **F-10** Competitor carousel “Sponsored” labels vary by snapshot (P2 earlier; P3 on one read).
- **F-11/F-12** Verification method and AI content automation are constrained by Amazon Conditions of Use. **F-13** Historic Pages-workflow failure (resolved; root redirect serves the site). **F-14** Prior prototype records superseded. **F-15** Trend/popularity/conversion signals unverified — no such claims are made. **F-16** Creators API license terms not reviewed.
- **F-24 → implemented.** The IP License 2(k) plain-view notice is now rendered on every generated page, driven by `data/content.json` (`site_disclaimer`), because the site displays Amazon listing titles.
- **F-50** Specification fields (capacity, dimensions, colour, material, titles) are shown although they were read from the page rather than SiteStripe or the API — same exposure class as F-02. **F-51** The short-link host is confirmed Amazon-controlled via IANA, and the codes are tokens, not ASINs. **F-52** API quota figures and the price-timestamp clause are third-party claims and are deliberately not encoded. **F-53** Two Pages publishers and two CI pipelines are configured. **F-54** Two official Creators API pages describe cross-marketplace access differently, so the engine takes the narrower reading.
- **F-21** Manufacturer not confirmed for P1 and P3. **F-23** Amazon Agent Terms apply to any automated agent that accesses Program Content (relevant gate before any automation; the shipped click tracker does not access Amazon content). **F-24** An Amazon text disclaimer is required if Amazon text is displayed. (Flag ID F-22 is unused.)
- **F-17** Policy section numbers in earlier records were corrected (ratings rule is 6(t), shortening 6(w), keywords 6(e)–(f), incentives 6(g), customer content 6(p), trademarks-in-identifiers 1(g)). **F-18** Brand bylines and specification tables were not re-read in the final pass and are marked as such. **F-19** The brief's automation goals conflict with Program Policies unless PA-API/Creators API access exists — no automation built, nothing simulated. **F-20** Competitor labels are paraphrases (ASINs authoritative); the standalone participation page uses different numbering, so citations point to the Program Policies page.

**Additional finding (session `sess-cd6113ca`):** no official Amazon documentation for the `link.amazon` domain was located; its resolution to Amazon.com was verified empirically on 2026-11-14 by three independent sessions, and a third-party description (https://linktw.in/link-amazon-vs-linktwin, **non-official**) says it routes via `amzlinks.in` (Button). **Answered:** IANA's root zone database shows `.amazon` as an active gTLD delegated to Amazon Registry Services, Inc. since 2020-06-02 (https://www.iana.org/domains/root/db/.amazon.html), so `link.amazon` is an Amazon-controlled registry domain rather than an unexplained third-party shortener; this is recorded as flag F-51. The remaining caution is operational, not ontological: a link that carries no Associates tag cannot attribute a sale (F-03, F-25).

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
11. Standard Commission Income Statement, Table 1 (public) — https://affiliate-program.amazon.com/help/node/topic/GRXPHT8U84RAYDXZ
12. Creators API introduction and FAQ — https://affiliate-program.amazon.com/creatorsapi/docs/en-us/introduction · https://affiliate-program.amazon.com/creatorsapi/docs/en-us/frequently-asked-questions
13. IANA root zone database, `.amazon` — https://www.iana.org/domains/root/db/.amazon.html
14. Google Search Central, people-first content — https://developers.google.com/search/docs/fundamentals/creating-helpful-content
15. Third-party, non-official corroboration of the `link.amazon` domain — https://linktw.in/link-amazon-vs-linktwin (flagged as non-official)

*Every table row above carries its source; values that could not be confirmed from an official source are blank, withheld, or flagged — never inferred.*

## 8. Automation layer (session `arena/8592c4f6`) — what now exists as code

Everything above is data and prose. This part is the executable platform the mandate asked for, added in
`engine/` (standard library only, no network calls at build time) and deliberately kept out of `docs/`: the
published pages stay generated by `scripts/build_site.py`, so the site has one source of truth.

| Capability the mandate asked for | Where it lives | What it publishes today |
|---|---|---|
| Product research and verification | `engine/research.py`, `engine/datastore.py` | Verified identity fields; refuses any row that asserts a value without an official source (the build fails, it does not warn) |
| Trending / high-converting identification | `engine/scoring.py` | **Nothing** — 0 of 3 products have the inputs a score requires, so the model returns `None` plus a missing-input list instead of a number |
| Pricing, review, competition, commission analysis | `engine/economics.py`, `data/engine-program.json` | Rates, bounties, caps and attribution windows with sources; prices and ratings withheld by policy (F-02, F-50) |
| SEO article / comparison / buying-guide generation | `engine/content.py`, `engine/agent.py` | Drafts exist but **all 7 are blocked by the publish gate**; a draft containing one unverified placeholder cannot be written to disk |
| Niche identification | `data/content.json` A-01…A-14, `engine/scoring.py` | One niche confirmed from the breadcrumb; no market-size or demand claim is made |
| Link publishing and management | `engine/links.py` | **Zero links** — it refuses to emit a tagged link without a real Partner Tag, and refuses any shortener that hides the Amazon destination (F-03, F-25) |
| Click and conversion tracking | `engine/tracking.py`, `data/tracking.jsonl` | An empty ledger with real attribution windows (24 h / 89 d / 180 d); metrics render blank, never a fabricated `0`; it rejects events not marked as authorized |
| Continuous optimization and automation | `engine/agent.py`, `engine/cli.py` | `python3 -m engine.cli {status\|verify\|rates\|economics\|audit\|content\|links\|tracking\|build}` |
| Compliance enforcement | `engine/policy.py` (26 cited controls incl. TEXT-01 for the 2(k) notice and AGENT-01 for the Agent Terms) | Blocking findings per draft, mirrored by `tools/check_links.py` for the rendered pages |

**Why the honest blanks are the deliverable.** A platform like this fails in production by publishing a
plausible number nobody sourced — an invented commission, a hallucinated rating, a "high-converting" badge
with no conversion data. The guarantee is structural rather than procedural: `Claim.__post_init__` raises if a
non-verified claim carries a value, `Datastore.audit()` raises if an asserted row lacks a source, the content
generator emits a blocking placeholder, and `_self_check` refuses to write a page that leaks `None`, an
unresolved placeholder, or a tagged link on a redirect host. 32 of 75 tracked claims are verified; the other
43 are blank **with a stated reason** — policy (F-02, F-50), missing account access (F-03, F-25), or no
authorized source at all (F-15). `python3 -m unittest discover -s tests` covers these paths (81 tests), and two
of them re-run `scripts/build_site.py` and `scripts/verify.py` so the engine can never silently break the site.

**What the owner must supply, in order of what it unblocks:**

1. An Associates **Partner Tag** for this site → `engine/links.py` starts emitting Special Links; F-03 and
   F-25 close. Until then nothing published can earn, and the site correctly says so.
2. The **commission category Amazon applies** to B0CDY277D3, B09B7SB46R, B08DKYBTPH (Associates Central) → F-01
   closes, or the published 4.50% becomes 3.00%.
3. **10 qualifying sales in 30 days**, then Creators API credentials → ratings, review counts and live pricing
   become lawfully displayable, `engine/scoring.py` starts producing scores, and F-16/F-52 can be cleared.
4. A decision on **F-50** (re-source the specification fields, or withhold them like prices).
5. **One** Pages publisher (F-53) and a written-approval check before any AI drafting is fed Amazon-sourced
   content (F-12).
