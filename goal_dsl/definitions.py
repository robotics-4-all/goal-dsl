import os
from os.path import dirname, join


THIS_DIR = dirname(__file__)
TEMPLATES_PATH = join(THIS_DIR, 'templates')
GRAMMAR_PATH = join(THIS_DIR, 'grammar')
MODEL_REPO_PATH = None
BUILTIN_MODELS = None
ZERO_LOGS = int(os.getenv('GOALDSL_ZERO_LOGS', 0))
LOG_LEVEL = os.getenv("GOALDSL_LOG_LEVEL", "INFO")
