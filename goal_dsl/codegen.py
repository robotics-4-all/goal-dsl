from os import path, mkdir, getcwd, chmod
from textx import generator
import jinja2

from goal_dsl.language import build_model, build_model_str, get_model_entities, get_model_scenarios
from goal_dsl.definitions import THIS_DIR
from goal_dsl.lib.condition import Condition
from goal_dsl.logging import default_logger as logger

THIS_DIR = path.abspath(path.dirname(__file__))

# Initialize template engine.
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(path.join(THIS_DIR, 'templates')),
    trim_blocks=True,
    lstrip_blocks=True)

template = jinja_env.get_template('scenario.py.jinja')

srcgen_folder = path.join(path.realpath(getcwd()), 'gen')


def generate(model_fpath: str,
             out_dir: str = ""):
    # Create output folder
    if out_dir in (None, ""):
        out_dir = srcgen_folder
    if not path.exists(out_dir):
        mkdir(out_dir)

    model = build_model(model_fpath)

    scenario_code: dict  = _generate_internal(model)

    for name, code in scenario_code.items():
        out_file = path.join(out_dir, f"{name}.py")
        with open(path.join(out_file), 'w') as f:
            f.write(code)
            chmod(out_file, 509)


def generate_str(model_str: str):
    model = build_model_str(model_str)
    scenario_code: dict  = _generate_internal(model)
    return scenario_code


def _generate_internal(model):
    scenarios = get_model_scenarios(model)
    entities = get_model_entities(model)

    for e in entities:
        e.attr_list = [attr.name for attr in e.attributes]
        e.attr_buff = [getattr(attr, "buffer", None) for attr in e.attributes]

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

        code = template.render(rtmonitor=rtmonitor,
                               scenario=scenario,
                               entities=entities,
                               entity_names=entity_names,
                               goals=goals)
        scenario_code[scenario.name] = code
    return scenario_code

def process_goals(goals):
    _goals = []
    for goal in goals:
        if goal.__class__.__name__ == 'WeightedGoal':
            goal = goal.goal
        if goal.__class__.__name__ == 'EntityStateConditionGoal':
            cond_lambda = make_condition_lambda(goal.condition)
            goal.condition.cond_lambda = cond_lambda
            logger.info(f'[*] - Goal <{goal.name}> condition lambda: {cond_lambda}')
        elif goal.__class__.__name__ == 'EntityPyConditionGoal':
            # TODO
            pass
        elif goal.__class__.__name__ == 'EntityStateChangeGoal':
            # TODO
            pass
        elif goal.__class__.__name__ == 'RectangleAreaGoal':
            # TODO
            pass
        elif goal.__class__.__name__ == 'CircularAreaGoal':
            # TODO
            pass
        elif goal.__class__.__name__ == 'PositionGoal':
            # TODO
            pass
        elif goal.__class__.__name__ == 'OrientationGoal':
            # TODO
            pass
        elif goal.__class__.__name__ == 'PoseGoal':
            # TODO
            pass
        elif goal.__class__.__name__ == 'ComplexGoal':
            _cgoals = process_goals(goal.goals)
            _goals.append(_cgoals)
            goal.goals = _cgoals
        else:
            logger.info(f'[X] {goal.__class__.__name__} not yet supported by the code generator!!')
        logger.info(f"[X] Transforming Goal <{goal.__class__.__name__}:{goal.name}> time constraints")
        goal_max_min_duration_from_tc(goal)
        _goals.append(goal)
    return _goals


def set_defaults(scenario, rtmonitor, wgoals):
    sweights = [goal.weight for goal in wgoals]
    if 0 in sweights or len(sweights) == 0:
        sweights = [1.0 / len(scenario.goals)] * len(scenario.goals)
    scenario.goalWeights = sweights
    if scenario.concurrent is None:
        scenario.concurrent = False


def goal_max_min_duration_from_tc(goal):
    max_duration = None
    min_duration = None
    for_duration = None
    if goal.timeConstraints is None:
        logger.info(f'[*] - Goal <{goal.name}> does not have any time constraints.')
    elif len(goal.timeConstraints) == 0:
        logger.info(f'[*] - Goal <{goal.name}> does not have any time constraints.')
    else:
        for tc in goal.timeConstraints:
            if tc.__class__.__name__ != 'TimeConstraint':
                continue
            elif tc.type == 'FROM_GOAL_START':
                max_duration = tc.time if str(tc.comparator) == '<' else max_duration
                min_duration = tc.time if str(tc.comparator) == '>' else min_duration
            elif tc.type == 'FOR_TIME':
                for_duration = tc.time
    logger.info(f'[*] - Goal <{goal.name}> max duration: {max_duration} seconds')
    logger.info(f'[*] - Goal <{goal.name}> min duration: {min_duration} seconds')
    logger.info(f'[*] - Goal <{goal.name}> for duration: {for_duration} seconds')
    goal.max_duration = max_duration
    goal.min_duration = min_duration
    goal.for_duration = for_duration


def make_condition_lambda(condition):
    return f'lambda entities: True if {condition.cond_py} else False'


def report_goals(scenario: list):
    for wgoal in scenario.goals:
        goal = wgoal.goal
        logger.info(f'[*] {goal.name} -> {wgoal.weight}')


def report_broker(broker):
    if broker.__class__.__name__ == 'AMQPBroker':
        logger.info('[*] AMQP Broker')
        logger.info(f' host: {broker.host}')
        logger.info(f' port: {broker.port}')
        logger.info(f' vhost: {broker.vhost}')
        logger.info(f' exchange: {broker.exchange}')
        logger.info(f' username: {broker.auth.username}')
        logger.info(f' password: {broker.auth.password}')
    elif broker.__class__.__name__ == 'RedisBroker':
        logger.info('[*] Redis Broker')
        logger.info(f' host: {broker.host}')
        logger.info(f' port: {broker.port}')
        logger.info(f' db: {broker.db}')
        logger.info(f' username: {broker.auth.username}')
        logger.info(f' password: {broker.auth.password}')
    elif broker.__class__.__name__ == 'MQTTBroker':
        logger.info('[*] MQTT Broker')
        logger.info(f' host: {broker.host}')
        logger.info(f' port: {broker.port}')
        logger.info(f' username: {broker.auth.username}')
        logger.info(f' password: {broker.auth.password}')
    else:
        logger.info(broker)
        raise ValueError(f'broker class ({broker}) not supported!!')


@generator('goal_dsl', 'python')
def codegen_python(metamodel, model, output_path, overwrite, debug, **custom_args):
    "Generator for generating goalee from goal_dsl descriptions"
    generate(model._tx_filename)
