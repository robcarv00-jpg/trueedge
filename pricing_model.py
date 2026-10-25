"""Sharp Mirror pricing model — what price maximizes revenue without
guessing willingness-to-pay we haven't measured?

Method (all assumptions labeled, no fake precision):
- Demand: constant-elasticity around a reference point. Reference: at
  $6.99/mo, 3.0% of activated free users convert (mid-range for consumer
  freemium). Three elasticity scenarios: -0.6 (loyal niche), -1.0 (unit),
  -1.5 (price-sensitive casuals). The truth is unknown until the cohort
  survey runs — so the pick must be ROBUST across scenarios (maximin),
  not optimal in one.
- Mix: 60% of subscribers take annual (priced at 50% of monthly x 12,
  the Pikkit/Action pattern), 40% monthly.
- Churn: monthly subs churn 7% + 0.25%/dollar of price; annual subs
  renew at 55%. Apple takes 15% (Small Business Program).
- Output: expected 24-month net revenue per 1,000 activated free users.

Competitor anchors (checked 2026-10-25): Pikkit Pro $29.99/mo,
$199.99/yr; Action PRO $24.99/mo, ~$99.99/yr; Rithmm $29.99/mo;
Dimers $25/mo; Juice Reel free. Headline monthly prices cluster
$25-40; effective annual prices cluster ~$8-17/mo. Nobody in the lane
sells premium analytics under $19.99/mo headline.

Run: python3 pricing_model.py
"""
from __future__ import annotations

APPLE_CUT = 0.15
REF_PRICE, REF_CONV = 6.99, 0.030
ANNUAL_DISCOUNT = 0.50          # annual price = monthly * 12 * (1 - 0.50)
ANNUAL_MIX = 0.60
ANNUAL_RENEWAL = 0.55
ELASTICITIES = {"loyal niche (-0.6)": -0.6, "unit (-1.0)": -1.0,
                "price-sensitive (-1.5)": -1.5}
PRICES = [2.99, 4.99, 6.99, 7.99, 9.99, 12.99, 14.99, 19.99]


def conv_at(price: float, elasticity: float) -> float:
    return REF_CONV * (price / REF_PRICE) ** elasticity


def ltv_net(price: float) -> float:
    """Expected 24-month net revenue per subscriber at a monthly price."""
    net_m = price * (1 - APPLE_CUT)
    churn = 0.07 + 0.0025 * price
    monthly_ltv = net_m * min(24, 1 / churn)
    annual_price = price * 12 * (1 - ANNUAL_DISCOUNT)
    annual_ltv = annual_price * (1 - APPLE_CUT) * (1 + ANNUAL_RENEWAL)
    return ANNUAL_MIX * annual_ltv + (1 - ANNUAL_MIX) * monthly_ltv


def revenue_per_1000(price: float, elasticity: float) -> float:
    return 1000 * conv_at(price, elasticity) * ltv_net(price)


if __name__ == "__main__":
    print("Expected 24-mo net revenue per 1,000 activated free users")
    print(f"{'price/mo':>9} {'annual':>8}", "  ".join(f"{k:>22}" for k in ELASTICITIES), "  worst-case")
    rows = {}
    for p in PRICES:
        revs = {k: revenue_per_1000(p, e) for k, e in ELASTICITIES.items()}
        rows[p] = revs
        print(f"${p:>7.2f} ${p * 12 * (1 - ANNUAL_DISCOUNT):>7.2f}",
              "  ".join(f"${v:>21,.0f}" for v in revs.values()),
              f"  ${min(revs.values()):,.0f}")
    best_each = {k: max(PRICES, key=lambda p: rows[p][k]) for k in ELASTICITIES}
    maximin = max(PRICES, key=lambda p: min(rows[p].values()))
    print(f"\nBest per scenario: " + ", ".join(f"{k} -> ${p}" for k, p in best_each.items()))
    print(f"Robust pick (maximizes the worst case): ${maximin}/mo, "
          f"${maximin * 12 * (1 - ANNUAL_DISCOUNT):.2f}/yr")
    base = rows[maximin]
    cheap = rows[4.99]
    print(f"At the robust pick vs $4.99: unit-elasticity revenue "
          f"${base['unit (-1.0)']:,.0f} vs ${cheap['unit (-1.0)']:,.0f} per 1,000 users; "
          f"worst case ${min(base.values()):,.0f} vs ${min(cheap.values()):,.0f}")
    subs_needed = {p: 111 / (p * (1 - APPLE_CUT) * 12) for p in (4.99, maximin)}
    print("Subscribers needed just to cover the $99/yr store cost for a year: "
          + ", ".join(f"${p}/mo -> {n:.1f}" for p, n in subs_needed.items())
          + " — break-even is not the constraint; revenue per user is.")
