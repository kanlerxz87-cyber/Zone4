"""Special Link construction and link safety.

Amazon's rules that shape this module (sources S2, S5, S13):

* an Associate tag is issued per locale and works only in that locale;
* a tag identifies you to Amazon — using someone else's, or a placeholder, earns
  nothing and breaches the agreement;
* §6(v)/(w) forbid cloaking or shorteners that obscure that the destination is
  Amazon, so this builder emits the *final* ``https://<host>/dp/<ASIN>?tag=...``
  URL and refuses anything else;
* §6(q) forbids causing an Amazon page to open other than by a customer click,
  so no auto-redirect/JS helper is ever produced here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlencode, urlsplit

from .config import ALLOWED_DESTINATION_HOSTS, Config
from .policy import is_amazon_host

#: US Store IDs end in "-20"; a tag is the store ID plus an optional tracking ID.
TAG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*-\d{2}$")
ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")
PLACEHOLDER_TAGS = {"amazon-20", "example-20", "yourid-20", "test-20", "tag-20", "chan-20"}


class LinkError(ValueError):
    pass


@dataclass
class SpecialLink:
    asin: str
    host: str
    tag: str
    campaign: str | None = None
    subtag: str | None = None

    @property
    def url(self) -> str:
        params: dict[str, str] = {"tag": self.tag}
        if self.campaign:
            params["linkCode"] = "ur1"
        if self.subtag:
            params["ascsubtag"] = self.subtag[:50]
        return f"https://{self.host}/dp/{self.asin}?{urlencode(params)}"

    @property
    def anchor(self) -> str:
        """Text-only link markup. rel values keep the link compliant and SEO-safe."""
        return (f'<a href="{self.url}" rel="nofollow sponsored noopener" '
                f'target="_blank">{self.asin}</a>')


def validate_tag(tag: str | None, *, allow_placeholder: bool = False) -> str:
    if not tag:
        raise LinkError(
            "No Partner Tag configured. Without your own registered tag, clicks are "
            "unattributed and no commission accrues (Sources S5, S13). Set "
            "ZONE4_PARTNER_TAG or config.json → marketplace.partner_tag."
        )
    tag = tag.strip().lower()
    if not TAG_RE.match(tag):
        raise LinkError(f"Partner Tag {tag!r} does not look like a Store ID (e.g. '<yourid>-20').")
    if tag in PLACEHOLDER_TAGS and not allow_placeholder:
        raise LinkError(
            f"{tag!r} is a placeholder example tag from documentation. Using it would "
            "route your traffic's commissions to someone else. Use your own registered tag."
        )
    return tag


def build_link(asin: str, *, host: str, tag: str, campaign: str | None = None,
               subtag: str | None = None) -> SpecialLink:
    asin = (asin or "").upper().strip()
    if not ASIN_RE.match(asin):
        raise LinkError(
            f"Refusing to build a link from {asin!r}: Amazon ASINs are 10 alphanumeric "
            "characters, so a shortened/truncated identifier cannot address a product."
        )
    if host not in ALLOWED_DESTINATION_HOSTS:
        raise LinkError(f"Destination host {host!r} is not an approved Amazon marketplace host.")
    return SpecialLink(asin=asin, host=host, tag=validate_tag(tag), campaign=campaign, subtag=subtag)


def is_safe_href(href: str) -> tuple[bool, str]:
    """Gate for links already written into content (used by the site build)."""
    parts = urlsplit(href)
    host = (parts.hostname or "").lower()
    if not host:
        return True, ""  # in-page anchor or relative path — handled by link checker
    if parts.scheme not in {"https", "http"}:
        return False, f"scheme {parts.scheme!r} is not permitted for outbound links"
    if not is_amazon_host(host):
        return True, ""
    if host.endswith(".amazon") or host.endswith("amzn.to") or "redirect" in host:
        return False, (
            f"{host} is a redirect/shortener host. Amazon links on the Site must make the "
            "Amazon destination clear (Participation Requirements §6(v)-(w))."
        )
    if "/dp/" in parts.path:
        m = re.search(r"/dp/([A-Z0-9]{6,20})", parts.path, re.I)
        if m and not ASIN_RE.match(m.group(1).upper()):
            return False, f"'{m.group(1)}' is not a 10-character ASIN; the link cannot resolve to a product."
    return True, ""


def links_in(html: str) -> list[str]:
    return re.findall(r"""href=["']([^"']+)["']""", html or "")


def audit_html_links(html: str, cfg: Config | None = None) -> list[dict]:
    """Return one record per outbound Amazon link with its safety verdict."""
    out = []
    for href in links_in(html):
        ok, why = is_safe_href(href)
        host = (urlsplit(href).hostname or "")
        if not is_amazon_host(host):
            continue
        out.append({"href": href, "ok": ok, "issue": why,
                    "tagged": "tag=" in (urlsplit(href).query or "")})
    return out
