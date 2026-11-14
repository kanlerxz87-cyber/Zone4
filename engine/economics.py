"""Commission and unit-economics math.

Only two things here are Amazon facts: the fixed category rates (Table 1 of the
Standard Commission Income Statement, source S1) and the attribution window
(Program Policies, source S2). Everything else is arithmetic on those facts and
on values the operator supplies. When an input is missing the answer is
``None`` — not zero, not an industry average.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .datastore import Datastore

#: Session ends 24 hours after the click (source S2).
SESSION_HOURS = 24
#: A cart order may be completed up to 89 days after the click (source S2).
CART_WINDOW_DAYS = 89
#: Product must ship/be paid for within 180 days of purchase (source S2).
SHIP_WINDOW_DAYS = 180
#: Prerequisite for Creators API access (source S4).
API_QUALIFYING_SALES_30D = 10


@dataclass
class Rate:
    categories: str
    rate_pct: float

    @property
    def decimal(self) -> float:
        return self.rate_pct / 100.0


def rate_table(store: Datastore) -> list[Rate]:
    return [Rate(r["categories"], float(r["rate_pct"])) for r in store.commission_rows()]


def rate_for(store: Datastore, category: str | None) -> Rate | None:
    pct = store.rate_for_category(category)
    if pct is None:
        return None
    for row in store.commission_rows():
        if any(part.strip().lower() == (category or "").strip().lower() for part in row["categories"].split(",")):
            return Rate(row["categories"], pct)
    return Rate("All Other Categories", pct)


@dataclass
class UnitEconomics:
    """Earnings for one qualifying order. Any unknown input ⇒ unknown output."""

    price: float | None
    rate_pct: float | None
    currency: str = "USD"
    quantity: int = 1

    @property
    def resolvable(self) -> bool:
        return self.price is not None and self.rate_pct is not None and self.quantity > 0

    @property
    def gross(self) -> float | None:
        if not self.resolvable:
            return None
        return round(self.price * self.quantity, 2)

    @property
    def commission(self) -> float | None:
        """Commission on Qualifying Revenue. ``None`` if price or category rate is unverified."""
        if not self.resolvable:
            return None
        return round(self.gross * (self.rate_pct / 100.0), 4)

    @property
    def missing(self) -> list[str]:
        out = []
        if self.price is None:
            out.append("price (no verified Amazon product page)")
        if self.rate_pct is None:
            out.append("category commission rate (category unknown)")
        return out

    def explain(self) -> str:
        if self.commission is None:
            return "Not calculable — missing: " + "; ".join(self.missing)
        return (f"{self.quantity} × {self.currency} {self.gross:,.2f} × {self.rate_pct:.2f}% "
                f"= {self.currency} {self.commission:,.4f} per order")


def unit_economics(price: float | None, rate_pct: float | None, currency: str = "USD",
                   quantity: int = 1) -> UnitEconomics:
    return UnitEconomics(price=price, rate_pct=rate_pct, currency=currency, quantity=quantity)


def epc(commission_per_sale: float | None, clicks: int | None, earnings: float | None) -> float | None:
    """Earnings per click. Refuses to invent either side of the fraction."""
    if commission_per_sale is None or not clicks or earnings is None:
        return None
    return round(earnings / clicks, 6)


def revenue_model(store: Datastore, category: str | None, price: float | None,
                  monthly_clicks: int | None = None, conv_rate: float | None = None) -> dict:
    """Full funnel for one product. Every unavailable input is reported, not guessed."""
    rate = rate_for(store, category)
    econ = unit_economics(price, rate.rate_pct if rate else None)
    missing = list(econ.missing)
    if monthly_clicks is None:
        missing.append("monthly clicks (no analytics connected — flag F-010)")
    if conv_rate is None:
        missing.append("conversion rate (no authorized reporting connected)")
    orders = revenue = None
    if monthly_clicks and conv_rate is not None and econ.commission is not None:
        orders = round(monthly_clicks * conv_rate, 4)
        revenue = round(orders * econ.commission, 2)
    return {
        "category": category,
        "commission_rate_pct": rate.rate_pct if rate else None,
        "rate_source": store.source_url("S1"),
        "price": price,
        "commission_per_order": econ.commission,
        "explanation": econ.explain(),
        "monthly_clicks": monthly_clicks,
        "conversion_rate": conv_rate,
        "projected_orders_per_month": orders,
        "projected_revenue_per_month": revenue,
        "missing_inputs": missing,
        "publishable": False,  # a projection is a claim about the future; never auto-published
    }


def bounty_summary(store: Datastore) -> Iterable[dict]:
    return store.bounties()
