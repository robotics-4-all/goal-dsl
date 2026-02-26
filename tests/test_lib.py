"""Tests for custom classes in lib/."""

from telos.lib.broker import AMQPBroker, Broker, BrokerAuthPlain, MQTTBroker, RedisBroker
from telos.lib.condition import (
    AndExpr,
    BinaryLogical,
    BoolCondition,
    Condition,
    DictCondition,
    GoalStatusCondition,
    GoalStatusRef,
    InRangeCondition,
    ListCondition,
    NotExpr,
    NumericCondition,
    OrExpr,
    StringCondition,
    TimeCondition,
)
from telos.lib.entity import (
    BoolAttribute,
    DictAttribute,
    Entity,
    FloatAttribute,
    IntAttribute,
    ListAttribute,
    StringAttribute,
    TimeAttribute,
)
from telos.lib.types import Date, Dict, List, Time

# ── Entity ─────────────────────────────────────────────


def test_entity_defaults():
    e = Entity(name="Test")
    assert e.name == "Test"
    assert e.freq == 1  # default when None/0
    assert e.attributes == []
    assert e.description == ""
    assert e.source is None


def test_entity_camel_name():
    e = Entity(name="my_sensor_name")
    assert e.camel_name == "MySensorName"


def test_entity_no_name():
    e = Entity()
    assert e.camel_name == ""


def test_entity_buffer():
    attr = FloatAttribute(name="temp")
    e = Entity(name="S1", attributes=[attr])
    e.init_attr_buffer("temp", 5)
    buf = e.get_buffer("temp")
    assert len(buf) == 5


# ── Attributes ─────────────────────────────────────────


def test_int_attribute_default():
    a = IntAttribute(name="x")
    assert a.value == 0
    assert a.type == "int"


def test_float_attribute_default():
    a = FloatAttribute(name="x")
    assert a.value == 0.0
    assert a.type == "float"


def test_string_attribute_default():
    a = StringAttribute(name="x")
    assert a.value == ""
    assert a.type == "str"


def test_bool_attribute_default():
    a = BoolAttribute(name="x")
    assert a.value is False
    assert a.type == "bool"


def test_time_attribute_default():
    a = TimeAttribute(name="x")
    assert a.type == "time"
    assert a.value.hour == 0
    assert a.value.minute == 0


def test_list_attribute_default():
    a = ListAttribute(name="x")
    assert a.value == []
    assert a.type == "list"


def test_dict_attribute_default():
    a = DictAttribute(name="x")
    assert a.type == "dict"
    assert a.value == {}


def test_int_attribute_with_value():
    a = IntAttribute(name="x", default=42)
    assert a.value == 42


def test_float_attribute_with_value():
    a = FloatAttribute(name="x", default=3.14)
    assert a.value == 3.14


# ── Brokers ────────────────────────────────────────────


def test_broker_defaults():
    b = Broker(name="B1", host="localhost", port=1883)
    assert b.ssl is False


def test_mqtt_broker_defaults():
    b = MQTTBroker(name="M1", host="localhost", port=1883)
    assert b.basePath == ""
    assert b.webPath == "/mqtt"
    assert b.webPort == 8883


def test_amqp_broker_defaults():
    b = AMQPBroker(name="A1", host="localhost", port=5672)
    assert b.topicExchange == "amq.topic"
    assert b.rpcExchange == "DEFAULT"


def test_redis_broker_defaults():
    b = RedisBroker(name="R1", host="localhost", port=6379)
    assert b.db == 0


def test_broker_auth_plain():
    a = BrokerAuthPlain(username="user", password="pass")
    assert a.username == "user"
    assert a.password == "pass"


# ── Types ──────────────────────────────────────────────


def test_list_repr():
    lst = List(items=[1, 2, 3])
    r = repr(lst)
    assert "1" in r and "2" in r and "3" in r


def test_list_empty():
    lst = List()
    assert lst.items == []


def test_dict_repr():
    class Item:
        def __init__(self, name, value):
            self.name = name
            self.value = value

    d = Dict(items=[Item("key", "val")])
    r = repr(d)
    assert "key" in r
    assert "val" in r


def test_dict_to_dict():
    class Item:
        def __init__(self, name, value):
            self.name = name
            self.value = value

    d = Dict(items=[Item("a", 1), Item("b", 2)])
    result = d.to_dict()
    assert result == {"a": 1, "b": 2}


def test_dict_empty():
    d = Dict()
    assert d.items == []
    assert repr(d) == "{}"


def test_time_to_int():
    t = Time(hour=1, minute=2, second=3)
    val = t.to_int()
    assert val == 3 + (2 << 8) + (1 << 16)


def test_time_defaults():
    t = Time()
    assert t.hour == 0
    assert t.minute == 0
    assert t.second == 0


def test_date():
    d = Date(month=12, day=25, year=2025)
    assert d.month == 12
    assert d.day == 25
    assert d.year == 2025


# ── Conditions ─────────────────────────────────────────


def test_condition_init():
    c = Condition()
    assert c.cond_lambda is None
    assert c.cond_raw is None


def test_or_expr_init():
    c = OrExpr(operands=["a", "b"])
    assert c.operands == ["a", "b"]


def test_and_expr_init():
    c = AndExpr(operands=["a", "b"])
    assert c.operands == ["a", "b"]


