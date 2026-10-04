"""Carga de redes y de logs de recableado."""
import os
import re

import igraph as ig

from config import CYCLES, GRID, N_NODES, node_xy

_CYCLE_RE = re.compile(r"graph_test_(\d+)\.adjlist$")


def grid_edges():
    """Enlaces fijos de la malla 50x50 (0-indexados)."""
    edges = []
    for i in range(1, N_NODES + 1):
        c, r = node_xy(i)
        if c < GRID - 1:
            edges.append((i - 1, i))          # vecino a la derecha
        if r < GRID - 1:
            edges.append((i - 1, i - 1 + GRID))  # vecino de abajo
    return edges


FIXED_EDGE_SET = frozenset(frozenset(e) for e in grid_edges())


def read_adjlist_edges(path):
    """Lee un adjlist de NetworkX y devuelve el conjunto de aristas (0-indexadas)."""
    edges = set()
    with open(path) as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            toks = line.split()
            if len(toks) < 2:
                continue
            u = int(toks[0]) - 1
            for t in toks[1:]:
                v = int(t) - 1
                if u != v:
                    edges.add((u, v) if u < v else (v, u))
    return edges


def edges_to_graph(edges):
    g = ig.Graph(n=N_NODES, edges=list(edges), directed=False)
    return g


def available_cycles(run_dir):
    cyc = {}
    for f in os.listdir(run_dir):
        m = _CYCLE_RE.match(f)
        if m:
            cyc[int(m.group(1))] = os.path.join(run_dir, f)
    return cyc


def iter_cycle_edges(run_dir, cycles=CYCLES):
    """Genera (ciclo, aristas, es_copia) para cada ciclo solicitado.

    Si no existe archivo para un ciclo (el simulador no registró recableados en
    ese ciclo), se reutiliza la red del último ciclo disponible (es_copia=True).
    """
    files = available_cycles(run_dir)
    last = None
    for c in cycles:
        if c in files:
            last = read_adjlist_edges(files[c])
            yield c, last, False
        elif last is not None:
            yield c, last, True
        else:
            raise FileNotFoundError(f"sin red inicial en {run_dir}")


def read_rewiring_log(run_dir):
    """Lee salida_<run>.txt y devuelve {ciclo: n_eventos_de_recableado}.

    Formato: 'c nodo -1 destino 1' (asignación inicial de enlaces dinámicos) y
    'r nodo viejo nuevo ciclo' (recableado del enlace dinámico nodo-viejo a
    nodo-nuevo en el ciclo indicado).
    """
    logs = [f for f in os.listdir(run_dir) if f.startswith("salida_") and f.endswith(".txt")]
    if not logs:
        return {}
    counts = {}
    with open(os.path.join(run_dir, logs[0])) as fh:
        for line in fh:
            if line.startswith("r "):
                toks = line.split()
                c = int(toks[4])
                counts[c] = counts.get(c, 0) + 1
    return counts
