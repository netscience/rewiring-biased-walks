# Reproduction of the analysis. Paths are relative to the repository root.
NETS_DIR ?= $(CURDIR)/nets
PY       ?= python3
WORKERS  ?= $(shell nproc 2>/dev/null || echo 2)
export NETS_DIR

.PHONY: all unpack metrics validate aggregate stats figures networks triangles controls robustness clean

all: unpack metrics validate aggregate stats figures networks triangles

unpack:
	mkdir -p $(NETS_DIR)
	for f in nets_packed/*.tar.xz; do tar -xJf $$f -C $(NETS_DIR); done

metrics:
	cd analysis && $(PY) run_metrics.py --workers $(WORKERS)

validate:
	cd analysis && $(PY) validate.py

aggregate:
	cd analysis && $(PY) aggregate.py

stats:
	cd analysis && $(PY) stats.py

figures:
	cd analysis && $(PY) figures.py && $(PY) concept_figures.py

networks:
	cd analysis && $(PY) draw_networks.py --rule R1 --lmax D2 && $(PY) draw_networks.py --rule R3 --lmax D2 && $(PY) draw_networks.py --rule R1 --lmax D16

triangles:
	cd analysis && $(PY) triangles.py --workers $(WORKERS)

controls:
	cd analysis && $(PY) controls.py --simruns ../simulator/simruns --workers $(WORKERS) && $(PY) controls_figure.py

robustness:
	cd analysis && $(PY) robustness.py --workers $(WORKERS)

clean:
	rm -rf analysis/results/metrics_per_cycle.csv analysis/results/rewiring_activity.csv analysis/results/degrees
