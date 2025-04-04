from os import path, mkdir, getcwd, chmod
from textx import generator
import jinja2

from goal_dsl.transformations.model_2_plantuml import generate_diagram as model_2_plantuml
from goal_dsl.transformations.m2t_python import (
    generate as m2t_python,
    generate_str as m2t_python_str
)


@generator('goal_dsl', 'python')
def codegen_python(metamodel, model, output_path, overwrite, debug, **custom_args):
    "Generator for generating goalee from goal_dsl descriptions"
    m2t_python(model._tx_filename)
