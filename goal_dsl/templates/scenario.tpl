#!/usr/bin/env python3

from goalee import Scenario, Redisbroker, MQTTBroker, AMQPBroker
from goalee.entity_goals import (
    EntityStateChangeGoal, EntityStateConditionGoal
)
from goalee.entity import Entity

from goalee.area_goals import *
from goalee.complex_goal import *
from goalee.types import Point


{% if broker.__class__.__name__ == 'AMQPBroker' %}
broker = AMQPBroker()
{% elif broker.__class__.__name__ == 'RedisBroker' %}
broker = RedisBroker()
{% elif broker.__class__.__name__ == 'MQTTBroker' %}
broker = MQTTBroker()
{% endif %}


{% for entity in entities %}
{{ entity.name }} = Entity(
    name='{{ entity.name }}',
    etype='{{ entity.etype }}',
    topic='{{ entity.topic }}',
    attributes={{ entity.attr_list }},
    # broker=broker
)
{% endfor %}


if __name__ == '__main__':
    t = Scenario(
        name='{{ scenario.name }}',
        broker=broker,
        score_weights={{ scenario.scoreWeights }}
    )

    {% for goal in goals %}
    {% if goal.__class__.__name__ == 'EntityStateConditionGoal' %}
    g = EntityStateConditionGoal(
        name='{{ goal.name }}',
        entities={{ entity_names }},
        condition=lambda entities: {{goal.cond_lambda}},
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
    cg = ComplexGoal(
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
        condition="{{goal.cond_lambda}}",
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
    cg.add_goal(g)
    {% endfor %}
    ## More Goals to Generate here
    {% endif %}
    t.add_goal(cg)
    {% endfor %}

    {% if scenario.concurrent == True %}
    t.run_concurrent()
    {% else %}
    t.run_seq()
    {% endif %}

