# examples — Telos Example Models

## OVERVIEW

16 `.telos` model files across 15 numbered directories. Progressive tutorial covering all DSL features from basics to real-world scenarios.

## STRUCTURE

Numbered directories guide learning step by step.

```
examples/
├── 01_hello_world/          # Minimal: source, entity, Watch goal, scenario
├── 02_sources_and_entities/ # MQTT, Redis, entity types, typed attributes, defaults
├── 03_conditions/           # Numeric, string, boolean, AND/OR/NOT, cross-entity
├── 04_entity_goals/         # Watch, When, Eval, then/config, timeout, tags, semicolons
├── 05_area_goals/           # Rect, Circle, Poly, Shadow, Line, area tags
├── 06_pose_goals/           # Pos, Heading, Pose, Point2D/3D, Orientation2D/3D
├── 07_trajectory_goals/     # Trace, Route, Arc
├── 08_composition/          # Cluster strategies, Loop, nested composition
├── 09_advanced_conditions/  # Aggregation, InRange, GoalStatus, n-ary, XOR/NOR/NAND
├── 10_time_constraints/     # FROM_GOAL_START, FOR_TIME, FROM_SCENARIO_START
├── 11_scenarios/            # Weights, antigoals, fatals, concurrent, tickFreq, namespace
├── 12_value_generators/     # Generators (constant, linear, gaussian, etc.), noise, defaults
├── 13_all_data_sources/     # MQTT+SSL, AMQP, Redis, REST, auth variants
├── 14_constants_and_metadata/ # const, Metadata, RTMonitor, comments
├── 15_real_world/           # 2 production-quality scenarios
│   ├── smart_greenhouse.telos
│   └── robot_inspection.telos
└── validate_all.sh          # Validates all examples
```

## WHERE TO LOOK

| Feature | Best Example |
|---------|-------------|
| Getting started | `01_hello_world/` |
| Entity goals (when/then/config) | `04_entity_goals/` |
| Conditions (typed, logical) | `03_conditions/`, `09_advanced_conditions/` |
| Area goals (spatial) | `05_area_goals/` |
| Pose / trajectory goals | `06_pose_goals/`, `07_trajectory_goals/` |
| Goal composition (Cluster, Loop) | `08_composition/` |
| Aggregation functions | `09_advanced_conditions/` |
| Time constraints | `10_time_constraints/` |
| Scenario options (weights, fatals) | `11_scenarios/` |
| Value generators + noise | `12_value_generators/` |
| All source types + REST | `13_all_data_sources/` |
| Constants, Metadata, RTMonitor | `14_constants_and_metadata/` |
| Real-world integration | `15_real_world/` |

## NOTES

- `validate_all.sh` validates all examples (no exclusions)
- All 16 examples validate successfully
- Each file includes educational comments explaining the concepts
- Examples avoid cross-file imports (textX bug with `auto_init_attributes=False`)
