"""Figura y resumen de los experimentos de control (R1, lmax = D/2, 5 corridas):
   base : horizonte adaptativo U[2, diam(G_t)], umbral de R1 = c/2 (configuración del artículo)
   thr0 : umbral de R1 = 0
   h30  : horizonte fijo de 30 saltos
Lee results/controls_metrics.csv y results/controls_tracers.csv (producidos por controls.py),
escribe figures/controls.pdf y results/controls_summary.csv e imprime las comparaciones usadas en el texto.
"""
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import plotstyle as ps
from config import FIG_DIR, MAX_CYCLE, RESULTS_DIR

ps.apply()
VARIANTS = [("base", "Reference ($\\theta=c/2$, $h\\sim U[2,d_t]$)"), ("thr0", "No threshold ($\\theta=0$)"), ("h30", "Fixed horizon ($h=30$)")]
STRATS = ["RWI", "RW", "RWD", "N2Vp1q2"]
METRICS = ["tracer_len", "frac_rewired", "k_max", "diameter", "dyn_len_frac_lmax", "clustering"]
ps.METRIC_LABEL["tracer_len"] = "Tracer route length (hops)"
ps.METRIC_LABEL["n_distinct"] = "Distinct nodes visited"


def load():
    m = pd.read_csv(os.path.join(RESULTS_DIR, "controls_metrics.csv"))
    t = pd.read_csv(os.path.join(RESULTS_DIR, "controls_tracers.csv"))
    m = m.merge(t, on=["variant", "strategy", "run", "cycle"], how="left")
    return m


def fig_controls(m, name="controls"):
    fig, axes = plt.subplots(len(METRICS), len(VARIANTS), figsize=(5.15, 1.08 * len(METRICS)),
                             sharex=True, sharey="row", constrained_layout=True)
    for j, (v, vlabel) in enumerate(VARIANTS):
        for i, met in enumerate(METRICS):
            ax = axes[i, j]
            for s in STRATS:
                d = m[(m.variant == v) & (m.strategy == s)].groupby("cycle")[met].agg(["mean", "std"]).reset_index()
                if d.empty or d["mean"].isna().all():
                    continue
                st = ps.STYLE[s]
                ax.plot(d.cycle, d["mean"], color=st["color"], ls=st["ls"], marker=st["marker"],
                        markevery=5, label=ps.STRAT_SHORT[s], lw=1.1)
                ax.fill_between(d.cycle, d["mean"] - d["std"], d["mean"] + d["std"], color=st["color"], alpha=0.12, lw=0)
            if i == 0:
                ax.set_title(vlabel, pad=16, fontsize=7.5)
            if j == 0:
                ps_row_label(ax, i, met)
            if i == len(METRICS) - 1:
                ax.set_xlabel("Rewiring cycle")
            ax.set_xlim(0, MAX_CYCLE)
            if met in ("k_max", "diameter"):
                ax.set_yscale("log")
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=len(STRATS), bbox_to_anchor=(0.5, 1.0))
    fig.savefig(os.path.join(FIG_DIR, name + ".pdf"))
    fig.savefig(os.path.join(FIG_DIR, name + ".png"))
    plt.close(fig)
    print("figura:", name)


def ps_row_label(ax, i, met):
    ax.text(0.0, 1.03, f"({chr(97 + i)}) {ps.METRIC_LABEL[met]}", transform=ax.transAxes,
            ha="left", va="bottom", fontsize=7.2, color="#0b0b0b", clip_on=False)


def summary(m):
    fin = m[m.cycle == MAX_CYCLE]
    cols = ["k_max", "diameter", "clustering", "modularity", "H_norm", "frac_rewired", "dyn_len_frac_lmax", "dyn_frac_top1pct", "tracer_len", "n_distinct"]
    g = fin.groupby(["variant", "strategy"])[cols].agg(["mean", "std"])
    g.columns = [f"{a}_{b}" for a, b in g.columns]
    # actividad media sobre los ciclos 1..30 y sobre los últimos 10
    act = m[m.cycle >= 1].groupby(["variant", "strategy", "run"]).frac_rewired.mean().groupby(["variant", "strategy"]).agg(["mean", "std"])
    act.columns = ["act_mean_1_30", "act_sd_1_30"]
    act2 = m[m.cycle >= 21].groupby(["variant", "strategy", "run"]).frac_rewired.mean().groupby(["variant", "strategy"]).mean()
    g = g.join(act).join(act2.rename("act_mean_21_30"))
    # longitud de trazador en el ciclo 1 y en el último
    t1 = m[m.cycle == 1].groupby(["variant", "strategy"]).tracer_len.mean().rename("tracer_len_c1")
    g = g.join(t1).reset_index()
    g.to_csv(os.path.join(RESULTS_DIR, "controls_summary.csv"), index=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
    print(g[["variant", "strategy", "k_max_mean", "k_max_std", "diameter_mean", "clustering_mean", "modularity_mean",
             "frac_rewired_mean", "act_mean_1_30", "act_mean_21_30", "dyn_len_frac_lmax_mean", "dyn_frac_top1pct_mean",
             "tracer_len_c1", "tracer_len_mean", "n_distinct_mean"]].round(3).to_string())
    # comparación con las corridas publicadas (10 corridas, nets/)
    pub = pd.read_csv(os.path.join(RESULTS_DIR, "final_state.csv"))
    pub = pub[(pub.rule == "R1") & (pub.lmax == "D2") & pub.strategy.isin(STRATS)]
    print("\n== publicadas (R1, D/2, 10 corridas) ==")
    print(pub[["strategy", "k_max_mean", "k_max_sd", "diameter_mean", "clustering_mean", "modularity_mean", "frac_rewired_mean", "dyn_len_frac_lmax_mean"]].round(3).to_string())


if __name__ == "__main__":
    m = load()
    fig_controls(m)
    summary(m)
