import pathlib
from os.path import join

import textx.scoping.providers as scoping_providers
from textx import (
    TextXSemanticError,
    get_children_of_type,
    get_location,
    language,
    metamodel_from_file,
)

from telos.definitions import BUILTIN_MODELS, MODEL_REPO_PATH
from telos.lib.broker import (
    AMQPBroker,
    Broker,
    BrokerAuthPlain,
    MQTTBroker,
    RedisBroker,
)
from telos.lib.condition import (
    AdvancedCondition,
    AndExpr,
    AtomicCondition,
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
    ParenCondition,
    PrimitiveCondition,
    StringCondition,
    TimeCondition,
)
from telos.lib.entity import (
    Attribute,
    BoolAttribute,
    DictAttribute,
    Entity,
    FloatAttribute,
    IntAttribute,
    ListAttribute,
    StringAttribute,
    TimeAttribute,
)
from telos.lib.timing import (
    DeadlineGoal,
    Duration,
    LatencyGoal,
    OrderingGoal,
    RateGoal,
)
from telos.lib.types import Date, Dict, List, Time

CURRENT_FPATH = pathlib.Path(__file__).parent.resolve()


class Constant:
    def __init__(self, parent=None, name=None, value=None, **kwargs):
        self.parent = parent
        self.name = name
        self.value = value


CUSTOM_CLASSES = [
    Constant,
    Entity,
    Condition,
    OrExpr,
    AndExpr,
    NotExpr,
    AtomicCondition,
    ParenCondition,
    BinaryLogical,
    PrimitiveCondition,
    AdvancedCondition,
    NumericCondition,
    BoolCondition,
    StringCondition,
    ListCondition,
    DictCondition,
    TimeCondition,
    InRangeCondition,
    GoalStatusCondition,
    GoalStatusRef,
    Attribute,
    IntAttribute,
    FloatAttribute,
    TimeAttribute,
    StringAttribute,
    BoolAttribute,
    ListAttribute,
    DictAttribute,
    Broker,
    MQTTBroker,
    AMQPBroker,
    RedisBroker,
    BrokerAuthPlain,
    List,
    Dict,
    Time,
    Date,
    Duration,
    RateGoal,
    LatencyGoal,
    OrderingGoal,
    DeadlineGoal,
]


def class_provider(name):
    classes = {x.__name__: x for x in CUSTOM_CLASSES}
    return classes.get(name)


def time_obj_processor(t):
    if t.hour > 24 or t.hour < 0:
        raise TextXSemanticError("Time.hours must be in range [0, 24]")
    if t.minute > 60 or t.minute < 0:
        raise TextXSemanticError("Time.minutes must be in range [0, 60]")
    if t.second > 60 or t.second < 0:
        raise TextXSemanticError("Time.seconds must be in range [0, 60]")


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


def model_proc(model, metamodel):
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
        classes=class_provider,
        auto_init_attributes=False,
        textx_tools_support=True,
        global_repository=global_repo,
        debug=debug,
    )

    metamodel.register_scope_providers(get_scope_providers())
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
