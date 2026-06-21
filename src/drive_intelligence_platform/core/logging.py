"""Structured logging configuration."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


def configure_logging(level: str, log_dir: Path) -> None:
    """Configure application logging to console and file."""

    log_dir.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(sys.stderr, level=level, backtrace=False, diagnose=False)
    logger.add(log_dir / "drive_intelligence.log", rotation="10 MB", retention="14 days")