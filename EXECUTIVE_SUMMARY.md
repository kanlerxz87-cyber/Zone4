# Executive summary — Zone4 (Northstar)

**What this is.** A GitHub Pages site that publishes specification-led buying guides and comparison pages
for five kitchen products the owner supplied as five `link.amazon/...` short links, alongside a
line-by-line verification record for every number it prints. Live site:
[https://kanlerxz87-cyber.github.io/Zone4/](https://kanlerxz87-cyber.github.io/Zone4/).

**Status: live, verified to the official sources on 2026-11-17, and ready for owner review of the items
flagged below.** Nothing in this repository reports a price, rating, review count or commission figure;
those are site policy blanks pending owner direction.

---

## 1. The five products (as supplied → as verified)

Each short link was followed to its final Amazon listing; the intended link and the observed redirect
are recorded in separate fields in [`data/product-intent.json`](data/product-intent.json) and published
as the [product-intent confirmation record](https://kanlerxz87-cyber.github.io/Zone4/docs/products.html).

| # | Submitted link | Intended ASIN | Listing (official source) | Category |
|---|----------------|---------------|---------------------------|----------|
| P1 | `link.amazon/B04G1MEwY` | `B0CDY277D3` | [Chefman 6-Quart Dual Basket Air Fryer Oven](https://www.amazon.com/dp/B0CDY277D3) | [Dual basket](https://kanlerxz87-cyber.github.io/Zone4/docs/categories/dual-basket-air-fryers.html) |
| P2 | `link.amazon/B02NbDxp3` | `B09B7SB46R` | [Emeril Lagasse 26 QT French Door Air Fryer Toaster Oven](https://www.amazon.com/dp/B09B7SB46R) | [Toaster-oven style](https://kanlerxz87-cyber.github.io/Zone4/docs/categories/air-fryer-toaster-ovens.html) |
| P3 | `link.amazon/B00hJ57DV` | `B08DKYBTPH` | [Chefman 8-Quart Single Basket Air Fryer](https://www.amazon.com/dp/B08DKYBTPH) | [Single basket](https://kanlerxz87-cyber.github.io/Zone4/docs/categories/single-basket-air-fryers.html) |
| P4 | `link.amazon/B0c8moW59` | `B0DHZTCNR5` | [ThermoMaven HT07 meat thermometer](https://www.amazon.com/dp/B0DHZTCNR5) | [Meat thermometers](https://kanlerxz87-cyber.github.io/Zone4/docs/categories/meat-thermometers.html) |
| P5 | `link.amazon/B0f3GKalj` | `B0DZFD6R9Z` | [CHEF iQ Sense Gen3 wireless meat thermometer](https://www.amazon.com/dp/B0DZFD6R9Z) | [Meat thermometers](https://kanlerxz87-cyber.github.io/Zone4/docs/categories/meat-thermometers.html) |

Two observations the owner should look at: **P4 and P5 resolve to meat thermometers, not air fryers**
(flag [F-56](https://kanlerxz87-cyber.github.io/Zone4/docs/flagged.html#F-56), intent re-confirmation
requested as [Q-45](https://kanlerxz87-cyber.github.io/Zone4/docs/questions.html)), and each listing
shows a variant family (size/color sub-listings), so the exact variant a submitted link intends is
flagged ([F-57](https://kanlerxz87-cyber.github.io/Zone4/docs/flagged.html#F-57),
[F-59](https://kanlerxz87-cyber.github.io/Zone4/docs/flagged.html#F-59)).

## 2. Tracking ID and Special Links (built, tested, not yet revenue-validated)

The owner supplied tracking ID **`shopnow047c-20`** on 2026-11-17. Every reader-facing product link on
the site is now a constructed Associates **Special Link** carrying that tag
(`https://www.amazon.com/dp/<ASIN>?tag=shopnow047c-20&linkCode=ogi&th=1&psc=1`), and each of the five was
**destination-tested on 2026-11-17** (the URL serves the intended listing; the record is in
[`data/product-intent.json`](data/product-intent.json)). As instructed, one link per product was tested
before scaling to the full site.

- **Attribution is not claimed.** Whether clicks and orders actually attribute to `shopnow047c-20` can
  only be confirmed in Associates Central reports by the account holder — that is the owner's validation
  gate (flag [F-03](https://kanlerxz87-cyber.github.io/Zone4/docs/flagged.html#F-03)).
- **The supplied short links are not called invalid.** Their compliance status is unresolved
  (flag FLG-003); they keep their register spot and appear in the published
  [intent table](https://kanlerxz87-cyber.github.io/Zone4/docs/products.html).
- Every product link carries `rel="sponsored"` and a plain "paid link" label beside the disclosure.

## 3. Verification method (unchanged, now covering five products)

Every published value was read from an official manufacturer, Amazon listing or Amazon policy page —
**never inferred**. Unconfirmed cells stay blank and carry a flag. Every table row on the site links to
its official source. The full field-by-field log is at
[verification.html](https://kanlerxz87-cyber.github.io/Zone4/docs/verification.html), maintained by
`scripts/verify.py` + `qa/audit_site.py` + `tools/check_links.py` + `tests/test_engine.py` (83 tests),
which fail the build on any unsourced row, price string, rating string or unmarked Amazon link.

## 4. Measurement: five defined events, local counter, empty campaign ledger

The brief asked for a privacy-preserving outbound-click counter and five defined events. The schema of
record is [`data/campaign-ledger.json`](data/campaign-ledger.json) (decision D-42):

| Event | Where | Recorded by |
|-------|-------|-------------|
| `page_view`, `outbound_click`, `chooser_answer` | site-side | `docs/tracker.js` — the visitor's browser only (`localStorage`), **no network call** |
| `reported_click`, `reported_order` | report-side | Authorized Associates Central reports export only — this site never generates them |

The **campaign ledger starts empty by design**: rows enter it only from named first-party reports with a
source and read-date per row. No conversion score, no revenue forecast, and no invented number appears
anywhere (the engine's tracking module refuses synthetic sources by test). A self-hosted analytics
endpoint is deliberately not configured — GitHub Pages is static-only and the owner must provide the
endpoint and privacy basis first (decision D-44). Everything is on the
[analytics page](https://kanlerxz87-cyber.github.io/Zone4/docs/analytics.html).

## 5. The site itself

Four category hubs ([single basket](https://kanlerxz87-cyber.github.io/Zone4/docs/categories/single-basket-air-fryers.html),
[dual basket](https://kanlerxz87-cyber.github.io/Zone4/docs/categories/dual-basket-air-fryers.html),
[toaster-oven style](https://kanlerxz87-cyber.github.io/Zone4/docs/categories/air-fryer-toaster-ovens.html),
[meat thermometers](https://kanlerxz87-cyber.github.io/Zone4/docs/categories/meat-thermometers.html)),
a three-question chooser, question-shaped buying guides and comparisons (8 marketing pieces including a
seasonal 2026 holiday gift guide and the Nov-2026 thermometer guide), and a measured-query target
list. A complete category-anchored cluster map, `sitemap.xml` and an RSS feed (`feed.xml`) are
regenerated at every build; the cadence is at least one question-shaped guide per month (decision D-43).

## 6. Compliance gate

Publication is gated in the engine (seven items blocked from publishing until each is verified or
owner-approved) plus the automated checks above. The gate's rule sets are the owner's "OA, FTC":
[Amazon Associates Program Policies](https://affiliate-program.amazon.com/help/operating/policies) and
[FTC disclosure guidance for influencers](https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers)
(that FTC page itself points to the Operating Agreement). The Influencer Program terms are recorded in
the policy register but are not the gate. Site-wide: disclosure strip under the masthead on every page, a
footer disclosure, `rel="sponsored"` + "paid link" labels on every product link, and no trademarked
domain in the brand.

## 7. What the owner should review (everything flagged is published, nothing blocks)

- **F-01** — exact commission schedule for `shopnow047c-20` unverified; the rate table stays blank.
- **F-03** — validate click/order attribution in Associates Central reports, then scale link use.
- **F-56 / Q-45** — confirm that two thermometer links are intended (they were supplied as products to market).
- **F-57 / F-59** — which variant each submitted link intends (size/color sub-listings).
- **F-53** — the listed model looks superseded by a newer generation; the current listing is published as supplied.
- The publish-gate checkboxes on [policy-compliance.html](https://kanlerxz87-cyber.github.io/Zone4/docs/policy-compliance.html).

Questions: 48 entries with known-vs-unknown splits and concrete discovery paths
([questions.html](https://kanlerxz87-cyber.github.io/Zone4/docs/questions.html)). Review-before-implement
choices: [suggestions.html](https://kanlerxz87-cyber.github.io/Zone4/docs/suggestions.html) (implemented
items name the change set and their enforcement tests).

---

*Every claim in this document is verified against an official source or flagged as unverified; the
published [verification log](https://kanlerxz87-cyber.github.io/Zone4/docs/verification.html) links each
field to its official source. This page displays no prices, ratings or review counts (F-02).*
