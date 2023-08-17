#!/usr/bin/env python3

from goalee import Target, Redisbroker
from goalee.topic_goals import *
from goalee.area_goals import *
from goalee.complex_goal import *
from goalee.types import Point


if __name__ == '__main__':
    {% if broker.__class__.__name__ == 'AMQPBroker' %}
    broker = AMQPbroker()
    {% elif broker.__class__.__name__ == 'RedisBroker' %}
    broker = Redisbroker()
    {% endif %}
    t = Target(
        name='{{ target.name }}',
        broker=broker,
        score_weights={{ target.scoreWeights }}
    )

    {% for goal in goals %}
    {% if goal.__class__.__name__ == 'EntityStateConditionGoal' %}
    g = EntityStateConditionGoal(
        condition={{goal.cond_lambda}},
        duration=({{ goal.min_duration }}, {{ goal.max_duration }}),
    )

    {% elif goal.__class__.__name__ == 'EntityStateChangeGoal' %}
    g = EntityStateChangeGoal(
        topic='{{ goal.entity.topic }}',
        name='{{ goal.name }}',
        duration=({{ goal.min_duration }}, {{ goal.max_duration }}),
    )
    {% elif goal.__class__.__name__ == 'WaypointTrajectoryGoal' %}
    g = WaypointTrajectoryGoal(
        topic='{{ goal.entity.topic }}',
        points=[
            {% for point in goal.points %}
            Point({{ point.x }}, {{ point.y }}, {{ point.z }}),
            {% endfor %}
        ],
        deviation={{ goal.maxDeviation }},
        duration=({{ goal.min_duration }}, {{ goal.max_duration }}),
    )
    {% elif goal.__class__.__name__ == 'PositionGoal' %}
    g = PositionGoal(
        topic='{{ goal.entity.topic }}',
        point=Point({{ goal.point.x }}, {{ goal.point.y }}, {{ goal.point.z }}),
        deviation={{ goal.maxDeviation }},
        duration=({{ goal.min_duration }}, {{ goal.max_duration }}),
    )
    {% elif goal.__class__.__name__ == 'ComplexGoal' %}
    g = ComplexGoal(
        {% if goal.algorithm.__class__.__name__ == 'ALL_ACCOMPLISHED'%}
        algorithm=ComplexGoalAlgorithm.ALL_ACCOMPLISHED,
        {% elif goal.algorithm.__class__.__name__ == 'NONE_ACCOMPLISHED'%}
        algorithm=ComplexGoalAlgorithm.NONE_ACCOMPLISHED,
        {% endif %}
        duration=({{ goal.min_duration }}, {{ goal.max_duration }}),
    )
    {% for goal in goal.goals %}
    {% if goal.__class__.__name__ == 'EntityStateConditionGoal' %}
    g = EntityStateConditionGoal(
        condition={{goal.cond_lambda}},
        duration=({{ goal.min_duration }}, {{ goal.max_duration }}),
    )

    {% elif goal.__class__.__name__ == 'EntityStateChangeGoal' %}
    g = EntityStateChangeGoal(
        topic='{{ goal.entity.topic }}',
        duration=({{ goal.min_duration }}, {{ goal.max_duration }}),
    )
    {% elif goal.__class__.__name__ == 'WaypointTrajectoryGoal' %}
    g = WaypointTrajectoryGoal(
        topic='{{ goal.entity.topic }}',
        points=[
            {% for point in goal.points %}
            Point(point.x, point.y, point.z),
            {% endfor %}
        ],
        deviation={{ goal.maxDeviation }},
        duration=({{ goal.min_duration }}, {{ goal.max_duration }}),
    )
    {% endif %}
    g.add_goal(gs)
    {% endfor %}
    ## More Goals to Generate here
    {% endif %}
    t.add_goal(g)
    {% endfor %}

    {% if target.concurrent == True %}
    t.run_concurrent()
    {% else %}
    t.run_seq()
    {% endif %}

