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
| `data/sources.json` | Source registry: each official source, and whether it was read |
| `data/policies.json` | Amazon Associates and FTC requirements, with status for this site |
| `data/flags.json` | Irregularities and unverified items (Flagged for Review) |
| `data/content.json` | Executive summary, analysis findings, category text |
| `data/reverification-2026-11-14.json` | Independent re-verification record from a parallel session |
| `scripts/build_site.py` | Builds `docs/` from `data/` (standard library only) |
| `scripts/verify.py` | Checks data and built pages; fails on any problem |
| `docs/` | The published site |
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
| `analysis.html` | 14 findings with their basis, confidence and source links |
| `verification.html` | Field-by-field verification log for every product |
| `policy-compliance.html` | 28 Amazon Associates and FTC rules, each with its official source section |
| `flagged.html` | Flagged for Review: 26 irregularities and unverified items |
| `sources.html` | Every source, whether it was read, and what it was used for |

## Rebuild and verify

```bash
python3 scripts/build_site.py
python3 scripts/verify.py
```

The verifier fails the build if any table row lacks a link to an official source, if a link or anchor is broken, if the required disclosure is missing from a page, if a price or star rating appears, or if an Amazon Mark is used as a page title, meta description or target keyword.

## Limits

- Amazon prices and star ratings are **not published**. Associates Participation Requirements 2(b) and 3(t) restrict them to Amazon-served links or PA-API / Creators API data.
- Commission rates are **blank** (the official schedule is behind an Amazon sign-in).
- Attribution to the user's Associates ID is **unverified** (no tag in the resolved links).
- Click, conversion, revenue and trend metrics are **blank**. No Associates reporting, API key or account is connected, so nothing is simulated.
- Automated research at scale is **not built**. The Associates Program IP License, Section 4 (Agent Terms) governs any agent that touches Program Content.
- Price tracking and price alerting are **not built**: Participation Requirement 3(y) prohibits them unless Amazon agrees otherwise.

Start with `flagged.html` on the live site for the items that need your decision.

The site is not endorsed by or affiliated with Amazon. Disclosure, per Associates Operating Agreement Section 5: "As an Amazon Associate I earn from qualifying purchases."
