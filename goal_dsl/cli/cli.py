import sys
import click
import os
from rich import print, pretty

from goal_dsl.transformations import m2t_python
from goal_dsl.language import build_model

pretty.install()


def make_executable(path):
    mode = os.stat(path).st_mode
    mode |= (mode & 0o444) >> 2    # copy R bits to X
    os.chmod(path, mode)


@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)


@cli.command('validate', help='Model Validation')
@click.pass_context
@click.argument('model_path')
def validate(ctx, model_path):
    try:
        model = build_model(model_path)
        print('[*] Model validation success!!')
    except Exception as e:
        print('[*] Validation failed with error(s):')
        print(str(e))
        sys.exit(1)


@cli.command('gen', help='Code Generator')
@click.pass_context
@click.argument('model_path')
def gen_scenarios(ctx, model_path: str):
    _ = m2t_python(model_path)
    # return
    # for vn in vnodes:
    #     filepath = f'{vn[0].name}.py'
    #     with open(filepath, 'w') as fp:
    #         fp.write(vn[1])
    #         make_executable(filepath)
    #     print(f'[CLI] Compiled virtual Entity: [bold]{filepath}')

def main():
    cli(prog_name='goaldsl')
