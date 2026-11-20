#!/usr/bin/env python3
"""Generated-count gate: no hand-typed register count may disagree with the registers.

Implements the recorded SG-37 mechanism (suggestion SG-37, decision D-10) and the
S-10 ENGINE.md test-count item. Every count printed about the project's own
registers in README.md, EXECUTIVE_SUMMARY.md, data/content.json and ENGINE.md is
computed here from the registers (data/suggestions.json, data/questions.json,
data/decisions.json, data/flags.json, data/requirements.json) and from unittest
discovery over tests/, then compared with the numerals the documents actually
print. The gate is wired in twice: a step in .github/workflows/site-checks.yml
and tests/test_doc_counts.py.

Modes
    python3 scripts/check_doc_counts.py          # check (exit 1 on any drift)
    python3 scripts/check_doc_counts.py --fix    # rewrite numerals in place, then re-check

--fix is numbers-only by construction: it substitutes the captured numerals and
rewrites the generated ENGINE.md comment; it never touches surrounding prose.
When a count sentence is absent because a document was intentionally reworded,
the check fails with "expected sentence not found" and the anchor in
COUNT_SURFACES must be updated consciously in the same commit.

Added 2026-11-19 by arena/3c1cee74-zone4. The drift this stops was live: see
flag F-94 (ENGINE.md said 92 tests against a 94-test suite; README's data-map
row said 88 flags against a 90-row register).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unittest
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent

# Patterns are anchored to the exact published sentences so a rewording fails
# loudly instead of silently skipping the surface. Groups map left-to-right onto
# `keys` entries of the register_counts() dictionary.
COUNT_SURFACES = [
    {
        "label": "README.md review-gate sentence",
        "file": "README.md",
        "pattern": (
            r"\*\*(\d+) suggestions\*\*, (?:and )?\*\*(\d+) questions\*\*, "
            r"(?:and )?\*\*(\d+) decisions\*\* \((\d+) recorded[,;] (\d+) open\), "
            r"(?:and |with )?\*\*(\d+) flags\*\*"
        ),
        "keys": ["suggestions", "questions", "decisions", "recorded", "open", "flags"],
    },
    {
        "label": "README.md requirements site-map row",
        "file": "README.md",
        "pattern": r"All (\d+) request requirements",
        "keys": ["requirements"],
    },
    {
        "label": "README.md data-map flags.json numeral",
        "file": "README.md",
        "pattern": r"\| `data/flags\.json` \| (\d+) flags;",
        "keys": ["flags"],
    },
    {
        "label": "EXECUTIVE_SUMMARY.md decision-support sentence",
        "file": "EXECUTIVE_SUMMARY.md",
        "pattern": (
            r"\*\*(\d+) suggestions\*\*, (?:and )?\*\*(\d+) questions\*\*, "
            r"(?:and )?\*\*(\d+) decisions\*\* \((\d+) recorded[,;] (\d+) open\), "
            r"(?:and |with )?\*\*(\d+) flags\*\*"
        ),
        "keys": ["suggestions", "questions", "decisions", "recorded", "open", "flags"],
    },
    {
        "label": "data/content.json executive-summary sentence",
        "file": "data/content.json",
        "pattern": (
            r"Decision support: (\d+) costed suggestions, (\d+) questions and "
            r"(\d+) decisions \((\d+) recorded; (\d+) open\)"
        ),
        "keys": ["suggestions", "questions", "decisions", "recorded", "open"],
    },
    {
        "label": "ENGINE.md test-count line",
        "file": "ENGINE.md",
        "pattern": r"#\s*(\d+) tests",
        "keys": ["tests"],
        "line_anchor": "unittest discover -s tests",
    },
]

# --- Publication counts on the generated site -------------------------------
# The document surfaces above cover README/EXECUTIVE_SUMMARY/content.json/ENGINE.md.
# They did not cover the pages themselves, so on 2026-11-20 the front page's meta
# description, every page's social-card alt text and the social preview PNG still
# said "three countertop air fryers" and "eight sourced guides" while five
# products and fourteen guides were published (decision D-54, flag F-95).
#
# check_publication_counts() closes that gap from the other side: it does not
# trust the build code at all, it reads the *generated* pages and the card
# script, and fails if any of them prints a catalogue count that disagrees with
# the registers.
PUBLICATION_COPY_SURFACES = [
    {
        "label": "docs/index.html meta description",
        "file": "docs/index.html",
        "pattern": r'<meta name="description" content="([^"]*)"',
        "expect": lambda c: [
            f"{c['air_fryers_word']} countertop air fryers",
            f"{c['thermometers_word']} meat thermometers",
            f"{c['published_guides_word']} sourced buying guides",
        ],
    },
    {
        "label": "docs/index.html social preview alt text",
        "file": "docs/index.html",
        "pattern": r'<meta property="og:image:alt" content="([^"]*)"',
        "expect": lambda c: [
            f"{c['air_fryers_word']} air fryer formats",
            f"{c['thermometers_word']} meat thermometers",
            f"{c['published_guides_word']} sourced guides",
        ],
    },
    {
        "label": "docs/about.html social preview alt text",
        "file": "docs/about.html",
        "pattern": r'<meta property="og:image:alt" content="([^"]*)"',
        "expect": lambda c: [
            f"{c['air_fryers_word']} air fryer formats",
            f"{c['published_guides_word']} sourced guides",
        ],
    },
]

# The card script must take its numerals from the register, not carry them.
SOCIAL_CARD_SCRIPT = "scripts/make_social_card.sh"

# Counts that are still typed into copy and are not yet derived. Each entry is a
# known, deliberate exception with its flag, so the gate cannot be satisfied by
# quietly widening it: removing a line here means the surface was fixed, adding
# one means an owner accepted the drift.
KNOWN_STATIC_COUNT_COPY = {
    # The card script's own subtitle line is generated now (2026-11-20), so the
    # only remaining static count in published copy is the case-study sentence
    # below, which names a fixed historical event rather than the catalogue.
    "scripts/build_site.py::1963": "design-prompt slot text, not a catalogue count",
}


def check_publication_counts(counts: Optional[Dict[str, int]] = None) -> List[str]:
    """Fail when a generated page or the card script disagrees with the registers."""
    sys.path.insert(0, str(ROOT / "scripts"))
    counts = counts or publication_counts()
    problems: List[str] = []
    for surface in PUBLICATION_COPY_SURFACES:
        path = ROOT / surface["file"]
        if not path.exists():
            problems.append(f"{surface['label']}: file missing ({surface['file']})")
            continue
        text = path.read_text(encoding="utf-8")
        match = re.search(surface["pattern"], text)
        if not match:
            problems.append(
                f"{surface['label']}: pattern not found in {surface['file']} "
                "(was the markup reworded? update PUBLICATION_COPY_SURFACES consciously)"
            )
            continue
        value = match.group(1)
        for expected in surface["expect"](counts):
            if expected not in value:
                problems.append(
                    f"{surface['label']}: expected {expected!r} in the published text "
                    f"but the page says {value[:160]!r}"
                )
    card = ROOT / SOCIAL_CARD_SCRIPT
    if not card.exists():
        problems.append(f"social card script missing ({SOCIAL_CARD_SCRIPT})")
    else:
        script = card.read_text(encoding="utf-8")
        # A hard-coded numeral in one of the three card() calls is the exact
        # defect F-95 records. The variables must be used instead.
        for literal_call in re.findall(r'^card c[abc] "\d+"', script, re.M):
            problems.append(
                f"{SOCIAL_CARD_SCRIPT}: {literal_call!r} carries a typed numeral; "
                "the card must read its counts from publication_counts()"
            )
        for var in ("N_AIR_FRYERS", "N_THERMOMETERS", "N_GUIDES", "N_PRODUCTS"):
            if f"{var}=" not in script.replace(" ", ""):
                problems.append(
                    f"{SOCIAL_CARD_SCRIPT}: {var} is not assigned from the register"
                )
    return problems


# A liveness pointer rather than a count: the file README names as the latest
# dated verification record must exist. Ordering same-day sessions is ambiguous,
# so the gate checks existence, not recency.
LATEST_SESSION_SURFACE = {
    "label": "README.md latest verification-session pointer",
    "file": "README.md",
    "pattern": r"The latest, `verification-session-([0-9a-f]+)\.json`",
}

ENGINE_COMMENT_NOTE = (
    "stdlib only (count generated by scripts/check_doc_counts.py --fix; do not hand-edit)"
)


class CountDrift(Exception):
    """Raised when unittest discovery itself is broken (imports fail)."""


def _load(path: str, key: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))[key]


def publication_counts() -> Dict[str, int]:
    """The site's own catalogue counts, computed once in scripts/build_extras.py."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import build_extras  # noqa: E402  (same pipeline the site build uses)

    return build_extras.publication_counts()


