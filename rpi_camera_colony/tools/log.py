import logging


def log_level_name_to_value(name=None, default=20):
    """Translate log level name to corresponding value. Default is INFO==20"""
    return logging._nameToLevel.get(str(name).upper(), default)


def setup_logging_control(level=None):
    if level is None:
        level = "DEBUG"
    logger = logging.getLogger()

    if not logger.handlers:
        logger.setLevel(getattr(logging, level))

        formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d - %(levelname)s"
            " - %(processName)s %(filename)s:%(lineno)s"
            " - %(message)s"
        )
        formatter.datefmt = "%Y-%m-%d %H:%M:%S"

        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(getattr(logging, level))
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        logging.info(f"Set up logging for rcc with level {level}")
