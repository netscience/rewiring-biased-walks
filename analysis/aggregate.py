"""Agrega las métricas por configuración (regla, estrategia, lmax) y ciclo,
y calcula indicadores de convergencia por corrida.

Salidas (results/):
  metrics_mean.csv        media y desviación estándar sobre ejecuciones, por configuración y ciclo
  final_state.csv         media ± sd en el ciclo 30 por configuración (una fila por configuración)
  convergence.csv         ciclo de convergencia de la serie promedio, por configuración, métrica y tolerancia
  n2v_ratio_symmetry.csv  comparación de pares node2vec con el mismo cociente q/p
"""
import os

import numpy as np
import pandas as pd

from config import MAX_CYCLE, RESULTS_DIR
from metrics import METRIC_COLUMNS

KEYS = ["rule", "strategy", "family", "p", "q", "lmax"]
CONV_METRICS = ["diameter", "aspl", "efficiency", "clustering", "H_norm", "k_max", "k_gini",
                "modularity", "n_communities", "assortativity", "dyn_len_mean", "frac_rewired"]
TOLERANCES = [0.05, 0.10]


def load():
    m = pd.read_csv(os.path.join(RESULTS_DIR, "metrics_per_cycle.csv"))
    a = pd.read_csv(os.path.join(RESULTS_DIR, "rewiring_activity.csv"))
    df = m.merge(a[["rule", "strategy", "lmax", "run", "cycle", "n_rewired", "frac_rewired"]],
                 on=["rule", "strategy", "lmax", "run", "cycle"], how="left")
    return df


def convergence_cycle(mean_series, sd_final, n_runs, tol):
    """Ciclo de convergencia de la serie promedio (sobre ejecuciones) de una métrica.

    Es el primer ciclo a partir del cual la serie permanece dentro de una banda
    alrededor de su valor final (ciclo 30). La anchura de la banda es
    max(tol * rango, SE_final), donde rango = max - min de la serie en los ciclos
    0..30 (hace comparable el criterio entre métricas de distinta escala) y
    SE_final = sd_final / sqrt(n_runs) es un piso de ruido para métricas casi
    constantes. Un valor cercano a 30 indica que la métrica aún cambia al final.
    """
    x = np.asarray(mean_series, dtype=float)
    final = x[-1]
    rng = np.nanmax(x) - np.nanmin(x)
    if not np.isfinite(rng) or rng == 0:
        return 0
    band = max(tol * rng, (sd_final if np.isfinite(sd_final) else 0.0) / np.sqrt(max(n_runs, 1)))
    bad = np.where(~(np.abs(x - final) <= band))[0]
    return int(bad[-1] + 1) if len(bad) else 0


def main():
    df = load()
    df = df.sort_values(KEYS + ["run", "cycle"])
    values = METRIC_COLUMNS + ["n_rewired", "frac_rewired"]

    g = df.groupby(KEYS + ["cycle"], dropna=False)[values]
    mean = g.mean().add_suffix("_mean")
    std = g.std(ddof=1).add_suffix("_sd")
    nrun = df.groupby(KEYS + ["cycle"], dropna=False)["run"].nunique().rename("n_runs")
    agg = pd.concat([mean, std, nrun], axis=1).reset_index()
    agg.to_csv(os.path.join(RESULTS_DIR, "metrics_mean.csv"), index=False)

    final = agg[agg.cycle == MAX_CYCLE].drop(columns="cycle")
    final.to_csv(os.path.join(RESULTS_DIR, "final_state.csv"), index=False)

    rows = []
    for key, grp in agg.groupby(KEYS, dropna=False):
        grp = grp.set_index("cycle").reindex(range(MAX_CYCLE + 1))
        n_runs = int(grp["n_runs"].max())
        for met in CONV_METRICS:
            for tol in TOLERANCES:
                rows.append(dict(zip(KEYS, key), metric=met, tol=tol, n_runs=n_runs,
                                 final_mean=grp[met + "_mean"].iloc[-1], final_sd=grp[met + "_sd"].iloc[-1],
                                 range=float(np.nanmax(grp[met + "_mean"]) - np.nanmin(grp[met + "_mean"])),
                                 conv_cycle=convergence_cycle(grp[met + "_mean"].values,
                                                              grp[met + "_sd"].iloc[-1], n_runs, tol)))
    conv = pd.DataFrame(rows)
    conv.to_csv(os.path.join(RESULTS_DIR, "convergence.csv"), index=False)

    # Simetría q/p en node2vec: pares (p,q) con el mismo cociente q/p.
    n2v = final[final.family == "N2V"].copy()
    n2v["ratio"] = (n2v.q / n2v.p).round(4)
    sym = []
    for (rule, lmax, ratio), grp in n2v.groupby(["rule", "lmax", "ratio"]):
        if len(grp) < 2:
            continue
        for met in ["diameter", "clustering", "H_norm", "k_max", "modularity", "assortativity"]:
            vals = grp[met + "_mean"].values
            sds = grp[met + "_sd"].values
            sym.append(dict(rule=rule, lmax=lmax, ratio=ratio, metric=met, n_pairs=len(grp),
                            spread=float(vals.max() - vals.min()),
                            mean_sd=float(np.nanmean(sds)),
                            spread_over_sd=float((vals.max() - vals.min()) / max(np.nanmean(sds), 1e-12)),
                            configs=";".join(f"p{p:g}q{q:g}" for p, q in zip(grp.p, grp.q))))
    pd.DataFrame(sym).to_csv(os.path.join(RESULTS_DIR, "n2v_ratio_symmetry.csv"), index=False)

    # Efecto de p (a q fija) y de q (a p fija) sobre el estado final, en unidades de la
    # desviación estándar entre ejecuciones.
    eff = []
    for met in ["diameter", "aspl", "clustering", "H_norm", "k_max", "k_gini", "modularity",
                "assortativity", "dyn_len_mean", "frac_rewired"]:
        for (rule, lmax), grp in n2v.groupby(["rule", "lmax"]):
            sd = max(grp[met + "_sd"].mean(), 1e-12)
            ep = np.mean([g[met + "_mean"].max() - g[met + "_mean"].min() for _, g in grp.groupby("q")])
            eq = np.mean([g[met + "_mean"].max() - g[met + "_mean"].min() for _, g in grp.groupby("p")])
            eff.append(dict(metric=met, rule=rule, lmax=lmax, run_sd=sd, effect_p=ep, effect_q=eq,
                            effect_p_over_sd=ep / sd, effect_q_over_sd=eq / sd))
    pd.DataFrame(eff).to_csv(os.path.join(RESULTS_DIR, "n2v_pq_effects.csv"), index=False)
    print("agregación lista:", len(agg), "filas de medias;", len(final), "configuraciones")


if __name__ == "__main__":
    main()
