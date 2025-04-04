"""
Top level package directory of goal-dsl
"""


__author__ = """Konstantinos Panayiotou"""
__email__ = 'klpanagi@gmail.com'
__version__ = "0.1.0"

from .language import goaldsl_language, get_metamodel
from .generator import codegen_python as codegen_python
