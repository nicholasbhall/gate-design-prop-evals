import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm
from sim_phase import p_pass, p_pass_fixed_barrier

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.linewidth": 0.6,
    "figure.dpi": 200,
})

# ----------------------------------------------------------------------
# FIGURE 1 — P(pass) over (mu, sigma) at f = 1, 5, 20
# ----------------------------------------------------------------------
MUS = np.linspace(0, 30, 25)
SIGS = np.linspace(30, 200, 20)
FREQS = [1, 5, 20]

fig, axes = plt.subplots(1, 3, figsize=(9.4, 3.2), sharey=True)
for ax, f in zip(axes, FREQS):
    Z = np.zeros((len(SIGS), len(MUS)))
    for i, sg in enumerate(SIGS):
        for j, mu in enumerate(MUS):
            Z[i, j], _ = p_pass(mu, sg, f, n_paths=4000, seed=101 + i * 97 + j)
    im = ax.contourf(MUS, SIGS, Z, levels=np.linspace(0, 1, 21),
                     cmap="Greys", vmin=0, vmax=1)
    cs = ax.contour(MUS, SIGS, Z, levels=[0.25, 0.5, 0.75],
                    colors="k", linewidths=0.8)
    ax.clabel(cs, fmt="%.2f", fontsize=7)
    # cost floor: net mu <= 0 is unreachable once costs are applied
    ax.axvspan(0, 0.0, color="none")
    ax.axvline(0, color="k", lw=1.2)
    ax.set_title(f"f = {f} trades/day", fontsize=9)
    ax.set_xlabel(r"net edge per trade  $\mu$  (\$)")
    ax.set_xlim(0, 30)
axes[0].set_ylabel(r"per-trade volatility  $\sigma$  (\$)")

# mark the best measured gross edge, granted as if costless
for ax in axes:
    ax.plot([1.74], [60], marker="o", ms=4, mfc="white", mec="k", mew=0.9, zorder=5)
axes[0].annotate("best measured\ngross edge (costless)", xy=(1.74, 60),
                 xytext=(6.5, 40), fontsize=6.5,
                 arrowprops=dict(arrowstyle="-", lw=0.6))

cb = fig.colorbar(im, ax=axes, fraction=0.022, pad=0.015,
                  ticks=[0, 0.25, 0.5, 0.75, 1.0])
cb.set_label("P(pass within 90 days)", fontsize=8)
cb.ax.tick_params(labelsize=7)
fig.savefig("fig1_phase_mu_sigma.png", bbox_inches="tight")
plt.close(fig)
print("fig1 written")

# ----------------------------------------------------------------------
# FIGURE 2 — sizing-optimised P(pass) vs per-trade skill q = mu/sigma
# ----------------------------------------------------------------------
QS = np.linspace(0.0, 0.20, 21)
SIG_GRID = [30, 40, 60, 90, 130, 200, 300, 450, 650, 900, 1250, 1700]

fig, ax = plt.subplots(figsize=(5.2, 3.5))
styles = {1: ("-", "k"), 5: ("--", "0.35"), 20: (":", "0.0")}
frontier = {}
for f in FREQS:
    ys = []
    for q in QS:
        best = 0.0
        for sg in SIG_GRID:
            p, _ = p_pass(q * sg, sg, f, n_paths=4000, seed=int(2000 + q * 1000 + sg))
            best = max(best, p)
        ys.append(best)
    frontier[f] = ys
    ls, c = styles[f]
    ax.plot(QS, ys, ls, color=c, lw=1.3, label=f"f = {f}")

ax.axhline(0.40, color="0.5", lw=0.8, ls="-.")
ax.annotate("continuous-monitoring benchmark  $d/(d+T)=0.40$",
            xy=(0.105, 0.405), fontsize=6.5, color="0.35")
ax.set_xlabel(r"per-trade skill  $q=\mu/\sigma$")
ax.set_ylabel("sizing-optimised P(pass)")
ax.set_xlim(0, 0.20)
ax.set_ylim(0, 1.0)
ax.legend(frameon=False, fontsize=8, loc="lower right")
ax.annotate("zero skill", xy=(0, frontier[20][0]), xytext=(0.018, 0.16),
            fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.6))
fig.savefig("fig2_frontier_q_f.png", bbox_inches="tight")
plt.close(fig)
print("fig2 written")

print()
print("zero-skill left edge (fine sizing grid):")
for f in FREQS:
    print(f"  f={f:<3} {frontier[f][0]:.3f}")
