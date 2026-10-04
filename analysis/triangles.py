"""Triángulos por ciclo y aparición del efecto de q (mecanismo de la Sección 4.2).

Para cada red registrada de las caminatas (RWI, RW, RWD, RWL con p=1 y q en {0.25,0.5,1,2}) cuenta
los triángulos de la red completa, los que contienen al menos un enlace dinámico y los incidentes al
1 % de nodos de mayor grado. Produce results/triangles.csv (una fila por red) y, con
metrics_per_cycle.csv, la figura figures/triangles.pdf: triángulos por ciclo y tamaño del efecto de q
(diferencia entre q=2 y q=0.25 de la serie promediada, en desviaciones estándar entre corridas) por ciclo.

Uso: python triangles.py [--lmax D2] [--workers 2]
"""
import argparse
import os
from multiprocessing import Pool

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import plotstyle as ps
from config import CYCLES, MAX_CYCLE, N_NODES, RESULTS_DIR, FIG_DIR, iter_runs, parse_strategy
from loader import FIXED_EDGE_SET, edges_to_graph, iter_cycle_edges

ps.apply()
STRATS = ["RWI", "RW", "RWD", "N2Vp1q0_25", "N2Vp1q0_5", "N2Vp1q1", "N2Vp1q2"]
RULES = ["R1", "R2", "R3"]


def triangle_stats(g, edges):
    tri = g.list_triangles() if hasattr(g, "list_triangles") else []
    n_tri = len(tri)
    if n_tri == 0:
        return dict(n_triangles=0, tri_with_dynamic=0, tri_top1=0, nodes_in_tri=0)
    deg = np.array(g.degree())
    top = set(np.argsort(-deg)[: max(1, N_NODES // 100)].tolist())
    dyn = 0
    top1 = 0
    nodes = set()
    for a, b, c in tri:
        nodes.update((a, b, c))
        if frozenset((a, b)) not in FIXED_EDGE_SET or frozenset((b, c)) not in FIXED_EDGE_SET or frozenset((a, c)) not in FIXED_EDGE_SET:
            dyn += 1
        if a in top or b in top or c in top:
            top1 += 1
    return dict(n_triangles=n_tri, tri_with_dynamic=dyn, tri_top1=top1, nodes_in_tri=len(nodes))


def process(job):
    rule, strat, lmax, run, run_dir = job
    fam, p, q = parse_strategy(strat)
    rows, prev = [], None
    for cycle, edges, copied in iter_cycle_edges(run_dir, CYCLES):
        if copied and prev is not None:
            st = prev
        else:
            g = edges_to_graph(edges)
            st = triangle_stats(g, edges)
        prev = st
        rows.append(dict(rule=rule, strategy=strat, family=fam, p=p, q=q, lmax=lmax, run=run, cycle=cycle, **st))
    return rows


def q_effect(mpc, rule, lmax, metric):
    """|media(q=2) - media(q=0.25)| / sd agrupada entre corridas, por ciclo."""
    a = mpc[(mpc.rule == rule) & (mpc.lmax == lmax) & (mpc.strategy == "N2Vp1q2")].groupby("cycle")[metric]
    b = mpc[(mpc.rule == rule) & (mpc.lmax == lmax) & (mpc.strategy == "N2Vp1q0_25")].groupby("cycle")[metric]
    ma, sa, mb, sb = a.mean(), a.std(), b.mean(), b.std()
    sd = np.sqrt((sa ** 2 + sb ** 2) / 2)
    return ((ma - mb) / sd.replace(0, np.nan)).fillna(0)


def figure(tri, mpc, lmax, name="triangles"):
    fig, axes = plt.subplots(2, 3, figsize=(5.15, 3.6), sharex=True, sharey="row", constrained_layout=True)
    for j, rule in enumerate(RULES):
        ax = axes[0, j]
        for s in ps.STRATEGIES:
            if s not in STRATS:
                continue
            d = tri[(tri.rule == rule) & (tri.lmax == lmax) & (tri.strategy == s)].groupby("cycle").n_triangles.agg(["mean", "std"])
            st = ps.STYLE[s]
            ax.plot(d.index, d["mean"] / 1000, color=st["color"], ls=st["ls"], marker=st["marker"], markevery=5, lw=1.1, label=ps.STRAT_SHORT[s])
            ax.fill_between(d.index, (d["mean"] - d["std"]) / 1000, (d["mean"] + d["std"]) / 1000, color=st["color"], alpha=0.12, lw=0)
        ax.set_ylim(0, 11.5)
        ax.set_title(f"Rule {rule[1]}", pad=14)
        if j == 0:
            ax.text(0.0, 1.03, "(a) Triangles ($\\times10^3$)", transform=ax.transAxes, fontsize=7.2, va="bottom")
        ax = axes[1, j]
        for k, (met, lab) in enumerate([("k_max", "$k_{\\max}$"), ("clustering", "$\\langle C\\rangle$"), ("H_norm", "$H/H_{\\max}$"), ("dyn_len_mean", "$\\langle\\ell\\rangle$")]):
            e = q_effect(mpc, rule, lmax, met)
            ax.plot(e.index, e.values, color=ps.CAT[k], ls=ps.LINESTYLES[k], lw=1.1, label=lab)
        ax.axhline(0, color="#8a8984", lw=0.6)
        ax.axhspan(-1, 1, color="#e1e0d9", alpha=0.5, lw=0)
        ax.set_xlabel("Rewiring cycle")
        ax.set_xlim(0, MAX_CYCLE)
        if j == 0:
            ax.text(0.0, 1.03, "(b) Effect of $q$ (s.d. units)", transform=ax.transAxes, fontsize=7.2, va="bottom")
            ax.legend(fontsize=6, loc="lower left", ncol=2, columnspacing=0.8, handlelength=1.6)
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=5, bbox_to_anchor=(0.5, 1.0))
    fig.savefig(os.path.join(FIG_DIR, name + ".pdf"))
    fig.savefig(os.path.join(FIG_DIR, name + ".png"))
    print("figura:", name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lmax", nargs="+", default=["D2"])
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--figure-only", action="store_true")
    args = ap.parse_args()
    out = os.path.join(RESULTS_DIR, "triangles.csv")
    if not args.figure_only:
        jobs = [j for j in iter_runs() if j[1] in STRATS and j[2] in args.lmax]
        print(len(jobs), "corridas", flush=True)
        rows = []
        with Pool(args.workers) as pool:
            for i, r in enumerate(pool.imap_unordered(process, jobs), 1):
                rows += r
                if i % 10 == 0:
                    print(f"[{i}/{len(jobs)}]", flush=True)
        pd.DataFrame(rows).to_csv(out, index=False)
    tri = pd.read_csv(out)
    mpc = pd.read_csv(os.path.join(RESULTS_DIR, "metrics_per_cycle.csv"))
    figure(tri, mpc, args.lmax[0])
    # resumen
    pd.set_option("display.width", 220)
    s = tri[tri.cycle.isin([1, 2, 3, 5, 10, 20, 30])].groupby(["rule", "strategy", "cycle"]).n_triangles.mean().unstack("cycle").round(0)
    print(s.to_string())
    for met in ["k_max", "clustering", "H_norm", "dyn_len_mean"]:
        for rule in RULES:
            e = q_effect(mpc, rule, args.lmax[0], met)
            first = e.index[(e.abs() >= 2)].min() if (e.abs() >= 2).any() else None
            print(met, rule, "primer ciclo con |efecto| >= 2 sd:", first, " efecto final:", round(float(e.iloc[-1]), 2))


if __name__ == "__main__":
    main()
