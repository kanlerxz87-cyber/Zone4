# Zone4 measurement reference collector

**Built and tested; not collecting production traffic.** The generated site emits an empty endpoint while `data/measurement.json` is disabled. A URL alone cannot enable it: the build also requires dated evidence and a reviewer for all five launch checks on the [Measurement page](https://kanlerxz87-cyber.github.io/Zone4/docs/measurement.html#launch-checklist).

This is a reference implementation, **not a production web server**. Python [explicitly does not recommend `http.server` for production](https://github.com/python/cpython/blob/3.11/Doc/library/http.server.rst). Do not expose this process directly to the internet or mistake a successful Pages deployment for commercial-hosting approval.

## Exact contract

| Event | Required fields | Stored aggregates | Source |
|---|---|---|---|
| `page_view` | `event`, `path` | UTC day / known canonical page path | [First-party contract](https://github.com/kanlerxz87-cyber/Zone4/blob/main/analytics-endpoint/server.py) |
| `outbound_click` | `event`, `path`, `asin` | Separate UTC day / source-path and UTC day / catalog-ASIN counts | [First-party contract](https://github.com/kanlerxz87-cyber/Zone4/blob/main/analytics-endpoint/server.py) |
| `guide_read_75` | `event`, `path` (a published guide or article) | UTC day / guide path; a visible marker, not proof of reading | [First-party contract](https://github.com/kanlerxz87-cyber/Zone4/blob/main/analytics-endpoint/server.py) |
| `category_click` | `event`, `path`, `target` (a known category path) | Separate UTC day / source-path and UTC day / category-target counts | [First-party contract](https://github.com/kanlerxz87-cyber/Zone4/blob/main/analytics-endpoint/server.py) |
| `feed_click` | `event`, `path` | UTC day / source path; not a subscription count | [First-party contract](https://github.com/kanlerxz87-cyber/Zone4/blob/main/analytics-endpoint/server.py) |

The authoritative [implementation](server.py) accepts only these schemas and the public routes in the built sitemap, category paths and published intent-record ASINs. Unknown fields, paths, ASINs, targets, duplicate JSON keys, non-JSON bodies and bodies over 512 bytes are refused. No query string, fragment, affiliate URL, raw event, client address, user agent, cookie, Referer or visitor identifier is written. Application request logging is disabled; **the host, proxy, CDN and network still receive connection metadata**, and their logs are outside this application's control.

`client.js` is the single browser source; `scripts/build_extras.py` compiles it into `docs/measure.js` with the same route/catalog allowlists. It omits credentials and Referer, does not follow receiver redirects, honors DNT/GPC before every send, ignores synthetic/cancelled activations, and never delays or redirects the outbound link. Preview hosts do not send to production. Delivery is best-effort, with no retry or unique-person/session inference.

POST and OPTIONS require the configured exact Origin. This is **not authentication or bot detection**: a non-browser caller can forge Origin. No event is a verified Amazon click or reported order. The collector never writes to `data/ledger.json` or `data/tracking.jsonl`.

## Local tests only

From the repository root, with Python 3.11+ and Node 22:

```sh
python3 scripts/build_site.py
node --test tests/measure_client.test.js
python3 -m unittest discover -s tests -p 'test_analytics_endpoint.py' -v
python3 -m unittest discover -s tests -p 'test_measurement_client.py' -v
```

The tests use temporary count files, intercept outbound destinations, exercise the generated client through a temporary local HTTP collector, and delete the fixtures. They do **not** navigate Amazon, create affiliate clicks, generate a purchase, or create a report row. Do not import fixture counts into production or campaign performance.

To inspect the reference runtime manually:

```sh
python3 analytics-endpoint/server.py --host 0.0.0.0 --port 8787
```

Only `/health` is public GET output; no count-export route exists. POSTs to `/event` require the allowed Origin, JSON content type and a valid bounded payload. Server-side DNT/GPC opt-outs also suppress recording. Store files are atomically replaced with private `0600` permissions. Use **one collector process per count file**; the lock protects threads, not multiple processes. The repository, built sitemap and catalog must accompany the reference runtime. Health returns 200/`ok` while storage is available, or 503/`unavailable` after a storage failure; it does not export traffic.

## Retention and failure behavior

The staged maximum in `data/measurement.json` is **30 UTC day buckets including today** (configurable from 1–90). Expired and future buckets are pruned on writes, at startup, and hourly while the process is running—even without a page event. For cleanup independent of a stopped collector, schedule this separately on the selected host:

```sh
python3 analytics-endpoint/server.py --prune-only --counts /private/zone4/counts.json
```

Run standalone pruning only while the collector is stopped: the lock is process-local, so a concurrent CLI writer could lose updates. The running collector uses its own hourly maintenance instead. This command adds no event and does not create an absent file. Host logs, backups, snapshots and stopped-service schedules need separate expiry rules; the application cannot delete them. `counts.json` and `.counts-*` are ignored by Git and must never be published.

A corrupt or unrecognized store fails closed: POST returns 503, health becomes unavailable, and the file is not replaced with invented empty counts. Startup also refuses a corrupt store. Deploy client, sitemap and catalog together; removing routes/ASINs requires an explicit aggregate-store migration/deletion review, not a silent reset. Preserve provenance for any retained export.

## Review before activation

The five source-linked questions, current facts, missing evidence and discovery steps live in **one register**: [`data/measurement.json`](../data/measurement.json), rendered to `docs/measurement.html`. Their confirmation fields are currently null.

1. **Permitted hosting:** [GitHub Pages limits](https://github.com/github/docs/blob/main/content/pages/getting-started-with-github-pages/github-pages-limits.md) restrict free hosting for an online business or a site primarily facilitating commercial transactions. Obtain hosting-use clarification or use a host that permits this business model; a reference label alone is not permission.
2. **Production runtime:** reviewed HTTPS, exact origin, request/body/time limits, rate limits, storage access, durable operations and an appropriately secured production service—not direct internet exposure of `http.server`.
3. **Privacy/consent:** actual controller/provider details, visitor-facing terms, applicable consent decision and every logging layer. [GitHub documents security IP logging for Pages](https://github.com/github/docs/blob/main/content/pages/getting-started-with-github-pages/what-is-github-pages.md); do not call the entire service anonymous.
4. **Deletion:** agreed retention, file permissions, quiet/stopped-service cleanup, backup expiry and log deletion tested on isolated dated fixtures.
5. **Deployment contract:** all five events, opt-outs and rejections tested with isolated staging counts and intercepted Amazon destinations. Preserve the dated evidence reference and reviewer; never generate artificial affiliate traffic or test purchases ([Associates Participation Requirements 6(s)/(u)](https://affiliate-program.amazon.com/help/operating/policies)).

After real evidence exists, record it, set the durable HTTPS `/event` URL and `enabled: true` in `data/measurement.json`, rebuild, and rerun the complete checks. This gate checks evidence **completeness**, not legal approval or live uptime. Update the canonical origin and every related sitemap/feed/redirect setting together if migrating. Search Console verification, tag registration and the one-link-per-product Associates report check remain separate account-side gates (F-57/F-58/F-61).
