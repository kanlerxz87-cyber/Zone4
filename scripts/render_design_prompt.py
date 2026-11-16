#!/usr/bin/env python3
"""Regenerate DESIGN_PROMPT.md from data/design.json.

The design prompt is assembled by scripts/build_site.py so the Design brief
page, this document and the register underneath them are the same brief. If
anyone edits the markdown by hand it will be overwritten by the next build,
which is the point: the prompt must never disagree with the data it came from.

Standard library only.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_site  # noqa: E402  (the builder owns the prompt assembly)

HEADER = """# Design prompt — the brief for the visual overhaul

**Status:** proposal, not implemented. Generated from `data/design.json` by
`scripts/render_design_prompt.py`; do not edit by hand, edit the data and re-run the script.
Last generated 2026-11-16 by `arena/89900251-zone4`.

**How to use:** fill the seven bracketed slots from the recorded decisions, then paste the block
below to a designer or a design tool. The slot table at the end names the decision that fills each
one. The compliance block is non-negotiable: it encodes Amazon Associates rules, FTC guidance and
this repository's own verification discipline.

**The three directions in the `[DIRECTION]` slot are fully specified on the**
[Design brief page](https://kanlerxz87-cyber.github.io/Zone4/docs/design.html)**, and each row of
the topic programme and the anti-pattern list below is expanded there with its evidence and its
source. This document is the paste-ready form of the same data.**

---

## Prompt

```
"""

FOOTER = """
```

---

## Where each bracketed slot comes from

| Slot | Filled from | Current value |
|---|---|---|
"""

FOOTER_TAIL = """
Nothing in this prompt is applied to the site. Each slot is a decision recorded on the
[Decision log](https://kanlerxz87-cyber.github.io/Zone4/docs/decisions.html) page; until one is
recorded the bracket stays, because guessing at a brand name or a voice is exactly the kind of
invention this site refuses to publish.

The eight candidate topic titles and their evidence notes live in `data/design.json` under
`topics`; the evidence discipline behind them is flag **F-15** (no trend claim without a dated
official snapshot) and **F-47** (the brief's "trendy topics and traffic" ask measured against the
guidance the site already cites).
"""


def main() -> int:
    text = build_site.design_prompt_text()
    lines = [HEADER, text, FOOTER]
    for slot in build_site.PROMPT_SLOTS:
        lines.append(f"| `{slot['slot']}` | {slot['filled_from']} | {slot['current']} |\n")
    lines.append(FOOTER_TAIL)
    out = ROOT / "DESIGN_PROMPT.md"
    out.write_text("".join(lines), encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
