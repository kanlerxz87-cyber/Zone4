# Zone4 — Amazon affiliate product research (verified)

A static research site for three user-supplied Amazon product links. It publishes only values that were checked against an official source. Anything that could not be verified is left blank and flagged.

Which generator produces the live pages: **only** `scripts/build_site.py` writes `docs/` (the published site). The engine under `engine/` renders its own separate preview into `build/site-preview/` and never writes `docs/`; see ENGINE.md, "Relationship to the published site". `tools/check_links.py` checks that engine preview and fails on a clean checkout until `python3 -m engine.cli build` has created it.

**Live site (GitHub Pages):** https://kanlerxz87-cyber.github.io/Zone4/

The repository's Pages source is `main` `/` (legacy build). The root `index.html` redirects to `docs/index.html`, and the root `.nojekyll` stops Jekyll processing. Setting the Pages source to `main` `/docs` in Settings would also work; the redirect then becomes unused but harmless.

## What is in the repo

| Path | Purpose |
|---|---|
| `data/products.json` | Verified product records (ASIN, brand, manufacturer, model, category, specifications, competitor ASINs) and, since 2026-11-17, the product-intent confirmation record: intended ASIN, listing URL, confirmation date and source kept apart from the dated observed-redirect targets (F-55) |
| `data/marketing.json` | Marketing content kit: 8 published pieces (three product spec checks, one comparison, four buying guides), SEO rules, the publishing cadence and the publishing checklist |
| `data/pipeline.json` | The automation pipeline, the click/conversion metrics, the five defined events (EV-1..EV-5), the analytics endpoint contract and the campaign-ledger specification |
| `data/campaign-ledger.json` | The campaign ledger: defined columns and a provenance rule, zero rows. Rows arrive only from authorized first-party reports; no conversion score or revenue forecast exists (Q-48) |
| `data/requirements.json` | The 35 requirements from the brief, one row each, with what is delivered, what blocks it and the official source |
| `data/sources.json` | Source registry: each official source, and whether it was read |
| `data/policies.json` | 30 Amazon Associates and FTC requirements, with status for this site |
| `data/flags.json` | 56 irregularities and unverified items (Flagged for Review) |
| `data/content.json` | Executive summary, 18 analysis findings, category text, and the 2026-11-17 re-check date |
| `data/suggestions.json` | The change backlog: 41 costed suggestions, each with the problem, proposal, effort, risk, the check that would prove it worked, the decision it sits behind and the official rule that constrains it |
| `data/questions.json` | 48 questions that must be answered before a change can be made: 22 answered from an official source or a recorded decision, the rest with what is known, how the missing piece is discovered and who can supply it |
| `data/decisions.json` | The decision queue (42 choices with options, cost and reversibility, also shown in dependency order) and the log of decisions actually taken: 30 recorded, 12 open |
| `data/design.json` | The design brief: three visual directions specified to build from, ten anti-"AI slop" patterns with replacements, two headline options per published article, an eight-topic organic-traffic programme and the five-step shortest path |
| `data/verification-session-*.json`, `data/reverification-2026-11-14.json` | One field-by-field record per verification session (the newest is `data/verification-session-cc32105d.json`, 2026-11-17) |
| `scripts/build_site.py` | Builds `docs/` from `data/` (standard library only), including `sitemap.xml`, `robots.txt` and the RSS `feed.xml` |
| `scripts/verify.py` | Checks data and built pages; fails on any problem (including the feed, the five events, the empty ledger, the product-intent record and the disclosure's masthead + footer placement) |
| `qa/audit_site.py` | Independent QA audit of the committed HTML, run separately from the builder |
| `scripts/render_design_prompt.py` | Regenerates `DESIGN_PROMPT.md` from `data/design.json`, so the document and the Design brief page are the same brief |
| `engine/` | The automation engine: research intake, claim checking, scoring, economics, links, tracking, policy gates, content and site generation |
| `tests/test_engine.py` | 83 unit tests for the engine |
| `tools/check_links.py` | Link, per-row sourcing, CSS and disclosure check for the engine's preview build |
| `ENGINE.md` | How the engine works, what it refuses to do, and its publish gate |
| `docs/` | The published site (28 generated pages plus the stylesheet, app script, tracker script, design-page script, sitemap, robots.txt and feed.xml) |
| `docs/analytics.html` + `docs/tracker.js` | First-party click counter for the five defined events (local-only by default, starts at zero, no fabricated data); the tracker loads on every page |
| `EXECUTIVE_SUMMARY.md` | Repository-level executive summary with the full source list |
| `DESIGN_PROMPT.md` | Ready-to-paste redesign brief (suggestion S-14, decision D-20); regenerated from `data/design.json` |
| `.github/workflows/site-checks.yml` | CI: rebuilds, verifies, and confirms `docs/` is up to date |
| `.github/workflows/qa.yml` | CI: independent QA audit of the committed site |
| `COORDINATION.md` | Shared task board and work log for all sessions |

## Site pages

| Page | What it holds |
|---|---|
| `index.html` | Publication front page: marketing hero, trust strip, the three-question chooser, featured guides, category tiles, the product table and key findings - products before process, with every dashboard surface in one navigation group and the footer directory |
| `executive-summary.html` | Headline findings, decisions needed, and what is not built |
| `requirements.html` | All 35 brief items: delivered, blocked or unverifiable, each with the official source |
| `products.html` | All three products, one row each, every row linked to its source, the derived counter-space analysis with its arithmetic shown, and the product-intent confirmation record (intent and observed redirects, never merged) |
| `categories/*.html` | One page per product format: dual-basket, single-basket, air-fry toaster ovens |
| `marketing.html` | All 8 pieces on one page, with a fact table per article |
| `articles/index.html` | Articles hub: every article grouped by product format, plus the topic calendar of question-shaped titles with their status |
| `articles/*.html` | One page per article, with its own title tag and meta description, the finished copy, its call to action, the fact table it was written from and the standing "Where next" block |
| `automation.html` | Pipeline stages, tracking metrics, optimisation loop and the Agent Terms |
| `analysis.html` | 18 findings with their basis, confidence and source links |
| `verification.html` | Field-by-field verification log for every product |
| `policy-compliance.html` | 30 Amazon Associates and FTC rules, each with its official source section |
| `analytics.html` | The five defined events, the empty campaign ledger and the endpoint contract, above the local-only click log with export and clear |
| `suggestions.html` | Suggestions: 41 changes worth making, costed and risk-assessed, with the recommended path first, the review workflow, and a status chip per item |
| `questions.html` | Open questions: 48 items, 22 answered, the rest with what is known, what is missing, who can supply it, and a discovery plan |
| `design.html` | Design brief: three specified visual directions, ten anti-"AI slop" patterns, two headline options per article, eight organic-traffic topics, the shortest credible path and a paste-ready prompt |
| `decisions.html` | Decision log: the open choices with their options in dependency order, plus the record of decisions taken |
| `flagged.html` | Flagged for Review: 56 irregularities and unverified items, grouped into those needing a decision, those corrected and those resolved |
| `sources.html` | Every source, whether it was read, and what it was used for |
| `feed.xml` | The RSS feed: one item per published guide, regenerated whenever a guide is added |

## Rebuild and verify

```bash
python3 scripts/build_site.py        # regenerate docs/ from data/
python3 scripts/render_design_prompt.py   # regenerate DESIGN_PROMPT.md from data/design.json
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

The verifier fails the build if any two pages share a meta description, if the RSS feed and the article set disagree, if a product's intent record is missing or merges the observed redirects into the intended ASIN, if the campaign ledger has a row without an authorized report behind it, if the disclosure is missing from a page or appears only once (it belongs under the masthead and in the footer), if a suggestion, question or decision points at a
record that does not exist, if a recorded decision is missing from the log, if any table row lacks a link to an official source, if a link or anchor is broken, if the required disclosure is missing from a page, if a price or star rating appears, if an Amazon Mark is used as a page title, meta description or target keyword, if a marketing fact row is never cited by a paragraph, or if a requirement row has an undeclared status, no source, or no evidence for its status. The QA audit re-checks the committed HTML on its own, so a hand-edit or a stale commit is caught too.

## Limits

- Amazon prices and star ratings are **not published**. Associates Participation Requirements 2(b) and 6(t) restrict them to Amazon-served links or Creators API / PA API data.
- The [public Standard Commission Income Statement, Table 1](https://affiliate-program.amazon.com/help/node/topic/GRXPHT8U84RAYDXZ) lists the Kitchen category at **4.50%**. This is a category-level reference only: the commission category Amazon assigns to each supplied ASIN is not confirmed from the official sources reviewed, so all product-level rate cells are blank and flagged (F-01). No product-level earnings estimate is published.
- Attribution to the user's Associates ID is **unverified** (no tag in the resolved links).
- Attributed click, order, revenue and trend metrics are **blank**. No Associates reporting, API key or account is connected, so nothing is simulated. The Analytics page records first-party clicks in the visitor's own browser and publishes no attributed figure.
- Automated research at scale is **not built**. The Associates Program IP License, Section 4 (Agent Terms) governs any agent that touches Program Content.
- No traffic, search-volume, click, conversion or revenue figure is published **anywhere**, including on the Design brief page. No official source supplies one for these products (F-15), the Operating Agreement Section 4 states that Amazon makes no representation about the traffic or commission income any site can expect, and Google lists trend-chasing as a warning sign of search-engine-first content. That tension is recorded as F-51 rather than resolved by a forecast.
- Price tracking and price alerting are **not built**: Participation Requirement 6(y) prohibits them unless Amazon agrees otherwise.

Start with `design.html` if you want the look-and-copy answers: it holds the three specified directions, the ten writing
patterns that make the site read as machine output, two headline options per article and the shortest path through the 12 open
decisions, all in one page. Then `suggestions.html` for the costed backlog, `questions.html` for what must be answered before
any of it can be built, `decisions.html` for the choice itself, `flagged.html` for the defects found, and `requirements.html`
for the brief-by-brief delivery status.

Nothing in this repository acts on a suggestion by itself. Every change is proposed, costed and left in the queue until the owner
records a decision. Two things were shipped before they were approved and are flagged accordingly (F-46): the editorial redesign
of `docs/styles.css` and the navigation split, both by `arena/d2a62d6b-zone4` on 2026-11-15. Both are reversible and
presentation-only — no price, rating, review count or commission figure was added and every table row still carries its official
source link — and both sit behind decision D-21 and suggestions S-17 and S-21 pending the owner's sign-off.

The site is not endorsed by or affiliated with Amazon. Disclosure, per Associates Operating Agreement Section 5: "As an Amazon Associate I earn from qualifying purchases."
