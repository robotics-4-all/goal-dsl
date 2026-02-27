.PHONY: help install install-dev lint format check test integration integration-e2e validate gen ci ci-full broker-up broker-down clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ── Setup ──────────────────────────────────────────────

install: ## Install package
	pip install .

install-dev: ## Install with dev + test dependencies
	pip install -e ".[dev,test]"
	pre-commit install

# ── Code Quality ───────────────────────────────────────

lint: ## Run ruff linter
	ruff check telos/

format: ## Auto-format code with ruff
	ruff format telos/
	ruff check --fix telos/

check: ## Lint + format check (no writes)
	ruff check telos/
	ruff format --check telos/

# ── Testing ────────────────────────────────────────────

test: ## Run unit tests with coverage
	@if [ -d tests ]; then python -m pytest tests/ -v --cov=telos --cov-report=term-missing --ignore=tests/integration; else echo "No tests/ directory — skipping"; fi

integration: ## Run integration tests — validate, generate, compile (no Docker)
	python -m pytest tests/integration/ -v -m "not integration"

integration-e2e: ## Run E2E integration tests (requires Docker)
	python -m pytest tests/integration/ -v -m integration

validate: ## Validate all example .telos files
	@python -c "$$VALIDATE_SCRIPT"

define VALIDATE_SCRIPT
import glob, sys
from telos.language import build_model
files = sorted(glob.glob('examples/**/*.telos', recursive=True))
ok = fail = 0
for f in files:
    try:
        build_model(f); ok += 1; print(f'  OK: {f}')
    except Exception as e:
        fail += 1; print(f'FAIL: {f} -> {e}')
print(f'{ok}/{ok+fail} OK')
sys.exit(1 if fail else 0)
endef
export VALIDATE_SCRIPT

gen: ## Generate Python code for all examples
	@for f in $$(find examples -name '*.telos' | sort); do \
		telos gen "$$f" 2>/dev/null && echo "  OK: $$f" || echo "FAIL: $$f"; \
	done

# ── CI ─────────────────────────────────────────────────

ci: check validate test integration ## Run full CI pipeline (lint + validate + test + integration)

ci-full: check validate test integration integration-e2e ## Full CI pipeline including E2E (requires Docker)

# ── Docker (test infrastructure) ──────────────────────

broker-up: ## Start MQTT broker + Redis for E2E tests
	docker compose -f docker/docker-compose.test.yml up -d --wait

broker-down: ## Stop MQTT broker + Redis
	docker compose -f docker/docker-compose.test.yml down -v

# ── Cleanup ────────────────────────────────────────────

clean: ## Remove build artifacts
	rm -rf build/ dist/ *.egg-info telos.egg-info gen/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
