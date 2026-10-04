"""Corridas de verificacion de las estrategias informadas (SP, CR) con la version actual del simulador:
R1, lmax = D/2, configuracion de referencia (umbral c/2, horizonte adaptativo), 5 ejecuciones de 30 ciclos.
Sirven para comprobar que las corridas de SP y CR heredadas del simposio coinciden con el simulador actual.

Uso (desde esta carpeta):  python run_informed.py --workers 8
Las corridas ya terminadas se omiten, asi que se puede interrumpir y relanzar.
Resultados en ./simruns/base/R1/<SP|CR>/D2/<ejecucion>/  (misma carpeta que los controles)
"""
import argparse, os, shutil, subprocess, sys, time
from multiprocessing import Pool

SIM = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SIM, "simruns")
FILES = ["main.py", "complexNetwork.py", "encaminamiento.py", "enlace.py", "event.py", "model.py", "paquete.py",
         "process.py", "reglas.py", "simulation.py", "simulator.py", "tamEnlace.py", "extractData.py"]
STRATS = {"SP": ("SHORTEST-PATH", 1, 1), "CR": ("COMPASS-ROUTING", 1, 1)}
VARIANTS = {"base": dict(UMBRAL_R1=0.5, HORIZONTE=None)}
RUNS = 5; CYCLES = 30

def job(args):
    variant, strat, run = args
    routing, p, q = STRATS[strat]
    d = os.path.join(OUT, variant, "R1", strat, "D2", str(run))
    if os.path.exists(os.path.join(d, f"datos-salida_{run}.txt")):
        return f"{variant}/{strat}/{run} ya existia"
    os.makedirs(d, exist_ok=True)
    for f in FILES:
        shutil.copy(os.path.join(SIM, f), d)
    cfg = dict(NODOS_ANILLO=0, ROWS=50, COLUMNS=50, RED=1, ROUTING=routing, P=p, Q=q, REGLA=1, ALPHA=0.3,
               VECTOR_POPULARIDAD=[1,1,0,1,0,1,1,1], VECTOR_DISTANCIA=[0,1,0,1,1,0,1,1], LONG_ENLACE=2,
               CICLOS=CYCLES, ENLACES_DINAMICOS=2, EXPLORADORES=20, DIV_CONEXIONES=1, **VARIANTS[variant])
    with open(os.path.join(d, "config.py"), "w") as f:
        for k, v in cfg.items():
            f.write(f"{k} = {v!r}\n")
    t = time.time()
    with open(os.path.join(d, f"salida_{run}.txt"), "w") as out:
        subprocess.run([sys.executable, "main.py", "log.txt"], cwd=d, stdout=out, stderr=subprocess.DEVNULL)
    subprocess.run([sys.executable, "extractData.py", f"salida_{run}.txt", "test"], cwd=d, stdout=subprocess.DEVNULL)
    return f"{variant}/{strat}/{run} {time.time()-t:.0f}s"

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=max(1, os.cpu_count() - 2))
    a = ap.parse_args()
    jobs = [(v, s, r) for v in ["base"] for r in range(1, RUNS + 1) for s in STRATS]
    print(f"{len(jobs)} corridas con {a.workers} procesos", flush=True)
    with Pool(a.workers) as pool:
        for msg in pool.imap_unordered(job, jobs):
            print(msg, flush=True)
    print("listo", flush=True)
