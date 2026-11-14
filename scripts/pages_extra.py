#!/usr/bin/env python3
"""Marketing, platform, requirements and re-verification pages.

Kept separate from build_site.py so the page bodies for the generated-content
layer can be read and reviewed on their own. Every function takes `ctx`, a
namespace of rendering helpers and data supplied by build_site.py, so this
module never imports the builder (no circular import).
"""
from __future__ import annotations


def quote_block(ctx, paras):
    """Render draft sentences as a claims-audit table: text, basis, source, status."""
    esc = ctx.esc
    ext = ctx.ext
    table = ctx.table
    pill = ctx.pill
    rows = []
    for item in paras:
        rows.append([
            esc(item["text"]),
            esc(item["basis"]),
            ext(item["source"], "Official source"),
            pill("Sourced", "ok"),
        ])
    return table(["Sentence in the draft", "Where the statement comes from", "Source link", "Status"], rows, "claims")


def page_marketing(ctx, current):
    esc, ext, table, pill, hero, href, flag_chip = (
        ctx.esc, ctx.ext, ctx.table, ctx.pill, ctx.hero, ctx.href, ctx.flag_chip)
    m = ctx.marketing
    out = [
        hero("Marketing content drafts", m["status"]),
        '<div class="callout">' + pill("Draft only, not published", "warn")
        + ' <span class="small">Each block lists the verified field its sentences come from. Sentences the evidence does not '
          "support are not written; they appear under 'Cannot claim' instead.</span></div>",
    ]

    rules = "".join("<li>" + esc(r) + "</li>" for r in m["writing_rules"])
    out.append("<section><h2>House rules the drafts follow</h2><ul class=\"bullets\">" + rules + "</ul>"
               '<p class="small muted">Rules referenced: ' + href(current, "policy-compliance.html", "Policy compliance")
               + ".</p></section>")

    for a in m["articles"]:
        prod = next(p for p in ctx.products if p["id"] == a["product_id"])
        kw_rows = []
        for k in a["keywords"]:
            kw_rows.append([
                esc(k["term"]), esc(k["basis"]), esc(k["volume"]), esc(k["competition"]),
                ctx.status_pill(k["status"]), ext(a["source"], "Listing title"),
            ])
        sections = ""
        for sec in a["sections"]:
            sections += "<h3>" + esc(sec["heading"]) + "</h3>" + quote_block(ctx, sec["paras"])
        cannot = "".join("<li>" + esc(x) + "</li>" for x in a["cannot_claim"])
        flags = " ".join(flag_chip(current, f) for f in prod["flags"])
        out.append(
            '<section id="C-' + esc(a["product_id"]) + '">'
            + "<h2>" + esc(a["type"]) + " — " + esc(prod["name_short"]) + "</h2>"
            + '<p class="small"><strong>SEO title:</strong> ' + esc(a["seo_title"]) + "</p>"
            + '<p class="small"><strong>Meta description:</strong> ' + esc(a["meta_description"]) + "</p>"
            + '<p class="small"><strong>Proposed slug:</strong> <code>/' + esc(a["slug"]) + "</code></p>"
            + "<p><strong>" + esc(a["h1"]) + "</strong><br><span class=\"muted\">" + esc(a["lead"]) + "</span></p>"
            + sections
            + "<h3>Candidate keywords</h3>"
            + table(["Term", "Basis", "Search volume", "Competition", "Status", "Source link"], kw_rows, "keywords")
            + '<p class="small muted">Search volume and competition are blank on purpose: no official keyword source is available '
              "in this environment, so nothing is estimated (flags F-01 and F-15).</p>"
            + "<h3>Call to action as it would be published</h3>"
            + "<p>" + ext(a["cta"]["url"], a["cta"]["label"], ' class="shop"')
            + '<div class="note">' + esc(ctx.disclosure) + "</div></p>"
            + "<h3>Cannot claim in this draft</h3><ul class=\"small\">" + cannot + "</ul>"
            + '<p class="small muted">Product record: ' + href(current, "products.html", prod["id"])
            + " · Verification: " + href(current, "verification.html", "log") + " · Flags: " + flags + "</p></section>"
        )

    cmp_ = m["comparison"]
    cmp_rows = [[esc(v) for v in r["values"]] + [ext(r["source"], "Amazon listing")] for r in cmp_["rows"]]
    out.append(
        '<section id="C-CMP"><h2>' + esc(cmp_["type"]) + "</h2>"
        + '<p class="small"><strong>SEO title:</strong> ' + esc(cmp_["seo_title"]) + "</p>"
        + '<p class="small"><strong>Meta description:</strong> ' + esc(cmp_["meta_description"]) + "</p>"
        + '<p class="small"><strong>Proposed slug:</strong> <code>/' + esc(cmp_["slug"]) + "</code></p>"
        + "<p>" + esc(cmp_["note"]) + "</p>"
        + table(cmp_["columns"], cmp_rows, "comparison")
        + "<h3>What the comparison can state</h3>" + quote_block(ctx, cmp_["verdict_paras"])
        + '<p class="small muted">Category node behind all three: ' + ext(cmp_["source"], "Air Fryers") + ".</p></section>"
    )

    bg = m["buying_guide"]
    dp_rows = []
    for d in bg["decision_paths"]:
        dp_rows.append([esc(d["question"]), esc(d["grounding"]), ext(d["source"], "Amazon listing"), pill("Sourced", "ok")])
    faq_rows = []
    for f in bg["faq"]:
        faq_rows.append([esc(f["q"]), esc(f["a"]), ctx.status_pill(f["status"]), ext(f["source"], "Source")])
    out.append(
        '<section id="C-BG"><h2>' + esc(bg["type"]) + "</h2>"
        + '<p class="small"><strong>SEO title:</strong> ' + esc(bg["seo_title"]) + "</p>"
        + '<p class="small"><strong>Meta description:</strong> ' + esc(bg["meta_description"]) + "</p>"
        + '<p class="small"><strong>Proposed slug:</strong> <code>/' + esc(bg["slug"]) + "</code></p>"
        + "<p>" + esc(bg["intro"]) + "</p><h3>Decision paths</h3>"
        + table(["Reader question", "What the listing evidence answers", "Source link", "Status"], dp_rows, "paths")
        + "<h3>Questions the guide will not fake an answer to</h3>"
        + table(["Question", "Answer as drafted", "Status", "Source link"], faq_rows, "faq")
        + "</section>"
    )

    pub_rows = []
    for x in m["publish_checklist"]:
        pub_rows.append([esc(x), ext(ctx.policies_url, "Associates Program Policies"), pill("Pre-publish", "muted")])
    out.append("<section><h2>Publish checklist</h2>"
               + table(["Step", "Rule source", "When"], pub_rows, "checklist") + "</section>")

    meas_rows = []
    for x in m["measurement_plan"]:
        meas_rows.append([esc(x["metric"]), esc(x["how"]), esc(x["limit"]), ext(x["source"], "Source"), pill("Planned", "muted")])
    out.append("<section><h2>Click and conversion measurement plan</h2>"
               '<p class="small muted">Nothing is measured today: no Associates reporting and no analytics property are connected. '
               "This is the compliant design the platform would run once access exists.</p>"
               + table(["Metric", "How it would be collected", "Constraint", "Rule source", "Status"], meas_rows, "measure")
               + "</section>")
    return "".join(out)


