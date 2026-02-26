# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-26
**Branch:** devel

## OVERVIEW

GoalDSL — external DSL for goal-driven behaviour verification of IoT-enabled CPS.
Built with **textX** (grammar/parsing), **Jinja2** (M2T codegen), **click** (CLI), **FastAPI** (REST API).

Architecture follows **SmAuto pattern**: `auto_init_attributes=False`, custom classes in `lib/`, `class_provider()` function.

## STRUCTURE

```
goal-dsl/
├── goal_dsl/              # Main Python package
│   ├── grammar/           # textX grammar files (.tx) — modular, 12 files
│   ├── templates/         # Jinja2 templates (.jinja) — M2T code generation
│   ├── transformations/   # Code generators (Python, PlantUML)
│   ├── cli/               # Click CLI: goaldsl validate|gen
│   ├── api/               # FastAPI REST API: /validate, /generate
│   ├── lib/               # Custom classes: condition, entity, broker, types
│   │   ├── condition.py   # Condition tree classes + cond_lambda builder
│   │   ├── entity.py      # Entity + typed attributes (Int/Float/Bool/String/List/Dict/Time)
│   │   ├── broker.py      # Broker classes (MQTT/AMQP/Redis + AuthPlain)
│   │   └── types.py       # Shared types: List, Dict, Time, Date
│   ├── language.py        # Metamodel: class_provider, CUSTOM_CLASSES, model_proc validation
│   ├── definitions.py     # Path constants, env vars (LOG_LEVEL, ZERO_LOGS, MODEL_REPO)
│   ├── logging.py         # Rich-based logging config
│   └── utils.py           # Timestamp utility
├── examples/              # 26 .goal example models across 18 scenario directories
├── build/                 # IGNORE — stale copy of goal_dsl/
├── pyproject.toml         # Build config, deps, entry points, ruff
├── .pre-commit-config.yaml # ruff linting + formatting
├── Dockerfile             # Python 3.9, uvicorn entrypoint
└── docker-compose.yml     # goaldsl service, port 8082->8080
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add/modify DSL syntax | `goal_dsl/grammar/*.tx` | Root grammar: `goal_dsl.tx`. Modular imports. |
| Add custom class | `goal_dsl/lib/` + `language.py` CUSTOM_CLASSES | Must use `parent=None, **kwargs` pattern |
| Change metamodel/validation | `goal_dsl/language.py` | `class_provider`, `model_proc`, `get_metamodel()` |
| Change Python codegen | `goal_dsl/transformations/m2t_python.py` + `goal_dsl/templates/scenario.py.jinja` | Template renders per-scenario |
| Add new goal type | Grammar `.tx` + lib class + `language.py` CUSTOM_CLASSES + codegen + template | Full pipeline touch |
| Condition evaluation logic | `goal_dsl/lib/condition.py` | `Condition.build()` → `process_node_condition()` post-order traversal |
| CLI commands | `goal_dsl/cli/cli.py` | Click-based: `validate`, `gen` |
| REST API endpoints | `goal_dsl/api/api.py` | FastAPI: `/validate`, `/generate`, file upload |
| DSL examples | `examples/*/scenario.goal` | Each subdir = one scenario with .goal files |
| Docker deployment | `Dockerfile`, `docker-compose.yml` | Uvicorn serves API |

## CONVENTIONS

- **File extension**: `.goal` for DSL model files
- **Architecture**: `auto_init_attributes=False` + `CUSTOM_CLASSES` list + `class_provider()` (SmAuto pattern)
- **Custom classes**: All use `__init__(self, parent=None, ..., **kwargs)` with defaults
- **Grammar modularity**: Each goal domain has its own `.tx` file imported by root grammar
- **textX entry points** registered in `pyproject.toml`: `textx_languages` → `goal_dsl:goaldsl_language`, `textx_generators` → `goal_dsl.transformations.m2t_python:codegen_python`
- **Scoping**: `FQNImportURI` for cross-file imports, `FQNGlobalRepo` for builtin models
- **Condition building**: `Condition.build()` does post-order traversal → sets `cond_lambda` (string expression)
- **Entity goals**: Use `when`/`then`/`config` blocks (SmAuto pattern)
- **Spatial goals**: Keep flat syntax (no when/then/config)
- **Logical operators**: UPPERCASE (`AND`, `OR`, `NOT`)
- **Bool conditions**: `is` / `is not` operators
- **Linter**: ruff, line-length=99

## ANTI-PATTERNS (THIS PROJECT)

- `build/` dir is a stale artifact — do NOT modify files there
- `model_2_plantuml.py` has unused `metamodel_from_file` import
- No `tests/` directory exists — no automated test suite
- Multi-file imports with `auto_init_attributes=False` have a textX bug — nested parser undoes attribute instrumentation. Workaround: inline entities instead of importing.

## COMMANDS

```bash
# Install
pip install -e .

# Validate a model
goaldsl validate <path>.goal

# Generate Python code
goaldsl gen <path>.goal

# Run API (Docker)
docker compose up --build

# Run API (direct)
uvicorn goal_dsl.api:api --host 0.0.0.0 --port 8080

# Build Docker image
./build.sh

# Validate all examples
./examples/validate_all.sh
```

## NOTES

- Version: 0.4.0 (from `goal_dsl/__init__.py`)
- Python >= 3.11 required
- `model_proc` runs validation on every model parse (name uniqueness, time validation)
- Condition building happens in codegen (`condition.build()`) not in `model_proc`
- Generated code goes to `./gen/` by default (relative to CWD)
- API uses `X-API-Key` header auth, key from `API_KEY` env var
- `GOALDSL_ZERO_LOGS=1` env var disables all logging
- `GOALDSL_LOG_LEVEL` env var controls log level (default: INFO)
- `GOALDSL_MODEL_REPO` env var sets model repository path for global scope providers
