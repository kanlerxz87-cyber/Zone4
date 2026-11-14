# Zone4 — Amazon affiliate product research (verified)

A static research site for three user-supplied Amazon product links. It publishes only values that were checked against an official source. Anything that could not be verified is left blank and flagged.

**Live site (GitHub Pages, `main` branch; the root redirects to `docs/`):** https://kanlerxz87-cyber.github.io/Zone4/

## What is in the repo

| Path | Purpose |
|---|---|
| `data/products.json` | Verified product records (ASIN, brand, category, specifications, competitor ASINs) |
| `data/requirements.json` | Every requirement in the project brief, with its delivery status and the official source for that status |
| `data/sources.json` | Source registry: each official source, and whether it was read |
| `data/policies.json` | Amazon Associates and FTC requirements, with status for this site |
| `data/flags.json` | Irregularities and unverified items (Flagged for Review) |
| `data/content.json` | Executive summary, analysis findings, category text |
| `data/reverification-2026-11-14.json` | Independent re-verification record of the supplied links and citations (2026-11-14), with the integration correction note |
| `scripts/build_site.py` | Builds `docs/` from `data/` (standard library only) |
| `scripts/verify.py` | Checks data and built pages; fails on any problem |
| `docs/` | The published site |
| `docs/analytics.html` + `docs/tracker.js` | First-party clicks & conversions tracker (local-only, starts at zero, no fabricated data) |
| `EXECUTIVE_SUMMARY.md` | Repository-level executive summary with the full source list |
| `.github/workflows/site-checks.yml` | CI: rebuilds, verifies, and confirms `docs/` is up to date |
| `COORDINATION.md` | Shared task board and work log for all sessions |

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

## Pages

GitHub Pages is a legacy build of `main` `/` (the repository's Pages source). The root `index.html` redirects to `docs/index.html`, and the root `.nojekyll` stops Jekyll processing. `scripts/verify.py` fails if the redirect is missing. Switching the Pages source to `main` `/docs` in Settings would also work; the redirect then becomes unused but harmless. Every push to `main` rebuilds the site.

## Limits

- Amazon prices and star ratings are **not published**. Associates Participation Requirements 2(b) and 6(t) restrict them to Amazon-served links or PA-API / Creators API data.
- Commission rates are **blank** (the official schedule is behind an Amazon sign-in).
- Attribution to the user's Associates ID is **unverified** (no tag in the resolved links).
- Automated research, AI article generation, price tracking and affiliate click/conversion tracking are **not built**. They are gated by Participation Requirements Sections 5, 6(s) and 6(y), the Conditions of Use AI clause and the IP License Agent Terms. The Requirements page names the blocking rule for each item; see also `data/content.json` (`not_built`) and `data/flags.json`.

Start with `flagged.html` on the live site for the items that need your decision.

The site is not endorsed by or affiliated with Amazon. Disclosure, per Associates Operating Agreement Section 5: "As an Amazon Associate I earn from qualifying purchases."
