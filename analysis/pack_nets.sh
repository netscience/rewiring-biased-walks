#!/bin/bash
# Empaqueta, por regla/estrategia, los adjlist de los ciclos 0-30 y el log salida_*.txt
# de cada ejecucion (excluye D32). Reanudable: omite los archivos ya creados.
# Uso: bash pack_nets.sh [segundos_max]
cd "$(dirname "$0")/../nets" || exit 1
OUT=../analysis/packed; LIMIT=${1:-150}; T0=$(date +%s)
for rule in R1 R2 R3; do for alg in $(ls $rule); do
  f=$OUT/${rule}_${alg}.tar.xz
  [ -f "$f" ] && continue
  (( $(date +%s) - T0 > LIMIT )) && { echo "tiempo agotado"; exit 2; }
  list=$(mktemp)
  for lm in D2 D4 D8 D16; do for r in $(ls $rule/$alg/$lm | grep -E '^[0-9]+$'); do
    for c in $(seq 0 30); do p=$rule/$alg/$lm/$r/graph_test_$c.adjlist; [ -f $p ] && echo $p; done
    ls $rule/$alg/$lm/$r/salida_*.txt
  done; done >> $list
  tar -cf - -T $list | xz -3 -T4 > $f.tmp && mv $f.tmp $f
  echo "$f $(stat -c %s $f) $(( $(date +%s) - T0 ))s"
  rm -f $list
done; done
echo "listo"
