"""
Apex 50K under real 4.0 rules (sourced 2026-08-31).

EVAL (EOD variant):  target +3000, EOD trailing DD 2000, DLL 1000, 6 contracts,
                     no consistency, no minimum days, 30-day access.
EVAL (Intraday):     target +3000, intraday trailing DD 2500 on UNREALISED,
                     no DLL, 6 contracts, no minimum days.

PA (funded):         starts 50,000. 2 contracts (not 6).
                     Safety net 52,100 - balance must stay above it after payout.
                     Min balance to request 52,600 (safety net + 500 min payout).
                     5 qualifying days, each >= $250 profit (EOD 50K).
                     50% consistency: no single day >= 50% of profit since last payout.
                     First payout cap 1,500.
"""
import numpy as np

START = 50000.0
TARGET = 3000.0
SAFETY_NET = 52100.0
MIN_REQUEST = 52600.0
MIN_QUAL_DAY = 250.0
N_QUAL_DAYS = 5
CONSISTENCY = 0.50
MIN_PAYOUT = 500.0
FIRST_CAP = 1500.0


def eval_pass(sig, dd, dll, days=30, n=200000, seed=3):
    """EOD trailing eval with a daily loss limit that halts (not kills) the day."""
    r = np.random.default_rng(seed)
    pnl = r.normal(0.0, sig, size=(n, days))
    if dll is not None:
        pnl = np.maximum(pnl, -dll)          # DLL halts the day, caps daily loss
    eq = np.cumsum(pnl, axis=1)
    peak = np.maximum.accumulate(
        np.concatenate([np.zeros((n, 1)), eq], axis=1), axis=1)[:, :-1]
    peak = np.maximum(peak, 0.0)
    ruin = eq <= (peak - dd)
    win = eq >= TARGET
    big = days + 1
    rd = np.where(ruin.any(1), ruin.argmax(1), big)
    wd = np.where(win.any(1), win.argmax(1), big)
    return ((wd < rd) & (wd <= days - 1)).mean()


def pa_payout(sig, dd=2000.0, days=60, n=200000, seed=8):
    """Funded stage. Returns P(reaches a first payout) and the mean payout size.
    Must satisfy ALL of: survive trailing DD, balance >= MIN_REQUEST,
    >= 5 days with profit >= 250, and max day < 50% of total profit."""
    r = np.random.default_rng(seed)
    pnl = r.normal(0.0, sig, size=(n, days))
    eq = np.cumsum(pnl, axis=1)
    peak = np.maximum.accumulate(
        np.concatenate([np.zeros((n, 1)), eq], axis=1), axis=1)[:, :-1]
    peak = np.maximum(peak, 0.0)
    alive = ~(eq <= (peak - dd)).any(1)

    qual = (pnl >= MIN_QUAL_DAY).sum(1) >= N_QUAL_DAYS
    total = eq[:, -1]
    maxday = pnl.max(1)
    consistent = maxday < CONSISTENCY * np.maximum(total, 1e-9)
    above = (START + total) >= MIN_REQUEST

    ok = alive & qual & consistent & above
    withdrawable = np.minimum(
        np.maximum(START + total - SAFETY_NET, 0.0), FIRST_CAP)
    payout = np.where(ok, withdrawable, 0.0)
    return ok.mean(), payout[ok].mean() if ok.any() else 0.0


print("=" * 78)
print("APEX 50K — EVAL STAGE")
print("=" * 78)
print(f"{'sigma/day':>11}{'EOD (dd2000,dll1000)':>24}{'Intraday (dd2500,no dll)':>27}")
for sig in (300, 600, 1000, 1500, 2500):
    p_eod = eval_pass(sig, 2000.0, 1000.0)
    p_intra = eval_pass(sig, 2500.0, None)
    print(f"{sig:>11}{p_eod:>24.3f}{p_intra:>27.3f}")

print()
print("=" * 78)
print("APEX 50K — FUNDED STAGE (the binding gate)")
print("=" * 78)
print("2 contracts, so sigma is roughly a third of eval sizing.")
print(f"{'sigma/day':>11}{'P(first payout)':>18}{'mean payout':>14}{'E[$ per PA]':>14}")
for sig in (100, 200, 300, 500, 800):
    pr, sz = pa_payout(sig)
    print(f"{sig:>11}{pr:>18.4f}{'$'+format(sz,'.0f'):>14}{'$'+format(pr*sz,'.0f'):>14}")

print()
print("=" * 78)
print("EV PER EVAL PURCHASED  (fee $30, eval sigma 1000, PA sigma 300)")
print("=" * 78)
p_eval = eval_pass(1000, 2000.0, 1000.0)
pr, sz = pa_payout(300)
print(f"  eval pass rate            {p_eval:.4f}")
print(f"  P(first payout | funded)  {pr:.4f}")
print(f"  mean first payout         ${sz:.0f}")
print(f"  joint                     {p_eval*pr:.4f}")
print(f"  EV = {p_eval:.4f} x {pr:.4f} x ${sz:.0f} - $30 = "
      f"${p_eval*pr*sz - 30:+.2f}")
print()
print("Break-even eval fee at this joint:", f"${p_eval*pr*sz:.2f}")
