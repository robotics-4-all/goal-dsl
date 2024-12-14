import re
from os.path import join
from textx import metamodel_from_file, get_children_of_type, metamodel_for_language, get_location
import textx.scoping.providers as scoping_providers
from textx import language
import statistics

from goal_dsl.definitions import THIS_DIR, MODEL_REPO_PATH, BUILTIN_MODELS

# CURRENT_FPATH = pathlib.Path(__file__).parent.resolve()


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


type_builtins = {
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
    'str': PrimitiveDataType(None, 'str')
}


CUSTOM_CLASSES = [
]

def class_provider(name):
    classes = dict(map(lambda x: (x.__name__, x), CUSTOM_CLASSES))
    return classes.get(name)


def model_proc(model, metamodel):
    pass


def condition_processor(plot):
    pass

def nid_processor(nid):
    nid = nid.replace("\n", "")
    return nid


obj_processors = {
    'Condition': condition_processor
}


def get_metamodel(debug: bool = False, global_repo: bool = False):
    metamodel = metamodel_from_file(
        join(THIS_DIR, 'grammar', 'goal_dsl.tx'),
        auto_init_attributes=True,
        textx_tools_support=True,
        classes=[
            PrimitiveDataType
        ],
        builtins=type_builtins,
        # global_repository=GLOBAL_REPO,
        global_repository=global_repo,
        debug=debug,
    )

    metamodel.register_scope_providers(get_scope_providers())
    metamodel.register_model_processor(model_proc)
    metamodel.register_obj_processors(obj_processors)
    return metamodel


def get_scope_providers():
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


def build_model(model_path):
    """
    This function builds a model from a given goal-driven CPS Behavior Verification language file.

    Parameters:
    model_path (str): The path to the goal-driven CPS Behavior Verification language file.

    Returns:
    model: The built model object representing the goal-driven CPS Behavior Verification language.
    """
    mm = get_metamodel(debug=False)  # Get the metamodel for the language
    model = mm.model_from_file(model_path)  # Parse the model from the file
    conds = get_top_level_condition(model)  # Get the top-level conditions from the model
    for cond in conds:
        build_cond_expr(cond, model)  # Build the condition expressions for each top-level condition
    return model  # Return the built model


def get_model_entities(model):
    return get_children_of_type("Entity", model)


def get_model_conditions(model):
    conds = get_children_of_type("ConditionList", model)
    return conds


def get_top_level_condition(model):
    tl_conds = []
    conds = get_model_conditions(model)
    for c in conds:
        if c.parent.__class__.__name__ not in (
            "ConditionGroup", "PrimitiveCondition", "AdvancedCondition"):
            tl_conds.append(c)
    return tl_conds


def get_model_goals(model):
    goals = get_children_of_type("Goal", model)
    return goals


def build_cond_expr(cond, model):
    cond_def = get_cond_definition(cond, model)
    cond.cond_expr = cond_def
    transform_cond(cond)


def transform_cond(cond):
    pattern = r'\b\w+\.\w+\b'
    matches = re.findall(pattern, cond.cond_expr)
    for m in matches:
        if is_float(m):
            continue
        entity, attr = m.split(".")
        attr_ref = f"entities['{entity}'].attributes['{attr}']"
        cond.cond_expr = cond.cond_expr.replace(m, attr_ref)
        cond.cond_expr = cond.cond_expr.replace("condition:", "")
        if cond.cond_expr.startswith(" "):
            cond.cond_expr = cond.cond_expr[1:]


def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


def get_cond_definition(cond, model):
    line_start, col_start = model._tx_parser.pos_to_linecol(cond._tx_position)
    line_end, col_end = model._tx_parser.pos_to_linecol(cond._tx_position_end)
    loc = get_location(cond)
    f = open(loc["filename"])
    lines = f.readlines()
    cond_def = "".join(lines[line_start-1:line_end]).replace("\n", "")
    cond_def = re.sub(' +', ' ', cond_def)
    return cond_def


def evaluate_cond(cond):
    # Check if condition has been build using build_expression
    if cond.cond_expr not in (None, ''):
        # Evaluate condition providing the textX model as global context for evaluation
        try:
            entities = {}
            # print(entities['system_clock'].attributes_dict['time'].value.to_int())
            print(f"Evaluate Condition: {cond.cond_expr}")
            if eval(
                cond.cond_expr,
                {
                    'entities': entities
                },
                {
                    'std': statistics.stdev,
                    'var': statistics.variance,
                    'mean': statistics.mean,
                    'min': min,
                    'max': max,
                }
            ):
                return True, f"{cond.parent.name}: triggered."
            else:
                return False, f"{cond.parent.name}: not triggered."
        except Exception as e:
            print(e)
            return False, f"{cond.parent.name}: not triggered."
    else:
        return False, f"{cond.parent.name}: condition not built."


@language('goal_dsl', '*.goal')
def goaldsl_language():
    "Goal-driven CPS Behavior Verification language"
    return get_metamodel()
