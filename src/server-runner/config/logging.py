import logging
from collections.abc import Sequence
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# ------------------------
# Defaults / Constants
# ------------------------
DEFAULT_LOG_DIR = Path("logs")
DEFAULT_LOG_FILE = "app.log"
DEFAULT_LOG_LEVEL = logging.DEBUG
DEFAULT_BACKUP_COUNT = 7
DEFAULT_DISABLED_LOGGERS = ["schedule"]
LOG_FORMAT = (
    "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(module)s - %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    log_dir: Path = DEFAULT_LOG_DIR,
    log_file_name: str = DEFAULT_LOG_FILE,
    level: int = DEFAULT_LOG_LEVEL,
    disable_loggers: Sequence[str] | None = None,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    extra_handlers: list[logging.Handler] | None = None,
) -> None:
    """
    Configure root logger once for the application.
    Modules should call get_logger() to retrieve their own logger.
    """
    if disable_loggers is None:
        disable_loggers = DEFAULT_DISABLED_LOGGERS

    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir / log_file_name

    # Disable noisy loggers
    for logger_name in disable_loggers:
        logging.getLogger(logger_name).disabled = True

    # Handlers
    file_handler = TimedRotatingFileHandler(
        log_file_path, when="midnight", interval=1, backupCount=backup_count
    )
    file_handler.setLevel(level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)

    handlers: list[logging.Handler] = [file_handler, stream_handler]
    if extra_handlers:
        handlers.extend(extra_handlers)

    # Root logger configuration
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=handlers,
    )


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Return a module-level logger.
    Defaults to the calling module's name if not provided.
    """
    if name is None:
        import inspect

        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        name = module.__name__ if module else "__main__"
    return logging.getLogger(name)
