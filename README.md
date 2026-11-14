# Zone4 — Amazon affiliate product research (verified)

A static research site for three user-supplied Amazon product links. It publishes only values that were checked against an official source. Anything that could not be verified is left blank and flagged.

**Live site (GitHub Pages):** https://kanlerxz87-cyber.github.io/Zone4/

The repository's Pages source is `main` `/` (legacy build). The root `index.html` redirects to `docs/index.html`, and the root `.nojekyll` stops Jekyll processing. Setting the Pages source to `main` `/docs` in Settings would also work; the redirect then becomes unused but harmless.

## What is in the repo

| Path | Purpose |
|---|---|
| `data/products.json` | Verified product records (ASIN, brand, category, specifications, competitor ASINs) |
| `data/marketing.json` | Marketing content kit: 3 product articles, 1 comparison page, 1 buying guide, SEO rules, publishing checklist |
| `data/pipeline.json` | The automation pipeline, the click/conversion metrics and the Agent Terms |
| `data/sources.json` | Source registry (20 entries): each official source, and whether it was read |
| `data/policies.json` | 30 Amazon Associates and FTC requirements, with status for this site |
| `data/flags.json` | 28 irregularities and unverified items (Flagged for Review) |
| `data/content.json` | Executive summary, 15 analysis findings, category text |
| `data/reverification-2026-11-14.json` | Independent re-verification record of the supplied links and citations |
| `scripts/build_site.py` | Builds `docs/` from `data/` (standard library only) |
| `scripts/verify.py` | Checks data and built pages; fails on any problem |
| `docs/` | The published site (14 generated pages plus the stylesheet, app script and tracker script) |
| `docs/analytics.html` + `docs/tracker.js` | First-party clicks & conversions tracker (local-only, starts at zero, no fabricated data) |
| `EXECUTIVE_SUMMARY.md` | Repository-level executive summary with the full source list |
| `.github/workflows/site-checks.yml` | CI: rebuilds, verifies, and confirms `docs/` is up to date |
| `COORDINATION.md` | Shared task board and work log for all sessions |

## Site pages

| Page | What it holds |
|---|---|
| `index.html` | Dashboard: KPIs, key findings, navigation cards |
| `executive-summary.html` | Headline findings, decisions needed, and what is not built |
| `products.html` | All three products, one row each, every row linked to its source |
| `categories/*.html` | One page per product format: dual-basket, single-basket, air-fry toaster ovens |
| `marketing.html` | Ready-to-publish articles, comparison page and buying guide, with a fact table per page |
| `automation.html` | Pipeline stages, tracking metrics, optimisation loop and the Agent Terms |
| `analysis.html` | 15 findings with their basis, confidence and source links |
| `verification.html` | Field-by-field verification log for every product |
| `policy-compliance.html` | 30 Amazon Associates and FTC rules, each with its official source section |
| `analytics.html` | Clicks & conversions: a local-only first-party click log, with export and clear |
| `flagged.html` | Flagged for Review: 28 irregularities and unverified items |
| `sources.html` | Every source, whether it was read, and what it was used for |

## Rebuild and verify

```bash
python3 scripts/build_site.py
python3 scripts/verify.py
```

The verifier fails the build if any table row lacks a link to an official source, if a link or anchor is broken, if the required disclosure is missing from a page, if a price or star rating appears, if an Amazon Mark is used as a page title, meta description or target keyword, or if a marketing fact row is never cited by a paragraph.

## Limits

- Amazon prices and star ratings are **not published**. Associates Participation Requirements 2(b) and 6(t) restrict them to Amazon-served links or Creators API / PA API data.
- Commission rates are **blank** (the official schedule is behind an Amazon sign-in).
- Attribution to the user's Associates ID is **unverified** (no tag in the resolved links).
- Attributed click, order, revenue and trend metrics are **blank**. No Associates reporting, API key or account is connected, so nothing is simulated. The Analytics page records first-party clicks in the visitor's own browser and publishes no attributed figure.
- Automated research at scale is **not built**. The Associates Program IP License, Section 4 (Agent Terms) governs any agent that touches Program Content.
- Price tracking and price alerting are **not built**: Participation Requirement 6(y) prohibits them unless Amazon agrees otherwise.
- Manufacturer is **blank** for P1 and P3: the Item details table was not read for those two pages, so it is not inferred from the brand (F-28).

Start with `flagged.html` on the live site for the items that need your decision.

The site is not endorsed by or affiliated with Amazon. Disclosure, per Associates Operating Agreement Section 5: "As an Amazon Associate I earn from qualifying purchases."
