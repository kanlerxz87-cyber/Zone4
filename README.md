# Zone4 — an air fryer buying-guide publication, built so every number has a receipt

**Live site:** https://kanlerxz87-cyber.github.io/Zone4/

Three countertop air fryers, compared on the fields their own listings print. The site is a
publication first — product cards, guides, a chooser, an RSS feed — and an audit trail second:
a verification log, a source register, a flag register and a decision queue, all reachable from the
footer index on every page.

It never publishes a price, a star rating or a popularity claim: the Associates programme rules
allow those only where Amazon serves the link or an approved API supplies them, and neither is
connected. Where a listing is silent, the page says so.

**Associates tag on every outbound product link:** `shopnow047c-20` — applied 2026-11-17 as
`https://www.amazon.com/dp/<ASIN>?tag=shopnow047c-20` with `rel="sponsored"`. Present on the link is
verifiable here; whether the tag is *enrolled* and whether a click is *credited* are Associates
Central facts and are recorded as unverified (F-03, F-55). No earnings figure or forecast is published.

## Current state (2026-11-17)

| | Count | Where it lives |
|---|---|---|
| Products, each read field by field from its listing | 3 | `data/products.json` |
| Published pieces: 3 reviews, 1 comparison, 5 guides | 9 | `data/marketing.json` |
| Pages in the published site | 29 | `docs/` (generated) |
| Requirements from the brief, one row each | 40 | `data/requirements.json` |
| Irregularities and unverified items recorded (41 still open) | 58 | `data/flags.json` |
| Costed suggestions | 40 | `data/suggestions.json` |
| Questions that gate a decision (24 already answered from a source) | 48 | `data/questions.json` |
| Decisions (30 recorded, the rest open) | 43 | `data/decisions.json` |
| Official sources, each marked read or not read | 32 | `data/sources.json` |
| Associate/FTC rules checked against the site | 30 | `data/policies.json` |
| Findings with their basis and confidence | 18 | `data/content.json` |
| Measurement events defined | 5 | `data/tracking-events.json` |

## How the site is built

**Only `scripts/build_site.py` writes `docs/`.** It reads `data/*.json` and emits every page, the
sitemap, the feed and the robots file. Run it, then check it:

```bash
python3 scripts/build_site.py      # writes docs/ (29 pages + feed.xml + sitemap.xml + robots.txt)
python3 scripts/verify.py          # data, links, anchors, disclosure, per-row sources, feed, tagged links
python3 qa/audit_site.py --strict-warnings
python3 scripts/make_og_image.py   # regenerates docs/og.png; needs Pillow (build-time only)
python3 -m unittest discover -s tests
node tools/node/tracker-smoke.mjs  # the five-event counter: no network call, no personal fields
```

`scripts/verify.py` fails the build on any of these, among others: a table row with no official
source link; a page missing from the footer index; a second primary navigation group; a shop link
without the Associates tag or without `rel="sponsored"`; a feed item with no live page; two pages
sharing a meta description; an Amazon Mark in a title tag or keyword.

The engine under `engine/` is a separate, offline pipeline with its own preview output
(`build/site-preview/`). It never writes `docs/`. See `ENGINE.md`.

## The rules this repository enforces on itself

1. **No value without a source.** A table row must contain a link to the official page that supports
   it, or show an explicit withheld/unverified state. The build fails otherwise.
2. **No inference.** If a listing does not state it, the site does not publish it. A blank is left
   blank and flagged.
3. **No prohibited data.** No prices, star ratings, review counts, price history or popularity
   claims. Each has a cited rule on the policy-compliance page.
4. **Disclosure adjacent to the link.** The Associates sentence sits in the same paragraph as every
   outbound product link, and again under the masthead and in the footer.
5. **Flags do not block publication; they block silence.** Everything unverified is published on the
   Flagged for review page with its source links.

## Documentation index

