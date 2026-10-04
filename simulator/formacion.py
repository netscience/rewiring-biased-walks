import subprocess
from pathlib import Path
import os
import shutil
import configuracion
from multiprocessing import Pool

PYTHON_EXEC = "python"  # Si tu entorno ya responde a 'python'

def generar_script_constantes(nombre_archivo, long_enlace, regla, tipo_red, ruteo, p, q, alpha, vect_popularidad, vect_distancia):
    constantes = {
        #--------ANILLO------------------
        # Número de nodos del anillo. Colocar 0 si no se usa anillo
        "NODOS_ANILLO": configuracion.NODOS_ANILLO, 
        #--------MALLA-------------------
        # Filas de la malla. Colocar 0 si no se usa malla
        "ROWS": configuracion.ROWS,
        # Columnas de la malla                  
        "COLUMNS": configuracion.COLUMNS,           
        #--------FORMACION-------------
        # Topología sobre la que se desarrollará la simulación: 1 -> "malla" o 3->"anillo"
        "RED": tipo_red,                           
        # Algoritmo de encaminamiento: "CR", "RW", "SP"
        "ROUTING": ruteo, 
        "P": p,
        "Q": q,
        "REGLA": regla,
        "ALPHA": alpha,
        "VECTOR_POPULARIDAD": vect_popularidad,
        "VECTOR_DISTANCIA": vect_distancia,
        # Divisor de la longitud de enlace dinámico: 1, 2, 4, 8, 16, 32 
        "LONG_ENLACE": long_enlace,        
        #--------EJECUCION---------------
        # Número de ciclos de formación
        "CICLOS": configuracion.CICLOS,                    
        #--------EXTRAS------------------
        # Número de enlaces dinámicos por nodo
        "ENLACES_DINAMICOS": configuracion.ENLACES_DINAMICOS,       
        # Número de experimentos a realizar
        "EXPLORADORES": configuracion.EXPLORADORES,
        # Divisor (con respecto al número de nodos, num_nodos/DIV_CONEXIONES) del máximo número de conexiones permitidas
        "DIV_CONEXIONES": configuracion.DIV_CONEXIONES         
    }

    with open(nombre_archivo, 'w') as f:
        f.write("# Archivo de constantes generado automáticamente\n\n")
        for nombre, valor in constantes.items():
            if isinstance(valor, str):
                f.write(f'{nombre} = "{valor}"\n')
            else:
                f.write(f"{nombre} = {valor}\n")
    print(f"Archivo '{nombre_archivo}' generado con {len(constantes)} constantes.")


def ejecutar_configuracion(args):
    ruta, long_enlace, r, tipo_red, ruteo, p, q, alpha, vect_popularidad, vect_distancia = args
    print(f"\n>>> Iniciando configuración en: {ruta}")
    
    # Crea config.py en la ruta
    generar_script_constantes(str(ruta) + "/config.py", long_enlace, r, tipo_red, ruteo, p ,q, alpha, vect_popularidad, vect_distancia)

    for x in range(1, configuracion.EJECUCIONES + 1):
        hoja = f"{ruta}/{x}"
        os.makedirs(hoja, exist_ok=True)

        print(f" - Simulación {x} en: {hoja}")

        salida_txt = f"{hoja}/salida_{x}.txt"
        # Creo el archivo log
        log_file = f"{hoja}/log_{x}.txt"
        with open(log_file, "w", encoding="utf-8") as logfile:
            logfile.write(f"Log de la ejecución {x} en {ruta}\n")
        
        # Ejecuta main.py desde la carpeta CR
        with open(salida_txt, "w") as out_f:
            subprocess.run([PYTHON_EXEC, "main.py", log_file], cwd=ruta, stdout=out_f)

        # Copia archivos auxiliares
        for archivo in ["extractData.py", "graph.adjlist"]:
            src = f"{ruta}/{archivo}"
            dest = f"{hoja}/{archivo}"
            if os.path.exists(src):
                shutil.copy(src, dest)
            else:
                print(f" No se encontró: {archivo} en {ruta}")

        # Ejecuta extractData.py desde la hoja
        if os.path.exists(hoja + "/extractData.py"):
            subprocess.run([PYTHON_EXEC, "extractData.py", f"salida_{x}.txt", "test"], cwd=hoja)
        else:
            print(" No se puede extraer: falta extractData.py")
            
    print(f"<<< Finalizada configuración en: {ruta}")


if __name__ == '__main__':
    tasks = []
    
    for red in configuracion.RED:
        if red == "anillo":
            nombre_red = "anillo" + str(configuracion.NODOS_ANILLO)
            tipo_red = 3
        elif red == "malla":
            nombre_red = f"malla{configuracion.ROWS}x{configuracion.COLUMNS}"
            tipo_red = 1    
        else:
            print(f" Tipo de red desconocido, saltando: {red}")
            continue   
        
        for r in configuracion.REGLAS:
            routing = "x"
            for ruteo in configuracion.ROUTING:
                if ruteo == "COMPASS-ROUTING":
                    routing = "CR"
                elif ruteo == "RANDOM-WALK":
                    routing = "RW" 
                elif ruteo == "RW-DEGREE":
                    routing = "RWD"
                elif ruteo == "RW-INVERSE":
                    routing = "RWI" 
                elif ruteo == "RW-NODE2VEC":
                    routing = "N2V"
                elif ruteo == "SHORTEST-PATH":
                    routing = "SP"
                else:
                    print(f" Algoritmo de ruteo desconocido, saltando: {ruteo}")
                    continue
                
                for long_enlace in configuracion.LONG_ENLACES:
                    if ruteo == "RW-NODE2VEC":
                        for pq in configuracion.PQ_NODE2VEC:
                            p = pq[0]
                            q = pq[1]
                            pstr = str(p).replace('.',"_")
                            qstr = str(q).replace('.',"_")
                            ruta = f"{configuracion.RESULTADOS_DIR}/{nombre_red}/R{r}/{routing}p{pstr}q{qstr}/D{long_enlace}"
                        
                            if not os.path.exists(ruta):
                                print(f" Ruta no encontrada, saltando: {ruta}")
                                continue
                            if r==4:
                                tasks.append((ruta, long_enlace, r, tipo_red, ruteo, p, q, configuracion.ALPHA, configuracion.VECTOR_POPULARIDAD, configuracion.VECTOR_DISTANCIA))
                            else:
                                tasks.append((ruta, long_enlace, r, tipo_red, ruteo, p, q, 0, 0, 0))
                    else:
                        ruta = f"{configuracion.RESULTADOS_DIR}/{nombre_red}/R{r}/{routing}/D{long_enlace}"
                        
                        if not os.path.exists(ruta):
                            print(f" Ruta no encontrada, saltando: {ruta}")
                            continue
                        if r == 4:
                            tasks.append((ruta, long_enlace, r, tipo_red, ruteo, 0, 0, configuracion.ALPHA, configuracion.VECTOR_POPULARIDAD, configuracion.VECTOR_DISTANCIA))
                        else:
                            tasks.append((ruta, long_enlace, r, tipo_red, ruteo, 0, 0, 0, 0, 0))

    # Leer NUM_WORKERS configurado
    num_workers = getattr(configuracion, "NUM_WORKERS", 4)
    print(f"\nEjecutando {len(tasks)} configuraciones en paralelo usando {num_workers} workers...")
    
    with Pool(processes=num_workers) as pool:
        pool.map(ejecutar_configuracion, tasks)
        
    print("\n¡Simulaciones de formación completadas con éxito!")
