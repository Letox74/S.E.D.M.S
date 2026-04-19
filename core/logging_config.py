import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent.resolve() / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_file_handler(filename: str | Path, formatter: logging.Formatter) -> RotatingFileHandler:
    handler = RotatingFileHandler(filename, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")  # max 5MB
    handler.setFormatter(formatter)
    return handler


def get_formatter_and_console_handler():
    log_format = "[%(name)s] - %(levelname)s - %(asctime)s: %(message)s"  # example: [app] - INFO - 2026-04-15: App started
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, date_format)

    console_handler = logging.StreamHandler()  # add console handler to write to the console
    console_handler.setFormatter(formatter)

    return console_handler, formatter


def setup_single_logger(
        logger: logging.Logger,
        filename: Path | str,
        level: logging.INFO | logging.ERROR = logging.INFO
) -> None:
    console_handler, formatter = get_formatter_and_console_handler()

    logger.setLevel(level)
    logger.addHandler(console_handler)
    logger.addHandler(get_file_handler(filename, formatter))
    #logger.propagate = False  # does not send logs to the root


def setup_logging():
    # Root Logger
    root_logger = logging.getLogger("App")
    setup_single_logger(root_logger, LOG_DIR / "app.log")

    # Error Logger
    error_logger = logging.getLogger("Error")
    setup_single_logger(error_logger, LOG_DIR / "error.log", logging.ERROR)

    # API Logger
    api_logger = logging.getLogger("Api")
    setup_single_logger(api_logger, LOG_DIR / "api.log")

    # Telemetry Logger
    telemetry_logger = logging.getLogger("Telemetry")
    setup_single_logger(telemetry_logger, LOG_DIR / "telemetry.log")
