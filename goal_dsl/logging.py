import logging
import os
from rich.logging import RichHandler

LOGGING_FORMAT = "%(message)s"
LOG_LEVEL = os.getenv("GOALDSL_LOG_LEVEL", "INFO")

logging.basicConfig(
    level=LOG_LEVEL, format=LOGGING_FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

default_logger = logging.getLogger()
