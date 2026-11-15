# Design prompt draft — the brief for the visual overhaul

**Status:** proposal, not implemented. Prepared 2026-11-15 by `arena/f87cc71f-zone4` per the brief's request for *"suggestions that will feed into the prompt to design the site"*. Adopted only when decision **D-20** is recorded on the site's [Suggestions](https://kanlerxz87-cyber.github.io/Zone4/docs/suggestions.html) / [Decisions](https://kanlerxz87-cyber.github.io/Zone4/docs/decisions.html) pages.

**How to use:** fill the four bracketed slots from the recorded picks (D-17 topic wave, D-18 visual direction and brand, the S-12 voice decision, D-19 trend rule), then paste the block below to a designer or a design tool. The compliance block is non-negotiable: it encodes Amazon Associates rules, FTC guidance and this repository's own verification discipline.

---

## Prompt

Design a polished affiliate-marketing website for a verified shortlist of three countertop air fryers sold on an online marketplace.

**GOAL.** An engaging, trustworthy marketing site that earns organic search traffic and converts informed readers into buyers through clearly disclosed affiliate links. It must read like a human-edited kitchen-technology publication, never like generated filler.

**BRAND & DIRECTION.** Brand name [D-18 pick]. Visual direction [D-18 pick: warm editorial / crisp data-journalism / bold deal-finder]. Editorial voice [S-12 pick]. Audience and market [Q-16 / Q-04 answers].

**PRODUCTS.** (1) A 6-quart dual-basket air fryer with two independent baskets and a sync-finish feature. (2) A 26-quart French-door air fryer toaster oven with 24 listed cooking functions. (3) An 8-quart single-basket air fryer with a 450-degree high-heat option. Present them by format — dual-basket, single-basket, toaster-oven — because format is the reader's real decision. Every product fact on the site must come from a cited listing field; never invent specifications, prices or ratings.

**REQUIRED PAGES.** A marketing landing page with a story-led hero; one category page per format; a products-at-a-glance comparison table; five long-form articles (three product pieces, one format comparison, one buying guide); a topics hub for the approved content calendar [D-17 pick]; and a governance section (verification log, policy compliance, flagged-for-review, sources, suggestions, questions, decision log) presented with the same design care as the marketing pages.

**TRAFFIC PROGRAM.** SEO-first, people-first. Build the approved topic calendar [D-17 pick: foundational four / full calendar] with catchy, question-shaped headlines and internal links from each topic to the format pages and reviews. Trendy language is allowed only under the adopted evidence rule [D-19 pick]; otherwise write timeless format advice. Target featured-snippet-shaped answers — size tables, checklists, glossaries — without writing for machines.

**COMPLIANCE HARD CONSTRAINTS (non-negotiable; they override any visual idea).**

- The affiliate disclosure sentence appears clearly at the top of every page.
- Do not publish prices, star ratings or review counts unless the authorized API route is approved (F-02).
- Do not use marketplace trademarks in page titles, meta descriptions or target keywords.
- Every table row that states a fact links to the official source it was read from.
- Anything unverified is left blank and visibly flagged, never inferred.
- Make no hands-on performance claims without real testing (FTC endorsement guidance).
- No price tracking and no price alerts (Participation Requirement 6(y)).
- Automated content stays inside the program's agent terms.

**DECISION WORKFLOW.** The site keeps a suggestions register where every change of direction is proposed, costed and risk-assessed, a questions register that separates what is known from what is missing, and a decision queue where the owner records the choice before anything is implemented. Design that review workflow as a first-class part of the product, not an afterthought.

**OUTPUT.** A complete design system (type scale, colour tokens, spacing, card and table components, disclosure component, decision-queue component), page templates for every required page, and two example article mockups built from real verified facts in `data/`. State which compliance constraints shaped each design decision.

---

## Where each bracketed slot comes from

| Slot | Source of truth |
|---|---|
| Brand name, visual direction | Decision **D-18** (suggestion **S-15**), closing flag **F-39** |
| Editorial voice | The **S-12** voice decision (rewrite the five articles once it lands) |
| Topic wave | Decision **D-17** (suggestion **S-13**: foundational four, or all eight) |
| Trend-language rule | Decision **D-19** (suggestion **S-16**) |
| Audience and market | Questions **Q-16** and **Q-04** |

The eight candidate topic titles live in suggestion **S-13** in `data/suggestions.json`; the evidence discipline behind them is flag **F-15** (no trend claim without a dated official snapshot).
