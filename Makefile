.PHONY: help install install-dev lint format check test integration validate gen ci build up down logs clean

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

integration: ## Run integration tests (requires Docker)
	python -m pytest tests/integration/ -v -m integration --timeout=120

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

ci: check validate test ## Run full CI pipeline (lint + validate + test)

# ── Docker ─────────────────────────────────────────────

build: ## Build Docker image
	docker compose build

up: ## Start services (detached)
	docker compose up -d

down: ## Stop services
	docker compose down

logs: ## Tail service logs
	docker compose logs -f

# ── Cleanup ────────────────────────────────────────────

clean: ## Remove build artifacts
	rm -rf build/ dist/ *.egg-info telos.egg-info gen/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
