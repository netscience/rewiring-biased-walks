# Biased random-walk exploration in distributed geometric rewiring — data and code

Companion repository of

> Aguirre-Guerrero D, Marcelín-Jiménez R, Lopez-Chavira MA, Robles-Martínez I.
> *Biased random-walk exploration shapes the emergent organization of spatial networks under distributed rewiring.*
> Applied Network Science (submitted). Extended version of a paper presented at the International Symposium on Complex Systems 2026.

It contains everything needed to reproduce the figures and tables of the article from the simulated networks,
and the simulator needed to regenerate the networks themselves.

## Layout

```
simulator/        discrete-event simulator (instrumented version, see simulator/README.md and CAMBIOS.md)
simulator/simruns/  the 70 control and verification runs of Sections 3.1 and 4.5 (1 860 + 310 networks)
analysis/         analysis pipeline: metrics, statistics, convergence, triangles, controls, robustness, figures
analysis/results/ metric tables produced by the pipeline (CSV; see analysis/README.md)
analysis/figures/ figures of the article and of the supplementary material (PDF + PNG)
nets_packed/      the 78 120 simulated networks of the main design (63 tar.xz archives, 1.2 GB)
Makefile          one-command reproduction (see below)
requirements.txt  Python dependencies
CITATION.cff      how to cite
```

## Data

The large files (`nets_packed/`, `simulator/simruns/`, `analysis/results/degrees.tar.gz` and
`analysis/results/metrics_per_cycle.csv`, about 1.8 GB in all) are excluded from the git repository by `.gitignore`
and distributed through the Zenodo archive <https://doi.org/10.5281/zenodo.23146563>; everything else is in git.

`nets_packed/<rule>_<strategy>.tar.xz` unpacks to `nets/<rule>/<strategy>/<lmax>/<run>/` with, for each run,
`graph_test_<cycle>.adjlist` (NetworkX adjacency list of the network after cycle *cycle*, static + dynamic links)
and `salida_<run>.txt` (simulator log: `c node -1 target 1` initial dynamic links, `r node old new cycle` rewiring events).
A `graph_test_<cycle>.adjlist` file is absent when no node rewired in that cycle; the network is then identical
to the previous one and the loader reuses it. Node *i* (1..2500) sits at row ⌊(i−1)/50⌋, column (i−1) mod 50 of the grid.

Configurations: rules R1, R2, R3 × strategies CR, SP, RW, RWD, RWI, N2Vp{0.25,0.5,1,2}q{0.25,0.5,1,2} ×
ℓmax ∈ {D2, D4, D8, D16} (= D/2 … D/16) × 10 runs × cycles 0–30.

## Reproducing the analysis

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make unpack      # extracts nets_packed/*.tar.xz into nets/   (6.9 GB on disk)
make metrics     # computes all metrics (≈ 3.5 h on 2 cores; resumable)
make validate    # checks clustering / diameter / ASPL against the simulator's own values
make aggregate   # means, final state, convergence, p/q effects
make stats       # bootstrap confidence intervals and nonparametric tests (Table 1, Sections 3.1, 4.1, 4.2)
make figures     # all figures of the article and supplement (incl. the conceptual figures)
make networks    # drawings of representative networks (Fig. 4, Supplementary S4)
make triangles   # triangle counts per cycle and the onset of the q effect (Fig. 7)
make controls    # metrics of the control and verification runs in simulator/simruns (Fig. 10, Section 3.1)
make robustness  # connectivity robustness of the final networks (Supplementary S5; ≈ 2 h)
```
`make all` runs the main chain (unpack → metrics → validate → aggregate → stats → figures → networks → triangles).
`make figures` and `make stats` alone work from the CSV files shipped in `analysis/results/`, so the
figures and tables can be regenerated without unpacking the networks. The border-effect table
(`analysis/results/hub_border.csv`) and the degree-distribution figures are produced by `make figures`
from `analysis/results/degrees.tar.gz` (unpack it into `analysis/results/degrees/` first).

## Regenerating the networks

`simulator/` contains the simulator used to produce `nets_packed/` and `simulator/simruns/`. The published
networks were produced with the upstream pipeline (`formacion.py` over the parameter lists in `configuracion.py`);
the exact parameter values, the way to run a single configuration by hand, and the scripts of the control
(`run_controls.py`) and verification (`run_informed.py`) runs are documented in `simulator/README.md`.
Runs are stochastic (no fixed seed); the run index 1–10 identifies the repetition.

## Licence

Code: MIT. Data and figures: CC BY 4.0.
