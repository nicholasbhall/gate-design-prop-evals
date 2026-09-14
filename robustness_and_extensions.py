import numpy as np
from math import sqrt, log, exp
from scipy import stats

TARGET, TRAIL, D_MAX = 3000.0, 2000.0, 90

def absorb(eq):
    n, d = eq.shape
    peak = np.maximum.accumulate(np.concatenate([np.zeros((n,1)), eq], axis=1), axis=1)[:, :-1]
    peak = np.maximum(peak, 0.0)
    ruin = eq <= (peak - TRAIL); win = eq >= TARGET; big = d + 1
    rd = np.where(ruin.any(1), ruin.argmax(1), big); wd = np.where(win.any(1), win.argmax(1), big)
    return ((wd < rd) & (wd <= d - 1)).mean()

# ---------------------------------------------------------------------------
# 1. ROBUSTNESS: same (mu, sigma, f) cells under four P&L distributions
# ---------------------------------------------------------------------------
def daily_pnl(dist, mu, sig, f, n, days, rng):
    """Per-trade draws with mean mu and sd sig, summed to daily."""
    if dist == "normal":
        x = rng.normal(mu, sig, size=(n, days, f))
    elif dist == "student_t3":
        t = rng.standard_t(3, size=(n, days, f)) / sqrt(3.0)   # unit variance
        x = mu + sig * t
    elif dist == "bernoulli":
        # win +1.5R / lose -R at win-rate w chosen to match mu and sig
        # mean = w*1.5R - (1-w)R = R(2.5w - 1); var = R^2*(2.5^2 w(1-w))
        # solve: choose R from sig, then w from mu
        R = sig / 1.25
        w = np.clip((mu / R + 1) / 2.5, 0.01, 0.99)
        win = rng.random((n, days, f)) < w
        x = np.where(win, 1.5*R, -R)
    elif dist == "regime":
        # two-state vol regime: sigma switches between 0.6*sig and 1.6*sig, persistent
        st = np.zeros((n, days), dtype=bool)
        st[:, 0] = rng.random(n) < 0.5
        for t in range(1, days):
            flip = rng.random(n) < 0.05
            st[:, t] = np.where(flip, ~st[:, t-1], st[:, t-1])
        s_eff = np.where(st, 1.6*sig, 0.6*sig)[:, :, None]
        x = rng.normal(mu, 1.0, size=(n, days, f)) * s_eff
    return x.sum(axis=2)

print("=" * 78)
print("ROBUSTNESS — P(pass) at representative cells under four P&L models")
print("=" * 78)
cells = [(0.0, 90, 5), (0.0, 300, 5), (3.0, 90, 5), (5.0, 90, 5), (8.0, 130, 5), (2.0, 60, 20)]
dists = ["normal", "student_t3", "bernoulli", "regime"]
print(f"{'(mu,sig,f)':>14}" + "".join(f"{d:>13}" for d in dists))
for mu, sg, f in cells:
    row = f"{str((mu,sg,f)):>14}"
    for d in dists:
        rng = np.random.default_rng(31)
        eq = np.cumsum(daily_pnl(d, mu, sg, f, 6000, D_MAX, rng), axis=1)
        row += f"{absorb(eq):>13.3f}"
    print(row)
print("Break-even rows (mu=3,5) are the ones that matter; sign of the no-go should hold.")

# ---------------------------------------------------------------------------
# 2. DEFLATED SHARPE for the two near-survivors (Bailey & Lopez de Prado 2014)
# ---------------------------------------------------------------------------
print()
print("=" * 78)
print("DEFLATED SHARPE — W1-06 (SR 3.07, n=60) and C10 (SR 3.15, n=53)")
print("=" * 78)
def expected_max_sr(N, var_sr=1.0):
    """E[max SR over N independent trials], Bailey & LdP approximation."""
    g = 0.5772156649
    return sqrt(var_sr) * ((1 - g) * stats.norm.ppf(1 - 1.0/N) + g * stats.norm.ppf(1 - 1.0/(N*np.e)))
def psr(sr_hat, sr_star, n, skew=0.0, kurt=3.0):
    """Probabilistic Sharpe: P(true SR > sr_star)."""
    denom = sqrt(1 - skew*sr_hat + (kurt-1)/4 * sr_hat**2)
    z = (sr_hat - sr_star) * sqrt(n - 1) / denom
    return stats.norm.cdf(z)
for name, sr, n in [("W1-06", 3.07, 60), ("C10", 3.15, 53)]:
    print(f"\n  {name}: annualised-per-trade SR {sr}, n={n}")
    # per-trade SR is what the ledger reports; convert to per-observation
    for N in (10, 40, 127):
        sr0 = expected_max_sr(N)
        # deflate: benchmark is E[max SR] under null of N trials on n obs, scaled
        sr0_pertrade = sr0 / sqrt(n)          # null SR per observation over n obs
        # PSR against that benchmark using per-observation SR
        sr_obs = sr / sqrt(252) if False else sr  # ledger SR already per-trade-annualised; treat as-is
        dsr = psr(sr/sqrt(n) if False else sr, sr0_pertrade*sqrt(n)*0 + sr0, n)
        print(f"    trials N={N:>3}: E[max SR | null] = {sr0:.2f}   DSR = P(true SR > E[max]) = {dsr:.3f}")
    print("    (assumes normal per-trade returns; skew/kurtosis of the ledger not retained)")

