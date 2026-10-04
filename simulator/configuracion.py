from pathlib import Path

#Configuración de una serie de experimentos de formación de redes
#--------- Directorios para guardar resultados -----------
home_path = Path.home()
BASE_DIR = str(home_path) + "/Repositorios/ResultadosCN/"
RESULTADOS_DIR = BASE_DIR + "Formacion"
#-------- Red inicial: Anillo ------------------
NODOS_ANILLO=64             # Número de nodos del anillo. Colocar 0 si no se usa anillo
#-------- Red inicial: Malla -------------------
ROWS=8                      # Filas de la malla. Colocar 0 si no se usa malla
COLUMNS=8                   # Columnas de la malla
#-------- Configuración de los experimentos de Reconexión -------------
# Estos parámetros se deben definir como lista aunque contengan un solo valor
RED=["malla"]  # Tipo de red: "malla", "anillo"
# Algoritmo de ruteo: "SHORTEST-PATH", "COMPASS-ROUTING", "RANDOM-WALK", "RW-DEGREE", "RW-INVERSE", "RW-NODE2VEC"
ROUTING=["RANDOM-WALK"]               
# Parámetros para Node2Vec
PQ_NODE2VEC = [
    (0.25,0.25), (0.25,0.5), (0.25,1), (0.25,2),
    (0.5,0.25), (0.5,0.5), (0.5,1), (0.5,2),
    (1,0.25), (1,0.5), (1,1), (1,2),
    (2,0.25), (2,0.5), (2,1), (2,2)
    ]

# Reglas de reconexión
REGLAS=[1,2,3,4] #1,2,3,4
# Parámetros de R4
ALPHA = 0.3 # Balancea la popularidad y la distancia
# Ambos vectores deben ser de igual longitud
VECTOR_POPULARIDAD = [1,1,0,1,0,1,1,1]
VECTOR_DISTANCIA = [0,1,0,1,1,0,1,1]


# Divisor de la longitud de enlace dinámico.
# Se recomendan valores que sean potencia de 2, 
# p.e., 1, 2, 4, 8, 16, etc. 
LONG_ENLACES=[2]             
#--------EJECUCION---------------
CICLOS=5                   # Número de ciclos de reconexión
EJECUCIONES = 2            # Número de ejecuciones por experimento   
#--------EXTRAS------------------
ENLACES_DINAMICOS=2        # Número de enlaces dinámicos por nodo
EXPLORADORES=4             # Número de paquetes exploradores por ciclo
# Divisor del máximo número de conexiones permitidas 
# máximo numero de conexiones permitidas=num_nodos/DIV_CONEXIONES
DIV_CONEXIONES=1            
#--------PARALELISMO--------------
# Número de procesos paralelos para ejecutar simulaciones
# Ajustar según el número de cores de la CPU
NUM_WORKERS=8