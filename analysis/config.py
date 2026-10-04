"""Configuración común del análisis estructural de las redes recableadas.

Estructura esperada de los datos:
    <NETS_DIR>/<regla>/<estrategia>/<lmax>/<ejecución>/graph_test_<ciclo>.adjlist
    <NETS_DIR>/<regla>/<estrategia>/<lmax>/<ejecución>/salida_<ejecución>.txt

Los nodos están etiquetados 1..2500 en orden por renglones sobre una malla
50x50: el nodo i ocupa la fila (i-1)//50 y la columna (i-1)%50.
"""
import math
import os
import re

NETS_DIR = os.environ.get("NETS_DIR", os.path.join(os.path.dirname(__file__), "..", "nets"))
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
FIG_DIR = os.path.join(os.path.dirname(__file__), "figures")

GRID = 50
N_NODES = GRID * GRID
N_FIXED_EDGES = 2 * GRID * (GRID - 1)        # 4900
N_DYNAMIC_EDGES = 2 * N_NODES                # 5000 (2 enlaces dinámicos por nodo)
D_MAX = math.hypot(GRID - 1, GRID - 1)       # diagonal de la malla, ~69.3

RULES = ["R1", "R2", "R3"]
LMAX_LABELS = ["D2", "D4", "D8", "D16"]      # D/2, D/4, D/8, D/16 (D/32 excluido)
LMAX_VALUES = {lab: D_MAX / int(lab[1:]) for lab in LMAX_LABELS}
LMAX_TEX = {"D2": r"$D/2$", "D4": r"$D/4$", "D8": r"$D/8$", "D16": r"$D/16$"}
N_RUNS = 10
MAX_CYCLE = 30
CYCLES = list(range(MAX_CYCLE + 1))

N2V_VALUES = [0.25, 0.5, 1, 2]
_N2V_RE = re.compile(r"^N2Vp([0-9_]+)q([0-9_]+)$")


def parse_strategy(name):
    """Devuelve (familia, p, q). familia in {CR, SP, RW, RWD, RWI, N2V}.
    El RW uniforme es equivalente a N2V con p = q = 1; se conserva como familia
    propia porque proviene de una corrida independiente."""
    m = _N2V_RE.match(name)
    if m:
        p = float(m.group(1).replace("_", "."))
        q = float(m.group(2).replace("_", "."))
        return "N2V", p, q
    return name, math.nan, math.nan


def strategy_label(name):
    fam, p, q = parse_strategy(name)
    if fam == "N2V":
        return f"N2V(p={p:g}, q={q:g})"
    return fam


def node_xy(i):
    """Coordenadas (x=columna, y=fila) del nodo i (1-indexado)."""
    r, c = divmod(i - 1, GRID)
    return c, r


def iter_runs(nets_dir=NETS_DIR):
    """Genera (regla, estrategia, lmax, ejecución, ruta) para todas las corridas."""
    for rule in RULES:
        rdir = os.path.join(nets_dir, rule)
        if not os.path.isdir(rdir):
            continue
        for strat in sorted(os.listdir(rdir)):
            sdir = os.path.join(rdir, strat)
            if not os.path.isdir(sdir):
                continue
            for lmax in LMAX_LABELS:
                ldir = os.path.join(sdir, lmax)
                if not os.path.isdir(ldir):
                    continue
                for run in sorted((d for d in os.listdir(ldir) if d.isdigit()), key=int):
                    yield rule, strat, lmax, int(run), os.path.join(ldir, run)
