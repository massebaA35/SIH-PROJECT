import logging
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)

    if not root_logger.handlers:
        root_logger.addHandler(console_handler)

    logging.getLogger("uvicorn.access").setLevel(LOG_LEVEL)
    logging.getLogger("uvicorn.error").setLevel(LOG_LEVEL)

    return root_logger

logger = setup_logging()
