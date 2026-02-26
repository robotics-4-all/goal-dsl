# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-26
**Commit:** 0718a45
**Branch:** devel

## OVERVIEW

GoalDSL — external DSL for goal-driven behaviour verification of IoT-enabled CPS.
Built with **textX** (grammar/parsing), **Jinja2** (M2T codegen), **click** (CLI), **FastAPI** (REST API).

## STRUCTURE

```
goal-dsl/
├── goal_dsl/              # Main Python package
│   ├── grammar/           # textX grammar files (.tx) — modular, 12 files
│   ├── templates/         # Jinja2 templates (.jinja) — M2T code generation
│   ├── transformations/   # Code generators (Python, PlantUML)
│   ├── cli/               # Click CLI: goaldsl validate|gen
│   ├── api/               # FastAPI REST API: /validate, /generate
│   ├── lib/               # Condition evaluation engine
│   ├── language.py        # Metamodel creation, scoping, obj_processors, model validation
│   ├── definitions.py     # Path constants, env vars
│   ├── logging.py         # Rich-based logging config
│   └── utils.py           # Timestamp utility
├── examples/              # 30 .goal example models across 20 scenario directories
├── build/                 # IGNORE — stale copy of goal_dsl/
├── Dockerfile             # Python 3.9, uvicorn entrypoint
├── docker-compose.yml     # goaldsl service, port 8082->8080
└── setup.py / setup.cfg   # Package config, textX entry points
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add/modify DSL syntax | `goal_dsl/grammar/*.tx` | Root grammar: `goal_dsl.tx`. Modular imports. |
| Change metamodel/validation | `goal_dsl/language.py` | `obj_processors`, `model_proc`, `get_metamodel()` |
| Change Python codegen | `goal_dsl/transformations/m2t_python.py` + `goal_dsl/templates/scenario.py.jinja` | Template renders per-scenario |
| Add new goal type | Grammar `.tx` + `language.py` (processors) + `m2t_python.py` (codegen) + template | Full pipeline touch |
| Condition evaluation logic | `goal_dsl/lib/condition.py` | `Condition.process_node_condition()` — post-order tree traversal |
| CLI commands | `goal_dsl/cli/cli.py` | Click-based: `validate`, `gen` |
| REST API endpoints | `goal_dsl/api/api.py` | FastAPI: `/validate`, `/generate`, file upload |
| DSL examples | `examples/*/scenario.goal` | Each subdir = one scenario with .goal files |
| Docker deployment | `Dockerfile`, `docker-compose.yml` | Uvicorn serves API |

## CONVENTIONS

- **File extension**: `.goal` for DSL model files
- **Grammar modularity**: Each goal domain has its own `.tx` file imported by root grammar
- **textX entry points** registered in `setup.cfg`: `textx_languages` → `goal_dsl:goaldsl_language`, `textx_generators` → `goal_dsl:codegen_python`
- **Scoping**: `FQNImportURI` for cross-file imports, `FQNGlobalRepo` for builtin models
- **Condition transform**: DSL conditions → Python lambda strings via regex substitution in `language.py`
- **Linter**: flake8, max-line-length=80

## ANTI-PATTERNS (THIS PROJECT)

- `build/` dir is a stale artifact — do NOT modify files there, they are copies of `goal_dsl/`
- `setup.py` references `smauto.__init__.py` in error message (line 16) — legacy name, project was renamed from SmAuto
- Duplicate `@generator` decorator in both `__init__.py` and `m2t_python.py` — only one is active via textX entry points
- Several goal types have `# TODO` in `m2t_python.py` `process_goals()` — codegen stubs not yet implemented
- `model_2_plantuml.py` has unused `metamodel_from_file` import
- No `tests/` directory exists — no automated test suite

## COMMANDS

```bash
# Install
pip install .

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

- Version: 0.3.0 (from `goal_dsl/__init__.py`)
- Metamodel is instantiated at module import time (`GoalDSLMetaModel = get_metamodel()` in `language.py:332`)
- `model_proc` runs validation + condition building on every model parse
- Generated code goes to `./gen/` by default (relative to CWD)
- API uses `X-API-Key` header auth, key from `API_KEY` env var
- `GOALDSL_ZERO_LOGS=1` env var disables all logging
- `GOALDSL_LOG_LEVEL` env var controls log level (default: INFO)
