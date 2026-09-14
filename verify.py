import numpy as np
from sim_phase import p_pass, p_pass_fixed_barrier, TARGET, TRAIL, D_MAX

print("=" * 70)
print("ANCHOR CHECK  (paper Table 3 / analytic anchor)")
print("=" * 70)
print(f"{'cell (mu,sg,f)':<20}{'analytic':>10}{'sim trailing':>14}{'penalty':>10}{'paper':>16}")
paper_vals = {(5, 100, 10): (0.871, 0.731, -14.0),
              (10, 150, 5): (0.841, 0.691, -15.0),
              (2, 80, 20):  (0.746, 0.580, -16.6)}
for (mu, sg, f), (pa_p, ps_p, pen_p) in paper_vals.items():
    pa = p_pass_fixed_barrier(mu, sg, f)
    ps, _ = p_pass(mu, sg, f, d_max=2000, n_paths=8000, seed=1)
    pen = (ps - pa) * 100
    ok = "OK" if abs(pa - pa_p) < 0.005 else "MISMATCH"
    print(f"({mu},{sg},{f})".ljust(20)
          + f"{pa:>10.3f}{ps:>14.3f}{pen:>9.1f}pp"
          + f"   {pa_p}/{ps_p}/{pen_p}  {ok}")

print()
print("Driftless limit d/(d+T) =", TRAIL / (TRAIL + TARGET))
print("Monotonicity: sim trailing must be <= analytic fixed-barrier in every cell.")

print()
print("=" * 70)
print("TABLE 4 CHECK  — net mu required for P(pass) ~ 0.5, sigma in [90,130]")
print("=" * 70)
for f in (1, 5, 20):
    for sg in (90, 110, 130):
        lo, hi = 0.0, 200.0
        for _ in range(22):
            mid = (lo + hi) / 2
            p, _ = p_pass(mid, sg, f, n_paths=4000, seed=7)
            if p < 0.5:
                lo = mid
            else:
                hi = mid
        print(f"  f={f:<3} sigma={sg:<5} mu* = ${(lo+hi)/2:6.2f}")
    print()

print("=" * 70)
print("TABLE 5 CHECK  — days per cleared account")
print("=" * 70)
rows = [(0.50, 40, 10), (1.00, 60, 5), (1.74, 60, 5), (2.00, 60, 5),
        (3.00, 90, 5), (5.00, 90, 5), (8.00, 130, 5)]
print(f"{'mu':>7}{'sg':>6}{'f':>4}{'P(pass)':>10}{'days/clear':>13}{'years':>9}")
for mu, sg, f in rows:
    p, days = p_pass(mu, sg, f, n_paths=8000, seed=3)
    if p > 0:
        # expected calendar days per clear, including failed attempts
        exp_days = (days if not np.isnan(days) else D_MAX) if False else None
    # attempt length: passers take `days`, failures consume the horizon
    pw, dw = p, days
    att = (dw if not np.isnan(dw) else 90) * pw + 90 * (1 - pw)
    per_clear = att / pw if pw > 0 else float('inf')
    print(f"{mu:>7.2f}{sg:>6}{f:>4}{pw:>10.3f}{per_clear:>13.0f}{per_clear/252:>9.2f}")

print()
print("=" * 70)
print("ZERO-SKILL FRONTIER  (paper 5.3: q=0 optimum should be 0.33-0.49)")
print("=" * 70)
for f in (1, 5, 20):
    best = 0.0
    for sg in (40, 60, 90, 130, 200, 300, 500, 800, 1200):
        p, _ = p_pass(0.0, sg, f, n_paths=4000, seed=11)
        best = max(best, p)
    print(f"  f={f:<3} sizing-optimised P(pass) at zero skill = {best:.3f}")
