# Zone4 — Amazon affiliate research and marketing platform

A verified, data-driven affiliate research site for three user-supplied Amazon product links, plus the marketing drafts, requirement
traceability and platform blueprint the brief asks for. It publishes only values checked against an official source; anything else is left
blank and flagged. **Live site (GitHub Pages, `main` branch; the root redirects to `docs/`):** https://kanlerxz87-cyber.github.io/Zone4/

## What is in the repo

| Path | Purpose |
|---|---|
| `data/products.json` | Product records (ASIN, brand and manufacturer as recorded, category, specifications, competitor ASINs) |
| `data/requirements.json` | Every requirement in the project brief with its delivery status and the official source for that status (30 rows, maintained by the integration sessions; rendered as `docs/requirements.html`) |
| `data/verification-session-ebf5c261.json` | Final-integration verification record for the combined data |
| `data/sources.json` | Source registry: each official source, whether it was read, and the second-pass re-check note |
| `data/policies.json` | 32 Amazon Associates, IP License and FTC requirements, each with a verbatim quote and this site's status |
| `data/flags.json` | 34 irregularities and unverified items (published on the Flagged for Review page) |
| `data/content.json` | Executive summary, findings, marketing drafts, brief coverage (Q-01 to Q-26), platform blueprint, re-verification log |
| `qa/audit_site.py` + `qa/README.md` | Independent QA audit (link-level disclosure beside every shop link, duplicate ids, a11y and SEO basics), run in CI |
| `.github/workflows/qa.yml` | CI: the QA audit, separate from `site-checks.yml` |
| `data/reverification-2026-11-14.json` | Independent re-verification record of the supplied links and citations (2026-11-14), with the integration correction note |
| `scripts/build_site.py` | Builds `docs/` from `data/` (standard library only, deterministic) |
| `scripts/pages_extra.py` | Page bodies for the marketing, platform, requirements and re-verification views |
| `scripts/verify.py` | Fails the build on any unsourced row, price or rating string, missing disclosure, testing claim or broken nav link |
| `docs/` | The published site |
| `.github/workflows/site-checks.yml` | CI: rebuild, verify, confirm `docs/` matches the data |
| `COORDINATION.md` | Shared task board, claims, sources and merge log for all sessions |
| `docs/analytics.html` + `docs/tracker.js` | First-party clicks & conversions tracker (local-only, starts at zero, no fabricated data) |
| `EXECUTIVE_SUMMARY.md` | Repository-level executive summary with the full source list |

## The 17 pages

Dashboard, executive summary, all products, three category pages, analysis and findings, the local-only analytics page (first-party click
counter, shipped by session `arena/7cfe23f4-zone4`), the requirements register (rendered from `data/requirements.json`), marketing content
(drafts), platform and automation, brief coverage (the Q-01 to Q-26 trace from `data/content.json`, published as `docs/brief-coverage.html`
so both requirement registers stay published side by side), verification log, re-verification pass, policy compliance, flagged for review, and
sources. All seventeen pages carry the Associates disclosure sentence and the IP License §2(k) content disclaimer in the footer;
`docs/analytics.html` is a static file, so the build does not rewrite it and the shared lines were added to it by hand in this merge.

## Requirements traceability

The Requirements page (`docs/requirements.html`) maps all 30 items in the project brief to one of five statuses
(Delivered, Delivered (partial), Not built - blocked (policy), Not built - needs access, Unverifiable (blank + flagged)),
each with the official source for that status. Blocked rows name the rule that gates them, for example Participation
Requirements Section 6(y), which states that the Site must not have price tracking or price alerting functionality.

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
  flag F-18; a brand page disagrees on one dimension (F-31).
* Deliberately blank: prices, ratings, review counts, commission rate, trend and conversion data — flags F-01, F-02, F-15.

## Limits

* Amazon prices and star ratings are not published. Associates Participation Requirements 2(b) and 6(t) restrict them to Amazon-served links
  or PA-API / Creators API data, and PA-API 5 is now deprecated (F-35).
* Price tracking or price alerting is not built at all: Participation Requirements 6(y) bars it on the Site (F-29).
* The IP License goes further than the Conditions of Use: API content may not be aggregated, analysed, repurposed or used to train a model
  without express prior written approval (rules R-17, R-29, flags F-12, F-34), so the automation stages are documented and gated, not built.
* Marketing copy is published as drafts inside this research site, not as monetised pages: no approved Associates account or tagged Special
  Link is confirmed here (flags F-25, F-31).
* Commission rates are blank; the official schedule sits behind an Amazon sign-in (F-01).
* Attribution to the user's Associates ID is **unverified** (no tag in the resolved links).
* Automated research, AI article generation, price tracking and affiliate click/conversion tracking are **not built**. They are gated by Participation Requirements Sections 5, 6(s) and 6(y), the Conditions of Use AI clause and the IP License Agent Terms. The Requirements page names the blocking rule for each item; see also `data/content.json` (`not_built`) and `data/flags.json`.

Start with `docs/flagged.html` for the items that need a decision.

The site is not endorsed by or affiliated with Amazon. Disclosure, per Associates Operating Agreement Section 5: "As an Amazon Associate I earn from qualifying purchases."
