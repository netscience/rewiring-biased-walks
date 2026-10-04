# Analysis pipeline (`analysis/`)

Scripts, in execution order. Set `NETS_DIR` to the folder that contains `R1/`, `R2/`, `R3/` (default `../nets`).

| script | role |
|---|---|
| `config.py` | constants (grid, ℓmax values, cycles), strategy-name parsing, node coordinates |
| `loader.py` | reads adjacency lists and rewiring logs; reuses the previous network for cycles without rewiring events |
| `metrics.py` | per-network metrics (python-igraph) |
| `run_metrics.py` | computes all metrics in parallel (resumable) → `results/metrics_per_cycle.csv`, `results/rewiring_activity.csv`, `results/degrees/*.npz` |
| `validate.py` | compares clustering, diameter and ASPL with the simulator's `datos-salida_*.txt` (max. discrepancy 5e-7 over 77 947 networks) |
| `aggregate.py` | run means ± s.d. per configuration and cycle (`metrics_mean.csv`), final state (`final_state.csv`), convergence cycles (`convergence.csv`), p/q effects (`n2v_pq_effects.csv`), q/p symmetry (`n2v_ratio_symmetry.csv`) |
| `stats.py` | 95 % bootstrap CIs of the final state (`final_state_ci.csv`) and Kruskal–Wallis / Mann–Whitney tests with Holm correction (`final_state_tests.csv`) |
| `figures.py` | time series, p×q heat maps, final-state comparisons, convergence heat maps, q/p plots, activity–hub coupling, degree distributions and their evolution, border effect (`hub_border.csv`) |
| `concept_figures.py` | the three conceptual figures of Section 2 (cycle, rules, exploration strategies) |
| `triangles.py` | triangles per cycle and effect of q per cycle (`triangles.csv`, Fig. 7) |
| `controls.py`, `controls_figure.py` | metrics, tracer-route lengths and figure of the control and verification runs (`controls_*.csv`, `informed_check.csv`, Fig. 10) |
| `robustness.py` | connectivity robustness under targeted attacks and random failures (`robustness.csv`, Supplementary S5) |
| `draw_networks.py` | drawings of representative networks on the grid (degree and Louvain communities) |
| `plotstyle.py` | shared plotting style (fixed colour-blind-safe categorical palette, single-hue sequential ramp) |
| `pack_nets.sh` | packs the networks per rule/strategy into tar.xz archives (how `nets_packed/` was produced) |

## Metrics (per network and cycle)

Degree: `k_max`, `k_std`, `k_gini`, `H_norm` (Shannon entropy of the degree distribution normalised by log2(n−1)).
Structure: `assortativity`, `clustering` (average local), `transitivity`, `diameter`, `aspl`, `efficiency` (global), `n_components`.
Communities (Louvain, seeded): `n_communities`, `modularity`, `edge_cut_ratio`.
Dynamic links: `dyn_len_mean`, `dyn_len_max`, `dyn_len_frac_lmax` (= mean length / ℓmax), `dyn_frac_top1pct`
(fraction of dynamic links incident to the top-1 % nodes by degree).
Dynamics (from the logs): `n_rewired`, `frac_rewired` (nodes that rewired in the cycle).

## Convergence criterion (`results/convergence.csv`)

For the run-averaged series of each metric, the convergence cycle is the first cycle after which the series stays
within a band of half-width max(tol · range, SE_final) around its final value (cycle 30), with tol ∈ {0.05, 0.10},
range = max − min over cycles 0..30 and SE_final = sd_final/√10. A value near 30 means the metric is still drifting.

## Output files

* `results/metrics_per_cycle.csv` — one row per network (78 120 rows).
* `results/metrics_mean.csv` — mean ± s.d. per configuration and cycle.
* `results/final_state.csv` — cycle-30 state per configuration.
* `results/convergence.csv`, `results/n2v_pq_effects.csv`, `results/n2v_ratio_symmetry.csv`.
* `results/final_state_ci.csv`, `results/final_state_tests.csv` — confidence intervals and tests (`stats.py`).
* `results/hub_border.csv` — distance to the border of the top-1 % nodes (border effect, Section 4.1).
* `results/triangles.csv` — triangle counts per network (`triangles.py`).
* `results/controls_metrics.csv`, `controls_tracers.csv`, `controls_summary.csv` — control and verification runs; `informed_check.csv` compares the new SP/CR/RW runs with the symposium runs.
* `results/robustness.csv`, `robustness_curves.npz` — robustness analysis.
* `results/degrees/` — degree sequences at cycles 0, 1, 2, 5, 10, 15, 20, 25, 30 (npz, shipped as `degrees.tar.gz`).
* `figures/` — PDF and PNG.
