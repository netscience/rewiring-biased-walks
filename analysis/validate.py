"""Compara clustering, diámetro y ASPL calculados con los datos-salida_*.txt del simulador."""
import os, glob
import numpy as np, pandas as pd
from config import NETS_DIR, iter_runs, MAX_CYCLE, RESULTS_DIR
m = pd.read_csv(os.path.join(RESULTS_DIR, "metrics_per_cycle.csv")).set_index(["rule","strategy","lmax","run","cycle"])
diffs = {"clustering":[], "diameter":[], "aspl":[]}; n=0; worst=[]
for rule, strat, lmax, run, d in iter_runs():
    fs = glob.glob(os.path.join(d, "datos-salida_*.txt"))
    if not fs: continue
    ref = pd.read_csv(fs[0], sep="\t", comment=None)
    ref.columns = [c.lstrip("#") for c in ref.columns]
    for _, r in ref.iterrows():
        c = int(r.cicle)
        if c > MAX_CYCLE: continue
        row = m.loc[(rule, strat, lmax, run, c)]
        for k, rk in [("clustering","avCl"),("diameter","diam"),("aspl","aspl")]:
            e = abs(row[k]-r[rk]); diffs[k].append(e)
            if e > 1e-4: worst.append((rule,strat,lmax,run,c,k,row[k],r[rk]))
        n += 1
print("redes comparadas:", n)
for k,v in diffs.items(): print(f"{k}: max |dif| = {max(v):.2e}, media = {np.mean(v):.2e}")
print("discrepancias > 1e-4:", len(worst)); print(worst[:10])
