"""
Rich-based logging utilities with colors, emojis, and structured output.

Designed for both human operators and AI agent consumption.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Custom theme for teanga logging
TEANGA_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "critical": "bold white on red",
    "debug": "dim cyan",
    "success": "bold green",
})

# Emoji prefixes for log levels
EMOJI_MAP = {
    "DEBUG": "🔍",
    "INFO": "🟢",
    "WARNING": "⚠️ ",
    "ERROR": "❌",
    "CRITICAL": "🔥",
}


class EmojiRichHandler(RichHandler):
    """RichHandler with emoji prefixes for better visual scanning."""

    def get_level_text(self, record: logging.LogRecord) -> str:
        """Add emoji prefix to level name."""
        level_name = record.levelname
        emoji = EMOJI_MAP.get(level_name, "")
        return f"{emoji} {level_name}"


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[Path] = None,
    rich_tracebacks: bool = True,
) -> logging.Logger:
    """
    Configure a logger with rich console output and optional file logging.

    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to write logs to file
        rich_tracebacks: Enable rich exception formatting

    Returns:
        Configured logger instance

    Example:
        >>> from teanga.utils.logging import setup_logger
        >>> logger = setup_logger(__name__, level="DEBUG")
        >>> logger.info("Processing episode", extra={"episode_id": "rnag_nuacht_123"})
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler with rich formatting
    console = Console(theme=TEANGA_THEME, stderr=True)
    console_handler = EmojiRichHandler(
        console=console,
        show_time=True,
        show_path=True,
        rich_tracebacks=rich_tracebacks,
        tracebacks_show_locals=True,
        markup=True,
    )
    console_handler.setLevel(getattr(logging, level.upper()))
    logger.addHandler(console_handler)

    # Optional file handler (plain text for machine parsing)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always capture full debug in files
        file_formatter = logging.Formatter(
            fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with default teanga configuration.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    # If logger has no handlers, set it up with defaults
    if not logger.handlers:
        return setup_logger(name)

    return logger
