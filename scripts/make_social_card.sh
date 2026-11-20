#!/usr/bin/env bash
# Builds docs/social-card.png, the social preview image referenced by og:image
# and twitter:image on every page (suggestion S-09, 2026-11-19).
#
# Deliberately text-and-shape only: no product photography. Suggestion S-18
# (real product photography, never generated or copied imagery) is still
# waiting on an owner decision, so the card carries no appliance images.
# ImageMagick only, no external assets, so the QA audit's external-host rule
# keeps holding.
#
# The three numerals on the card are read from the registers through
# scripts/build_extras.py::publication_counts(), never typed here. Until
# 2026-11-20 they were literals (3, 2, 8) and the card kept asserting eight
# sourced guides after fourteen were published - the same drift class as flag
# F-94, on a surface no text gate could see (decision D-55, flag F-95).
# Usage: scripts/make_social_card.sh [out.png]
set -euo pipefail

OUT="${1:-docs/social-card.png}"

# Numerals come from the data files. If the register cannot be read, fail loudly
# rather than fall back to a remembered number.
COUNTS_JSON="$(python3 -c 'import json,sys; sys.path.insert(0,"scripts"); import build_extras; print(json.dumps(build_extras.publication_counts()))')"
read_counts() { python3 -c 'import json,sys; print(json.loads(sys.argv[1])[sys.argv[2]])' "$COUNTS_JSON" "$1"; }
N_AIR_FRYERS="$(read_counts air_fryers)"
N_THERMOMETERS="$(read_counts thermometers)"
N_GUIDES="$(read_counts published_guides)"
N_PRODUCTS="$(read_counts products)"
: "${N_AIR_FRYERS:?could not read air fryer count}" "${N_THERMOMETERS:?could not read thermometer count}"
: "${N_GUIDES:?could not read guide count}" "${N_PRODUCTS:?could not read product count}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

W=1200; H=630
F="DejaVu-Sans"; FB="DejaVu-Sans-Bold"
BG='#faf7f2'; PANEL='#ffffff'; INK='#23201b'; MUTED='#6b6459'
ACC='#b45309'; SOFT='#fdf0e0'; SIDE='#26221c'

card() { # out num label sub
  convert -size 328x178 xc:"$BG" \
    -fill "$SOFT" -draw "roundrectangle 0,0 327,177 16,16" \
    -fill "$ACC" -font "$FB" -pointsize 40 -annotate +24+74 "$2" \
    -fill "$INK" -font "$FB" -pointsize 18 -annotate +24+118 "$3" \
    -fill "$MUTED" -font "$F" -pointsize 15 -annotate +24+145 "$4" \
    "$TMP/$1.png"
}

card ca "$N_AIR_FRYERS" "air fryer formats" "basket, dual-basket, oven"
card cb "$N_THERMOMETERS" "meat thermometers" "instant-read, wireless"
card cc "$N_GUIDES" "sourced guides" "a receipt behind every figure"

convert -size ${W}x${H} xc:"$BG" \
  -fill "$SIDE" -draw "rectangle 0,0 46,${H}" \
  -fill "$ACC" -draw "rectangle 46,0 52,${H}" \
  -fill "$PANEL" -draw "roundrectangle 92,58 1108,86 14,14" \
  -fill "$ACC" -font "$FB" -pointsize 13 -annotate +112+78 'DISCLOSURE' \
  -fill "$SIDE" -font "$F" -pointsize 14 \
  -annotate +212+77 'As an Amazon Associate I earn from qualifying purchases.' \
  -fill "$ACC" -font "$FB" -pointsize 16 -annotate +96+140 'ZONE4  -  AIR FRYER AND KITCHEN BUYING GUIDES' \
  -fill "$INK" -font "$FB" -pointsize 60 -annotate +93+216 'Find the air fryer' \
  -fill "$INK" -font "$FB" -pointsize 60 -annotate +93+284 'that fits your kitchen.' \
  -fill "$MUTED" -font "$F" -pointsize 24 \
  -annotate +96+336 "$N_PRODUCTS countertop appliances compared on the numbers their" \
  -fill "$MUTED" -font "$F" -pointsize 24 \
  -annotate +96+370 'listings actually state: size, format and counter depth.' \
  "$TMP/ca.png" -geometry +92+404 -composite \
  "$TMP/cb.png" -geometry +436+404 -composite \
  "$TMP/cc.png" -geometry +780+404 -composite \
  -fill "$MUTED" -font "$F" -pointsize 15 \
  -annotate +96+608 'No prices, star ratings or hands-on claims are published.' \
  "$OUT"

identify "$OUT"
