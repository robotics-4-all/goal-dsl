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
    model = build_model(model_fpath)
    if not path.exists(out_dir):
        mkdir(out_dir)

    scenarios = get_model_scenarios(model)
    entities = get_model_entities(model)

    for e in entities:
        e.attr_list = [attr.name for attr in e.attributes]
        e.attr_buff = [getattr(attr, "buffer", None) for attr in e.attributes]

    entity_names = [e.name for e in entities]

    for scenario in scenarios:
        broker = scenario.broker
        wgoals = scenario.goals

        set_defaults(scenario, broker, wgoals)

        goals = [goal.goal for goal in wgoals]

        goals = process_goals(goals)
        scenario.scoreWeights = [goal.weight for goal in wgoals]

        out_file = path.join(out_dir, f"{scenario.name}.py")
        with open(path.join(out_file), 'w') as f:
            f.write(template.render(broker=broker,
                                    scenario=scenario,
                                    entities=entities,
                                    entity_names=entity_names,
                                    goals=goals))
        chmod(out_file, 509)
        return out_dir


def generate_str(model_str: str):
    model = build_model_str(model_str)

    scenarios = get_model_scenarios(model)
    entities = get_model_entities(model)

    for e in entities:
        e.attr_list = [attr.name for attr in e.attributes]
        e.attr_buff = [getattr(attr, "buffer", None) for attr in e.attributes]

    entity_names = [e.name for e in entities]

    for scenario in scenarios:
        broker = scenario.broker
        wgoals = scenario.goals

        set_defaults(scenario, broker, wgoals)

        goals = [goal.goal for goal in wgoals]

        goals = process_goals(goals)
        scenario.scoreWeights = [goal.weight for goal in wgoals]

        code = template.render(broker=broker,
                               scenario=scenario,
                               entities=entities,
                               entity_names=entity_names,
                               goals=goals)
        return code


def process_goals(goals):
    _goals = []
    for goal in goals:
        if goal.__class__.__name__ == 'WeightedGoal':
            goal = goal.goal
        if goal.__class__.__name__ == 'EntityStateConditionGoal':
            cond_lambda = make_condition_lambda(goal.condition)
            goal.condition.cond_lambda = cond_lambda
            logger.info(f'[*] - Goal <{goal.name}> condition lambda: {cond_lambda}')
        elif goal.__class__.__name__ == 'EntityStateChangeGoal':
            pass
        elif goal.__class__.__name__ == 'RectangleAreaGoal':
            pass
        elif goal.__class__.__name__ == 'CircularAreaGoal':
            pass
        elif goal.__class__.__name__ == 'ComplexGoal':
            _cgoals = process_goals(goal.goals)
            _goals.append(_cgoals)
            goal.goals = _cgoals
        else:
            print(f'[X] {goal.__class__.__name__} not yet supported by the code generator!!')
        goal_max_min_duration_from_tc(goal)
        _goals.append(goal)
    return _goals


def set_defaults(scenario, broker, wgoals):
    sweights = [goal.weight for goal in wgoals]
    if 0 in sweights or len(sweights) == 0:
        sweights = [1 / len(scenario.goals)] * len(scenario.goals)
    if scenario.concurrent is None:
        scenario.concurrent = True


def goal_max_min_duration_from_tc(goal):
    max_duration = None
    min_duration = None
    if goal.timeConstraints is None:
        print(f'[*] - Goal <{goal.name}> does not have any time constraints.')
    elif len(goal.timeConstraints) == 0:
        print(f'[*] - Goal <{goal.name}> does not have any time constraints.')
    else:
        for tc in goal.timeConstraints:
            if tc.__class__.__name__ != 'TimeConstraintDuration':
                continue
            max_duration = tc.time if tc.comparator == '<' else max_duration
            min_duration = tc.time if tc.comparator == '>' else min_duration
    print(f'[*] - Goal <{goal.name}> max duration: {max_duration} seconds')
    print(f'[*] - Goal <{goal.name}> min duration: {min_duration} seconds')
    goal.max_duration = max_duration
    goal.min_duration = min_duration


# def make_condition_lambda(condition):
#     cond = Condition(condition)
#     cond.build()
#     return cond.cond_expr
def make_condition_lambda(condition):
    return f'lambda entities: True if {condition.cond_py} else False'

def report_goals(scenario: list):
    for wgoal in scenario.goals:
        goal = wgoal.goal
        print(f'[*] {goal.name} -> {wgoal.weight}')


def report_broker(broker):
    if broker.__class__.__name__ == 'AMQPBroker':
        print('[*] AMQP Broker')
        print(f' host: {broker.host}')
        print(f' port: {broker.port}')
        print(f' vhost: {broker.vhost}')
        print(f' exchange: {broker.exchange}')
        print(f' username: {broker.auth.username}')
        print(f' password: {broker.auth.password}')
    elif broker.__class__.__name__ == 'RedisBroker':
        print('[*] Redis Broker')
        print(f' host: {broker.host}')
        print(f' port: {broker.port}')
        print(f' db: {broker.db}')
        print(f' username: {broker.auth.username}')
        print(f' password: {broker.auth.password}')
    elif broker.__class__.__name__ == 'MQTTBroker':
        print('[*] MQTT Broker')
        print(f' host: {broker.host}')
        print(f' port: {broker.port}')
        print(f' username: {broker.auth.username}')
        print(f' password: {broker.auth.password}')
    else:
        print(broker)
        raise ValueError(f'broker class ({broker}) not supported!!')


@generator('goal_dsl', 'python')
def codegen_python(metamodel, model, output_path, overwrite, debug, **custom_args):
    "Generator for generating goalee from goal_dsl descriptions"
    generate(model._tx_filename)
