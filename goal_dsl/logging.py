import logging
import os
from rich.logging import RichHandler
from goal_dsl.definitions import LOG_LEVEL, ZERO_LOGS


if ZERO_LOGS:
    logging.disable()
else:
    LOGGING_FORMAT = "%(message)s"

    logging.basicConfig(
        level=LOG_LEVEL, format=LOGGING_FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )

default_logger = logging.getLogger()
