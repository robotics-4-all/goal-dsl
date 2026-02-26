.PHONY: help install install-dev lint format check test validate gen ci build up down logs clean

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
	ruff check goal_dsl/

format: ## Auto-format code with ruff
	ruff format goal_dsl/
	ruff check --fix goal_dsl/

check: ## Lint + format check (no writes)
	ruff check goal_dsl/
	ruff format --check goal_dsl/

# ── Testing ────────────────────────────────────────────

test: ## Run pytest
	python -m pytest tests/ -v

validate: ## Validate all example .goal files
	@python -c "$$VALIDATE_SCRIPT"

define VALIDATE_SCRIPT
import glob, sys
from goal_dsl.language import build_model
files = sorted(glob.glob('examples/**/*.goal', recursive=True))
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
	@for f in $$(find examples -name '*.goal' | sort); do \
		goaldsl gen "$$f" 2>/dev/null && echo "  OK: $$f" || echo "FAIL: $$f"; \
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
	rm -rf build/ dist/ *.egg-info goal_dsl.egg-info goaldsl.egg-info gen/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
