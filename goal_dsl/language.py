import re
from os.path import join
from textx import metamodel_from_file, get_children_of_type, metamodel_for_language, get_location
import textx.scoping.providers as scoping_providers
from textx import language
import statistics

from goal_dsl.definitions import THIS_DIR, MODEL_REPO_PATH, BUILTIN_MODELS

# CURRENT_FPATH = pathlib.Path(__file__).parent.resolve()

CUSTOM_CLASSES = [
]

def class_provider(name):
    classes = dict(map(lambda x: (x.__name__, x), CUSTOM_CLASSES))
    return classes.get(name)


def model_proc(model, metamodel):
    pass


def get_metamodel(debug: bool = False, global_repo: bool = False):
    metamodel = metamodel_from_file(
        join(THIS_DIR, 'grammar', 'goal_dsl.tx'),
        classes=class_provider,
        auto_init_attributes=False,
        textx_tools_support=True,
        # global_repository=GLOBAL_REPO,
        global_repository=global_repo,
        debug=debug,
    )

    metamodel.register_scope_providers(get_scode_providers())
    metamodel.register_model_processor(model_proc)
    return metamodel


def get_scode_providers():
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
    mm = get_metamodel(debug=False)
    model = mm.model_from_file(model_path)
    conds = get_top_level_condition(model)
    for cond in conds:
        build_cond_expr(cond, model)
    # entities = get_children_of_type('Entity', model)
    return model


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
    print(goals)


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
