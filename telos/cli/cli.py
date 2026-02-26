import os

import click
from rich import pretty, print

from telos.language import build_model
from telos.transformations import m2t_python

pretty.install()


def make_executable(path):
    mode = os.stat(path).st_mode
    mode |= (mode & 0o444) >> 2  # copy R bits to X
    os.chmod(path, mode)


@click.group()
@click.pass_context
def cli(ctx):
    ctx.ensure_object(dict)


@cli.command("validate", help="Model Validation")
@click.pass_context
@click.argument("model_path")
def validate(ctx, model_path):
    try:
        _ = build_model(model_path)
        print("[*] Model validation success!!")
    except Exception as e:
        print(f"[*] Validation failed with error(s): {e}")
        ctx.exit(1)
    else:
        ctx.exit(0)


@cli.command("gen", help="Code Generator")
@click.pass_context
@click.argument("model_path")
def gen_scenarios(ctx, model_path: str):
    _ = m2t_python(model_path)


def main():
    cli(prog_name="telos")
