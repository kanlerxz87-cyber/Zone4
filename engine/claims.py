"""Claims, statuses, and the verification gate.

This module encodes the project's single hard rule: **no value may be
published unless a specific official source was actually read.** A ``Claim``
that is not ``VERIFIED`` publishes ``None`` and keeps its flag attached, so a
downstream template, table row, or revenue figure physically cannot pick up a
guess.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Iterable

#: Amazon ASINs are 10 alphanumeric characters (source S11). Books are an
#: exception in that their ASIN equals the 10-digit ISBN, still 10 characters.
ASIN_LENGTH = 10
ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")

#: Any "10-character-ish" identifier typed into a URL path.
PATH_ID_RE = re.compile(r"/(?:dp|gp/product|product)/([A-Za-z0-9]{6,20})")


class Status(str, Enum):
    VERIFIED = "verified"
    VERIFIED_PARTIAL = "verified-partial"
    UNVERIFIED = "unverified"
    BLOCKED = "blocked"
    FAIL = "fail"

    @property
    def publishable(self) -> bool:
        """Only fully verified claims may carry a value into a published page."""
        return self is Status.VERIFIED


@dataclass
class Source:
    """An official page that was read."""

    id: str
    title: str
    url: str
    publisher: str = ""
    retrieved: str = ""
    note: str = ""

    @property
    def citation(self) -> str:
        return f"{self.publisher or 'Official source'} — {self.title} ({self.retrieved})"


@dataclass
class Claim:
    """One asserted field: value + the source that justifies it, or no value."""

    key: str
    label: str
    value: Any = None
    status: Status = Status.UNVERIFIED
    source: Source | None = None
    quote: str = ""
    flag: str | None = None
    reason: str = ""
    entity: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.status, str):
            self.status = Status(self.status)
        # The gate. Enforced here rather than in templates so it cannot be
        # bypassed by a new caller.
        if not self.status.publishable and self.value is not None:
            raise ValueError(
                f"Claim '{self.key}' is {self.status.value} and may not carry a value "
                f"(got {self.value!r}). Set it to None and raise a flag instead."
            )
        if self.status.publishable and self.source is None:
            raise ValueError(f"Claim '{self.key}' is verified but has no source.")

    @property
    def display(self) -> str:
        """What a page shows. Unverified renders as the blank marker, never 0/—."""
        if self.status.publishable and self.value is not None:
            return f"{self.value}" if not isinstance(self.value, str) else self.value
        return ""

    @property
    def is_blank(self) -> bool:
        return self.display == ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        d["source"] = {"id": self.source.id, "url": self.source.url, "title": self.source.title} if self.source else None
        return d


@dataclass
class Entity:
    """A thing being researched (a product reference, a policy area)."""

    ref: str
    name: str
    claims: dict[str, Claim] = field(default_factory=dict)
    flags: list[str] = field(default_factory=list)
    notes: str = ""
    #: Set when a supplied short link was followed to a real product page.
    resolved_asin: str | None = None

    def add(self, claim: Claim) -> None:
        claim.entity = self.ref
        self.claims[claim.key] = claim
        if not claim.status.publishable and claim.flag and claim.flag not in self.flags:
            self.flags.append(claim.flag)

    def get(self, key: str) -> Claim | None:
        return self.claims.get(key)

    def verified_count(self) -> int:
        return sum(1 for c in self.claims.values() if c.status.publishable)

    @property
    def complete(self) -> bool:
        return bool(self.claims) and self.verified_count() == len(self.claims)


def extract_identifier(url_or_asin: str) -> str | None:
    """Pull the product identifier out of a URL, or accept a bare ASIN."""
    s = (url_or_asin or "").strip()
    if not s:
        return None
    if ASIN_RE.match(s.upper()) and "/" not in s:
        return s.upper()
    m = PATH_ID_RE.search(s)
    if m:
        return m.group(1).upper()
    tail = s.rstrip("/").rsplit("/", 1)[-1]
    tail = re.sub(r"\.(pdf|html?|aspx?)$", "", tail)
    if re.fullmatch(r"[A-Za-z0-9]{6,20}", tail):
        return tail.upper()
    return None


def validate_asin_format(identifier: str | None) -> tuple[bool, str]:
    """Return ``(ok, detail)`` using Amazon's published 10-character rule."""
    if not identifier:
        return False, "No product identifier could be parsed from the supplied URL."
    n = len(identifier)
    if n != ASIN_LENGTH:
        return False, (
            f"Identifier '{identifier}' is {n} characters; Amazon ASINs are "
            f"{ASIN_LENGTH} alphanumeric characters."
        )
    if not ASIN_RE.match(identifier):
        return False, f"Identifier '{identifier}' contains characters outside [A-Z0-9]."
    return True, f"Identifier '{identifier}' matches the 10-character ASIN format."


class VerificationReport:
    """Aggregate of every claim across every entity, with the gate applied."""

    def __init__(self, entities: Iterable[Entity] = ()) -> None:
        self.entities: list[Entity] = list(entities)

    def add(self, entity: Entity) -> None:
        self.entities.append(entity)

    @property
    def claims(self) -> list[Claim]:
        return [c for e in self.entities for c in e.claims.values()]

    def verified(self) -> list[Claim]:
        return [c for c in self.claims if c.status.publishable]

    def withheld(self) -> list[Claim]:
        return [c for c in self.claims if not c.status.publishable]

    def flags(self) -> list[str]:
        out: list[str] = []
        for e in self.entities:
            for f in e.flags:
                if f not in out:
                    out.append(f)
        return out

    def publishable(self) -> bool:
        """True only when every claim is fully verified from an official source."""
        return all(c.status.publishable for c in self.claims) and bool(self.claims)

    def summary(self) -> dict:
        total = len(self.claims)
        v = len(self.verified())
        return {
            "entities": len(self.entities),
            "claims_total": total,
            "claims_verified": v,
            "claims_withheld": total - v,
            "verification_rate": round(v / total, 4) if total else 0.0,
            "publishable": self.publishable(),
            "open_flags": len(self.flags()),
        }
