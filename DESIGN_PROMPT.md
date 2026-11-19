# Design prompt — the brief for the visual overhaul

**Status:** adopted and partly applied. Generated from `data/design.json` by
`scripts/render_design_prompt.py`; do not edit by hand, edit the data and re-run the script.
Last generated 2026-11-19 by `arena/d7393cc0-zone4`.

**How to use:** fill the seven bracketed slots from the recorded decisions, then paste the block
below to a designer or a design tool. The slot table at the end names the decision that fills each
one. The compliance block is non-negotiable: it encodes Amazon Associates rules, FTC guidance and
this repository's own verification discipline.

**The three directions in the `[DIRECTION]` slot are fully specified on the**
[Design brief page](https://kanlerxz87-cyber.github.io/Zone4/docs/design.html)**, and each row of
the topic programme and the anti-pattern list below is expanded there with its evidence and its
source. This document is the paste-ready form of the same data.**

---

## Prompt

```
Design a polished affiliate-marketing website for three countertop air fryers
whose every published figure is checked against an official source.

GOAL. A site that earns organic search traffic and converts informed readers
through clearly disclosed affiliate links, and that reads like a human-edited
kitchen-technology publication. It must not read like generated filler.

BRAND & DIRECTION. Brand [BRAND]. Visual direction [DIRECTION].
Editorial voice [VOICE]. Audience and market [AUDIENCE].

DIRECTION OPTIONS (pick one; each is fully specified on the Design brief page):
  - DIR-A Warm editorial (D-18 option A): A kitchen magazine that happens to show its sources.
    Display type: Fraunces (optical size 96, soft), fallback: Georgia, 'Iowan Old Style', 'Palatino Linotype', serif
    Body type: Inter 17px / 1.65, fallback: system-ui, sans-serif
    Palette: ink #241C17, paper #FBF7F1, terracotta #C4613C, sage #6F7F63, rule #E7DDD1, muted #6B6058
    Hero: Paper background, no photography tint. One-line promise (max 9 words), one-line method statement, two calls to action side by side, one product image right-aligned at 40% width. No badge strip, no counters.
    Disclosure: A one-line strip directly above the article headline, ink on paper, 15px, carrying the Operating Agreement sentence verbatim and a link to Section 5. On desktop it repeats as a 40px sticky sub-header once the article headline scrolls past. It is never placed inside a list of links or a group of hashtags.
  - DIR-B Crisp data-journalism (D-18 option B): The receipts are the design.
    Display type: Newsreader (optical size 48), fallback: 'Source Serif 4', Georgia, serif
    Body type: 'IBM Plex Sans' 16px / 1.6, fallback: system-ui, sans-serif
    Palette: ink #12161B, paper #FFFFFF, signal_blue #1B57C4, verified_green #17734B, rule #D8DEE5, muted #5A6572
    Hero: No photograph. A headline, a one-line method statement ('Every figure on this page links to the page it was read from'), and a compact strip of three derived counts. The hero is the argument, not the mood.
    Disclosure: A full-width bar pinned above the masthead, ink on white, with a check glyph, the Operating Agreement sentence verbatim and the Section 5 link. It stays visible for the whole session, not just at the top of the page. Never collapsed behind a 'more' control.
  - DIR-C Bold deal-finder, evidence-only (D-18 option C): Big verdicts, big badges, and nothing a price would normally carry.
    Display type: Archivo Black for badges and verdict tiles; Archivo SemiBold for headlines, fallback: 'Helvetica Neue', Arial, sans-serif
    Body type: Inter 16px / 1.6, fallback: system-ui, sans-serif
    Palette: ink #0B0B0B, paper #FFFFFF, accent_yellow #FFD166, verdict_green #0E7C4A, alert_red #C1121F, rule #E5E5E5
    Hero: Black field, yellow call to action, three 'best for' tiles immediately beneath, each with a one-line reason drawn from a listed field. The method statement sits below the tiles, not above them.
    Disclosure: A full-width black bar with white type directly beneath the masthead and again immediately above every call-to-action cluster. It must be the loudest element on the page: 16px, weight 600, never smaller than the badge type beside it.
    Constrained by flags: F-02, F-15, F-22

PRODUCTS. (1) A 6-quart dual-basket air fryer with two independent 3-quart
baskets and a listed Sync Finish feature. (2) A 26QT French-door air fryer
toaster oven whose listing states two different cooking-function counts.
(3) An 8-quart single-basket air fryer with a 450F high-heat option, part of a
6/8/9-quart variant family. Present them by format - dual-basket,
single-basket, toaster-oven - because format is the reader's real decision.
Every product fact must come from a cited listing field; never invent a
specification, a price, a rating or a review count.

REQUIRED PAGES. A marketing landing page with a story-led hero; one category
page per format; a products-at-a-glance comparison table; five long-form
articles (three reviews, one format comparison, one buying guide); a topics hub
for the approved content calendar [TOPICS]; and a governance section
(verification log, policy compliance, flagged for review, sources, suggestions,
questions, decision log) designed with the same care as the marketing pages.

HEADLINES. Use register [HEADLINES]. A headline names the reader's decision or a
number the page can prove. Never let a headline describe the site's own checking
process, and never repeat one construction across several articles - that is the
single clearest signal that a page was generated rather than written.

TRAFFIC PROGRAMME. SEO-first and people-first. Build the approved topic calendar
[TOPICS] with question-shaped headlines and internal links from every topic to
the format pages and the reviews. Trendy language is allowed only under the
evidence rule [TREND_RULE], which requires a dated official snapshot behind every
popularity claim; otherwise write timeless format advice. Target
featured-snippet-shaped answers - size tables, checklists, glossaries - without
writing for machines.

ANTI-PATTERNS. Do not ship any of these; each is a documented defect on the
current site:
  - AS-01: The headline advertises the site's process instead of the reader's payoff -> Headline names the decision or the number; the method moves to a one-line 'how we checked' note under the byline and to the fact table, where it already is.
  - AS-02: Reader-irrelevant apparatus in the opening paragraphs -> Open on the reader's problem. Move the ASIN and the category path into the fact table and the evidence rail, where they are already sourced and where the reader who wants them looks.
  - AS-03: Articles that describe writing the article -> Open with a specific, checkable fact or a concrete kitchen situation. If the writing really is simple, show it by being simple.
  - AS-04: Hedging at the end of paragraphs -> One honesty paragraph per article, in a fixed position, stating what could not be verified. Every other paragraph states its claim flatly and carries its source.
  - AS-05: A comparison page that refuses to compare -> Rank on attributes the listings actually state: largest listed capacity, shallowest listed counter depth, most listed presets, fewest baskets. Say which field decides each row and link it.
  - AS-06: No author, no method statement, no answer to 'who wrote this' -> A named editorial standard instead of a fake individual: one 'how this site checks a figure' page, linked from every article's byline line, plus a stated review date per article.
  - AS-07: No statement about how the content was produced -> One sentence on the method page: what is written by hand, what is generated and then checked, and what is never published without an official source.
  - AS-08: Governance apparatus in the shop window -> Hero carries one promise and two calls to action. The decision queue, the flag counts and the verification log stay one click away and are labelled as governance, which is what they are.
  - AS-09: Prose that restates the table above it -> The paragraph says what the numbers mean for a kitchen; the table says what the numbers are. If a paragraph has no fact id it is not allowed to state a fact, and if it only restates one it is deleted.
  - AS-10: Uniform paragraph length and sentence rhythm across every piece -> Vary deliberately during the rewrite: at least one paragraph of one sentence in every article, and at least one of eight sentences.

COMPLIANCE HARD CONSTRAINTS (non-negotiable; they override any visual idea).
  - The affiliate disclosure sentence appears clearly at the top of every page,
    placed with the endorsement, never behind a click and never inside a group
    of links or hashtags.
  - Do not publish prices, star ratings or review counts unless the approved API
    route is in place.
  - Do not use marketplace trademarks in page titles, meta descriptions or
    target keywords.
  - Every table row that states a fact links to the official source it was read
    from. Anything unverified is left blank and visibly flagged, never inferred.
  - Make no hands-on performance claim without real testing, and claim no
    experience with a product nobody here has used.
  - No price tracking and no price alerts.
  - No traffic, click, conversion or revenue figure may appear anywhere: no
    official source supplies one for these products.

DECISION WORKFLOW. Design the review workflow as a first-class part of the
product: a suggestions register where every change is proposed, costed and
risk-assessed, a questions register that separates what is known from what is
missing, and a decision queue in dependency order that the owner works through
before anything is implemented.

OUTPUT. A complete design system (type scale, colour tokens, spacing, card and
table components, disclosure component, decision-queue component), page
templates for every required page, and two example article mockups built from
real verified facts. State which compliance constraint shaped each design
decision.
```

---

## Where each bracketed slot comes from

| Slot | Filled from | Current value |
|---|---|---|
| `[DIRECTION]` | D-18 (direction family) and D-35 (the specification to build from) | Warm editorial (DIR-A), adopted 2026-11-17 (D-35); the token and component list on the Design brief page is the specification. The safe presentation layer is applied to the storefront and articles (D-47, 2026-11-19); the full direction stays a build reference. |
| `[BRAND]` | D-18 and Q-19 (trade-name clearance) | Zone4 - air fryer buying guides (recorded 2026-11-16, D-18). |
| `[VOICE]` | D-12 and the S-12 voice decision | Warm, plain, decision-first (recorded 2026-11-16, D-12), now with the shop-not-audit rule: reader surfaces lead with the products and the questions a buyer asks; the verification machinery lives in one dashboard group and the footer, never in the headline. |
| `[TOPICS]` | D-17 (which wave) | The ten-topic question calendar (D-17; extended to the two published thermometer listings as Wave 3 by D-50 on 2026-11-19) on the front-page roadmap and the Articles hub, one guide per 14 days to sitemap and feed (cadence set 2026-11-17). |
| `[HEADLINES]` | D-37 (steady or punchy register) | Steady register as published (D-37 recorded 2026-11-17); punchy variants on the Design brief page stay parked behind D-12. |
| `[TREND_RULE]` | D-19 (the evidence rule for popularity words) | Popularity claims only as dated snapshots of an official page (D-19); no traffic, revenue or search-volume figure anywhere (F-15, F-51). |
| `[AUDIENCE]` | Q-16 and Q-04 | still open (Q-16 and Q-04) |

The adopted DIR-A presentation layer is applied to the storefront and articles (2026-11-19,
decision D-47): the publication masthead, the DIR-A palette and typography, the editorial card
system, mono listing figures, the paper hero, the sticky disclosure component and the 'how we
checked' byline link. The three directions, the anti-pattern list and the topic programme stay
proposals until each is individually recorded and built. Each slot is a decision recorded on the
[Decision log](https://kanlerxz87-cyber.github.io/Zone4/docs/decisions.html) page; until one is
recorded the bracket stays, because guessing at a brand name or a voice is exactly the kind of
invention this site refuses to publish.

The eight candidate topic titles and their evidence notes live in `data/design.json` under
`topics`; the evidence discipline behind them is flag **F-15** (no trend claim without a dated
official snapshot) and **F-51** (the brief's "trendy topics and traffic" ask measured against the
guidance the site already cites).
