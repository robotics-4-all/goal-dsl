"""Tests for condition building and lambda generation."""

from telos.language import OPERATORS, build_condition, transform_operand
from telos.language import build_model_str
from telos.transformations.m2t_python import make_condition_lambda

from .conftest import BROKER_MQTT


def _cond_model(condition_text, attr_type="float"):
    return (
        BROKER_MQTT
        + f"""
Entity S1
    type: sensor
    topic: 'test'
    source: HomeMQTT
    attributes:
        - temp: float
        - humidity: float
        - active: bool
        - label: str
end

Goal<When> G1
    when
        {condition_text}
end

Scenario Sc
    goals:
        - G1
    concurrent: false
end
"""
    )


def _build_and_get_lambda(condition_text):
    m = build_model_str(_cond_model(condition_text))
    g = m.goals[0]
    build_condition(g.condition)
    return g.condition.cond_lambda


def test_numeric_gt():
    lam = _build_and_get_lambda("S1.temp > 30")
    assert ">" in lam
    assert "30" in lam
    assert "S1" in lam
    assert "temp" in lam


def test_numeric_lt():
    lam = _build_and_get_lambda("S1.temp < 10")
    assert "<" in lam
    assert "10" in lam


def test_numeric_eq():
    lam = _build_and_get_lambda("S1.temp == 25")
    assert "==" in lam


def test_numeric_gte():
    lam = _build_and_get_lambda("S1.temp >= 20")
    assert ">=" in lam


def test_compound_and():
    lam = _build_and_get_lambda("(S1.temp > 30) AND (S1.humidity < 0.5)")
    assert "and" in lam
    assert "temp" in lam
    assert "humidity" in lam


def test_compound_or():
    lam = _build_and_get_lambda("(S1.temp > 30) OR (S1.temp < 10)")
    assert "or" in lam


def test_bool_is():
    lam = _build_and_get_lambda("S1.active is true")
    assert "==" in lam
    assert "True" in lam or "true" in lam.lower()


def test_bool_is_not():
    lam = _build_and_get_lambda("S1.active is not false")
    assert "!=" in lam


def test_string_eq():
    lam = _build_and_get_lambda("S1.label == 'active'")
    assert "==" in lam
    assert "active" in lam


def test_aggregation_mean():
    lam = _build_and_get_lambda("mean(S1.temp, 5) > 25")
    assert "mean" in lam
    assert "get_buffer" in lam


def test_aggregation_std():
    lam = _build_and_get_lambda("std(S1.temp, 3) < 1")
    assert "std" in lam
    assert "get_buffer" in lam


