"""Click / conversion / earnings ledger with Amazon's attribution rules.

The ledger is an *append-only JSONL file* the operator populates from authorized
reporting (Associates Central reports, or your own analytics export). This module
never synthesises events: with an empty ledger every rollup is ``None`` and the
site prints "not connected", which is the honest state of this workspace
(flag F-010).

Attribution implemented from the official Program Policies text (source S2):

* a Session starts at the Special-Link click and ends 24 h later, when the
  customer orders a non-digital product, or when they click *another* publisher's
  link — whichever comes first;
* a cart order may complete up to 89 days after the click;
* the product must ship/be paid for within 180 days of purchase.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Iterator

SESSION_HOURS = 24
CART_WINDOW_DAYS = 89
SHIP_WINDOW_DAYS = 180

EVENT_TYPES = ("impression", "click", "session", "order", "refund")


class EventError(ValueError):
    pass


@dataclass
class Event:
    ts: str                    # ISO-8601 UTC
    type: str                  # one of EVENT_TYPES
    ref: str | None = None     # entity/product reference
    href: str | None = None
    amount: float | None = None
    currency: str = "USD"
    other_tag: str | None = None   # set when another publisher's link was clicked
    order_status: str | None = None
    source: str = "manual"     # where the event came from (associates-report, analytics-export…)

    def __post_init__(self) -> None:
        if self.type not in EVENT_TYPES:
            raise EventError(f"type {self.type!r} must be one of {EVENT_TYPES}")
        if self.source == "synthetic-example":
            raise EventError("Synthetic events are refused; the ledger is for observed data only.")
        datetime.fromisoformat(self.ts.replace("Z", "+00:00"))

    @property
    def moment(self) -> datetime:
        return datetime.fromisoformat(self.ts.replace("Z", "+00:00"))


class Ledger:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else None
        self.events: list[Event] = []
        if self.path and self.path.exists():
            self.load()

    # -- io --------------------------------------------------------------
    def load(self) -> int:
        self.events = []
        n = 0
        if not (self.path and self.path.exists()):
            return 0
        for line in self.path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                self.events.append(Event(**json.loads(line)))
                n += 1
            except (EventError, ValueError, TypeError) as exc:
                raise EventError(f"{self.path}:{n + 1}: {exc}") from exc
        self.events.sort(key=lambda e: e.moment)
        return n

    def append(self, *events: Event) -> None:
        if not self.path:
            raise EventError("Ledger has no path; pass a file to append to.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as fh:
            for e in events:
                fh.write(json.dumps(asdict(e)) + "\n")
                self.events.append(e)
        self.events.sort(key=lambda ev: ev.moment)

    def __iter__(self) -> Iterator[Event]:
        return iter(self.events)

    def __len__(self) -> int:
        return len(self.events)

    # -- session model ---------------------------------------------------
    def sessions(self) -> list[list[Event]]:
        """Group events into per-ref click→session chains honouring the resets."""
        by_ref: dict[str, list[Event]] = {}
        for e in self.events:
            by_ref.setdefault(e.ref or "_", []).append(e)
        chains: list[list[Event]] = []
        for _, evs in by_ref.items():
            cur: list[Event] = []
            for ev in evs:
                if ev.type == "click":
                    if cur:
                        chains.append(cur)
                    cur = [ev]
                    continue
                if ev.type == "click_foreign":
                    if cur:
                        chains.append(cur)
                    cur = []
                    continue
                if cur:
                    head = cur[0].moment
                    if ev.type == "order":
                        if head + timedelta(hours=SESSION_HOURS) >= ev.moment or \
                                head + timedelta(days=CART_WINDOW_DAYS) >= ev.moment:
                            cur.append(ev)
                    else:
                        if head + timedelta(hours=SESSION_HOURS) >= ev.moment:
                            cur.append(ev)
            if cur:
                chains.append(cur)
        return chains

    def attributed_orders(self) -> list[Event]:
        out = []
        for chain in self.sessions():
            for ev in chain:
                if ev.type == "order":
                    out.append(ev)
        return out

    # -- rollups ---------------------------------------------------------
    def rollup(self) -> dict:
        clicks = [e for e in self.events if e.type == "click"]
        imps = [e for e in self.events if e.type == "impression"]
        orders = self.attributed_orders()
        paid = [o for o in orders if (o.order_status or "shipped") in {"shipped", "paid", "completed"}]
        revenue = sum(o.amount or 0 for o in paid) if any(o.amount for o in paid) else None
        ctr = (len(clicks) / len(imps)) if imps else None
        conv = (len(orders) / len(clicks)) if clicks and orders else None
        return {
            "events_recorded": len(self.events),
            "impressions": len(imps) if imps else None,
            "clicks": len(clicks) if clicks else None,
            "orders_attributed": len(orders) if orders else None,
            "click_through_rate": round(ctr, 4) if ctr is not None else None,
            "conversion_rate": round(conv, 4) if conv is not None else None,
            "earnings": round(revenue, 2) if revenue is not None else None,
            "earnings_per_click": round(revenue / len(clicks), 4)
            if (revenue and clicks) else None,
            "connected": bool(self.events),
            "empty_state": None if self.events else "No authorized reporting connected (flag F-010).",
            "windows": {
                "session_hours": SESSION_HOURS,
                "cart_window_days": CART_WINDOW_DAYS,
                "ship_window_days": SHIP_WINDOW_DAYS,
                "source": "https://affiliate-program.amazon.com/help/operating/policies",
            },
        }

    def per_ref(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for ref in sorted({e.ref for e in self.events if e.ref}):
            sub = Ledger(None)
            sub.events = [e for e in self.events if e.ref == ref]
            out[ref] = sub.rollup()
        return out


def from_records(records: Iterable[dict]) -> Ledger:
    led = Ledger(None)
    led.events = [Event(**r) for r in records]
    led.events.sort(key=lambda e: e.moment)
    return led


def export_report(led: Ledger, dest: Path | None = None) -> dict:
    report = {"rollup": led.rollup(), "by_reference": led.per_ref()}
    if dest:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(report, indent=2))
    return report
