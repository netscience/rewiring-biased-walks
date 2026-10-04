# Cambios respecto a github.com/netscience/rewiring (para la version extendida)

Todos son retrocompatibles: sin los parametros nuevos el simulador se comporta exactamente igual.

* `complexNetwork.py`
  - `HORIZONTE` (config, opcional): si es un entero, los exploradores usan ese numero fijo de saltos en
    lugar de `randint(2, diametro)`. Si no se define, comportamiento original.
  - `UMBRAL_R1` (config, opcional, por omision 0.5): fraccion de exploradores que deben haber visitado al
    candidato para que R1 lo acepte (`frecNodo = EXPLORADORES * UMBRAL_R1`). Antes era 0.5 fijo.
  - Instrumentacion: cuando un nodo recibe sus `EXPLORADORES` ACK del ciclo escribe en la salida la linea
    `e nodo longitud_media_rutas nodos_distintos_visitados ciclo`.
* `extractData.py`
  - Ignora las lineas `e ` (no son cambios de topologia).
  - `FAST = True`: no calcula clustering/diametro/ASPL (lento); solo escribe los adjlist por ciclo.
    Poner `FAST = False` para recuperar el comportamiento original.
* `run_controls.py`: lanza los experimentos de control (ver docstring).
