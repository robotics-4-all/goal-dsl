"""Tests for language module — validation, metamodel, model utilities."""

import pytest
from textx import TextXSemanticError, TextXSyntaxError

from telos.language import (
    build_model,
    build_model_str,
    class_provider,
    get_metamodel,
    get_model_entities,
    get_model_goals,
    get_model_scenarios,
    telos_language,
)

from .conftest import BROKER_MQTT


def test_build_model_str(minimal_model):
    m = build_model_str(minimal_model)
    assert m is not None
    assert len(m.entities) == 1


def test_build_model_file(minimal_model, tmp_path):
    f = tmp_path / "test.telos"
    f.write_text(minimal_model)
    m = build_model(str(f))
    assert m is not None
    assert len(m.entities) == 1


def test_duplicate_entity_names():
    with pytest.raises(TextXSemanticError, match="Entity.*already exists"):
        build_model_str(
            BROKER_MQTT
            + """
Entity S1
    type: sensor
    topic: 'a'
    source: HomeMQTT
    attributes:
        - temp: float
end

Entity S1
    type: sensor
    topic: 'b'
    source: HomeMQTT
    attributes:
        - temp: float
end
"""
        )


def test_duplicate_broker_names():
    with pytest.raises(TextXSemanticError, match="Source.*already exists"):
        build_model_str("""
Broker<MQTT> B1
    host: 'localhost'
    port: 1883
end

Broker<MQTT> B1
    host: 'localhost'
    port: 1884
end
""")


def test_duplicate_goal_names():
    with pytest.raises(TextXSemanticError, match="Goal.*already exists"):
        build_model_str(
            BROKER_MQTT
            + """
Entity S1
    type: sensor
    topic: 'a'
    source: HomeMQTT
    attributes:
        - temp: float
end

Goal<Watch> G1
    entity: S1
end

Goal<Watch> G1
    entity: S1
end

Scenario Sc
    goals:
        - G1
    concurrent: false
end
"""
        )


def test_duplicate_entity_attrs():
    with pytest.raises(TextXSemanticError, match="attribute.*already exists"):
        build_model_str(
            BROKER_MQTT
            + """
Entity S1
    type: sensor
    topic: 'a'
    source: HomeMQTT
    attributes:
        - temp: float
        - temp: float
end
"""
        )


def test_class_provider_known():
    from telos.lib.entity import Entity

    result = class_provider("Entity")
    assert result is Entity


def test_class_provider_unknown():
    assert class_provider("NonExistentClass") is None


def test_get_metamodel():
    mm = get_metamodel()
    assert mm is not None


def test_get_model_entities(full_model):
    m = build_model_str(full_model)
    entities = get_model_entities(m)
    assert len(entities) >= 3


def test_get_model_goals(full_model):
    m = build_model_str(full_model)
    goals = get_model_goals(m)
    assert len(goals) >= 5


def test_get_model_scenarios(full_model):
    m = build_model_str(full_model)
    scenarios = get_model_scenarios(m)
    assert len(scenarios) == 2


def test_invalid_model():
    with pytest.raises((TextXSyntaxError, TextXSemanticError)):
        build_model_str("this is not a valid model at all!!!")


def test_telos_language():
    assert telos_language is not None
    assert hasattr(telos_language, "name")
    assert telos_language.name == "telos"


def test_time_obj_processor_valid():
    from telos.language import time_obj_processor
    from telos.lib.types import Time

    t = Time(hour=12, minute=30, second=45)
    # Should not raise
    time_obj_processor(t)


def test_time_obj_processor_invalid_hour():
    from telos.language import time_obj_processor
    from telos.lib.types import Time

    t = Time(hour=25, minute=0, second=0)
    with pytest.raises(TextXSemanticError, match="Time.hours"):
        time_obj_processor(t)


def test_time_obj_processor_invalid_minute():
    from telos.language import time_obj_processor
    from telos.lib.types import Time

    t = Time(hour=0, minute=61, second=0)
    with pytest.raises(TextXSemanticError, match="Time.minutes"):
        time_obj_processor(t)


def test_time_obj_processor_invalid_second():
    from telos.language import time_obj_processor
    from telos.lib.types import Time

    t = Time(hour=0, minute=0, second=61)
    with pytest.raises(TextXSemanticError, match="Time.seconds"):
        time_obj_processor(t)


def test_verify_source_names_duplicate_rest():
    from telos.language import build_model_str

    with pytest.raises(TextXSemanticError, match="Source.*already exists"):
        build_model_str("""
RESTEndpoint A1
    verb: GET
    host: 'localhost'
    port: 80
    path: '/a'
end

RESTEndpoint A1
    verb: GET
    host: 'localhost'
    port: 80
    path: '/b'
end
""")


def test_eval_condition_safe():
    build_model_str(
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
        'S1.temp > 10 and S1.temp < 50'
end

Scenario Sc
    goals:
        - G1
    concurrent: false
end
"""
    )


def test_eval_condition_import_rejected():
    with pytest.raises(TextXSemanticError, match="dangerous"):
        build_model_str(
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
        '__import__("os").system("ls")'
end

Scenario Sc
    goals:
        - G1
    concurrent: false
end
"""
        )


def test_eval_condition_exec_rejected():
    with pytest.raises(TextXSemanticError, match="dangerous"):
        build_model_str(
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
        'exec("bad")'
end

Scenario Sc
    goals:
        - G1
    concurrent: false
end
"""
        )


def test_eval_condition_os_rejected():
    with pytest.raises(TextXSemanticError, match="dangerous"):
        build_model_str(
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
        'os.system("ls")'
end

Scenario Sc
    goals:
        - G1
    concurrent: false
end
"""
        )
