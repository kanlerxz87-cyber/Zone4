# Design prompt — the brief for the visual overhaul (final, adopted)

**Status:** adopted as the working brief on 2026-11-16 by decision **D-20** (recorded under the owner's written delegation for that session). The bracketed slots are filled from the recorded picks. The design itself was implemented in the same session (decisions **D-18**, **D-21**); this document is kept as the record of what the overhaul was told to do, and as the brief for any future design pass. Reopening D-20 reopens the brief.

**How to use:** paste the block below to a designer or a design tool. The compliance block is non-negotiable: it encodes Amazon Associates rules, FTC guidance and this repository's own verification discipline. Any design produced from it must still pass `scripts/verify.py` and `qa/audit_site.py`.

---

## Prompt

Design a polished affiliate-marketing website for a verified shortlist of three countertop air fryers sold on an online marketplace.

**GOAL.** An engaging, trustworthy marketing site that earns organic search traffic and converts informed readers into buyers through clearly disclosed affiliate links. It must read like a human-edited kitchen-technology publication, never like generated filler.

**BRAND & DIRECTION.** Brand name **Zone4** (kept: the project's own established name; no new trade name is introduced while trade-name clearance Q-19 is open). Visual direction **warm editorial (kitchen-magazine)**: serif display type, warm off-white and copper palette, story-led hero, card-based reading surfaces. Editorial voice **the knowledgeable friend in the kitchen — plain, warm, specific; it concludes and ranks on top of verified facts, and every factual claim still resolves to a sourced row; no hedging filler, no breathless superlatives** (D-12/S-12). Audience and market **amazon.com storefront for now (Q-04 open); readers are shoppers choosing between a dual-basket, a single-basket and a French-door toaster oven who want honest, sourced numbers before they click** (Q-16 open — use cases still to be confirmed).

**PRODUCTS.** (1) A 6-quart dual-basket air fryer with two independent baskets and a sync-finish feature. (2) A 26-quart French-door air fryer toaster oven with 24 listed cooking functions. (3) An 8-quart single-basket air fryer with a 450-degree high-heat option. Present them by format — dual-basket, single-basket, toaster-oven — because format is the reader's real decision. Every product fact on the site must come from a cited listing field; never invent specifications, prices or ratings.

**REQUIRED PAGES.** A marketing landing page with a story-led hero, a trust strip and the three-question "which one is for you" chooser; one category page per format; a products-at-a-glance comparison table plus the derived counter-space analysis (arithmetic shown, labelled derived); seven long-form articles (three product spec checks, one format comparison, three buying guides incl. a sizes-explained piece and a dated seasonal piece); a topics hub carrying the approved content calendar **(D-17 pick: the full calendar of eight, published in waves)**; and a governance section (verification log, policy compliance, flagged-for-review, sources, suggestions, questions, decision log) presented with the same design care as the marketing pages.

**TRAFFIC PROGRAM.** SEO-first, people-first. Build the approved topic calendar **(D-17: full calendar; wave one shipped 2026-11-16)** with catchy, question-shaped headlines and internal links from each topic to the format pages and reviews. Trendy language is allowed only under the adopted evidence rule **(D-19 pick: a popularity claim only as a dated snapshot of an official page; otherwise evergreen or calendar-based framing — a dated seasonal guide is fine, "the hottest air fryer of 2026" is not)**. Target featured-snippet-shaped answers — size tables, checklists, glossaries — without writing for machines. Growth is pitched on the verification angle, not volume (D-28): every number comes with its receipt, and the receipt is a selling point, not a footnote.

**ANTI-FILLER VOICE RULES (the "no AI slop" clause).** The owner's standard is explicit: the site must not read like machine output. Binding rules: no paragraph may open by defining its own category; no sentence may end with a hedging clause when the evidence is already sourced; never repeat one rhetorical shape across pages; make a recommendation wherever the verified facts support one and label it editorial judgement; prefer concrete nouns and real numbers to abstract marketing adjectives; write headlines a human would click out of curiosity, not out of keyword math; and when something is unknown, say so in plain words instead of padding around it. A reader should be able to tell within one paragraph that a person cared about their kitchen, not about a word count.

**COMPLIANCE HARD CONSTRAINTS (non-negotiable; they override any visual idea).**

- The affiliate disclosure sentence appears clearly at the top of every page, and again under every article headline and beside every paid link ("(paid link)").
- Do not publish prices, star ratings or review counts unless the authorized API route is approved (F-02).
- Do not use marketplace trademarks in page titles, meta descriptions or target keywords.
- Every table row that states a fact links to the official source it was read from.
- Anything unverified is left blank and visibly flagged, never inferred. Every article carries a "what we do not show, and why" block (D-25).
- Make no hands-on performance claims without real testing (FTC endorsement guidance; D-06: this is a specification and decision site).
- No price tracking and no price alerts (Participation Requirement 6(y)); no deals section, ever (D-30).
- Paid search is never used, and marketplace trademarks are never bid on (D-29).
- Automated content stays inside the program's agent terms (D-34: research stays manual until the Agent Terms are implemented and reviewed).

**DECISION WORKFLOW.** The site keeps a suggestions register where every change of direction is proposed, costed and risk-assessed, a questions register that separates what is known from what is missing, and a decision queue where the owner records the choice before anything is implemented. Design that review workflow as a first-class part of the product, not an afterthought.

**OUTPUT.** A complete design system (type scale, colour tokens, spacing, card and table components, disclosure component, decision-queue component), page templates for every required page, and two example article mockups built from real verified facts in `data/`. State which compliance constraints shaped each design decision.

---

## Where each slot's pick comes from (all recorded 2026-11-16 in `data/decisions.json`)

| Slot | Recorded pick | Decision |
|---|---|---|
| Brand name | Zone4 (kept; Q-19 clearance still open) | D-18 (with D-10) |
| Visual direction | Warm editorial (kitchen-magazine) | D-18 (closes S-15) |
| Editorial voice | Knowledgeable friend in the kitchen; judgement on sourced facts | D-12 / S-12 |
| Topic wave | Full calendar of eight, published in waves | D-17 / S-13 |
| Trend-language rule | Dated official snapshots only; evergreen or calendar framing otherwise | D-19 / S-16 |
| Audience and market | amazon.com storefront pending Q-04; kitchen shoppers comparing formats | Q-16 / Q-04 (still open) |
| Redesign sign-off | Keep and amend the 2026-11-15 redesign | D-21 (resolves F-46) |

The eight candidate topic titles live in suggestion **S-13** in `data/suggestions.json`; the evidence discipline behind them is flag **F-15** (no trend claim without a dated official snapshot). The chooser, the "what we do not show" blocks, the counter-space analysis and the mobile pass requested by the owner on 2026-11-16 are recorded as suggestions **S-19**, **S-22**, **S-23** and **S-20** and implemented under decisions **D-23**, **D-25**, **D-26** and **D-24**.
