#!/usr/bin/env python3
"""Generate the three format illustrations used as category and card imagery.

Why illustrations and not photographs: the site may not use Amazon's product
photography (the IP License governs Program Content, and suggestion S-18 remains
an open owner decision), and it must never pass off a stock or generated image as
a photograph of the actual appliance. What it CAN do is show the *format* - two
baskets side by side, one deep basket, a French-door oven - as clearly labelled
line art. Nothing in these images is a claim about a product's appearance.

Each image is deterministic and drawn from the same palette tokens as the site.
Run: python3 scripts/make_format_art.py
"""
from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "img"

BG = (253, 251, 247)
PANEL = (255, 255, 255)
INK = (35, 32, 27)
MUTED = (107, 100, 89)
LINE = (214, 205, 190)
ACCENT = (180, 83, 9)
SOFT = (253, 240, 224)
GLASS = (232, 236, 238)

FONTS = pathlib.Path("/usr/share/fonts/truetype/dejavu")
W, H = 800, 500


def f(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def frame(d: ImageDraw.ImageDraw) -> None:
    d.rectangle([0, 0, W, H], fill=BG)
    d.rounded_rectangle([24, 24, W - 24, H - 24], radius=18, fill=PANEL, outline=LINE, width=2)


def label(d, xy, text, size=20, bold=False, fill=MUTED) -> None:
    d.text(xy, text, font=f("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size), fill=fill)


def dual_basket() -> Image.Image:
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    frame(d)
    d.text((60, 56), "Dual basket", font=f("DejaVuSerif-Bold.ttf", 36), fill=INK)
    label(d, (60, 104), "Two independent baskets, one housing", 18)
    # housing
    d.rounded_rectangle([110, 160, 690, 408], radius=22, fill=(247, 244, 239), outline=INK, width=3)
    # two baskets
    for x in (150, 430):
        d.rounded_rectangle([x, 196, x + 220, 380], radius=12, fill=SOFT, outline=INK, width=3)
        # handle
        d.rounded_rectangle([x + 58, 176, x + 162, 200], radius=8, fill=INK)
        d.line([x + 20, 230, x + 200, 230], fill=LINE, width=2)
        label(d, (x + 22, 248), "3 qt", 20, True, ACCENT)
    label(d, (300, 424), "basket A", 16); label(d, (560, 424), "basket B", 16)
    return img


def single_basket() -> Image.Image:
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    frame(d)
    d.text((60, 56), "Single basket", font=f("DejaVuSerif-Bold.ttf", 36), fill=INK)
    label(d, (60, 104), "One deep cavity, one drawer", 18)
    d.rounded_rectangle([150, 150, 650, 410], radius=22, fill=(247, 244, 239), outline=INK, width=3)
    d.rounded_rectangle([200, 186, 600, 392], radius=14, fill=SOFT, outline=INK, width=3)
    d.rounded_rectangle([330, 166, 470, 192], radius=8, fill=INK)
    for y in (230, 268, 306):
        d.line([228, y, 572, y], fill=LINE, width=2)
    label(d, (252, 336), "8 qt single cavity", 22, True, ACCENT)
    return img


def oven() -> Image.Image:
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    frame(d)
    d.text((60, 56), "Air-fryer toaster oven", font=f("DejaVuSerif-Bold.ttf", 36), fill=INK)
    label(d, (60, 104), "French doors, shelves instead of a basket", 18)
    d.rounded_rectangle([110, 150, 690, 420], radius=20, fill=(247, 244, 239), outline=INK, width=3)
    # French doors, open
    d.polygon([(132, 172), (330, 196), (330, 392), (132, 400)], fill=(240, 236, 229), outline=INK)
    d.polygon([(668, 172), (470, 196), (470, 392), (668, 400)], fill=(240, 236, 229), outline=INK)
    # interior with two shelves
    d.rectangle([332, 198, 468, 390], fill=GLASS, outline=INK, width=2)
    for y in (250, 320):
        d.line([338, y, 462, y], fill=INK, width=3)
    for x in (372, 428):
        d.ellipse([x - 12, 212, x + 12, 236], outline=ACCENT, width=3)
    label(d, (300, 434), "shelf 1", 16); label(d, (406, 434), "shelf 2", 16)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn, alt in (
        ("format-dual-basket.png", dual_basket, "Line drawing: two independent 3-quart baskets in one housing"),
        ("format-single-basket.png", single_basket, "Line drawing: one deep 8-quart basket in a single drawer"),
        ("format-oven.png", oven, "Line drawing: a French-door toaster oven with two shelves"),
    ):
        img = fn()
        path = OUT / name
        img.save(path, "PNG", optimize=True)
        print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size} bytes) - alt: {alt}")


if __name__ == "__main__":
    main()
