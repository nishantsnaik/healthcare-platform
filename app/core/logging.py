"""
Logging Configuration Module

This module configures structured logging for the application using structlog.
Structured logging means logs are written in a consistent format (usually JSON)
that makes them easier to parse, search, and analyze.

Why use structlog?
- Structured output: Logs are JSON objects, not plain text
- Context preservation: Automatically includes request IDs, user info, etc.
- Multiple output formats: JSON for production, pretty console for development
- Performance: Optimized for high-throughput applications

For beginners: This replaces Python's built-in logging with a more powerful
system that produces machine-readable logs.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.core.config import settings


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add application-specific context to all log entries.
    
    This is a custom processor that adds metadata to every log message.
    Processors are functions that transform log entries before they're output.
    
    Args:
        logger: The logger instance (unused but required by structlog)
        method_name: The logging method (info, debug, error, etc.)
        event_dict: The log entry data as a dictionary
        
    Returns:
        EventDict: The modified log entry with app context added
        
    Example:
        Input: {"message": "Alert created", "alert_id": 123}
        Output: {"message": "Alert created", "alert_id": 123, "app": "healthcare-platform", "environment": "development"}
    """
    event_dict["app"] = "healthcare-platform"
    event_dict["environment"] = "development"
    return event_dict


def drop_color_message_key(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Remove color message key for cleaner JSON output.
    
    The console renderer adds color information that we don't want in JSON logs.
    This processor removes that key when outputting JSON.
    
    Args:
        logger: The logger instance (unused)
        method_name: The logging method (unused)
        event_dict: The log entry data
        
    Returns:
        EventDict: The log entry without the color_message key
    """
    event_dict.pop("color_message", None)
    return event_dict


def configure_logging() -> None:
    """
    Configure structlog for the entire application.
    
    This function sets up the logging pipeline with processors that transform
    log entries. It supports two output formats:
    - JSON: Structured logs for production environments
    - Console: Pretty-colored logs for development
    
    The logging pipeline works like this:
    1. Log entry is created with message and data
    2. Processors transform the entry (add timestamp, log level, etc.)
    3. Renderer formats the entry (JSON or console)
    4. Output is written to stdout
    
    Returns:
        None
    """
    # Configure Python's standard logging library
    # This is the foundation that structlog builds upon
    logging.basicConfig(
        format="%(message)s",  # Simple format, structlog handles the rest
        stream=sys.stdout,     # Output to standard output
        level=getattr(logging, settings.log_level.upper()),  # Set log level from config
    )

    # Shared processors that run for all log entries
    # Processors are functions that transform log data in sequence
    shared_processors: list[Processor] = [
        # Merge context variables (set with structlog.contextvars.bind_contextvars)
        structlog.contextvars.merge_contextvars,
        # Add the log level (INFO, DEBUG, ERROR, etc.)
        structlog.processors.add_log_level,
        # Add ISO 8601 timestamp to each log entry
        structlog.processors.TimeStamper(fmt="iso"),
        # Add application-specific context
        add_app_context,
        # Add stack information when exceptions occur
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.log_format == "json":
        # JSON format for production
        # JSON logs are easier to parse and analyze with log aggregation tools
        structlog.configure(
            processors=shared_processors
            + [
                # Remove color codes for clean JSON
                drop_color_message_key,
                # Render as JSON
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,  # Performance optimization
        )
    else:
        # Console format for development
        # Pretty colored output for easier reading during development
        structlog.configure(
            processors=shared_processors
            + [
                # Pretty console output with colors
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance for a module.
    
    This function creates a logger with the given name. The name is typically
    the module name (__name__) which helps identify where log messages come from.
    
    Args:
        name: The name for the logger (usually __name__ of the module)
        
    Returns:
        structlog.stdlib.BoundLogger: A configured logger instance
        
    Example usage:
        logger = get_logger(__name__)
        logger.info("Alert created", alert_id=123)
    """
    return structlog.get_logger(name)
