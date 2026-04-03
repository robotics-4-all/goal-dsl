import pathlib
import re
from collections import deque
from os.path import join

import textx.scoping.providers as scoping_providers
from textx import (
    TextXSemanticError,
    get_children_of_type,
    get_location,
    get_metamodel as _tx_get_metamodel,
    language,
    metamodel_from_file,
    textx_isinstance,
)

from telos.definitions import BUILTIN_MODELS, MODEL_REPO_PATH

CURRENT_FPATH = pathlib.Path(__file__).parent.resolve()

_DURATION_PATTERN = re.compile(r"^(\d+(?:\.\d+)?)(ms|s|m|h)$")
_DURATION_MULTIPLIERS = {"ms": 0.001, "s": 1.0, "m": 60.0, "h": 3600.0}
_ATTR_DEFAULTS = {"int": 0, "float": 0.0, "str": "", "bool": False, "list": []}


def _entity_obj_processor(entity):
    if entity.source and hasattr(entity.source, "ref"):
        entity.source = entity.source.ref
    entity.freq = entity.freq if entity.freq not in (None, 0) else 1
    entity.attributes = entity.attributes or []
    entity.attr_buffs = []
    entity.attributes_dict = {attr.name: attr for attr in entity.attributes}
    entity.attributes_buff = {attr.name: None for attr in entity.attributes}

    def _init_attr_buffer(attr_name, size):
        entity.attributes_buff[attr_name] = deque(maxlen=size)

    entity.init_attr_buffer = _init_attr_buffer


def _attribute_obj_processor(attr):
    default = attr.default
    dtype = attr.dtype
    if dtype == "time":
        if default is None:
            from types import SimpleNamespace

            t = SimpleNamespace(parent=attr, hour=0, minute=0, second=0)
            t.to_int = lambda: 0
            attr.value = t
        else:
            attr.value = default
    elif dtype == "dict":
        items = default.items if (default is not None and hasattr(default, "items")) else []
        attr.items = items
        attr.items_dict = {item.name: item for item in items}
        attr.value = attr.items_dict
    elif dtype == "list":
        if default is not None and hasattr(default, "items"):
            attr.value = default.items
        else:
            attr.value = default if default is not None else []
    elif dtype in _ATTR_DEFAULTS:
        attr.value = default if default is not None else _ATTR_DEFAULTS[dtype]
    else:
        attr.value = default


def _init_duration(dur):
    dur.value = 0.0
    dur.unit = "s"
    if dur.raw:
        m = _DURATION_PATTERN.match(dur.raw)
        if m:
            dur.value = float(m.group(1))
            dur.unit = m.group(2)
    mult = _DURATION_MULTIPLIERS.get(dur.unit, 1.0)
    dur.to_seconds = lambda: dur.value * mult


def process_duration_objects(model):
    for dur in get_children_of_type("Duration", model):
        _init_duration(dur)


def time_obj_processor(t):
    if t.hour > 24 or t.hour < 0:
        raise TextXSemanticError("Time.hours must be in range [0, 24]")
    if t.minute > 60 or t.minute < 0:
        raise TextXSemanticError("Time.minutes must be in range [0, 60]")
    if t.second > 60 or t.second < 0:
        raise TextXSemanticError("Time.seconds must be in range [0, 60]")
    t.to_int = lambda: t.second + int(t.minute << 8) + int(t.hour << 16)


def process_time_class(model):
    types_time = get_children_of_type("Time", model)
    for t in types_time:
        if t.hour > 24 or t.hour < 0:
            raise TextXSemanticError("Time.hours must be in range [0, 24]")
        if t.minute > 60 or t.minute < 0:
            raise TextXSemanticError("Time.minutes must be in range [0, 60]")
        if t.second > 60 or t.second < 0:
            raise TextXSemanticError("Time.seconds must be in range [0, 60]")


def verify_source_names(model):
    _ids = []
    sources = get_children_of_type("MQTTBroker", model)
    sources += get_children_of_type("AMQPBroker", model)
    sources += get_children_of_type("RedisBroker", model)
    sources += get_children_of_type("RESTEndpoint", model)
    for s in sources:
        if s.name in _ids:
            raise TextXSemanticError(
                f"Source with name <{s.name}> already exists", **get_location(s)
            )
        _ids.append(s.name)


