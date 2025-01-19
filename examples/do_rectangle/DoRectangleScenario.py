#!/usr/bin/env python3

import os
from statistics import stdev as std, mean as mean, variance as var

from goalee import Scenario, RedisBroker, MQTTBroker, AMQPBroker
from goalee.entity import Entity
from goalee.types import Point, Orientation
from goalee.area_goals import (
    RectangleAreaGoal,
    CircularAreaGoal,
    MovingAreaGoal,
    AreaGoalTag
)
from goalee.complex_goal import (
    ComplexGoal,
    ComplexGoalAlgorithm
)
from goalee.entity_goals import (
    EntityStateChange,
    EntityStateCondition
)
from goalee.pose_goals import (
    PoseGoal,
    PositionGoal,
    OrientationGoal
)

entities_list = []

Robot1Pose = Entity(
    name='Robot1Pose',
    etype='sensor',
    topic='gn_robot_1.pose.internal',
    attributes=['position', 'orientation'],
    source=RedisBroker(
        host='localhost',
        port=6379,
        db=0,  # default DB number is 0
        username='',
        password='',
    )
,
)
entities_list.append(Robot1Pose)


if __name__ == '__main__':
    broker = None

    scenario = Scenario(
        name='DoRectangleScenario',
        broker=broker,
        score_weights=[0.25, 0.25, 0.25, 0.25]
    )

    g = CircularAreaGoal(
        name='Goal_1',
        entities=[Robot1Pose],
        center=Point(100, 5, 0),
        radius=0.5,
        tag=AreaGoalTag.ENTER,
        max_duration=None,
        min_duration=None,
    )

    scenario.add_goal(g)
    g = CircularAreaGoal(
        name='Goal_2',
        entities=[Robot1Pose],
        center=Point(100, 10, 0),
        radius=0.5,
        tag=AreaGoalTag.ENTER,
        max_duration=None,
        min_duration=None,
    )

    scenario.add_goal(g)
    g = CircularAreaGoal(
        name='Goal_3',
        entities=[Robot1Pose],
        center=Point(95, 10, 0),
        radius=0.5,
        tag=AreaGoalTag.ENTER,
        max_duration=None,
        min_duration=None,
    )

    scenario.add_goal(g)
    g = CircularAreaGoal(
        name='Goal_4',
        entities=[Robot1Pose],
        center=Point(95, 5, 0),
        radius=0.5,
        tag=AreaGoalTag.ENTER,
        max_duration=None,
        min_duration=None,
    )

    scenario.add_goal(g)


    scenario.run_seq()
