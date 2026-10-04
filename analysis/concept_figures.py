"""Figuras conceptuales del modelo: ciclo de recableado, estrategias de exploración y
reglas de recableado. Salida en figures/concept_*.pdf|png."""
import math
import os
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch

import plotstyle as ps
from config import FIG_DIR

ps.apply()
os.makedirs(FIG_DIR, exist_ok=True)
BLUE, ORANGE, AQUA, YELLOW, PINK, GREEN, VIOLET, RED = ps.CAT
INK, INK2, MUTED, GRID_C = "#0b0b0b", "#52514e", "#898781", "#d5d4cd"


def save(fig, name):
    fig.savefig(os.path.join(FIG_DIR, name + ".pdf"))
    fig.savefig(os.path.join(FIG_DIR, name + ".png"), dpi=400)
    plt.close(fig)
    print("figura:", name)


# ------------------------------------------------------------------ mini grid
def mini_grid(n=9, dynamic=()):
    G = nx.grid_2d_graph(n, n)
    for e in G.edges():
        G.edges[e]["dyn"] = False
    for a, b in dynamic:
        G.add_edge(a, b, dyn=True)
    return G


def draw_grid(ax, G, n=9, node_size=9, edges=True):
    for u, v, d in (G.edges(data=True) if edges else []):
        if d["dyn"]:
            ax.plot([u[0], v[0]], [u[1], v[1]], color=INK2, lw=0.8, ls=(0, (3, 2)), zorder=2)
        else:
            ax.plot([u[0], v[0]], [u[1], v[1]], color=GRID_C, lw=0.8, zorder=1)
    xs, ys = zip(*G.nodes())
    ax.scatter(xs, ys, s=node_size, color="#c3c2b7", zorder=3, lw=0)
    ax.set_xlim(-0.7, n - 0.3); ax.set_ylim(-0.7, n - 0.3)
    ax.set_aspect("equal"); ax.axis("off")


def draw_route(ax, route, color, label=None, lw=1.6, ls="-", zorder=5, marker=True):
    xs = [p[0] for p in route]; ys = [p[1] for p in route]
    ax.plot(xs, ys, color=color, lw=lw, ls=ls, zorder=zorder, label=label, solid_capstyle="round")
    if marker:
        ax.scatter(xs[1:-1], ys[1:-1], s=14, color=color, zorder=zorder + 1, lw=0)
        ax.scatter([xs[-1]], [ys[-1]], s=38, color=color, zorder=zorder + 1, lw=0, marker="s")


def compass_route(G, src, dst):
    route = [src]; cur = src
    while cur != dst and len(route) < 60:
        best, bang = None, 1e9
        for nb in G.neighbors(cur):
            if nb in route:
                continue
            a1 = math.atan2(nb[1] - cur[1], nb[0] - cur[0])
            a2 = math.atan2(dst[1] - cur[1], dst[0] - cur[0])
            ang = abs((a1 - a2 + math.pi) % (2 * math.pi) - math.pi)
            if ang < bang:
                best, bang = nb, ang
        if best is None:
            break
        route.append(best); cur = best
    return route


def saw(G, src, h, weight, rng):
    """Caminata auto-evitante con pesos weight(prev, cur, cand)."""
    route = [src]; cur = src; prev = None
    for _ in range(h):
        cands = [x for x in G.neighbors(cur) if x not in route]
        if not cands:
            break
        w = np.array([weight(prev, cur, x) for x in cands], float)
        nxt = cands[rng.choice(len(cands), p=w / w.sum())]
        prev, cur = cur, nxt
        route.append(cur)
    return route


