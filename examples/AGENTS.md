# examples — Telos Example Models

## OVERVIEW

26 `.telos` model files across 18 scenario directories demonstrating all DSL features.
All examples use the refactored syntax: `broker:`/`topic:`, `when`/`then`/`config`, UPPERCASE operators.

## STRUCTURE

Each subdirectory = one example scenario. Pattern: `scenario.telos`.

```
examples/
├── entity_goals/          # EntityStateChange + EntityStateCondition + EntityPyCondition
├── area_goals/            # RectangleArea + CircularArea
├── do_rectangle/          # Rectangle area with time constraints
├── pose_goals/            # Position, Orientation, Pose (3 files)
├── waypoint_trajectory_goal/  # WaypointTrajectory
├── moving_area_goal/      # MovingArea with multiple entities
├── complex_goal/          # ComplexGoal with ALL_ACCOMPLISHED_ORDERED
├── complex_goal_at_least_once/  # ComplexGoal with AT_LEAST_ONE
├── goal_repeater/         # GoalRepeater wrapping inner goal
├── goal_repeater_2/       # GoalRepeater variant
├── advanced_conditions/   # Aggregation, InRange, GoalStatus, bool conditions
├── entity_pycond/         # EntityPyCondition (Python string conditions)
├── entity_rest/           # Entity with REST endpoint defined
├── variable_entity/       # Value generators + noise on attributes
├── loc_measure/           # 7 .telos files — multi-entity, multi-goal stress test
├── rse_scenarios/         # 2 subdirs: scenario_1/, scenario_2/
├── v3/                    # Comprehensive syntax example
└── validate_all.sh        # Runs telos validate on all examples
```

## WHERE TO LOOK

| Feature | Best Example |
|---------|-------------|
| Entity goals (when/then/config) | `entity_goals/` |
| Complex goals | `complex_goal/` or `complex_goal_at_least_once/` |
| Advanced conditions (aggregation, GoalStatus, InRange) | `advanced_conditions/` |
| EntityPyCondition (string conditions) | `entity_pycond/` |
| Value generators + noise | `variable_entity/` |
| Area goals | `area_goals/`, `do_rectangle/`, `moving_area_goal/` |
| Pose/trajectory | `pose_goals/`, `waypoint_trajectory_goal/` |
| GoalRepeater | `goal_repeater/`, `goal_repeater_2/` |
| Multi-entity, multi-goal | `loc_measure/` (7 files) |

## NOTES

- `validate_all.sh` validates grammar parsing only (closest thing to a test suite)
- Deleted examples: `entity_attr_stream/`, `composite_entity/`, `data_types/` (features removed)
- Multi-file imports work but have a textX bug with `auto_init_attributes=False` — examples inline entities instead
- All 26 examples validate and generate successfully
