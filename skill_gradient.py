"""
Skill gradient. Does the evaluation carry skill information?
For each per-trade edge mu (net of costs), find the sizing-optimised pass
probability. If the curve is flat over the range participants plausibly occupy,
the evaluation filters nothing; if steep, it filters.

Also computes the gradient at FIXED sizing (a participant who does not optimise),
which is the more realistic population case.
"""
import numpy as np
from sim_phase import p_pass

# per-trade skill q = mu/sigma, in units the paper uses
QS = np.array([-0.04, -0.02, 0.0, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12, 0.20])
SIG_GRID = [30, 40, 60, 90, 130, 200, 300, 450, 650, 900, 1250, 1700]
FIXED_SIG = 90   # a "reasonable" sizing a non-optimising participant might use

print("=" * 78)
print("SKILL GRADIENT — sizing-OPTIMISED participant  (max over sigma)")
print("=" * 78)
print(f"{'q':>8}" + "".join(f"{'f='+str(f):>10}" for f in (1,5,20)))
opt = {}
for q in QS:
    row = f"{q:>8.3f}"
    for f in (1,5,20):
        best = 0.0
        for sg in SIG_GRID:
            p,_ = p_pass(q*sg, sg, f, n_paths=4000, seed=int(5000+q*1000+sg+f))
            best = max(best, p)
        opt[(q,f)] = best
        row += f"{best:>10.3f}"
    print(row)

print()
print("=" * 78)
print(f"SKILL GRADIENT — FIXED sizing (sigma={FIXED_SIG})")
print("=" * 78)
print(f"{'q':>8}" + "".join(f"{'f='+str(f):>10}" for f in (1,5,20)))
fix = {}
for q in QS:
    row = f"{q:>8.3f}"
    for f in (1,5,20):
        p,_ = p_pass(q*FIXED_SIG, FIXED_SIG, f, n_paths=6000, seed=int(7000+q*1000+f))
        fix[(q,f)] = p
        row += f"{p:>10.3f}"
    print(row)

print()
print("=" * 78)
print("GRADIENT SUMMARY — change in P(pass) per +0.01 of q, over 0 <= q <= 0.05")
print("=" * 78)
for f in (1,5,20):
    d_opt = (opt[(0.05,f)] - opt[(0.0,f)]) / 5
    d_fix = (fix[(0.05,f)] - fix[(0.0,f)]) / 5
    print(f"  f={f:<3} optimised: {d_opt:+.3f}/0.01q   fixed-sizing: {d_fix:+.3f}/0.01q")
print()
print("Interpretation: at q=0 the optimised curve is already ~0.4; the fixed-sizing")
print("curve is the population-relevant one. The evaluation IS a filter (monotone),")
print("but a weak one: the gap between zero skill and modest skill is small relative")
print("to the gap between optimised and unoptimised sizing at the SAME skill.")
