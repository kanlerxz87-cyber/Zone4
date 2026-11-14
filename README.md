# Zone4 — Amazon affiliate research and marketing platform

A verified, data-driven affiliate research site for three user-supplied Amazon product links, plus the marketing drafts, requirement
traceability and platform blueprint the brief asks for. It publishes only values checked against an official source; anything else is left
blank and flagged. **Live site (GitHub Pages, `main` branch; the root redirects to `docs/`):** https://kanlerxz87-cyber.github.io/Zone4/

## What is in the repo

| Path | Purpose |
|---|---|
| `data/products.json` | Product records (ASIN, brand and manufacturer as recorded, category, specifications, competitor ASINs) |
| `data/sources.json` | Source registry: each official source, whether it was read, and the second-pass re-check note |
| `data/policies.json` | 31 Amazon Associates, IP License and FTC requirements, each with a verbatim quote and this site's status |
| `data/flags.json` | 29 irregularities and unverified items (published on the Flagged for Review page) |
| `data/content.json` | Executive summary, findings, marketing drafts, requirements coverage, platform blueprint, re-verification log |
| `data/reverification-2026-11-14.json` | Independent re-verification record of the supplied links and citations (2026-11-14), with the integration correction note |
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
star-rating string may appear, the Associates disclosure and the IP License 2(k) content disclaimer must appear on every page, no copy may
claim the product was tested, no page may reuse Amazon's badge or sales strings, and every page must be reachable from the sidebar.

## Verification status

* Two independent passes ran on 2026-11-14. The re-verification page lists 25 checks: link redirects, listing titles, category breadcrumbs,
  also-viewed ASINs and the absence of a tag parameter were re-confirmed, and every policy quote was checked against the live official page.
* Re-confirmed: all three `link.amazon` short links resolve to ASINs `B0CDY277D3`, `B09B7SB46R`, `B08DKYBTPH`, with no Associates tag.
* Carried forward, not re-verified in the later pass: the Item details specification fields (litre capacity, dimensions, colour, material) —
  flag F-18; a brand page disagrees on one dimension (F-28).
* Deliberately blank: prices, ratings, review counts, commission rate, trend and conversion data — flags F-01, F-02, F-15.

## Limits

* Amazon prices and star ratings are not published. Associates Participation Requirements 2(b) and 6(t) restrict them to Amazon-served links
  or PA-API / Creators API data.
* Price tracking or price alerting is not built at all: Participation Requirements 6(y) bars it on the Site (F-25).
* The IP License goes further than the Conditions of Use: API content may not be aggregated, analysed, repurposed or used to train a model
  without express prior written approval (rules R-17, R-28, flags F-12, F-30), so the automation stages are documented and gated, not built.
* Marketing copy is published as drafts inside this research site, not as monetised pages: no approved Associates account or tagged Special
  Link is confirmed here (F-27).
* Commission rates are blank; the official schedule sits behind an Amazon sign-in (F-01).

Start with `docs/flagged.html` for the items that need a decision.

The site is not endorsed by or affiliated with Amazon. Disclosure, per Associates Operating Agreement Section 5: "As an Amazon Associate I earn from qualifying purchases."
