# Rendered publication checks

HTML/source checks cannot establish whether the disclosure is inside the first screen or a menu fits on a phone. This separate, pinned Playwright tool checks the generated `docs/` site in Chromium. It is not shipped to readers and does not collect traffic or contact Amazon.

From the repository root:

```sh
python3 scripts/build_site.py
npm ci --prefix qa/browser
cd qa/browser
npx playwright install --with-deps chromium
npm run check
```

The checker starts and closes its own temporary static server. It checks every published page at 320×568, 375×667, 390×844, 768×1024 and 1440×1000: document overflow, visible above-fold Associates disclosure under the masthead, one headline, disabled collection, missing resources and JavaScript errors. It also opens each native menu with the keyboard on phone and desktop layouts **with page JavaScript disabled**, focuses the first and last menu links, checks the panel fits, and confirms every footer destination remains in the navigation.

All external requests are blocked and reported as failures. No sponsored product destination is activated, no telemetry is enabled, and no event is written to the campaign ledger. Results and a failure screenshot go to ignored `build/browser-qa/results/`; they describe local layout fixtures, not reader behavior, deployed collector acceptance or Amazon reporting.

On a restricted machine that already provides a compatible Chromium binary, set `ZONE4_CHROMIUM_EXECUTABLE` to its path instead of downloading a browser. Any system-library configuration is local tooling setup, not part of the public site. CI uses the pinned Playwright installer normally. The separate Node/Python measurement tests remain the authoritative payload and HTTP contracts; this rendered-layout check does not replace deployment acceptance.
