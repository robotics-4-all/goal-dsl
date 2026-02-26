# grammar — textX Grammar Files

## OVERVIEW

Modular textX grammar defining the GoalDSL syntax. Root: `goal_dsl.tx`. Each domain concept in its own `.tx` file.

## STRUCTURE

```
grammar/
├── goal_dsl.tx          # ROOT — GoalDSLModel, Metadata, RTMonitor, Scenario, imports
├── goal.tx              # Goal supertype, ComplexGoal, GTermGoal, GoalRepeater, WeightedGoal
├── entity_goals.tx      # EntityStateChange, EntityStateCondition, EntityPyCondition, EntityAttrStream
├── area_goals.tx        # RectangleArea, CircularArea, PolylineArea, MovingArea, StraightLine
├── pose_goals.tx        # Pose, Position, Orientation goals
├── trajectory_goals.tx  # StraightLineTrajectory, WaypointTrajectory, CurveTrajectory
├── entity.tx            # Entity, Attribute, EntityType, EntityMode, EntitySource
├── communication.tx     # MessageBroker (MQTT, AMQP, Redis), RESTEndpoint, Authentication
├── condition.tx         # Condition tree (ConditionGroup, PrimitiveCondition, MathExpression, operators)
├── types.tx             # Time, Date, List, Dict, Point2D/3D, Orientation2D/3D, DataType, Property
├── time_constraint.tx   # TimeConstraint, FROM_GOAL_START, FOR_TIME, etc.
└── utils.tx             # FQN, Import, Comment, Keyword rules
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Add new goal type | Create rule in domain `.tx` → add to `Goal` alternatives in `goal.tx` | Follow existing pattern: `'Goal<TypeName>' name=ID (...) 'end'` |
| Add entity attribute | `entity.tx` | `Attribute` rule, dtype references `DataType` via FQN |
| Add new broker type | `communication.tx` | Add to `MessageBroker` alternatives |
| Modify condition syntax | `condition.tx` | Complex: MathExpression for numerics, operator rules at bottom |
| Add new time constraint | `time_constraint.tx` | Add to `TimeConstraintType` alternatives |
| Add new data type | `types.tx` | `DataType = PrimitiveDataType \| CustomDataType \| Enumeration` |
| Change import syntax | `utils.tx` | `Import` rule, `FQN` for dot-notation paths |

## CONVENTIONS

- **Naming**: Goal rules use `'Goal<TypeName>'` keyword prefix
- **Any-order groups**: `(...)#` — properties can appear in any order
- **Cross-references**: `[Type:FQN|+m:collection*]` for model-level, `+pm:` for parent-model level
- **Optional fields**: Marked with `?` suffix on assignment
- **List separators**: `'-'` for goal/entity lists, `','` for points/values
- **Comments**: `//` line, `/* */` block (defined in `utils.tx`)

## NOTES

- `CurveTrajectoryGoal` defined in `trajectory_goals.tx` but NOT referenced in `TrajectoryGoal` alternatives — unreachable
- `EntityStateTransitionGoal` defined in `entity_goals.tx` but NOT in `EntityGoal` alternatives — unreachable
- `TermPool` defined in `condition.tx` but not referenced from root grammar — unused
- `StraightLine` in `area_goals.tx` overlaps conceptually with `StraightLineTrajectoryGoal` in `trajectory_goals.tx`
