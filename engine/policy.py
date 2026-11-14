"""Compliance gates derived clause-by-clause from Amazon's official terms.

Every rule cites the clause it came from (Program Policies → "Associates
Program Participation Requirements", and the Operating Agreement). The gates are
*blocking*: ``agent.publish_queue`` will not emit a draft that fails one, and the
site build fails if a published page would.

This is a mechanical pre-screen for the operator, not legal advice, and not a
substitute for reading the current terms.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit

REQUIRED_DISCLOSURE = "As an Amazon Associate I earn from qualifying purchases."

#: IP License 2(k): plain-view notice required whenever Program Content
#: consisting of text (a listing title, a specification line) is displayed.
AMAZON_TEXT_NOTICE = ("CERTAIN CONTENT THAT APPEARS ON THIS SITE COMES FROM AMAZON. THIS CONTENT IS PROVIDED "
                      "AS IS AND IS SUBJECT TO CHANGE OR REMOVAL AT ANY TIME.")

#: FTC-endorsed short forms (source S8: "'Paid link' right next to an affiliate
#: link should be an adequate disclosure of the nature of the link").
LINK_LEVEL_TOKENS = ("paid link", "#ad", "#commissionsearned", "affiliate link", "sponsor")

# Amazon destinations are recognised by *registrable domain*, not by substring:
# "amazon.example.org" must not pass while "amazon.co.uk" and hosts under Amazon's
# delegated ".amazon" gTLD (source S12) must.

def is_amazon_host(host: str | None) -> bool:
    """True when the host's registrable domain is an Amazon one.

    Accepts ``amazon.<tld>``, ``amazon.<cc>.<tld>``, any subdomain of those, and
    any host under Amazon's ``.amazon`` gTLD (source S12) — e.g. ``link.amazon``.
    Rejects look-alikes such as ``notamazon.com`` and ``amazon.example.org``.
    """
    if not host:
        return False
    labels = [l for l in host.lower().strip(".").split(".") if l]
    if not labels:
        return False
    if labels[-1] == "amazon":                       # <anything.>amazon  (gTLD)
        return True
    if host.lower() in {"amzn.to", "www.amzn.to"}:  # Amazon's own shortener
        return True
    if len(labels) >= 2 and labels[-2] == "amazon" and re.fullmatch(r"[a-z]{2,6}", labels[-1]):
        return True                                   # amazon.com / amazon.co.uk subdomains
    if len(labels) >= 3 and labels[-3] == "amazon" \
            and re.fullmatch(r"[a-z]{2}", labels[-2]) and re.fullmatch(r"[a-z]{2}", labels[-1]):
        return True                                   # amazon.co.uk, amazon.com.br
    return False


def mentions_amazon(text: str) -> bool:
    """True when any URL in the document points at an Amazon host."""
    for raw in re.findall(r"""["'(](?:https?:)?//([^/"'\s>]+)""", text or "", re.I):
        host = raw.split("@")[-1].split(":")[0].strip().lower()
        if is_amazon_host(host):
            return True
    return False


@dataclass
class Rule:
    id: str
    clause: str
    summary: str
    severity: str = "blocking"
    source_url: str = "https://affiliate-program.amazon.com/help/operating/policies"

    @property
    def key(self) -> str:
        return self.id


#: Titles this workspace reproduces verbatim from Amazon listings. Populated by
#: engine.content when it builds drafts, so the §2(k) check knows what counts as
#: Program Content text without hard-coding product names into the policy module.
PROGRAM_TEXT: set[str] = set()


def register_program_text(value: str | None) -> None:
    if value:
        PROGRAM_TEXT.add(value)


class _ProgramText(list):
    """Read-only view kept for the detector above; a list so order is stable."""

    def __iter__(self):
        return iter(sorted(PROGRAM_TEXT))

    def __bool__(self):
        return bool(PROGRAM_TEXT)


_PROGRAM_TEXT = _ProgramText()

RULES: list[Rule] = [
    Rule("DISC-01", "Operating Agreement §5", "Required identification statement must appear on the Site, clear and prominent.", source_url="https://affiliate-program.amazon.com/help/operating/agreement"),
    Rule("DISC-02", "Participation Requirements (help topic GHQNZAU6669EZS98)", "Link-level disclosure must be clear and conspicuous, placed near the link/review.", source_url="https://affiliate-program.amazon.com/help/node/topic/GHQNZAU6669EZS98"),
    Rule("LINK-01", "Participation Requirements §6(v)", "No cloaking/hiding/spoofing of the URL containing Special Links, incl. Redirecting Links.", ),
    Rule("LINK-02", "Participation Requirements §6(w)", "No link shortener/button/hyperlink used so that the Amazon destination is unclear."),
    Rule("LINK-03", "Participation Requirements §6(n)", "No framing of an Amazon Site inside the Site (incl. WebView)."),
    Rule("LINK-04", "Participation Requirements §6(o)", "No Special Links in pop-under/layer ads or transitional page ads."),
    Rule("LINK-05", "Participation Requirements §6(q)", "No opening Amazon pages other than by the customer clicking a Special Link."),
    Rule("TRAF-01", "Participation Requirements §6(s)", "No artificially generated clicks/impressions or Sessions (robots, scripts, self-clicks).", ),
    Rule("TRAF-02", "Participation Requirements §6(u)", "No self-purchases or friend/family/employee purchases through Special Links; no resale."),
    Rule("TRAF-03", "Participation Requirements §6(g)", "No reward, rebate, points, donation, or incentive for using Special Links."),
    Rule("PRICE-01", "Participation Requirements §6(y)", "Site must not have price tracking / price alerting functionality absent Amazon agreement."),
    Rule("DATA-01", "Participation Requirements §6(P-ml)", "Program Content / Special Links must not be used to develop machine-learning models without prior written approval."),
    Rule("DATA-02", "Participation Requirements §6(a) content", "No adding to / altering Program Content beyond proportional resize or non-meaning-changing truncation."),
    Rule("DATA-03", "Participation Requirements §6(P-stale)", "Program Content no longer available on Amazon must be promptly removed and destroyed."),
    Rule("DATA-04", "Participation Requirements §6(t)", "Reviews/star ratings may only be shown when obtained via Creators API / PA API."),
    Rule("TEXT-01", "IP License §2(k)", "When Product Advertising Content consisting of text is displayed, the Amazon 'AS IS / subject to change' notice must appear in plain view."),
    Rule("AGENT-01", "IP License §4 (Agent Terms)", "An automated agent accessing Program Content must identify itself as an agent (Agent/<name> in the user agent) and must not conceal that it is an agent or circumvent access limits."),
    Rule("OFFLINE-01", "Participation Requirements §4", "No offline promotion: print, ebook, mailing, oral solicitation, or Amazon marks with Special Links."),
    Rule("OFFLINE-02", "Participation Requirements §4", "Email/SMS/DM with Special Links only when solicited (recipient opted in)."),
    Rule("CHANNEL-01", "Participation Requirements §6(p)", "No Special Links inside content placed on an Amazon Site (reviews, forums, Wish Lists, guides)."),
    Rule("CHANNEL-02", "Participation Requirements §5", "No client-side software (extensions/toolbar/plug-in) or TV set-top/CTV placements outside Approved Mobile Apps."),
    Rule("SEARCH-01", "Participation Requirements §6(f)", "No bidding on Amazon marks/misspellings; no Prohibited Paid Search Placement."),
    Rule("CROSS-01", "Participation Requirements §6(z)", "No using Program Content to promote competing retailers' products; no use of Excluded Products data."),
    Rule("PRIV-01", "Participation Requirements §3(b)/(e)", "Cookie/pixel disclosure and GDPR/ePrivacy compliance for visitor data."),
    Rule("ACC-01", "Participation Requirements §6(i)", "No collection/caching of Amazon customer account information."),
    Rule("API-01", "Participation Requirements §6 (account status)", "Publishing content that requires API eligibility while ineligible; see Creators API prerequisites."),
]

RULE_BY_ID = {r.id: r for r in RULES}

#: Patterns that indicate a draft is making an unbacked performance claim.
PERFORMANCE_CLAIM_RE = re.compile(
    r"(?i)\b(we (?:earn|make)[es]?|earn(?:ings|ed)? of|makes? \$|up to \$|\d+(?:\.\d+)?\s?% conversion|"
    r"guaranteed|risk[- ]free income|passive income of|\$\d[\d,\.]* per (?:month|day|sale))"
)
SUPERLATIVE_RE = re.compile(r"(?i)\b(best|top[- ]rated|#1|no\.1|most popular|number one|unbeatable|perfect)\b")
STALE_PRICE_RE = re.compile(r"(?i)\b(price drop|price alert|track (?:the )?price|notify me when|below \$\d)")


@dataclass
class Finding:
    rule_id: str
    message: str
    severity: str = "blocking"
    evidence: str = ""

    @property
    def rule(self) -> Rule:
        return RULE_BY_ID[self.rule_id]


@dataclass
class Draft:
    """Something about to be published: HTML/text + its outbound links."""

    name: str
    html: str = ""
    text: str = ""
    links: list[str] = field(default_factory=list)
    verified_sources: list[str] = field(default_factory=list)
    price_display_enabled: bool = False
    has_tracking_script: bool = False


def _all_links(draft: Draft) -> list[str]:
    hrefs = re.findall(r"""href=["']([^"']+)["']""", draft.html or "")
    return list(dict.fromkeys(list(hrefs) + list(draft.links)))


def check_disclosure(draft: Draft) -> list[Finding]:
    out: list[Finding] = []
    body = f"{draft.html}\n{draft.text}"
    if REQUIRED_DISCLOSURE.lower() not in body.lower():
        out.append(Finding("DISC-01",
                           "Required identification statement is absent from the page."))
    links = [l for l in _all_links(draft) if is_amazon_host(urlsplit(l).hostname)]
    if links and not any(tok in body.lower() for tok in LINK_LEVEL_TOKENS):
        out.append(Finding("DISC-02",
                           "Amazon links present but no clear link-level disclosure token "
                           f"(any of: {', '.join(sorted(set(LINK_LEVEL_TOKENS)))})."))
    return out


def check_links(draft: Draft) -> list[Finding]:
    out: list[Finding] = []
    for href in _all_links(draft):
        parts = urlsplit(href)
        host = (parts.hostname or "").lower()
        if not host or host.startswith("localhost"):
            continue
        if href.startswith(("javascript:", "data:")):
            out.append(Finding("LINK-01", f"Non-http link to {href!r} cannot be an auditable Special Link."))
            continue
        if not is_amazon_host(host):
            continue  # not an Amazon-bound link; other checks handle it
        q = (parts.query or "").lower()
        if "tag=" not in q and "ascsubtag" not in q and "amzn1" not in q:
            out.append(Finding("DISC-02",
                               f"Amazon link {href} carries no Associate tag, so clicks are untracked "
                               "and purchases earn nothing.", severity="warning"))
        if host.endswith(".amazon") or host.endswith(".amzn.to") or "redirect" in host or "go." in host:
            out.append(Finding("LINK-02",
                               f"'{host}' is a redirect/shortener host; embedding it as the href can make "
                               "the Amazon destination unclear (Participation Requirements §6(w)). "
                               "Link to the final amazon.com/dp/ URL instead."))
    return out


def check_prohibitions(draft: Draft) -> list[Finding]:
    out: list[Finding] = []
    body = f"{draft.html}\n{draft.text}"

    if "<iframe" in body.lower() and mentions_amazon(body):
        out.append(Finding("LINK-03", "An iframe appears alongside an Amazon URL — framing an Amazon Site is prohibited."))
    if re.search(r"(?i)pop-?under|layer ad|interstitial", body):
        out.append(Finding("LINK-04", "Pop-under / layer / interstitial placement detected next to Special Links."))
    if re.search(r"(?i)(window\.open|target=[\"']_blank[\"']).*amazon", body) and "location.href" in body.lower():
        out.append(Finding("LINK-05", "Scripted navigation to Amazon detected; pages may only open from a customer click."))
    if re.search(r"(?i)(auto(?:matically)? (?:click|visit|open)|bot traffic|click farm|proxy clicks|scripted clicks)", body):
        out.append(Finding("TRAF-01", "Language implies generated/bot clicks."))
    if re.search(r"(?i)(buy (?:it )?(?:yourself|through my link to save)|family and friends (?:to )?buy|self[- ]referral)", body):
        out.append(Finding("TRAF-02", "Encourages self/family purchases through Special Links."))
    if re.search(r"(?i)(giveaway|sweepstakes|reward points|loyalty (?:points|program)|donat\w+ per click|earn (?:points|credits) by clicking)", body):
        out.append(Finding("TRAF-03", "Incentivised clicking / reward-for-click mechanics detected."))
    if STALE_PRICE_RE.search(body) or (draft.price_display_enabled is False and re.search(r"(?i)\$\d+(?:\.\d{2})?\b", body)):
        out.append(Finding("PRICE-01", "Price tracking/alerting or a hardcoded dollar price on a page where price display is gated off (see flag F-006)."))
    if re.search(r"(?i)train(?:ing|ed|ing data)? .{0,25}(?:model|ML|machine learning)|dataset for (?:model )?training", body):
        out.append(Finding("DATA-01", "References using Program Content/links as ML training data."))
    # IP License §2(k) bites on displayed *Program Content text*, not on a page
    # that merely mentions the Associate relationship, so the trigger is a
    # verbatim Amazon listing title inside the draft. A false positive here would
    # block compliant copy, which is worse than a lint that never fires.
    quoted = [q for q in _PROGRAM_TEXT if q and q.split(" | ")[0][:40] in body]
    if quoted and "COMES FROM AMAZON" not in body.upper():
        out.append(Finding("TEXT-01", "Draft reproduces an Amazon listing title ("
                       + ", ".join(q[:28] + "…" for q in quoted[:2])
                       + ") without the IP License 2(k) plain-view notice."))
    if re.search(r"(?i)(scrap(e|ing)|crawl(er|ing)|harvest)\b", body) and mentions_amazon(body):
        out.append(Finding("AGENT-01", "Draft describes automated access to Amazon content; agent self-identification and no-circumvention terms apply."))
    if re.search(r"(?i)reviews? (?:of|from) amazon|star rating", body) and not draft.verified_sources:
        out.append(Finding("DATA-04", "Review/star-rating language with no API-sourced provenance recorded."))
    if re.search(r"(?i)(ebook|printed|newsletter \(unsubscribed\)|cold email|flyer)", body) and mentions_amazon(body):
        out.append(Finding("OFFLINE-01", "Offline/unsolicited channel referenced together with Amazon links."))
    if re.search(r"(?i)browser extension|bookmarklet|toolbar|plugin", body):
        out.append(Finding("CHANNEL-02", "Client-side software placement is prohibited outside Approved Mobile Applications."))
    if re.search(r"(?i)\bbid on\b.{0,40}\bamazon\b|keyword (?:auction|bidding).*amazon", body):
        out.append(Finding("SEARCH-01", "Paid-search bidding on Amazon marks is prohibited."))
    if re.search(r"(?i)\bvs\.? (?:walmart|ebay|aliexpress|best buy|target)\b", body) and mentions_amazon(body):
        out.append(Finding("CROSS-01", "Program Content used alongside competing-retailer promotion for the same product."))
    if re.search(r"(?i)localStorage|document\.cookie|gtag|googletagmanager|pixel", body) and not draft.verified_sources:
        out.append(Finding("PRIV-01", "Tracking technology present with no recorded cookie/consent disclosure."))
    if re.search(r"(?i)(account password|login credentials|your amazon password)", body):
        out.append(Finding("ACC-01", "Any collection of Amazon customer credentials is prohibited."))
    return out


def check_claims(draft: Draft) -> list[Finding]:
    out: list[Finding] = []
    body = f"{draft.html}\n{draft.text}"
    if PERFORMANCE_CLAIM_RE.search(body):
        out.append(Finding("DISC-02",
                           "Unsubstantiated earnings/conversion claim. Publishing claims with no verified "
                           "reporting behind them is misleading and risks material breach.",
                           severity="blocking"))
    for m in SUPERLATIVE_RE.finditer(body):
        out.append(Finding("DATA-02",
                           f"Editorial superlative '{m.group(1)}' needs first-hand testing or cited evidence "
                           "to satisfy Google's people-first criteria (source S9).",
                           severity="advisory"))
    return out


def evaluate(draft: Draft) -> list[Finding]:
    findings: list[Finding] = []
    findings += check_disclosure(draft)
    findings += check_links(draft)
    findings += check_prohibitions(draft)
    findings += check_claims(draft)
    # de-duplicate
    seen: set[tuple[str, str]] = set()
    unique: list[Finding] = []
    for f in findings:
        k = (f.rule_id, f.message)
        if k not in seen:
            seen.add(k)
            unique.append(f)
    return unique


def blocking(findings: list[Finding]) -> list[Finding]:
    return [f for f in findings if f.severity == "blocking"]


def compliance_matrix() -> list[dict]:
    """Machine-readable control matrix used by the site's compliance page."""
    return [{"id": r.id, "clause": r.clause, "requirement": r.summary,
             "severity": r.severity, "source": r.source_url} for r in RULES]
