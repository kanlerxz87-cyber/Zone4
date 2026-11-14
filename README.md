# Zone4 — Amazon affiliate product research (verified)

A static research site for three user-supplied Amazon product links. It publishes only values that were checked against an official source. Anything that could not be verified is left blank and flagged.

**Live site (GitHub Pages, from `main` `/docs`):** https://kanlerxz87-cyber.github.io/Zone4/

## What is in the repo

| Path | Purpose |
|---|---|
| `data/products.json` | Verified product records (ASIN, brand, category, specifications, competitor ASINs) |
| `data/sources.json` | Source registry: each official source, and whether it was read |
| `data/policies.json` | Amazon Associates and FTC requirements, with status for this site |
| `data/flags.json` | Irregularities and unverified items (Flagged for Review) |
| `data/content.json` | Executive summary, analysis findings, category text |
| `scripts/build_site.py` | Builds `docs/` from `data/` (standard library only) |
| `scripts/verify.py` | Checks data and built pages; fails on any problem |
| `docs/` | The published site |
| `.github/workflows/site-checks.yml` | CI: rebuilds, verifies, and confirms `docs/` is up to date |
| `COORDINATION.md` | Shared task board and work log for all sessions |

## Rebuild and verify

```bash
python3 scripts/build_site.py
python3 scripts/verify.py
```

## Pages

GitHub Pages is a legacy build of `main` `/` (the repository's Pages source). The root `index.html` redirects to `docs/index.html`, and the root `.nojekyll` stops Jekyll processing. `scripts/verify.py` fails if the redirect is missing. Switching the Pages source to `main` `/docs` in Settings would also work; the redirect then becomes unused but harmless. Every push to `main` rebuilds the site.

## Limits

- Amazon prices and star ratings are **not published**. Associates Participation Requirements 2(b) and 3(t) restrict them to Amazon-served links or PA-API / Creators API data.
- Commission rates are **blank** (the official schedule is behind an Amazon sign-in).
- Attribution to the user's Associates ID is **unverified** (no tag in the resolved links).
- Automated research, AI article generation and click tracking are **not built**. See `data/content.json` (`not_built`) and `data/flags.json`.

Start with `flagged.html` on the live site for the items that need your decision.

The site is not endorsed by or affiliated with Amazon. Disclosure, per Associates Operating Agreement Section 5: "As an Amazon Associate I earn from qualifying purchases."
