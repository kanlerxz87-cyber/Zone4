# Zone4 measurement endpoint

A small, self-hosted endpoint for the five defined events (see `docs/measurement.html`).

- Accepts only `page_view`, `outbound_click`, `guide_read_75`, `category_click`, `feed_click`.
- Stores **daily counts per event and path** (and per ASIN for outbound clicks). It does not store the client address, user agent, referrer, cookies or any visitor identifier, and it writes no request log.
- Standard library only: `python3 analytics-endpoint/server.py --host 0.0.0.0 --port 8787`.
- `counts.json` is created next to the server; it is listed in `.gitignore` so counts are never committed.

**Not hosted.** GitHub Pages serves static files only, so this endpoint has to run on a host the owner controls. Until it does, the site sends no measurement request. To switch it on: host the server, set `MEASURE_ENDPOINT` in `scripts/build_extras.py` to its `/event` URL, and rebuild with `python3 scripts/build_site.py`.
