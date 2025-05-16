"""
Top level package directory of goal-dsl
"""


__author__ = """Konstantinos Panayiotou"""
__email__ = 'klpanagi@gmail.com'
__version__ = "0.3.0"

from .language import get_metamodel
from .transformations import m2t_python
from textx import generator, language


@generator('goal_dsl', 'python')
def codegen_python(metamodel, model, output_path, overwrite, debug, **custom_args):
    "TextX generator for generating goalee from goal_dsl descriptions"
    m2t_python(model._tx_filename)


@language('goal_dsl', '*.goal')
def goaldsl_language():
    "Goal-driven Behavior Verification DSL for CPSs"
    return get_metamodel()
