"""
Structured logging configuration.

Applies JSON logging in production and human-readable format in development.
"""

from __future__ import annotations

import logging
import sys

from app.core.config import Settings


def setup_logging(settings: Settings) -> None:
    """Configure the root logger based on the environment."""

    level = logging.DEBUG if settings.debug else logging.INFO
    if settings.is_production:
        level = logging.WARNING

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    # Remove any existing handlers to avoid duplicate output
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)

    if settings.is_production:
        try:
            from pythonjsonlogger import jsonlogger
            # Use JSON formatting for production
            formatter = jsonlogger.JsonFormatter(fmt)
        except ImportError:
            formatter = logging.Formatter(fmt)
    else:
        formatter = logging.Formatter(fmt)

    handler.setFormatter(formatter)

    root.setLevel(level)
    root.addHandler(handler)

    # Quiet noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("appwrite").setLevel(logging.WARNING)
