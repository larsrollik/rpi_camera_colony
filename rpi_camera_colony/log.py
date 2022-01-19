import logging

from rich.logging import RichHandler


def log_level_name_to_value(name=None, default=20):
    """Translate log level name to corresponding value. Default is INFO==20"""
    return logging._nameToLevel.get(str(name).upper(), default)


def setup_logging_control(level=None):
    if level is None:
        level = "DEBUG"
    logger = logging.getLogger()

    if not logger.handlers:
        logger.setLevel(getattr(logging, level))

        formatter = logging.Formatter("%(message)s")
        formatter.datefmt = "%Y-%m-%d %H:%M:%S.%f"

        logging_handler = RichHandler(
            level=level,
            enable_link_path=False,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
        )
        logging_handler.setFormatter(formatter)
        logger.addHandler(logging_handler)
        logging.info(f"Set up logging for rcc with level {level}")