def test_inrange():
    m = build_model_str(
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
        S1.temp in range [18.0, 26.0]
end

Scenario Sc
    goals:
        - G1
    concurrent: false
end
"""
    )
    g = m.goals[0]
    build_condition(g.condition)
    lam = g.condition.cond_lambda
    assert "18.0" in lam
    assert "26.0" in lam


def test_goal_status():
    m = build_model_str(
        BROKER_MQTT
        + """
Entity S1
    type: sensor
    topic: 'test'
    source: HomeMQTT
    attributes:
        - temp: float
end

Goal<Watch> G1
    entity: S1
end

Goal<When> G2
    when
        G1.status == REACHED
end

Scenario Sc
    goals:
        - G1
        - G2
    concurrent: false
end
"""
    )
    g = next(g for g in m.goals if g.name == "G2")
    build_condition(g.condition)
    lam = g.condition.cond_lambda
    assert "goals" in lam
    assert "G1" in lam
    assert "REACHED" in lam


def test_make_condition_lambda():
    m = build_model_str(
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
    g = m.goals[0]
    build_condition(g.condition)
    result = make_condition_lambda(g.condition)
    assert result.startswith("lambda entities, goals={}")
    assert "True if" in result
    assert "else False" in result


def test_operators_dict():
    assert OPERATORS["=="](1, 2) == "(1 == 2)"
    assert OPERATORS["!="](1, 2) == "(1 != 2)"
    assert OPERATORS[">"](1, 2) == "(1 > 2)"
    assert OPERATORS["<"](1, 2) == "(1 < 2)"
    assert OPERATORS[">="](1, 2) == "(1 >= 2)"
    assert OPERATORS["<="](1, 2) == "(1 <= 2)"
    assert "and" in OPERATORS["AND"]("a", "b")
    assert "or" in OPERATORS["OR"]("a", "b")
    assert OPERATORS["is"]("a", "b") == "(a == b)"
    assert OPERATORS["is not"]("a", "b") == "(a != b)"
    assert OPERATORS["~"]("a", "b") == "(a in b)"
    assert OPERATORS["!~"]("a", "b") == "(a not in b)"
    assert OPERATORS["has"]("a", "b") == "(b in a)"
    assert "InRange" in OPERATORS
    assert OPERATORS["XOR"]("a", "b") == "(a ^ b)"
    assert "not" in OPERATORS["NOR"]("a", "b")
    assert "not" in OPERATORS["NAND"]("a", "b")


def test_transform_operand_primitives():
    assert transform_operand(42) == 42
    assert transform_operand(3.14) == 3.14
    result = transform_operand("hello")
    assert result == "'hello'"
    assert transform_operand(True) is True


def test_transform_operand_list():
    List = type("List", (), {})
    lst = List()
    lst.items = [1, 2, 3]
    result = transform_operand(lst)
    assert result == "[1, 2, 3]"


def test_transform_operand_dict():
    Dict = type("Dict", (), {})
    d = Dict()
    d.items = []
    result = transform_operand(d)
    assert result == "{}"


def test_transform_operand_time():
    Time = type("Time", (), {})
    t = Time()
    t.hour = 1
    t.minute = 2
    t.second = 3
    t.to_int = lambda: t.second + int(t.minute << 8) + int(t.hour << 16)
    result = transform_operand(t)
    assert result == t.to_int()


def test_aggregation_var():
    lam = _build_and_get_lambda("var(S1.temp, 4) < 2")
    assert "var" in lam
    assert "get_buffer" in lam


def test_aggregation_min():
    lam = _build_and_get_lambda("min(S1.temp, 3) > 0")
    assert "min" in lam
    assert "get_buffer" in lam


def test_aggregation_max():
    lam = _build_and_get_lambda("max(S1.temp, 3) < 100")
    assert "max" in lam
    assert "get_buffer" in lam


def test_not_operator():
    lam = _build_and_get_lambda("NOT S1.temp > 30")
    assert "not" in lam


def test_xor_operator():
    lam = _build_and_get_lambda("(S1.temp > 30) XOR (S1.humidity > 0.5)")
    assert "^" in lam


def test_nor_operator():
    lam = _build_and_get_lambda("(S1.temp > 30) NOR (S1.humidity > 0.5)")
    assert "not" in lam
    assert "or" in lam


def test_nand_operator():
    lam = _build_and_get_lambda("(S1.temp > 30) NAND (S1.humidity > 0.5)")
    assert "not" in lam
    assert "and" in lam


def test_string_contains():
    lam = _build_and_get_lambda("S1.label ~ 'active'")
    assert "in" in lam


def test_string_not_contains():
    lam = _build_and_get_lambda("S1.label !~ 'active'")
    assert "not in" in lam


def test_string_has():
    lam = _build_and_get_lambda("S1.label has 'a'")
    assert "in" in lam


def test_string_neq():
    lam = _build_and_get_lambda("S1.label != 'inactive'")
    assert "!=" in lam


def test_nary_and():
    lam = _build_and_get_lambda("S1.temp > 30 AND S1.humidity > 0.5 AND S1.temp < 100")
    assert lam.count("and") == 2


def test_nary_or():
    lam = _build_and_get_lambda("S1.temp > 30 OR S1.humidity > 0.5 OR S1.temp < 100")
    assert lam.count("or") == 2


def test_mixed_precedence():
    lam = _build_and_get_lambda("S1.temp > 30 AND S1.humidity > 0.5 OR S1.temp < 100")
    assert "and" in lam
    assert "or" in lam


def test_not_condition():
    lam = _build_and_get_lambda("NOT S1.temp > 30")
    assert "not" in lam


def test_not_with_parens():
    lam = _build_and_get_lambda("NOT (S1.temp > 30)")
    assert "not" in lam


def test_grouped_or_and():
    lam = _build_and_get_lambda("(S1.temp > 30 OR S1.humidity > 0.5) AND S1.temp < 100")
    assert "and" in lam
    assert "or" in lam
