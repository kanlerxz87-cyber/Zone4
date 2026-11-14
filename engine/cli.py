"""Command line entry point: ``python -m engine <command>``.

Commands
--------
status        what is verified, what is withheld, what is blocking publication
verify        re-run the identifier + product-page checks for every product
rates         print the official commission table (and a single lookup)
economics     per-product unit economics, honest about missing inputs
audit         compliance evaluation of a generated page (default: all drafts)
content       render draft docs and print their publish-gate result
links         show the Special Link the builder would emit (or refuse)
tracking      rollups from data/tracking.jsonl (empty ⇒ nulls, never zeros)
build         render the site from the verified data and self-check it
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .agent import Agent
from .config import Config
from .datastore import DataError, Datastore
from .links import build_link
from .research import extract_identifier
from .claims import validate_asin_format


def _agent(args) -> Agent:
    cfg = Config.load(Path(args.config) if getattr(args, "config", None) else None)
    if getattr(args, "root", None):
        cfg.data_dir = Path(args.root) / "data"
    return Agent(cfg=cfg)


def cmd_status(args) -> int:
    a = _agent(args)
    report = a.run()
    print(json.dumps({"verification": report["verification"], "publish_gate": report["publish_gate"],
                      "flags_open": report["flags_open"], "tracking": report["tracking"]},
                     indent=2))
    return 0


def cmd_verify(args) -> int:
    cfg = Config.load()
    store = Datastore(Path(args.data_dir) if args.data_dir else cfg.data_dir)
    prober = None
    allow = bool(args.online)
    from .research import AmazonProber
    prober = AmazonProber(allow_network=allow)
    rows = 0
    for probe in store.findings["products"]:
        ident = extract_identifier(probe["supplied_url"])
        ok, detail = validate_asin_format(ident)
        probe_res = prober.probe(ident or "")
        verdict = "PASS" if ok else "FAIL"
        print(f"{probe['ref']}  {ident}  format={verdict}  ({detail})")
        print(f"        probe={probe_res.status.value.upper():9s} {probe_res.detail}")
        rows += 1
    print(f"\n{rows} references checked. "
          + ("Live probe enabled." if allow else "Live probe disabled (add --online to hit amazon.com)."))
    return 0


def cmd_rates(args) -> int:
    cfg = Config.load()
    store = Datastore(Path(args.data_dir) if args.data_dir else cfg.data_dir)
    if args.category:
        rate = store.rate_for_category(args.category)
        print(json.dumps({"category": args.category, "rate_pct": rate,
                          "source": store.source_url("S1")}, indent=2))
        return 0
    for row in store.commission_rows():
        print(f"{row['rate_pct']:>6.2f}%  {row['categories']}")
    print(f"\nSource: {store.source_url('S1')}  (retrieved 2026-11-14)")
    return 0


def cmd_economics(args) -> int:
    a = _agent(args)
    print(json.dumps(a.stage_economics(a.store.products()), indent=2, sort_keys=True))
    return 0


def cmd_audit(args) -> int:
    a = _agent(args)
    items = a.stage_gate(a.stage_content(a.store.products()))
    blocked = 0
    leaks = 0
    for item in items:
        state = "READY" if item.ready else "BLOCKED"
        blocked += 0 if item.ready else 1
        print(f"{state:8s} {item.doc_slug}")
        for r in item.reasons:
            print(f"         · {r}")
        # A draft that passed the gate must not still carry a placeholder: that
        # is an integrity failure, unlike a draft that is correctly withheld.
        if item.ready and any("UNRESOLVED" in str(r).upper() for r in item.reasons):
            leaks += 1
            print("         ! READY but unresolved — this draft must not publish")
    print(f"\n{len(items) - blocked}/{len(items)} ready · {blocked} blocked by gates")
    if leaks:
        print(f"FAILED: {leaks} draft(s) passed the gate while unresolved")
        return 1
    return 1 if (blocked and args.strict) else 0


def cmd_content(args) -> int:
    a = _agent(args)
    docs = a.stage_content(a.store.products())
    for doc in docs:
        print(f"{doc.slug}: {len(doc.placeholders)} placeholder(s), "
              f"disclosure={'yes' if doc.disclosures_present else 'NO'}")
    return 0


def cmd_links(args) -> int:
    cfg = Config.load()
    for raw in args.references:
        ident = extract_identifier(raw)
        try:
            link = build_link(ident or "", host=cfg.marketplace.host,
                              tag=args.tag or cfg.marketplace.partner_tag or "")
            print(f"OK   {link.url}")
        except Exception as exc:  # noqa: BLE001
            print(f"REFUSE {ident or raw}: {exc}")
    return 0


def cmd_tracking(args) -> int:
    a = _agent(args)
    print(json.dumps({"rollup": a.stage_tracking()}, indent=2))
    return 0


def cmd_build(args) -> int:
    from .sitegen import render_all, report_json
    a = _agent(args)
    out = Path(args.out) if args.out else (a.cfg.root / "build" / "site-preview")
    report = a.run()
    written = render_all(a.store, report, out)
    report_json(a.store, report, a.cfg.data_dir / "report.json")
    for name in sorted(written):
        print(f"wrote {name} ({len(written[name])} chars)")
    print(f"\npublish gate: {report['publish_gate']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m platform", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", help="path to config.json (optional)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status").set_defaults(func=cmd_status)
    v = sub.add_parser("verify"); v.add_argument("--online", action="store_true")
    v.add_argument("--data-dir"); v.set_defaults(func=cmd_verify)
    r = sub.add_parser("rates"); r.add_argument("--category"); r.add_argument("--data-dir")
    r.set_defaults(func=cmd_rates)
    e = sub.add_parser("economics"); e.set_defaults(func=cmd_economics)
    au = sub.add_parser("audit"); au.add_argument("--strict", action="store_true")
    au.set_defaults(func=cmd_audit)
    sub.add_parser("content").set_defaults(func=cmd_content)
    li = sub.add_parser("links"); li.add_argument("references", nargs="+"); li.add_argument("--tag")
    li.set_defaults(func=cmd_links)
    tr = sub.add_parser("tracking"); tr.set_defaults(func=cmd_tracking)
    bu = sub.add_parser("build"); bu.add_argument("--out"); bu.set_defaults(func=cmd_build)

    args = ap.parse_args(argv)
    try:
        return args.func(args)
    except DataError as exc:
        print(f"DATA ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
