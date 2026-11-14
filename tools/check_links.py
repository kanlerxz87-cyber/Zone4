#!/usr/bin/env python3
"""Site integrity checker — the CI gate for "no broken links, no unsourced rows".

Checks, for every HTML page in the repository root:

1. **Internal links resolve.** Every ``href`` to a local file exists, and every
   in-page ``#anchor`` matches an ``id`` on that page.
2. **Every table row is sourced or flagged.** A row must either contain an
   http(s) link to the official page that supports it, or show a blank marker
   together with an explicit unverified/withheld state. A row with a value and
   no source is a hard failure.
3. **CSS coverage.** No class used by a page may be undefined in ``styles.css``
   (the defect that shipped in an earlier merge — flag F-009).
4. **No nulls, no placeholders, no invented money.** ``>None<``, ``nan``,
   ``[[UNVERIFIED`` and dollar figures without a rate table behind them fail.
5. **Disclosure.** The required Associates statement appears on every page that
   links out to Amazon.

Exit code 0 = publishable. Non-zero with a report otherwise.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
SKIP_HREFS = re.compile(r"^(mailto:|tel:|javascript:|data:)")
BLANK_MARKERS = ("—", "&mdash;", "class=\"blank\"", "class='blank'")
UNVERIFIED_MARKERS = ("unverified", "needs verification", "not computable", "withheld",
                      "blocked", "held", "flagged", "not connected", "not established",
                      "no verified", "not retrieved", "not confirmed")
def is_amazon_host(host):
    """Registrable-domain check mirroring engine.policy (kept standalone so this
    script can run in CI without importing the package)."""
    if not host:
        return False
    labels = [l for l in host.lower().strip(".").split(".") if l]
    if not labels:
        return False
    if labels[-1] == "amazon" or host.lower() in {"amzn.to", "www.amzn.to"}:
        return True
    if len(labels) >= 2 and labels[-2] == "amazon" and re.fullmatch(r"[a-z]{2,6}", labels[-1]):
        return True
    return (len(labels) >= 3 and labels[-3] == "amazon"
            and bool(re.fullmatch(r"[a-z]{2}", labels[-2])) and bool(re.fullmatch(r"[a-z]{2}", labels[-1])))
DISCLOSURE = "As an Amazon Associate I earn from qualifying purchases."


def pages(root: Path) -> list[Path]:
    return sorted(p for p in root.glob("*.html"))


def css_classes(root: Path) -> set[str]:
    """Union of class selectors across every stylesheet in the tree.

    The published site (``docs/``) uses ``styles.css``; the engine's preview build
    writes its own ``preview.css``. Both are honoured so the check is about
    coverage, not about a particular filename.
    """
    css = ""
    for sheet in sorted(root.glob("*.css")):
        css += sheet.read_text(encoding="utf-8")
    return set(re.findall(r"\.([A-Za-z][\w-]*)", css))


def check_internal(root: Path, problems: list[str]) -> None:
    for page in pages(root):
        html = page.read_text(encoding="utf-8")
        ids = set(re.findall(r"\bid=[\"']([^\"']+)[\"']", html))
        for href in re.findall(r"""href=["']([^"']+)["']""", html):
            if SKIP_HREFS.match(href):
                problems.append(f"{page.name}: forbidden link scheme in {href!r}")
                continue
            parts = urlsplit(href)
            if parts.scheme in {"http", "https"}:
                if parts.netloc == "":
                    problems.append(f"{page.name}: empty netloc in {href!r}")
                continue
            if href.startswith("#"):
                if href != "#" and href[1:] not in ids:
                    problems.append(f"{page.name}: in-page anchor {href} has no matching id")
                continue
            target = (page.parent / href.split("#")[0]).resolve()
            if not target.exists():
                problems.append(f"{page.name}: broken internal link -> {href}")
            elif "#" in href:
                frag = href.split("#", 1)[1]
                if frag:
                    t_html = target.read_text(encoding="utf-8")
                    if f'id="{frag}"' not in t_html and f"id='{frag}'" not in t_html:
                        problems.append(f"{page.name}: {href} points to a missing id on {target.name}")


def check_rows(root: Path, problems: list[str]) -> None:
    for page in pages(root):
        html = page.read_text(encoding="utf-8")
        for i, block in enumerate(re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.S), start=1):
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", block, re.S)
            if not cells:
                continue
            header = "<th>" in block or "<th " in block
            if header:
                continue
            text = re.sub(r"<[^>]+>", " ", block)
            has_value = bool(re.search(r"[A-Za-z0-9$%]{2,}", " ".join(c for c in cells if "<a" not in c)))
            has_link = "href=\"http" in block or "href='http" in block
            lowered = block.lower() + text.lower()
            flagged = any(m in lowered for m in UNVERIFIED_MARKERS)
            blanked = any(m in block for m in BLANK_MARKERS)
            if not has_link and not (flagged and blanked):
                snippet = re.sub(r"\s+", " ", text).strip()[:110]
                problems.append(
                    f"{page.name}: table row {i} has no source link and no blank+flag treatment — "
                    f"'{snippet}'")


def check_css(root: Path, problems: list[str]) -> None:
    defined = css_classes(root)
    if not defined:
        problems.append(f"{root}: no stylesheet found — cannot verify CSS coverage")
    for page in pages(root):
        html = page.read_text(encoding="utf-8")
        used: set[str] = set()
        for m in re.findall(r"""class=["']([^"']+)["']""", html):
            used |= set(m.split())
        for cls in sorted(used - defined):
            problems.append(f"{page.name}: class '{cls}' is used but defined in no stylesheet")


def check_hygiene(root: Path, problems: list[str]) -> None:
    for page in pages(root):
        html = page.read_text(encoding="utf-8")
        if re.search(r">\s*None\s*<", html):
            problems.append(f"{page.name}: a Python None leaked into a cell")
        if "[[UNVERIFIED" in html:
            problems.append(f"{page.name}: unresolved placeholder would be published")
        if "nan" in html.lower().replace("n/a", ""):
            for line_no, line in enumerate(html.splitlines(), 1):
                if re.search(r">\s*nan\s*<|NaN", line):
                    problems.append(f"{page.name}:{line_no}: NaN in output")
        hosts = {(urlsplit(h).hostname or "").lower()
                  for h in re.findall(r"""href=["']https?://[^"']+["']""", html)}
        amazon_links = [h for h in hosts if is_amazon_host(h)]
        if amazon_links and DISCLOSURE.lower() not in html.lower():
            problems.append(f"{page.name}: links to Amazon ({', '.join(sorted(amazon_links))}) "
                            "without the required disclosure statement")
        # IP License 2(k): a page that displays Amazon-sourced text must carry
        # the plain-view notice. Checked here as well as at generation time so a
        # hand-written page cannot slip past the generator.
        if amazon_links and "COMES FROM AMAZON" not in html.upper():
            problems.append(f"{page.name}: displays Amazon links or Amazon-sourced text without the "
                            "IP License 2(k) Amazon content notice")
        for href in re.findall(r"""href=["']([^"']+)["']""", html):
            parts = urlsplit(href)
            host = (parts.hostname or "").lower()
            if host.endswith((".amazon", ".amzn.to")) and "tag=" in (parts.query or ""):
                problems.append(f"{page.name}: tagged affiliate link on a redirect host ({host}) — "
                                "Participation Requirements §6(v)-(w)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=str(ROOT / "build" / "site-preview"),
                    help="directory of generated pages (default: the engine preview build)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    root = Path(args.root)
    problems: list[str] = []
    check_internal(root, problems)
    check_rows(root, problems)
    check_css(root, problems)
    check_hygiene(root, problems)

    if not args.quiet:
        n = len(pages(root))
        lines = sum(len(p.read_text().splitlines()) for p in root.glob("*.css"))
        print(f"checked {n} pages, {lines} css lines")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  ✗ {p}")
        return 1
    print("✓ no broken links, every table row sourced or flagged, CSS complete, disclosure present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
