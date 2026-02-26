# examples — GoalDSL Example Models

## OVERVIEW

30 `.goal` model files across 20 scenario directories demonstrating all DSL features.

## STRUCTURE

Each subdirectory = one example scenario. Pattern: `scenario.goal` + optional `gen/` with generated Python output.

```
examples/
├── entity_goals/          # EntityStateChange + EntityStateCondition
├── area_goals/            # RectangleArea + CircularArea
├── do_rectangle/          # Rectangle area with time constraints
├── pose_goals/            # Position, Orientation, Pose (3 files)
├── waypoint_trajectory_goal/  # WaypointTrajectory
├── moving_area_goal/      # MovingArea with multiple entities
├── complex_goal/          # ComplexGoal with ALL_ACCOMPLISHED_ORDERED
├── complex_goal_at_least_once/  # ComplexGoal with AT_LEAST_ONE
├── goal_repeater/         # GoalRepeater wrapping inner goal
├── goal_repeater_2/       # GoalRepeater variant
├── advanced_conditions/   # Multi-file: entities.goal + scenario.goal (import demo)
├── entity_pycond/         # EntityPyCondition (Python string conditions)
├── entity_attr_stream/    # EntityAttrStream goal type
├── entity_rest/           # REST endpoint as entity source
├── variable_entity/       # Variable entity definitions
├── composite_entity/      # Nested entity compartments
├── data_types/            # Custom DataType and Enumeration
├── loc_measure/           # 7 .goal files — multi-entity, multi-goal stress test
├── rse_scenarios/         # 2 subdirs: scenario_1/, scenario_2/
├── v3/                    # Version 3 syntax example
└── validate_all.sh        # Runs goaldsl validate on all examples
```

## WHERE TO LOOK

| Feature | Best Example |
|---------|-------------|
| Multi-file imports | `advanced_conditions/` (entities.goal → scenario.goal) |
| Complex goals | `complex_goal/` or `complex_goal_at_least_once/` |
| All goal types | `loc_measure/` (7 files, covers entity + area + conditions) |
| REST data source | `entity_rest/` |
| Pose/trajectory | `pose_goals/`, `waypoint_trajectory_goal/` |
| Custom types | `data_types/` |
| Generated output | Any `*/gen/` subdirectory |

## NOTES

- `validate_all.sh` is the closest thing to a test suite — validates grammar parsing only
- Generated Python files in `gen/` dirs may be stale (not auto-regenerated)
- `v3/` suggests syntax evolution — compare with other examples for differences
