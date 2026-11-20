# Zone4 aggregate measurement collector

**Built and tested; not deployed.** GitHub Pages is [static hosting](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages). No shared analytics endpoint or Amazon order feed is connected to the public site. Do not treat local test counts as reader activity.

## Contract

| Event | Accepted dimensions | Stored aggregate |
|---|---|---|
| `page_view` | Published page path | UTC day → path → count |
| `outbound_click` | Published page path, one of the five intended ASINs | Day → path → count; day → ASIN → count |
| `guide_read_75` | Published page path | Day → path → count (once per guide page load in the browser) |
| `category_click` | Published page path, existing category slug | Day → path → count; day → category → count |
| `feed_click` | Published page path | Day → path → count |

Implementation source for every row: [`server.py`](server.py), generated browser script [`../docs/measure.js`](../docs/measure.js), definitions in [`../scripts/build_extras.py`](../scripts/build_extras.py). These are project-defined events, **not events or attribution rules defined by Amazon**.

- No cookies, client address, user agent, referrer, visitor/session identifier, query string, free text or individual event timestamp is stored by the application. Additional JSON fields are rejected, even if they would not have been saved.
- Paths, category slugs and ASINs are allowlisted from this checkout's `docs/` and product-intent register. Deploy the whole checkout; restart after publishing new pages/products so the allowlists refresh.
- The browser honours Do Not Track and Global Privacy Control. It sends credential-free, no-referrer `fetch` requests with keepalive and never delays a product link or queues a failed event.
- POST requires the configured exact Origin. CORS alone is not a write barrier. Origin is **not authentication**: a non-browser client can forge it. These are approximate event counts, not bot-filtered, deduplicated or independently audited traffic.
- JSON payloads are capped at 512 bytes; input types, fields and dimensions are checked before storage; write failures return 503; updates use a lock and atomic replacement. Use **one collector process and one local persistent volume**. The in-process lock does not make multiple workers or replicas safe.
- A rolling 90-day UTC aggregate window is pruned on startup and each write. Schedule the prune command daily as well, including inactive days. Do not retain backups beyond the chosen window without a separate policy.
- The application writes no request logs. A host/proxy may log IP addresses; logging at that layer is a separate deployment responsibility. [GitHub Pages itself logs visitor IP addresses for security](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages#data-collection).

## Local verification (not production activation)

```sh
python3 -m unittest discover -s tests -p test_analytics_endpoint.py -v
python3 analytics-endpoint/server.py --host 0.0.0.0 --port 8787
```

`GET /health` returns 204. `POST /event` returns 204 only for an accepted event; errors return 400/403/413/415/503. No counts or report HTTP endpoint is exposed. Read `counts.json` on the server through authorized host access; it is gitignored and must not be committed. There is no conversion dashboard populated by fabricated data.

Daily prune command (same volume and user as the running single-process server; schedule outside request handling, not concurrently with another writer):

```sh
python3 analytics-endpoint/server.py --counts /persistent/zone4/counts.json --prune-only
```

Stop the collector for the daily prune operation, run the command, then restart it; or rely on continuous genuine writes with an independently scheduled controlled maintenance window for inactive periods. The file lock is process-local.

## Production gate — do not claim this is live until checked

1. Provision an owner-controlled HTTPS host and persistent disk. No such service credentials or host are available to this session. Do not use an ephemeral Arena preview URL as a production endpoint.
2. Put the single process behind an HTTPS reverse proxy with request/body/connection limits and access logs disabled or separately reviewed. The standard-library server is not a public production edge. Capacity/load testing and abuse filtering remain open.
3. Set exact allowed origin (`--origin https://kanlerxz87-cyber.github.io`), ensure only published paths/products are accepted, configure the daily pruning maintenance job, and review privacy text and any applicable consent requirements.
4. Set `MEASURE_ENDPOINT` in `scripts/build_extras.py` to the permanent HTTPS `/event` URL and rebuild the static site. Empty remains the safe default. End-to-end check all five events, DNT/GPC opt-out, zero cookies/identifiers, network failure behaviour and persistence after restart. Exclude those synthetic checks from production reports.
5. Keep the [campaign ledger](../data/ledger.json) empty until authorized Amazon reports are actually obtained. A click is not an order; page views are not eligible sessions; no event ratio here is an Amazon conversion rate. Amazon's [Operating Agreement](https://affiliate-program.amazon.com/help/operating/agreement) and [Program Policies](https://affiliate-program.amazon.com/help/operating/policies) govern the separate Associates workflow.

All five events are implemented, but **durable hosting, account verification, conversion reporting and real traffic measurements remain unverified** (F-57/F-58/F-59/F-61). No product prices, ratings, revenue or search volume are collected by this endpoint.
