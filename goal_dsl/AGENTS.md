# goal_dsl — Core Package

## OVERVIEW

Main Python package implementing the GoalDSL language: grammar loading, metamodel, validation, code generation, CLI, and API.

## STRUCTURE

```
goal_dsl/
├── __init__.py          # Package entry: version, textX @language + @generator decorators
├── language.py          # Central file: metamodel, scoping, obj_processors, model validation
├── definitions.py       # TEMPLATES_PATH, GRAMMAR_PATH, env vars (GOALDSL_ZERO_LOGS, LOG_LEVEL)
├── logging.py           # Rich logging setup, controlled by definitions.py
├── utils.py             # gen_timestamp() only
├── grammar/             # textX grammar .tx files (see grammar/AGENTS.md)
├── templates/           # Jinja2 .jinja files for M2T generation
├── transformations/     # Code generators
│   ├── m2t_python.py    # Python codegen: parse model → Jinja render → write .py per scenario
│   └── model_2_plantuml.py  # PlantUML diagram generator
├── cli/cli.py           # Click CLI: `goaldsl validate|gen`
├── api/api.py           # FastAPI REST: /validate, /generate (with file/b64/JSON variants)
└── lib/condition.py     # Condition tree → Python expression transformer
```

## WHERE TO LOOK

| Task | File | Key function/class |
|------|------|--------------------|
| Metamodel creation | `language.py` | `get_metamodel()` (line 303) |
| Model validation | `language.py` | `model_proc()` — calls verify_*, process_goals, build_conditions |
| Object processors | `language.py` | `obj_processors` dict (line 270): Goal, NID, Scenario |
| Scoping providers | `language.py` | `get_scope_providers()` — FQNImportURI + FQNGlobalRepo |
| Condition → Python | `language.py` | `transform_cond_py()` — regex-based Entity.attr → `entities["X"].attributes["Y"]` |
| Condition tree eval | `lib/condition.py` | `Condition.process_node_condition()` — recursive post-order traversal |
| Python codegen | `transformations/m2t_python.py` | `generate()` → `_generate_internal()` → template.render() |
| PlantUML codegen | `transformations/model_2_plantuml.py` | `generate_diagram()` |

## CONVENTIONS

- `build_model(path)` / `build_model_str(str)` — two parse entry points
- Codegen output: one `.py` file per Scenario, named `{scenario.name}.py`
- Template context: `rtmonitor`, `scenario`, `entities`, `entity_names`, `goals`
- `__init__.py` re-exports `get_metamodel` and `m2t_python` as public API
- `transformations/__init__.py` aliases: `m2t_python = generate`, `m2t_python_str = generate_str`

## ANTI-PATTERNS

- Two `@generator('goal_dsl', 'python')` decorators exist: `__init__.py:15` AND `m2t_python.py:202` — only setup.cfg entry point matters
- `m2t_python.py` re-defines `THIS_DIR` (line 10) shadowing the import from definitions
- Condition processing has two parallel systems: old regex-based (`language.py:398-453`) and new tree-based (`lib/condition.py`) — both are active
- `pycondition_processor` in `language.py` builds `cond_py` via regex but result is used differently than `lib/condition.py` tree approach
