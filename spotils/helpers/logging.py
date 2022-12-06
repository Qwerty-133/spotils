"""Project logging utilites."""
import logging
import sys

from loguru import logger

from spotils import meta
from spotils.config import Log

USER_LOG_PATH = (
    meta.APPLICATION_PATHS.user_log_path / f"{meta.__app_name__}.log"
)


class InterceptHandler(logging.Handler):
    """Intercept logs from logging into loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit the actual logrecords into logger."""
        # Get corresponding Loguru level if it exists.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    """
    Configure logging for this application.

    - Removes the preconfigured loguru logger.
    - Adds a handler for logging to a log file.
    """
    logging.basicConfig(
        handlers=[InterceptHandler()],
        level=logging.NOTSET,
        force=True,
    )
    logger.remove(0)
    logger.add(
        USER_LOG_PATH,
        level=Log.level,
        retention=Log.retention,
        rotation=Log.rotation,
    )
