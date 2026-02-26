# telos — Core Package

## OVERVIEW

Main Python package implementing the Telos language: grammar loading, metamodel, validation, code generation, CLI, and API.
Uses SmAuto architecture: `auto_init_attributes=False`, custom classes in `lib/`, `class_provider()`.

## STRUCTURE

```
telos/
├── __init__.py          # Package entry: version, textX @language decorator
├── language.py          # Central: class_provider, CUSTOM_CLASSES, model_proc validation, get_metamodel()
├── definitions.py       # TEMPLATES_PATH, GRAMMAR_PATH, env vars (ZERO_LOGS, LOG_LEVEL, MODEL_REPO)
├── logging.py           # Rich logging setup, controlled by definitions.py
├── utils.py             # gen_timestamp() only
├── grammar/             # textX grammar .tx files (see grammar/AGENTS.md)
├── templates/           # Jinja2 .jinja files for M2T generation
├── transformations/     # Code generators
│   ├── m2t_python.py    # Python codegen: parse → condition.build() → Jinja render → .py per scenario
│   └── model_2_plantuml.py  # PlantUML diagram generator
├── cli/cli.py           # Click CLI: `telos validate|gen`
├── api/api.py           # FastAPI REST: /validate, /generate (with file/b64/JSON variants)
└── lib/                 # Custom classes (SmAuto pattern)
    ├── condition.py     # Condition tree classes + cond_lambda builder (post-order traversal)
    ├── entity.py        # Entity + typed attributes (Int/Float/Bool/String/List/Dict/Time)
    ├── broker.py        # Broker classes (MQTT/AMQP/Redis + BrokerAuthPlain)
    └── types.py         # Shared types: List, Dict, Time, Date
```

## WHERE TO LOOK

| Task | File | Key function/class |
|------|------|--------------------|
| Metamodel creation | `language.py` | `get_metamodel()` — auto_init_attributes=False, class_provider |
| Model validation | `language.py` | `model_proc()` — verify names, time validation |
| Custom classes | `lib/*.py` + `language.py` | CUSTOM_CLASSES list + class_provider() |
| Scoping providers | `language.py` | `get_scope_providers()` — FQNImportURI + FQNGlobalRepo |
| Condition building | `lib/condition.py` | `Condition.build()` → `process_node_condition()` post-order |
| Python codegen | `transformations/m2t_python.py` | `generate()` → condition.build() → template.render() |
| PlantUML codegen | `transformations/model_2_plantuml.py` | `generate_diagram()` |

## CONVENTIONS

- `build_model(path)` / `build_model_str(str)` — two parse entry points, return single model
- Codegen output: one `.py` file per Scenario, named `{scenario.name}.py`
- Template context: `rtmonitor`, `scenario`, `entities`, `entity_names`, `goals`
- `__init__.py` re-exports `get_metamodel` and `telos_language` as public API
- `transformations/__init__.py` aliases: `m2t_python = generate`, `m2t_python_str = generate_str`
- Condition building happens in codegen (not in model_proc)

## ANTI-PATTERNS

- `build/` dir is a stale artifact — do NOT modify
- `model_2_plantuml.py` has unused `metamodel_from_file` import
- textX `auto_init_attributes=False` + multi-file imports bug — workaround: inline entities
