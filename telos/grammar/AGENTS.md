# grammar — textX Grammar Files

## OVERVIEW

Modular textX grammar defining the Telos syntax. Root: `telos.tx`. Each domain concept in its own `.tx` file.
Uses SmAuto-style condition grammar with UPPERCASE logical operators, typed attribute references, and when/then/config blocks.

## STRUCTURE

```
grammar/
├── telos.tx             # ROOT — TelosModel, Metadata, RTMonitor, Scenario, imports
├── goal.tx              # Goal supertype, ComplexGoal, GoalRepeater, WeightedGoal
├── entity_goals.tx      # EntityStateChange, EntityStateCondition, EntityPyCondition (when/then/config)
├── area_goals.tx        # RectangleArea, CircularArea, PolylineArea, MovingArea, StraightLine
├── pose_goals.tx        # Pose, Position, Orientation goals
├── trajectory_goals.tx  # StraightLineTrajectory, WaypointTrajectory, CurveTrajectory
├── entity.tx            # Entity, typed Attributes (Int/Float/Bool/String/List/Dict/Time), ValueGens, Noise
├── communication.tx     # MessageBroker (MQTT, AMQP, Redis), BrokerConnection, RESTEndpoint, Authentication
├── condition.tx         # SmAuto-style: ConditionGroup, typed conditions, GoalStatusCondition, aggregation
├── types.tx             # Time, Date, List, Dict, Point2D/3D, Orientation2D/3D
├── time_constraint.tx   # TimeConstraint, FROM_GOAL_START, FOR_TIME, etc.
└── utils.tx             # FQN, Import (importURI), Comment, Keyword rules
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Add new goal type | Create rule in domain `.tx` → add to `Goal` alternatives in `goal.tx` | Pattern: `'Goal<TypeName>' name=ID (...) 'end'` |
| Add entity attribute type | `entity.tx` | Add to `Attribute` alternatives + `NumericAttribute` if numeric |
| Add new broker type | `communication.tx` | Add to `MessageBroker` alternatives |
| Modify condition syntax | `condition.tx` | Typed conditions, aggregation functions, operator rules |
| Add new time constraint | `time_constraint.tx` | Add to `TimeConstraintType` alternatives |
| Change import syntax | `utils.tx` | `Import` rule with `importURI` attribute (required by FQNImportURI) |

## CONVENTIONS

- **Naming**: Goal rules use `'Goal<TypeName>'` keyword prefix
- **Any-order groups**: `(...)#` — properties can appear in any order
- **Cross-references**: `[Type:FQN|+m:collection*]` for model-level
- **Optional fields**: Marked with `?` suffix on assignment
- **List separators**: `'-'` for goal/entity lists, `','` for points/values
- **Comments**: `//` line, `/* */` block (defined in `utils.tx`)
- **Entity goals**: Use `when` (condition), `then` (triggers), `config` (timeConstraints, description)
- **Spatial goals**: Flat syntax — no when/then/config blocks
- **Conditions**: UPPERCASE logical operators (AND, OR, NOT), typed attribute refs
- **Bool conditions**: `is` / `is not` operators
- **Aggregation**: `mean(attr, N)`, `std(attr, N)`, etc. with buffer size

## NOTES

- `CurveTrajectoryGoal` in `trajectory_goals.tx` NOT referenced in alternatives — unreachable
- `StraightLine` in `area_goals.tx` overlaps with `StraightLineTrajectoryGoal`
- `ConditionGroup` only supports binary nesting: `(A) AND (B)`, chain as `((A) AND (B)) AND (C)`
- `GoalStatusCondition` references goals by name (ID), not cross-ref — avoids circular deps
