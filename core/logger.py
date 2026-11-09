"""
AI-CONTENT-AUTOMATION — Logging Setup
======================================
Centralised logging using loguru.
All modules should import the logger from here.

Usage:
    from core.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Something happened")
    logger.error("Something failed: {error}", error=str(e))
"""

import sys
from pathlib import Path
from loguru import logger as _base_logger


# ── Log directory ─────────────────────────────────────────────────────────────
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ── Remove default loguru handler ─────────────────────────────────────────────
_base_logger.remove()

# ── Console output (clean, coloured) ─────────────────────────────────────────
_base_logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>",
    level="DEBUG",
    colorize=True,
    backtrace=True,
    diagnose=True,
)

# ── Main application log (all levels) ────────────────────────────────────────
_base_logger.add(
    LOG_DIR / "app.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} — {message}",
    level="DEBUG",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
)

# ── Error-only log ────────────────────────────────────────────────────────────
_base_logger.add(
    LOG_DIR / "errors.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} — {message}\n{exception}",
    level="ERROR",
    rotation="5 MB",
    retention="90 days",
    compression="zip",
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
)

# ── Scheduler log (separate file) ────────────────────────────────────────────
_scheduler_logger = _base_logger.bind(module="scheduler")
_scheduler_logger.add(
    LOG_DIR / "scheduler.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    level="INFO",
    filter=lambda record: record["extra"].get("module") == "scheduler",
    rotation="5 MB",
    retention="30 days",
    encoding="utf-8",
)

# ── Publishing log ────────────────────────────────────────────────────────────
_publish_logger = _base_logger.bind(module="publishing")
_publish_logger.add(
    LOG_DIR / "publishing.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    level="INFO",
    filter=lambda record: record["extra"].get("module") == "publishing",
    rotation="5 MB",
    retention="30 days",
    encoding="utf-8",
)


def get_logger(name: str):
    """
    Returns a bound logger for the given module name.
    Use this in every module instead of importing loguru directly.

    Example:
        logger = get_logger(__name__)
        logger.info("Module started")
    """
    return _base_logger.bind(name=name)


def get_scheduler_logger():
    """Returns the scheduler-specific logger."""
    return _base_logger.bind(module="scheduler", name="scheduler")


def get_publishing_logger():
    """Returns the publishing-specific logger."""
    return _base_logger.bind(module="publishing", name="publishing")
