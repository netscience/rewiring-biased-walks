"""Figuras del análisis (PDF + PNG en figures/).

Requiere haber ejecutado run_metrics.py y aggregate.py.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import plotstyle as ps
from config import FIG_DIR, LMAX_LABELS, LMAX_TEX, MAX_CYCLE, N2V_VALUES, RESULTS_DIR, RULES

ps.apply()
os.makedirs(FIG_DIR, exist_ok=True)

MEAN = pd.read_csv(os.path.join(RESULTS_DIR, "metrics_mean.csv"))
FINAL = pd.read_csv(os.path.join(RESULTS_DIR, "final_state.csv"))
CONV = pd.read_csv(os.path.join(RESULTS_DIR, "convergence.csv"))
ALL_STRATS = ps.STRATEGIES_EXT


def save(fig, name):
    fig.savefig(os.path.join(FIG_DIR, name + ".pdf"))
    fig.savefig(os.path.join(FIG_DIR, name + ".png"))
    plt.close(fig)
    print("figura:", name)


def row_label(ax, i, met):
    """Etiqueta de fila tipo subfigura, en lugar de la etiqueta del eje y."""
    ax.text(0.0, 1.03, f"({chr(97 + i)}) {ps.METRIC_LABEL[met]}", transform=ax.transAxes,
            ha="left", va="bottom", fontsize=7.2, color="#0b0b0b", clip_on=False)


# ---------------------------------------------------------------- series temporales
def fig_timeseries(metrics, lmax, name, strategies=ps.STRATEGIES):
    fig, axes = plt.subplots(len(metrics), len(RULES), figsize=(5.15, 1.08 * len(metrics)),
                             sharex=True, sharey="row", constrained_layout=True)
    for j, rule in enumerate(RULES):
        for i, met in enumerate(metrics):
            ax = axes[i, j]
            for s in strategies:
                d = MEAN[(MEAN.rule == rule) & (MEAN.strategy == s) & (MEAN.lmax == lmax)].sort_values("cycle")
                if d.empty:
                    continue
                st = ps.STYLE[s]
                ax.plot(d.cycle, d[met + "_mean"], color=st["color"], ls=st["ls"], marker=st["marker"],
                        markevery=5, label=ps.STRAT_SHORT[s], lw=1.1)
                ax.fill_between(d.cycle, d[met + "_mean"] - d[met + "_sd"], d[met + "_mean"] + d[met + "_sd"],
                                color=st["color"], alpha=0.12, lw=0)
            if i == 0:
                ax.set_title(f"Rule {rule[1]}", pad=16)
            if j == 0:
                row_label(ax, i, met)
            if i == len(metrics) - 1:
                ax.set_xlabel("Rewiring cycle")
            ax.set_xlim(0, MAX_CYCLE)
            if met in ("k_max", "diameter"):
                ax.set_yscale("log")
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=len(strategies), bbox_to_anchor=(0.5, 1.0))
    save(fig, name)


# ---------------------------------------------------------------- heatmaps p x q
def fig_n2v_heatmaps(metrics, lmax, name, rules=RULES):
    fig, axes = plt.subplots(len(metrics), len(rules), figsize=(1.45 * len(rules) + 0.8, 1.32 * len(metrics)),
                             constrained_layout=True)
    axes = np.atleast_2d(axes)
    for i, met in enumerate(metrics):
        sub = FINAL[(FINAL.family == "N2V") & (FINAL.lmax == lmax)]
        vmin, vmax = sub[met + "_mean"].min(), sub[met + "_mean"].max()
        cmap = ps.DIV_BR if met == "assortativity" else ps.SEQ_BLUE
        if met == "assortativity":
            m = max(abs(vmin), abs(vmax)); vmin, vmax = -m, m
        for j, rule in enumerate(rules):
            ax = axes[i, j]
            d = sub[sub.rule == rule]
            M = np.full((4, 4), np.nan)
            for _, r in d.iterrows():
                M[N2V_VALUES.index(r.q), N2V_VALUES.index(r.p)] = r[met + "_mean"]
            im = ax.imshow(M, origin="lower", cmap=cmap, vmin=vmin, vmax=vmax, aspect="equal")
            for a in range(4):
                for b in range(4):
                    v = M[a, b]
                    if np.isfinite(v):
                        norm = (v - vmin) / (vmax - vmin + 1e-12)
                        txt = f"{v:.0f}" if met in ("k_max", "diameter", "n_communities") else f"{v:.2f}"
                        ax.text(b, a, txt, ha="center", va="center", fontsize=6,
                                color="white" if (norm > 0.6 or (met == "assortativity" and abs(v) > 0.5 * m)) else "#0b0b0b")
            ax.set_xticks(range(4)); ax.set_xticklabels([f"{v:g}" for v in N2V_VALUES])
            ax.set_yticks(range(4)); ax.set_yticklabels([f"{v:g}" for v in N2V_VALUES])
            ax.grid(False)
            if i == 0:
                ax.set_title(f"Rule {rule[1]}")
            if i == len(metrics) - 1:
                ax.set_xlabel("$p$ (return; inert)")
            if j == 0:
                ax.set_ylabel("$q$ (locality)")
            ax.text(0.02, 0.98, ps.METRIC_LABEL[met], transform=ax.transAxes, fontsize=6, va="top",
                    bbox=dict(fc="white", ec="none", alpha=0.75, pad=1.2))
        fig.colorbar(im, ax=axes[i, :].tolist(), shrink=0.8, pad=0.02)
    fig.suptitle(rf"RWL exploration (node2vec transition rule), $\ell_{{max}}$ = {LMAX_TEX[lmax]}, cycle {MAX_CYCLE}", fontsize=8.5)
    save(fig, name)


# ---------------------------------------------------------------- estado final por estrategia
def fig_final_by_strategy(metrics, name, strategies=ps.STRATEGIES):
    fig, axes = plt.subplots(len(metrics), len(RULES), figsize=(5.15, 1.0 * len(metrics) + 0.6),
                             sharex=True, sharey="row", constrained_layout=True)
    lm_style = {lm: dict(color=ps.CAT[i], marker=ps.MARKERS[i]) for i, lm in enumerate(LMAX_LABELS)}
    x = np.arange(len(strategies))
    for j, rule in enumerate(RULES):
        for i, met in enumerate(metrics):
            ax = axes[i, j]
            for k, lm in enumerate(LMAX_LABELS):
                d = FINAL[(FINAL.rule == rule) & (FINAL.lmax == lm)].set_index("strategy").reindex(strategies)
                off = (k - 1.5) * 0.17
                ax.errorbar(x + off, d[met + "_mean"], yerr=d[met + "_sd"], fmt=lm_style[lm]["marker"],
                            color=lm_style[lm]["color"], ms=3.2, lw=0.8, capsize=1.5, label=LMAX_TEX[lm])
            ax.set_xticks(x); ax.set_xticklabels([ps.STRAT_SHORT[s] for s in strategies], rotation=40, ha="right")
            if i < len(metrics) - 1:
                ax.tick_params(labelbottom=False)
            if i == 0:
                ax.set_title(f"Rule {rule[1]}", pad=16)
            if j == 0:
                row_label(ax, i, met)
            if met in ("k_max",):
                ax.set_yscale("log")
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, bbox_to_anchor=(0.5, 1.0), title=r"$\ell_{max}$")
    save(fig, name)


# ---------------------------------------------------------------- convergencia
def fig_convergence_heatmap(metrics, tol, name):
    fig, axes = plt.subplots(len(metrics), len(RULES), figsize=(5.15, 0.9 * len(metrics) + 0.5),
                             constrained_layout=True, sharex=True, sharey=True)
    axes = np.atleast_2d(axes)
    sub = CONV[CONV.tol == tol]
    for i, met in enumerate(metrics):
        for j, rule in enumerate(RULES):
            ax = axes[i, j]
            d = sub[(sub.rule == rule) & (sub.metric == met)]
            M = np.full((len(LMAX_LABELS), len(ALL_STRATS)), np.nan)
            for _, r in d.iterrows():
                if r.strategy in ALL_STRATS:
                    M[LMAX_LABELS.index(r.lmax), ALL_STRATS.index(r.strategy)] = r["conv_cycle"]
            im = ax.imshow(M, cmap=ps.SEQ_BLUE, vmin=0, vmax=MAX_CYCLE, aspect="auto")
            for a in range(M.shape[0]):
                for b in range(M.shape[1]):
                    if np.isfinite(M[a, b]):
                        ax.text(b, a, f"{M[a,b]:.0f}", ha="center", va="center", fontsize=6,
                                color="white" if M[a, b] > 0.6 * MAX_CYCLE else "#0b0b0b")
            ax.set_xticks(range(len(ALL_STRATS)))
            ax.set_xticklabels([ps.STRAT_SHORT[s] for s in ALL_STRATS], rotation=45, ha="right", fontsize=6)
            ax.set_yticks(range(len(LMAX_LABELS))); ax.set_yticklabels([LMAX_TEX[l] for l in LMAX_LABELS])
            ax.grid(False)
            if i == 0:
                ax.set_title(f"Rule {rule[1]}", pad=16)
            if j == 0:
                row_label(ax, i, met)
    fig.colorbar(im, ax=axes.ravel().tolist(), shrink=0.6, pad=0.01, label=f"Convergence cycle (tol. {tol:.0%})")
    save(fig, name)


# ---------------------------------------------------------------- simetría q/p
def fig_ratio_symmetry(metrics, lmax, name):
    fig, axes = plt.subplots(len(metrics), len(RULES), figsize=(5.15, 1.22 * len(metrics)),
                             sharex=True, sharey="row", constrained_layout=True)
    axes = np.atleast_2d(axes)
    sub = FINAL[(FINAL.family == "N2V") & (FINAL.lmax == lmax)].copy()
    sub["ratio"] = sub.q / sub.p
    pstyle = {p: dict(color=ps.CAT[i], marker=ps.MARKERS[i]) for i, p in enumerate(N2V_VALUES)}
    for j, rule in enumerate(RULES):
        for i, met in enumerate(metrics):
            ax = axes[i, j]
            d = sub[sub.rule == rule]
            for p in N2V_VALUES:
                dp = d[d.p == p].sort_values("ratio")
                ax.errorbar(dp.ratio, dp[met + "_mean"], yerr=dp[met + "_sd"], fmt=pstyle[p]["marker"],
                            color=pstyle[p]["color"], ms=3.5, lw=0.8, capsize=1.5, label=f"$p$={p:g}")
            ax.set_xscale("log", base=2)
            if i == 0:
                ax.set_title(f"Rule {rule[1]}", pad=16)
            if j == 0:
                row_label(ax, i, met)
            if i == len(metrics) - 1:
                ax.set_xlabel("$q/p$")
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, bbox_to_anchor=(0.5, 1.0))
    save(fig, name)


# ---------------------------------------------------------------- acoplamiento actividad-hubs
def fig_activity_vs_hubs(lmax, name, strategies=ps.STRATEGIES):
    fig, axes = plt.subplots(1, len(RULES), figsize=(5.15, 1.75), sharey=True, constrained_layout=True)
    for j, rule in enumerate(RULES):
        ax = axes[j]
        for s in strategies:
            d = MEAN[(MEAN.rule == rule) & (MEAN.strategy == s) & (MEAN.lmax == lmax) & (MEAN.cycle >= 1)].sort_values("cycle")
            if d.empty:
                continue
            st = ps.STYLE[s]
            ax.plot(d.frac_rewired_mean, d.dyn_frac_top1pct_mean, color=st["color"], ls=st["ls"], lw=1,
                    marker=st["marker"], markevery=[0, -1], ms=3, label=ps.STRAT_SHORT[s])
        ax.set_title(f"Rule {rule[1]}")
        ax.set_xlabel(ps.METRIC_LABEL["frac_rewired"])
        if j == 0:
            ax.set_ylabel(ps.METRIC_LABEL["dyn_frac_top1pct"])
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=len(strategies), bbox_to_anchor=(0.5, 1.0))
    save(fig, name)


if __name__ == "__main__":
    ts_metrics = ["diameter", "clustering", "H_norm", "k_max", "modularity", "frac_rewired"]
    for lm in ["D2", "D8"]:
        fig_timeseries(ts_metrics, lm, f"timeseries_{lm}")
    hm_metrics = ["diameter", "clustering", "H_norm", "k_max", "modularity", "assortativity"]
    for lm in LMAX_LABELS:
        fig_n2v_heatmaps(hm_metrics, lm, f"n2v_heatmaps_{lm}")
    fig_final_by_strategy(["diameter", "clustering", "H_norm", "k_max", "modularity", "assortativity"], "final_by_strategy",
                          strategies=ps.STRATEGIES_EXT)
    fig_final_by_strategy(["dyn_len_frac_lmax", "dyn_frac_top1pct", "frac_rewired", "efficiency"], "final_by_strategy_2",
                          strategies=ps.STRATEGIES_EXT)
    for tol in (0.05, 0.10):
        fig_convergence_heatmap(["diameter", "clustering", "H_norm", "k_max", "modularity", "frac_rewired"], tol,
                                f"convergence_tol{int(tol*100):02d}")
    for lm in ["D2", "D8"]:
        fig_ratio_symmetry(["diameter", "clustering", "k_max", "modularity"], lm, f"n2v_ratio_{lm}")
        fig_activity_vs_hubs(lm, f"activity_vs_hubs_{lm}")
    if os.path.exists(os.path.join(RESULTS_DIR, "robustness.csv")):
        fig_robustness()
    fig_degree_distributions("D2")
    fig_degree_distributions("D16", name="degree_distributions_D16")
    fig_degree_evolution()


# ---------------------------------------------------------------- robustez (suplementario)
def fig_robustness(name="robustness", strategies=None):
    rb = pd.read_csv(os.path.join(RESULTS_DIR, "robustness.csv"))
    strategies = strategies or ps.STRATEGIES_EXT
    lm_style = {lm: dict(color=ps.CAT[i], marker=ps.MARKERS[i]) for i, lm in enumerate(LMAX_LABELS)}
    rows = [("attack", "R"), ("attack", "f_star"), ("failure", "R"), ("failure", "f_star")]
    labels = {("attack", "R"): "Robustness $R$, targeted attacks", ("attack", "f_star"): "Critical fraction $f^\\star$, targeted attacks",
              ("failure", "R"): "Robustness $R$, random failures", ("failure", "f_star"): "Critical fraction $f^\\star$, random failures"}
    fig, axes = plt.subplots(len(rows), len(RULES), figsize=(5.15, 1.2 * len(rows) + 0.6),
                             sharex=True, sharey="row", constrained_layout=True)
    x = np.arange(len(strategies))
    for j, rule in enumerate(RULES):
        for i, (scen, met) in enumerate(rows):
            ax = axes[i, j]
            for k, lm in enumerate(LMAX_LABELS):
                d = rb[(rb.rule == rule) & (rb.lmax == lm) & (rb.scenario == scen)]
                g = d.groupby("strategy")[met].agg(["mean", "std"]).reindex(strategies)
                off = (k - 1.5) * 0.17
                ax.errorbar(x + off, g["mean"], yerr=g["std"], fmt=lm_style[lm]["marker"], color=lm_style[lm]["color"],
                            ms=3.2, lw=0.8, capsize=1.5, label=LMAX_TEX[lm])
            ax.set_xticks(x); ax.set_xticklabels([ps.STRAT_SHORT[s] for s in strategies], rotation=40, ha="right")
            if i < len(rows) - 1:
                ax.tick_params(labelbottom=False)
            if i == 0:
                ax.set_title(f"Rule {rule[1]}", pad=16)
            if j == 0:
                ax.text(0.0, 1.03, f"({chr(97 + i)}) {labels[(scen, met)]}", transform=ax.transAxes, ha="left",
                        va="bottom", fontsize=7.2, color="#0b0b0b")
            ax.set_ylim(0, 1)
    h, l = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, bbox_to_anchor=(0.5, 1.0), title=r"$\ell_{max}$")
    save(fig, name)


# ---------------------------------------------------------------- distribuciones de grado
def _degree_pk(rule, strat, lmax, cycle, bins):
    """P(k) promedio sobre ejecuciones, en bins logarítmicos (densidad por unidad de k)."""
    pk = []
    for run in range(1, 11):
        f = os.path.join(RESULTS_DIR, "degrees", f"{rule}_{strat}_{lmax}_{run}.npz")
        if not os.path.exists(f):
            continue
        z = np.load(f)
        cyc = list(z["cycles"])
        if cycle not in cyc:
            continue
        deg = z["degrees"][cyc.index(cycle)]
        h, _ = np.histogram(deg, bins=bins)
        pk.append(h / len(deg) / np.diff(bins))
    if not pk:
        return None
    pk = np.array(pk)
    return pk.mean(0), pk.std(0)


def fig_degree_distributions(lmax="D2", cycle=MAX_CYCLE, name="degree_distributions", strategies=ps.STRATEGIES):
    bins = np.unique(np.round(np.logspace(np.log10(3), np.log10(2600), 28)).astype(int))
    centers = np.sqrt(bins[:-1] * bins[1:])
    fig, axes = plt.subplots(1, len(RULES), figsize=(5.15, 2.2), sharey=True, constrained_layout=True)
    for j, rule in enumerate(RULES):
        ax = axes[j]
        for s in strategies:
            r = _degree_pk(rule, s, lmax, cycle, bins)
            if r is None:
                continue
            m, sd = r
            ok = m > 0
            st = ps.STYLE[s]
            ax.plot(centers[ok], m[ok], color=st["color"], ls=st["ls"], marker=st["marker"], ms=2.8, lw=1,
                    label=ps.STRAT_SHORT[s])
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_title(f"Rule {rule[1]}")
        ax.set_xlabel("degree $k$")
        if j == 0:
            ax.set_ylabel("$P(k)$")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, bbox_to_anchor=(0.5, 1.0))
    save(fig, name)


def fig_degree_evolution(rule="R1", lmax="D2", name="degree_evolution", strategies=("RWI", "RW", "RWD", "N2Vp1q2")):
    bins = np.unique(np.round(np.logspace(np.log10(3), np.log10(2600), 28)).astype(int))
    centers = np.sqrt(bins[:-1] * bins[1:])
    cycles = [1, 5, 10, 20, 30]
    cmap = ps.SEQ_BLUE
    fig, axes = plt.subplots(1, len(strategies), figsize=(5.15, 1.9), sharex=True, sharey=True, constrained_layout=True)
    for j, s in enumerate(strategies):
        ax = axes[j]
        for i, c in enumerate(cycles):
            r = _degree_pk(rule, s, lmax, c, bins)
            if r is None:
                continue
            m, _ = r
            ok = m > 0
            ax.plot(centers[ok], m[ok], color=cmap(0.25 + 0.75 * i / (len(cycles) - 1)), lw=1, marker="o", ms=2.2,
                    label=f"cycle {c}")
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_title(ps.STRAT_SHORT[s])
        ax.set_xlabel("degree $k$")
        if j == 0:
            ax.set_ylabel("$P(k)$")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=5, bbox_to_anchor=(0.5, 1.0))
    save(fig, name)
