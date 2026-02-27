# Telos

An external Domain-Specific Language for goal-driven behaviour verification of IoT-enabled Cyber-Physical Systems. Define declarative verification scenarios for smart entities, robots, and connected devices using typed conditions, spatial constraints, and composable goal structures.

## Installation

```bash
git clone https://github.com/robotics-4-all/goal-dsl
cd goal-dsl
pip install .
```

Requires Python >= 3.11.

## Features

- Declarative, human-readable goal definitions
- Typed condition system with aggregation functions
- Composable goal structures (complex goals, repeaters)
- Multiple data source support (MQTT, AMQP, Redis, REST)
- Python code generation for runtime verification
- CLI and REST API interfaces

**Supported goal types:**

| Category | Goals |
|----------|-------|
| Entity | Watch, When, Eval |
| Area | Rect, Circle, Poly, Shadow, Line |
| Pose | Pos, Heading, Pose |
| Trajectory | Trace, Route, Arc |
| Composition | Cluster, Loop |
| Timing | Rate, Latency, Ordering, Deadline |

## Quick Start

```
Source<MQTT> HomeMQTT
    host: 'localhost'
    port: 1883
    auth:
        username: ''
        password: ''
end

Entity TempSensor
    type: sensor
    topic: 'bedroom.temperature'
    source: HomeMQTT
    attributes:
        - temp: float
end

Goal<When> TempHigh
    when
        TempSensor.temp > 30
end

Scenario MyScenario
    goals:
        - TempHigh
    concurrent: false
end
```

```bash
telos validate scenario.telos
telos gen scenario.telos
```

## Language Overview

For the complete syntax reference, see [docs/language-reference.md](docs/language-reference.md).

### Data Sources

Entities connect to data sources — either message brokers or REST endpoints.

**Message Brokers** (MQTT, AMQP, Redis):

```
Source<MQTT> HomeMQTT
    host: 'localhost'
    port: 1883
    auth:
        username: 'user'
        password: 'pass'
end
```

**REST Endpoints:**

```
RESTEndpoint SensorAPI
    verb: GET
    host: 'api.example.com'
    port: 443
    path: '/sensors/temperature'
end
```

### Entities

Entities represent connected devices with typed attributes.

```
Entity TempSensor
    type: sensor
    topic: 'bedroom.temperature'
    source: HomeMQTT
    freq: 10
    attributes:
        - temp: float
        - humidity: float
        - active: bool
end
```

- **type**: `sensor`, `actuator`, `hybrid`, or `robot`
- **topic**: Message topic for the entity
- **source**: Reference to a Source or RESTEndpoint
- **freq** (optional): Publishing frequency (sensors)
- **attributes**: Typed fields — `int`, `float`, `str`, `bool`, `list`, `dict`, `time`

Sensor attributes support value generators for virtual entities:

```
Entity VirtualSensor
    type: sensor
    freq: 5
    topic: 'virtual.bme'
    source: HomeMQTT
    attributes:
        - temperature: float -> gaussian(10, 20, 5) with noise gaussian(1, 1)
        - humidity: float -> linear(1, 0.2) with noise uniform(0, 1)
        - pressure: float -> constant(0.5)
end
```

### Conditions

Conditions reference entity attributes using dot notation (`EntityName.attribute`). Logical operators are **UPPERCASE**.

```
// Simple numeric
TempSensor.temp > 30

// N-ary AND/OR (no parentheses needed)
TempSensor.temp > 30 AND HumiditySensor.humidity < 0.5 AND DoorSensor.locked is true

// AND binds tighter than OR
TempSensor.temp > 30 AND HumiditySensor.humidity < 0.5 OR PressSensor.pressure > 1.0

// Parentheses for explicit grouping
(TempSensor.temp > 30 OR PressSensor.pressure > 1.0) AND HumiditySensor.humidity < 0.5

// NOT (unary)
NOT DoorSensor.locked is true

// XOR/NOR/NAND/XNOR require parenthesized binary form
(TempSensor.temp > 30) XOR (HumiditySensor.humidity < 0.5)

// Aggregation functions
mean(TempSensor.temp, 10) > 25 AND std(TempSensor.temp, 10) < 2

// Boolean
DoorSensor.locked is true

// Goal status
Goal_1.status == REACHED
```

**Operators:**

| Type | Operators |
|------|-----------|
| Numeric | `>`, `>=`, `<`, `<=`, `==`, `!=` |
| String | `~`, `!~`, `==`, `!=`, `has`, `in`, `not in` |
| Boolean | `is`, `is not` |
| Logical | `AND`, `OR`, `NOT`, `XOR`, `NOR`, `XNOR`, `NAND` |
| List/Dict | `==`, `!=`, `is`, `is not` |

`AND` binds tighter than `OR`. Use parentheses to override precedence. `XOR`, `NOR`, `NAND`, `XNOR` require parenthesized binary form: `(A) XOR (B)`.

**Aggregation functions:** `mean`, `std`, `var`, `min`, `max`, each taking `(attribute, buffer_size)`.

### Entity Goals

Entity goals use `when`/`then`/`config` blocks. All goal types support optional `timeout:` (seconds) and `tags:` fields.

**Watch** — reached when any message arrives on the entity's topic:

```
Goal<Watch> MessageReceived
    entity: TempSensor
end
```

**When** — reached when a typed condition evaluates to true:

```
Goal<When> TempAlert
    when
        TempSensor.temp > 30 AND HumiditySensor.humidity < 0.5
    then
        - NextGoal
    config
        timeConstraints:
            - FROM_GOAL_START(<60)
        description: 'Temperature alert'
    timeout: 60.0
    tags: [critical, temperature]
end
```

