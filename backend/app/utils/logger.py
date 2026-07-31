"""
Centralized logging configuration for AgriSense AI.
Provides structured logging with both console and file handlers.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(
    name: str = "agrisense",
    level: str = "INFO",
    log_file: str = "agrisense.log",
) -> logging.Logger:
    """
    Create and configure a logger with console and rotating file handlers.

    Args:
        name:     Logger name (shown in log lines).
        level:    Logging level string (DEBUG / INFO / WARNING / ERROR).
        log_file: Path to the rotating log file.

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers when the function is called multiple times
    if logger.handlers:
        return logger

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # ─── Formatter ────────────────────────────────────────────────────────────
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=date_fmt)

    # ─── Console Handler ──────────────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # ─── Rotating File Handler ────────────────────────────────────────────────
    try:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB per file
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as exc:
        logger.warning("Could not set up file logging: %s", exc)

    return logger


# ─── Module-level logger used across the application ─────────────────────────
logger = setup_logger()
