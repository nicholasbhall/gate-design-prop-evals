import numpy as np
from hedge import _absorb, hedged_pair, unhedged, TARGET, TRAIL

FEE = 98.0

print("=" * 76)
print("1. WHY THE PAIR CANNOT BOTH PASS  (structural)")
print("=" * 76)
print("Mirrored accounts: eq_A = -eq_B - 2*cost. For both to reach +3000 the sum")
print("of equities would need to be +6000; it is instead pinned at -2*cost*days.")
print("P(both pass) measured = 0.000 in every cell. The pair is strictly disjoint.")
print("Therefore P(>=1 passes) = P(A) + P(B) = 2p, purchased for 2 fees.")
print()

print("=" * 76)
print("2. ASYMMETRIC SIZING — does an unequal pair break the neutrality?")
print("=" * 76)
def asym_pair(sig, cost, ratio, days=90, n=150000, seed=5):
    r = np.random.default_rng(seed)
    g = r.normal(0.0, sig, size=(n, days))
    a = np.cumsum(g - cost, axis=1)
    b = np.cumsum(-g * ratio - cost * ratio, axis=1)
    pa, _ = _absorb(a)
    pb, _ = _absorb(b)
    return (pa | pb).mean(), (pa & pb).mean()

print(f"{'ratio B:A':>10}{'P(>=1)':>10}{'P(both)':>10}{'E[funded]':>12}{'$/funded':>11}")
for ratio in (0.25, 0.5, 1.0, 2.0, 4.0):
    p_any, p_both = asym_pair(1000, 20, ratio)
    exp_f = p_any + p_both
    print(f"{ratio:>10.2f}{p_any:>10.3f}{p_both:>10.3f}{exp_f:>12.3f}"
          f"{2*FEE/exp_f:>11.0f}")
print()

print("=" * 76)
print("3. N-ACCOUNT BASKET — one long against N-1 shorts")
print("=" * 76)
def basket(sig, cost, n_short, days=90, n=120000, seed=9):
    r = np.random.default_rng(seed)
    g = r.normal(0.0, sig, size=(n, days))
    passes = np.zeros(n, dtype=bool)
    total = 0.0
    pl, _ = _absorb(np.cumsum(g - cost, axis=1))
    passes |= pl
    total += pl.mean()
    for k in range(n_short):
        ps, _ = _absorb(np.cumsum(-g / n_short - cost, axis=1))
        passes |= ps
        total += ps.mean()
    return passes.mean(), total

print(f"{'accounts':>10}{'P(>=1)':>10}{'E[funded]':>12}{'$/funded':>11}")
for ns in (1, 2, 3, 5):
    p_any, exp_f = basket(1000, 20, ns)
    tot_fee = FEE * (ns + 1)
    print(f"{ns+1:>10}{p_any:>10.3f}{exp_f:>12.3f}{tot_fee/exp_f:>11.0f}")
print()

print("=" * 76)
print("4. THE PAYOUT CEILING IS WHAT NEUTRALISES IT")
print("=" * 76)
print("EV per pair = E[funded] x payout_rate x payout_size - 2 x fee")
print("sigma=1000, cost=20/day: E[funded per pair] = 0.590")
exp_f = 0.590
print()
print(f"{'payout ceiling':>16}{'no consist.':>14}{'40% cap':>11}{'20% cap':>11}")
for ceiling in (1000, 2000, 3000, 5000, 10000):
    row = f"{'$'+str(ceiling):>16}"
    for pr in (0.348, 0.348, 0.174):
        ev = exp_f * pr * ceiling - 2 * FEE
        row += f"{'$'+format(ev, '+.0f'):>13} "
    print(row)
print()
print("Funded-stage payout rates from Table 3 at the 40% win-rate row.")
print("At the observed $1,000 ceiling the pair is marginal-to-negative.")
print("The ceiling, not the hedge prohibition, is the binding constraint.")
