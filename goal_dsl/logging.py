import logging
import os
from rich.logging import RichHandler
from goal_dsl.definitions import LOG_LEVEL, ZERO_LOGS


if ZERO_LOGS:
    logging.disable()
else:
    LOGGING_FORMAT = "%(message)s"

    logging.basicConfig(
        format=LOGGING_FORMAT, datefmt="[%X]", handlers=[RichHandler()], force=True
    )
    logging.getLogger().setLevel(LOG_LEVEL)

default_logger = logging.getLogger()
