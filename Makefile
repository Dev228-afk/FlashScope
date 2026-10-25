.PHONY: test benchmark triage clean help

RECORDS ?= 2300000
DB ?= /tmp/flashscope_benchmark.db
WORKSPACE_DB ?= benchmark.db

help:
	@echo "FlashScope Build & Test Automation"
	@echo "  make test        - Run all unit and integration tests (pytest)"
	@echo "  make benchmark   - Run full 2.3M-record ingestion and triage scale benchmark"
	@echo "  make triage      - Run automated incident triage on flashscope.db"
	@echo "  make clean       - Remove cached artifacts and temporary databases"

test:
	PYTHONPATH=. python3 -m pytest -v

benchmark:
	PYTHONPATH=. python3 benchmarks/run_benchmark.py --records $(RECORDS) --db $(DB) --copy-to $(WORKSPACE_DB)

triage:
	PYTHONPATH=. python3 -m flashscope.cli.main triage --db $(WORKSPACE_DB)

clean:
	rm -rf .pytest_cache __pycache__ tests/__pycache__ tests/unit/__pycache__ tests/integration/__pycache__
	rm -f *.db *.db-wal *.db-shm /tmp/flashscope_benchmark.db*