def verify_entity_names(model):
    _ids = []
    entities = get_children_of_type("Entity", model)
    for e in entities:
        if e.name in _ids:
            raise TextXSemanticError(
                f"Entity with name <{e.name}> already exists", **get_location(e)
            )
        _ids.append(e.name)
        verify_entity_attrs(e)


def verify_entity_attrs(entity):
    _ids = []
    for attr in entity.attributes:
        if attr.name in _ids:
            raise TextXSemanticError(
                f"Entity attribute <{attr.name}> already exists", **get_location(attr)
            )
        _ids.append(attr.name)


def verify_goal_names(model):
    _ids = []
    goals = getattr(model, "goals", []) or []
    for goal in goals:
        if goal.name in _ids:
            raise TextXSemanticError(
                f"Goal with name <{goal.name}> already exists", **get_location(goal)
            )
        _ids.append(goal.name)


DANGEROUS_PATTERNS = [
    "__import__",
    "__builtins__",
    "__class__",
    "__subclasses__",
    "import ",
    "exec(",
    "eval(",
    "compile(",
    "open(",
    "os.",
    "sys.",
    "subprocess",
    "lambda ",
    "def ",
    "class ",
    "globals(",
    "locals(",
    "getattr(",
    "setattr(",
    "delattr(",
    "breakpoint(",
    "__dict__",
]


def verify_constant_names(model):
    _ids = []
    constants = getattr(model, "constants", []) or []
    for c in constants:
        if c.name in _ids:
            raise TextXSemanticError(
                f"Constant with name <{c.name}> already exists", **get_location(c)
            )
        _ids.append(c.name)


def verify_eval_conditions(model):
    goals = get_children_of_type("EntityPyConditionGoal", model)
    for goal in goals:
        condition = getattr(goal, "condition", None)
        if condition is None:
            continue
        for pattern in DANGEROUS_PATTERNS:
            if pattern in condition:
                raise TextXSemanticError(
                    f"Goal<Eval> '{goal.name}' contains dangerous pattern"
                    f" '{pattern}' in condition",
                    **get_location(goal),
                )


def verify_duration_values(model):
    durations = get_children_of_type("Duration", model)
    for d in durations:
        if d.value <= 0:
            raise TextXSemanticError(
                f"Duration value must be positive, got {d.value}{d.unit}",
                **get_location(d),
            )


PRIMITIVES = (int, float, str, bool)

OPERATORS = {
    "~": lambda left, right: f"({left} in {right})",
    "!~": lambda left, right: f"({left} not in {right})",
    "has": lambda left, right: f"({right} in {left})",
    "has not": lambda left, right: f"({right} not in {left})",
    "==": lambda left, right: f"({left} == {right})",
    "!=": lambda left, right: f"({left} != {right})",
    "is": lambda left, right: f"({left} == {right})",
    "is not": lambda left, right: f"({left} != {right})",
    "in": lambda left, right: f"({left} in {right})",
    "not in": lambda left, right: f"({left} not in {right})",
    ">": lambda left, right: f"({left} > {right})",
    ">=": lambda left, right: f"({left} >= {right})",
    "<": lambda left, right: f"({left} < {right})",
    "<=": lambda left, right: f"({left} <= {right})",
    "AND": lambda left, right: f"({left} and {right})",
    "OR": lambda left, right: f"({left} or {right})",
    "NOT": lambda left, right: f"({left} is not {right})",
    "XOR": lambda left, right: f"({left} ^ {right})",
    "NOR": lambda left, right: f"(not ({left} or {right}))",
    "XNOR": lambda left, right: f"(({left} or {right}) and (not {left} or not {right}))",
    "NAND": lambda left, right: f"(not ({left} and {right}))",
    "InRange": lambda attr, min, max: f"({attr} > {min} and {attr} < {max})",
}


def _list_node_to_str(node) -> str:
    def _convert(item):
        if item.__class__.__name__ == "List":
            return _list_node_to_str(item)
        return repr(item)

    return "[" + ", ".join(_convert(x) for x in node.items) + "]"