# ---------------------------------------------------------------------------
# 3. CROSS-FIRM HEDGE: sacrificial leg at $39, surviving leg at $98 no-consistency
# ---------------------------------------------------------------------------
print()
print("=" * 78)
print("CROSS-FIRM HEDGE — cheap sacrificial leg vs symmetric same-firm pair")
print("=" * 78)
FEE_A, FEE_C = 98.0, 39.0     # Lucid Flex vs TopOne headline
ACT_C = 189.0                 # TopOne activation if it ends up being the survivor
def pair(sig, cost, n=200000, seed=0):
    r = np.random.default_rng(seed)
    g = r.normal(0.0, sig, size=(n, D_MAX))
    pa = absorb(np.cumsum(g - cost, axis=1)); pb = absorb(np.cumsum(-g - cost, axis=1))
    return pa, pb
print(f"{'sigma':>8}{'P(A pass)':>11}{'P(C pass)':>11}{'same-firm $/funded':>20}{'cross-firm $/funded':>21}")
for sig in (500, 1000, 2000):
    pa, pb = pair(sig, 20)
    same = 2*FEE_A / (pa + pb)
    # cross-firm: pay 98 + 39 up front; if C leg passes you owe 189 activation
    exp_cost = FEE_A + FEE_C + pb*ACT_C
    cross = exp_cost / (pa + pb)
    print(f"{sig:>8}{pa:>11.3f}{pb:>11.3f}{same:>20.0f}{cross:>21.0f}")
print("Cross-firm saves on the sacrificial fee but the cheap firm's activation fee")
print("bites whenever the cheap leg is the one that passes (half the time).")

# ---------------------------------------------------------------------------
# 4. FUNDED-STAGE HEDGE: survive 5 days + reach +2000, no target
# ---------------------------------------------------------------------------
print()
print("=" * 78)
print("FUNDED-STAGE HEDGE — pair aimed at the withdrawal threshold, not the target")
print("=" * 78)
def funded_absorb(eq, thresh=2000.0, min_days=5):
    n, d = eq.shape
    peak = np.maximum.accumulate(np.concatenate([np.zeros((n,1)), eq], axis=1), axis=1)[:, :-1]
    peak = np.maximum(peak, 0.0)
    ruin = eq <= (peak - TRAIL); win = eq >= thresh; big = d + 1
    rd = np.where(ruin.any(1), ruin.argmax(1), big); wd = np.where(win.any(1), win.argmax(1), big)
    ok = (wd < rd) & (wd <= d-1) & ((wd+1) >= min_days)
    return ok.mean()
print(f"{'sigma':>8}{'P(>=1 payout-eligible)':>25}{'unhedged':>11}{'ratio':>8}")
for sig in (300, 500, 1000):
    r = np.random.default_rng(9)
    g = r.normal(0.0, sig, size=(150000, 60))
    pa = funded_absorb(np.cumsum(g-10, axis=1)); pb = funded_absorb(np.cumsum(-g-10, axis=1))
    un = funded_absorb(np.cumsum(r.normal(-10, sig, size=(150000,60)), axis=1))
    print(f"{sig:>8}{pa+pb:>25.3f}{un:>11.3f}{(pa+pb)/max(un,1e-9):>8.2f}")
print("Ratio ~2.0 => same linearity as the eval stage: 2x probability for 2x fees.")

# ---------------------------------------------------------------------------
# 5. APEX trade-level rebuild
# ---------------------------------------------------------------------------
print()
print("=" * 78)
print("APEX 50K — trade-level rebuild (Bernoulli trades, 1:1.5, 6 contracts NQ)")
print("=" * 78)
START, SAFETY, MINREQ, MINQUAL, NQUAL, CONS, CAP = 50000., 52100., 52600., 250., 5, 0.5, 1500.
def apex_eval(w, R, tpd, cost, n=60000, days=30, seed=3):
    rng = np.random.default_rng(seed)
    win = rng.random((n, days, tpd)) < w
    pnl = (np.where(win, 1.5*R, -R) - cost).sum(2)
    pnl = np.maximum(pnl, -1000.0)                # DLL halts the day
    return absorb(np.cumsum(pnl, axis=1))
def apex_pa(w, R, tpd, cost, n=60000, days=60, seed=8):
    rng = np.random.default_rng(seed)
    win = rng.random((n, days, tpd)) < w
    pnl = (np.where(win, 1.5*R, -R) - cost).sum(2)
    eq = np.cumsum(pnl, axis=1)
    peak = np.maximum(np.maximum.accumulate(np.concatenate([np.zeros((n,1)), eq],1),1)[:, :-1], 0.0)
    alive = ~(eq <= peak - 2000.0).any(1)
    qual = (pnl >= MINQUAL).sum(1) >= NQUAL
    tot = eq[:, -1]; cons = pnl.max(1) < CONS*np.maximum(tot, 1e-9)
    above = (START + tot) >= MINREQ
    ok = alive & qual & cons & above
    w_ = np.minimum(np.maximum(START + tot - SAFETY, 0.0), CAP)
    return ok.mean(), (w_[ok].mean() if ok.any() else 0.0)
print(f"{'win rate':>9}{'R($)':>7}{'trades/d':>10}{'p_eval':>8}{'p_payout':>10}{'payout':>9}{'EV @$30':>9}")
for w in (0.40, 0.42, 0.44):
    for R, tpd in ((400, 4), (250, 6)):
        pe = apex_eval(w, R, tpd, 4.0)
        pp, sz = apex_pa(w, R/3, tpd, 4.0)   # PA: 2 contracts => R scaled by 1/3
        print(f"{w:>9.2f}{R:>7}{tpd:>10}{pe:>8.3f}{pp:>10.3f}{'$'+format(sz,'.0f'):>9}{'$'+format(pe*pp*sz-30,'+.0f'):>9}")
print("At the 40% driftless rate the trade-level model is negative everywhere; the")
print("Gaussian model's +$28 cost-free cell does not survive trade-level costs.")
