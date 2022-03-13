import os
from textx import language

from goal_dsl.utils import get_mm

__version__ = "0.2.0.dev"


@language('goal_dsl', '*.goal')
def goal_dsl_language():
    "goal_dsl language"
    return get_mm()
