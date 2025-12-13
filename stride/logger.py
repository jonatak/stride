"""Logger contains helper to initialise and override loggers."""

import inspect
import logging
import sys

from loguru import logger


class InterceptHandler(logging.Handler):
    """Intercepter provided fron loguru documentation.

    This intercepter allow the retro compatibility and use of the default python logger.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists.
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame:
            filename = frame.f_code.co_filename
            is_logging = filename == logging.__file__
            is_frozen = "importlib" in filename and "_bootstrap" in filename
            if depth > 0 and not (is_logging or is_frozen):
                break
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def init_logging_override():
    """helper to help override uvicorn logger with new InterceptHandler."""
    intercept_handler = InterceptHandler()
    loggers = (
        logging.getLogger(name)
        for name in logging.root.manager.loggerDict
        if name.startswith("uvicorn.")
    )
    for uvicorn_logger in loggers:
        uvicorn_logger.handlers = [intercept_handler]

    # change handler for default uvicorn logger
    logging.getLogger("uvicorn").handlers.clear()


def init_logger(
    level: str = "INFO",
    format: str = "{time:YYYY-MM-DDTHH:mm:ss}Z {level} {name}:{line} [{extra}] {message}",
):
    """init_logger initialise the global logger.

    Args:
        level (str): level can be of value DEBUG, INFO, WARN, ERROR.
        format (str): The expected log format output.
    """
    assert level in ("DEBUG", "INFO", "WARN", "ERROR")
    logger.configure(
        handlers=[
            {
                "sink": sys.stdout,
                "format": format,
                "level": level,
                "serialize": False,
                "filter": None,
            }
        ]
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