# ================================================================== FIGURA 1: ciclo
def fig_cycle():
    """Un ciclo visto desde un nodo i: estado inicial, exploración y recableado."""
    n = 9
    src = (3, 3); lmax = 3.2
    d1, d2 = (5, 5), (1, 5)              # enlaces dinámicos actuales de i
    other_dyn = []
    G = mini_grid(n, [(src, d1), (src, d2)] + other_dyn)
    deg = dict(G.degree())
    rng = np.random.default_rng(21)
    # trazadores de i: caminatas auto-evitantes uniformes
    routes = [saw(G, src, h, lambda p, c, x: 1.0, np.random.default_rng(sd)) for h, sd in [(5, 1), (6, 4), (4, 9), (7, 2), (5, 14), (6, 8)]]
    # tabla f_v (nodos no vecinos visitados) y f_e (uso de enlaces dinámicos)
    nbrs = set(G.neighbors(src))
    fv = {}
    fe = {d1: 0, d2: 0}
    for r in routes:
        if r[1] in fe:
            fe[r[1]] += 1
        for x in r[1:]:
            if x not in nbrs:
                fv[x] = fv.get(x, 0) + 1
    def collinear(x):
        return any(abs((dl[0] - src[0]) * (x[1] - src[1]) - (dl[1] - src[1]) * (x[0] - src[0])) < 1e-9 for dl in (d1, d2))
    j = max((x for x in fv if not collinear(x)), key=lambda x: (fv[x], -math.hypot(x[0] - src[0], x[1] - src[1])))
    least = min(fe, key=fe.get)

    fig, axes = plt.subplots(1, 3, figsize=(5.15, 2.0))
    titles = ["(a) Start of cycle $t$", "(b) Exploration phase", "(c) Rewiring phase"]
    for k, ax in enumerate(axes):
        # malla estática
        for u, v, d in G.edges(data=True):
            if not d["dyn"]:
                ax.plot([u[0], v[0]], [u[1], v[1]], color=GRID_C, lw=0.8, zorder=1)
        xs, ys = zip(*G.nodes()); ax.scatter(xs, ys, s=6, color="#c3c2b7", zorder=3, lw=0)
        for (u, v) in other_dyn:
            ax.plot([u[0], v[0]], [u[1], v[1]], color=INK2, lw=0.8, ls=(0, (3, 2)), zorder=2)
        ax.add_patch(Circle(src, lmax, fc="none", ec=INK2, lw=0.7, ls=(0, (1.5, 1.5)), zorder=2))
        ax.text(src[0] - lmax * 0.78, src[1] + lmax * 0.72, "$\\ell_{max}$", fontsize=6.5, color=INK2, ha="right")
        # enlaces dinámicos de i
        for dl in (d1, d2):
            removed = (k == 2 and dl == least)
            ax.plot([src[0], dl[0]], [src[1], dl[1]], color=RED if removed else BLUE, lw=1.6,
                    ls=(0, (3, 2)) if removed else "-", alpha=0.6 if removed else 1, zorder=4)
        if k == 0:
            ax.annotate("dynamic links of $i$\n(length $\\leq \\ell_{max}$)", xy=((src[0] + d1[0]) / 2, (src[1] + d1[1]) / 2),
                        xytext=(6.2, 7.6), fontsize=5.5, color=BLUE, ha="center",
                        arrowprops=dict(arrowstyle="-", color=BLUE, lw=0.6))
            ax.annotate("static links\n(never change)", xy=(6.5, 1), xytext=(7.4, -0.2), fontsize=5.5, color=INK2, ha="center",
                        arrowprops=dict(arrowstyle="-", color=INK2, lw=0.6))
        if k == 1:
            for r, col in zip(routes, [AQUA, ORANGE, VIOLET, GREEN, PINK, YELLOW]):
                xs = [p[0] for p in r]; ys = [p[1] for p in r]
                ax.plot(xs, ys, color=col, lw=1.1, zorder=5, alpha=0.9)
                ax.scatter([xs[-1]], [ys[-1]], s=16, color=col, zorder=6, lw=0, marker="s")
            # tablas
            top = sorted(fv.items(), key=lambda kv: -kv[1])[:4]
            txt = "$f_{v,i}$ (visits)\n" + "\n".join(f"{x}: {c}" for x, c in top) + "\n…"
            ax.text(0.02, 0.98, txt, transform=ax.transAxes, fontsize=5.4, va="top", ha="left", color=INK,
                    bbox=dict(fc="white", ec=GRID_C, boxstyle="round,pad=0.3"), zorder=8)
            txt2 = "$f_{e,i}$ (link use)\n" + "\n".join(f"{x}: {c}" for x, c in fe.items())
            ax.text(0.98, 0.98, txt2, transform=ax.transAxes, fontsize=5.4, va="top", ha="right", color=INK,
                    bbox=dict(fc="white", ec=GRID_C, boxstyle="round,pad=0.3"), zorder=8)
        if k == 2:
            for x, c in fv.items():
                ax.scatter([x[0]], [x[1]], s=8 + 14 * c, color=BLUE, alpha=0.35, zorder=4, lw=0)
            ax.plot([src[0], j[0]], [src[1], j[1]], color=GREEN, lw=1.8, zorder=6)
            ax.scatter([j[0]], [j[1]], s=120, fc="none", ec=GREEN, lw=1.6, zorder=7)
            ax.text(j[0] + 0.4, j[1] + 0.05, "$j$ (chosen by\nthe rule)", fontsize=5.5, color=GREEN, va="center")
            mx, my = (src[0] + least[0]) / 2, (src[1] + least[1]) / 2
            ax.text(mx + 0.3, my - 0.35, "released\n(least used)", fontsize=5.5, color=RED, ha="left", va="top")
            ax.text(0.02, 0.98, "request sent to $j$ along\nthe recorded route;\nsynchronous update",
                    transform=ax.transAxes, fontsize=5.3, va="top", color=INK2,
                    bbox=dict(fc="white", ec=GRID_C, boxstyle="round,pad=0.3"), zorder=8)
        ax.scatter([src[0]], [src[1]], s=55, color=INK, zorder=9, marker="D")
        ax.text(src[0] - 0.55, src[1] - 0.1, "$i$", fontsize=8, ha="center", va="center")
        ax.set_xlim(-0.7, n - 0.3); ax.set_ylim(-0.7, n - 0.3); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(titles[k], fontsize=6.5, loc="left")
    fig.subplots_adjust(top=0.92, bottom=0.02, left=0.01, right=0.99, wspace=0.05)
    save(fig, "concept_cycle")


