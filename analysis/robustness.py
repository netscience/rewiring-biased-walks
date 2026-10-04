"""Robustez de las redes finales ante ataques dirigidos y fallas aleatorias
(material suplementario). Métricas como en Lopez-Chavira et al. (2024):

  N_LCC(f) = n_LCC / (n - p)      orden relativo de la componente gigante tras quitar p = f·n nodos
  R        = (1/n) Σ_p N_LCC(p)   robustez de conectividad
  f*       : primer f con N_LCC(f) <= 0.5 (punto crítico)
  f_0.9, f_0.1 : límites del área crítica 0.9 >= N_LCC >= 0.1

Ataques: se elimina en cada paso el nodo de mayor grado de la red remanente.
Fallas: eliminación en orden uniforme aleatorio (N_FAIL realizaciones por red).

Uso: python robustness.py [--lmax D2 D4 ...] [--rules R1 R2 R3] [--strategies ...] [--workers 2]
Salida: results/robustness.csv (una fila por red y escenario) y results/robustness_curves.npz
"""
import argparse
import os
from multiprocessing import Pool

import numpy as np

from config import CYCLES, MAX_CYCLE, N_NODES, RESULTS_DIR, iter_runs, parse_strategy
from loader import edges_to_graph, iter_cycle_edges

N_FAIL = 10
F_GRID = np.linspace(0, 1, 101)  # fracciones en las que se muestrea N_LCC


def lcc_curve(g, order):
    """N_LCC tras eliminar sucesivamente los nodos en `order` (atacante no adaptativo)."""
    n = g.vcount()
    curve = np.empty(n)
    h = g.copy()
    alive = np.ones(n, bool)
    # eliminar por lotes de 1% para acelerar: recalcular componentes cada paso es O(m)
    for p in range(n):
        v = order[p]
        alive[v] = False
        if p % 25 == 0 or p == n - 1:
            sub = h.induced_subgraph(np.where(alive)[0])
            lcc = max(sub.connected_components().sizes()) if sub.vcount() else 0
            curve[p] = lcc / max(n - p - 1, 1)
        else:
            curve[p] = np.nan
    # interpolar los pasos no calculados
    idx = np.where(~np.isnan(curve))[0]
    curve = np.interp(np.arange(n), idx, curve[idx])
    return curve


def attack_curve(g):
    """Ataque adaptativo: en cada paso se elimina el nodo de mayor grado remanente."""
    n = g.vcount()
    h = g.copy()
    h.vs["orig"] = list(range(n))
    curve = np.empty(n)
    for p in range(n):
        deg = np.array(h.degree())
        v = int(deg.argmax())
        h.delete_vertices(v)
        if p % 25 == 0 or p == n - 1:
            lcc = max(h.connected_components().sizes()) if h.vcount() else 0
            curve[p] = lcc / max(h.vcount(), 1)
        else:
            curve[p] = np.nan
    idx = np.where(~np.isnan(curve))[0]
    return np.interp(np.arange(n), idx, curve[idx])


def summarize(curve):
    n = len(curve)
    f = np.arange(n) / n
    R = float(curve.mean())
    def first(th):
        i = np.where(curve <= th)[0]
        return float(f[i[0]]) if len(i) else 1.0
    return dict(R=R, f_star=first(0.5), f_09=first(0.9), f_01=first(0.1))


def process(job):
    rule, strat, lmax, run, run_dir = job
    edges = None
    for c, e, _ in iter_cycle_edges(run_dir, CYCLES):
        edges = e
    g = edges_to_graph(edges)
    fam, p, q = parse_strategy(strat)
    rows, curves = [], {}
    base = dict(rule=rule, strategy=strat, family=fam, p=p, q=q, lmax=lmax, run=run)
    ca = attack_curve(g)
    rows.append(dict(base, scenario="attack", realization=0, **summarize(ca)))
    curves["attack"] = np.interp(F_GRID, np.arange(N_NODES) / N_NODES, ca)
    rng = np.random.default_rng(1000 * run + 7)
    cf_all = []
    for r in range(N_FAIL):
        order = rng.permutation(N_NODES)
        cf = lcc_curve(g, order)
        rows.append(dict(base, scenario="failure", realization=r, **summarize(cf)))
        cf_all.append(np.interp(F_GRID, np.arange(N_NODES) / N_NODES, cf))
    curves["failure"] = np.mean(cf_all, axis=0)
    return f"{rule}_{strat}_{lmax}_{run}", rows, curves


def main():
    import pandas as pd
    ap = argparse.ArgumentParser()
    ap.add_argument("--lmax", nargs="+", default=["D2", "D4", "D8", "D16"])
    ap.add_argument("--rules", nargs="+", default=["R1", "R2", "R3"])
    ap.add_argument("--strategies", nargs="+", default=None)
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    jobs = [j for j in iter_runs() if j[0] in args.rules and (args.strategies is None or j[1] in args.strategies) and j[2] in args.lmax]
    print(len(jobs), "redes", flush=True)
    rows, curves = [], {}
    with Pool(args.workers) as pool:
        for i, (tag, r, c) in enumerate(pool.imap_unordered(process, jobs), 1):
            rows += r; curves[tag] = c
            if i % 10 == 0:
                print(f"[{i}/{len(jobs)}]", flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(RESULTS_DIR, "robustness.csv"), index=False)
    np.savez_compressed(os.path.join(RESULTS_DIR, "robustness_curves.npz"), f=F_GRID,
                        **{f"{k}__{s}": v for k, d in curves.items() for s, v in d.items()})
    print("listo")


if __name__ == "__main__":
    main()
