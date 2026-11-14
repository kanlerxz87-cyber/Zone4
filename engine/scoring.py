"""Opportunity scoring for niches and products.

A score is a claim about profitability, so the model refuses to run without the
verified inputs it needs. ``score_product`` returns a ``ScoreResult`` with
``value is None`` and an explicit list of what is missing — which is exactly
what the site renders, instead of a plausible-looking number with no basis.

Weights are documented, tunable, and *not* presented as an Amazon-endorsed
model: they are this workspace's editorial heuristic, declared here so a human
can change them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_WEIGHTS = {
    "commission_rate": 0.25,   # official Table 1 rate for the category
    "price_band": 0.15,        # higher AOV ⇒ more absolute earnings per order
    "rating": 0.20,            # buyer satisfaction signal
    "review_volume": 0.20,     # demand + social proof (log-scaled)
    "competition": 0.20,       # inverse of review-count concentration
}
REQUIRED = ["commission_rate_pct", "price", "star_rating", "review_count"]


@dataclass
class ScoreResult:
    ref: str
    value: float | None
    inputs: dict = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    rationale: str = ""

    @property
    def publishable(self) -> bool:
        return self.value is not None and not self.missing

    def display(self) -> str:
        return f"{self.value:.1f}/100" if self.value is not None else ""


def _rating_component(rating: float) -> float:
    # 4.0 → 0, 5.0 → 100, clipped below 3.5.
    return max(0.0, min(100.0, (rating - 4.0) / 1.0 * 100.0))


def _volume_component(reviews: float) -> float:
    import math
    return max(0.0, min(100.0, (math.log10(max(reviews, 1)) - 1) / 3.0 * 100.0))


def _price_component(price: float, lo: float = 25.0, hi: float = 300.0) -> float:
    return max(0.0, min(100.0, (price - lo) / (hi - lo) * 100.0))


def _competition_component(reviews: float, players: int | None = None) -> float:
    """Lower review counts among the competing set ⇒ easier to rank.

    Without a verified competitor set this returns ``None`` upstream, which is
    why competition is only scored when ``players`` is supplied.
    """
    if players is None:
        return None
    ratio = reviews / max(players, 1)
    return max(0.0, min(100.0, 100.0 - min(ratio, 1000.0) / 10.0))


def score_product(ref: str, attrs: dict, weights: dict | None = None,
                  competitor_count: int | None = None) -> ScoreResult:
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)
    missing = [k for k in REQUIRED if attrs.get(k) in (None, "", [])]
    inputs: dict[str, float] = {}
    parts: list[str] = []

    if not missing:
        rate = float(attrs["commission_rate_pct"])
        inputs["commission_rate"] = max(0.0, min(100.0, rate / 10.0 * 100.0))  # 10% = full marks
        parts.append(f"commission {rate:.2f}% → {inputs['commission_rate']:.1f}")
        inputs["price_band"] = _price_component(float(attrs["price"]))
        parts.append(f"price {float(attrs['price']):.2f} → {inputs['price_band']:.1f}")
        inputs["rating"] = _rating_component(float(attrs["star_rating"]))
        parts.append(f"rating {float(attrs['star_rating']):.2f} → {inputs['rating']:.1f}")
        inputs["review_volume"] = _volume_component(float(attrs["review_count"]))
        parts.append(f"reviews {int(attrs['review_count'])} → {inputs['review_volume']:.1f}")
        comp = _competition_component(float(attrs["review_count"]), competitor_count)
        if comp is None:
            missing.append("verified competitor set for the category (competition sub-score)")
        else:
            inputs["competition"] = comp
            parts.append(f"competition → {comp:.1f}")

    if missing:
        return ScoreResult(ref=ref, value=None, inputs=inputs, missing=missing,
                           rationale="Score withheld; missing verified inputs: " + ", ".join(missing))

    total = sum(w[k] * inputs[k] for k in inputs)
    return ScoreResult(ref=ref, value=round(total, 1), inputs=inputs, missing=[],
                       rationale="Weighted sum of verified components: " + "; ".join(parts))


def score_all(store, entities) -> dict[str, dict]:
    """Score every entity that has verified inputs; report the rest as withheld."""
    out: dict[str, dict] = {}
    for ent in entities:
        attrs = {k: (c.value if c and c.status.publishable else None) for k, c in ent.claims.items()}
        res = score_product(ent.ref, attrs)
        out[ent.ref] = {
            "score": res.value,
            "inputs": {k: round(v, 2) for k, v in res.inputs.items()},
            "missing": res.missing,
            "rationale": res.rationale,
            "publishable": res.publishable,
        }
    return out


def niche_shortlist(store, candidates: list[dict] | None = None) -> dict:
    """Niche selection table.

    ``candidates`` must be records already carrying verified category + rate +
    demand evidence. With none supplied (the current state of this workspace)
    the model returns an empty shortlist plus the reason, rather than inventing
    profitable niches.
    """
    rows = [c for c in (candidates or []) if c.get("verified")]
    return {
        "rows": rows,
        "count": len(rows),
        "withheld_reason": store.niche_scoring().get(
            "note", "No candidate niche has verified demand, competition, and rate evidence."),
        "how_to_populate": (
            "Use Creators API SearchItems/GetBrowseNodes for category structure and product counts "
            "(requires the 10-qualifying-sales prerequisite), then attach the official rate from Table 1. "
            "See https://affiliate-program.amazon.com/creatorsapi/docs/en-us/introduction"
        ),
    }
