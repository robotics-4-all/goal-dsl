import os
from textx import language, metamodel_from_file

from goal_dsl.utils import get_mm

__version__ = "0.1.0.dev"


@language('goal_dsl', '*.goal')
def goal_dsl_language():
    "goal_dsl language"
    return get_mm()
