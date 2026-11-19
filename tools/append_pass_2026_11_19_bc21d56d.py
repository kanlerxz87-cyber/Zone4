#!/usr/bin/env python3
"""One-off append script for the 2026-11-19 decision-support pass (arena/bc21d56d-zone4).

Appends flag F-74, suggestions SG-31..SG-38, questions Q-52..Q-56 and the
decision-paths data. No existing row is modified except the suggestions
_meta.statuses vocabulary (one dated status added, matching the 11-16/11-17
pattern). Run from the repo root; deletes itself is NOT done (kept as the
audit record of what this session added).
"""
import json

ROOT = "/home/user/Zone4"


def load(path):
    with open(f"{ROOT}/{path}", encoding="utf-8") as fh:
        return json.load(fh)


def save(path, doc):
    with open(f"{ROOT}/{path}", "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


GHC = "https://github.com/kanlerxz87-cyber/Zone4/blob/main/"
HELPFUL = "https://developers.google.com/search/docs/fundamentals/creating-helpful-content"
AI_CONTENT = "https://developers.google.com/search/blog/2023/02/google-search-and-ai-content"
PEXP = "https://developers.google.com/search/docs/appearance/page-experience"
SNIPPET = "https://developers.google.com/search/docs/appearance/snippet"
AGREEMENT = "https://affiliate-program.amazon.com/help/operating/agreement"
FTC101 = "https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers"
FTC_END = "https://www.ftc.gov/business-guidance/advertising-marketing/endorsements-influencers-reviews"

# ---------------------------------------------------------------- flags ----
flags = load("data/flags.json")
flag_ids = {f["id"] for f in flags["flags"]}
assert "F-74" not in flag_ids, "F-74 already exists"
assert "F-73" in flag_ids, "F-73 (parallel session) must exist; renumber before appending"
flags["flags"].append({
    "id": "F-74",
    "severity": "Low",
    "title": "The brief's claim that the site 'reads like some AI slop website' is itself unverified: no page, sentence or surface is named as evidence",
    "detail": "Added 2026-11-19 by arena/bc21d56d-zone4. The current session brief repeats the 2026-11-17 wording ('It should not read like some AI slop website like it looks like now') but names no page, sentence or surface. What the register can establish: ten anti-patterns (AS-01..AS-10 in data/design.json) were documented from observed evidence and their replacements applied under recorded decisions D-12 (voice) and D-36 (copy pass); F-52 records the one opener defect found and its correction; every published article was rewritten to the recorded voice. Whether further surfaces still read as machine output is an owner judgement that no official source or register row currently evidences. This flag publishes the gap instead of treating the complaint as a finding. Q-52 asks the owner for the named examples; SG-34 stages the evidence pass that converts each named example into an AS-11+ row.",
    "status": "Needs review (owner input requested)",
    "action": "Reviewer/owner: name the published pages or sentences that read as machine output (question Q-52). Each named example becomes an anti-pattern row with its evidence and a replacement, and the openers are re-read against the expanded list (SG-34). If no example is named, that answer is recorded and this flag closes with the owner-confirmed result.",
    "sources": [
        HELPFUL,
        f"{GHC}data/design.json",
    ],
})
save("data/flags.json", flags)

# ---------------------------------------------------------- suggestions ----
sg = load("data/suggestions.json")
sg_ids = {s["id"] for s in sg["suggestions"]}
for sid in [f"SG-{n}" for n in range(31, 39)]:
    assert sid not in sg_ids, f"{sid} already exists"

# one dated status added to the register vocabulary, matching the 11-16/11-17 pattern
sg["_meta"]["statuses"]["Implemented 2026-11-19"] = (
    "Decision recorded earlier (D-38, 2026-11-17) and the change it commits is live in this build (2026-11-19)."
)

sg["suggestions"].extend([
    {
        "id": "SG-31",
        "priority": "P2 - Adds real value",
        "title": "Name the one reader the design prompt is written for, and fill its [AUDIENCE] slot from evidence",
        "problem": "The design brief's paste-ready prompt fills six of its seven slots from recorded decisions. The [AUDIENCE] slot still ships open ('still open (Q-16 and Q-04)'), so the brief a designer or a design tool receives asks it to write for nobody in particular. Google's people-first guidance ties helpful content to a specific intended audience, and an unspecified audience is the reader-side condition the brief's 'reads like AI slop' complaint (F-74) describes.",
        "proposal": "After Q-16 and Q-04 are answered - by the owner, or from dated Search Console queries once D-42 is actioned - fill the [AUDIENCE] slot with one named primary reader (for example, a first-time buyer measuring a small counter), and re-read the eight published openers and the hero sentence against that persona once. Wording only: no published value, table, link or product fact changes.",
        "why": "Every other slot in the prompt is already filled from a recorded decision, so this is the cheapest remaining lever on whether the site reads as written for someone rather than generated at no one.",
        "effort": "About an hour of wording once the persona is named; no build change.",
        "risk": "Low. The failure mode to avoid is inventing a persona: the slot must be filled from an owner statement or a dated measurement record, attributed to the decision or record that supplied it.",
        "check": "scripts/render_design_prompt.py shows the [AUDIENCE] slot filled and attributed; the persona's source (a decision or a dated measurement record) is named in the slot row; a second render is byte-identical.",
        "sources": [
            {"url": HELPFUL, "ref": "Google Search Central: helpful content is created for a specific, intended audience"},
        ],
        "flags": ["F-74"],
        "status": "Needs a decision first",
        "decision": "D-35",
        "status_note_2026_11_19": "Added 2026-11-19 by arena/bc21d56d-zone4 from the brief's design-suggestion request. The slot itself is filled from Q-16/Q-04 or from measured queries; the decision pointer is D-35 because that is the recorded design-specification decision the prompt slots render under. Nothing is filled until the evidence exists.",
    },
    {
        "id": "SG-32",
        "priority": "P2 - Adds real value",
        "title": "Propose the next topic wave: three question-shaped candidates prepared for the calendar's first review",
        "problem": "The eight-topic calendar was adopted (D-17) and one topic is written (T-04). The calendar's first review has no prepared candidates, so the next wave would be chosen from instinct - the exact failure mode the cadence and the evidence rule were adopted to prevent.",
        "proposal": "Prepare three candidates for the owner's calendar review, each question-shaped and built only from fact rows already verified in the register: (a) 'Which of the three listed footprints leaves you counter space to work?' - a decision page from the published counter-space analysis; (b) 'Which listing answers a first-time buyer's first five questions?' - a gap page built from the three product fact tables; (c) 'Two baskets, one big basket, or a toaster oven: what the listed function counts say about cleanup' - an extension of the published format comparison into the cleanup dimension. Each candidate carries its fact-row ids and its official listing sources before any writing starts.",
        "why": "The brief asks for catchy, trendy articles. The evidence rule (D-19) and the people-first standard (D-17) are what make that publishable at speed; candidates prepared in advance are how the calendar stays question-shaped under deadline pressure instead of drifting into demand claims.",
        "effort": "Half a day to write the three candidate rows with their fact-row ids. Writing the chosen articles is the calendar's normal cadence.",
        "risk": "Topic candidates that imply popularity ('what people are searching for') would breach the recorded evidence rule D-19; the candidates above are framed as reader questions, not demand claims.",
        "check": "Each candidate names its fact-row ids and links the official listing pages those facts were read from; no search-volume, popularity or traffic figure appears anywhere in the row (D-19; Operating Agreement Section 4).",
        "sources": [
            {"url": HELPFUL, "ref": "Google Search Central: the people-first standard the candidates are written to"},
            {"url": AGREEMENT, "ref": "Operating Agreement Section 4: no representation about traffic any site can expect"},
        ],
        "flags": [],
        "status": "Awaiting decision",
        "decision": "D-17",
        "status_note_2026_11_19": "Added 2026-11-19 by arena/bc21d56d-zone4. The pointer is D-17 because adopting any topic beyond the recorded eight is a calendar revision that the owner reviews; until then the candidates stay proposals with their fact-row ids attached.",
    },
    {
        "id": "SG-33",
        "priority": "P2 - Adds real value",
        "title": "Finish the social-preview half of S-09: a real og:image and Article structured data on every article page",
        "problem": "S-09 is partly implemented. Structured data exists on the front page and one guide, and no published page carries an og:image, so a link shared in a chat or a social feed shows no preview image at all. The 'measure whether search traffic arrives' half of S-09 cannot fairly start from an unshareable card.",
        "proposal": "Generate one static, text-based site-card image (owned, no product photography - D-22 governs product photos separately), wire og:image and card tags into the head builder, and extend the Article structured-data block to every article page. Re-run S-09's measurement plan once D-42 is actioned.",
        "why": "A shared link with no preview card loses the click before the content can earn it. This is the last purely technical item on the S-09 list; the rest is measurement that waits on the owner's Search Console decision.",
        "effort": "Half a day: one image, head-builder changes, and the per-article JSON-LD block.",
        "risk": "Low. The image must not imply endorsement, testing claims or Amazon marks; text-only with the site name and subject avoids all three.",
        "check": "Every published page's head carries og:image; the QA audit's head and per-page checks pass; the image file ships with a recorded provenance note (generated by this repository, not copied).",
        "sources": [
            {"url": PEXP, "ref": "Google Search Central: page experience and presentation guidance (the S-09 decision's source)"},
            {"url": SNIPPET, "ref": "Google Search Central: how titles and snippets are presented"},
        ],
        "flags": [],
        "status": "Awaiting decision",
        "decision": "D-09",
        "status_note_2026_11_19": "Added 2026-11-19 by arena/bc21d56d-zone4 after checking the built pages: og:image appears on none of them (grep across docs/), and S-09's status already read 'partly implemented'. This row stages the unfinished half rather than re-opening what D-09 already approved.",
    },
    {
        "id": "SG-34",
        "priority": "P2 - Adds real value",
        "title": "Run the slop-evidence pass: convert the owner's named examples into new anti-pattern rows, then re-read the openers against them",
        "problem": "The brief says the site 'should not read like some AI slop website like it looks like now' but names no page or sentence (F-74). The anti-slop register (AS-01..AS-10) documents ten observed patterns with evidence and replacements; a complaint without examples cannot be turned into a targeted fix, only into rewrites that might miss what the owner actually saw.",
        "proposal": "Take the owner's answer to Q-52 - the specific pages or sentences that read as machine output. Convert each named example into an AS-11+ row with the same structure as the existing ten (pattern, evidence, replacement), then re-read the eight published openers, the hero sentence and the category pages against the expanded list and correct what fails. If the owner names nothing, record that answer too: the register then holds an owner-confirmed result instead of an open complaint.",
        "why": "This is the difference between acting on the brief's wording and acting on its substance. The register method keeps every fix checkable and prevents a style pendulum.",
        "effort": "Half a day once examples arrive (or the absence is recorded).",
        "risk": "Low. The risk is over-correcting into voiceless prose; the existing register's replacement column pattern guards against that, and the recorded voice (D-12) governs.",
        "check": "Every new AS row names its evidence (page and quote); the design prompt render includes the new rows; the re-read result is recorded per article; no popularity or process claim is introduced.",
        "sources": [
            {"url": HELPFUL, "ref": "Google Search Central: what makes content helpful and people-first"},
            {"url": AI_CONTENT, "ref": "Google Search Central: Google's guidance on AI-generated content and reward for helpfulness"},
        ],
        "flags": ["F-74"],
        "status": "Needs a decision first",
        "decision": "D-36",
        "status_note_2026_11_19": "Added 2026-11-19 by arena/bc21d56d-zone4. The pointer is D-36 (the recorded copy-pass decision) because the pass this row stages is that decision's method applied to newly named evidence, not a new direction.",
    },
    {
        "id": "SG-35",
        "priority": "P2 - Adds real value",
        "title": "Front-load the 2026 holiday window: schedule the next two calendar pieces inside the gift season instead of at the 14-day cadence",
        "problem": "The publishing cadence is one guide per 14 days (recorded 2026-11-17; the owner may change it, F-65). The gift guide is already published, but the next calendar piece at the current cadence falls after the season's peak: Black Friday 2026 falls on 2026-11-27 and the gift season runs to the end of December. A steady cadence that ignores the calendar wastes the seasonal window the gift guide was written for.",
        "proposal": "Owner decision: publish the next two calendar topics inside the 2026-11-27..2026-12-25 window (roughly weekly), then return to the 14-day cadence in January. The framing stays calendar-based, which the recorded evidence rule D-19 explicitly allows; no popularity or demand claim is made about the season.",
        "why": "The gift guide exists and the seasonal dates are calendar arithmetic, not forecasts. This is the one cadence change that needs no measurement to justify, because the season's dates are fixed.",
        "effort": "An owner decision, plus the normal writing cadence compressed by roughly a week per piece.",
        "risk": "Writing faster can read thinner; the anti-slop register and the fact-row discipline are the guard, and the cadence reverts in January.",
        "check": "publishing.json records the temporary cadence with its end date; the feed and sitemap carry the pieces as they land; no traffic, demand or popularity figure is cited anywhere (D-19).",
        "sources": [
            {"url": HELPFUL, "ref": "Google Search Central: people-first content - the standard the cadence serves"},
            {"url": AGREEMENT, "ref": "Operating Agreement Section 4: no representation about expected traffic"},
        ],
        "flags": ["F-65"],
        "status": "Awaiting decision",
        "decision": "D-17",
        "status_note_2026_11_19": "Added 2026-11-19 by arena/bc21d56d-zone4. The calendar dates used (2026-11-27, 2026-12-25) are fixed calendar dates, not claims about demand. F-65 already records that the cadence is owner-changeable, so this row asks rather than changes.",
    },
    {
        "id": "SG-36",
        "priority": "P2 - Adds real value",
        "title": "Give the Decision centre a choose-a-path triage: the open decisions presented as three coherent orders",
        "problem": "Twelve open decisions sit in one queue in numeric order. The brief asks for 'a section dedicated for suggestions so someone can review suggestions and choose the best path before implementing any changes' - the Decision centre exists and presents counts, a reading order and the gating decisions, but a reviewer must still assemble a strategy from twelve isolated rows.",
        "proposal": "Add a 'choose a path' section to the Decision centre page, rendered at build time from a new top-level paths key in data/decisions.json: Path A orders the measurement and attribution decisions (D-41, D-43, D-16, D-42, D-02, D-08); Path B orders the audience and catalogue decisions (D-42, D-13, D-40, D-15, D-22); Path C orders the presentation decisions (D-39, D-22, D-44). Each step names what it unblocks; each path names what it deliberately delays. The paths are presentations of the register, not new decisions; the numeric queue stays the source of truth and every row keeps the decision's own official source link.",
        "why": "D-38's recorded option A already committed the queue to dependency order and a shortest credible path; this extends the same principle from one path to the three strategies the owner can actually choose between, which is what 'choose the best path' asks for.",
        "effort": "One build change plus the paths data. No published value, product fact, link or policy claim moves.",
        "risk": "A derived order can look authoritative where it is a recommendation. The section states that every path is optional and the queue remains the source of truth; the build refuses to render a path step that names an unknown or no-longer-open decision.",
        "check": "Every path step references a decision id that exists and is currently open; each rendered row carries the decision's own official source; the page states the paths are recommendations, not recorded choices.",
        "sources": [
            {"url": f"{GHC}data/decisions.json", "ref": "The register itself: the decisions and statuses the paths are derived from"},
            {"url": HELPFUL, "ref": "Google Search Central: does the site have a primary purpose or focus (the D-38 source)"},
        ],
        "flags": [],
        "status": "Implemented 2026-11-19",
        "decision": "D-38",
        "status_note_2026_11_19": "Added and shipped 2026-11-19 by arena/bc21d56d-zone4. This is decision-support presentation (the review surface the brief asks for), not implementation of any gated change: nothing on the site's published content, links or product records changes because of it.",
    },
    {
        "id": "SG-37",
        "priority": "P3 - Housekeeping",
        "title": "Stop the count drift for good: generate the README and executive-summary register counts from the registers at build time",
        "problem": "README.md and EXECUTIVE_SUMMARY.md carry hard-coded register counts (suggestions, questions, decisions, flags). The counts drifted once before (F-71) and needed another hand reconciliation in this pass after parallel sessions appended rows in the same week. Every parallel session multiplies the chance the next drift ships.",
        "proposal": "Have the build write a small generated counts file from the registers, and replace the hard-coded numbers in the two documents with wording that points at the always-current Decision centre counts (the pages are generated from the same data and cannot drift). Add a verifier rule that fails if a stale hard-coded count reappears.",
        "why": "Documentation that states counts is the last surface that can silently disagree with the registers; the site pages cannot drift because they are generated from the registers themselves.",
        "effort": "About two hours: one generator step, two document edits, one verifier rule.",
        "risk": "Low. The documents' prose must keep working when read as plain files, so the wording says 'see the live page' rather than printing a number that can age.",
        "check": "A clean-checkout build leaves no register count in the two documents that disagrees with the registers; the verifier fails a reintroduced hard-coded count.",
        "sources": [
            {"url": f"{GHC}ENGINE.md", "ref": "The engine documentation whose test-count line was the F-71 class of drift"},
            {"url": f"{GHC}data/suggestions.json", "ref": "The registers the counts would be generated from"},
        ],
        "flags": ["F-71"],
        "status": "Awaiting decision",
        "decision": "D-10",
        "status_note_2026_11_19": "Added 2026-11-19 by arena/bc21d56d-zone4 after reconciling the counts by hand for this pass. The pointer is D-10 (documentation in line with the code), recorded 2026-11-16; this row stages the automation that would make the reconciliation unnecessary.",
    },
    {
        "id": "SG-38",
        "priority": "P3 - Housekeeping",
        "title": "Define the starter query set now, so Search Console data has a baseline to be compared against on day one",
        "problem": "D-42 (Search Console verification) is open, and the site's stated plan is to choose the next topic from measured queries (SG-29, Q-40). Nothing defines what the measurements will be compared against: when the first impressions arrive there is no record of which queries the published pages were built to answer, so 'did the right page arrive for its question' is unanswerable in hindsight.",
        "proposal": "Record a starter query set before any measurement exists, in the ledger's provenance format: one query per published page, drawn from that page's own title and question (for example, the sizes article maps to its '6QT vs 8QT vs 26QT' question). The set is a hypothesis record, not a claim about demand; once Search Console reports, the ledger gains dated rows comparing measured queries against it.",
        "why": "The measurement contract (five events, ledger rules) already exists; this adds the search-side baseline at zero cost, and it can be written today without any account access.",
        "effort": "About an hour to write the set into a data file with per-query provenance.",
        "risk": "Low. The set must be labelled as the site's own hypothesis: no search-volume figure and no claim that any query is popular (D-19).",
        "check": "Each starter query maps to exactly one published page; the file states it is a hypothesis record with its creation date; the ledger's append-only, provenance rules apply to the future measured rows.",
        "sources": [
            {"url": PEXP, "ref": "Google Search Central: page experience and measurement guidance (the D-42 decision's source)"},
            {"url": HELPFUL, "ref": "Google Search Central: the people-first standard the pages were written to"},
        ],
        "flags": [],
        "status": "Needs a decision first",
        "decision": "D-42",
        "status_note_2026_11_19": "Added 2026-11-19 by arena/bc21d56d-zone4. The set itself needs no account access, but recording it on the site publishes a measurement intent, so the row waits on D-42 rather than writing the file unilaterally.",
    },
])
save("data/suggestions.json", sg)

# ------------------------------------------------------------ questions ----
qs = load("data/questions.json")
q_ids = {q["id"] for q in qs["questions"]}
for qid in [f"Q-{n}" for n in range(52, 57)]:
    assert qid not in q_ids, f"{qid} already exists"
qs["questions"].extend([
    {
        "id": "Q-52",
        "area": "Editorial voice and content standards",
        "question": "Which published pages or sentences read as machine output to the owner, and what would the opposite look like on this site?",
        "why_it_matters": "The brief states the site 'should not read like some AI slop website like it looks like now' but names no page, sentence or surface (F-74). The anti-slop register documents ten observed patterns with evidence and replacements; a complaint without examples cannot be turned into a targeted fix, only into rewrites that might miss what the owner actually saw.",
        "kind": "Owner decision",
        "known": "The register method: every anti-pattern row (AS-01..AS-10 in data/design.json) names the pattern, the evidence and a replacement. Eight published articles were rewritten once under the recorded voice decision D-12 and the 2026-11-17 copy pass D-36; F-52 records the one opener defect found and its correction.",
        "how_to_discover": "The owner names the pages or quotes the sentences that read as machine output. Each named example becomes an AS-11+ row with its evidence and replacement, and the openers are re-read against the expanded list (SG-34). If no example is named, that answer is recorded and F-74 closes with the owner-confirmed result.",
        "answerable_by": "The site owner",
        "blocks": ["SG-34"],
        "flags": ["F-74"],
        "sources": [
            {"url": HELPFUL, "ref": "Google Search Central: what makes content helpful and people-first"},
            {"url": AI_CONTENT, "ref": "Google Search Central: Google's guidance on AI-generated content"},
        ],
        "status": None,
    },
    {
        "id": "Q-53",
        "area": "Design brief",
        "question": "Which single reader should the design prompt's [AUDIENCE] slot name first, and how will the site know when it has chosen wrong?",
        "why_it_matters": "Six of the prompt's seven slots are filled from recorded decisions; the [AUDIENCE] slot still ships open. Until it is named, every surface speaks to everyone, which reads as speaking to no one - the reader-side of the not-slop requirement - and the brief a designer receives stays incomplete.",
        "kind": "Owner decision",
        "known": "Q-16 asks the broader audience question (use cases) and Q-04 asks whether amazon.com is the right storefront; neither names one primary reader. The slot stays open until an owner statement or dated measurement fills it with attribution.",
        "how_to_discover": "The owner names one primary reader (for example a first-time buyer measuring a small counter, a gift buyer, or an upgrader replacing an older appliance); or, once D-42 is actioned, the first months of measured queries name the reader from evidence. Fill the slot with attribution to whichever supplied it (SG-31), and review the choice against the measured queries after a season.",
        "answerable_by": "The site owner (or dated measurement once Search Console is connected)",
        "blocks": ["SG-31"],
        "flags": [],
        "sources": [
            {"url": HELPFUL, "ref": "Google Search Central: helpful content is created for a specific, intended audience"},
        ],
        "status": None,
    },
    {
        "id": "Q-54",
        "area": "Publishing cadence",
        "question": "Should the one-guide-per-14-days cadence temporarily front-load the 2026 gift window (2026-11-27 to 2026-12-25) and revert in January?",
        "why_it_matters": "The gift guide is published and the next calendar piece at the current cadence falls after the season's peak days. The cadence was recorded as an owner-changeable default (F-65); the seasonal dates are calendar arithmetic, not forecasts, so this is the one cadence change that needs no demand data to justify - and declining it costs nothing.",
        "kind": "Owner decision",
        "known": "The cadence (one guide per 14 days) was recorded 2026-11-17 and flagged owner-changeable (F-65). The recorded evidence rule D-19 allows calendar-based framing; no popularity or demand claim is needed or permitted for the season.",
        "how_to_discover": "The owner confirms or declines the temporary cadence (SG-35). If confirmed, publishing.json records the temporary cadence with its end date; if declined, the 14-day cadence stands and the calendar review happens after the season.",
        "answerable_by": "The site owner",
        "blocks": ["SG-35"],
        "flags": ["F-65"],
        "sources": [
            {"url": HELPFUL, "ref": "Google Search Central: people-first content - the standard the cadence serves; no official source governs publishing frequency itself"},
        ],
        "status": None,
    },
    {
        "id": "Q-55",
        "area": "Measurement",
        "question": "Which queries should form the starter baseline set - one per published page, drawn from each page's own question - and who records it before any measurement exists?",
        "why_it_matters": "The plan is to choose the next topic from measured queries (D-42, SG-29), but nothing defines what the measurements will be compared against. Without a written baseline recorded before data arrives, 'did the right page arrive for its question' is unanswerable in hindsight and topic choices drift back to instinct.",
        "kind": "Owner decision",
        "known": "The five-event measurement contract and the ledger's provenance rules exist (data/ledger.json). D-42 names no baseline set, and Q-40 records that no search-volume figure exists for any topic - the baseline is a hypothesis record, not a demand claim.",
        "how_to_discover": "Draft the set from the published pages themselves (one query per page, from its own title and question - SG-38), label it as the site's hypothesis record with its creation date, and compare the first dated Search Console rows against it once the property is verified.",
        "answerable_by": "The site owner (any session can draft the set; recording it as the baseline is the owner's confirmation)",
        "blocks": ["SG-38"],
        "flags": [],
        "sources": [
            {"url": PEXP, "ref": "Google Search Central: page experience and measurement guidance (the D-42 decision's source)"},
            {"url": HELPFUL, "ref": "Google Search Central: the people-first standard the pages were written to"},
        ],
        "status": None,
    },
    {
        "id": "Q-56",
        "area": "Reader participation",
        "question": "Does the owner want an on-page reader-question intake (readers submit the question they arrived with), and who writes the answers under what moderation and privacy rules?",
        "why_it_matters": "The site's growth plan is question-shaped content chosen from measured demand; an intake is the one channel where readers supply questions directly, and it is the natural feed for the measured 'what readers ask next' module proposed in S-44. Without a decision, the only follow channel is the RSS feed (SG-30) and the question data stays one-sided.",
        "kind": "Owner decision",
        "known": "Reader capture of contact details is gated on the privacy decisions D-16/D-41. An intake that publishes answers about products is endorsement-adjacent: any published answer that recommends a product carries the material-connection disclosure the FTC guidance requires.",
        "how_to_discover": "Owner decision: yes or no; who writes the answers; whether answers are pre-moderated before publication; and the privacy rule for anything submitted. If approved, it ships only after the privacy boundary decision (D-16) is recorded.",
        "answerable_by": "The site owner",
        "blocks": [],
        "flags": [],
        "sources": [
            {"url": FTC101, "ref": "FTC: Disclosures 101 - material connections must be disclosed clearly and conspicuously"},
            {"url": FTC_END, "ref": "FTC: Endorsements, Influencers, and Reviews - endorsements must reflect honest opinions and disclose connections"},
        ],
        "status": None,
    },
])
for q in qs["questions"]:
    if q.get("status") is None and q["id"] in {"Q-52", "Q-53", "Q-54", "Q-55", "Q-56"}:
        del q["status"]
save("data/questions.json", qs)

# ------------------------------------------------ decisions: paths data ----
dec = load("data/decisions.json")
assert "paths" not in dec, "paths key already exists"
dec["paths"] = {
    "_meta": {
        "description": "Choose-a-path triage for the Decision centre page (added 2026-11-19, arena/bc21d56d-zone4, implementing the presentation D-38 option A commits). The paths are presentations of the open decisions in coherent orders, not recorded choices: the queue stays the source of truth and every path is optional. The builder refuses to render a path step that names an unknown or no-longer-open decision.",
        "added_utc": "2026-11-19",
        "added_by": "arena/bc21d56d-zone4",
    },
    "paths": [
        {
            "id": "PATH-A",
            "name": "Path A - measurement and attribution first",
            "one_line": "Make every click and query countable before adding anything new.",
            "best_for": "The owner wants to know what is working before spending another hour on content or looks.",
            "steps": [
                {"decision": "D-41", "why": "Approve the privacy boundary: local-only analytics, or a first-party endpoint with a separate consent flow. Nothing may flow until this is recorded.", "unblocks": "D-43, D-16, reader capture (SG-30), the campaign ledger"},
                {"decision": "D-43", "why": "Choose where the endpoint runs. The endpoint code and the five event definitions exist in the repository; hosting is the owner's call.", "unblocks": "The five defined events; F-59 closes"},
                {"decision": "D-16", "why": "Confirm what measurement is acceptable and the consent wording that goes with it before scaling.", "unblocks": "The measured 'what readers ask next' module (S-44)"},
                {"decision": "D-42", "why": "Verify the property in Search Console and submit the sitemap and feed.", "unblocks": "Measured queries for topic choice (SG-29, Q-40); the starter baseline (SG-38)"},
                {"decision": "D-02", "why": "Pursue Creators API access so prices and ratings can be published lawfully.", "unblocks": "The blank price and rating cells; gated on Amazon's stated sales prerequisite (Q-02)"},
                {"decision": "D-08", "why": "Publish the per-ASIN commission rate once known, or publish no rate at all.", "unblocks": "An honest answer to the commission question on the products page"},
            ],
            "delays": "Presentation polish (D-39, D-22) and catalogue widening (D-40, D-13).",
            "cost_note": "Mostly account work and configuration; the writing cadence is unchanged.",
        },
        {
            "id": "PATH-B",
            "name": "Path B - audience and catalogue first",
            "one_line": "Learn who arrives, then widen what the site can honestly promote.",
            "best_for": "The owner wants growth in what the site covers before investing in how it measures or looks.",
            "steps": [
                {"decision": "D-42", "why": "Verify Search Console first: measured queries tell the calendar which questions arrive before anything is widened.", "unblocks": "Evidence-based topic choice (SG-29, Q-40, Q-53)"},
                {"decision": "D-13", "why": "Confirm the three supplied links are the intended products.", "unblocks": "The product register's intent record closes cleanly"},
                {"decision": "D-40", "why": "Confirm the intended products for all five links and how the two thermometer listings stay scoped (D-46 governs until reversed).", "unblocks": "A five-product catalogue decision; the thermometer category's scope"},
                {"decision": "D-15", "why": "State what research automation is authorised and from what source it may read.", "unblocks": "Faster verified listings without manual re-reading"},
                {"decision": "D-22", "why": "Choose the photography route: the owner's own photos or images served through an approved Amazon tool.", "unblocks": "Real product imagery on the category and product pages (S-18)"},
            ],
            "delays": "Endpoint hosting (D-43, D-16) and the token-layer polish (D-39).",
            "cost_note": "Some owner confirmations and one or two build passes; no measurement work beyond Search Console.",
        },
        {
            "id": "PATH-C",
            "name": "Path C - presentation first",
            "one_line": "Finish the look the brief asks for, at the smallest decision cost.",
            "best_for": "The owner wants the 'polished marketing site' read fixed before anything else is touched.",
            "steps": [
                {"decision": "D-39", "why": "Move colour, type and spacing into a token layer so a direction can be switched in one file.", "unblocks": "Every future visual pass gets cheaper and reversible"},
                {"decision": "D-22", "why": "Decide the photography route (owner photos or an approved Amazon tool) - the one visual input a listing cannot supply.", "unblocks": "Real imagery; closes S-18's open decision"},
                {"decision": "D-44", "why": "Decide whether the measurement surfaces added 2026-11-17 fold into the design brief or stay as shipped.", "unblocks": "A single, settled brief for the next design pass"},
            ],
            "delays": "All measurement (D-41, D-43, D-16, D-42) and any catalogue widening (D-40, D-13).",
            "cost_note": "The smallest set: three decisions, build work only, nothing account-side.",
        },
    ],
}
save("data/decisions.json", dec)

print("appended: F-74, SG-31..SG-38, Q-52..Q-56, decisions.paths")