| Path | Purpose |
|---|---|
| `ENGINE.md` | The automation engine: what it does, what it refuses to do, and its publish gate |
| `DESIGN_PROMPT.md` | A paste-ready design brief generated from `data/design.json` |
| `COORDINATION.md` | The shared task board and the log of every session that has worked here |
| `EXECUTIVE_SUMMARY.md` | The long-form summary (the site's own Executive summary page is the reader version) |
| `qa/README.md` | How the independent QA audit differs from `scripts/verify.py` |

---

## Historical record (kept for the audit trail)

The sections below record the repository as it stood on earlier dates. Counts in them are historical
and are superseded by the table above.

## What is in the repo

| Path | Purpose |
|---|---|
| `data/products.json` | Verified product records (ASIN, brand, manufacturer, model, category, specifications, competitor ASINs) |
| `data/marketing.json` | Marketing content kit: 3 product spec-check articles, 1 comparison page, 3 buying guides (format, sizes, seasonal), SEO rules, publishing checklist |
| `data/pipeline.json` | The automation pipeline, the click/conversion metrics and the Agent Terms |
| `data/requirements.json` | The 35 requirements from the brief, one row each, with what is delivered, what blocks it and the official source |
| `data/sources.json` | Source registry (32 entries): each official source, and whether it was read |
| `data/policies.json` | 30 Amazon Associates and FTC requirements, with status for this site |
| `data/flags.json` | 51 irregularities and unverified items (Flagged for Review) |
| `data/content.json` | Executive summary, 18 analysis findings, category text, and the 2026-11-15 re-check date |
| `data/reverification-2026-11-14.json` | Independent re-verification record of the supplied links and citations |
| `data/verification-session-f87cc71f.json` | Second independent re-verification (2026-11-15): short links, titles, carousels, Table 1, OA Section 5, FTC |
| `data/design.json` | The design brief: three visual directions specified to build from, ten anti-"AI slop" patterns with replacements, two headline options per published article, an eight-topic organic-traffic programme and the five-step shortest path |
| `data/verification-session-89900251.json` | 2026-11-16 verification pass: three short links re-resolved, P1–P3 titles, breadcrumbs and also-viewed carousels re-read, and the Associates, FTC and Google guidance pages quoted verbatim |
| `data/flags.json` | 50 irregularities and unverified items (Flagged for Review) |
| `data/content.json` | Executive summary, 18 analysis findings, category text, and the 2026-11-16 re-check date |
| `data/verification-session-4c552c78.json` | Same-day re-read (2026-11-16) of the three short links, their listing pages, Table 1, the Program Policies, the Operating Agreement and the Conditions of Use; flag F-49 record |
| `data/verification-session-f9f20f21.json` | Re-check of 2026-11-16 (residual scope): all three product pages re-read for the Item details tables (not exposed that day; every exposed value corroborates the record), Table 1 re-read, F-48 resolved against PR #28's diff, flag F-50 found (P2 accessory-count inconsistency) |
| `data/reverification-2026-11-14.json` | Independent re-verification record of the supplied links and citations |
| `data/verification-session-f87cc71f.json` | Second independent re-verification (2026-11-15): short links, titles, carousels, Table 1, OA Section 5, FTC |
| `data/verification-session-c42349c3.json` | Re-check of 2026-11-16: the three supplied links (displayed text and target), the three product pages, the Operating Agreement §5 sentence, the Program Policies date and FTC Disclosures 101. Flags F-47 and F-48 and a dated update to F-44 record what differs |
| `DESIGN_PROMPT.md` | Ready-to-paste redesign brief (suggestion S-14, decision D-20); fills its bracketed slots from the recorded picks |
| `data/verification-session-ebf5c261.json` | Second independent verification session's field-by-field record |
| `data/verification-session-d8564cd0.json` | 2026-11-15 verification pass by `arena/d8564cd0-zone4`: commission table re-read, P1/P2/P3 page reads, flag F-44 record |
| `scripts/build_site.py` | Builds `docs/` from `data/` (standard library only) |
| `scripts/verify.py` | Checks data and built pages; fails on any problem |
| `qa/audit_site.py` | Independent QA audit of the committed HTML, run separately from the builder |
| `scripts/render_design_prompt.py` | Regenerates `DESIGN_PROMPT.md` from `data/design.json`, so the document and the Design brief page are the same brief |
| `engine/` | The automation engine: research intake, claim checking, scoring, economics, links, tracking, policy gates, content and site generation |
| `tests/test_engine.py` | 83 unit tests for the engine |
| `tools/check_links.py` | Link, per-row sourcing, CSS and disclosure check for the engine's preview build |
| `ENGINE.md` | How the engine works, what it refuses to do, and its publish gate |
| `data/suggestions.json` | The change backlog: 31 costed suggestions, each with the problem, proposal, effort, risk, the check that would prove it worked and the official rule that constrains it |
| `data/questions.json` | 37 questions that must be answered before a change can be made: 18 answered (14 from official sources, 4 closed by the 2026-11-16 decisions), 19 still open, each naming what is known, how the missing piece is discovered and who can answer it |
| `data/decisions.json` | The decision queue (34 choices with options, cost and reversibility) and the log of decisions actually taken: 26 recorded on 2026-11-16 under the owner's written delegation, 8 still open |
| `docs/` | The published site (26 generated pages plus the stylesheet, app script and tracker script) |
| `data/suggestions.json` | The change backlog: 36 costed suggestions, each with the problem, proposal, effort, risk, the check that would prove it worked and the official rule that constrains it |
| `data/questions.json` | 44 questions that must be answered before a change can be made: 18 already answered from an official source, 26 still open, each naming what is known, how the missing piece is discovered and who can answer it |
| `data/decisions.json` | The decision queue (39 choices with options, cost and reversibility, also shown in dependency order) and the log of decisions actually taken |
| `docs/` | The published site (25 generated pages plus the stylesheet, app script, tracker script and design-page copy script) |
| `docs/analytics.html` + `docs/tracker.js` | First-party clicks & conversions tracker (local-only, starts at zero, no fabricated data) |
| `EXECUTIVE_SUMMARY.md` | Repository-level executive summary with the full source list |
| `.github/workflows/site-checks.yml` | CI: rebuilds, verifies, and confirms `docs/` is up to date |
| `.github/workflows/qa.yml` | CI: independent QA audit of the committed site |
| `COORDINATION.md` | Shared task board and work log for all sessions |

## Site pages

| Page | What it holds |
|---|---|
| `index.html` | Landing page: marketing hero, trust strip, the three-question chooser, article cards, category tiles, the open-decisions queue, the product table and key findings |
| `executive-summary.html` | Headline findings, decisions needed, and what is not built |
| `requirements.html` | All 35 brief items: delivered, blocked or unverifiable, each with the official source |
| `products.html` | All three products, one row each, every row linked to its source, plus the derived counter-space analysis with its arithmetic shown |
| `categories/*.html` | One page per product format: dual-basket, single-basket, air-fry toaster ovens |
| `marketing.html` | All seven articles on one page, with a fact table per article |
| `articles/index.html` | Articles hub: every article grouped by product format, plus the topic calendar of planned, question-shaped titles |
| `articles/*.html` | One page per article, with its own title tag and meta description, the finished copy, its call to action and the fact table it was written from |
| `automation.html` | Pipeline stages, tracking metrics, optimisation loop and the Agent Terms |
| `analysis.html` | 18 findings with their basis, confidence and source links |
| `verification.html` | Field-by-field verification log for every product |
| `policy-compliance.html` | 30 Amazon Associates and FTC rules, each with its official source section |
| `analytics.html` | Clicks & conversions: a local-only first-party click log, with export and clear |
| `suggestions.html` | Suggestions: 36 changes worth making, costed and risk-assessed, in three priority bands, waiting on a decision rather than already applied |
| `questions.html` | Open questions: 44 items, 18 of them already answered from an official source, the rest with what is known, what is missing and who can supply it |
| `design.html` | Design brief: three specified visual directions with type stacks, colour tokens and component rules; ten anti-"AI slop" patterns with replacements; two headline options per article; eight organic-traffic topics; the five-step shortest credible path; and a paste-ready prompt. Nothing on it has been applied. |
| `decisions.html` | Decision log: the 39 open choices with their options, in the order each unblocks the others, plus the record of decisions taken |
| `flagged.html` | Flagged for Review: 51 irregularities and unverified items, grouped into those needing a decision, those corrected and those resolved |
| `suggestions.html` | Suggestions: 31 changes worth making, costed and risk-assessed, with the recommended path first, the review workflow, and a status chip per item (shipped 2026-11-16, staged, awaiting the owner, or refused by policy) |
| `questions.html` | Open questions: 37 items, 18 answered (official sources or recorded decisions), the rest with what is known, what is missing, who can supply it, and a discovery plan |
| `decisions.html` | Decision log: 26 decisions recorded on 2026-11-16 (each with its recorded choice), 8 open choices with their options, and the log of who recorded what and when |
| `flagged.html` | Flagged for Review: 50 irregularities and unverified items, grouped into those needing a decision, those corrected and those resolved |
| `sources.html` | Every source, whether it was read, and what it was used for |

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

The verifier fails the build if any two pages share a meta description, if a suggestion, question or decision points at a
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
patterns that make the site read as machine output, two headline options per article and the shortest path through the 39 open
decisions, all in one page. Then `suggestions.html` for the costed backlog, `questions.html` for what must be answered before
any of it can be built, `decisions.html` for the choice itself, `flagged.html` for the defects found, and `requirements.html`
for the brief-by-brief delivery status.

Nothing in this repository acts on a suggestion by itself. Every change is proposed, costed and left in the queue until the owner
records a decision. Two things were shipped before they were approved and are flagged accordingly (F-46): the editorial redesign
of `docs/styles.css` and the navigation split, both by `arena/d2a62d6b-zone4` on 2026-11-15. Both are reversible and
presentation-only — no price, rating, review count or commission figure was added and every table row still carries its official
source link — and both sit behind decision D-21 and suggestions S-17 and S-21 pending the owner's sign-off.

The site is not endorsed by or affiliated with Amazon. Disclosure, per Associates Operating Agreement Section 5: "As an Amazon Associate I earn from qualifying purchases."
