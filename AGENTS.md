# PROJECT KNOWLEDGE BASE

**Generated:** 2026-02-27
**Branch:** devel

## OVERVIEW

Telos — external DSL for goal-driven behaviour verification of IoT-enabled CPS.
Built with **textX** (grammar/parsing), **Jinja2** (M2T codegen), **click** (CLI), **FastAPI** (REST API).

Architecture follows **SmAuto pattern**: `auto_init_attributes=False`, custom classes in `lib/`, `class_provider()` function.

## STRUCTURE

```
goal-dsl/
├── telos/              # Main Python package
│   ├── grammar/           # textX grammar files (.tx) — modular, 12 files
│   ├── templates/         # Jinja2 templates (.jinja) — M2T code generation
│   ├── transformations/   # Code generators (Python, PlantUML)
│   ├── cli/               # Click CLI: telos validate|gen
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
├── examples/              # 16 .telos example models across 15 numbered tutorial directories
├── tests/                 # 210 tests, 93% coverage
├── build/                 # IGNORE — stale artifact
├── pyproject.toml         # Build config, deps, entry points, ruff
├── .pre-commit-config.yaml # ruff linting + formatting
├── Dockerfile             # Python 3.9, uvicorn entrypoint
└── docker-compose.yml     # telos service, port 8082->8080
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add/modify DSL syntax | `telos/grammar/*.tx` | Root grammar: `telos.tx`. Modular imports. |
| Add custom class | `telos/lib/` + `language.py` CUSTOM_CLASSES | Must use `parent=None, **kwargs` pattern |
| Change metamodel/validation | `telos/language.py` | `class_provider`, `model_proc`, `get_metamodel()` |
| Change Python codegen | `telos/transformations/m2t_python.py` + `telos/templates/scenario.py.jinja` | Template renders per-scenario |
| Add new goal type | Grammar `.tx` + lib class + `language.py` CUSTOM_CLASSES + codegen + template | Full pipeline touch |
| Condition evaluation logic | `telos/lib/condition.py` | `Condition.build()` → `process_node_condition()` post-order traversal |
| CLI commands | `telos/cli/cli.py` | Click-based: `validate`, `gen` |
| REST API endpoints | `telos/api/api.py` | FastAPI: `/validate`, `/generate`, file upload |
| DSL examples | `examples/01_hello_world/` → `examples/15_real_world/` | 15 numbered tutorials, progressive |
| Docker deployment | `Dockerfile`, `docker-compose.yml` | Uvicorn serves API |

## CONVENTIONS

- **File extension**: `.telos` for DSL model files
- **Architecture**: `auto_init_attributes=False` + `CUSTOM_CLASSES` list + `class_provider()` (SmAuto pattern)
- **Custom classes**: All use `__init__(self, parent=None, ..., **kwargs)` with defaults
- **Grammar modularity**: Each goal domain has its own `.tx` file imported by root grammar
- **textX entry points** registered in `pyproject.toml`: `textx_languages` → `telos:telos_language`, `textx_generators` → `telos.transformations.m2t_python:codegen_python`
- **Scoping**: `FQNImportURI` for cross-file imports, `FQNGlobalRepo` for builtin models
- **Condition building**: `Condition.build()` does post-order traversal → sets `cond_lambda` (string expression)
- **Condition precedence**: Expression grammar: OR (lowest) > AND > NOT (highest). N-ary: `A AND B AND C`. XOR/NOR/NAND/XNOR are binary with parens.
- **Entity goals**: Use `when`/`then`/`config` blocks (SmAuto pattern)
- **Spatial goals**: Keep flat syntax (no when/then/config)
- **Goal terminators**: Both `end` and `;` accepted (semicolon for inline definitions)
- **Source keywords**: `Source<MQTT>`, `Source<AMQP>`, `Source<Redis>` (Python classes still named `MQTTBroker` etc.)
- **Logical operators**: UPPERCASE (`AND`, `OR`, `NOT`)
- **Bool conditions**: `is` / `is not` operators
- **Weight syntax**: `@ weight` (e.g., `@ 0.5`)
- **Imports**: Both quoted (`import "file.telos"`) and bare (`import datasources`) supported
- **Constants**: `const NAME = VALUE` at model level (int, float, string, bool)
- **Linter**: ruff, line-length=99

## ANTI-PATTERNS (THIS PROJECT)

- `build/` dir is a stale artifact — do NOT modify files there
- `model_2_plantuml.py` has unused `metamodel_from_file` import
- Multi-file imports with `auto_init_attributes=False` have a textX bug — nested parser undoes attribute instrumentation. Workaround: inline entities instead of importing.

## COMMANDS

```bash
# Install
pip install -e .

# Validate a model
telos validate <path>.telos

# Generate Python code
telos gen <path>.telos

# Run API (Docker)
docker compose up --build

# Run API (direct)
uvicorn telos.api:api --host 0.0.0.0 --port 8080

# Build Docker image
./build.sh

# Validate all examples
./examples/validate_all.sh
```

## NOTES

- Version: 0.5.0 (from `telos/__init__.py`)
- Python >= 3.11 required
- `model_proc` runs validation on every model parse (name uniqueness, time validation)
- Condition building happens in codegen (`condition.build()`) not in `model_proc`
- Generated code goes to `./gen/` by default (relative to CWD)
- API uses `X-API-Key` header auth, key from `API_KEY` env var
- `TELOS_ZERO_LOGS=1` env var disables all logging
- `TELOS_LOG_LEVEL` env var controls log level (default: INFO)
- `TELOS_MODEL_REPO` env var sets model repository path for global scope providers
