# MarketPilot — Amazon Affiliate Research Desk

A static GitHub Pages dashboard prototype for evidence-led affiliate product research. It organizes supplied product URLs, summarizes research gaps and surfaces unverified items instead of inventing product attributes or performance claims.

## Pages
- **Overview** — high-level research status and submitted product table.
- **Product research** — structured catalog with unverified fields intentionally blank.
- **Executive summary** — mandate, evidence status, recommendations and compliance guardrails.
- **Flagged for Review** — source links and unresolved items.

## Run locally
Open `index.html` in a browser. The site has no build-time dependencies or backend. GitHub Actions validates in-page links and deploys the static site to GitHub Pages when changes reach `main` (Pages must be enabled with GitHub Actions in repository settings).

## Evidence limits
Product identity, prices, categories, ratings, commissions, trends, competition and conversion performance were not independently confirmed. The supplied `link.amazon` URLs are reproduced verbatim; their destination and validity remain unverified. No Amazon API, affiliate account, analytics or publishing service is connected. See the site's **Flagged for Review** page and `COORDINATION.md` for the verification log.
