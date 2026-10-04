"""Calcula las métricas estructurales de todas las redes (todas las corridas y
ciclos 0..30) y la actividad de recableado por ciclo.

Salidas (en results/):
  metrics_per_cycle.csv   una fila por (regla, estrategia, lmax, ejecución, ciclo)
  rewiring_activity.csv   eventos de recableado por ciclo, desde los logs salida_*.txt
  degrees/<...>.npz       secuencias de grado en los ciclos DEGREE_CYCLES

Reanudable: las corridas ya presentes en metrics_per_cycle.csv se omiten.
Uso: python run_metrics.py [--workers N] [--limit K]
"""
import argparse
import csv
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

from config import (CYCLES, LMAX_VALUES, N_NODES, RESULTS_DIR, iter_runs,
                    parse_strategy)
from loader import edges_to_graph, iter_cycle_edges, read_rewiring_log
from metrics import METRIC_COLUMNS, compute_metrics

DEGREE_CYCLES = [0, 1, 2, 5, 10, 15, 20, 25, 30]
KEY_COLUMNS = ["rule", "strategy", "family", "p", "q", "lmax", "run", "cycle", "copied"]
METRICS_CSV = os.path.join(RESULTS_DIR, "metrics_per_cycle.csv")
ACTIVITY_CSV = os.path.join(RESULTS_DIR, "rewiring_activity.csv")
DEG_DIR = os.path.join(RESULTS_DIR, "degrees")


def process_run(job):
    rule, strat, lmax, run, run_dir = job
    fam, p, q = parse_strategy(strat)
    rows, degs = [], {}
    prev = None
    for cycle, edges, copied in iter_cycle_edges(run_dir, CYCLES):
        g = edges_to_graph(edges)
        if copied and prev is not None:
            m = prev  # red idéntica a la del ciclo anterior (sin recableados)
        else:
            m = compute_metrics(g, edges, LMAX_VALUES[lmax], seed=run * 1000 + cycle)
        prev = m
        row = dict(rule=rule, strategy=strat, family=fam, p=p, q=q, lmax=lmax,
                   run=run, cycle=cycle, copied=int(copied))
        row.update(m)
        rows.append(row)
        if cycle in DEGREE_CYCLES:
            degs[cycle] = np.array(g.degree(), dtype=np.uint16)
    counts = read_rewiring_log(run_dir)
    activity = [dict(rule=rule, strategy=strat, family=fam, p=p, q=q, lmax=lmax, run=run,
                     cycle=c, n_rewired=counts.get(c, 0), frac_rewired=counts.get(c, 0) / N_NODES)
                for c in CYCLES]
    tag = f"{rule}_{strat}_{lmax}_{run}"
    np.savez_compressed(os.path.join(DEG_DIR, tag + ".npz"),
                        cycles=np.array(sorted(degs)), degrees=np.stack([degs[c] for c in sorted(degs)]))
    return tag, rows, activity


def done_runs():
    if not os.path.exists(METRICS_CSV):
        return set()
    done = set()
    with open(METRICS_CSV) as fh:
        for r in csv.DictReader(fh):
            done.add(f"{r['rule']}_{r['strategy']}_{r['lmax']}_{r['run']}")
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    os.makedirs(DEG_DIR, exist_ok=True)

    done = done_runs()
    jobs = [j for j in iter_runs() if f"{j[0]}_{j[1]}_{j[2]}_{j[3]}" not in done]
    if args.limit:
        jobs = jobs[: args.limit]
    print(f"{len(done)} corridas ya calculadas, {len(jobs)} pendientes", flush=True)

    new_m = not os.path.exists(METRICS_CSV)
    new_a = not os.path.exists(ACTIVITY_CSV)
    t0 = time.time()
    with open(METRICS_CSV, "a", newline="") as fm, open(ACTIVITY_CSV, "a", newline="") as fa, \
            Pool(args.workers) as pool:
        wm = csv.DictWriter(fm, fieldnames=KEY_COLUMNS + METRIC_COLUMNS)
        wa = csv.DictWriter(fa, fieldnames=["rule", "strategy", "family", "p", "q", "lmax", "run",
                                            "cycle", "n_rewired", "frac_rewired"])
        if new_m:
            wm.writeheader()
        if new_a:
            wa.writeheader()
        for i, (tag, rows, activity) in enumerate(pool.imap_unordered(process_run, jobs), 1):
            wm.writerows(rows)
            wa.writerows(activity)
            fm.flush(); fa.flush()
            if i % 10 == 0 or i == len(jobs):
                el = time.time() - t0
                print(f"[{i}/{len(jobs)}] {tag}  {el/60:.1f} min, ~{el/i*(len(jobs)-i)/60:.1f} min restantes",
                      flush=True)


if __name__ == "__main__":
    main()
