from os import chmod, getcwd, mkdir, path

import jinja2
from textx import generator

from telos.definitions import TEMPLATES_PATH
from telos.language import (
    build_model,
    build_model_str,
    get_model_entities,
    get_model_scenarios,
)
from telos.logging import default_logger as logger

THIS_DIR = path.abspath(path.dirname(__file__))

# Initialize template engine.
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATES_PATH), trim_blocks=True, lstrip_blocks=True
)

template = jinja_env.get_template("scenario.py.jinja")

srcgen_folder = path.join(path.realpath(getcwd()), "gen")


def generate(model_fpath: str, out_dir: str = ""):
    """Generate Python code from a Telos model file."""
    if out_dir in (None, ""):
        out_dir = srcgen_folder
    if not path.exists(out_dir):
        mkdir(out_dir)

    model = build_model(model_fpath)
    scenario_code: dict = _generate_internal(model)

    for name, code in scenario_code.items():
        out_file = path.join(out_dir, f"{name}.py")
        with open(out_file, "w") as f:
            f.write(code)
            chmod(out_file, 509)

    return out_dir


def generate_str(model_str: str):
    """Generate Python code from a Telos model string."""
    model = build_model_str(model_str)
    scenario_code: dict = _generate_internal(model)
    return scenario_code


def _generate_internal(model):
    scenarios = get_model_scenarios(model)
    entities = get_model_entities(model)

    for e in entities:
        e.attr_list = [attr.name for attr in e.attributes]

    entity_names = [e.name for e in entities]

    rtmonitor = model.rtmonitor

    scenario_code = {}

    for scenario in scenarios:
        wgoals = scenario.goals

        set_defaults(scenario, rtmonitor, wgoals)

        goals = [goal.goal for goal in wgoals]
        goals = process_goals(goals)
        scenario.goals = goals

        scenario.fatals = process_goals(scenario.fatals)
        scenario.antigoals = process_goals(scenario.antigoals)

        code = template.render(
            rtmonitor=rtmonitor,
            scenario=scenario,
            entities=entities,
            entity_names=entity_names,
            goals=goals,
        )
        scenario_code[scenario.name] = code
    return scenario_code


def process_goals(goals):
    _goals = []
    for goal in goals:
        if goal.__class__.__name__ == "WeightedGoal":
            goal = goal.goal
        goal_type = goal.__class__.__name__
        if goal_type == "EntityStateConditionGoal":
            if goal.condition is not None:
                goal.condition.build()
                cond_lambda = make_condition_lambda(goal.condition)
                goal.condition.cond_lambda = cond_lambda
                logger.info(f"[*] - Goal <{goal.name}> condition lambda: {cond_lambda}")
        elif goal_type == "EntityPyConditionGoal":
            if goal.condition is not None:
                goal.cond_py = goal.condition
                logger.info(f"[*] - Goal <{goal.name}> py condition: {goal.cond_py}")
        elif goal_type == "EntityStateChangeGoal":
            logger.info(f"[*] - Goal <{goal.name}> entity: {goal.entity.name}")
        elif goal_type in (
            "RectangleAreaGoal",
            "CircularAreaGoal",
            "MovingAreaGoal",
        ):
            pass
        elif goal_type in (
            "PositionGoal",
            "OrientationGoal",
            "PoseGoal",
        ):
            pass
        elif goal_type in (
            "StraightLineTrajectoryGoal",
            "WaypointTrajectoryGoal",
            "CurveTrajectoryGoal",
        ):
            pass
        elif goal_type == "RateGoal":
            logger.info(
                f"[*] - Goal <{goal.name}> rate: entity={goal.entity.name}, "
                f"interval={goal.interval}"
            )
        elif goal_type == "LatencyGoal":
            if goal.triggerCondition is not None:
                goal.triggerCondition.build()
                cond_lambda = make_condition_lambda(goal.triggerCondition)
                goal.triggerCondition.cond_lambda = cond_lambda
                logger.info(f"[*] - Goal <{goal.name}> trigger condition lambda: {cond_lambda}")
            if goal.responseCondition is not None:
                goal.responseCondition.build()
                cond_lambda = make_condition_lambda(goal.responseCondition)
                goal.responseCondition.cond_lambda = cond_lambda
                logger.info(f"[*] - Goal <{goal.name}> response condition lambda: {cond_lambda}")
        elif goal_type == "OrderingGoal":
            logger.info(f"[*] - Goal <{goal.name}> ordering: {goal.sequence}")
        elif goal_type == "DeadlineGoal":
            if goal.condition is not None:
                goal.condition.build()
                cond_lambda = make_condition_lambda(goal.condition)
                goal.condition.cond_lambda = cond_lambda
                logger.info(f"[*] - Goal <{goal.name}> deadline condition lambda: {cond_lambda}")
        elif goal_type == "GoalRepeater":
            _g = process_goals([goal.goal])
            _goals.extend(_g)
        elif goal_type == "ComplexGoal":
            _cgoals = process_goals(goal.goals)
            goal.goals = _cgoals
        else:
            logger.info(f"[X] {goal_type} not yet supported by the code generator!!")
        logger.info(f"[*] Transforming Goal <{goal_type}:{goal.name}> time constraints")
        goal_max_min_duration_from_tc(goal)
        _goals.append(goal)
    return _goals


def set_defaults(scenario, rtmonitor, wgoals):
    sweights = []
    for goal in wgoals:
        w = getattr(goal, "weight", None)
        sweights.append(w if w not in (None, 0) else 0)
    if 0 in sweights or len(sweights) == 0:
        n = len(scenario.goals)
        sweights = [1.0 / n] * n if n > 0 else []
    scenario.goalWeights = sweights
    if getattr(scenario, "concurrent", None) is None:
        scenario.concurrent = False


def goal_max_min_duration_from_tc(goal):
    max_duration = None
    min_duration = None
    for_duration = None
    time_constraints = getattr(goal, "timeConstraints", None)
    if not time_constraints:
        logger.info(f"[*] - Goal <{goal.name}> does not have any time constraints.")
    else:
        for tc in time_constraints:
            if tc.__class__.__name__ != "TimeConstraint":
                continue
            elif tc.type == "FROM_GOAL_START":
                if str(tc.comparator) == "<":
                    max_duration = tc.time
                elif str(tc.comparator) == ">":
                    min_duration = tc.time
            elif tc.type == "FOR_TIME":
                for_duration = tc.time
    timeout = getattr(goal, "timeout", None)
    if timeout is not None and max_duration is None:
        max_duration = timeout
    logger.info(f"[*] - Goal <{goal.name}> max duration: {max_duration} seconds")
    logger.info(f"[*] - Goal <{goal.name}> min duration: {min_duration} seconds")
    logger.info(f"[*] - Goal <{goal.name}> for duration: {for_duration} seconds")
    goal.max_duration = max_duration
    goal.min_duration = min_duration
    goal.for_duration = for_duration


def make_condition_lambda(condition):
    return f"lambda entities, goals={{}}: True if {condition.cond_lambda} else False"


@generator("telos", "python")
def codegen_python(
    metamodel,
    model,
    output_path,
    overwrite,
    debug,
    **custom_args,
):
    "Generator for generating Python code from Telos models"
    generate(model._tx_filename)
