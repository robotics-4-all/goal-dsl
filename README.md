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

## Quick Start

```
Broker<MQTT> HomeMQTT
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
Broker<MQTT> HomeMQTT
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
- **source**: Reference to a Broker or RESTEndpoint
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

// Compound
(TempSensor.temp > 30) AND (HumiditySensor.humidity < 0.5)

// Aggregation functions
(mean(TempSensor.temp, 10) > 25) AND (std(TempSensor.temp, 10) < 2)

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

**Aggregation functions:** `mean`, `std`, `var`, `min`, `max` — each takes `(attribute, buffer_size)`.

### Entity Goals

Entity goals use `when`/`then`/`config` blocks.

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
        (TempSensor.temp > 30) AND (HumiditySensor.humidity < 0.5)
    then
        - NextGoal
    config
        timeConstraints:
            - FROM_GOAL_START(<60)
        description: 'Temperature alert'
end
```

**Eval** — uses a Python expression string for complex conditions:

```
Goal<Eval> ComplexCheck
    when
        'TempSensor.temp * 2 > HumiditySensor.humidity + 10'
end
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
        - Goal_1 -> 0.5
        - Goal_2 -> 0.3
        - Goal_3 -> 0.2
    antigoals:
        - FatalCondition
    concurrent: true
    tickFreq: 10
end
```

- **goals**: Weighted goal list (weights optional, default: equal)
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

### Imports

Models can be split across files:

```
// datasources.telos
Broker<MQTT> HomeMQTT
    host: 'localhost'
    port: 1883
end

// scenario.telos
import datasources.telos

Entity TempSensor
    type: sensor
    topic: 'bedroom.temp'
    source: HomeMQTT
    attributes:
        - temp: float
end
```

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

See the [examples/](./examples/) directory for working models covering all goal types.

## License

See [LICENSE](./LICENSE).
