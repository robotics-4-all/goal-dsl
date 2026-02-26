import os
from os.path import dirname, join

THIS_DIR = dirname(__file__)
TEMPLATES_PATH = join(THIS_DIR, "templates")
GRAMMAR_PATH = join(THIS_DIR, "grammar")
BUILTIN_MODELS = None
MODEL_REPO_PATH = os.getenv("TELOS_MODEL_REPO", None)

ZERO_LOGS = os.getenv("TELOS_ZERO_LOGS", "0") == "1"
LOG_LEVEL = os.getenv("TELOS_LOG_LEVEL", "INFO").upper()
