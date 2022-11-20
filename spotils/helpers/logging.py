"""Project logging utilites."""
import logging

from loguru import logger


class InterceptHandler(logging.Handler):
    """Intercept logs from logging into loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit the actual logrecords into logger."""
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )
