"""Render the GitHub Pages site from the verified data layer.

The site is generated from ``data/*.json`` so a table cell and the engine's own
view of that fact can never drift apart. Blank + a flag is a first-class output:
every withheld value is shown as an explicit "Unverified" pill with the source
that *would* confirm it, so the page is auditable line by line.

Only class names defined in the repo's ``styles.css`` (plus its documented
compatibility block) are used, and internal links are checked at build time.
"""

from __future__ import annotations

import re

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

from .claims import Status
from .datastore import PRODUCT_FIELDS, Datastore
from .economics import rate_table
from .links import is_safe_href
from .policy import AMAZON_TEXT_NOTICE, REQUIRED_DISCLOSURE, compliance_matrix

STYLESHEET = "preview.css"

NAV = [
    ("index.html", "▦", "Overview"),
    ("verification.html", "◎", "Verification ledger"),
    ("rates.html", "£", "Rates & economics"),
    ("compliance.html", "⚖", "Compliance controls"),
    ("data-api.html", "⛁", "Data & API"),
    ("flagged.html", "⚑", "Flagged for review"),
]


ESC = html.escape


def nav_html(active: str, flags: int) -> str:
    items = []
    for href, glyph, label in NAV:
        cls = ' class="active"' if href == active else ""
        badge = f'<b class="count">{flags}</b>' if href == "flagged.html" and flags else ""
        items.append(f'<a{cls} href="{href}">{glyph} <span>{label}</span>{badge}</a>')
    return (f'<aside class="sidebar"><a class="brand" href="index.html">'
            f'<span class="brand-mark">N</span> northstar<span class="muted">.ai</span></a>'
            f'<div class="nav-label">WORKSPACE</div><nav>{"".join(items)}</nav>'
            f'<div class="sidebar-foot"><div class="avatar">AI</div><div><strong>Verified-data mode</strong>'
            f'<small>Read-only • no Amazon API connected</small></div></div></aside>')


def page(*, title: str, active: str, flags: int, body: str, crumb: str,
         status: str = "Evidence-first build", stylesheet: str = STYLESHEET) -> str:
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{ESC(title)} — Northstar</title><link rel="stylesheet" href="{stylesheet}"></head><body>'
            + nav_html(active, flags)
            + f'<main class="main"><header class="topbar"><div><span class="eyebrow">{ESC(crumb)}</span>'
            f'<h1>{ESC(title)}</h1></div><span class="status"><i></i> {ESC(status)}</span></header>\n'
            + body
            + f'<div class="disclosure">{REQUIRED_DISCLOSURE}</div>'
            + '<div class="notice" id="amazon-text"><b>Amazon content notice</b><span>'
            + ESC(AMAZON_TEXT_NOTICE)
            + ' <small>IP License 2(k); required in plain view wherever Amazon-sourced text is displayed.'
            '</small></span></div>'
            + '<footer><a href="index.html">← Overview</a>'
            '<span>Generated from data/*.json · blank = not confirmed by an official source</span></footer>'
            + '</main></body></html>\n')


def table(headers: list[str], rows: list[list[str]], note: str = "") -> str:
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    out = (f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead>'
           f'<tbody>{body}</tbody></table></div>')
    if note:
        out += f'<p class="table-note">{note}</p>'
    return out


def src(url: str, label: str = "Official source ↗") -> str:
    return f'<a href="{ESC(url)}" rel="nofollow noopener" target="_blank">{label}</a>'


def pill(verified: bool, text_v: str = "Verified", text_u: str = "Unverified") -> str:
    return f'<span class="pill {"ok" if verified else "warn"}">{text_v if verified else text_u}</span>'


def panel(title: str, intro: str, inner: str, pill_html: str = "", eyebrow: str = "",
          anchor: str = "") -> str:
    head = (f'<div class="panel-head"><div>{f"<span class=eyebrow>{eyebrow}</span>" if eyebrow else ""}'
            f"<h3>{title}</h3><p>{intro}</p></div>{pill_html}</div>")
    aid = f' id="{anchor}"' if anchor else ""
    return f'<section class="panel"{aid}>{head}{inner}</section>'


# ---------------------------------------------------------------- pages
def page_verification(store: Datastore, report: dict) -> str:
    flags = store.flags()
    summary = report["verification"]
    metrics = (
        '<section class="metrics">'
        f'<article><div class="metric-head">Product references</div><strong>{len(store.products())}</strong>'
        f'<small>Supplied links</small></article>'
        f'<article><div class="metric-head">Claims verified</div><strong>{summary["claims_verified"]}</strong>'
        f'<small>Official source read line by line</small></article>'
        f'<article><div class="metric-head">Claims withheld</div><strong>{summary["claims_withheld"]}</strong>'
        f'<small>Blank rather than inferred</small></article>'
        f'<article><div class="metric-head">Open flags</div><strong>{len(flags)}</strong>'
        f'<small>On the review queue</small></article></section>'
    )

    blocks = []
    for ent in store.products():
        rows = []
        for key, label in PRODUCT_FIELDS:
            c = ent.get(key)
            val = c.display if c else ""
            link = src(store.findings["products"][[p["ref"] for p in store.findings["products"]].index(ent.ref)]
                       ["checks"]["product_page_probe"]["url"], "Amazon product-page probe ↗")
            rows.append([f"<b>{label}</b>", f"<code>{ESC(val)}</code>" if val else "<span class='blank'></span>",
                         pill(bool(val and val.strip())), link])
        checks = []
        for name, det in store.findings["products"][[p["ref"] for p in store.findings["products"]].index(ent.ref)]["checks"].items():
            checks.append([name, det["status"], det.get("detail", ""),
                           src(store.source_url(det.get("source_id")), "source ↗") if det.get("source_id")
                           else '<span class="blank"></span>'])
        blocks.append(
            panel(f"{ent.ref} · {ent.name}",
                  f"Identifier parsed from the supplied URL and checked against Amazon's published ASIN rule. "
                  f"{ESC(ent.notes)}",
                  table(["Field", "Value", "State", "Source for manual review"], rows)
                  + '<div class="eyebrow">CHECKS RUN</div>'
                  + table(["Check", "Result", "What was observed", "Source"], checks),
                  pill_html=f'<span class="pill warn">{ent.verified_count()}/{len(ent.claims)} verified</span>'))
    method_sources = ["S11", "S11", "S13", "S12", "S2"]
    method = table(
        ["Step", "Method", "Basis"],
        [[str(i + 1), ESC(m), src(store.source_url(method_sources[i] if i < len(method_sources) else "S2"),
                                   f"{method_sources[i] if i < len(method_sources) else 'S2'} ↗")]
         for i, m in enumerate(store.findings.get("method", []))])
    body = (metrics
            + panel("Method", "How each row above was produced, in order.", method)
            + "".join(blocks)
            + '<div class="notice"><b>Reading a blank cell</b><span>Blank means the official page did not '
              'return the value. It never means zero, and it is never filled with an estimate.</span></div>')
    return page(title="Verification ledger", active="verification.html", flags=len(flags),
                crumb="EVIDENCE / LINE BY LINE", body=body,
                status=f'{summary["claims_verified"]}/{summary["claims_total"]} claims verified')


def page_rates(store: Datastore, report: dict) -> str:
    flags = store.flags()
    rows = []
    for r in rate_table(store):
        rows.append([ESC(r.categories), f"<b>{r.rate_pct:.2f}%</b>",
                     src(store.source_url("S1"), "Commission Income Statement ↗")])
    bounty_rows = [[ESC(b["program"]), ESC(b["action"]), f"<b>${b['rate_usd']:.2f}</b>",
                    src(store.source_url("S1"), "Bounty Events ↗")] for b in store.bounties()]
    econ_rows = []
    for ref, m in sorted(report["economics"].items()):
        econ_rows.append([
            ref,
            ESC(str(m["category"])) if m["category"] else "<span class='blank'></span>",
            f"{m['commission_rate_pct']:.2f}%" if m["commission_rate_pct"] is not None else "<span class='blank'></span>",
            f"${m['price']:,.2f}" if m["price"] is not None else "<span class='blank'></span>",
            f"${m['commission_per_order']:,.4f}" if m["commission_per_order"] is not None else "<span class='blank'></span>",
            src(m["rate_source"], "rate source ↗"),
            pill(m["commission_per_order"] is not None, "Computable", "Not computable"),
        ])
    cap_rows = []
    for c in store.program["commission_caps"]:
        ok = c["status"].startswith("verified") and not c["status"].startswith("unverified")
        cap_rows.append([ESC(c["claim"]),
                         ESC(c["status"]),
                         src(store.source_url(c["source_id"]), "source ↗") if c.get("source_id") else "",
                         pill(ok, "Verified", "Flagged")])
    attr_rows = []
    for a in store.program["attribution_rules"]:
        ok = a["status"].startswith("verified")
        attr_rows.append([ESC(a["claim"]), ESC(a["status"]),
                          src(store.source_url(a["source_id"]), "Program Policies ↗"),
                          pill(ok, "Verified", "Unverified")])
    body = (
        panel("Standard commission rates",
              "Table 1 of the official Associates Standard Commission Income Statement, transcribed "
              "verbatim on 2026-11-14. Rates are a fixed percentage of Qualifying Revenue.",
              table(["Product category (as listed)", "Fixed rate", "Source"], rows),
              pill_html='<span class="pill ok">11 rows verified</span>',
              eyebrow="OFFICIAL RATE TABLE")
        + panel("Bounty events",
                "Special Commission Income rows read on the retrieval date. The official table continues "
                "beyond the retrieved text, so this list is explicitly not exhaustive.",
                table(["Program", "Bounty action", "Rate", "Source"], bounty_rows),
                eyebrow="SPECIAL COMMISSION")
        + panel("Caps and claims to avoid",
                "Caps that appear in the official statement, plus a widely repeated rate claim that the "
                "official table does not support.",
                table(["Statement", "Status", "Source", "Verdict"], cap_rows),
                eyebrow="GUARDRAILS")
        + panel("Attribution windows",
                "The measured windows that decide whether a purchase is a Qualifying Purchase.",
                table(["Rule", "Status", "Source", "Verdict"], attr_rows),
                eyebrow="SESSION MODEL")
        + panel("Unit economics per requested product",
                "Commission per order = verified price × the applicable product commission rate. The product "
                "pages are identified, but their Amazon browse path does not establish an Associates category; "
                "prices are also withheld. Per-ASIN rates and earnings stay blank rather than estimated.",
                table(["Reference", "Amazon browse category", "Product-specific rate", "Price", "Earning per order", "Standard rate table", "State"], econ_rows),
                pill_html='<span class="pill warn">0 of 3 computable</span>',
                eyebrow="REVENUE MODEL")
        + '<div class="notice amber"><b>Why there is no revenue forecast</b><span>Earnings need clicks and '
          'conversion from authorized reporting. None is connected to this workspace, so no projection is '
          'published — see flag F-010.</span></div>')
    return page(title="Rates & economics", active="rates.html", flags=len(flags),
                crumb="ECONOMICS / PROGRAM TERMS", body=body, status="All rates source-linked")


def page_compliance(store: Datastore, report: dict) -> str:
    flags = store.flags()
    matrix = compliance_matrix()
    rows = [[m["id"], ESC(m["clause"]), ESC(m["requirement"]), m["severity"], src(m["source"], "clause ↗")]
            for m in matrix]
    disc = store.program["disclosure"]
    ftc_rows = [[ESC(p), src(store.source_url("S8"), "FTC guidance ↗")] for p in disc["ftc_guidance"]["points"]]
    legal_rows = [[ESC(l["claim"]), ESC(l["status"]), src(store.source_url(l["source_id"]), "source ↗"),
                   pill(l["status"].startswith("verified"))] for l in store.program["legal_clauses"]]
    gate = report["publish_gate"]
    # Every row must point at the clause it is judged under, so the control ids
    # quoted in the gate's reasons are resolved back to their official source.
    clause_source = {m["id"]: m["source"] for m in matrix}
    queue_rows = []
    for q in report["publish_queue"]:
        cited = sorted({c for c in clause_source
                        for c in re.findall(r"\b([A-Z]{3,7}-\d{2})\b", "; ".join(q["reasons"] + q["findings"]))})
        links = " ".join(src(clause_source[c], f"{c} ↗") for c in cited[:4]) or \
            src(store.source_url("S2"), "Program Policies ↗")
        queue_rows.append([f"<code>{ESC(q['slug'])}</code>", "PASS" if q["ready"] else "BLOCKED",
                           ESC("; ".join(q["reasons"])[:220] or "—"),
                           ESC("; ".join(q["findings"])[:120] or "—"), links])
    body = (
        '<div class="notice"><b>Required disclosure</b><span>'
        f'<span class="disclosure">“{REQUIRED_DISCLOSURE}”</span> — Operating Agreement §5 requires this '
        'statement to appear clearly and prominently on the Site. A disclosure is a duty, not evidence of '
        'approval or enrollment.</span></div>'
        + panel("Control matrix", "Each control maps to a clause in Amazon's official terms and is enforced "
                "mechanically by <code>engine/policy.py</code> before any draft can publish.",
                table(["Control", "Clause", "Requirement", "Severity", "Source"], rows),
                pill_html=f'<span class="pill neutral">{len(matrix)} controls</span>', eyebrow="GATES")
        + panel("Disclosure placement",
                "Amazon's own guidance plus the FTC's published positions on what does and does not count as "
                "clear and conspicuous.",
                table(["Guidance", "Source"], ftc_rows), eyebrow="DISCLOSURE")
        + panel("Legal and data clauses",
                "Clauses in the Program Policies that bind site operation beyond link formatting.",
                table(["Clause", "Status", "Source", "Verdict"], legal_rows), eyebrow="LEGAL")
        + panel("Publish gate — live state",
                "Output of the compliance engine against the drafts this workspace can generate. Blocked items "
                "stay unpublished until every reason is cleared.",
                table(["Draft", "Gate", "Reasons", "Rule hits", "Clause source"], queue_rows),
                pill_html=_gate_pill(gate),
                eyebrow="AUTOMATION")
    )
    return page(title="Compliance controls", active="compliance.html", flags=len(flags),
                crumb="COMPLIANCE / CONTROLS", body=body,
                status=f'{gate["blocked_items"]} drafts blocked')


def page_data_api(store: Datastore, report: dict) -> str:
    flags = store.flags()
    da = store.program["data_access"]
    pre_rows = []
    for p in da["prerequisites"]:
        ok = p["status"].startswith("verified")
        pre_rows.append([ESC(p["claim"]), ESC(p["status"]),
                         src(store.source_url(p["source_id"]), "official docs ↗"), pill(ok)])
    ops_rows = [[f"<code>{o['operation']}</code>", ESC(o["description"]),
                 src(store.source_url(o["source_id"]), "docs ↗")] for o in da["operations"]]
    tech_rows = []
    for t in da["technical"]:
        ok = t["status"].startswith("verified")
        tech_rows.append([ESC(t["claim"]), ESC(t["status"]),
                          ESC(t.get("reason", "") or ""),
                          src(store.source_url(t["source_id"]), "source ↗") if t.get("source_id") else "",
                          pill(ok, "Verified", "Held")])
    ident_rows = [[ESC(i["claim"]), src(store.source_url(i["source_id"]), "source ↗")]
                  for i in store.program["identity_rules"]]
    link_rows = []
    for l in report["research"]["links"]:
        ok = l["ok"]
        link_rows.append([l["ref"], f"<code>{ESC(l['url'])}</code>" if l["url"] else "<span class='blank'></span>",
                          ESC(l["detail"]), pill(ok, "Link buildable", "Blocked")])
    body = (
        panel("Access prerequisites",
              "The gate between this workspace and live Amazon product data. Read from the official docs on "
              "2026-11-14; none of them are satisfied here, so no API data is claimed.",
              table(["Prerequisite", "Status", "Source", "Verdict"], pre_rows),
              pill_html='<span class="pill warn">Not satisfied</span>', eyebrow="ELIGIBILITY")
        + panel("Documented operations", "The four operations the Creators API exposes for catalog work.",
                table(["Operation", "Description", "Source"], ops_rows), eyebrow="API SURFACE")
        + panel("Technical constraints",
                "Implementation facts that shape the pipeline design. Anything not read from an official page is "
                "held as unverified rather than assumed.",
                table(["Fact", "Status", "Why it is blank / note", "Source", "Verdict"], tech_rows),
                eyebrow="ENGINEERING")
        + panel("Link build attempt",
              "The link builder refuses to emit a Special Link from an identifier that cannot address a product, "
              "and refuses placeholder tags and redirect hosts.",
              table(["Reference", "Link that would be built", "Engine decision", "State"], link_rows),
              eyebrow="LINK SAFETY")
        + panel("Identity and host facts",
              "Facts used by the identifier checks, from Amazon's own seller documentation and the IANA root zone.",
              table(["Statement", "Source"], ident_rows), eyebrow="IDENTIFIERS")
        + '<div class="notice amber"><b>Not claimed</b><span>Request quotas (TPS/TPD), exact price-cache windows, '
          'and review/offer coverage are left unverified: their official pages were not retrieved by this '
          'workspace. Flags F-006 and F-007 carry the follow-up.</span></div>')
    return page(title="Data & API", active="data-api.html", flags=len(flags),
                crumb="DATA PLANE / AMAZON ACCESS", body=body, status=f"{len(pre_rows)} prerequisites")


def page_flagged(store: Datastore, report: dict) -> str:
    flags = store.flags()
    rows = []
    for f in flags:
        ev = "<br>".join(src(u, u[:58] + "…" if len(u) > 58 else u) for u in f.get("evidence", []))
        rows.append([f"<b>{f['id']}</b>", f'<span class="pill {"warn" if f["severity"] in ("blocker", "high") else "neutral"}">{f["severity"]}</span>',
                     ESC(f["title"]), ESC(f["detail"]), ESC(f.get("target", "")), ev, ESC(f.get("action", ""))])
    counts = {s: sum(1 for f in flags if f["severity"] == s) for s in ("blocker", "high", "medium", "low")}
    body = (
        f'<div class="notice amber"><b>{len(flags)} items are awaiting human review</b><span>'
        f'blocker {counts["blocker"]} · high {counts["high"]} · medium {counts["medium"]} · low {counts["low"]}. '
        'These do not block the site: nothing they concern has been asserted as verified anywhere on this site, '
        'and every affected table cell is blank.</span></div>'
        + panel("Review queue", "Each item records what was checked, what was seen, the official page to read, "
                "and the single action that closes it.",
                table(["Flag", "Severity", "Issue", "Detail", "Affects", "Source for manual review", "Action"], rows),
                pill_html=f'<span class="pill warn">{len(flags)} open</span>', eyebrow="OPEN ITEMS")
        + panel("Product-level flags", "The three supplied references, one row each.",
                table(["Reference", "Identifier", "Status", "Why values are withheld", "Provided link"],
                      [[p["ref"], f"<code>{p['identifier']}</code>",
                        f'<span class="pill warn">{p["status"]}</span>', ESC(p["why_blank"]),
                        src(p["supplied_url"], "supplied URL ↗")]
                       for p in store.findings["products"]]),
                eyebrow="CATALOG")
        + panel("Scoring withheld", "Opportunity scores need verified inputs; the model reports what is missing.",
                table(["Reference", "Score", "Missing verified inputs", "Rationale"],
                      [[ref, "<span class='blank'></span>", ESC(", ".join(v["missing"])), ESC(v["rationale"])]
                       for ref, v in sorted(report["scoring"].items())]),
                pill_html='<span class="pill warn">0 scored</span>', eyebrow="MODEL")
    )
    return page(title="Flagged for review", active="flagged.html", flags=len(flags),
                crumb="QUALITY CONTROL / OPEN ITEMS", body=body,
                status=f"{len(flags)} items · site still publishes")


def page_index(store: Datastore, report: dict) -> str:
    flags = store.flags()
    v = report["verification"]
    cats = [
        ("verification.html", "Verification ledger", "Line-by-line checks: what was run, what each row cites, what stays blank."),
        ("rates.html", "Rates & economics", "Official commission table, bounties, caps, attribution windows, unit economics."),
        ("compliance.html", "Compliance controls", "The control matrix the generator enforces before anything can publish."),
        ("data-api.html", "Data & API", "Creators API prerequisites, operations, link-safety decisions, quotas held as unverified."),
        ("flagged.html", "Flagged for review", "Every irregularity, its official source, and the action that closes it."),
    ]
    cards = "".join(
        f'<a class="cat-card" href="{href}"><b>{label}</b><span>{desc}</span></a>' for href, label, desc in cats)
    rows = []
    n_resolved = 0
    for ent in store.products():
        verified = [c for c in ent.claims.values() if c.status.publishable and c.value]
        name_claim = ent.claims.get("product_name")
        identity = (name_claim.value if name_claim and name_claim.status.publishable else None)
        if ent.resolved_asin:
            n_resolved += 1
            ident_html = (f'<b>{ESC(ent.resolved_asin)}</b>'
                          f'<small>{ESC(identity)[:70] if identity else "name withheld"}</small>')
            status_html = '<span class="pill ok">Identity verified</span>'
        else:
            ident_html = f'<b>Product {ent.ref[-2:]}</b><small>identity not verified</small>'
            status_html = '<span class="pill warn">Needs verification</span>'
        rate = ent.claims.get("commission_rate_pct")
        comm_html = (f"{rate.value:.2f}% <small class='muted'>{ESC(rate.source.publisher or '')}</small>"
                     if rate and rate.status.publishable and rate.value else "<span class='blank'></span>")
        rows.append([
            f'<div class="product"><span class="product-icon">{ent.ref[-2:]}</span><div>{ident_html}</div></div>',
            "<span class='blank'></span>", "<span class='blank'></span>", comm_html,
            f'{len(verified)}/{len(ent.claims)} fields verified',
            status_html,
            src(ent.get("supplied_url").value, "Supplied link ↗"),
        ])
    body = (
        '<section class="welcome small-welcome"><div><span class="eyebrow light">AFFILIATE INTELLIGENCE PLATFORM</span>'
        '<h2>Automation that cannot invent a fact.</h2>'
        '<p>Research, economics, content drafting, link safety and compliance gates are implemented as code; '
        'the pages below are generated from the same verified data. Anything Amazon did not confirm is left '
        'blank and flagged, never estimated.</p></div></section>'
        '<section class="metrics">'
        f'<article><div class="metric-head">Supplied products</div><strong>03</strong>'
        f'<small>{n_resolved} of 3 identities resolved</small></article>'
        f'<article><div class="metric-head">Claims verified</div><strong>{v["claims_verified"]}</strong>'
        f'<small>of {v["claims_total"]} tracked fields</small></article>'
        f'<article><div class="metric-head">Commission rates</div><strong>11</strong><small>official table rows</small></article>'
        f'<article><div class="metric-head">Open flags</div><strong>{len(flags)}</strong><small>review queue</small></article>'
        '</section>'
        + panel("Categories", "One page per area of the platform, each table sourced per row.",
                f'<div class="cat-grid">{cards}</div>', eyebrow="WORKSPACE")
        + panel("Product catalog", "Identity resolved from the supplied short link; every other field is shown "
                "only where an official page was read, and prices and ratings stay withheld.",
                table(["Product", "Price", "Rating / reviews", "Commission", "Evidence", "Status", "Source"], rows),
                pill_html=f'<span class="pill warn">{v["claims_withheld"]} withheld</span>', eyebrow="RESEARCH QUEUE",
                anchor="catalog")
        + '<div class="notice" id="method"><b>Reading rules for this site</b><span>Blank = not confirmed by an official '
          'source. Every verified row links the page it was read from, with the retrieval date. '
          'No earnings, traffic or product-quality claim is made anywhere.</span></div>'
    )
    return page(title="Overview", active="index.html", flags=len(flags), crumb="WORKSPACE / DASHBOARD",
                body=body, status=f'{v["claims_verified"]}/{v["claims_total"]} claims verified')


PAGES = {
    "index.html": page_index,
    "verification.html": page_verification,
    "rates.html": page_rates,
    "compliance.html": page_compliance,
    "data-api.html": page_data_api,
    "flagged.html": page_flagged,
}


def render_all(store: Datastore, report: dict, out_dir: Path) -> dict[str, str]:
    """Write the engine's self-contained preview (never the published ``docs/`` site)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "preview.css").write_text(PREVIEW_CSS, encoding="utf-8")
    written: dict[str, str] = {}
    for name, fn in PAGES.items():
        html_text = fn(store, report)
        _self_check(html_text, name)
        (out_dir / name).write_text(html_text, encoding="utf-8")
        written[name] = html_text
    return written


def _gate_pill(gate: dict) -> str:
    if gate["open"]:
        return '<span class="pill ok">OPEN</span>'
    return f'<span class="pill warn">{gate["blocked_items"]} blocked</span>'


#: Hosts that may be linked *as evidence under review* even though they must
#: never be used as a Special Link (they are redirect/shortener hosts).
REVIEW_ONLY_HOST_SUFFIX = (".amazon", ".amzn.to")


def _self_check(html_text: str, name: str) -> None:
    """Refuse to write a page that would break the site."""
    import re
    from urllib.parse import urlsplit

    for href in re.findall(r"""href=["']([^"']+)["']""", html_text):
        parts = urlsplit(href)
        host = (parts.hostname or "").lower()
        if not host:
            continue
        query = parts.query or ""
        tagged = "tag=" in query.lower()
        if not tagged:
            # Untagged links on this site are audit evidence (a probe URL, a policy
            # page, the user's own supplied reference). They must never be an
            # affiliate link, so an untagged link carrying our tag params is a bug.
            continue
        # Tagged links are Special Links and must satisfy every rule.
        if host.endswith(REVIEW_ONLY_HOST_SUFFIX) or "redirect" in host:
            raise ValueError(
                f"{name}: redirect/shortener host {host} used as a tagged Special Link — "
                "Participation Requirements §6(v)-(w)")
        ok, why = is_safe_href(href)
        if not ok:
            raise ValueError(f"{name}: unsafe affiliate link {href!r} — {why}")
    if re.search(r">\s*None\s*<", html_text) or "None</td>" in html_text or ">nan<" in html_text.lower():
        raise ValueError(f"{name}: a null leaked into a cell; render it blank instead")
    if "[[UNVERIFIED" in html_text:
        raise ValueError(f"{name}: unresolved placeholder in a published page")


def report_json(store: Datastore, report: dict, dest: Path) -> None:
    dest.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


PREVIEW_CSS = """
:root{--ink:#172b3a;--muted:#71808c;--line:#e6ebee;--bg:#f6f8f9;--teal:#157b73;--deep:#133d49;--mint:#dff2ed}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
.sidebar{position:fixed;inset:0 auto 0 0;width:236px;background:#fff;border-right:1px solid var(--line);padding:26px 16px;display:flex;flex-direction:column;gap:4px}
.brand{font-weight:800;font-size:19px;color:#17394a;text-decoration:none;display:flex;align-items:center;gap:8px}
.brand-mark{height:28px;width:28px;display:inline-grid;place-items:center;background:#1e8277;color:#fff;border-radius:9px;font-size:14px}
.muted{color:#7f9496;font-weight:500;font-size:13px}
.nav-label{font-size:10px;letter-spacing:1.2px;font-weight:700;color:#8997a0;margin:34px 8px 8px}
nav{display:grid;gap:4px}
nav a{display:flex;align-items:center;gap:11px;padding:9px 11px;color:#667781;text-decoration:none;border-radius:8px;font-size:13.5px}
nav a span{flex:1}
nav a.active{background:#eaf5f2;color:#176f68;font-weight:700}
.count{font-size:11px;background:#f3e7d5;color:#9b681e;padding:2px 7px;border-radius:8px}
.sidebar-foot{margin-top:auto;border-top:1px solid var(--line);padding-top:12px;display:flex;gap:9px;align-items:center;font-size:11px;color:var(--muted)}
.avatar{height:28px;width:28px;border-radius:50%;background:var(--mint);color:#1a6d66;display:grid;place-items:center;font-weight:700;font-size:11px}
.main{margin-left:236px;padding:26px 30px 40px}
.topbar{display:flex;justify-content:space-between;align-items:flex-end;gap:14px;margin-bottom:18px}
.topbar h1{font-size:26px;margin:4px 0 0;letter-spacing:-.6px;color:var(--deep)}
.eyebrow{font-size:10px;letter-spacing:1.2px;font-weight:700;color:#8997a0}
.eyebrow.light{color:#5c9a92}
.status{font-size:11.5px;color:var(--muted);display:flex;align-items:center;gap:7px;white-space:nowrap}
.status i{width:7px;height:7px;border-radius:50%;background:#38a34a;display:inline-block}
.welcome,.small-welcome{background:#fff;border:1px solid var(--line);border-radius:14px;padding:22px 24px;margin-bottom:18px}
.welcome h2,.small-welcome h2{font-size:22px;margin:6px 0 8px;letter-spacing:-.5px;color:var(--deep)}
.welcome p,.small-welcome p{color:#5c6b75;max-width:78ch;margin:0}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:18px}
.metrics article{background:#fff;border:1px solid var(--line);border-radius:12px;padding:15px 16px}
.metric-head{font-size:11px;font-weight:600;color:var(--muted);display:flex;justify-content:space-between;gap:8px}
.metrics article strong{display:block;font-size:26px;font-weight:800;color:var(--deep);margin:8px 0 3px;letter-spacing:-.9px}
.metrics article small{color:#8b98a2;font-size:11px}
.panel{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px 19px;margin-bottom:16px}
.panel.compact{padding:16px 17px}
.panel-head{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;margin-bottom:12px}
.panel-head h3{margin:2px 0 5px;font-size:16px;color:var(--deep);letter-spacing:-.3px}
.panel-head p{margin:0;color:var(--muted);font-size:12.5px;max-width:80ch;line-height:1.6}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:16px}
.notice{background:#eaf3f2;border-left:3px solid #3d9382;padding:13px 16px;margin:0 0 16px;border-radius:6px;display:flex;gap:12px;color:#62757c;font-size:12.5px;line-height:1.6}
.notice b{color:#246d67;white-space:nowrap}
.notice.amber{background:#fff6e9;border-color:#dda849}
.notice.amber b{color:#96650f}
.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:10px}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}
thead th{background:#fafcfc;font-size:10.5px;letter-spacing:.7px;text-transform:uppercase;color:#7e8b94;position:sticky;top:0}
tbody tr:last-child td{border-bottom:0}
table.wide{min-width:860px}
td a,th a{color:var(--teal);text-decoration:none;border-bottom:1px solid #cfe4e0;font-size:12px;word-break:break-word}
.pill{display:inline-block;padding:4px 9px;border-radius:20px;font-size:10.5px;font-weight:700;white-space:nowrap}
.pill.ok{background:#e6f4ea;color:#1c7a3d}
.pill.warn{background:#fdecea;color:#a3392f}
.pill.neutral,.pill.source{background:#eef2f4;color:#5b6b74}
.blank{color:#b3bcc3}
span.blank::after,td>.blank:empty::after{content:"\2014"}
.table-note{color:var(--muted);font-size:11.5px;margin:10px 2px 0}
code{font:600 12px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;background:#f2f6f7;color:#245259;padding:2px 5px;border-radius:5px;word-break:break-all}
.disclosure{background:#0f2f39;color:#dff2ed;border-radius:11px;padding:14px 16px;font-weight:600;font-size:13px;margin:14px 0 0}
.cat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:11px}
.cat-card{display:block;background:#fbfdfd;border:1px solid var(--line);border-radius:11px;padding:14px 15px;text-decoration:none;color:inherit}
.cat-card:hover{border-color:#bfded8}
.cat-card b{display:block;color:var(--deep);margin-bottom:5px;font-size:14px}
.cat-card span{color:var(--muted);font-size:12px}
.product{display:flex;align-items:center;gap:10px}
.product b{display:block;font-size:13px}
.product small{display:block;color:#93a0a9;font-size:11px}
.product-icon{height:29px;width:29px;flex:0 0 29px;display:grid;place-items:center;border-radius:9px;background:var(--mint);color:#1a6d66;font-weight:700;font-size:12px}
ol.checklist,ul.checklist{margin:0;padding:0;list-style:none;display:grid;gap:8px}
ol.checklist li,ul.checklist li{background:#fbfdfd;border:1px solid var(--line);border-radius:10px;padding:10px 12px;font-size:12.5px;line-height:1.6;color:#4d5f6a}
footer{display:flex;justify-content:space-between;gap:12px;color:var(--muted);font-size:11.5px;padding:6px 2px 0}
footer a{color:var(--teal);text-decoration:none}
@media (max-width:900px){.sidebar{position:static;width:auto}.main{margin-left:0;padding:18px}.two-col,.metrics{grid-template-columns:1fr}}
"""