# One spelling map for the whole pipeline: scripts/build_extras.py owns it, so the
# pages, the card and this gate cannot disagree about how a count is worded.
_text_number = staticmethod(lambda n: __import__("build_extras")._text_number(n)).__func__


def unittest_total() -> int:
    """Total test cases found by discovery over tests/ (imports, not runs)."""
    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / "tests"))

    def walk(s):
        for item in s:
            if isinstance(item, unittest.TestSuite):
                yield from walk(item)
            else:
                yield item

    cases = list(walk(suite))
    broken = [c for c in cases if type(c).__name__ == "_FailedTest"]
    if broken:
        raise CountDrift(
            "unittest discovery failed (import errors count as gate failures): "
            + "; ".join(str(c) for c in broken[:5])
        )
    return len(cases)


def register_counts() -> Dict[str, int]:
    decisions = _load("data/decisions.json", "decisions")
    return {
        "suggestions": len(_load("data/suggestions.json", "suggestions")),
        "questions": len(_load("data/questions.json", "questions")),
        "decisions": len(decisions),
        "recorded": sum(
            1 for d in decisions if str(d.get("status", "")).lower().startswith("recorded")
        ),
        "open": sum(1 for d in decisions if str(d.get("status", "")).startswith("Open")),
        "flags": len(_load("data/flags.json", "flags")),
        "requirements": len(_load("data/requirements.json", "requirements")),
        "tests": unittest_total(),
    }


