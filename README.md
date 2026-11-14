# Zone4 — Amazon affiliate product research (verified)

A static research site for three user-supplied Amazon product links. It publishes only values that were checked against an official source. Anything that could not be verified is left blank and flagged.

**Live site (GitHub Pages, `main` branch; the root redirects to `docs/`):** https://kanlerxz87-cyber.github.io/Zone4/

## What is in the repo

| Path | Purpose |
|---|---|
| `data/products.json` | Verified product records (ASIN, brand, category, specifications, competitor ASINs) |
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
| `engine/` | Automation layer: verification, economics, scoring, drafting, link safety, tracking, compliance gates |
| `data/engine-*.json` | The engine's own sources, program facts and verification ledger (kept separate from the site data) |
| `data/reverification-2026-11-14.json` | Independent re-verification log of the three links and the citations |
| `tests/test_engine.py` | 73 stdlib tests, including guards that `docs/` stays buildable and verifiable |
| `tools/check_links.py` | Site integrity checker for the engine's preview build |
| `.github/workflows/ci.yml` | CI: runs both pipelines (engine and published site) |

## Rebuild and verify

```bash
python3 scripts/build_site.py
python3 scripts/verify.py
git diff --exit-code -- docs    # the build must be deterministic

python3 -m unittest discover -s tests   # engine + integration guards
python3 -m engine.cli build             # writes the gitignored preview in build/site-preview
python3 tools/check_links.py            # checks that preview
```

To read a fact or a rate the engine has already verified, without building anything:

```bash
python3 -m engine.cli status
python3 -m engine.cli rates --category Kitchen
python3 -m engine.cli audit --strict
```

## Pages

GitHub Pages is a legacy build of `main` `/` (the repository's Pages source). The root `index.html` redirects to `docs/index.html`, and the root `.nojekyll` stops Jekyll processing. `scripts/verify.py` fails if the redirect is missing. Switching the Pages source to `main` `/docs` in Settings would also work; the redirect then becomes unused but harmless. Every push to `main` rebuilds the site.

## Limits

- Amazon prices and star ratings are **not published**. Associates Participation Requirements 2(b) and 6(t) restrict them to Amazon-served links or PA-API / Creators API data.
- Commission rates are **published from the official rate table**: 4.50% is the Standard Commission Income Statement value for the Kitchen band ([source](https://affiliate-program.amazon.com/help/node/topic/GRXPHT8U84RAYDXZ)), recorded on each product row. Which band Amazon applies to a given ASIN is still open (F-01): the breadcrumb top node *Home & Kitchen* straddles the Kitchen (4.50%) and Home (3.00%) rows, and the account's report is the authority. No earning figure is derived, because prices are withheld and no traffic is measured.
- Attribution to the user's Associates ID is **unverified** (no tag in the resolved links).
- Automated research, AI article generation and click tracking are **implemented in `engine/` but publish nothing**: each refuses to emit a value it cannot cite, so the site shows blanks rather than modelled output. See `ENGINE.md` and `data/content.json` (`not_built`).

Start with `flagged.html` on the live site for the items that need your decision.

The site is not endorsed by or affiliated with Amazon. Disclosure, per Associates Operating Agreement Section 5: "As an Amazon Associate I earn from qualifying purchases."
