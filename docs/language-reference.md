# GoalDSL Language Reference

Complete syntax reference for GoalDSL. For a quick introduction, see the [README](../README.md).

## Table of Contents

- [Model Structure](#model-structure)
- [Metadata](#metadata)
- [Data Sources](#data-sources)
  - [Message Brokers](#message-brokers)
  - [REST Endpoints](#rest-endpoints)
  - [Authentication](#authentication)
- [Entities](#entities)
  - [Attribute Types](#attribute-types)
  - [Value Generators](#value-generators)
  - [Noise Functions](#noise-functions)
- [Conditions](#conditions)
  - [Numeric Conditions](#numeric-conditions)
  - [String Conditions](#string-conditions)
  - [Boolean Conditions](#boolean-conditions)
  - [List and Dict Conditions](#list-and-dict-conditions)
  - [Time Conditions](#time-conditions)
  - [InRange Conditions](#inrange-conditions)
  - [GoalStatus Conditions](#goalstatus-conditions)
  - [Aggregation Functions](#aggregation-functions)
  - [Condition Groups](#condition-groups)
- [Goals](#goals)
  - [Watch](#watch)
  - [When](#when)
  - [Eval](#eval)
  - [Rect](#rect)
  - [Circle](#circle)
  - [Poly](#poly)
  - [Shadow](#shadow)
  - [Pos](#pos)
  - [Heading](#heading)
  - [Pose](#pose)
  - [Trace](#trace)
  - [Route](#route)
  - [Cluster](#cluster)
  - [Loop](#loop)
- [Scenarios](#scenarios)
- [Time Constraints](#time-constraints)
- [Geometry Types](#geometry-types)
- [Imports](#imports)
- [Comments](#comments)
- [RTMonitor](#rtmonitor)

---

## Model Structure

A GoalDSL model file (`.goal`) has the following top-level structure. All sections are optional and can appear in any order.

```
import <file>.goal

Metadata ... end

Broker<...> ... end
RESTEndpoint ... end
Entity ... end
Goal<...> ... end
Scenario ... end
```

## Metadata

Optional model metadata.

```
Metadata
    name: MyProject
    version: "1.0.0"
    author: "Author Name"
    email: "author@example.com"
    description: "Project description"
end
```

All fields except `name` and `version` are optional.

## Data Sources

Entities reference data sources for communication. A source can be a message broker or a REST endpoint.

### Message Brokers

Three broker protocols are supported.

**MQTT:**

```
Broker<MQTT> HomeMQTT
    host: 'localhost'
    port: 1883
    ssl: false
    basePath: ''
    webPath: '/mqtt'
    webPort: 8883
    auth:
        username: 'user'
        password: 'pass'
end
```

| Property | Required | Description |
|----------|----------|-------------|
| `host` | yes | Hostname or IP |
| `port` | yes | Port number |
| `ssl` | no | Enable TLS (default: false) |
| `basePath` | no | MQTT base path |
| `webPath` | no | WebSocket path |
| `webPort` | no | WebSocket port |
| `auth` | no | Authentication credentials |

**AMQP:**

```
Broker<AMQP> MyAMQP
    host: 'rabbitmq.local'
    port: 5672
    vhost: '/'
    topicExchange: 'amq.topic'
    auth:
        username: 'guest'
        password: 'guest'
end
```

| Property | Required | Description |
|----------|----------|-------------|
| `host` | yes | Hostname or IP |
| `port` | yes | Port number |
| `vhost` | no | Virtual host |
| `topicExchange` | no | Topic exchange name |
| `rpcExchange` | no | RPC exchange name |
| `ssl` | no | Enable TLS |
| `auth` | no | Authentication credentials |

**Redis:**

```
Broker<Redis> LocalRedis
    host: 'localhost'
    port: 6379
    db: 0
    ssl: false
    auth:
        username: ''
        password: ''
end
```

| Property | Required | Description |
|----------|----------|-------------|
| `host` | yes | Hostname or IP |
| `port` | yes | Port number |
| `db` | no | Database number (default: 0) |
| `ssl` | no | Enable TLS |
| `auth` | no | Authentication credentials |

### REST Endpoints

```
RESTEndpoint SensorAPI
    verb: GET
    host: 'api.example.com'
    port: 443
    path: '/api/v1/sensors'
    base_url: 'https://api.example.com'
    params:
        query:
            - sensorId: str
            - limit: int
        path:
            - regionId: str
        body:
            - payload: dict
    headers:
        - authorization: str
        - contentType: str
end
```

| Property | Required | Description |
|----------|----------|-------------|
| `verb` | yes | `GET`, `POST`, `PUT`, or `DELETE` |
| `host` | yes | Hostname |
| `port` | yes | Port number |
| `path` | yes | URL path |
| `base_url` | no | Base URL |
| `params` | no | Query, path, and body parameters |
| `headers` | no | HTTP headers |

Parameters and headers are typed properties (`name: type`) where type is one of: `int`, `float`, `str`, `bool`, `list`, `dict`, `time`.

### Authentication

Three authentication methods are supported in broker definitions.

**Plain credentials:**
```
auth:
    username: 'user'
    password: 'pass'
```

**API key:**
```
auth:
    key: 'my-api-key'
```

**Certificate:**
```
auth:
    cert: '<PEM string>'
    // or
    certPath: '/path/to/cert.pem'
```

## Entities

An entity represents a connected device or data source endpoint.

```
Entity TempSensor
    type: sensor
    topic: 'bedroom.temperature'
    source: HomeMQTT
    freq: 10
    description: 'Bedroom temperature sensor'
    attributes:
        - temp: float = 20.0
        - humidity: float
        - label: str = 'default'
        - active: bool = true
end
```

| Property | Required | Description |
|----------|----------|-------------|
| `type` | yes | `sensor`, `actuator`, `hybrid`, or `robot` |
| `topic` | yes | Message topic (use `.` as separator) |
| `source` | yes | Reference to a Broker or RESTEndpoint |
| `freq` | no | Publishing frequency in Hz (sensors) |
| `description` | no | Human-readable description |
| `attributes` | yes | List of typed attributes |

Each entity has its own source reference, enabling multi-broker architectures.

### Attribute Types

| Type | Syntax | Default |
|------|--------|---------|
| Integer | `name: int` | `0` |
| Float | `name: float` | `0.0` |
| String | `name: str` | `""` |
| Boolean | `name: bool` | `false` |
| Time | `name: time` | `00:00:00` |
| List | `name: list` | `[]` |
| Dict | `name: dict` | `{}` |

Attributes can have default values:

```
attributes:
    - temp: float = 25.0
    - label: str = 'sensor_a'
    - active: bool = true
    - readings: list = [1, 2, 3]
    - config: dict = {threshold: float, unit: str}
```

### Value Generators

Sensor attributes can define value generators for virtual entity simulation.

```
- temperature: float -> gaussian(10, 20, 5) with noise gaussian(1, 1)
```

Syntax: `-> <Generator> with noise <Noise>` (noise is optional).

**Generator functions:**

| Function | Syntax | Description |
|----------|--------|-------------|
| Constant | `constant(value)` | Fixed value |
| Linear | `linear(start, step)` | Linear ramp |
| Saw | `saw(min, max, step)` | Sawtooth wave |
| Gaussian | `gaussian(value, maxValue, sigma)` | Gaussian distribution |
| Sinus | `sinus(dc, amplitude, step)` | Sinusoidal wave |
| Replay | `replay([v1, v2, ...], times)` | Replay value list (`-1` = infinite) |
| ReplayFile | `replay("filepath")` | Replay from CSV file |

### Noise Functions

| Function | Syntax | Description |
|----------|--------|-------------|
| Uniform | `uniform(min, max)` | Uniform random noise |
| Gaussian | `gaussian(mu, sigma)` | Gaussian random noise |

## Conditions

Conditions evaluate entity attribute values. They are used in `EntityStateCondition` goals via the `when` block.

Attribute references use fully-qualified dot notation: `EntityName.attribute_name`.

### Numeric Conditions

```
TempSensor.temp > 30
TempSensor.temp <= 25.5
TempSensor.temp == 0
```

Operators: `>`, `>=`, `<`, `<=`, `==`, `!=`

Both operands can be attribute references:

```
TempSensor1.temp > TempSensor2.temp
```

### String Conditions

```
StatusSensor.label == 'active'
StatusSensor.label ~ 'act'
StatusSensor.label has 'err'
```

Operators: `~` (contains), `!~` (not contains), `==`, `!=`, `has`, `in`, `not in`

### Boolean Conditions

```
DoorSensor.locked is true
DoorSensor.locked is not false
```

Operators: `is`, `is not`

### List and Dict Conditions

```
SensorA.readings == [1, 2, 3]
SensorA.config != SensorB.config
```

Operators: `==`, `!=`, `is`, `is not`, `in`, `not in` (list only)

### Time Conditions

```
ClockEntity.current > 08:30
```

Operators: `>`, `>=`, `<`, `<=`, `==`, `!=`, `is`, `is not`

### InRange Conditions

```
TempSensor.temp in range [18.0, 26.0]
```

Checks if a numeric attribute falls within a closed interval.

### GoalStatus Conditions

Reference the status of other goals in conditions:

```
Goal_1.status == REACHED
Goal_2.status != FAILED
```

Status values: `PENDING`, `RUNNING`, `REACHED`, `FAILED`, `TIMEOUT`.

### Aggregation Functions

Apply statistical functions over an attribute's value buffer.

```
mean(TempSensor.temp, 10) > 25
std(TempSensor.temp, 5) < 2.0
```

| Function | Syntax | Description |
|----------|--------|-------------|
| `mean` | `mean(attr, N)` | Mean of last N values |
| `std` | `std(attr, N)` | Standard deviation |
| `var` | `var(attr, N)` | Variance |
| `min` | `min(attr, N)` | Minimum value |
| `max` | `max(attr, N)` | Maximum value |

### Condition Groups

Combine conditions with logical operators. Parentheses are required.

```
(TempSensor.temp > 30) AND (HumiditySensor.humidity < 0.5)

((CondA) AND (CondB)) OR (CondC)
```

**Logical operators** (UPPERCASE): `AND`, `OR`, `NOT`, `XOR`, `NOR`, `XNOR`, `NAND`.

Condition groups are binary: chain three-way conditions as `((A) AND (B)) AND (C)`.

## Goals

All goals follow the pattern `Goal<Type> Name ... end`.

### Watch

Reached when any message arrives on the entity's topic, regardless of payload.

```
Goal<Watch> MessageReceived
    entity: TempSensor
    then
        - NextGoal
    config
        description: 'Wait for sensor message'
end
```

### When

Reached when a typed condition evaluates to true.

```
Goal<When> TempAlert
    when
        (TempSensor.temp > 30) AND (HumiditySensor.humidity < 0.5)
    then
        - NextGoal_A
        - NextGoal_B
    config
        timeConstraints:
            - FROM_GOAL_START(<60)
        description: 'Temperature and humidity alert'
end
```

- **when**: Typed condition expression
- **then** (optional): List of goal names to trigger on completion
- **config** (optional): Time constraints and description

### Eval

Uses a Python expression string for conditions that cannot be expressed in the typed condition grammar (e.g., arithmetic on attributes).

```
Goal<Eval> ArithmeticCheck
    when
        'TempSensor.temp * 2 > HumiditySensor.humidity + 10'
    config
        description: 'Arithmetic condition check'
end
```

The condition string is a quoted Python expression.

### Rect

```
Goal<Rect> EnterZone
    entities:
        - Robot1Pose
    bottomLeftEdge: Point3D(0, 0, 0)
    lengthX: 5
    lengthY: 5
    tag: ENTER
    timeConstraints:
        - FROM_GOAL_START(<180)
        - FOR_TIME(5)
end
```

### Circle

```
Goal<Circle> AvoidZone
    entities:
        - Robot1Pose
    center: Point3D(5, 5, 0)
    radius: 3
    tag: AVOID
end
```

### Poly

```
Goal<Poly> CustomZone
    entities:
        - Robot1Pose
    points: [Point2D(0, 0), Point2D(2, 4), Point2D(4, 0)]
    tag: ENTER
end
```

### Shadow

A dynamic area that follows a moving entity.

```
Goal<Shadow> KeepDistance
    movingEntity: Robot1Pose
    entities:
        - Robot2Pose
    radius: 2
    tag: AVOID
end
```

**Area goal tags:** `ENTER`, `EXIT`, `AVOID`, `STEP`.

### Pos

```
Goal<Pos> ReachTarget
    entity: Robot1Pose
    position: Point3D(1, 1, 0)
    maxDeviation: 0.1
    timeConstraints:
        - FROM_GOAL_START(<60)
end
```

### Heading

```
Goal<Heading> FaceNorth
    entity: Robot1Pose
    orientation: Orientation2D(0)
    maxDeviation: 0.05
end
```

### Pose

Combined position and orientation goal.

```
Goal<Pose> PrecisePose
    entity: Robot1Pose
    position: Point3D(1, 1, 0)
    orientation: Orientation2D(0)
    maxDeviationPos: 0.1
    maxDeviationOri: 0.05
end
```

### Trace

```
Goal<Trace> DriveStraight
    entity: Robot1Pose
    startPoint: Point3D(0, 0, 0)
    finishPoint: Point3D(10, 0, 0)
    maxDeviation: 0.5
end
```

### Route

```
Goal<Route> FollowPath
    entity: Robot1Pose
    points: [Point3D(0,0,0), Point3D(1,1,0), Point3D(2,0,0)]
    maxDeviation: 0.5
end
```

### Cluster

Compose multiple goals with an execution strategy.

```
Goal<Cluster> AllChecks
    goals:
        - Goal_1
        - Goal_2
        - Goal_3
    strategy: ALL_ACCOMPLISHED_ORDERED
    config
        xAccomplished: 2
        description: 'All checks must pass in order'
end
```

**Strategies:**

| Strategy | Description |
|----------|-------------|
| `ALL_ACCOMPLISHED` | All goals must be reached |
| `ALL_ACCOMPLISHED_ORDERED` | All goals reached in sequence |
| `NONE_ACCOMPLISHED` | No goals should be reached |
| `AT_LEAST_ONE_ACCOMPLISHED` | At least one goal reached |
| `JUST_ONE_ACCOMPLISHED` | Exactly one goal reached |
| `EXACTLY_X_ACCOMPLISHED` | Exactly X goals reached |
| `EXACTLY_X_ACCOMPLISHED_ORDERED` | Exactly X goals reached in sequence |

`xAccomplished` is required for `EXACTLY_X_*` strategies.

### Loop

Execute a goal multiple times.

```
Goal<Loop> RepeatCheck
    goal: TargetGoal
    times: 10
    config
        description: 'Repeat target goal 10 times'
end
```

## Scenarios

A scenario defines which goals to execute and how.

```
Scenario Verification
    goals:
        - Goal_1 -> 0.5
        - Goal_2 -> 0.3
        - Goal_3 -> 0.2
    antigoals:
        - UnwantedCondition
    fatals:
        - CriticalFailure
    concurrent: true
    tickFreq: 10
    namespace: 'my_app'
    description: 'Main verification scenario'
    timeConstraints:
        - FROM_SCENARIO_START(<300)
end
```

| Property | Required | Description |
|----------|----------|-------------|
| `goals` | yes | Weighted goal list (`goal -> weight`, weight optional) |
| `antigoals` | no | Goals that should NOT be reached |
| `fatals` | no | Goals that abort the scenario if reached |
| `concurrent` | no | `true` for parallel, `false` for sequential (default) |
| `tickFreq` | no | Goal evaluation frequency in Hz |
| `namespace` | no | Namespace for topic scoping |
| `description` | no | Human-readable description |
| `timeConstraints` | no | Scenario-level time constraints |

When weights are omitted, goals are weighted equally.

## Time Constraints

Time constraints limit goal or scenario execution duration.

```
timeConstraints:
    - FROM_GOAL_START(<60)
    - FOR_TIME(5)
    - FROM_SCENARIO_START(<300)
```

| Type | Description |
|------|-------------|
| `FROM_GOAL_START(<N)` | Must complete within N seconds of goal start |
| `FROM_GOAL_START(>N)` | Must take at least N seconds |
| `FROM_SCENARIO_START(<N)` | Must complete within N seconds of scenario start |
| `FOR_TIME(N)` | Must hold true for N seconds |
| `BETWEEN_GOALS_MIN(N)` | Minimum time between sequential goals |
| `BETWEEN_GOALS_MAX(N)` | Maximum time between sequential goals |

Comparators: `>`, `<`, `>=`, `<=`, `==`.

## Geometry Types

**Points:**

```
Point2D(x, y)
Point3D(x, y, z)
```

**Orientations:**

```
Orientation2D(z)        // Yaw only
Orientation3D(x, y, z)  // Roll, pitch, yaw
```

## Imports

Split models across files using imports.

```
import datasources.goal
import entities.goal
```

The import path is relative to the importing file. File extension is included.

## Comments

```
// Single-line comment

/* Multi-line
   comment */
```

## RTMonitor

Optional runtime monitor configuration for event and log publishing.

```
RTMonitor
    source: LocalRedis
    namespace: 'my_app'
    eventTopic: 'goaldsl.{U_ID}.event'
    logsTopic: 'goaldsl.{U_ID}.log'
end
```

Topic strings support environment variable interpolation via `{VAR_NAME}` syntax.
