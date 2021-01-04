# goal-dsl

Domain-Specific Language for evaluation of IoT applications and system behavior, 
based on **Goals**.

The general idea is that we can define goal rules based on messages arrived
at specific topics. For example, a goal may define a rule to wait until receive an event
or a message on a topic.

To expand this idea to the context of Cyber-Physical Systems, beyond
topic-related Goals, it is useful to be able to define environment-related Goals
for mobile things, such as robots. For example, in robotics it is common
to require definition of Goals related to the Pose of the robot, or to follow a trajectory.


**Goal Types**:
- Topic Goals
- Area Goals
- Pose Goals
- Trajectory Goals
- Complex Goal
- Goal Sequence

## Goal Types

### Topic Goals

#### TopicMessageReceivedGoal
This Goal is considered **REACHED** when a message arrives at a specific topic,
without any considerations of the payload of the message.

```
TopicMsgReceivedGoal TopicGoalA -> {
    topic: 'robot.opts.face_detection.detected';
}

TopicMsgReceivedGoal TopicGoalD -> {
    topic: 'env.door.kitchen.opened';
}
```

#### TopicMessageParamGoal
Set this Goal for cases where you want to filter messages arrived at a topic
based on the value of a param (using an expression).

```
TopicMsgParamGoal TopicGoalB -> {
    topic: 'robot.sensor.motion.speed';
    param: 'linVel';
    expression: '> 10';
}

TopicMsgParamGoal TopicGoalC -> {
    topic: 'robot.sensor.motion.speed';
    param: 'angVel';
    expression: '> 10';
}
```

### Area Goals

An **AreaGoal** can be of type `AVOID` (DANGER ZONE) or `REACH` (HAPPY ZONE).
The first defines area goals which have to be avoided by mobile things, while
the latter have to be reached. The type is a property of all area goals.

#### RectangleAreaGoal
A rectangle area defined by (centerPoint, radius) that has to either be reached
or avoided.

```
RectangleAreaGoal GoalA -> {
    centerPoint: Point2D(2.0, 6.0);
    sideLength: 3.0;
    type: REACH;
}
```

#### CircularAreaGoal
A circular area defined by (centerPoint, radius) that has to be either reached
or avoided.

```
CircularAreaGoal GoalB -> {
    centerPoint: Point2D(2.0, 6.0);
    radius: 3.0;
    type: AVOID;
}
```

#### StraightLineAreaGoal
A straight line defined by (startPoint, finishPoint) that has to be either
reached or avoided.

### Pose Goals

Pose goals are those related to the pose of a specific thing.
Mostly used in mobile robot applications.

#### PointGoal
Reach a specific point in space.

#### OrientationGoal
Reach a specific orientation in space.

#### PoseGoal
Reach a specific pose (orientation, position) in space.


### Trajectory Goals

Use this type to define goals for a thing to follow/track a trajectory. Mostly used in mobile robot applications.

#### StraightLineTrajectoryGoal
A straight line trajectory goal, defined by (startPoint, finishPoint,
    maxDeviation).

#### CustomPointsTrajectoryGoal
A straight line trajectory goal, defined by (startPoint, finishPoint,
    trajectoryPoints, maxDeviation).

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

```
ComplexGoal GoalC -> {
    algorithm: ALL_ACCOMPLISHED;
    addGoal(GoalA);
    addGoal(GoalB);
}
```

### Goal Sequence

A number of Goals which have to be accomplished in sequence.

```
Sequence S1 -> {
    addGoal(GoalC);
    addGoal(GoalD);
    addGoal(GoalE);
}
```

## Time Constraints for Goals

Goals can have time constraints, like maximum duration from previous goal.
For this reason we introduce the **TimeConstraint** concept that allows the
definition of the following types of time constraints.

- **FROM_APP_START**
- **FROM_GOAL_START**

An example constraint definition:

```
TConstraint TC1 -> {
    type: FROM_GOAL_START;
    time:  10.0;
    deviation: 1.0;
}
```

Assign time constraint to a goal.

```
ComplexGoal GoalC -> {
    timeConstraint: tc.TC1;
    algorithm: ALL_ACCOMPLISHED;
    addGoal(area_goals.GoalA);
    addGoal(area_goals.GoalB);
}

```

## Target

**Target** defines a set of goals which are assigned to be executed for a
specific target/application.

A **Target** is defined by a list of Goals.

```
import sequence_goal.goal as seq;
import complex_goals.goal as complex;

Target MyAppTarget -> [complex.GoalC, complex.GoalD, complex.GoalE];

Target MyApp2Target -> [seq.S2];

```


## Other Concepts

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
Orientation2D(x, y)

Orientation3D(x, y, z)
```

## Metamodel of the Language

The metamodel of the DSL, defines the concepts of the language.

![bridges_1](./docs/images/GoalDSLMetamodel.png)


## Multiple model files -  Import models

The language supports multi-file models via model imports.
A nested model import layer is implemented, enabling pythonic imports
of models defined in other files.

```
// File area_goals.goal

RectangleAreaGoal GoalA -> {
    centerPoint: Point2D(2.0, 6.0);
    sideLength: 3.0;
    type: REACH;
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

## Thoughts

### AreaRoomGoal
Provide Goal types for semantic declaration of reach or avoid areas,
        for example "enter the kitchen".
Even though this can be achieved using the `AreaGoal` goals, such definitions
will be easier to configure. Though, the environment must somehow post
the current room location of the thing in order to be able to operate. This also
means that the environment must be semantically annotated.

### Add Scoring in Language

Assign score metrics/weights/etc on goals.
Scores can be defined when defining the "Target" goals (Goals which will be used
    for a target).

### Better in-language expressions for TopicMessageParamGoal

Currently a string is passed to the parser.

```
expression: '> 10';
```

### Post assignment of TimeConstraint to Goals

Now time constraints can be statically assigned as a property of each goal.
It would be better to assign these dynamically.

This can be achieved using two approaches:

- Define a GoalContainer for adding to the GoalSequence. GoalContainer will
have a reference to a Goal and a ref to a TimeConstraint. e.g.

```
Sequence S2 -> {
    addGoal(TopicGoalA, TC1);
}

```

- Dynamic assignment that the language must support. e.g.
```
TopicMsgParamGoal TopicGoalB -> {
    topic: 'robot.sensor.motion.speed';
    param: 'linVel';
    expression: '> 10';
}

TopicGoalB.timeConstraint = TC1
```

### Anti-Goals

Support setting every Goal in Anti-Goal mode, meaning that it **MUST NOT BE
ACCOMPLISED**. This can be defined as an optional property of all **Goal** classes.
Or define an AntiGoal class that will wrap all Goal classes and make the
anti-goals.

```
TopicMsgReceivedGoal TopicGoalA -> {
    topic: "robot.opts.face_detection.detected";
    antiGoal: True;
}

```

```
TopicMsgReceivedGoal TopicGoalA -> {
    topic: "robot.opts.face_detection.detected";
}

AntiGoal AntiTopicGoalA(TopicGoalA);

```


**Note**: Currently, Area Goals can be set to 'AVOID' or 'REACHED' mode.

## Examples

An example that covers the complete list of features and of the language can
found [here](./examples/)

# Credits

- [klpanagi](https://github.com/klpanagi)
- [imgchris]()
- [etsardou]()
- [asymeo]()