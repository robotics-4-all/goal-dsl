"""Tests for Python code generation."""

import os

from telos.transformations.m2t_python import generate, generate_str

from .conftest import BROKER_MQTT


def test_generate_minimal(minimal_model):
    result = generate_str(minimal_model)
    assert isinstance(result, dict)
    assert "S1" in result
    code = result["S1"]
    assert "Entity(" in code
    assert "MQTTBroker(" in code or "source=MQTTBroker" in code


def test_generate_full_model(full_model):
    result = generate_str(full_model)
    assert "MainScenario" in result
    assert "SecondScenario" in result
    assert len(result) == 2


def test_generate_contains_imports(minimal_model):
    result = generate_str(minimal_model)
    code = result["S1"]
    assert "from goalee" in code
    assert "import" in code


def test_generate_condition_goal():
    model = (
        BROKER_MQTT
        + """
Entity S1
    type: sensor
    topic: 'test'
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
"""
    )
    result = generate_str(model)
    code = result["Sc"]
    assert "lambda entities" in code
    assert "temp" in code


def test_generate_py_condition():
    model = (
        BROKER_MQTT
        + """
Entity S1
    type: sensor
    topic: 'test'
    source: HomeMQTT
    attributes:
        - temp: float
end

Goal<Eval> G1
    when
        'S1.temp * 2 > 50'
end

Scenario Sc
    goals:
        - G1
    concurrent: false
end
"""
    )
    result = generate_str(model)
    code = result["Sc"]
    assert "S1.temp * 2 > 50" in code


def test_generate_watch_goal(minimal_model):
    result = generate_str(minimal_model)
    code = result["S1"]
    assert "EntityStateChange" in code


def test_generate_complex_goal(full_model):
    result = generate_str(full_model)
    code = result["MainScenario"]
    assert "ComplexGoal" in code


def test_generate_area_goal(full_model):
    result = generate_str(full_model)
    code = result["MainScenario"]
    assert "RectangleAreaGoal" in code


def test_generate_repeater_goal(full_model):
    result = generate_str(full_model)
    code = result["MainScenario"]
    assert "GoalRepeater" in code


def test_generate_to_file(minimal_model, tmp_path):
    model_file = tmp_path / "test.telos"
    model_file.write_text(minimal_model)
    out_dir = str(tmp_path / "gen")
    generate(str(model_file), out_dir)
    assert os.path.exists(os.path.join(out_dir, "S1.py"))


def test_generate_time_constraints(full_model):
    result = generate_str(full_model)
    code = result["MainScenario"]
    assert "max_duration" in code or "for_duration" in code


def test_generate_weights(full_model):
    result = generate_str(full_model)
    code = result["MainScenario"]
    assert "goal_weights" in code


def test_generate_concurrent(full_model):
    result = generate_str(full_model)
    code = result["MainScenario"]
    assert "run_concurrent" in code


def test_generate_scenario_rtmonitor(full_model):
    result = generate_str(full_model)
    code = result["MainScenario"]
    assert "init_rtmonitor" in code


def test_generate_pose_goal():
    model = (
        BROKER_MQTT
        + """
Entity Robot1
    type: robot
    topic: 'robot.pose'
    source: HomeMQTT
    attributes:
        - position: dict
        - orientation: dict
end

Goal<Pose> G_Pose
    entity: Robot1
    position: Point3D(1, 1, 0)
    orientation: Orientation3D(0, 0, 1.57)
    maxDeviationPos: 0.1
    maxDeviationOri: 0.05
end

Scenario Sc
    goals:
        - G_Pose
    concurrent: false
end
"""
    )
    result = generate_str(model)
    code = result["Sc"]
    assert "PoseGoal" in code


def test_generate_position_goal():
    model = (
        BROKER_MQTT
        + """
Entity Robot1
    type: robot
    topic: 'robot.pose'
    source: HomeMQTT
    attributes:
        - position: dict
end

Goal<Pos> G_Pos
    entity: Robot1
    position: Point3D(1, 1, 0)
    maxDeviation: 0.1
end

Scenario Sc
    goals:
        - G_Pos
    concurrent: false
end
"""
    )
    result = generate_str(model)
    code = result["Sc"]
    assert "PositionGoal" in code


def test_generate_orientation_goal():
    model = (
        BROKER_MQTT
        + """
Entity Robot1
    type: robot
    topic: 'robot.pose'
    source: HomeMQTT
    attributes:
        - orientation: dict
end

Goal<Heading> G_Head
    entity: Robot1
    orientation: Orientation2D(1.57)
    maxDeviation: 0.05
end

Scenario Sc
    goals:
        - G_Head
    concurrent: false
end
"""
    )
    result = generate_str(model)
    code = result["Sc"]
    assert "OrientationGoal" in code


def test_generate_circle_goal():
    model = (
        BROKER_MQTT
        + """
Entity Robot1
    type: robot
    topic: 'robot.pose'
    source: HomeMQTT
    attributes:
        - position: dict
end

Goal<Circle> G_Circle
    entities:
        - Robot1
    center: Point3D(5, 5, 0)
    radius: 3
    tag: ENTER
end

Scenario Sc
    goals:
        - G_Circle
    concurrent: false
end
"""
    )
    result = generate_str(model)
    code = result["Sc"]
    assert "CircularAreaGoal" in code


def test_generate_shadow_goal():
    model = (
        BROKER_MQTT
        + """
Entity Robot1
    type: robot
    topic: 'robot.pose'
    source: HomeMQTT
    attributes:
        - position: dict
end

Entity Robot2
    type: robot
    topic: 'robot2.pose'
    source: HomeMQTT
    attributes:
        - position: dict
end

Goal<Shadow> G_Shadow
    movingEntity: Robot1
    entities:
        - Robot2
    radius: 3
    tag: ENTER
end

Scenario Sc
    goals:
        - G_Shadow
    concurrent: false
end
"""
    )
    result = generate_str(model)
    code = result["Sc"]
    assert "MovingAreaGoal" in code


def test_generate_to_file_default_dir(minimal_model, tmp_path):
    model_file = tmp_path / "test.telos"
    model_file.write_text(minimal_model)
    out_dir = str(tmp_path / "out")
    result = generate(str(model_file), out_dir)
    assert result == out_dir


def test_generate_with_generators(model_with_generators):
    result = generate_str(model_with_generators)
    assert isinstance(result, dict)
    assert "S1" in result
