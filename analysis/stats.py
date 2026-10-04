"""Inferencia estadística sobre los estados finales (ciclo 30).

1. Intervalos de confianza bootstrap (percentil, 95 %, 10 000 remuestreos) de la media sobre las
   10 corridas, para cada (regla, estrategia, lmax, métrica) -> results/final_state_ci.csv
2. Pruebas no paramétricas sobre las comparaciones afirmadas en el texto:
   - Kruskal-Wallis entre las siete estrategias principales, por (regla, lmax, métrica)
   - Mann-Whitney U (bilateral) entre pares RWI/RW, RW/RWD, RWL_{q=0.25}/RWL_{q=2} y RW/RWL_{q=2}
   - Kruskal-Wallis entre los cuatro valores de q (p=1) y entre los cuatro valores de p (q=1)
   Con corrección de Holm por métrica dentro de cada familia de pruebas -> results/final_state_tests.csv
Uso: python stats.py
"""
import os

import numpy as np
import pandas as pd
from scipy import stats

from config import MAX_CYCLE, RESULTS_DIR

METRICS = ["diameter", "clustering", "H_norm", "k_max", "modularity", "frac_rewired",
           "dyn_len_frac_lmax", "assortativity", "k_gini", "efficiency"]
MAIN = ["SP", "CR", "RWI", "RW", "RWD", "N2Vp1q0_25", "N2Vp1q2"]
PAIRS = [("RWI", "RW"), ("RW", "RWD"), ("N2Vp1q0_25", "N2Vp1q2"), ("RW", "N2Vp1q2"), ("RW", "N2Vp1q1")]
B = 10_000


def boot_ci(x, rng):
    x = np.asarray(x, float)
    idx = rng.integers(0, len(x), size=(B, len(x)))
    means = x[idx].mean(axis=1)
    return np.percentile(means, [2.5, 97.5])


def kw(groups):
    """Kruskal-Wallis con guardia para el caso degenerado (todos los valores iguales)."""
    allv = np.concatenate(groups)
    if np.allclose(allv, allv[0]):
        return 0.0, 1.0
    return stats.kruskal(*groups)


def holm(pvals):
    p = np.asarray(pvals, float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p[i])
        adj[i] = min(1.0, running)
    return adj


def main():
    df = pd.read_csv(os.path.join(RESULTS_DIR, "metrics_per_cycle.csv"))
    act = pd.read_csv(os.path.join(RESULTS_DIR, "rewiring_activity.csv"))
    fin = df[df.cycle == MAX_CYCLE].copy()
    if "frac_rewired" not in fin.columns:
        a = act[act.cycle == MAX_CYCLE][["rule", "strategy", "lmax", "run", "frac_rewired"]]
        fin = fin.merge(a, on=["rule", "strategy", "lmax", "run"], how="left")
    rng = np.random.default_rng(2026)

    # 1. bootstrap CIs
    rows = []
    for (rule, strat, lmax), g in fin.groupby(["rule", "strategy", "lmax"]):
        for m in METRICS:
            x = g[m].dropna().values
            if len(x) < 2:
                continue
            lo, hi = boot_ci(x, rng)
            rows.append(dict(rule=rule, strategy=strat, lmax=lmax, metric=m, n=len(x),
                             mean=x.mean(), sd=x.std(ddof=1), ci_lo=lo, ci_hi=hi))
    ci = pd.DataFrame(rows)
    ci.to_csv(os.path.join(RESULTS_DIR, "final_state_ci.csv"), index=False)

    # 2. tests
    trows = []
    for (rule, lmax), g in fin.groupby(["rule", "lmax"]):
        for m in METRICS:
            groups = [g[g.strategy == s][m].dropna().values for s in MAIN]
            if min(len(x) for x in groups) < 3:
                continue
            H, p = kw(groups)
            trows.append(dict(rule=rule, lmax=lmax, metric=m, test="KW_strategies", a="7 main", b="",
                              stat=H, p=p))
            for a, b in PAIRS:
                xa, xb = g[g.strategy == a][m].dropna().values, g[g.strategy == b][m].dropna().values
                if len(xa) < 3 or len(xb) < 3:
                    continue
                if np.allclose(xa, xa[0]) and np.allclose(xb, xb[0]) and np.isclose(xa[0], xb[0]):
                    U, p = np.nan, 1.0
                else:
                    U, p = stats.mannwhitneyu(xa, xb, alternative="two-sided")
                d = (xb.mean() - xa.mean()) / np.sqrt((xa.var(ddof=1) + xb.var(ddof=1)) / 2) if (xa.var() + xb.var()) > 0 else np.nan
                trows.append(dict(rule=rule, lmax=lmax, metric=m, test="MWU", a=a, b=b, stat=U, p=p,
                                  mean_a=xa.mean(), mean_b=xb.mean(), cohen_d=d))
            qg = [g[g.strategy == f"N2Vp1q{q}"][m].dropna().values for q in ["0_25", "0_5", "1", "2"]]
            pg = [g[g.strategy == f"N2Vp{p_}q1"][m].dropna().values for p_ in ["0_25", "0_5", "1", "2"]]
            if min(len(x) for x in qg) >= 3:
                H, p = kw(qg)
                trows.append(dict(rule=rule, lmax=lmax, metric=m, test="KW_q", a="q in {0.25,0.5,1,2}", b="p=1", stat=H, p=p))
            if min(len(x) for x in pg) >= 3:
                H, p = kw(pg)
                trows.append(dict(rule=rule, lmax=lmax, metric=m, test="KW_p", a="p in {0.25,0.5,1,2}", b="q=1", stat=H, p=p))
    tests = pd.DataFrame(trows)
    tests["p_holm"] = np.nan
    for (rule, lmax, test, a, b), idx in tests.groupby(["rule", "lmax", "test", "a", "b"]).groups.items():
        tests.loc[idx, "p_holm"] = holm(tests.loc[idx, "p"].values)
    tests.to_csv(os.path.join(RESULTS_DIR, "final_state_tests.csv"), index=False)

    # resumen para el texto
    pd.set_option("display.width", 200)
    print("== KW entre 7 estrategias, p_holm max por regla ==")
    print(tests[tests.test == "KW_strategies"].groupby("rule").p_holm.max())
    print("== MWU pares: fracción de (lmax, métrica) con p_holm < 0.05 por regla y par ==")
    mw = tests[tests.test == "MWU"]
    print(mw.assign(sig=mw.p_holm < 0.05).groupby(["rule", "a", "b"]).sig.mean().unstack(0))
    print("== KW q (p=1): fracción significativa por regla ==")
    kq = tests[tests.test == "KW_q"]
    print(kq.assign(sig=kq.p_holm < 0.05).groupby("rule").sig.mean())
    print(kq[kq.rule != "R1"].sort_values("p_holm").head(8)[["rule", "lmax", "metric", "stat", "p", "p_holm"]])
    print("== KW p (q=1): fracción significativa por regla, y mínimo p_holm ==")
    kp = tests[tests.test == "KW_p"]
    print(kp.assign(sig=kp.p_holm < 0.05).groupby("rule").sig.agg(["mean", "sum", "size"]))
    print(kp.sort_values("p_holm").head(5)[["rule", "lmax", "metric", "stat", "p", "p_holm"]])
    print("== pares RWI/RW y RW/RWD en D2 para k_max, H_norm, clustering ==")
    print(mw[(mw.lmax == "D2") & mw.metric.isin(["k_max", "H_norm", "clustering", "diameter"])][
        ["rule", "metric", "a", "b", "mean_a", "mean_b", "p", "p_holm", "cohen_d"]].to_string())


if __name__ == "__main__":
    main()
