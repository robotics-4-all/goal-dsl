import re
from os.path import join
from textx import metamodel_from_file, get_children_of_type, metamodel_for_language, get_location
import textx.scoping.providers as scoping_providers
from textx import language, get_model, textx_isinstance, TextXSemanticError, get_parent_of_type, get_children

from goal_dsl.logging import default_logger as logger

from goal_dsl.definitions import THIS_DIR, MODEL_REPO_PATH, BUILTIN_MODELS


class PrimitiveDataType(object):
    """
    We are registering user PrimitiveDataType class to support
    primitive types (integer, string) in our entity models
    Thus, user doesn't need to provide integer and string
    types in the model but can reference them in attribute types nevertheless.
    """
    def __init__(self, parent, name):
        self.parent = parent
        self.name = name

    def __str__(self):
        return self.name


BUILTIN_TYPES = {
    'int': PrimitiveDataType(None, 'int'),
    'int32': PrimitiveDataType(None, 'int32'),
    'int64': PrimitiveDataType(None, 'int64'),
    'uint': PrimitiveDataType(None, 'uint'),
    'uint8': PrimitiveDataType(None, 'uint8'),
    'uint32': PrimitiveDataType(None, 'uint32'),
    'uint64': PrimitiveDataType(None, 'uint64'),
    'float': PrimitiveDataType(None, 'float'),
    'float32': PrimitiveDataType(None, 'float32'),
    'float64': PrimitiveDataType(None, 'float64'),
    'str': PrimitiveDataType(None, 'str'),
    'dict': PrimitiveDataType(None, 'dict'),
    'list': PrimitiveDataType(None, 'list'),
}


BUILDIN_MATH_FUNCTIONS = [
    "max", "min", "sum", "mean", "std", "var"
]


CUSTOM_CLASSES = [
]


def class_provider(name):
    classes = dict(map(lambda x: (x.__name__, x), CUSTOM_CLASSES))
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


def verify_broker_names(model):
    _ids = []
    brokers = get_children_of_type("MQTTBroker", model)
    brokers += get_children_of_type("AMQPBroker", model)
    brokers += get_children_of_type("RedisBroker", model)
    for b in brokers:
        if b.name in _ids:
            raise TextXSemanticError(
                f"Broker with name <{b.name}> already exists", **get_location(b)
            )
        _ids.append(b.name)


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


def verify_goal_names(model):
    _ids = []
    goals = get_children_of_type("Goal", model)
    for goal in goals:
        if goal.name in _ids:
            raise TextXSemanticError(
                f"Goal with name <{goal.name}> already exists", **get_location(goal)
            )
        _ids.append(goal.name)


def verify_entity_attrs(entity):
    _ids = []
    for attr in entity.attributes:
        if attr.name in _ids:
            raise TextXSemanticError(
                f"Entity attribute <{attr.name}> already exists", **get_location(attr)
            )
        _ids.append(attr.name)


def build_entity_attr_buff_tuples(conds):
    pattern = r'(?:mean|std|min|max|std|var)\((\w+)\.(\w+), (\d+)\)'
    result = [] # List to store the entity attribute buffer tuples
    for cond in conds:
        matches = re.findall(pattern, cond.cond_def)
        result += [(entity, attribute, int(number)) for entity, attribute, number in matches]
    return result


def build_entity_attr_map(entities):
    entity_attr_map = {}
    for entity in entities:
        entity_attr_map[entity.name] = {}
        for attr in entity.attributes:
            entity_attr_map[entity.name][attr.name] = None
    return entity_attr_map


def scenario_processor(scenario):
    logger.info("Running scenario processor...")
    if not scenario.goalTickFreqHz:
        scenario.goalTickFreqHz = 10
    if not scenario.concurrent:
        scenario.concurrent = False


def model_proc(model, metamodel):
    logger.info("Running model processor...")
    process_time_class(model)
    process_goals(model)
    verify_entity_names(model)
    verify_broker_names(model)
    verify_goal_names(model)

    conds = get_top_level_condition(model)  # Get the top-level conditions from the model
    build_condition_expressions(conds)  # Build the condition expressions for each top-level condition

    entities = get_model_entities(model)  # Get the entities from the model
    entity_attr_buffs = build_entity_attr_buff_tuples(conds)  # Build the entity attribute buffer tuples
    update_entity_attributes(entities, entity_attr_buffs)  # Update the entity attributes with buffer values

    entity_attr_map = build_entity_attr_map(entities)  # Build the entity attribute map
    # print(entity_attr_map)
    logger.info("Model processing completed")


def build_condition_expressions(conds, model_str: str = None):
    for cond in conds:
        build_condition(cond, model_str)


def update_entity_attributes(entities, entity_attr_buffs):
    for entity in entities:
        initialize_entity_attributes(entity)
        update_entity_buffer(entity, entity_attr_buffs)


