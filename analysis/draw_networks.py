"""Dibuja redes representativas (ciclo 30, ejecución 1) sobre la malla original,
coloreando los nodos por grado y las comunidades Louvain.

Uso: python draw_networks.py [--rule R1] [--lmax D2] [--run 1]
"""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection

import plotstyle as ps
from config import FIG_DIR, LMAX_TEX, MAX_CYCLE, N_NODES, NETS_DIR, node_xy
from loader import FIXED_EDGE_SET, edges_to_graph, iter_cycle_edges

ps.apply()
XY = np.array([node_xy(i) for i in range(1, N_NODES + 1)], dtype=float)


def draw(ax, edges, g, mode, vmax=None):
    es = np.array(list(edges))
    dyn = np.array([frozenset(e) not in FIXED_EDGE_SET for e in es])
    segs = np.stack([XY[es[:, 0]], XY[es[:, 1]]], axis=1)
    ax.add_collection(LineCollection(segs[~dyn], colors="#e1e0d9", lw=0.25, zorder=1))
    ax.add_collection(LineCollection(segs[dyn], colors="#52514e", lw=0.12, alpha=0.35, zorder=2))
    deg = np.array(g.degree())
    if mode == "degree":
        order = np.argsort(deg)
        # Escala logarítmica común a todos los paneles (vmax = grado máximo global).
        from matplotlib.colors import LogNorm
        rel = np.log(deg[order] / 4.0) / np.log((vmax or deg.max()) / 4.0)
        sc = ax.scatter(XY[order, 0], XY[order, 1], c=deg[order], s=1.5 + 35 * np.clip(rel, 0, 1) ** 2,
                        cmap=ps.SEQ_BLUE, norm=LogNorm(vmin=4, vmax=vmax or deg.max()), lw=0, zorder=3)
        return sc
    import random; random.seed(0)
    part = g.community_multilevel()
    memb = np.array(part.membership)
    cols = np.array(ps.CAT + ["#898781", "#5aa9e6", "#c45a2a", "#7bc96f", "#b89a00", "#a05080", "#305030", "#8070d0"])
    ax.scatter(XY[:, 0], XY[:, 1], c=cols[memb % len(cols)], s=4, lw=0, zorder=3)
    return part


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule", default="R1")
    ap.add_argument("--lmax", default="D2")
    ap.add_argument("--run", type=int, default=1)
    ap.add_argument("--cycle", type=int, default=MAX_CYCLE)
    args = ap.parse_args()
    strategies = ps.STRATEGIES
    graphs = {}
    for s in strategies:
        run_dir = os.path.join(NETS_DIR, args.rule, s, args.lmax, str(args.run))
        for c, e, _ in iter_cycle_edges(run_dir, range(args.cycle + 1)):
            edges = e
        graphs[s] = (edges, edges_to_graph(edges))
    vmax = max(max(g.degree()) for _, g in graphs.values())
    # Disposición 4 x 4: cuatro estrategias por bloque de dos filas (grado / comunidades);
    # el hueco libre del segundo bloque aloja la barra de color del grado.
    ncol = 4
    fig, axes = plt.subplots(4, ncol, figsize=(5.15, 5.6), constrained_layout=True)
    sc = None
    for j, s in enumerate(strategies):
        edges, g = graphs[s]
        blk, col = divmod(j, ncol)
        for i, mode in enumerate(["degree", "communities"]):
            ax = axes[2 * blk + i, col]
            res = draw(ax, edges, g, mode, vmax=vmax)
            if mode == "degree":
                sc = res
            ax.set_xlim(-1, 50); ax.set_ylim(-1, 50); ax.set_aspect("equal")
            ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
            for sp in ax.spines.values():
                sp.set_visible(False)
            if i == 0:
                ax.set_title(f"{ps.STRAT_SHORT[s]}   $k_{{max}}$ = {max(g.degree())}", fontsize=7)
            else:
                ax.set_title(f"$n_C$ = {len(res)},  $M$ = {res.modularity:.2f}", fontsize=6.5)
    # huecos: barra de color en el primero, el resto en blanco
    empties = [axes[r, c] for r in range(4) for c in range(ncol) if not axes[r, c].has_data()]
    for k, ax in enumerate(empties):
        ax.axis("off")
    if empties and sc is not None:
        cax = empties[0].inset_axes([0.15, 0.1, 0.12, 0.8])
        cb = fig.colorbar(sc, cax=cax)
        cb.set_label("degree (log scale)", fontsize=6.5)
        cb.ax.tick_params(labelsize=6)
    fig.suptitle(rf"Rule {args.rule[1]}, $\ell_{{max}}$ = {LMAX_TEX[args.lmax]}, cycle {args.cycle}: "
                 "degree (rows 1 and 3) and Louvain communities (rows 2 and 4)", fontsize=7)
    name = f"networks_{args.rule}_{args.lmax}_c{args.cycle}"
    fig.savefig(os.path.join(FIG_DIR, name + ".png"), dpi=400)
    fig.savefig(os.path.join(FIG_DIR, name + ".pdf"))
    print("figura:", name)


if __name__ == "__main__":
    main()
