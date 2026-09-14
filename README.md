# Gate Design and Stage-Dependent Incentives in Retail Proprietary-Trading Evaluations

Simulation code, figure-generation scripts, and the document build script for the paper.

**Author:** Nicholas Hall · ORCID [0009-0006-0586-0220](https://orcid.org/0009-0006-0586-0220)
**Preprint:** SSRN (link to follow) · arXiv (link to follow)
**License:** MIT for code; the paper itself is CC BY-NC-ND 4.0.

Every simulated number in the paper — Tables 5 through 26 and Figures 1 and 2 — is produced by a script in `code/`.
No market data is required for any of them: they are Monte Carlo simulations of a contract, not backtests.
The strategy backtests of Section 8 used licensed futures data that cannot be redistributed; the account-level
verdicts they produced are reported in the paper and reproduced in `verify.py` from the stated parameters.

## Layout

```
code/
  sim_phase.py                    core absorbing-barrier simulator (trailing drawdown, EOD monitoring)
  run_phase_diagram.py            Figure 1, Figure 2, Tables 5–8            (§4.3, §5)
  breakeven.py                    Table 13 — independent break-even solver  (§7.1)
  hedge_symmetric.py              Tables 22, 24 — symmetric hedged pair     (§12.2, §12.5)
  hedge_variants.py               Table 23 — asymmetric and basket variants (§12.4)
  apex_gaussian.py                Table 25 — Apex 50K, Gaussian daily model (§12.6)
  skill_gradient.py               Table 7 — P(pass | skill)                 (§5.4)
  robustness_and_extensions.py    Tables 9, 26; cross-firm and funded hedge;
                                  deflated-Sharpe indicator                 (§5.6, §10, §12.4, §12.6)
  verify.py                       reproduction checks from Appendix A
figures/
  fig1_phase_mu_sigma.png
  fig2_frontier_q_f.png
build_paper.js                    generates the paper .docx from source (Node, docx package)
```

## Running

Python 3.10+, `numpy`, `scipy`, `matplotlib`.

```bash
pip install numpy scipy matplotlib
cd code
python run_phase_diagram.py       # ~3 min; writes ../figures/*.png and prints Tables 5–8
python breakeven.py               # ~2 min
python hedge_symmetric.py         # ~1 min
python hedge_variants.py
python apex_gaussian.py
python skill_gradient.py          # ~5 min
python robustness_and_extensions.py
python verify.py                  # Appendix A checks
```

All scripts use fixed seeds. Exact reproduction is expected on the same numpy version; an independent
implementation should agree within Monte Carlo error (±0.8 pp at P = 0.5 for 4,000 paths).

To rebuild the paper: `npm install docx` then `node build_paper.js`. Requires the two PNGs in `figures/`.

## What is not here

- Futures price data (licensed; Databento GLBX.MDP3).
- The research ledger of 127 investigations and the orchestration layer described in §2. The paper reports
  their outputs; the transcripts are retained by the author.
- Firm rule parameters beyond what the paper states. Every parameter used carries a retrieval date in the paper
  and was taken from the firm's public site.

## Citation

Hall, N. (2026). Gate Design and Stage-Dependent Incentives in Retail Proprietary-Trading Evaluations:
Why Passing Is Not Standalone Evidence of Skill, and Why the Product Fails to Pay Under Measured Trading
Constraints. Working paper.
