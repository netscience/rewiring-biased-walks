"""Estilo común de las figuras (matplotlib), pensado para el PDF del artículo."""
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

# Paleta categórica (orden fijo, apta para daltonismo); los marcadores actúan como
# codificación secundaria para impresión en escala de grises.
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*"]
LINESTYLES = ["-", "--", "-.", ":", "-", "--", "-.", ":"]

# Estrategias representativas y su orden/estilo fijo en todas las figuras.
STRATEGIES = ["SP", "CR", "RWI", "RW", "RWD", "N2Vp1q0_25", "N2Vp1q2"]
STRAT_LABEL = {
    "SP": "SP", "CR": "CR", "RW": "RW", "RWD": "RWD", "RWI": "RWI",
    "N2Vp1q0_25": "RWL($q$=0.25)",
    "N2Vp1q2": "RWL($q$=2)",
}
STRAT_SHORT = {
    "SP": "SP", "CR": "CR", "RW": "RW", "RWD": "RWD", "RWI": "RWI",
    "N2Vp1q0_25": "RWL$_{q=0.25}$", "N2Vp1q0_5": "RWL$_{q=0.5}$", "N2Vp1q1": "RWL$_{q=1}$", "N2Vp1q2": "RWL$_{q=2}$",
}
STYLE = {s: dict(color=CAT[i], marker=MARKERS[i], ls=LINESTYLES[i]) for i, s in enumerate(STRATEGIES)}
# Conjunto ampliado para figuras de estado final: RWL(q) (regla de transición de node2vec) con p = 1 y los
# cuatro valores de q; p no tiene efecto porque las caminatas son auto-evitantes (results/n2v_pq_effects.csv).
STRATEGIES_EXT = ["SP", "CR", "RWI", "RW", "RWD", "N2Vp1q0_25", "N2Vp1q0_5", "N2Vp1q1", "N2Vp1q2"]

# Rampa secuencial de un solo tono (azul) para heatmaps.
SEQ_BLUE = LinearSegmentedColormap.from_list(
    "seq_blue", ["#eef4fc", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"])
# Rampa divergente azul-gris-rojo para la asortatividad.
DIV_BR = LinearSegmentedColormap.from_list("div_br", ["#0d366b", "#2a78d6", "#f0efec", "#e34948", "#7a1b1b"])

METRIC_LABEL = {
    "diameter": "Diameter $d$",
    "aspl": r"Avg. shortest path $\langle d \rangle$",
    "efficiency": "Global efficiency $E$",
    "clustering": r"Avg. clustering $\langle C \rangle$",
    "H_norm": "Degree entropy $H/H_{max}$",
    "k_max": "Max. degree $k_{max}$",
    "k_gini": "Degree Gini",
    "assortativity": "Degree assortativity $r$",
    "modularity": "Modularity $M$",
    "n_communities": "Communities $n_C$",
    "edge_cut_ratio": "Edge cut ratio $E_C$",
    "dyn_len_mean": r"Mean dynamic link length $\langle \ell \rangle$",
    "dyn_len_frac_lmax": r"$\langle \ell \rangle / \ell_{max}$",
    "dyn_frac_top1pct": "Dynamic links at top-1% hubs",
    "frac_rewired": "Fraction of nodes rewiring",
    "transitivity": "Transitivity",
}


def apply():
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 8,
        "axes.titlesize": 8.5,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "axes.edgecolor": "#c3c2b7",
        "axes.linewidth": 0.6,
        "axes.grid": True,
        "grid.color": "#e1e0d9",
        "grid.linewidth": 0.5,
        "axes.axisbelow": True,
        "xtick.color": "#52514e",
        "ytick.color": "#52514e",
        "axes.labelcolor": "#0b0b0b",
        "lines.linewidth": 1.3,
        "lines.markersize": 3.5,
        "legend.frameon": False,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,
    })
