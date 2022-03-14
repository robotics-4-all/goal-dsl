"""
Top level package directory of goal-dsl
"""


__author__ = """Konstantinos Panayiotou"""
__email__ = 'klpanagi@gmail.com'
__version__ = "0.2.0.dev"


from textx import language

from goal_dsl.utils import get_mm


@language('goal_dsl', '*.goal')
def goal_dsl_language():
    "goal_dsl language"
    return get_mm()
