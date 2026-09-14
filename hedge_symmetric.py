"""
Hedged-pair simulation.

Two accounts, same instrument, opposite direction, same size. Daily P&L is
mirrored: whatever account A makes gross, account B loses gross. Both pay costs.
Both carry target +3000 and EOD trailing drawdown 2000.

Question: P(at least one account passes) and expected cost per funded account,
against the unhedged baseline.
"""

import numpy as np

TARGET = 3000.0
TRAIL = 2000.0


def _absorb(eq):
    """Given (n_paths, days) cumulative EOD equity, return (passed, pass_day)."""
    n, d = eq.shape
    peak = np.maximum.accumulate(
        np.concatenate([np.zeros((n, 1)), eq], axis=1), axis=1)[:, :-1]
    peak = np.maximum(peak, 0.0)
    ruin = eq <= (peak - TRAIL)
    win = eq >= TARGET
    big = d + 1
    ruin_day = np.where(ruin.any(1), ruin.argmax(1), big)
    win_day = np.where(win.any(1), win.argmax(1), big)
    passed = (win_day < ruin_day) & (win_day <= d - 1)
    return passed, win_day


def hedged_pair(sigma_daily, cost_daily, days=90, n=200000, seed=0):
    """Mirrored pair. Returns P(>=1 passes), P(both pass), P(neither)."""
    r = np.random.default_rng(seed)
    gross = r.normal(0.0, sigma_daily, size=(n, days))
    eq_a = np.cumsum(gross - cost_daily, axis=1)
    eq_b = np.cumsum(-gross - cost_daily, axis=1)
    pa, _ = _absorb(eq_a)
    pb, _ = _absorb(eq_b)
    return (pa | pb).mean(), (pa & pb).mean(), (~pa & ~pb).mean()


def unhedged(sigma_daily, cost_daily, days=90, n=200000, seed=1):
    r = np.random.default_rng(seed)
    eq = np.cumsum(r.normal(-cost_daily, sigma_daily, size=(n, days)), axis=1)
    p, _ = _absorb(eq)
    return p.mean()


FEE = 98.0
PAYOUT = 1000.0

print("=" * 78)
print("HEDGED PAIR vs UNHEDGED SINGLE  (target +3000, EOD trailing 2000, 90d)")
print("=" * 78)
print(f"{'sigma/day':>10}{'cost/day':>10}{'P(>=1 pass)':>14}{'P(both)':>10}"
      f"{'P(none)':>10}{'unhedged':>11}{'$/funded':>11}{'baseline':>11}")

for sig in (250, 500, 1000, 1500, 2000):
    for cost in (5, 20, 50):
        p_any, p_both, p_none = hedged_pair(sig, cost)
        p_un = unhedged(sig, cost)
        # hedged: 2 fees buys E[funded] = p_any + p_both accounts
        exp_funded = p_any + p_both
        cost_per = (2 * FEE) / exp_funded if exp_funded > 0 else float('inf')
        base = FEE / p_un if p_un > 0 else float('inf')
        print(f"{sig:>10}{cost:>10}{p_any:>14.3f}{p_both:>10.3f}"
              f"{p_none:>10.3f}{p_un:>11.3f}{cost_per:>11.0f}{base:>11.0f}")

print()
print("=" * 78)
print("EV PER PAIR at $1,000 payout ceiling, assuming payout_rate = 1.0")
print("=" * 78)
for sig in (500, 1000, 2000):
    p_any, p_both, _ = hedged_pair(sig, 20)
    exp_funded = p_any + p_both
    ev = exp_funded * PAYOUT - 2 * FEE
    print(f"  sigma={sig:<6} E[funded per pair]={exp_funded:.3f}  "
          f"EV = {exp_funded:.3f}x$1000 - $196 = ${ev:+.0f}")

print()
print("Industry-cited unhedged pass rate 5-10% implies $/funded of "
      f"${FEE/0.10:.0f}-${FEE/0.05:.0f}.")