def _dict_node_to_str(node) -> str:
    parts = []
    for item in node.items:
        parts.append(f"'{item.name}': {repr(item.value)}")
    return "{" + ", ".join(parts) + "}"


def transform_operand(node) -> str:
    if type(node) in PRIMITIVES:
        if type(node) is str:
            return f"'{node}'"
        else:
            return node
    elif node.__class__.__name__ == "List":
        return _list_node_to_str(node)
    elif node.__class__.__name__ == "Dict":
        return _dict_node_to_str(node)
    elif node.__class__.__name__ == "Time":
        return node.to_int()
    elif textx_isinstance(node, _tx_get_metamodel(node).namespaces["condition"]["AugmentedAttr"]):
        return transform_augmented_attr(node)
    elif textx_isinstance(node, _tx_get_metamodel(node).namespaces["condition"]["SimpleTimeAttr"]):
        return f"entities['{node.attribute.parent.name}'].attributes['{node.attribute.name}']"
    else:
        return f"entities['{node.parent.name}']." + f"attributes['{node.name}']"


def transform_augmented_attr(aattr) -> str:
    parent = aattr.parent
    val: str = ""
    if aattr.__class__.__name__ == "SimpleNumericAttr":
        attr_ref = aattr.attribute
        entity_ref = aattr.attribute.parent
        if parent.__class__.__name__ in ("StdAttr", "MeanAttr", "VarAttr", "MinAttr", "MaxAttr"):
            entity_ref.init_attr_buffer(attr_ref.name, parent.size)
            entity_ref.attr_buffs.append((attr_ref.name, parent.size))
            val = f"entities['{entity_ref.name}'].get_buffer('{attr_ref.name}')"
        else:
            val = f"entities['{entity_ref.name}'].attributes['{attr_ref.name}']"
    elif aattr.__class__.__name__ in (
        "SimpleBoolAttr",
        "SimpleStringAttr",
        "SimpleDictAttr",
        "SimpleListAttr",
    ):
        attr_ref = aattr.attribute
        entity_ref = aattr.attribute.parent
        val = f"entities['{entity_ref.name}'].attributes['{attr_ref.name}']"
    elif aattr.__class__.__name__ == "StdAttr":
        val = f"std({transform_augmented_attr(aattr.attribute)})"
    elif aattr.__class__.__name__ == "MeanAttr":
        val = f"mean({transform_augmented_attr(aattr.attribute)})"
    elif aattr.__class__.__name__ == "VarAttr":
        val = f"var({transform_augmented_attr(aattr.attribute)})"
    elif aattr.__class__.__name__ == "MaxAttr":
        val = f"max({transform_augmented_attr(aattr.attribute)})"
    elif aattr.__class__.__name__ == "MinAttr":
        val = f"min({transform_augmented_attr(aattr.attribute)})"
    return val


def process_node_condition(cond_node):
    mm = _tx_get_metamodel(cond_node.parent)
    cond_ns = mm.namespaces["condition"]

    if textx_isinstance(cond_node, cond_ns["OrExpr"]):
        for op in cond_node.operands:
            process_node_condition(op)
        lambdas = [op.cond_lambda for op in cond_node.operands]
        cond_node.cond_lambda = (
            " or ".join(f"({lam})" for lam in lambdas) if len(lambdas) > 1 else lambdas[0]
        )

    elif textx_isinstance(cond_node, cond_ns["AndExpr"]):
        for op in cond_node.operands:
            process_node_condition(op)
        lambdas = [op.cond_lambda for op in cond_node.operands]
        cond_node.cond_lambda = (
            " and ".join(f"({lam})" for lam in lambdas) if len(lambdas) > 1 else lambdas[0]
        )

    elif textx_isinstance(cond_node, cond_ns["NotExpr"]):
        process_node_condition(cond_node.operand)
        if cond_node.operand.__class__.__name__ == "NotExpr":
            cond_node.cond_lambda = f"(not ({cond_node.operand.cond_lambda}))"
        else:
            cond_node.cond_lambda = cond_node.operand.cond_lambda

    elif textx_isinstance(cond_node, cond_ns["ParenCondition"]):
        process_node_condition(cond_node.inner)
        cond_node.cond_lambda = cond_node.inner.cond_lambda

    elif textx_isinstance(cond_node, cond_ns["BinaryLogical"]):
        process_node_condition(cond_node.r1)
        process_node_condition(cond_node.r2)
        cond_node.cond_lambda = OPERATORS[cond_node.operator](
            cond_node.r1.cond_lambda, cond_node.r2.cond_lambda
        )

    elif textx_isinstance(cond_node, cond_ns["InRangeCondition"]):
        operand1 = transform_operand(cond_node.attribute)
        cond_node.cond_lambda = OPERATORS["InRange"](operand1, cond_node.min, cond_node.max)

    elif textx_isinstance(cond_node, cond_ns["GoalStatusCondition"]):
        goal_name = cond_node.operand1.goal
        status_val = cond_node.operand2
        cond_node.cond_lambda = OPERATORS[cond_node.operator](
            f"goals['{goal_name}'].status", f"'{status_val}'"
        )

    else:
        operand1 = transform_operand(cond_node.operand1)
        operand2 = transform_operand(cond_node.operand2)
        cond_node.cond_lambda = OPERATORS[cond_node.operator](operand1, operand2)


