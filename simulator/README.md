# Simulator

Discrete-event simulator of the distributed geometric rewiring model, taken from
<https://github.com/netscience/rewiring> (branch `controls-extended-version`) with the backward-compatible
additions listed in `CAMBIOS.md` (configurable R1 threshold, fixed exploration horizon, tracer-route
instrumentation; without the new parameters it behaves exactly as the published version). Python ≥ 3.9,
dependencies in `requirements.txt` (`networkx`, `numpy`, `matplotlib`).

Key implementation facts relied upon in the article (Section 2 of the paper):

* tracer walks are self-avoiding: nodes already in the packet route are excluded from the next hop;
* the maximum number of hops of a tracer is drawn uniformly from {2, …, diam(G_t)}, with diam(G_t)
  the diameter of the network at the start of the cycle (unless `HORIZONTE` is set);
* rule R1 requires the candidate to have been visited by at least `UMBRAL_R1 · EXPLORADORES` tracers
  (default 0.5, i.e. c/2); the threshold applies to rewiring only, not to the first assignment of free links;
* the visit table f_n excludes the current neighbours (static and dynamic) of the node.

## How the published networks were produced (`nets_packed/`)

The upstream pipeline runs one simulation per configuration from the parameter lists in `configuracion.py`
(`formacion.py` writes a `config.py` into each run folder and calls `main.py` and `extractData.py`).
The parameters used for the article were:

```
RED = ["malla"]            ROWS = COLUMNS = 50
REGLAS = [1, 2, 3]
ROUTING = ["SHORTEST-PATH", "COMPASS-ROUTING", "RANDOM-WALK", "RW-DEGREE", "RW-INVERSE", "RW-NODE2VEC"]
PQ_NODE2VEC = [(p, q) for p in (0.25, 0.5, 1, 2) for q in (0.25, 0.5, 1, 2)]
LONG_ENLACES = [2, 4, 8, 16]      # ℓmax = D/2, D/4, D/8, D/16  (D/32 was also run but is not used)
CICLOS = 30                       # 50 for the SP, CR and RW runs shared with the symposium paper
EJECUCIONES = 10
EXPLORADORES = 20                 # tracers per node, c
ENLACES_DINAMICOS = 2
DIV_CONEXIONES = 1
```

Each run folder contains `salida_<run>.txt` (the event log) and the per-cycle adjacency lists
`graph_test_<cycle>.adjlist` written by `extractData.py`; these are what `nets_packed/` archives.
Runs are stochastic (no fixed seed); the run index 1–10 identifies the repetition.

## A single run by hand

Write a `config.py` in a working folder (see the dictionary in `run_controls.py` for the full list of
keys, e.g. `ROUTING = "RW-NODE2VEC"`, `P = 1`, `Q = 2`, `REGLA = 1`, `LONG_ENLACE = 2`, `CICLOS = 30`,
`EXPLORADORES = 20`, `ENLACES_DINAMICOS = 2`), copy the simulator modules next to it and run

```bash
python main.py log.txt > salida_1.txt
python extractData.py salida_1.txt test        # writes graph_test_<cycle>.adjlist
```

## Control and verification runs (`simruns/`)

* `run_controls.py` — the control experiments of Section 4.5 of the paper: R1, ℓmax = D/2, strategies RW, RWD,
  RWI and RWL(q = 2), five runs of 30 cycles each, in three variants: `base` (reference configuration),
  `thr0` (`UMBRAL_R1 = 0`) and `h30` (`HORIZONTE = 30`). The instrumented simulator adds lines
  `e node mean_route_length distinct_nodes cycle` to the log, which `analysis/controls.py` reads.
* `run_informed.py` — five runs each of SP and CR in the reference configuration, used in Section 3.1 to check
  that the SP/CR/RW runs inherited from the symposium paper are reproduced by the current simulator
  (`analysis/results/informed_check.csv`).

Both scripts skip finished runs and can be interrupted and relaunched (`python run_controls.py --workers 8`).
Results go to `simruns/<variant>/R1/<strategy>/D2/<run>/`; `analysis/controls.py --simruns ../simulator/simruns`
computes the metrics (`make controls` from the repository root).