**Eval** — uses a Python expression string for complex conditions:

```
Goal<Eval> ComplexCheck
    when
        'TempSensor.temp * 2 > HumiditySensor.humidity + 10'
end
```

Goals can use `;` instead of `end` for compact one-line definitions:

```
Goal<When> TempHigh when TempSensor.temp > 30 ;
```

### Cluster Goals and Loops

```
Goal<Cluster> AllChecks
    goals:
        - Goal_1
        - Goal_2
        - Goal_3
    strategy: ALL_ACCOMPLISHED_ORDERED
end

Goal<Loop> RepeatCheck
    goal: Goal_1
    times: 5
end
```

**Strategies:** `ALL_ACCOMPLISHED`, `ALL_ACCOMPLISHED_ORDERED`, `NONE_ACCOMPLISHED`, `AT_LEAST_ONE_ACCOMPLISHED`, `EXACTLY_X_ACCOMPLISHED`, `EXACTLY_X_ACCOMPLISHED_ORDERED`.

### Scenarios

A scenario groups goals for execution.

```
Scenario Verification
    goals:
        - Goal_1 @ 0.5
        - Goal_2 @ 0.3
        - Goal_3 @ 0.2
    antigoals:
        - FatalCondition
    concurrent: true
    tickFreq: 10
end
```

- **goals**: Weighted goal list (`goal @ weight`, weight optional, default: equal)
- **antigoals** (optional): Goals that should NOT be reached
- **fatals** (optional): Goals that abort the scenario if reached
- **concurrent**: `true` for parallel, `false` for sequential execution

### Time Constraints

```
timeConstraints:
    - FROM_GOAL_START(<60)
    - FOR_TIME(5)
```

Types: `FROM_GOAL_START`, `FROM_SCENARIO_START`, `FOR_TIME`, `BETWEEN_GOALS_MIN`, `BETWEEN_GOALS_MAX`.

### Timing Goals

Timing goals verify temporal behavior using the `Duration` type (`100ms`, `2s`, `5m`, `1h`).

**Rate** — verify entity publishes at a consistent rate:

```
Goal<Rate> StableHeartbeat
    entity: TempSensor
    interval: 2s
    tolerance: 200ms
    window: 10
end
```

**Latency** — measure trigger→response time:

```
Goal<Latency> QuickResponse
    trigger: CommandSensor.command == 'read'
    response: StatusSensor.status == 'ok'
    within: 100ms
end
```

**Ordering** — verify goals complete in sequence:

```
Goal<Ordering> StartupOrder
    sequence:
        - StableHeartbeat
        - QuickResponse
    within: 30s
end
```

**Deadline** — condition must be met by a wall-clock time:

```
Goal<Deadline> MorningWarmup
    when TempSensor.temp > 20
    by: 08:00:00
end
```

### Imports

Models can be split across files:

```
// datasources.telos
Source<MQTT> HomeMQTT
    host: 'localhost'
    port: 1883
end

// scenario.telos
import "datasources.telos"
import datasources          // bare form, auto-appends .telos

Entity TempSensor
    type: sensor
    topic: 'bedroom.temp'
    source: HomeMQTT
    attributes:
        - temp: float
end
```

Both quoted (`import "file.telos"`) and bare (`import file`) forms are supported. Bare imports automatically append `.telos`.

### Constants

Top-level named constants for reuse across the model.

```
const TEMP_THRESHOLD = 30
const RATE = 0.5
const LABEL = 'high'
const ACTIVE = true
```

Supported value types: `int`, `float`, `string`, `bool`.

## CLI

```bash
telos validate <model>.telos    # Validate a model
telos gen <model>.telos         # Generate Python code
```

## REST API

```bash
# Docker
docker compose up --build

# Direct
uvicorn telos.api:api --host 0.0.0.0 --port 8080
```

Endpoints: `POST /validate`, `POST /generate`. See `telos/api/api.py` for details.

## Examples

The [examples/](./examples/) directory provides a progressive tutorial covering all Telos features:

| # | Directory | Topics |
|---|-----------|--------|
| 01 | `hello_world` | Minimal model: source, entity, goal, scenario |
| 02 | `sources_and_entities` | MQTT/Redis sources, entity types, attribute types, defaults |
| 03 | `conditions` | Numeric, string, boolean conditions, AND/OR/NOT |
| 04 | `entity_goals` | Watch, When, Eval, then/config blocks, timeout, tags, `;` syntax |
| 05 | `area_goals` | Rect, Circle, Poly, Shadow, Line, area tags |
| 06 | `pose_goals` | Pos, Heading, Pose, geometry types |
| 07 | `trajectory_goals` | Trace, Route, Arc |
| 08 | `composition` | Cluster strategies, Loop, nested composition |
| 09 | `advanced_conditions` | Aggregation functions, InRange, GoalStatus, n-ary, XOR/NOR |
| 10 | `time_constraints` | FROM_GOAL_START, FOR_TIME, FROM_SCENARIO_START |
| 11 | `scenarios` | Weights, antigoals, fatals, concurrent, tickFreq |
| 12 | `value_generators` | Generator functions, noise, default values |
| 13 | `all_data_sources` | MQTT+SSL, AMQP, Redis, REST, authentication |
| 14 | `constants_and_metadata` | Constants, Metadata, RTMonitor, comments |
| 15 | `real_world` | Complete greenhouse and robot inspection scenarios |
| 16 | `timing_goals` | Rate, Latency, Ordering, Deadline goals, Duration type |

## License

See [LICENSE](./LICENSE).
