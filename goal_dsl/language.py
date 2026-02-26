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

from goal_dsl.definitions import BUILTIN_MODELS, MODEL_REPO_PATH
from goal_dsl.lib.broker import (
    AMQPBroker,
    Broker,
    BrokerAuthPlain,
    MQTTBroker,
    RedisBroker,
)
from goal_dsl.lib.condition import (
    AdvancedCondition,
    BoolCondition,
    Condition,
    ConditionGroup,
    DictCondition,
    GoalStatusCondition,
    GoalStatusRef,
    InRangeCondition,
    ListCondition,
    NumericCondition,
    PrimitiveCondition,
    StringCondition,
    TimeCondition,
)
from goal_dsl.lib.entity import (
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
from goal_dsl.lib.types import Date, Dict, List, Time

CURRENT_FPATH = pathlib.Path(__file__).parent.resolve()

CUSTOM_CLASSES = [
    Entity,
    Condition,
    ConditionGroup,
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
    goals = get_children_of_type("Goal", model)
    for goal in goals:
        if goal.name in _ids:
            raise TextXSemanticError(
                f"Goal with name <{goal.name}> already exists", **get_location(goal)
            )
        _ids.append(goal.name)


def model_proc(model, metamodel):
    process_time_class(model)
    verify_entity_names(model)
    verify_source_names(model)
    verify_goal_names(model)


def get_metamodel(debug: bool = False, global_repo: bool = False):
    metamodel = metamodel_from_file(
        CURRENT_FPATH.joinpath("grammar/goal_dsl.tx"),
        classes=class_provider,
        auto_init_attributes=False,
        textx_tools_support=True,
        global_repository=global_repo,
        debug=debug,
    )

    metamodel.register_scope_providers(get_scope_providers())
    metamodel.register_model_processor(model_proc)
    return metamodel


def get_scope_providers():
    sp = {"*.*": scoping_providers.FQNImportURI(importAs=True)}
    if BUILTIN_MODELS:
        sp["brokers*"] = scoping_providers.FQNGlobalRepo(join(BUILTIN_MODELS, "broker", "*.goal"))
        sp["entities*"] = scoping_providers.FQNGlobalRepo(join(BUILTIN_MODELS, "entity", "*.goal"))
    if MODEL_REPO_PATH:
        sp["brokers*"] = scoping_providers.FQNGlobalRepo(join(MODEL_REPO_PATH, "broker", "*.goal"))
        sp["entities*"] = scoping_providers.FQNGlobalRepo(
            join(MODEL_REPO_PATH, "entity", "*.goal")
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


@language("goal_dsl", "*.goal")
def goaldsl_language():
    "Goal-driven Behavior Verification DSL for CPSs"
    return get_metamodel()
