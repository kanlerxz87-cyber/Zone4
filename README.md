# Zone4 — Amazon affiliate product research (verified)

A static research site for three user-supplied Amazon product links. It publishes only values that were checked against an official source. Anything that could not be verified is left blank and flagged.

**Live site (GitHub Pages):** https://kanlerxz87-cyber.github.io/Zone4/

The repository's Pages source is `main` `/` (legacy build). The root `index.html` redirects to `docs/index.html`, and the root `.nojekyll` stops Jekyll processing. Setting the Pages source to `main` `/docs` in Settings would also work; the redirect then becomes unused but harmless.

## What is in the repo

| Path | Purpose |
|---|---|
| `data/products.json` | Verified product records (ASIN, brand, manufacturer, model, category, specifications, competitor ASINs) |
| `data/marketing.json` | Marketing content kit: 3 product articles, 1 comparison page, 1 buying guide, SEO rules, publishing checklist |
| `data/pipeline.json` | The automation pipeline, the click/conversion metrics and the Agent Terms |
| `data/requirements.json` | The 35 requirements from the brief, one row each, with what is delivered, what blocks it and the official source |
| `data/sources.json` | Source registry (32 entries): each official source, and whether it was read |
| `data/policies.json` | 30 Amazon Associates and FTC requirements, with status for this site |
| `data/flags.json` | 46 irregularities and unverified items (Flagged for Review) |
| `data/content.json` | Executive summary, 18 analysis findings, category text, and the 2026-11-16 re-check date |
| `data/verification-session-4c552c78.json` | Same-day re-read (2026-11-16) of the three short links, their listing pages, Table 1, the Program Policies, the Operating Agreement and the Conditions of Use; flag F-47 record |
| `data/reverification-2026-11-14.json` | Independent re-verification record of the supplied links and citations |
| `data/verification-session-f87cc71f.json` | Second independent re-verification (2026-11-15): short links, titles, carousels, Table 1, OA Section 5, FTC |
| `DESIGN_PROMPT.md` | Ready-to-paste redesign brief (suggestion S-14, decision D-20); fills its bracketed slots from the recorded picks |
| `data/verification-session-ebf5c261.json` | Second independent verification session's field-by-field record |
| `data/verification-session-d8564cd0.json` | 2026-11-15 verification pass by `arena/d8564cd0-zone4`: commission table re-read, P1/P2/P3 page reads, flag F-44 record |
| `scripts/build_site.py` | Builds `docs/` from `data/` (standard library only) |
| `scripts/verify.py` | Checks data and built pages; fails on any problem |
| `qa/audit_site.py` | Independent QA audit of the committed HTML, run separately from the builder |
| `engine/` | The automation engine: research intake, claim checking, scoring, economics, links, tracking, policy gates, content and site generation |
| `tests/test_engine.py` | 83 unit tests for the engine |
| `tools/check_links.py` | Link, per-row sourcing, CSS and disclosure check for the engine's preview build |
| `ENGINE.md` | How the engine works, what it refuses to do, and its publish gate |
| `data/suggestions.json` | The change backlog: 31 costed suggestions, each with the problem, proposal, effort, risk, the check that would prove it worked and the official rule that constrains it |
| `data/questions.json` | 37 questions that must be answered before a change can be made: 14 already answered from an official source, 23 still open, each naming what is known, how the missing piece is discovered and who can answer it |
| `data/decisions.json` | The decision queue (34 choices with options, cost and reversibility) and the log of decisions actually taken |
| `docs/` | The published site (24 generated pages plus the stylesheet, app script and tracker script) |
| `docs/analytics.html` + `docs/tracker.js` | First-party clicks & conversions tracker (local-only, starts at zero, no fabricated data) |
| `EXECUTIVE_SUMMARY.md` | Repository-level executive summary with the full source list |
| `.github/workflows/site-checks.yml` | CI: rebuilds, verifies, and confirms `docs/` is up to date |
| `.github/workflows/qa.yml` | CI: independent QA audit of the committed site |
| `COORDINATION.md` | Shared task board and work log for all sessions |

## Site pages

