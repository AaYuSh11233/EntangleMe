import logging

_PACKAGE_NAME = __name__.split(".", maxsplit=1)[0]


def add_stderr_logger(level: int = logging.DEBUG) -> logging.StreamHandler:
    """
    Helper for quickly adding a StreamHandler to the logger. Useful for
    debugging.
    Returns the handler after adding it.
    """
    logger = logging.getLogger(_PACKAGE_NAME)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.debug("Added a stderr logging handler to logger: %s", logger.name)
    return handler
