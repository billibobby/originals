"""
Logging configuration for The Originals.
Provides centralized logging setup with security event tracking.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_console: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up application logging with file rotation and console output.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (default: logs/app.log)
        enable_console: Whether to enable console logging
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
        
    Returns:
        Configured logger instance
    """
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Default log file path
    if log_file is None:
        log_file = str(log_dir / "app.log")
    else:
        log_file = str(Path(log_file))
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Add file handler with rotation
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        logger.addHandler(file_handler)
    
    # Add console handler
    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        logger.addHandler(console_handler)
    
    # Set up specific loggers
    _setup_security_logger(log_dir, formatter)
    _setup_server_logger(log_dir, formatter)
    
    logger.info("Logging system initialized")
    return logger


def _setup_security_logger(log_dir: Path, formatter: logging.Formatter):
    """Set up dedicated security event logger."""
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.WARNING)
    
    # Security events get their own log file
    security_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "security.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=10,
        encoding='utf-8'
    )
    
    security_formatter = logging.Formatter(
        fmt='%(asctime)s - SECURITY - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    security_handler.setFormatter(security_formatter)
    security_logger.addHandler(security_handler)
    security_logger.propagate = False  # Don't propagate to root logger


def _setup_server_logger(log_dir: Path, formatter: logging.Formatter):
    """Set up dedicated Minecraft server logger."""
    server_logger = logging.getLogger('minecraft_server')
    server_logger.setLevel(logging.INFO)
    
    # Server logs get their own file
    server_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "server.log",
        maxBytes=20 * 1024 * 1024,  # 20MB
        backupCount=5,
        encoding='utf-8'
    )
    
    server_handler.setFormatter(formatter)
    server_logger.addHandler(server_handler)
    server_logger.propagate = False  # Don't propagate to root logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (usually __name__ of the module)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_server_event(message: str, level: str = "INFO"):
    """
    Log a Minecraft server event.
    
    Args:
        message: Log message
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    server_logger = logging.getLogger('minecraft_server')
    log_method = getattr(server_logger, level.lower())
    log_method(message)


def log_security_event(event_type: str, message: str, level: str = "WARNING"):
    """
    Log a security event.
    
    Args:
        event_type: Type of security event
        message: Log message
        level: Log level (WARNING, ERROR, CRITICAL)
    """
    security_logger = logging.getLogger('security')
    log_method = getattr(security_logger, level.lower())
    log_method(f"[{event_type}] {message}")


class ContextFilter(logging.Filter):
    """
    Add context information to log records.
    """
    
    def filter(self, record):
        """Add context information to the log record."""
        try:
            from flask import request, g
            
            # Add request context if available
            if request:
                record.ip_address = request.remote_addr
                record.user_agent = request.headers.get('User-Agent', 'Unknown')
                record.endpoint = request.endpoint
                record.method = request.method
                record.url = request.url
            else:
                record.ip_address = 'N/A'
                record.user_agent = 'N/A'
                record.endpoint = 'N/A'
                record.method = 'N/A'
                record.url = 'N/A'
            
            # Add user context if available
            record.user_id = getattr(g, 'user_id', 'N/A')
            record.username = getattr(g, 'username', 'N/A')
            
        except (RuntimeError, ImportError):
            # Outside of request context or Flask not available
            record.ip_address = 'N/A'
            record.user_agent = 'N/A'
            record.endpoint = 'N/A'
            record.method = 'N/A'
            record.url = 'N/A'
            record.user_id = 'N/A'
            record.username = 'N/A'
        
        return True


def setup_request_logging():
    """Set up request-specific logging with context."""
    
    # Add context filter to all handlers
    context_filter = ContextFilter()
    
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(context_filter)
    
    # Enhanced formatter with context
    enhanced_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(ip_address)s] [%(username)s] [%(method)s %(endpoint)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Update formatters for existing handlers
    for handler in root_logger.handlers:
        handler.setFormatter(enhanced_formatter) 