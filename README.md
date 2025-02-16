GoalDSL is an external Domain-Specific Language (DSL) for the behaviour verification of IoT-enabled CPS applications and systems, based on a goal-driven approach. The general idea is that goal-driven rules can be defined for entities (smart objects, virtual artefacts, etc.) in a CPS, a smart environment or a digital twin.

Goal-driven verification scenarios can be defined based on messages arriving at specific topics of a message broker. For example, a goal may define a rule to wait until receiving a message from the in-house robot or until the temperature in the bedroom reaches a specific value. To expand this idea to the context of Cyber-Physical Systems and Smart Home Automation, beyond topic-related goals, it is useful to be able to define goals for mobile smart objects (e.g. robots) and for monitoring the state of smart objects and act on them. For example, in robotics it is common to require definition of goals related to the pose of the robot, or to follow a trajectory, to pass from a specific point or reach a destination target. Concerning smart home specific goals, the language supports goals which monitor the attribute values of entities. In a nutshell, our approach can be used to verify that the implementation meets expected functional standards, regarding application development for smart environments.

# Table of contents
- [Table of contents](#table-of-contents)
  - [Installation ](#installation-)
  - [Features](#features)
  - [Usage](#usage)
  - [Data Sources](#data-sources)
  - [Message Broker](#message-broker)
    - [Entities](#entities)
      - [Definition of attribute functions for virtual/digital entities](#definition-of-attribute-functions-for-virtualdigital-entities)
    - [Conditions](#conditions)
      - [Condition Formatting:](#condition-formatting)
      - [Lists and Dictionaries:](#lists-and-dictionaries)
      - [Operators](#operators)
      - [Build-in simple aggregation functions](#build-in-simple-aggregation-functions)
      - [Writing Conditions](#writing-conditions)
    - [Entity Goals](#entity-goals)
      - [EntityStateChange](#entitystatechange)
      - [EntityStateCondition](#entitystatecondition)
    - [Area Goals](#area-goals)
      - [Rectangle Area](#rectangle-area)
      - [Circular Area](#circular-area)
      - [Polyline Area](#polyline-area)
      - [Mobile Area](#mobile-area)
    - [Pose Goals](#pose-goals)
      - [PositionGoal](#positiongoal)
      - [OrientationGoal](#orientationgoal)
      - [PoseGoal](#posegoal)
    - [Trajectory Goals](#trajectory-goals)
      - [WaypointTrajectoryGoal](#waypointtrajectorygoal)
    - [Complex Goals](#complex-goals)
  - [Time Constraints ](#time-constraints-)
  - [Scenario ](#scenario-)
  - [Other Concepts of the Language ](#other-concepts-of-the-language-)
    - [Point](#point)
    - [Orientation](#orientation)
  - [Import](#import)
  - [Validation ](#validation-)
  - [Code Generation ](#code-generation-)
  - [Examples ](#examples-)
  - [Extra ](#extra-)


## Installation <a name="installation"></a>

Download this repository and simply install using `pip` package manager.

```
git clone https://github.com/robotics-4-all/goal-dsl
cd goal-dsl
pip install .
```

## Features

- **Declarative Syntax**: Define goals and their relationships in a clear and concise manner.
- **Extensible**: Easily add custom goals and actions to fit your specific use case.
- **Integration-Friendly**: Designed to work seamlessly with robotics frameworks and middleware.
- **Human-Readable**: Goals are defined in a way that is easy to understand and maintain.

Currently the DSL supports the following types of goals

- **Entity Goals**
    - EntityStateChange
    - EntityStateCondition
- **Area Goals**
    - RectangleArea
    - CircularArea
    - PolylineArea
    - MovingArea
- **Pose Goals**
    - PositionGoal
    - OrientationGoal
    - PoseGoal
- **Trajectory Goals**
    - StraightLineTrajectoryGoal
    - WaypointTrajectoryGoal
- **Complex Goal**

## Usage


## Data Sources

**TBD!!**

## Message Broker

The Broker acts as the communication layer for messages where each device has
its own Topic which is basically a mailbox for sending and receiving messages.
SmartAutomation DSL supports Brokers which support the MQTT, AMQP and Redis
protocols. You can define a Broker using the syntax in the following example:

```
Broker<MQTT> HomeMQTT
    host: 'localhost'
    port: 1883
    auth:
        username: ''
        password: ''
end
```

```
Broker<Redis> LocalRedis
    host: 'localhost'
    port: 6379
    ssl: false
    auth:
        username: ''
        password: ''
end
```

- **host**: Host IP address or hostname for the Broker
- **port**: Broker Port number
- **auth**: Authentication credentials. Unified for all communication brokers
    - **username**: Username used for authentication
    - **password**: Password used for authentication
- **vhost (Optional)**: Vhost parameter. Only for AMQP brokers
- **ssl (Optional)**: Enable/Disable ssl channel encryption
- **topicExchange (Optional)**: (Optional) Exchange parameter. Only for AMQP brokers
- **rpcExchange (FUTURE SUPPORT)**: Exchange parameter. Only for AMQP brokers
- **db (Optional)**: Database number parameter. Only for Redis brokers


### Entities

Entities are your connected smart devices that send and receive information using a message broker. Entities have the following required properties:

- A unique name
- A data source to connect (e.g. Message Broker, REST Service, DB Entry etc)
- A URI to send/receive messages
- A number of Attributes, which define the Data Model of the Entity

**Attributes** are what define the structure and the type of information in the messages the Entity sends to the communication broker.

Entity definitions follow the syntax of the below examples, for both sensor and actuator types. The difference between the two is that sensors are considered "Producers" while actuators are "Consumers" in the environment. Sensor Entities have an extra property, that is the `freq` to set the publishing frequency of either physical or virtual.

```
Entity TempSensor1
    type: sensor
    topic: 'bedroom.temperature'
    source: MyMQTTBroker
    attributes:
        - temp: float
end
```

```
Entity bedroom_lamp
    type: actuator
    topic: "bedroom.lamp"
    source: cloud_platform_issel
    attributes:
        - power: bool
end
```

```
Entity Robot1Pose
    type: sensor
    topic: 'robot_1.pose'
    source: HomeMQTT
    attributes:
        - position: dict
        - orientation: dict
end
```



- **type**: The Entity type. Currently supports `sensor`, `actuator` or `hybrid`
- **topic**: The Topic in the Broker used by the Entity to send and receive
messages. Note that / should be substituted with .
(e.g: bedroom/aircondition -> bedroom.aircondition).
- **source**: The name property of a previously defined Data Source (e.g. Broker) which the
Entity uses to communicate.
- **attributes**: Attributes have a name and a type. As can be seen in the above
example, HA-Auto supports int, float, string, bool, list and dictionary types.
Note that nested dictionaries are also supported.
- **description (Optional)**: A description of the Entity
- **freq (Optional)**: Used for Entities of type "**sensor**" to set the msg publishing rate

Notice that each Entity has it's own reference to a Broker, thus the metamodel
allows for communicating with Entities which are connected to different message
brokers. This allows for definining automation for multi-broker architectures.

Supported data types for Attributes:

- **int**: Integer numerical values
- **float**: Floating point numerical values
- **bool**: Boolean (true/false) values
- **str**: String values
- **time**: Time values (e.g. `01:25`)
- **list**: List / Array
- **dict**: Dictionary

#### Definition of attribute functions for virtual/digital entities

SmAuto provides a code generator which can be utilized to transform Entities models
into executable source code in Python.
This feature of the language enables end-to-end generation of the objects (sensors, actuators, robots)
which send and receive data based on their models. Thus it can be used to
generate while virtual smart environments and directly dig into defining and
testing automations.

For this purpose, the language supports (Optional) definition of a `Value Generator` and a `Noise` to be applied on each attribute of an Entity of type **sensor** separately.

```
Entity weather_station
    type: sensor
    freq: 5
    topic: "smauto.bme"
    source: home_mqtt_broker
    attributes:
        - temperature: float -> gaussian(10, 20, 5) with noise gaussian(1,1)
        - humidity: float -> linear(1, 0.2) with noise uniform (0, 1)
        - pressure: float -> constant(0.5)
end
```

The above example utilizes this feature of the language. Each attribute can define
it's own value and noise generators, using a simple grammar as evident below:

```
-> <ValueGenerator> with noise <NoiseGenerator>
```

**Supported Value Generators:**

- **Constant**: `constant(value)`. Constant value
- **Linear**: `linear(min, step)`. Linear function
- **Saw**: `saw(min, max, step)`. Saw function.
- **Gaussian**: `gaussian(value, maxValue, sigma)`. Gaussian function
- **Replay**: `replay([values], times)`. Replay from a list of values. The `times` parameter can be used to force replay iterations to a specific value. If `times=-1` then values will be replayed infinitely.
- **ReplayFile**: `replayFile("FILE_PATH")`. Replay data from a file.


**Supported Noise Generators:**

- **Uniform**: `uniform(min, max)`.
- **Gaussian**: `gaussian(mean, sigma)`.

Value generation and Noise are optional in the language and are features used
by the Virtual Entity generator to transform Entity models into executable code.

![SmAutoValueGenA](assets/images/Smauto_ValueGen_1.png)


### Conditions

Conditions are very similar to conditions in imperative programming languages
such as Python, Java, C++ or JavaScript. You can use Entity Attributes in a
condition just like a variable by referencing it in the Condition using
it's Fully-Qualified Name (FQN) in dot (.) notation.

```
entity_name.attribute_name
```

<!-- ![ConditionMM](assets/images/SmAutoConditionMM.png) -->


#### Condition Formatting:

You can combine two conditions into a more complex one using logical operators.
The general format of the Condition is:

`(condition_1) <LOGICAL_OP> (condition_2)`

Make sure to not forget the parenthesis.

`(condition_1) AND (condition_2) AND (condition_3)`


#### Lists and Dictionaries:

The language has support for Lists and Dictionaries and even nesting them.
However, for now the use of lists and dictionaries in conditions are treated
as full objects and their individual elements cannot be accessed and used in
conditions. This means that you can compare a List to a full other List, but
cannot compare individual list items. Similarly, you can compare a full
dictionary to another but cannot use individual dictionary items in conditions.

Nested in-language reference to Dict and List items will be supported in a future release
of the language.

#### Operators

- String Operators: `~`, `!~`, `==`, `!=`, `has`
- Numeric Operators: `>`, `>=`, `<`, `<=`, `==`, `!=`
- Logical Operators: `and`, `or`, `not`, `xor`, `nor`, `xnor`, `nand`
- BooleanValueOperator: `is` , `is not`;
- List and Dictionary Operators: `==`, `!=`

#### Build-in simple aggregation functions

The language provides buildi-in functions which can be applied to attribute references
when defining a Condition.

```
condition:
    condition: (mean(TempSensor1.temp, 5) > 0.5 ) and
        (std(TempSensor2.temp, 3) < 1)

condition:
    condition: TempSensor1.temp * 2 > TempSensor2.temp + 1

condition:
    var(mean(TempSensor1.temp, 10), 10) >= 0.1
```


**Supported Functions:**

- **mean**: The mean of the attribute buffer
- **std**: The standard deviation of the attribute buffer
- **var**: The variance of the attribute buffer
- **min**: The minimum value in the attribute buffer
- **max**: The maximum value in the attribute buffer

#### Writing Conditions

Bellow you will find some example conditions.

```
AirQualitySensor1.gas <= 25
```
```
(TempSensor1.temp > 10) and
    (TempSensor2.temp > 10) and
    (TempSensor2.temp - TempSensor1.temp < 2)
```


### Entity Goals

#### EntityStateChange
This Goal is considered **REACHED** when a message arrives at a specific topic,
without any considerations of the payload of the message.

```
Goal<EntityStateChange> Goal_1
    entity: TempSensor1
end

```

#### EntityStateCondition
Set this Goal for cases where you want to filter messages arrived at a topic
based on an exppression.

```
Goal<EntityStateCondition> Goal_2
    condition:
        (AirQualitySensor1.gas < 10) AND (AirQualitySensor1.humidity < 30)
end

Goal<EntityStateCondition> Goal_3
    condition: ((TempSensor1.temp > 10) AND (TempSensor2.temp > 10))
        AND (TempSensor3.temp > 10)
end

Goal<EntityStateCondition> Goal_4
    condition:
        (mean(TempSensor1.temp, 10) > 0.5 ) AND
            (mean(TempSensor2.temp, 10) > 30)
end
```


### Area Goals

An **AreaGoal** is related areas in the environment which have a meaning for an
application. An example would be the avoidance of specific areas. All Area Goals
have a tag that gives a meaning to the goal

**Tag**:
- AVOID
- ENTER
- EXIT
- STEP


The first defines area goals which have to be avoided by mobile things, while
the latter an area that has to be "entered". All Area Goals have a `tag`
property.

#### Rectangle Area
A rectangle area defined by (centerPoint, radius) that has to either be reached
or avoided.

```
Goal<RectangleArea> Goal_1
    entities:
        - Robot1Pose
    bottomLeftEdge: Point3D(0, 0, 0)
    lengthX: 5
    lengthY: 5
    tag: ENTER
    timeConstraints:
        - FOR_TIME(5)
        - FROM_GOAL_START(<180)
end
```

Where:
- entities (Optional): List of Entities to monitor. If no entities are defined then it will monitor all included in the model Entities.
- bottomLeftEdge: The bottom left point of the rectangle to build the area
- lengthX: The length of the rectangle on the X axis
- lengthY: The length of the rectangle on the Y axis
- timeConstraints: List of time constraints (see relevant section)
- tag: `ENTER` or `AVOID`

#### Circular Area
A circular area defined by (centerPoint, radius).

```
Goal<CircularArea> Goal_2
    center: Point3D(5, 5, 0)
    radius: 5
    tag: AVOID
end
```

Where:
- entities (Optional): List of Entities to monitor. If no entities are defined then it will monitor all included in the model Entities.
- center: The center of the circle to build the area
- radius: The radius of the circle
- timeConstraints: List of time constraints (see relevant section)
- tag: `ENTER` or `AVOID`

#### Polyline Area

**UNDER DEVELOPMENT!!**

A polyline area defined by a list of Points.

```
Goal<PolylineArea> GoalC
    entity: my_robot
    points: [Point2D(0.0, 0.0), Point2D(2.0, 4.0), Point2D(4.0,  0.0)]
    tag: AVOID
end
```


#### Mobile Area
This type of Goal can be used for mobile objects, such as robots.

```
Entity Robot2Pose
    type: sensor
    topic: 'robot_2.pose'
    source: HomeMQTT
    attributes:
        - position: dict
        - orientation: dict
end

Goal<MovingArea> Goal_1
    movingEntity: Robot1Pose
    entities:
        - Robot2Pose
    radius: 2
    tag: AVOID
end
```


### Pose Goals

Pose goals are those related to the pose of a specific thing.
Mostly used in mobile robot applications.

#### PositionGoal
Reach a specific position in space.

```
Goal<Position> Goal_3
    entity: RobotArmPose
    position: Point3D(0, 0, 0)
    maxDeviation: 0.1
    timeConstraints:
        - FROM_GOAL_START(<60)
end

Goal<Position> Goal_1
    entity: Robot1Pose
    position: Point3D(1, 1, 0)
    maxDeviation: 0.1
end
```

#### OrientationGoal
Reach a specific orientation in space.

```
Goal<Orientation> Goal_2
    entity: Robot2Pose
    orientation: Orientation2D(1)
    maxDeviation: 0.1
end
```

#### PoseGoal
Reach a specific pose (orientation, position) in space.

```
Goal<Pose> Goal_1
    entity: Robot2Pose
    orientation: Orientation2D(1)
    position: Point3D(1, 1, 0)
    maxDeviationOri: 0.1
    maxDeviationPos: 1
end
```

### Trajectory Goals

Use this type to define goals for a thing to follow/track a trajectory. Mostly used in mobile robot applications.

<!-- #### StraightLineTrajectoryGoal
A straight line trajectory goal, defined by (startPoint, finishPoint,
    maxDeviation). -->

#### WaypointTrajectoryGoal
A custom trajectory goal, defined by (list of points, maxDeviation).

### Complex Goals

The **ComplexGoal** is used to defined goals which are a collection of goals.
For example, using complex goals, we can define a collection of Goals, from
which at least one has to be accomplished.

Below are the possible types of algorithms to apply for a ComplexGoal
definition.

- **ALL_ACCOMPLISHED**
- **ALL_ACCOMPLISHED_ORDERED**
- **NONE_ACCOMPLISHED**
- **AT_LEAST_ONE**
- **EXACTLY_X_ACCOMPLISHED**
- **EXACTLY_X_ACCOMPLISHED_ORDERED**

```
Goal<EntityStateChange> Goal_1
    entity: TempSensor1
end

Goal<EntityStateCondition> Goal_2
    condition:
        (AirQualitySensor1.gas < 10) AND
        (AirQualitySensor1.humidity < 30)
end

Goal<EntityStateCondition> Goal_3
    condition: ((TempSensor1.temp > 10) AND (TempSensor2.temp > 10))
        AND (TempSensor3.temp > 10)
end

Goal<Complex> CG1
    goals:
        - Goal_1
        - Goal_2
        - Goal_3
    strategy: ALL_ACCOMPLISHED_ORDERED
end
```

In case of Ordered algorithms, which is the cases of `ALL_ACCOMPLISHED_ORDERED`,
`EXACTLY_X_ACCOMPLISHED_ORDERED`, the execution of inner Goals is sequential.


## Time Constraints <a name="timeconstraints"></a>

Goals can have time constraints, like maximum duration from previous goal.
For this reason we introduce the **TimeConstraint** concept, which allows the definition of time constraints.

```
Goal<EntityStateCondition> Goal_3
    condition:
        (TemperatureSensorList.regionA < 20) AND
        (HumiditySensorList.regionA < 0.8)
    timeConstraints:
        - FROM_GOAL_START(<1800)
end
```

In the above example the constraint indicates that **The duration of the Goal must not exceed 10 seconds**.

Each TimeConstraint can measure time relative to either the start of
the application or the start of the current goal. This can be defined using the
`type` property of **TimeConstraint** classes and can have one of the following
values.

- **FROM_APP_START**
- **FROM_GOAL_START**

The `expression` can use one of the values `>`, `<`, `>=`, `<=` and `==`.


## Scenario <a name="scenario"></a>

**Scenario** defines a set of goals which are assigned to be executed for a
specific target/application. A scenario needs to be linked to a specific
middleware (message broker),

A **Scenario** is defined by a list of Goals and a communication middleware.

```
Scenario ScenarioB
    goals:
        - Goal_1 -> 0.2
        - Goal_2 -> 0.2
        - Goal_3 -> 0.2
        - Goal_4 -> 0.2
        - Goal_5 -> 0.2
    concurrent: false
end
```

A scenario can have multiple Goals, which are executed **concurrently** or in a **sequential** order. This is defined for each scenario via the **concurrent** property.


## Other Concepts of the Language <a name="other"></a>

### Point

In order to be able to define points in 2D and 3D space, the **Point2D** and
**Point3D** classes are introduced.

The syntax for defining a Point.

```
Point2D(x, y)

Point3D(x, y, z)
```

### Orientation

In order to be able to define the orientation of things in 2D and 3D space,
   the **Orientation2D** and **Orientation3D** classes are introduced.

The syntax for defining a Point.

```
Orientation2D(z)  // In 2D space only zAxes rotation is allowed.

Orientation3D(x, y, z)
```


## Import

The language supports multi-file models via model imports.
A nested model import layer is implemented, enabling pythonic imports
of models defined in other files.

```
// File datasources.goal

Broker<MQTT> MyMQTTBroker
    host: 'localhost'
    port: 1883
    auth:
        username: ''
        password: ''
end

```

```
// File entities.goal

import datasources.goal

Entity TempSensor1
    type: sensor
    topic: 'bedroom.temperature'
    source: MyMQTTBroker
    attributes:
        - temp: float
end

Entity TempSensor2
    type: sensor
    topic: 'bathroom.temperature'
    source: MyMQTTBroker
    attributes:
        - temp: float
end

Entity TempSensor3
    type: sensor
    topic: 'livingroom.temperature'
    source: MyMQTTBroker
    attributes:
        - temp: float
end

Entity AirQualitySensor1
    type: sensor
    topic: 'kitchen.airq'
    source: MyMQTTBroker
    attributes:
        - gas: float
        - humidity: float
end
```

```
// File scenario.goal

import entities.goal

Goal<EntityStateChange> Goal_1
    entity: TempSensor1
end

Goal<EntityStateCondition> Goal_2
    condition: mean(TempSensor1.temp, 5) > 10
end

Goal<EntityStateCondition> Goal_3
    condition: mean(TempSensor1.temp, 10) > 10
end

Goal<EntityStateCondition> Goal_4
    condition: (mean(TempSensor1.temp, 5) > 0.5 ) and
        (std(TempSensor2.temp, 3) < 1)
end

Goal<EntityStateCondition> Goal_5
    condition: TempSensor1.temp * 2 > 10
end

Goal<EntityStateCondition> Goal_6
    condition: TempSensor1.temp * 2 > TempSensor2.temp + 1
end

Scenario MyScenario
    goals:
        - Goal_1
        - Goal_2
        - Goal_3
        - Goal_4
        - Goal_5
    concurrent: True
end
```


## Validation <a name="validation"></a>

Validation is perfomed using either the CLI or the REST API of the DSL.

In the case of the CLI, `validate` is a subcommand of `goaldsl`.

To validate a GoalDSL model file, execute:

```bash
goaldsl validate scenario.goal
```

If the model passes the validation rules (grammar) you should see something
like:

```bash
[I] ➜ goaldsl validate scenario.goal
target.goal: OK.
```


## Code Generation <a name="generation"></a>

Code generation is perfomed using either the CLI or the REST API of the DSL.

In the case of the CLI, `gen` is a subcommand of `goaldsl`.


To generate the source code of a GoalDSL model, execute:

```bash
goaldsl gen scenario.goal
```

## Examples <a name="examples"></a>

Several examples of usage can be found under the [examples directory](./examples/) of this repository.

## Extra <a name="extra"></a>

* [goal-dsl.vim](https://github.com/johnstef99/goal-dsl.vim) Vim syntax support for goal-dsl
