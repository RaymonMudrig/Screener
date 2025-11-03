"""
Logging utilities for stock screener
Provides centralized logging configuration using loguru
"""

import sys
from pathlib import Path
from loguru import logger


# Remove default handler
logger.remove()

# Configuration (will be loaded from config file)
_initialized = False


def init_logger(
    log_file: str = "logs/screener.log",
    level: str = "INFO",
    max_size: str = "10MB",
    backup_count: int = 5,
    console_output: bool = True,
    log_format: str = None
) -> None:
    """
    Initialize logger with configuration

    Args:
        log_file: Path to log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        max_size: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        console_output: Whether to output to console
        log_format: Custom log format
    """
    global _initialized

    if _initialized:
        return

    # Default format
    if log_format is None:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Add console handler
    if console_output:
        logger.add(
            sys.stderr,
            format=log_format,
            level=level,
            colorize=True
        )

    # Add file handler with rotation
    logger.add(
        log_file,
        format=log_format,
        level=level,
        rotation=max_size,
        retention=backup_count,
        compression="zip",
        encoding="utf-8"
    )

    _initialized = True
    logger.info("Logger initialized")


def get_logger(name: str = None):
    """
    Get a logger instance

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        Logger instance
    """
    global _initialized

    # Initialize with defaults if not already done
    if not _initialized:
        try:
            # Try to load config
            from .config import get_config
            config = get_config()
            logging_config = config.logging

            init_logger(
                log_file=logging_config.get('file', 'logs/screener.log'),
                level=logging_config.get('level', 'INFO'),
                max_size=logging_config.get('max_size', '10MB'),
                backup_count=logging_config.get('backup_count', 5),
                console_output=logging_config.get('console_output', True),
                log_format=logging_config.get('format')
            )
        except Exception:
            # Fallback to default configuration
            init_logger()

    if name:
        return logger.bind(name=name)
    return logger


# Convenience logging functions
def debug(message: str, **kwargs):
    """Log debug message"""
    logger.debug(message, **kwargs)


def info(message: str, **kwargs):
    """Log info message"""
    logger.info(message, **kwargs)


def warning(message: str, **kwargs):
    """Log warning message"""
    logger.warning(message, **kwargs)


def error(message: str, **kwargs):
    """Log error message"""
    logger.error(message, **kwargs)


def critical(message: str, **kwargs):
    """Log critical message"""
    logger.critical(message, **kwargs)


def exception(message: str, **kwargs):
    """Log exception with traceback"""
    logger.exception(message, **kwargs)
