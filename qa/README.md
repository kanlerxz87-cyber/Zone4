# QA audit (independent site checks)

`audit_site.py` is an **independent** quality audit of the committed site in
`docs/` plus the root GitHub Pages entry point. It complements — and does not
replace — `scripts/verify.py` (which rebuilds from `data/` and checks data
validity). This audit runs against the committed HTML as-is, so it also catches
hand-edits or a stale commit.

## Run

```bash
python3 qa/audit_site.py            # local audit of docs/
python3 qa/audit_site.py --live     # + GitHub Pages API status (needs network)
```

Exit code `0` = pass (warnings may be printed); `1` = at least one failure.

## Hard failures

| Check | Why |
|---|---|
| Root `index.html` → `docs/` redirect, root & `docs/` `.nojekyll` | GitHub Pages serves `main /` (legacy source) |
| Disclosure sentence on every page | Associates Operating Agreement §5 |
| Exactly one `<h1>`, `lang`, `<title>`, meta description, viewport, skip link | SEO / accessibility baseline |
| Unique element ids | Anchor integrity |
| Every internal link and `#anchor` resolves | "No broken links" merge rule |
| External anchors: official hosts only, `rel="noopener noreferrer"` | Source integrity + tab-nabbing guard |
| Every table body row links to an official source | Brief: every table row needs an official source link |
| No currency amounts, no star-rating patterns | Participation Requirements 2(b) / 3(t) |
| No location-claim residue (`Bucharest`/`Romania`) | Flag F-09 regression guard |
| Shop links only to the three supplied `link.amazon` short links, with the disclosure sentence in the same table row | Link-level disclosure near each affiliate link |
| `products.html` lists all three ASINs and all three short links | Coverage of the three supplied products |

## Warnings (reported, non-blocking)

- External `<script>`/`<link>`/`<iframe>` hosts outside the official set
  (for example analytics injected by a future change).
- A page in `docs/` that the shared sidebar nav does not reach, or a nav target
  missing on disk.
- Nav pages without exactly one `aria-current="page"`.
- Tables without `<thead>` or header cells missing `scope="col"`.

`--strict-warnings` promotes warnings to failures. CI runs the plain mode so
that content added by other sessions is never blocked by advisory findings.

## CI

`.github/workflows/qa.yml` runs this audit on every pull request and on pushes
to `main`, independently of the `Site checks` workflow.