def test_not_expr_init():
    c = NotExpr(operand="a")
    assert c.operand == "a"


def test_binary_logical_init():
    c = BinaryLogical(r1="left", operator="XOR", r2="right")
    assert c.r1 == "left"
    assert c.r2 == "right"
    assert c.operator == "XOR"


def test_numeric_condition_init():
    c = NumericCondition(operand1="a", operator=">", operand2=10)
    assert c.operand1 == "a"
    assert c.operator == ">"
    assert c.operand2 == 10


def test_bool_condition_init():
    c = BoolCondition(operand1="a", operator="is", operand2=True)
    assert c.operator == "is"


def test_string_condition_init():
    c = StringCondition(operand1="a", operator="==", operand2="b")
    assert c.operator == "=="


def test_list_condition_init():
    c = ListCondition(operand1="a", operator="==", operand2=[1, 2])
    assert c.operator == "=="


def test_dict_condition_init():
    c = DictCondition(operand1="a", operator="!=", operand2={})
    assert c.operator == "!="


def test_time_condition_init():
    c = TimeCondition(operand1="a", operator=">", operand2="08:00")
    assert c.operator == ">"


def test_inrange_condition_init():
    c = InRangeCondition(attribute="temp", min=10, max=30)
    assert c.min == 10
    assert c.max == 30


def test_goal_status_ref_init():
    r = GoalStatusRef(goal="G1")
    assert r.goal == "G1"


def test_goal_status_condition_init():
    c = GoalStatusCondition(operand1="ref", operator="==", operand2="REACHED")
    assert c.operator == "=="
    assert c.operand2 == "REACHED"


# ── Entity update methods ─────────────────────────────


def test_entity_update_state():
    attr_f = FloatAttribute(name="temp")
    attr_b = BoolAttribute(name="active")
    e = Entity(name="S1", attributes=[attr_f, attr_b])
    e.init_attr_buffer("temp", 3)
    e.update_state({"temp": 25.0, "active": True})
    assert e.attributes_dict["temp"].value == 25.0
    assert e.attributes_dict["active"].value is True
    assert e.state == {"temp": 25.0, "active": True}


def test_entity_update_buffers():
    attr_f = FloatAttribute(name="temp")
    e = Entity(name="S1", attributes=[attr_f])
    e.init_attr_buffer("temp", 3)
    Entity.update_buffers(e.attributes_buff, {"temp": 10.0})
    Entity.update_buffers(e.attributes_buff, {"temp": 20.0})
    assert len(e.attributes_buff["temp"]) == 2
    assert list(e.attributes_buff["temp"]) == [10.0, 20.0]


def test_entity_update_attributes_simple():
    attr_f = FloatAttribute(name="temp")
    e = Entity(name="S1", attributes=[attr_f])
    Entity.update_attributes(e.attributes_dict, {"temp": 99.0})
    assert e.attributes_dict["temp"].value == 99.0


def test_entity_update_attributes_time():
    attr_t = TimeAttribute(name="ts")
    e = Entity(name="S1", attributes=[attr_t])
    Entity.update_attributes(
        e.attributes_dict,
        {"ts": {"hour": 10, "minute": 30, "second": 45}},
    )
    assert e.attributes_dict["ts"].value.hour == 10
    assert e.attributes_dict["ts"].value.minute == 30
    assert e.attributes_dict["ts"].value.second == 45


def test_entity_get_buffer_empty():
    attr_f = FloatAttribute(name="temp")
    e = Entity(name="S1", attributes=[attr_f])
    e.init_attr_buffer("temp", 5)
    # Buffer not full yet — returns zeros
    buf = e.get_buffer("temp")
    assert buf == [0] * 5


def test_entity_get_buffer_full():
    attr_f = FloatAttribute(name="temp")
    e = Entity(name="S1", attributes=[attr_f])
    e.init_attr_buffer("temp", 3)
    e.attributes_buff["temp"].append(1.0)
    e.attributes_buff["temp"].append(2.0)
    e.attributes_buff["temp"].append(3.0)
    buf = e.get_buffer("temp")
    assert list(buf) == [1.0, 2.0, 3.0]


def test_entity_with_existing_value():
    attr_i = IntAttribute(name="x", default=42)
    assert attr_i.value == 42


def test_string_attribute_with_value():
    a = StringAttribute(name="x", default="hello")
    assert a.value == "hello"


def test_bool_attribute_with_value():
    a = BoolAttribute(name="x", default=True)
    assert a.value is True


def test_list_attribute_with_value():
    a = ListAttribute(name="x", default=[1, 2, 3])
    assert a.value == [1, 2, 3]


def test_dict_attribute_with_items():
    class Item:
        def __init__(self, name, value):
            self.name = name
            self.value = value

    items = [Item("key1", "val1"), Item("key2", "val2")]
    a = DictAttribute(name="x", items=items)
    assert len(a.value) == 2
    assert "key1" in a.value
    assert "key2" in a.value


# ── Types additional ───────────────────────────────────


def test_time_repr():
    t = Time(hour=10, minute=5, second=30)
    assert t.hour == 10
    assert t.minute == 5
    assert t.second == 30


def test_date_defaults():
    d = Date()
    assert d.month is None
    assert d.day is None
    assert d.year is None


def test_list_with_items():
    lst = List(items=[10, 20, 30])
    r = repr(lst)
    assert "10" in r
    assert "30" in r
