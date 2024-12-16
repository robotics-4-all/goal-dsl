#!/usr/bin/env python3

from goalee import Scenario, RedisBroker, MQTTBroker, AMQPBroker
from goalee.entity import Entity

from goalee.area_goals import *
from goalee.complex_goal import *
from goalee.types import Point
from goalee.entity_goals import (
    EntityStateChange,
    EntityStateCondition
)

entities_list = []

{% for entity in entities %}
{{ entity.name }} = Entity(
    name='{{ entity.name }}',
    etype='{{ entity.etype }}',
    topic='{{ entity.topic }}',
    attributes={{ entity.attr_list }},
    {% if entity.source.ref.__class__.__name__ == 'AMQPBroker' %}
    source=AMQPBroker(
        host='{{ entity.source.ref.host }}',
        port={{ entity.source.ref.port }},
        username='{{ entity.source.ref.username }}',
        password='{{ entity.source.ref.password }}',
        vhost='{{ entity.source.ref.vhost }}',
    )
    {% elif entity.source.ref.__class__.__name__ == 'RedisBroker' %}
    source=RedisBroker(
        host='{{ entity.source.ref.host }}',
        port={{ entity.source.ref.port }},
        db={{ entity.source.ref.db }},  # default DB number is 0
        username='{{ entity.source.ref.username }}',
        password='{{ entity.source.ref.password }}',
    )
    {% elif entity.source.ref.__class__.__name__ == 'MQTTBroker' %}
    source=MQTTBroker(
        host='{{ entity.source.ref.host }}',
        port={{ entity.source.ref.port }},
        username='{{ entity.source.ref.username }}',
        password='{{ entity.source.ref.password }}',
    )
    {% endif %}
)

entities_list.append({{ entity.name }})
{% endfor %}


if __name__ == '__main__':
    {% if scenario.broker.__class__.__name__ == 'AMQPBroker' %}
    broker = AMQPBroker(
        host='{{ scenario.broker.host }}',
        port={{ scenario.broker.port }},
        username='{{ scenario.broker.username }}',
        password='{{ scenario.broker.password }}',
        vhost='{{ scenario.broker.vhost }}',
    )
    {% elif scenario.broker.__class__.__name__ == 'RedisBroker' %}
    broker = RedisBroker(
        host='{{ scenario.broker.host }}',
        port={{ scenario.broker.port }},
        db={{ scenario.broker.db }},  # default DB number is 0
        username='{{ scenario.broker.username }}',
        password='{{ scenario.broker.password }}',
    )
    {% elif scenario.broker.__class__.__name__ == 'MQTTBroker' %}
    broker = MQTTBroker(
        host='{{ scenario.broker.host }}',
        port={{ scenario.broker.port }},
        username='{{ scenario.broker.username }}',
        password='{{ scenario.broker.password }}',
    )
    {% endif %}
    t = Scenario(
        name='{{ scenario.name }}',
        broker=broker,
        score_weights={{ scenario.scoreWeights }}
    )

    {% for goal in goals %}
    {% if goal.__class__.__name__ == 'EntityStateConditionGoal' %}
    g = EntityStateCondition(
        name='{{ goal.name }}',
        entities=[{% for e in entity_names %}{{ e }}, {% endfor %}],
        # condition=lambda entities: True if {{goal.cond_lambda}} else False,
        condition='{{ goal.condition.cond_expr.replace("'", "\"") }}',
        max_duration={{ goal.max_duration }},
        min_duration={{ goal.min_duration }},
    )

    {% elif goal.__class__.__name__ == 'EntityStateChangeGoal' %}
    g = EntityStateChange(
        entity={{ goal.entity.name }},
        name='{{ goal.name }}',
        max_duration={{ goal.max_duration }},
        min_duration={{ goal.min_duration }},
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
    {% elif goal.__class__.__name__ == 'RectangleAreaGoal' %}
    g = RectangleAreaGoal(
        name='{{ goal.name }}',
        entities=[{% for e in entity_names %}{{ e }}, {% endfor %}],
        bottom_left_edge={{ goal.bottom_left_edge}},
        length_x={{ goal.lengthX}},
        length_y={{ goal.lengthY}},
        tag=AreaGoalTag.{{ goal.tag }},
        max_duration={{ goal.max_duration }},
        min_duration={{ goal.min_duration }},
    )
    {% elif goal.__class__.__name__ == 'CircularAreaGoal' %}
    g = CircularAreaGoal(
        name='{{ goal.name }}',
        entities=[{% for e in entity_names %}{{ e }}, {% endfor %}],
        center={{ goal.center }},
        radius={{ goal.radius }},
        tag=AreaGoalTag.{{ goal.tag }},
        max_duration={{ goal.max_duration }},
        min_duration={{ goal.min_duration }},
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
    cg.add_goal(cg)
        {% endfor %}
    ## More Goals to Generate here
    {% endif %}
    t.add_goal(g)
    {% endfor %}

    {% if scenario.concurrent == True %}
    t.run_concurrent()
    {% else %}
    t.run_seq()
    {% endif %}

