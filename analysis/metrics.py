"""Métricas estructurales de una red (igraph)."""
import math

import numpy as np

from config import N_NODES, node_xy
from loader import FIXED_EDGE_SET

_XY = np.array([node_xy(i) for i in range(1, N_NODES + 1)], dtype=float)
_H_MAX = math.log2(N_NODES - 1)  # entropía máxima (grafo completo), como en Lopez-Chavira et al. 2024


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    if x.sum() == 0:
        return 0.0
    return (2 * np.sum(np.arange(1, n + 1) * x) / (n * x.sum())) - (n + 1) / n


def degree_entropy(deg):
    """Entropía de Shannon normalizada de la distribución de grado (Eq. 3 del
    artículo de Sci. Rep.), H / H_max con H_max = log2(n-1)."""
    counts = np.bincount(deg)
    p = counts[counts > 0] / len(deg)
    return float(-(p * np.log2(p)).sum() / _H_MAX)


def compute_metrics(g, edges, lmax_value, seed=0):
    """Calcula todas las métricas de la red g (igraph.Graph) construida con `edges`.

    lmax_value: longitud máxima permitida para los enlaces dinámicos (en unidades
    de la malla), para expresar la longitud usada como fracción del presupuesto.
    """
    out = {}
    deg = np.array(g.degree())
    out["n_edges"] = g.ecount()
    out["k_max"] = int(deg.max())
    out["k_std"] = float(deg.std())
    out["k_gini"] = float(gini(deg))
    out["H_norm"] = degree_entropy(deg)
    out["assortativity"] = float(g.assortativity_degree(directed=False))
    out["clustering"] = float(g.transitivity_avglocal_undirected(mode="zero"))
    out["transitivity"] = float(g.transitivity_undirected())

    # Distancias: diámetro, longitud promedio de camino, eficiencia global,
    # a partir del histograma de longitudes de camino (calculado en C por igraph).
    comps = g.connected_components()
    out["n_components"] = len(comps)
    h = g.path_length_hist(directed=False)
    bins = list(h.bins())
    lens = np.array([b[0] for b in bins], dtype=float)
    cnt = np.array([b[2] for b in bins], dtype=float)
    n_pairs = N_NODES * (N_NODES - 1) / 2
    out["diameter"] = int(lens[cnt > 0].max())
    out["aspl"] = float((lens * cnt).sum() / cnt.sum())
    out["efficiency"] = float((cnt / lens).sum() / n_pairs)

    # Comunidades (Louvain / multilevel).
    import random
    random.seed(seed)
    part = g.community_multilevel()
    out["n_communities"] = len(part)
    out["modularity"] = float(part.modularity)
    memb = np.array(part.membership)
    es = np.array(g.get_edgelist())
    cut = memb[es[:, 0]] != memb[es[:, 1]]
    out["edge_cut_ratio"] = float(cut.mean())

    # Métricas espaciales de los enlaces dinámicos.
    dyn = np.array([e for e in edges if frozenset(e) not in FIXED_EDGE_SET])
    out["n_dynamic"] = len(dyn)
    if len(dyn):
        L = np.hypot(*(_XY[dyn[:, 0]] - _XY[dyn[:, 1]]).T)
        out["dyn_len_mean"] = float(L.mean())
        out["dyn_len_max"] = float(L.max())
        out["dyn_len_frac_lmax"] = float(L.mean() / lmax_value)
        # Concentración de los enlaces dinámicos en el 1% de nodos de mayor grado.
        top = np.argsort(deg)[-max(1, N_NODES // 100):]
        top_set = np.zeros(N_NODES, bool); top_set[top] = True
        out["dyn_frac_top1pct"] = float((top_set[dyn[:, 0]] | top_set[dyn[:, 1]]).mean())
    else:
        for k in ("dyn_len_mean", "dyn_len_max", "dyn_len_frac_lmax", "dyn_frac_top1pct"):
            out[k] = math.nan
    return out


METRIC_COLUMNS = [
    "n_edges", "k_max", "k_std", "k_gini", "H_norm", "assortativity", "clustering",
    "transitivity", "n_components", "diameter", "aspl", "efficiency", "n_communities",
    "modularity", "edge_cut_ratio", "n_dynamic", "dyn_len_mean", "dyn_len_max",
    "dyn_len_frac_lmax", "dyn_frac_top1pct",
]
