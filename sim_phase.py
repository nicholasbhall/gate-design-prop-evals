"""
Fix 1: (mu, sigma, frequency) simulation study.
Core reconstructed from the archived sim_phase.py. The analytic function has been
cleaned up (the archived copy carried dead scratch lines and a redundant theta
assignment); the surviving final expression is preserved exactly.
"""

import numpy as np

TARGET = 3000.0
TRAIL = 2000.0
D_MAX = 90
N_PATHS = 4000


def p_pass(mu, sigma, f, d_max=D_MAX, n_paths=N_PATHS, seed=None):
    """P(hit +TARGET before trailing-DD ruin, within d_max days), EOD checks.
    Also returns mean days-to-pass among passers."""
    r = np.random.default_rng(seed)
    mu_d = f * mu
    sd_d = np.sqrt(f) * sigma
    pnl = r.normal(mu_d, sd_d, size=(n_paths, d_max))
    eq = np.cumsum(pnl, axis=1)
    # running peak of EOD equity BEFORE today, including start (0)
    peak = np.maximum.accumulate(
        np.concatenate([np.zeros((n_paths, 1)), eq], axis=1), axis=1)[:, :-1]
    peak = np.maximum(peak, 0.0)
    ruin = eq <= (peak - TRAIL)
    win = eq >= TARGET
    big = d_max + 1
    ruin_day = np.where(ruin.any(1), ruin.argmax(1), big)
    win_day = np.where(win.any(1), win.argmax(1), big)
    passed = (win_day < ruin_day) & (win_day <= d_max - 1)
    p = passed.mean()
    days = win_day[passed].mean() + 1 if passed.any() else np.nan
    return p, days


def p_pass_fixed_barrier(mu, sigma, f):
    """Analytic: Brownian with drift, FIXED barriers +T / -d, continuous monitoring.
    Scale function s(x) = exp(-theta x), theta = 2m/s^2.
    P(hit +b before -a | start 0) = (e^{th a} - 1) / (e^{th a} - e^{-th b})"""
    m = f * mu
    s2 = f * sigma ** 2
    if abs(m) < 1e-12:
        return TRAIL / (TRAIL + TARGET)
    th = 2 * m / s2
    a, b = TRAIL, TARGET
    return (np.exp(th * a) - 1) / (np.exp(th * a) - np.exp(-th * b))
