# Northstar — source-led affiliate research dashboard

A lightweight, static GitHub Pages site for organizing affiliate product research with an evidence-first policy. It includes an overview dashboard, product evidence ledger, strategy and policy summary, and a flagged-for-review page.

## Run locally

Open `index.html` in a browser, or serve the repository root with any static web server. No build step or dependencies are required.

## Publish on GitHub Pages

The workflow in `.github/workflows/pages.yml` deploys the repository root when changes are pushed to `main` or via manual workflow dispatch. In repository settings, configure Pages to use **GitHub Actions**. Deployment cannot be confirmed until that workflow runs in the target repository.

## Research limitations

The three supplied references are listed in `products.html`. Product identity, current product details, pricing, ratings, reviews, demand, competition, commission, and affiliate-link status are intentionally blank because they were not confirmed from official product or Associates sources. See `flagged.html` for unresolved items and `insights.html` for linked official policy sources. No live Amazon APIs, tracking, publishing, or conversion analytics have been implemented; the site does not imply otherwise.

Amazon Associates policies: https://affiliate-program.amazon.com/help/operating/policies

FTC Endorsement Guides FAQ: https://www.ftc.gov/business-guidance/resources/ftcs-endorsement-guides-what-people-are-asking
