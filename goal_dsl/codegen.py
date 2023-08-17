from os import path, mkdir, getcwd, chmod
from textx import generator
import jinja2

from goal_dsl.language import build_model
from goal_dsl.definitions import THIS_DIR

THIS_DIR = path.abspath(path.dirname(__file__))

# Initialize template engine.
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(path.join(THIS_DIR, 'templates')),
    trim_blocks=True,
    lstrip_blocks=True)

template = jinja_env.get_template('template.tpl')

srcgen_folder = path.join(path.realpath(getcwd()), 'gen')


def generate(model_fpath: str,
             out_dir: str = ""):
    # Create output folder
    if out_dir in (None, ""):
        out_dir = srcgen_folder
    model, _ = build_model(model_fpath)
    if not path.exists(out_dir):
        mkdir(out_dir)

    scenarios = model.scenarios
    for scenario in scenarios:
        broker = scenario.broker
        goals = scenario.goals
        set_defaults(scenario, broker, goals)
        report_broker(broker)
        report_goals(scenario)

        # goals = process_goals(target.goals)
        #
        # out_file = path.join(out_dir, "goal_checker.py")
        # with open(path.join(out_file), 'w') as f:
        #     f.write(template.render(broker=broker,
        #                             target=target,
        #                             goals=goals))
        # chmod(out_file, 509)
        # return out_dir


def process_goals(goals):
    for goal in goals:
        if goal.__class__.__name__ == 'EntityStateConditionGoal':
            cond_lambda = make_condition_lambda(goal.condition)
            goal.cond_lambda = cond_lambda
        if goal.__class__.__name__ == 'EntityStateChangeGoal':
            print(goal)
        goal_max_min_duration_from_tc(goal)
        if goal.__class__.__name__ == 'ComplexGoal':
            process_goals(goal.goals)
    return goals


def set_defaults(target, broker, goals):
    if target.concurrent is None:
        target.concurrent = True
    if target.scoreWeights is None:
        target.scoreWeights = [1/len(target.goals)] * len(target.goals)
    elif len(target.scoreWeights) == 0:
        target.scoreWeights = [1/len(target.goals)] * len(target.goals)


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


def to_python_op(op):
    if op == 'AND':
        return 'and'
    elif op == 'OR':
        return 'or'


def make_condition_lambda(condition):
    expr = transform_condition(condition)
    return f'lambda msg: True if {expr} else False'


def transform_condition(condition):
    expr = ''
    if condition.__class__.__name__ == "ConditionGroup":
        r1 = transform_condition(condition.r1)
        r2 = transform_condition(condition.r2)
        op = condition.operator
        expr = f'({r1} {to_python_op(op)} {r2})'
    elif condition.__class__.__name__ == "StringCondition":
        m = condition_param_to_py_syntax(condition.param)
        if condition.operator in ('==', '!='):
            # expr = f'msg["{condition.param}"] == "{condition.val}"'
            # print(condition.param)
            expr = f'{m} {condition.operator} "{condition.val}"'
        elif condition.operator == '~':
            expr = f'"{condition.val}" in {m}'
        elif condition.operator == '!~':
            expr = f'"{condition.val}" not in {m}'
    elif condition.__class__.__name__ == "NumericCondition":
        m = condition_param_to_py_syntax(condition.param)
        expr = f'{m} {condition.operator} {condition.val}'
    return expr


def condition_param_to_py_syntax(param):
    levels = param.name.split('.')
    sub_str = 'msg'
    for l in levels:
        sub_str = sub_str + f'[\'{l}\']'
    return sub_str


def report_goals(target: list):
    for goal in target.goals:
        print(f'[*] - Found Goal of type <{goal.__class__.__name__}>')


def report_broker(middleware):
    if middleware.__class__.__name__ == 'AMQPBroker':
        print('[*] - Middleware == AMQP Broker')
        print(f'-> host: {middleware.host}')
        print(f'-> port: {middleware.port}')
        print(f'-> vhost: {middleware.vhost}')
        print(f'-> exchange: {middleware.exchange}')
        print(f'-> username: {middleware.auth.username}')
        print(f'-> password: {middleware.auth.password}')
    elif middleware.__class__.__name__ == 'RedisBroker':
        print('[*] - Middleware == Redis Broker')
        print(f'-> host: {middleware.host}')
        print(f'-> port: {middleware.port}')
        print(f'-> db: {middleware.db}')
        print(f'-> username: {middleware.auth.username}')
        print(f'-> password: {middleware.auth.password}')
    elif middleware.__class__.__name__ == 'MQTTBroker':
        print('[*] - Middleware == MQTTBroker Broker')
        print(f'-> host: {middleware.host}')
        print(f'-> port: {middleware.port}')
        print(f'-> username: {middleware.auth.username}')
        print(f'-> password: {middleware.auth.password}')
    else:
        raise ValueError(f'Middleware class ({middleware}) not supported!!')


@generator('goal_dsl', 'python')
def codegen_python(metamodel, model, output_path, overwrite, debug, **custom_args):
    "Generator for generating goalee from goal_dsl descriptions"
    generate(model._tx_filename)