def initialize_entity_attributes(entity):
    for attr in entity.attributes:
        if not hasattr(attr, "buffer"):
            setattr(attr, "buffer", None)


def update_entity_buffer(entity, entity_attr_buffs):
    for c in entity_attr_buffs:
        if c[0] == entity.name:
            update_attribute_buffer(entity, c)


def update_attribute_buffer(entity, c):
    for attr in entity.attributes:
        if attr.name == c[1]:
            if attr.buffer is None or attr.buffer < c[2]:
                setattr(attr, "buffer", c[2])


def process_goals(model):
    _goals = get_children_of_type("RectangleAreaGoal", model) + \
        get_children_of_type("CircularAreaGoal", model) + \
        get_children_of_type("MovingAreaGoal", model)
    for goal in _goals:
        if goal.entities is None:
            goal.entities = [e for e in model.entities]


def condition_processor(cond):
    # build_cond_expr(cond)
    pass


def nid_processor(nid):
    nid = nid.replace("\n", "")
    return nid


def goal_obj_processor(goal):
    if not hasattr(goal, "entities") or goal.entities is None:
        goal.entities = []
    if goal.__class__.__name__ == 'EntityPyConditionGoal':
        pycondition_processor(goal)
    if goal.__class__.__name__ == 'EntityAttrStreamGoal':
        attr_stream_processor(goal)


def extract_object_dot_access(input_string):
    pattern = r"\b[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)+\b"
    matches = re.findall(pattern, input_string)
    return matches


def attr_stream_processor(goal):
    attr = goal.stream.attr
    entity = goal.stream.attr.parent
    goal.attr = attr
    goal.entity = entity


def pycondition_processor(goal):
    logger.info(f"Transforming Condition: {goal.condition}")
    cond_py = goal.condition
    cond_py = cond_py.lstrip().rstrip()  # Remove leading/trailing spaces
    cond_py = re.sub(' +', ' ', cond_py)  # Remove extra spaces
    cond_py = re.sub(r'\n', '', cond_py)  # Remove newlines

    def replace_math_functions(match):
        entity_name = match.group(2)
        attribute_path = match.group(3)
        number = match.group(4)

        parts = [part for part in attribute_path.split('.') if not part.isdigit()]
        if len(parts) > 1:
            return f"{match.group(1)}(entities[\"{entity_name}\"].get_buffer(\"{parts[0]}\", {number}))[\"{'.'.join(parts[1:])}\"]"
        else:
            return f"{match.group(1)}(entities[\"{entity_name}\"].get_buffer(\"{attribute_path}\", {number}))"

    cond_py = re.sub(r'(mean|std|var|max|min)\((\b\w+)\.([\w.]+), (\d+)\)', replace_math_functions, cond_py)

    def replace_attributes(match):
        entity_name = match.group(1)
        attribute_path = match.group(2)
        parts = [part for part in attribute_path.split('.') if not part.isdigit()]
        if len(parts) > 1:
            return f"entities[\"{entity_name}\"].attributes[\"{parts[0]}\"][\"{'.'.join(parts[1:])}\"]"
        else:
            return f"entities[\"{entity_name}\"].attributes[\"{attribute_path}\"]"

    cond_py = re.sub(r'(\b\w+)\.((?!\d+\b)[\w.]+)', replace_attributes, cond_py)
    goal.cond_py = cond_py
    logger.info(f"Transformed Condition: {cond_py}")


obj_processors = {
    'Goal': goal_obj_processor,
    'NID': nid_processor,
    'Scenario': scenario_processor,
}


def report(model):
    goals = get_model_goals(model)
    entities = get_model_entities(model)
    logger.info(f"Goals: {goals}")
    logger.info(f"Entities: {entities}")


def get_scope_providers():
    """
    Returns a dictionary of scope providers for different model types.

    """
    sp = {"*.*": scoping_providers.FQNImportURI(importAs=True)}
    if BUILTIN_MODELS:
        sp["brokers*"] = scoping_providers.FQNGlobalRepo(
            join(BUILTIN_MODELS, "broker", "*.goal"))
        sp["entities*"] = scoping_providers.FQNGlobalRepo(
            join(BUILTIN_MODELS, "entity", "*.goal"))
    if MODEL_REPO_PATH:
        sp["brokers*"] = scoping_providers.FQNGlobalRepo(
            join(MODEL_REPO_PATH, "broker", "*.goal"))
        sp["entities*"] = scoping_providers.FQNGlobalRepo(
            join(MODEL_REPO_PATH, "entity", "*.goal"))
    return sp


