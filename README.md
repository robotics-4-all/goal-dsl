#.
GoalDSL is an external Domain-Specific Language (DSL) for the behaviour verification of IoT-enabled CPS applications and systems, based on a goal-driven approach. The general idea is that goal-driven rules can be defined for entities (smart objects, virtual artefacts, etc.) in a CPS, a smart environment or a digital twin.

Goal-driven verification scenarios can be defined based on messages arriving at specific topics of a message broker. For example, a goal may define a rule to wait until receiving a message from the in-house robot or until the temperature in the bedroom reaches a specific value. To expand this idea to the context of Cyber-Physical Systems and Smart Home Automation, beyond topic-related goals, it is useful to be able to define goals for mobile smart objects (e.g. robots) and for monitoring the state of smart objects and act on them. For example, in robotics it is common to require definition of goals related to the pose of the robot, or to follow a trajectory, to pass from a specific point or reach a destination target. Concerning smart home specific goals, the language supports goals which monitor the attribute values of entities. In a nutshell, our approach can be used to verify that the implementation meets expected functional standards, regarding application development for smart environments.

# Table of contents
1. [Installation](#installation)
2. [Goal Types](#goaltypes)
3. [Time Constraints for Goals](#timeconstraints)
4. [Communication Middleware / Message Broker](#middleware)
5. [Scenario](#scenario)
6. [Other Concepts of the Language](#other)
7. [Multiple model files -  Import models](#multifile)
8. [Validation](#validation)
8. [Code Generation](#generation)
9. [Metamodel](#metamodel)
10. [Examples](#examples)
11. [Extra](#extra)


## Installation <a name="installation"></a>

Download this repository and simply install using `pip` package manager.

```
git clone https://github.com/robotics-4-all/goal-dsl
cd goal-dsl
pip install .
```

### Entities

Entities are your connected smart devices that send and receive information
using a message broker. Entities have the following required properties:

- A unique name
- A broker to connect to
- A topic to send/receive messages
- A set of attributes

**Attributes** are what define the structure and the type of information in the
messages the Entity sends to the communication broker.

Entity definitions follow the syntax of the below examples, for both sensor and actuator types. The difference between the two is that sensors are considered "Producers" while actuators are "Consumers" in the environment. Sensor Entities have an extra property, that is the `freq` to set the publishing frequency of either physical or virtual.

```
Entity weather_station
    type: sensor
    freq: 5
    topic: "bedroom.weather_station"
    source: cloud_broker
    attributes:
        - temperature: float
        - humidity: float
        - pressure: float
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

- **type**: The Entity type. Currently supports `sensor`, `actuator` or `hybrid`
- **topic**: The Topic in the Broker used by the Entity to send and receive
messages. Note that / should be substituted with .
(e.g: bedroom/aircondition -> bedroom.aircondition).
- **broker**: The name property of a previously defined Broker which the
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

#### Attribute value generation for virtual Entities

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

`(condition_1) LOGICAL_OP (condition_2)`

Make sure to not forget the parenthesis.

`condition_1 AND condition_2 AND condition_3`

will have to be rephrased to an equivalent like:

`((condition_1) AND (condition_2)) AND (condition_3)`


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

#### Build-in attribute processing functions

The language provides buildi-in functions which can be applied to attribute references
when defining a Condition.

```
condition:
    (mean(bedroom_temp_sensor.temperature, 10) > 28) and
    (std(bedroom_temp_sensor.temperature, 10) > 1)

condition:
    bedroom_humidity_sensor.humidity in range(30, 60)

condition:
    bedroom_temp_sensor.temperature in range(24, 26) and
    bedroom_humidity_sensor.humidity in range(30, 60)

condition:
    var(mean(bedroom_temp_sensor.temperature, 10), 10) >= 0.1
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
(bedroom_humidity.humidity < 0.3) AND (bedroom_humidifier.state == 0)

((bedroom_human_detector.position != []) AND
    (bedroom_thermometer.temperature < 27.5)
) AND (bedroom_thermostat.state == 0)
```

## Goal Types <a name="goaltypes"></a>

- **Entity Goals**
    - EntityStateChange
    - EntityStateCondition
- **Area Goals**
    - RectangleArea
    - CircularArea
    - PolylineArea
    - StraightLineArea
    - MovingArea
- **Pose Goals**
    - PositionGoal
    - OrientationGoal
    - PoseGoal
- **Trajectory Goals**
    - StraightLineTrajectoryGoal
    - StraightLineTrajectoryGoal
- **Complex Goal**


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
Goal<RectangleArea> GoalA
    entity: my_robot
    bottomLeftEdge: Point2D(2.0, 6.0)
    lengthX: 3.0
    lengthY: 4.0
    tag: ENTER
end
```

#### Circular Area
A circular area defined by (centerPoint, radius).

```
Goal<CircularArea> GoalB
    entity: my_robot
    center: Point2D(2.0, 6.0)
    radius: 3.0
    tag: AVOID
end
```

#### Polyline Area
A polyline area defined by a list of Points.

```
Goal<PolylineArea> GoalC
    entity: my_robot
    points: [Point2D(0.0, 0.0), Point2D(2.0, 4.0), Point2D(4.0,  0.0)]
    tag: AVOID
end
```

#### Straight Line
A straight line in the environment, defined by (startPoint, finishPoint) that has to be either reached or avoided.

```
Goal<StraightLine> GoalD
    entity: my_robot
    startPoint: Point2D(2.0, 7.6);
    endPoint: Point2D(2.0, 7.6);
    tag: AVOID;
end
```

#### Mobile Area
This type of Goal can be used for mobile objects, such as robots.

```
Goal<MobileArea> GoalD
    radius: 46;  // 46cm
    tag: AVOID;
}
```


### Pose Goals

Pose goals are those related to the pose of a specific thing.
Mostly used in mobile robot applications.

#### PositionGoal
Reach a specific position in space.

```
Goal<Position> Goal_5
    entity: RobotArmPose
    position: Point3D(0, 0, 0)
    maxDeviation: 0.1
    timeConstraints:
        - FROM_GOAL_START(<60)
end
```

#### OrientationGoal
Reach a specific orientation in space.

```
Goal<Orientation> Goal_5
    orientation: Orientation2D(1.0);  // rad
    maxDeviation: 0.2; // rad
end
```

#### PoseGoal
Reach a specific pose (orientation, position) in space.

```
PoseGoal ExamplePoseGoal -> {
    position: Point2D(0.0, 0.0);
    orientation: Orientation2D(1.0);  // rad?
    maxDeviationPos: 0.2;
    maxDeviationOri: 0.2;
}
```

### Trajectory Goals

Use this type to define goals for a thing to follow/track a trajectory. Mostly used in mobile robot applications.

#### StraightLineTrajectoryGoal
A straight line trajectory goal, defined by (startPoint, finishPoint,
    maxDeviation).

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


## Communication Middleware / Message Broker <a name="middleware"></a>

The Broker acts as the communication layer for messages where each device has
its own Topic which is basically a mailbox for sending and receiving messages.
SmartAutomation DSL supports Brokers which support the MQTT, AMQP and Redis
protocols. You can define a Broker using the syntax in the following example:

```
Broker<MQTT> hassio_mqtt
    host: "localhost"
    port: 1883
    auth:
        username: "my_username"
        password: "my_password"
end
```

- **type**: The first line can be `MQTT`, `AMQP` or `Redis` according to the broker type
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
    broker: MyMQTTBroker
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


## Multiple model files -  Import models <a name="multifile"></a>

The language supports multi-file models via model imports.
A nested model import layer is implemented, enabling pythonic imports
of models defined in other files.

```
// File area_goals.goal

RectangleAreaGoal GoalA -> {
    centerPoint: Point2D(2.0, 6.0);
    sideLength: 3.0;
    type: ENTER;
}

CircularAreaGoal GoalB -> {
    centerPoint: Point2D(2.0, 6.0);
    radius: 3.0;
    type: AVOID;
}
```

```
// File complex_goals.goal

// area_goals.goal file exists in current directory.
// Includes GoalA and GoalB goals
import area_goals.goal as area_goals;

ComplexGoal GoalC -> {
    algorithm: ALL_ACCOMPLISHED;
    addGoal(area_goals.GoalA);
    addGoal(area_goals.GoalB);
}
```


## Validation <a name="validation"></a>

To validate a model description file, simply execute:

```
textx check target.goal --language goal_dsl
```

If the model passes the validation rules (grammar) you should see something
like:

```
[I] ➜ textx check target.goal --language goal_dsl
target.goal: OK.
```


## Code Generation <a name="generation"></a>

The code-generator is shipped as a separate package which you will have to
manually install. Once installed, it will be listed in **textx generators**
and can be used via the textx cli.

Install Goal-DSL python source generator from: https://github.com/robotics-4-all/goal-gen

Then execute the following command:

```
textx generate target.goal --target goalee
```

## Metamodel <a name="metamodel"></a>

The abstract metamodel of the DSL, that defines the concepts, their relations and top-level constraints, is shown below.

![bridges_1](./docs/images/GoalDSLMetamodel.png)


## Examples <a name="examples"></a>

Several examples can be found [here](./examples/).

## Extra <a name="extra"></a>

* [goal-dsl.vim](https://github.com/johnstef99/goal-dsl.vim) Vim syntax support for goal-dsl
