# Zone4 measurement endpoint

A small, self-hosted endpoint for the five defined events (see `docs/measurement.html`).

- Accepts only `page_view`, `outbound_click`, `guide_read_75`, `category_click`, `feed_click`.
- Stores **daily counts per event and path** (and per ASIN for outbound clicks). It does not store the client address, user agent, referrer, cookies or any visitor identifier, and it writes no request log.
- Standard library only: `python3 analytics-endpoint/server.py --host 0.0.0.0 --port 8787`.
- `counts.json` is created next to the server; it is listed in `.gitignore` so counts are never committed.

**Not hosted.** GitHub Pages serves static files only, so this endpoint has to run on a host the owner controls. Until it does, the site sends no measurement request. To switch it on: host the server, set `MEASURE_ENDPOINT` in `scripts/build_extras.py` to its `/event` URL, and rebuild with `python3 scripts/build_site.py`.

## Go-live decision checklist

| Question | Current answer | Evidence to collect before enabling |
|---|---|---|
| Can Pages run the collector? | No. It serves the static publication. | Confirm an owner-controlled HTTPS service and persistent storage. [GitHub Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/about-github-pages) |
| Does the collector reject unrelated browser origins? | Yes: POST requires the configured Origin. This is not authentication; non-browser clients can supply that header. | Check allowed browser delivery and rejection of other origins on staging; put rate limits at the ingress. [Collector implementation](https://github.com/kanlerxz87-cyber/Zone4/blob/main/analytics-endpoint/server.py) |
| Are measurements free of visitor identifiers? | The application writes aggregate counts and no request log. Hosting infrastructure is not verified. | Review proxy and hosting logging, restrict access to the aggregate file, and use a single collector process per count file. [Collector implementation](https://github.com/kanlerxz87-cyber/Zone4/blob/main/analytics-endpoint/server.py) |
| Do clicks confirm orders? | No. None of the five events records a purchase. | Keep test traffic out of production counts; use authorized Associates reporting for orders and preserve report dates and provenance. [Associates Central](https://affiliate-program.amazon.com/) |

Before enabling on Pages, test all five events from a staging origin with a temporary counts file, check the daily totals, and confirm Do Not Track and Global Privacy Control suppress requests. These are release checks, not evidence of live traffic or attribution.
