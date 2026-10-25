"""Two-tier pricing check + price-test sample size. Stdlib only.

Question 1: does Free / Plus $4.99 / Pro $14.99 beat every single price?
Assumptions (labeled, varied in sensitivity):
- Activated users split casual / semi-serious. Casuals convert at $4.99
  (3.5%) and effectively never above it. Semi-serious convert 9% at
  $4.99, 7.5% at $9.99, 6% at $14.99 — they pay more when asked, which
  is the entire two-tier argument.
- Cannibalization: fraction of would-be Pro buyers who settle for Plus.
  This is the parameter that can kill the two-tier case, so it is swept.
- LTV per subscriber imported from pricing_model.py (mix, churn, Apple).

Question 2: the $9.99-vs-$14.99 test at 4% vs 3% conversion — how many
users per arm does it actually take? (Normal-approx two-proportion test,
alpha .05 two-sided, power .80.)

Run: python3 pricing_tiers.py
"""
from __future__ import annotations
import math, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pricing_model import ltv_net  # noqa: E402

CASUAL_CONV = {4.99: 0.035, 9.99: 0.004, 14.99: 0.001}
SEMI_CONV = {4.99: 0.09, 9.99: 0.075, 14.99: 0.06}


def single(price: float, semi_share: float) -> float:
    conv = (1 - semi_share) * CASUAL_CONV[price] + semi_share * SEMI_CONV[price]
    return 1000 * conv * ltv_net(price)


def two_tier(semi_share: float, cannibal: float) -> float:
    casual_rev = 1000 * (1 - semi_share) * CASUAL_CONV[4.99] * ltv_net(4.99)
    pro_buyers = 1000 * semi_share * SEMI_CONV[14.99]
    semi_rev = (pro_buyers * (1 - cannibal) * ltv_net(14.99)
                + pro_buyers * cannibal * ltv_net(4.99))
    return casual_rev + semi_rev


def n_per_arm(p1: float, p2: float, alpha: float = 0.05, power: float = 0.80) -> float:
    z_a, z_b = 1.959964, 0.841621          # two-sided .05, power .80
    return ((z_a + z_b) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))) / (p1 - p2) ** 2


def power_at_n(p1: float, p2: float, n: float, alpha: float = 0.05) -> float:
    se = math.sqrt((p1 * (1 - p1) + p2 * (1 - p2)) / n)
    z = abs(p1 - p2) / se - 1.959964
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


if __name__ == "__main__":
    print("24-mo net revenue per 1,000 activated users")
    for semi in (0.15, 0.30, 0.50):
        print(f"\n semi-serious share {semi:.0%}:")
        for p in (4.99, 9.99, 14.99):
            print(f"   single ${p:>5}: ${single(p, semi):,.0f}")
        for c in (0.0, 0.25, 0.50):
            print(f"   two-tier (cannibalization {c:.0%}): ${two_tier(semi, c):,.0f}")
    n = n_per_arm(0.04, 0.03)
    print(f"\nPrice test $9.99 vs $14.99 at 4% vs 3% conversion:")
    print(f"  n per arm for 80% power: {n:,.0f}")
    print(f"  power at 1,500/arm: {power_at_n(0.04, 0.03, 1500):.0%} "
          f"— a coin-flip-grade test; ~{n:,.0f}/arm is the honest number, "
          f"or accept a longer run / larger minimum effect.")