def _sub_numbers(match: re.Match, keys: List[str], counts: Dict[str, int]) -> str:
    """Rebuild a regex match keeping every character except the captured numerals.

    match.span(i) is relative to the searched string, so the offsets are rebased
    onto match.group(0) before slicing (a regression test covers a match that
    does not start at offset 0).
    """
    text = match.group(0)
    base = match.start()
    out: List[str] = []
    prev = 0
    for i, key in enumerate(keys, start=1):
        s, e = match.span(i)
        s_rel, e_rel = s - base, e - base
        out.append(text[prev:s_rel])
        out.append(str(counts[key]))
        prev = e_rel
    out.append(text[prev:])
    return "".join(out)


def extract(text: str, pattern: str) -> List[int]:
    """First match's captured numerals as ints; [] when the pattern is absent."""
    m = re.search(pattern, text)
    return [int(g) for g in m.groups()] if m else []


def fix_text(text: str, pattern: str, keys: List[str], counts: Dict[str, int]) -> str:
    return re.sub(pattern, lambda m: _sub_numbers(m, keys, counts), text)


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding="utf-8")


def check(counts: Optional[Dict[str, int]] = None) -> List[str]:
    """Return one human-readable message per drifted surface; empty when clean."""
    counts = counts or register_counts()
    drifts: List[str] = []
    for surface in COUNT_SURFACES:
        text = _read(surface["file"])
        pattern = surface["pattern"]
        keys = surface["keys"]
        if surface.get("line_anchor"):
            lines = [ln for ln in text.splitlines() if surface["line_anchor"] in ln]
            if not lines:
                drifts.append(
                    f"{surface['label']}: no line containing '{surface['line_anchor']}' "
                    f"was found in {surface['file']}; update COUNT_SURFACES consciously"
                )
                continue
            text = lines[0]
        matches = list(re.finditer(pattern, text))
        if not matches:
            drifts.append(
                f"{surface['label']}: expected count sentence not found in {surface['file']} "
                f"(was the prose reworded? update COUNT_SURFACES consciously)"
            )
            continue
        for m in matches:
            for i, key in enumerate(keys, start=1):
                got = int(m.group(i))
                want = counts[key]
                if got != want:
                    drifts.append(
                        f"{surface['label']}: prints {got} for {key}, registers hold {want}"
                    )
    # Liveness pointer: the named verification-session file must exist.
    ptext = _read(LATEST_SESSION_SURFACE["file"])
    pm = re.search(LATEST_SESSION_SURFACE["pattern"], ptext)
    if not pm:
        drifts.append(
            f"{LATEST_SESSION_SURFACE['label']}: expected sentence not found in README.md"
        )
    else:
        named = ROOT / f"data/verification-session-{pm.group(1)}.json"
        if not named.exists():
            drifts.append(
                f"{LATEST_SESSION_SURFACE['label']}: README names "
                f"{named.name}, which does not exist in data/"
            )
    return drifts


