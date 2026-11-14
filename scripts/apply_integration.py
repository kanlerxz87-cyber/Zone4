#!/usr/bin/env python3
"""Apply the integration-session data fixes, verifying each change against the
official sources read on 2026-11-14 by session arena/ebf5c261-zone4.

- RV-I1: competitor labels become the exact listing titles shown on the official
  Amazon product pages (also-viewed carousel, first three items per product).
- F-05: P2 brand resolved to "Emeril" (Brand Name) / "Emeril Lagasse"
  (Manufacturer) from the product page's own Item details table.
- F-10: note that the 2026-11-14 re-check snapshot did not show the 'Sponsored'
  carousel label (rendering varies); flag stays open.
- F-17: RV-I3 automation/policy conflict added to the flagged set.
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def save(name, doc):
    (DATA / name).write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


# ---- products.json ------------------------------------------------------
products = load("products.json")

exact_labels = {
    "B0B7C327LK": "Chefman 6 Quart Dual Basket Air Fryer - Digital Touchscreen, Smart Sync Finish, Hi-Fry, Auto Shutoff, 2 Independent 3QT Nonstick Dishwasher-Safe Frying Baskets - Digital Double Air Fryer - Black",
    "B0BYKGN61Q": "Gourmia Air Fryer - 10 Qt Dual Basket Capacity, Stainless Steel | Digital Display, Touch Controls, 7 Cooking Presets, 90\u2013400\u00b0F Adjustable Temperature, Dishwasher-Safe Baskets & Crisper Trays",
    "B0CNSB81V6": "Nutrichef Double Basket Air Fryer 8.8 QT | Family Size Oil Free Airfryer with Transparent Window | 9-1 Preset Cooking Options | 360\u00b0 Hot Air Circulation Technology | 4.4 QTs per Basket | Black",
    "B0BZ52FLKC": "Emeril Lagasse Dual Zone Technology 25QT Air Fryer Oven | Dual-zone 25QT air fryer oven cooks two foods at once with synchronized settings and faster convection cooking.",
    "B0FM5KF34G": "Ninja French Door Premier Air Fry Oven, 10-in-1, 20.3 Qt, Stainless, FO101 | 450F cyclonic air, PFAS-free surface, Air fry, sear crisp, bake, broil, toast, dehydrate",
    "B0F92GL7JH": "HotKing Dual-Zone Air Fryer Toaster Oven Combo, 28 QT XL Convection Oven | French Door, Stainless Steel Non-Toxic, 10-in-1 Multifunction, 500F Broil, Rotisserie, Dehydrate, Reheat, Bake, ETL Rated",
    "B0CNY1YVDD": "Chefman Air Fryer \u2013 6 QT Compact Airfryer for Quick & Easy Meals in Minutes, Features Hi-Fry Technology for Extra Crisp, Touchscreen Controls with 4 Presets, Nonstick & Dishwasher Safe Basket - Black",
    "B0D5FX6VRL": "Chefman Air Fryer \u2013 6 QT Compact Airfryer for Quick & Easy Meals, Features Hi-Fry Technology for Extra Crisp, Easy-View Window, Touch Controls with 4 Presets, Nonstick & Dishwasher Safe Basket - Black",
    "B0C33CHG99": "Cosori TurboBlaze Air Fryer, 9-in-1, 6 Qt, PFAS-Free Ceramic Coating | 90\u00b0-450\u00b0F, 5 Fan Speeds, Air Fry, Roast, Broil, Frozen, Bake, Dry, Proof, 95% Less Oil, Safety Lock, Dishwasher-Safe, 1725W",
}

changed = 0
for p in products["products"]:
    for c in p["competitors"]:
        if exact_labels.get(c["asin"]):
            if c["label"] != exact_labels[c["asin"]]:
                c["label"] = exact_labels[c["asin"]]
                c["label_source_note"] = "Exact listing title as shown on the official Amazon product page (also-viewed carousel)."
                changed += 1

for p in products["products"]:
    if p["id"] == "P2":
        p["brand"] = "Emeril"
        p["brand_source_note"] = (
            "Item details table on the official product page: 'Brand Name | Emeril', "
            "'Manufacturer | Emeril Lagasse' (read 2026-11-14, session arena/ebf5c261-zone4). "
            "The page also shows store 'Emeril Store' and a byline 'Innovation IQ'; the brand "
            "field uses the Item details values."
        )
        p["flags"] = [f for f in p["flags"] if f != "F-05"]

save("products.json", products)
print(f"products.json: {changed} competitor labels set to exact listing titles; P2 brand resolved.")

# ---- flags.json ---------------------------------------------------------
flags = load("flags.json")
by_id = {f["id"]: f for f in flags["flags"]}

by_id["F-05"]["status"] = "Resolved"
by_id["F-05"]["detail"] = (
    "Resolved on 2026-11-14 by session arena/ebf5c261-zone4: the official product page's own "
    "'Item details' table lists 'Brand Name | Emeril' and 'Manufacturer | Emeril Lagasse'. The "
    "brand is recorded as 'Emeril'. The page also shows store 'Emeril Store' and a byline "
    "'Innovation IQ' (seen in the earlier snapshot); the Item details values are used because "
    "they are Amazon's structured product-information fields."
)
by_id["F-05"]["action"] = "None. Resolved from the official Item details table."

by_id["F-10"]["detail"] += (
    " Re-checked 2026-11-14 by session arena/ebf5c261-zone4: the current snapshot of the P2 "
    "page did not show the 'Sponsored' label above the also-viewed carousel, so the label varies "
    "by rendering. The flag stays open; treat the P2 competitor list as a possible paid signal."
)

flags["flags"].append({
    "id": "F-17",
    "severity": "High",
    "title": "Brief's automation goals conflict with Associates Program Policies without API access",
    "detail": (
        "The brief asks for automated research, AI article generation, publishing, click and "
        "conversion tracking. Program Policies Participation Requirements Section 2(b) limits "
        "price display to Amazon-served links or Creators API / PA API data; Section 6(s) bars "
        "artificially generated clicks or impressions; Section 6(t) bars review and star-rating "
        "display without API data. No Associates tag, PA-API or Creators API access exists in this "
        "environment, so none of these features is built and no values were simulated."
    ),
    "sources": ["https://affiliate-program.amazon.com/help/operating/policies"],
    "status": "Needs review",
    "action": (
        "Obtain Associates approval and PA-API / Creators API access, and confirm eligibility "
        "before any automation is connected. See also F-01, F-02, F-03, F-11 and F-12."
    ),
})
save("flags.json", flags)
print("flags.json: F-05 resolved; F-10 variance note added; F-17 (RV-I3) added.")

# ---- content.json ------------------------------------------------------
content = load("content.json")

for a in content["analysis"]:
    if a["id"] == "A-02":
        a["finding"] = "All three brands are verified: P1 and P3 are Chefman; P2 is Emeril (manufacturer Emeril Lagasse)."
        a["basis"] = (
            "Brand byline on P1 and P3 reads Chefman. P2's official page lists 'Brand Name | Emeril' "
            "and 'Manufacturer | Emeril Lagasse' in its Item details table (F-05 resolved 2026-11-14). "
            "The P2 page also shows store 'Emeril Store' and a byline 'Innovation IQ'."
        )
        a["confidence"] = "Verified"

bullets = content["executive_summary"]["bullets"]
brand_bullet = (
    "Brands verified: P1 and P3 are Chefman. P2's official product page lists Brand Name "
    "'Emeril' and Manufacturer 'Emeril Lagasse' in its Item details table (F-05 resolved)."
)
if not any(b.startswith("Brands verified") for b in bullets):
    bullets.insert(1, brand_bullet)

save("content.json", content)
print("content.json: A-02 updated; brand bullet added to the executive summary.")

# ---- sources.json ------------------------------------------------------
sources = load("sources.json")
for s in sources["sources"]:
    if s["id"] == "S-P2":
        s["used_for"] = (
            "Listing title, store and byline, category breadcrumb, specification table, also-viewed "
            "ASINs, brand and manufacturer from the Item details table, price and rating (withheld from site)"
        )
        s["notes"] += (
            " Re-checked 2026-11-14 by session arena/ebf5c261-zone4: Item details table shows "
            "'Brand Name | Emeril' and 'Manufacturer | Emeril Lagasse'."
        )
save("sources.json", sources)
print("sources.json: S-P2 used_for and notes updated.")