| Page | What it holds |
|---|---|
| `index.html` | Landing page: marketing hero, KPIs, trending-article cards, category tiles, the decision queue, the product table and key findings |
| `executive-summary.html` | Headline findings, decisions needed, and what is not built |
| `requirements.html` | All 35 brief items: delivered, blocked or unverifiable, each with the official source |
| `products.html` | All three products, one row each, every row linked to its source |
| `categories/*.html` | One page per product format: dual-basket, single-basket, air-fry toaster ovens |
| `marketing.html` | The same articles, comparison page and buying guide on one page, with a fact table per article |
| `articles/index.html` | Articles hub: every article, grouped by the product format it covers |
| `articles/*.html` | One page per article, with its own title tag and meta description, the finished copy, its call to action and the fact table it was written from |
| `automation.html` | Pipeline stages, tracking metrics, optimisation loop and the Agent Terms |
| `analysis.html` | 18 findings with their basis, confidence and source links |
| `verification.html` | Field-by-field verification log for every product |
| `policy-compliance.html` | 30 Amazon Associates and FTC rules, each with its official source section |
| `analytics.html` | Clicks & conversions: a local-only first-party click log, with export and clear |
| `suggestions.html` | Suggestions: 31 changes worth making, costed and risk-assessed, in three priority bands, waiting on a decision rather than already applied |
| `questions.html` | Open questions: 37 items, 14 of them already answered from an official source, the rest with what is known, what is missing and who can supply it |
| `decisions.html` | Decision log: the 34 open choices with their options, plus the record of decisions taken |
| `flagged.html` | Flagged for Review: 46 irregularities and unverified items, grouped into those needing a decision, those corrected and those resolved |
| `sources.html` | Every source, whether it was read, and what it was used for |

## Rebuild and verify

```bash
python3 scripts/build_site.py     # regenerate docs/ from data/
python3 scripts/verify.py         # data + page checks
python3 qa/audit_site.py          # independent audit of the committed HTML

python3 -m engine.cli build       # builds the engine preview into build/site-preview (needed by the next line)
python3 -m unittest discover -s tests   # 83 engine tests
python3 -m engine.cli status            # what is verified, withheld or blocked
python3 -m engine.cli audit             # compliance gate on the engine's drafts
python3 tools/check_links.py            # link and per-row sourcing check
```

The engine is offline by default: with no OAuth credentials it raises rather than returning stand-in data, and its network probe path degrades to
`BLOCKED` so that "Amazon has no such page" stays distinct from "this environment cannot reach the network". Any request it does make identifies itself
as `Agent/zone4-research`, as the Agent Terms in IP License Section 4(c) require.

The verifier fails the build if any two pages share a meta description, if a suggestion, question or decision points at a
record that does not exist, if a recorded decision is missing from the log, if any table row lacks a link to an official source, if a link or anchor is broken, if the required disclosure is missing from a page, if a price or star rating appears, if an Amazon Mark is used as a page title, meta description or target keyword, if a marketing fact row is never cited by a paragraph, or if a requirement row has an undeclared status, no source, or no evidence for its status. The QA audit re-checks the committed HTML on its own, so a hand-edit or a stale commit is caught too.

## Limits

- Amazon prices and star ratings are **not published**. Associates Participation Requirements 2(b) and 6(t) restrict them to Amazon-served links or Creators API / PA API data.
- The [public Standard Commission Income Statement, Table 1](https://affiliate-program.amazon.com/help/node/topic/GRXPHT8U84RAYDXZ) lists the Kitchen category at **4.50%**. This is a category-level reference only: the commission category Amazon assigns to each supplied ASIN is not confirmed from the official sources reviewed, so all product-level rate cells are blank and flagged (F-01). No product-level earnings estimate is published.
- Attribution to the user's Associates ID is **unverified** (no tag in the resolved links).
- Attributed click, order, revenue and trend metrics are **blank**. No Associates reporting, API key or account is connected, so nothing is simulated. The Analytics page records first-party clicks in the visitor's own browser and publishes no attributed figure.
- Automated research at scale is **not built**. The Associates Program IP License, Section 4 (Agent Terms) governs any agent that touches Program Content.
- Price tracking and price alerting are **not built**: Participation Requirement 6(y) prohibits them unless Amazon agrees otherwise.

Start with `suggestions.html` on the live site for the costed backlog, `questions.html` for what must be answered before any of
it can be built, `decisions.html` for the choice itself, `flagged.html` for the defects found, and `requirements.html` for the
brief-by-brief delivery status.

Nothing in this repository acts on a suggestion by itself. Every change is proposed, costed and left in the queue until the owner
records a decision. Two things were shipped before they were approved and are flagged accordingly (F-46): the editorial redesign
of `docs/styles.css` and the navigation split, both by `arena/d2a62d6b-zone4` on 2026-11-15. Both are reversible and
presentation-only — no price, rating, review count or commission figure was added and every table row still carries its official
source link — and both sit behind decision D-21 and suggestions S-17 and S-21 pending the owner's sign-off.

The site is not endorsed by or affiliated with Amazon. Disclosure, per Associates Operating Agreement Section 5: "As an Amazon Associate I earn from qualifying purchases."
