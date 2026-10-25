from dataclasses import dataclass

@dataclass
class Vertical:
    name: str
    data_cost_mo: int
    legal_risk: int
    appstore_risk: int
    build_weeks: int
    market_size: int
    moat: int

    @property
    def ship_score(self) -> float:
        raw = (self.market_size + self.moat
               - self.legal_risk * 0.8
               - self.appstore_risk * 0.6
               - self.data_cost_mo / 100
               - self.build_weeks * 0.3)
        return round(raw, 1)

VERTICALS = [
    Vertical("Bet tracking + edge",      40,  3, 3, 4,  7, 7),
    Vertical("Stocks journal",           30,  4, 2, 3,  9, 4),
    Vertical("Crypto portfolio",         20,  3, 2, 3,  8, 4),
    Vertical("Bonds / yield",            15,  2, 2, 2,  4, 3),
    Vertical("Real estate areas",       400,  3, 3, 8,  7, 5),
    Vertical("All-in-one dashboard",    600, 10, 8, 20, 9, 8),
]

ranked = sorted(VERTICALS, key=lambda v: -v.ship_score)
print(f"{'vertical':28} {'ship':>6} {'cost/mo':>9} {'weeks':>6} {'legal':>6}")
print("-" * 62)
for v in ranked:
    print(f"{v.name:28} {v.ship_score:>6} ${v.data_cost_mo:>8} {v.build_weeks:>6} {v.legal_risk:>6}")

winner = ranked[0]
print(f"\nSTART WITH: {winner.name}")
print(f"Target launch: {winner.build_weeks} weeks solo")
print(f"Total run-rate at launch: ~${winner.data_cost_mo}/mo in data")
