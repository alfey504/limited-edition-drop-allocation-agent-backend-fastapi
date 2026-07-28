import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_DIR = Path("logs")
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

_configured = False


def configure_logging(level: int = logging.INFO) -> None:
    """Idempotent — safe to call multiple times (e.g. from multiple modules importing
    get_logger) without ending up with duplicate handlers on every log line."""
    global _configured
    if _configured:
        return

    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(_LOG_FORMAT)

    file_handler = RotatingFileHandler(
        _LOG_DIR / "app.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    app_logger = logging.getLogger("app")
    app_logger.setLevel(level)
    app_logger.addHandler(file_handler)
    app_logger.addHandler(console_handler)
    app_logger.propagate = False

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Pass __name__. Already namespaced under "app" (this package's own name),
    so it's naturally a descendant of the "app" logger configure_logging() sets
    handlers on — no extra prefix needed."""
    configure_logging()
    return logging.getLogger(name)