def build_condition(cond) -> str:
    process_node_condition(cond)
    return cond.cond_lambda


def model_proc(model, metamodel):
    process_duration_objects(model)
    process_time_class(model)
    verify_constant_names(model)
    verify_entity_names(model)
    verify_source_names(model)
    verify_goal_names(model)
    verify_eval_conditions(model)
    verify_duration_values(model)


def get_metamodel(debug: bool = False, global_repo: bool = False):
    metamodel = metamodel_from_file(
        CURRENT_FPATH.joinpath("grammar/telos.tx"),
        auto_init_attributes=True,
        textx_tools_support=True,
        global_repository=global_repo,
        debug=debug,
    )

    metamodel.register_scope_providers(get_scope_providers())
    metamodel.register_obj_processors(
        {
            "Entity": _entity_obj_processor,
            "Attribute": _attribute_obj_processor,
            "Time": time_obj_processor,
        }
    )
    metamodel.register_model_processor(model_proc)
    return metamodel


def _normalize_import_uri(uri):
    if uri.endswith(".telos"):
        return uri
    return uri.replace(".", "/") + ".telos"


def get_scope_providers():
    sp = {
        "*.*": scoping_providers.FQNImportURI(
            importAs=True, importURI_converter=_normalize_import_uri
        )
    }
    if BUILTIN_MODELS:
        sp["brokers*"] = scoping_providers.FQNGlobalRepo(join(BUILTIN_MODELS, "broker", "*.telos"))
        sp["entities*"] = scoping_providers.FQNGlobalRepo(
            join(BUILTIN_MODELS, "entity", "*.telos")
        )
    if MODEL_REPO_PATH:
        sp["brokers*"] = scoping_providers.FQNGlobalRepo(
            join(MODEL_REPO_PATH, "broker", "*.telos")
        )
        sp["entities*"] = scoping_providers.FQNGlobalRepo(
            join(MODEL_REPO_PATH, "entity", "*.telos")
        )
    return sp


def build_model(model_path):
    mm = get_metamodel(debug=False)
    model = mm.model_from_file(model_path)
    return model


def build_model_str(model_str):
    mm = get_metamodel(debug=False)
    model = mm.model_from_str(model_str)
    return model


def get_model_grammar(model_path):
    mm = get_metamodel()
    grammar_model = mm.grammar_model_from_file(model_path)
    return grammar_model


def get_model_entities(model):
    entities = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:
        for m in model._tx_model_repository.all_models:
            entities += m.entities
    else:
        entities = model.entities
    return entities


def get_model_goals(model):
    goals = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:
        for m in model._tx_model_repository.all_models:
            goals += m.goals
    else:
        goals = model.goals
    return goals


def get_model_scenarios(model):
    scenarios = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:
        for m in model._tx_model_repository.all_models:
            scenarios += m.scenarios
    else:
        scenarios = model.scenarios
    return scenarios


@language("telos", "*.telos")
def telos_language():
    "Telos — Goal-driven Behavior Verification DSL for CPSs"
    return get_metamodel()
