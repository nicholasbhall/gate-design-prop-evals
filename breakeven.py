"""
Break-even win rate solver. Two-stage, EOD trailing, R:R 1:1.5.
Finds the win rate w at which EV per evaluation crosses zero, per firm.

Per trade: win -> +1.5R, lose -> -1.0R. Driftless baseline at 1:1.5 is w=0.40.
Stage 1 (eval):   pass = reach +3000 before trailing DD 2000.
Stage 2 (funded): survive, clear min days, satisfy consistency, reach withdraw.
"""
import numpy as np

TARGET = 3000.0
TRAIL = 2000.0
WITHDRAW = 2000.0       # funded-stage withdraw threshold (HAL-123 convention)
PAYOUT = 1000.0         # 50% split of the 2000 drawdown
MIN_DAYS = 5
R = 250.0               # risk per trade in dollars
COST = 5.0              # round-turn friction per trade

FIRMS = {
    "Firm A (Lucid Flex 50K)":      dict(fee=98.0,  dll=None,   consist=None),
    "Firm B (Tradeify 50K)":        dict(fee=87.0,  dll=1250.0, consist=0.20),
    "Firm C (TopOne Elite Access)": dict(fee=228.0, dll=None,   consist=0.40),
}


def day_pnl(rng, w, n, days, trades_per_day):
    """Daily P&L from trades_per_day draws at win rate w, R:R 1:1.5, costs on."""
    tot = np.zeros((n, days))
    for _ in range(trades_per_day):
        win = rng.random((n, days)) < w
        tot += np.where(win, 1.5 * R, -R) - COST
    return tot


def stage(rng, w, n, days, tpd, goal, dll, consist, need_days):
    pnl = day_pnl(rng, w, n, days, tpd)
    if dll is not None:
        pnl = np.maximum(pnl, -dll)
    eq = np.cumsum(pnl, axis=1)
    peak = np.maximum.accumulate(
        np.concatenate([np.zeros((n, 1)), eq], axis=1), axis=1)[:, :-1]
    peak = np.maximum(peak, 0.0)
    ruin = eq <= (peak - TRAIL)
    win_b = eq >= goal
    big = days + 1
    rd = np.where(ruin.any(1), ruin.argmax(1), big)
    wd = np.where(win_b.any(1), win_b.argmax(1), big)
    ok = (wd < rd) & (wd <= days - 1)
    if need_days:
        ok &= (wd + 1) >= MIN_DAYS
    if consist is not None:
        # best single day must not exceed consist x total profit at the pass day
        idx = np.clip(wd, 0, days - 1)
        rows = np.arange(n)
        cum = eq[rows, idx]
        best = np.array([pnl[i, :idx[i] + 1].max() if ok[i] else 0.0
                         for i in range(n)])
        ok &= best <= consist * np.maximum(cum, 1e-9)
    return ok.mean()


def ev(w, fee, dll, consist, n=40000, seed=11):
    rng = np.random.default_rng(seed)
    p_pass = stage(rng, w, n, 60, 5, TARGET, dll, None, False)       # eval: fast
    p_pay = stage(rng, w, n, 60, 1, WITHDRAW, dll, consist, True)     # funded: slow
    return p_pass * p_pay * PAYOUT - fee, p_pass, p_pay


print("=" * 78)
print("BREAK-EVEN WIN RATE AT 1:1.5  (driftless baseline = 0.400)")
print("=" * 78)
for name, f in FIRMS.items():
    lo, hi = 0.34, 0.60
    for _ in range(16):
        mid = (lo + hi) / 2
        e, _, _ = ev(mid, f["fee"], f["dll"], f["consist"])
        if e < 0:
            lo = mid
        else:
            hi = mid
    be = (lo + hi) / 2
    e, pp, pb = ev(be, f["fee"], f["dll"], f["consist"])
    print(f"{name:<30} break-even {be*100:5.2f}%   "
          f"(+{(be-0.40)*100:4.2f}pp over driftless)   "
          f"pass {pp:.3f}  payout {pb:.3f}")

print()
print("=" * 78)
print("EV TABLE  (for the paper)")
print("=" * 78)
print(f"{'win rate':>10}" + "".join(f"{k.split('(')[0].strip():>22}" for k in FIRMS))
for w in (0.38, 0.40, 0.42, 0.44, 0.46, 0.48):
    row = f"{w*100:>9.1f}%"
    for name, f in FIRMS.items():
        e, _, _ = ev(w, f["fee"], f["dll"], f["consist"])
        row += f"{'$'+format(e,'+.0f'):>22}"
    print(row)