# ================================================================== FIGURA 2: exploración
def fig_exploration():
    n = 9
    dyn = [((1, 1), (4, 3)), ((2, 6), (6, 7)), ((5, 2), (7, 5)), ((3, 3), (3, 6)), ((6, 4), (8, 1))]
    G = mini_grid(n, dyn)
    src, dst = (1, 2), (7, 6)
    fig = plt.figure(figsize=(5.15, 2.95))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1.25], wspace=0.06, left=0.01, right=0.99, top=0.93, bottom=0.17)

    # (a) estrategias informadas
    ax = fig.add_subplot(gs[0]); draw_grid(ax, G, n)
    sp = nx.shortest_path(G, src, dst)
    cr = compass_route(G, src, dst)
    draw_route(ax, sp, BLUE, "SP: geodesic")
    draw_route(ax, cr, ORANGE, "CR: smallest angle", ls=(0, (4, 1.5)))
    ax.scatter([src[0]], [src[1]], s=60, color=INK, zorder=8, marker="D")
    ax.scatter([dst[0]], [dst[1]], s=80, color=INK, zorder=8, marker="*")
    ax.text(src[0] - 0.55, src[1] - 0.08, "$i$", fontsize=8, ha="center", va="center")
    ax.text(dst[0], dst[1] + 0.45, "destination", fontsize=5.6, ha="center")
    ax.legend(loc="upper center", fontsize=5.6, frameon=False, bbox_to_anchor=(0.5, -0.01), ncol=1, handlelength=1.6)
    ax.set_title("(a) Informed exploration", fontsize=7, loc="left")

    # (b) caminatas auto-evitantes
    ax = fig.add_subplot(gs[1]); draw_grid(ax, G, n)
    deg = dict(G.degree())
    w_rw = lambda p, c, x: 1.0
    w_rwd = lambda p, c, x: deg[x]
    w_rwi = lambda p, c, x: 1.0 / deg[x]
    r1 = saw(G, src, 7, w_rw, np.random.default_rng(3))
    r2 = saw(G, src, 7, w_rwd, np.random.default_rng(11))
    r3 = saw(G, src, 7, w_rwi, np.random.default_rng(5))
    draw_route(ax, r1, AQUA, "RW: uniform")
    draw_route(ax, r2, YELLOW, "RWD: towards hubs", ls=(0, (4, 1.5)))
    draw_route(ax, r3, PINK, "RWI: away from hubs", ls=(0, (1, 1.2)))
    ax.scatter([src[0]], [src[1]], s=60, color=INK, zorder=8, marker="D")
    ax.text(src[0] - 0.55, src[1] - 0.08, "$i$", fontsize=8, ha="center", va="center")
    ax.legend(loc="upper center", fontsize=5.6, frameon=False, bbox_to_anchor=(0.5, -0.01), ncol=1, handlelength=1.6,
              title="self-avoiding, $h \\sim U\\{2,..,\\mathrm{diam}(G_t)\\}$", title_fontsize=5.6)
    ax.set_title("(b) Walk-based exploration", fontsize=7, loc="left")

    # (c) diagrama de decisión + tabla de pesos
    ax = fig.add_subplot(gs[2]); ax.set_xlim(-2.4, 3.6); ax.set_ylim(-4.3, 1.9); ax.set_aspect("equal"); ax.axis("off")
    t, v = (-1.5, 0.0), (0.0, 0.0)
    x1, x2, x3 = (0.9, 1.25), (1.6, 0.0), (0.9, -1.25)
    for a_, b_ in [(t, v), (v, x1), (v, x2), (v, x3)]:
        ax.plot([a_[0], b_[0]], [a_[1], b_[1]], color=INK2, lw=0.9, zorder=1)
    ax.plot([t[0], x1[0]], [t[1], x1[1]], color=GREEN, lw=1.6, zorder=2)
    ax.scatter(*zip(t, v, x1, x2, x3), s=[70, 90, 60, 60, 60], color=["#c3c2b7", INK, BLUE, BLUE, BLUE], zorder=3, lw=0)
    ax.plot([t[0] - 0.2, t[0] + 0.2], [t[1] - 0.2, t[1] + 0.2], color=RED, lw=1.4, zorder=4)
    ax.plot([t[0] - 0.2, t[0] + 0.2], [t[1] + 0.2, t[1] - 0.2], color=RED, lw=1.4, zorder=4)
    ax.text(t[0], t[1] - 0.4, "$t$ (previous,\nvisited)", fontsize=5.6, ha="center", va="top", color=INK2)
    ax.text(v[0] + 0.15, v[1] - 0.4, "$v$ (current)", fontsize=5.8, ha="center", va="top", color=INK)
    ax.text(x1[0] + 0.25, x1[1] + 0.05, "$x_1 \\in N(t)$: triangle", fontsize=5.6, va="center", color=GREEN)
    ax.text(x2[0] + 0.25, x2[1], "$x_2$", fontsize=6.2, va="center")
    ax.text(x3[0] + 0.25, x3[1] - 0.05, "$x_3$", fontsize=6.2, va="center")
    ax.text(-2.4, 1.85, "(c) Next-hop weights $w(x)$", fontsize=7, va="top")
    rows = [("RW", "1", "1", "1"), ("RWD", "$k_{x_1}$", "$k_{x_2}$", "$k_{x_3}$"),
            ("RWI", "$1/k_{x_1}$", "$1/k_{x_2}$", "$1/k_{x_3}$"), ("RWL($q$)", "1", "$1/q$", "$1/q$")]
    y0 = -2.35; cols = [-0.5, 0.6, 1.7]
    ax.plot([-2.3, 2.4], [y0 + 0.2, y0 + 0.2], color=GRID_C, lw=0.6)
    ax.text(-2.2, y0 + 0.42, "strategy", fontsize=5.8, color=MUTED, va="center")
    for j, h in enumerate(["$x_1$", "$x_2$", "$x_3$"]):
        ax.text(cols[j], y0 + 0.42, h, fontsize=6, color=MUTED, ha="center", va="center")
    for i, (name, *vals) in enumerate(rows):
        y = y0 - 0.36 * i
        ax.text(-2.2, y, name, fontsize=6.2, color=INK, va="center")
        for j, val in enumerate(vals):
            ax.text(cols[j], y, val, fontsize=6.2, ha="center", va="center",
                    color=GREEN if (name.startswith("RWL") and j == 0) else INK)
    ax.text(-2.2, y0 - 0.36 * 4 - 0.1, "A move back to $t$ is never available,\nso a return weight (node2vec's $1/p$)\nhas no effect.",
            fontsize=5.3, color=MUTED, va="top")
    save(fig, "concept_exploration")


