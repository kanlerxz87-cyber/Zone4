# Zone4 — Amazon affiliate product research and marketing platform

A verified, data-driven affiliate research site for three user-supplied Amazon product links, plus the marketing drafts, requirement
traceability and platform blueprint that the brief asks for. It publishes only values checked against an official source; anything else is
left blank and flagged. Live site: https://kanlerxz87-cyber.github.io/Zone4/ (GitHub Pages, built from `main`).

## What is in the repo

| Path | Purpose |
|---|---|
| `data/products.json` | Product records (ASIN, brand as shown, category, specifications, competitor ASINs) |
| `data/sources.json` | Source registry: each official source, whether it was read, and the 2026-11-14 re-check note |
| `data/policies.json` | 24 Amazon Associates and FTC requirements, each with a verbatim quote and its status on this site |
| `data/flags.json` | 22 irregularities and unverified items (published on the Flagged for Review page) |
| `data/content.json` | Executive summary, findings, marketing drafts, requirements coverage, platform blueprint, re-verification log |
| `scripts/build_site.py` | Builds `docs/` from `data/` (standard library only, deterministic) |
| `scripts/pages_extra.py` | Page bodies for the marketing, platform, requirements and re-verification views |
| `scripts/verify.py` | Fails the build on any unsourced row, price or rating string, missing disclosure, testing claim or broken nav link |
| `docs/` | The published site |
| `.github/workflows/site-checks.yml` | CI: rebuild, verify, confirm `docs/` matches the data |
| `COORDINATION.md` | Shared task board, claims, sources and merge log for all sessions |

## The 15 pages

Dashboard, executive summary, all products, three category pages, analysis and findings, marketing content (drafts), platform and
automation, requirements coverage, verification log, re-verification pass, policy compliance, flagged for review, sources.

## Rebuild and verify

```bash
python3 scripts/build_site.py
python3 scripts/verify.py
```

`verify.py` enforces the compliance rules mechanically, so a mistake cannot ship: every table row must link to an official host, no price or
star-rating string may appear, the disclosure sentence must be on every page, no copy may claim the product was tested, and every page must
be reachable from the sidebar.

## Verification status

* 23 checks in the independent re-verification pass of 2026-11-14 (`docs/reverification.html`): link redirects, listing titles, category
  breadcrumbs, also-viewed ASINs, the absence of a tag parameter, and every policy quote were re-read from the official pages.
* Re-confirmed: all three `link.amazon` short links resolve to ASINs `B0CDY277D3`, `B09B7SB46R`, `B08DKYBTPH`, with no Associates tag.
* Carried forward, not re-verified: the four specification-table fields (litre capacity, dimensions, colour, material) — flag F-17.
* Deliberately blank: prices, ratings, review counts, commission rate, trend and conversion data — flags F-01, F-02, F-15.

## Limits

* Amazon prices and star ratings are not published. Participation Requirements 2(b) and 3(t) restrict them to Amazon-served links or
  PA-API / Creators API data.
* Price tracking or price alerting is not built at all: Participation Requirements 3(y) bars it on the Site (F-18).
* Program Content may not be used to develop machine learning models (Participation Requirements 5, and the same in the Conditions of Use),
  so no model is trained on listing data and automated generation stays gated (F-12, F-19).
* Marketing copy is published as drafts inside this research site, not as monetised pages: no approved Associates account or tagged Special
  Link is confirmed here (F-21).
* Commission rates are blank; the official schedule sits behind an Amazon sign-in (F-01).

Start with `docs/flagged.html` for the items that need a decision.

The site is not endorsed by or affiliated with Amazon. Disclosure, per Associates Operating Agreement Section 5: "As an Amazon Associate I earn from qualifying purchases."