def fix(counts: Optional[Dict[str, int]] = None) -> List[str]:
    """Rewrite drifted numerals in place; returns the surfaces it changed."""
    counts = counts or register_counts()
    changed: List[str] = []
    for surface in COUNT_SURFACES:
        text = _read(surface["file"])
        keys = surface["keys"]
        if surface.get("line_anchor"):
            lines = text.splitlines()
            hit = None
            for idx, ln in enumerate(lines):
                if surface["line_anchor"] in ln and re.search(surface["pattern"], ln):
                    hit = idx
                    break
            if hit is None:
                continue
            original = lines[hit]
            head, sep, _tail = original.partition("#")
            if not sep:
                continue
            lines[hit] = head.rstrip() + "  # " + f"{counts['tests']} tests, " + ENGINE_COMMENT_NOTE
            if lines[hit] != original:
                changed.append(f"{surface['label']} -> {counts['tests']} tests")
            _write(surface["file"], "\n".join(lines) + ("\n" if text.endswith("\n") else ""))
            continue
        before = text
        after = fix_text(text, surface["pattern"], keys, counts)
        if after != before:
            _write(surface["file"], after)
            changed.append(surface["label"])
    return changed


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fix", action="store_true", help="rewrite drifted numerals in place")
    args = parser.parse_args(argv)
    try:
        counts = register_counts()
    except CountDrift as exc:
        print(f"FAIL {exc}")
        return 1
    if args.fix:
        changed = fix(counts)
        for c in changed:
            print(f"fixed {c}")
        if not changed:
            print("nothing to fix; all hand-typed counts already match the registers")
    drifts = check(counts)
    if drifts:
        print("Hand-typed counts disagree with the registers (SG-37 gate, flag F-94):")
        for d in drifts:
            print(f"  - {d}")
        print("Run: python3 scripts/check_doc_counts.py --fix   (numerals only, never prose)")
        return 1
    pub_counts = publication_counts()
    pub = check_publication_counts(pub_counts)
    if pub:
        print(
            "A generated page or the social card disagrees with the registers "
            "(D-54 gate, flag F-95):"
        )
        for d in pub:
            print(f"  - {d}")
        print(
            "Fix the generator (scripts/build_site.py / scripts/make_social_card.sh), "
            "rebuild, and re-run this gate. Do not edit docs/ by hand."
        )
        return 1
    summary = ", ".join(f"{k}={v}" for k, v in counts.items())
    print(f"OK all hand-typed counts agree with the registers ({summary})")
    print(
        "OK the generated pages and the social card print the register counts "
        f"(products={pub_counts['products']}, air fryers={pub_counts['air_fryers']}, "
        f"thermometers={pub_counts['thermometers']}, guides={pub_counts['published_guides']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