def page_platform(ctx, current):
    esc, ext, table, hero, href = ctx.esc, ctx.ext, ctx.table, ctx.hero, ctx.href
    pf, niche = ctx.platform, ctx.niche
    st_rows = []
    for x in pf["stages"]:
        st_rows.append([
            esc(x["stage"]), esc(x["automation"]), ext(x["source"], "Gate reference"),
            ctx.status_pill(x["gate"]), ctx.status_pill(x["status"]),
        ])
    guard = "".join("<li>" + esc(g) + "</li>" for g in pf["guardrails"])
    notconn = "".join("<li>" + esc(n) + "</li>" for n in pf["not_connected"])
    method = "".join("<li>" + esc(step) + "</li>" for step in niche["method"])
    niche_rows = []
    for n in niche["candidate_niches"]:
        niche_rows.append([
            esc(n["niche"]), esc(n["demand"]), esc(n["competition"]), esc(n["ticket_size"]),
            esc(n["commission_rate"]), esc(n["content_angle"]), ext(n["evidence_url"], n["evidence"]),
            ctx.pill(n["status"], "muted"),
        ])
    return (
        hero("Platform & automation", pf["summary"])
        + "<section><h2>Stages and their gates</h2>"
        + table(["Stage", "Automation intended", "Gate source", "Gate", "Status today"], st_rows, "stages")
        + "</section><section><h2>Guardrails built into the pipeline</h2>"
        + '<ul class="bullets">' + guard + "</ul>"
        + '<p class="small muted">These checks live in the build itself ('
        + href(current, "sources.html", "scripts/verify.py") + ") and run in CI on every push and pull request.</p></section>"
        + "<section><h2>Scalability</h2><p>" + esc(pf["scalability"]) + "</p></section>"
        + '<section><h2>Not connected in this environment</h2><ul class="small">' + notconn + "</ul></section>"
        + "<section><h2>Niche selection method</h2><p>" + esc(niche["note"]) + "</p>"
        + '<ol class="small">' + method + "</ol>"
        + "<h3>Candidate niches scored</h3>"
        + table(["Niche", "Demand", "Competition", "Ticket size", "Commission rate", "Content angle", "Source link", "Status"],
                niche_rows, "niche")
        + "</section>"
    )