def get_metamodel(debug: bool = False, global_repo: bool = True):
    """
    Creates and returns a metamodel for  GoalDSL.

    Args:
        debug (bool): If True, enables debugging information. Defaults to False.
        global_repo (bool): If True, uses a global repository for the metamodel. Defaults to True.

    Returns:
        Metamodel: The created metamodel with registered scope providers, model processor, and object processors.
    """
    metamodel = metamodel_from_file(
        join(THIS_DIR, 'grammar', 'goal_dsl.tx'),
        auto_init_attributes=True,
        textx_tools_support=True,
        classes=[
            PrimitiveDataType
        ],
        builtins=BUILTIN_TYPES,
        global_repository=global_repo,
        debug=debug,
    )

    metamodel.register_scope_providers(get_scope_providers())
    metamodel.register_obj_processors(obj_processors)
    metamodel.register_model_processor(model_proc)
    return metamodel


GoalDSLMetaModel = get_metamodel(debug=False)  # Get the metamodel for the language


def build_model(model_path):
    """
    This function builds a model from a given goal-driven CPS Behavior Verification language file.

    Parameters:
    model_path (str): The path to the goal-driven CPS Behavior Verification language file.

    Returns:
    model: The built model object representing the goal-driven CPS Behavior Verification language.
    """
    model = GoalDSLMetaModel.model_from_file(model_path)  # Parse the model from the file
    return model  # Return the built model


def build_model_str(model_str):
    """
    This function builds a model from a given goal-driven CPS Behavior Verification language file.

    Parameters:
    model_path (str): The path to the goal-driven CPS Behavior Verification language file.

    Returns:
    model: The built model object representing the goal-driven CPS Behavior Verification language.
    """
    model = GoalDSLMetaModel.model_from_str(model_str)  # Parse the model from the file
    return model  # Return the built model


def get_model_entities(model):
    entities = []
    if model._tx_model_repository is not None and model._tx_model_repository.all_models:
        for m in model._tx_model_repository.all_models:
            entities += m.entities
    else:
        entities = model.entities
    return entities


def get_model_pycond_goals(model):
    conds = get_children_of_type("EntityPyConditionGoal", model)
    return conds


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


## OLD CONDITIONS -----------------------------------------

def get_model_conditions(model):
    conds = get_children_of_type("Condition", model)
    return conds

def get_top_level_condition(model):
    tl_conds = []
    conds = get_model_conditions(model)
    for c in conds:
        if c.parent.__class__.__name__ not in (
            "ConditionGroup", "PrimitiveCondition", "AdvancedCondition"):
            tl_conds.append(c)
    return tl_conds

def build_condition(cond, model_str: str = None):
    cond_def = get_cond_definition(cond, model_str)
    cond.cond_def = cond_def
    cond.cond_py = transform_cond_py(cond)


def transform_cond_py(cond):
    cond_def = cond.cond_def
    cond_def = cond_def.replace("condition:", "").lstrip().rstrip()
    logger.info(f"Transforming Condition: {cond_def}")
    cond_py = cond_def
    cond_py = re.sub(r'mean\(([^,]+)\.([^,]+), (\d+)\)', r'mean(entities["\1"].get_buffer("\2", \3))', cond_py)
    cond_py = re.sub(r'std\(([^,]+)\.([^,]+), (\d+)\)', r'std(entities["\1"].get_buffer("\2"), \3)', cond_py)
    cond_py = re.sub(r'var\(([^,]+)\.([^,]+), (\d+)\)', r'var(entities["\1"].get_buffer("\2", \3))', cond_py)
    cond_py = re.sub(r'max\(([^,]+)\.([^,]+), (\d+)\)', r'max(entities["\1"].get_buffer("\2", \3))', cond_py)
    cond_py = re.sub(r'min\(([^,]+)\.([^,]+), (\d+)\)', r'min(entities["\1"].get_buffer("\2", \3))', cond_py)
    cond_py = re.sub(r'(\b\w+)\.(?!\d)(\w+\b)', r'entities["\1"].attributes["\2"]', cond_py)
    logger.info(f"Transformed Condition: {cond_py}")
    return cond_py


def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


def get_cond_definition(cond, model_str: str = None):
    model = get_model(cond)
    line_start, _ = model._tx_parser.pos_to_linecol(cond._tx_position)
    line_end, _ = model._tx_parser.pos_to_linecol(cond._tx_position_end)
    loc = get_location(cond)
    if loc["filename"]:
        f = open(loc["filename"])
        lines = f.readlines()
    else:
        lines = model_str.split("\n")
    cond_def = "".join(lines[line_start-1:line_end]).replace("\n", "")
    cond_def = re.sub(' +', ' ', cond_def)
    return cond_def

## ----------------------------------------------------------

@language('goal_dsl', '*.goal')
def goaldsl_language():
    "Goal-driven Behavior Verification DSL for CPSs"
    return get_metamodel()


def get_model_grammar(model_path):
    mm = get_metamodel()
    grammar_model = mm.grammar_model_from_file(model_path)
    return grammar_model


def is_instance_textx(obj, type_name):
    return obj.__class__.__name__ == type_name