# ================================================================== FIGURA 3: reglas
def fig_rules():
    n = 9
    G = mini_grid(n)
    src = (2, 2); c = 20; lmax = 3.6
    # tabla f_v de ejemplo (nodos no vecinos visitados por los 20 trazadores)
    fv = {(4, 3): 13, (3, 3): 7, (4, 2): 9, (1, 3): 4, (5, 3): 11, (2, 5): 6, (6, 2): 3, (4, 4): 5, (0, 0): 2, (1, 5): 3}
    geo = nx.single_source_shortest_path_length(G, src)
    dist = lambda a: math.hypot(a[0] - src[0], a[1] - src[1])
    inside = {x: dist(x) <= lmax for x in fv}
    # R1: argmax con umbral c/2 y dentro de lmax
    elig1 = [x for x in fv if fv[x] >= c / 2 and inside[x]]
    sel1 = max(elig1, key=lambda x: fv[x]) if elig1 else None
    # R2: distancia geodésica 2, dentro de lmax
    elig2 = [x for x in fv if geo.get(x) == 2 and inside[x]]
    sel2 = elig2[0]
    # R3: proporcional entre los que están dentro
    elig3 = [x for x in fv if inside[x]]
    tot = sum(fv[x] for x in elig3)

    fig, axes = plt.subplots(1, 3, figsize=(5.15, 2.0))
    titles = ["(a) R1: most visited, $f_{v,i} \\geq c/2$", "(b) R2: uniform, geodesic dist. 2",
              "(c) R3: probability $\\propto f_{v,i}$"]
    for k, ax in enumerate(axes):
        draw_grid(ax, G, n, node_size=6, edges=False)
        ax.add_patch(Circle(src, lmax, fc="none", ec=INK2, lw=0.8, ls=(0, (2, 2)), zorder=2))
        ax.text(src[0] + lmax * 0.72, src[1] - lmax * 0.78, "$\\ell_{max}$", fontsize=7, color=INK2)
        # candidatos
        for x, f in fv.items():
            col = BLUE if inside[x] else MUTED
            ax.scatter([x[0]], [x[1]], s=10 + 9 * f, color=col, alpha=0.9 if inside[x] else 0.5, zorder=4, lw=0)
            if k == 2 and inside[x]:
                off = {(3, 3): (-0.5, 0.3), (4, 3): (0, 0.33), (5, 3): (0.5, 0.3), (4, 2): (0, -0.55), (4, 4): (0.5, 0.25)}
                dx, dy = off.get(x, (0, 0.3))
                ax.text(x[0] + dx, x[1] + dy, f"{f/tot:.2f}", fontsize=5, color=VIOLET, zorder=6, ha="center")
            else:
                ax.text(x[0] + 0.22, x[1] + 0.22, str(f), fontsize=6, color=INK2 if inside[x] else MUTED, zorder=6)
        ax.set_ylim(-1.3, n - 0.3)
        ax.scatter([src[0]], [src[1]], s=55, color=INK, zorder=7, marker="D")
        ax.text(src[0] - 0.55, src[1] - 0.35, "$i$", fontsize=8)
        if k == 0:
            for x in fv:
                if fv[x] >= c / 2:
                    ax.add_patch(Circle(x, 0.38, fc="none", ec=ORANGE, lw=1.0, zorder=5))
            ax.scatter([sel1[0]], [sel1[1]], s=140, fc="none", ec=GREEN, lw=1.8, zorder=8)

        elif k == 1:
            for x in elig2:
                ax.add_patch(Circle(x, 0.38, fc="none", ec=ORANGE, lw=1.0, zorder=5))
            ax.scatter([sel2[0]], [sel2[1]], s=140, fc="none", ec=GREEN, lw=1.8, zorder=8)

        else:
            pass
        ax.set_title(titles[k], fontsize=6.3, loc="left")
    fig.subplots_adjust(top=0.93, bottom=0.02, left=0.01, right=0.99, wspace=0.05)
    save(fig, "concept_rules")


if __name__ == "__main__":
    fig_cycle()
    fig_exploration()
    fig_rules()
