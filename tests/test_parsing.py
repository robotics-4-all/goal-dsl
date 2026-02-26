"""Tests for grammar parsing — verify all constructs parse via build_model_str."""

import pytest

from goal_dsl.language import build_model_str

from .conftest import BROKER_AMQP, BROKER_MQTT, BROKER_REDIS, ENTITY_ALL_TYPES, REST_ENDPOINT


def _model(body):
    """Wrap body in a minimal parseable model (broker is usually needed)."""
    return BROKER_MQTT + body


# ── Brokers ────────────────────────────────────────────


def test_parse_mqtt_broker():
    m = build_model_str(BROKER_MQTT)
    b = m.brokers[0]
    assert b.__class__.__name__ == "MQTTBroker"
    assert b.name == "HomeMQTT"
    assert b.host == "localhost"
    assert b.port == 1883


def test_parse_redis_broker():
    m = build_model_str(BROKER_REDIS)
    b = m.brokers[0]
    assert b.__class__.__name__ == "RedisBroker"
    assert b.name == "LocalRedis"
    assert b.db == 2
    assert b.ssl is True


def test_parse_amqp_broker():
    m = build_model_str(BROKER_AMQP)
    b = m.brokers[0]
    assert b.__class__.__name__ == "AMQPBroker"
    assert b.name == "MyAMQP"
    assert b.vhost == "/test"
    assert b.topicExchange == "amq.topic"


def test_parse_broker_auth():
    m = build_model_str(BROKER_MQTT)
    b = m.brokers[0]
    assert b.auth is not None
    assert b.auth.username == "user"
    assert b.auth.password == "pass"


def test_parse_rest_endpoint():
    m = build_model_str(REST_ENDPOINT)
    ep = m.restEndpoints[0]
    assert ep.name == "SensorAPI"
    assert ep.verb == "GET"
    assert ep.host == "api.example.com"
    assert ep.port == 443
    assert ep.path == "/sensors"


# ── Entities ───────────────────────────────────────────


def test_parse_entity_sensor():
    m = build_model_str(
        _model("""
Entity TempSensor
    type: sensor
    topic: 'bedroom.temp'
    source: HomeMQTT
    freq: 10
    description: 'A sensor'
    attributes:
        - temp: float
end
""")
    )
    e = m.entities[0]
    assert e.name == "TempSensor"
    assert e.etype == "sensor"
    assert e.topic == "bedroom.temp"
    assert e.freq == 10
    assert e.description == "A sensor"
    assert len(e.attributes) == 1


def test_parse_entity_actuator():
    m = build_model_str(
        _model("""
Entity Lamp
    type: actuator
    topic: 'bedroom.lamp'
    source: HomeMQTT
    attributes:
        - power: bool
end
""")
    )
    e = m.entities[0]
    assert e.etype == "actuator"


def test_parse_entity_all_attr_types():
    m = build_model_str(_model(ENTITY_ALL_TYPES))
    e = m.entities[0]
    types = {a.name: a.__class__.__name__ for a in e.attributes}
    assert types["i"] == "IntAttribute"
    assert types["f"] == "FloatAttribute"
    assert types["s"] == "StringAttribute"
    assert types["b"] == "BoolAttribute"
    assert types["l"] == "ListAttribute"
    assert types["d"] == "DictAttribute"
    assert types["t"] == "TimeAttribute"


def test_parse_entity_source_ref():
    m = build_model_str(
        _model("""
Entity S1
    type: sensor
    topic: 'test'
    source: HomeMQTT
    attributes:
        - v: float
end
""")
    )
    e = m.entities[0]
    assert e.source is not None
    assert e.source.ref is not None
    assert e.source.ref.__class__.__name__ == "MQTTBroker"
    assert e.source.ref.name == "HomeMQTT"


def test_parse_entity_with_generators(model_with_generators):
    m = build_model_str(model_with_generators)
    e = m.entities[0]
    assert e.name == "VirtualSensor"
    assert len(e.attributes) == 3
    assert e.freq == 5


# ── Goals ──────────────────────────────────────────────


def test_parse_watch_goal(minimal_model):
    m = build_model_str(minimal_model)
    g = m.goals[0]
    assert g.__class__.__name__ == "EntityStateChangeGoal"
    assert g.name == "G1"
    assert g.entity.name == "TempSensor"


def test_parse_when_goal():
    m = build_model_str(
        _model("""
Entity S1
    type: sensor
    topic: 'a'
    source: HomeMQTT
    attributes:
        - temp: float
end

Goal<When> G1
    when
        S1.temp > 30
end

Scenario Sc
    goals:
        - G1
    concurrent: false
end
""")
    )
    g = m.goals[0]
    assert g.__class__.__name__ == "EntityStateConditionGoal"
    assert g.condition is not None


def test_parse_when_goal_compound(condition_model):
    m = build_model_str(condition_model)
    g = next(g for g in m.goals if g.name == "CompoundGoal")
    assert g.condition.__class__.__name__ == "ConditionGroup"


def test_parse_when_goal_with_then_config(full_model):
    m = build_model_str(full_model)
    g = next(g for g in m.goals if g.name == "G_When")
    assert len(g.triggers) > 0
    assert g.description == "Temperature alert"
    assert len(g.timeConstraints) == 1


def test_parse_eval_goal(full_model):
    m = build_model_str(full_model)
    g = next(g for g in m.goals if g.name == "G_Eval")
    assert g.__class__.__name__ == "EntityPyConditionGoal"
    assert "TempSensor.temp" in g.condition


