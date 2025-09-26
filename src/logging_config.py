"""Logging configuration for industry news agent."""
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    show_file_line: bool = True,
    show_function: bool = True
) -> None:
    """
    Setup logging configuration with customizable format.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        show_file_line: Whether to show file name and line number
        show_function: Whether to show function name
    """
    # Convert string level to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Build format string based on options
    format_parts = [
        '%(asctime)s',
        '%(name)s',
        '%(levelname)s'
    ]
    
    if show_file_line:
        format_parts.append('%(filename)s:%(lineno)d')
    
    if show_function:
        format_parts.append('%(funcName)s')
    
    format_parts.append('%(message)s')
    
    log_format = ' - '.join(format_parts)
    
    # Configure basic logging
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[]
    )
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(console_formatter)
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(file_formatter)
        
        # Add both handlers to root logger
        root_logger = logging.getLogger()
        root_logger.handlers.clear()  # Clear existing handlers
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
        root_logger.setLevel(numeric_level)
    else:
        # Only console handler
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.addHandler(console_handler)
        root_logger.setLevel(numeric_level)
    
    # Set specific logger levels
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('anyio').setLevel(logging.WARNING)
    
    # Set Tencent Cloud SDK loggers to WARNING level to reduce noise
    logging.getLogger('tencentcloud_sdk_common').setLevel(logging.WARNING)
    logging.getLogger('tencentcloud').setLevel(logging.WARNING)
    
    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {log_level}, File: {log_file or 'Console only'}")
    if show_file_line:
        logger.info("File and line numbers are enabled in log messages")
    if show_function:
        logger.info("Function names are enabled in log messages")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def set_log_level(logger_name: str, level: str) -> None:
    """
    Set log level for a specific logger.
    
    Args:
        logger_name: Name of the logger to configure
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger(logger_name).setLevel(numeric_level)


def enable_debug_logging() -> None:
    """Enable debug logging for all loggers."""
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info("Debug logging enabled for all loggers")


def disable_debug_logging() -> None:
    """Disable debug logging, set to INFO level."""
    logging.getLogger().setLevel(logging.INFO)
    logging.info("Debug logging disabled, set to INFO level")


def set_tencent_sdk_log_level(level: str = "WARNING") -> None:
    """
    Set log level specifically for Tencent Cloud SDK loggers.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, level.upper(), logging.WARNING)
    
    # Set Tencent Cloud SDK loggers
    logging.getLogger('tencentcloud_sdk_common').setLevel(numeric_level)
    logging.getLogger('tencentcloud').setLevel(numeric_level)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Tencent Cloud SDK log level set to {level}")


def enable_tencent_sdk_debug() -> None:
    """Enable debug logging for Tencent Cloud SDK."""
    set_tencent_sdk_log_level("DEBUG")


def disable_tencent_sdk_debug() -> None:
    """Disable debug logging for Tencent Cloud SDK, set to WARNING."""
    set_tencent_sdk_log_level("WARNING")