def page_requirements(ctx, current):
    esc, ext, table, hero = ctx.esc, ctx.ext, ctx.table, ctx.hero
    rows = []
    counts = {"Delivered": 0, "Drafted": 0, "Gated": 0}
    for q in ctx.requirements:
        status = q["status"]
        key = "Delivered" if status.startswith("Delivered") else ("Drafted" if status.startswith("Drafted") else "Gated")
        counts[key] += 1
        rows.append([
            esc(q["id"]), esc(q["brief"]), ctx.status_pill(status), esc(q["delivered"]),
            esc(q["blocker"]), ext(q["evidence_url"], q["evidence"]),
        ])
    summary = " · ".join(f"{k}: {v}" for k, v in counts.items())
    return (
        hero("Requirements coverage",
             "Every requirement in the brief, traced to what this repository does about it. Gated rows name the credential, data "
             "source or compliance decision that blocks them, with the flag that carries it.")
        + '<div class="callout small">' + esc(summary) + " · " + str(len(ctx.requirements)) + " requirements in total.</div>"
        + '<p><input id="filter" class="filter" type="search" placeholder="Filter rows (for example: Blocked, Q-07, F-18)" '
          'aria-label="Filter table"></p>'
        + table(["ID", "Requirement (from the brief)", "Status", "What exists today", "Blocker or limit", "Evidence source"],
                rows, "requirements")
    )


def page_reverification(ctx, current):
    esc, ext, table, hero, flag_chip, href = ctx.esc, ctx.ext, ctx.table, ctx.hero, ctx.flag_chip, ctx.href
    rev = ctx.reverif
    rows = []
    reconfirmed = 0
    for chk in rev["checks"]:
        if chk["status"].startswith("Re-confirmed"):
            reconfirmed += 1
        rows.append([
            esc(chk["id"]), esc(chk["check"]), esc(chk["expected"]), esc(chk["result"]),
            ctx.status_pill(chk["status"]), ext(chk["source"], "Official source"),
        ])
    chips = " ".join(flag_chip(current, f) for f in ("F-12", "F-18", "F-24", "F-25", "F-26", "F-27", "F-28", "F-29", "F-30"))
    return (
        hero("Independent re-verification pass",
             f"Second pass by session {rev['session']} on {rev['date_utc']} (UTC). {reconfirmed} of {len(rev['checks'])} checks "
             "re-confirmed the published record; the rest are labelled new, corrected or carried forward rather than silently accepted.")
        + '<p class="small muted">' + esc(rev["method"]) + "</p>"
        + '<p><input id="filter" class="filter" type="search" placeholder="Filter rows (for example: Re-confirmed, carried, F-17)" '
          'aria-label="Filter table"></p>'
        + table(["ID", "Check performed", "Expected from the record", "What this pass observed", "Result", "Source link"],
                rows, "reverification")
        + '<p class="small muted">Open items this pass produced: ' + chips + ". See "
        + href(current, "flagged.html", "Flagged for review") + ".</p>"
    )


def build_pages(ctx):
    """Return the BODIES entries for the four added pages."""
    return {
        "marketing.html": lambda cur: page_marketing(ctx, cur),
        "platform.html": lambda cur: page_platform(ctx, cur),
        "requirements.html": lambda cur: page_requirements(ctx, cur),
        "reverification.html": lambda cur: page_reverification(ctx, cur),
    }