def test_parse_rect_goal(full_model):
    m = build_model_str(full_model)
    g = next(g for g in m.goals if g.name == "G_Rect")
    assert g.__class__.__name__ == "RectangleAreaGoal"
    assert g.lengthX == 5
    assert g.tag == "ENTER"


def test_parse_circle_goal(full_model):
    m = build_model_str(full_model)
    g = next(g for g in m.goals if g.name == "G_Circle")
    assert g.__class__.__name__ == "CircularAreaGoal"
    assert g.radius == 3
    assert g.tag == "AVOID"


def test_parse_pos_goal(full_model):
    m = build_model_str(full_model)
    g = next(g for g in m.goals if g.name == "G_Pos")
    assert g.__class__.__name__ == "PositionGoal"
    assert g.maxDeviation == pytest.approx(0.1)


def test_parse_heading_goal(full_model):
    m = build_model_str(full_model)
    g = next(g for g in m.goals if g.name == "G_Heading")
    assert g.__class__.__name__ == "OrientationGoal"
    assert g.maxDeviation == pytest.approx(0.05)


def test_parse_route_goal(full_model):
    m = build_model_str(full_model)
    g = next(g for g in m.goals if g.name == "G_Route")
    assert g.__class__.__name__ == "WaypointTrajectoryGoal"
    assert len(g.points) == 3


def test_parse_cluster_goal(full_model):
    m = build_model_str(full_model)
    g = next(g for g in m.goals if g.name == "G_Cluster")
    assert g.__class__.__name__ == "ComplexGoal"
    assert len(g.goals) == 3
    assert g.algorithm == "ALL_ACCOMPLISHED_ORDERED"


def test_parse_loop_goal(full_model):
    m = build_model_str(full_model)
    g = next(g for g in m.goals if g.name == "G_Loop")
    assert g.__class__.__name__ == "GoalRepeater"
    assert g.times == 3


def test_parse_pose_goal():
    m = build_model_str(
        _model("""
Entity R1
    type: sensor
    topic: 'r1.pose'
    source: HomeMQTT
    attributes:
        - position: dict
        - orientation: dict
end

Goal<Pose> G1
    entity: R1
    position: Point3D(1, 1, 0)
    orientation: Orientation2D(0)
    maxDeviationPos: 0.1
    maxDeviationOri: 0.05
end

Scenario Sc
    goals:
        - G1
    concurrent: false
end
""")
    )
    g = m.goals[0]
    assert g.__class__.__name__ == "PoseGoal"


# ── Conditions ─────────────────────────────────────────


def test_parse_bool_condition(condition_model):
    m = build_model_str(condition_model)
    g = next(g for g in m.goals if g.name == "BoolGoal")
    assert g.condition is not None


def test_parse_goal_status_condition(goal_status_model):
    m = build_model_str(goal_status_model)
    g = next(g for g in m.goals if g.name == "G2")
    assert g.condition.__class__.__name__ == "GoalStatusCondition"


def test_parse_inrange_condition(inrange_model):
    m = build_model_str(inrange_model)
    g = m.goals[0]
    assert g.condition.__class__.__name__ == "InRangeCondition"


def test_parse_aggregation(condition_model):
    m = build_model_str(condition_model)
    g = next(g for g in m.goals if g.name == "AggGoal")
    assert g.condition is not None


def test_parse_string_condition():
    m = build_model_str(
        _model("""
Entity S1
    type: sensor
    topic: 'a'
    source: HomeMQTT
    attributes:
        - label: str
end

Goal<When> G1
    when
        S1.label == 'active'
end

Scenario Sc
    goals:
        - G1
    concurrent: false
end
""")
    )
    g = m.goals[0]
    assert g.condition.__class__.__name__ == "StringCondition"


# ── Scenario / Metadata / RTMonitor ────────────────────


def test_parse_scenario_weights(full_model):
    m = build_model_str(full_model)
    s = next(s for s in m.scenarios if s.name == "MainScenario")
    assert len(s.goals) == 3
    assert s.concurrent is True


def test_parse_scenario_antigoals(full_model):
    m = build_model_str(full_model)
    s = next(s for s in m.scenarios if s.name == "MainScenario")
    assert len(s.antigoals) > 0


def test_parse_metadata(full_model):
    m = build_model_str(full_model)
    assert m.metadata is not None
    assert m.metadata.name == "TestProject"
    assert m.metadata.version == "1.0.0"


def test_parse_rtmonitor(full_model):
    m = build_model_str(full_model)
    assert m.rtmonitor is not None
    assert m.rtmonitor.eTopic == "goaldsl.test.event"


def test_parse_time_constraints(full_model):
    m = build_model_str(full_model)
    g = next(g for g in m.goals if g.name == "G_Rect")
    assert len(g.timeConstraints) == 2


def test_parse_shadow_goal():
    m = build_model_str(
        _model("""
Entity R1
    type: sensor
    topic: 'r1.pose'
    source: HomeMQTT
    attributes:
        - position: dict
end

Entity R2
    type: sensor
    topic: 'r2.pose'
    source: HomeMQTT
    attributes:
        - position: dict
end

Goal<Shadow> G1
    movingEntity: R1
    entities:
        - R2
    radius: 2
    tag: AVOID
end

Scenario Sc
    goals:
        - G1
    concurrent: false
end
""")
    )
    g = m.goals[0]
    assert g.__class__.__name__ == "MovingAreaGoal"
    assert g.radius == 2
