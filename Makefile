# Atalho para Linux/macOS/CI (GNU make). No Windows, use direto: python tools/check.py
PYTHON ?= python

.PHONY: check install

install:
	$(PYTHON) -m pip install -e . --group dev
	$(PYTHON) -m pre_commit install

check:
	$(PYTHON) tools/check.py
