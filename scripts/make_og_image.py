#!/usr/bin/env python3
"""Generate docs/og.png - the social preview image every page advertises.

Why a generated image: the site must not use Amazon product photography (the
IP License governs Program Content, and F-18/S-18 is still an open owner
decision), and it must not use someone else's photograph. A typographic card
that states only the site's own positioning needs no licence and cannot
misrepresent a product.

The image is deterministic: the same script produces the same pixels, so the
committed file can be regenerated and diffed. It is drawn with Pillow, which is
a build-time dependency only - the published site ships a static PNG and no
runtime library.

Run: python3 scripts/make_og_image.py
"""
from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "og.png"

W, H = 1200, 630
BG = (250, 247, 242)        # --bg      warm off-white
INK = (35, 32, 27)          # --ink     warm near-black
MUTED = (107, 100, 89)      # --muted
ACCENT = (180, 83, 9)       # --accent  warm copper
SOFT = (253, 240, 224)      # --accent-soft
LINE = (231, 225, 214)

FONTS = pathlib.Path("/usr/share/fonts/truetype/dejavu")


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # A quiet warm wash in the corner, matching the site's hero gradient.
    for i in range(260):
        alpha = int(26 * (1 - i / 260))
        d.ellipse([W - 520 - i * 2, -300 - i, W + 120, 260 + i],
                  outline=None, fill=None)
    overlay = Image.new("RGB", (W, H), BG)
    od = ImageDraw.Draw(overlay)
    for i in range(220, 0, -1):
        od.ellipse([W - 240 - i * 2, -220 - i, W + 240, 300 + i], fill=(253, 240, 224))
    img = Image.blend(img, overlay, 0.55)
    d = ImageDraw.Draw(img)

    # Brand lockup
    d.rectangle([64, 60, 68, 128], fill=ACCENT)
    d.text((86, 58), "Zone4", font=font("DejaVuSerif-Bold.ttf", 54), fill=INK)
    d.text((88, 122), "AIR FRYER BUYING GUIDES", font=font("DejaVuSans-Bold.ttf", 20), fill=MUTED)

    # Headline
    d.text((64, 226), "Three air fryers,", font=font("DejaVuSerif-Bold.ttf", 66), fill=INK)
    d.text((64, 300), "checked against", font=font("DejaVuSerif-Bold.ttf", 66), fill=INK)
    d.text((64, 374), "their own listings.", font=font("DejaVuSerif-Bold.ttf", 66), fill=ACCENT)

    # Supporting line
    d.text((64, 476),
           "Capacity, counter depth, cleanup - every figure linked to the official page.",
           font=font("DejaVuSans.ttf", 26), fill=MUTED)
    d.text((64, 514),
           "No prices, no star ratings, no popularity claims. Gaps are published, not hidden.",
           font=font("DejaVuSans.ttf", 26), fill=MUTED)

    # Rule + required disclosure strip along the bottom
    d.line([64, 574, W - 64, 574], fill=LINE, width=2)
    d.rectangle([64, 592, 76, 604], fill=ACCENT)
    d.text((88, 586),
           "As an Amazon Associate I earn from qualifying purchases.",
           font=font("DejaVuSans-Bold.ttf", 21), fill=MUTED)

    OUT.parent.mkdir(exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
