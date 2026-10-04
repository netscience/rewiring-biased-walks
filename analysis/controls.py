"""Análisis de los experimentos de control (R1, lmax = D/2):
   base : horizonte adaptativo U[2, diam], umbral de R1 = c/2 (como en el artículo), instrumentado
   thr0 : umbral de R1 = 0
   h30  : horizonte fijo de 30 saltos

Calcula las métricas por ciclo de cada red (misma pipeline que run_metrics.py), lee las líneas
"e nodo long_media n_distintos ciclo" de los logs (longitud media de los trazadores de cada nodo
y nodos distintos que visitaron) y produce results/controls_metrics.csv, results/controls_tracers.csv
y la figura figures/controls.pdf.

Uso: NETS_DIR no se usa; la ruta de simruns se da con --simruns.
"""
import argparse
import os
from multiprocessing import Pool

import numpy as np
import pandas as pd

from config import CYCLES, LMAX_VALUES, N_NODES, RESULTS_DIR, parse_strategy
from loader import edges_to_graph, iter_cycle_edges, read_rewiring_log
from metrics import METRIC_COLUMNS, compute_metrics

VARIANTS = ["base", "thr0", "h30"]
STRATS = ["RWI", "RW", "RWD", "N2Vp1q2", "SP", "CR"]


def read_tracer_log(run_dir):
    logs = [f for f in os.listdir(run_dir) if f.startswith("salida_") and f.endswith(".txt")]
    rows = []
    with open(os.path.join(run_dir, logs[0])) as fh:
        for line in fh:
            if line.startswith("e "):
                t = line.split()
                rows.append((int(t[4]), float(t[2]), int(t[3])))
    if not rows:
        return pd.DataFrame(columns=["cycle", "tracer_len", "n_distinct"])
    df = pd.DataFrame(rows, columns=["cycle", "tracer_len", "n_distinct"])
    return df.groupby("cycle")[["tracer_len", "n_distinct"]].mean().reset_index()


def process(job):
    variant, strat, run, run_dir = job
    fam, p, q = parse_strategy(strat)
    rows, prev = [], None
    for cycle, edges, copied in iter_cycle_edges(run_dir, CYCLES):
        g = edges_to_graph(edges)
        m = prev if (copied and prev is not None) else compute_metrics(g, edges, LMAX_VALUES["D2"], seed=run * 1000 + cycle)
        prev = m
        rows.append(dict(variant=variant, strategy=strat, family=fam, q=q, run=run, cycle=cycle, **m))
    counts = read_rewiring_log(run_dir)
    for r in rows:
        r["frac_rewired"] = counts.get(r["cycle"], 0) / N_NODES
    tr = read_tracer_log(run_dir)
    tr["variant"] = variant; tr["strategy"] = strat; tr["run"] = run
    return rows, tr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--simruns", default="/home/claude/simruns")
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    jobs = []
    for v in VARIANTS:
        for s in STRATS:
            base = os.path.join(args.simruns, v, "R1", s, "D2")
            if not os.path.isdir(base):
                continue
            for r in sorted(os.listdir(base)):
                d = os.path.join(base, r)
                if r.isdigit() and os.path.exists(os.path.join(d, f"datos-salida_{r}.txt")):
                    jobs.append((v, s, int(r), d))
    print(len(jobs), "corridas de control", flush=True)
    allrows, alltr = [], []
    with Pool(args.workers) as pool:
        for rows, tr in pool.imap_unordered(process, jobs):
            allrows += rows; alltr.append(tr)
    pd.DataFrame(allrows).to_csv(os.path.join(RESULTS_DIR, "controls_metrics.csv"), index=False)
    pd.concat(alltr).to_csv(os.path.join(RESULTS_DIR, "controls_tracers.csv"), index=False)
    print("listo")


if __name__ == "__main__":
    main()
