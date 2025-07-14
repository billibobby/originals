"""
Enhanced Logging Configuration for The Originals
Provides structured logging with rotation and proper levels
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(app=None, log_level=None):
    """Setup comprehensive logging system"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Determine log level
    if log_level is None:
        log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[]
    )
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # File handler for all logs (with rotation)
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'the_originals.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(detailed_formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Error file handler (errors only)
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'errors.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_handler.setFormatter(detailed_formatter)
    error_handler.setLevel(logging.ERROR)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(simple_formatter)
    console_handler.setLevel(logging.INFO)
    
    # Get root logger and add handlers
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    
    # Flask app logger
    if app:
        app.logger.setLevel(logging.INFO)
    
    # Server operations logger
    server_logger = logging.getLogger('server')
    server_logger.setLevel(logging.INFO)
    
    # Security logger for authentication/authorization events
    security_logger = logging.getLogger('security')
    security_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'security.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=10  # Keep more security logs
    )
    security_handler.setFormatter(detailed_formatter)
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.INFO)
    
    # Update system logger
    update_logger = logging.getLogger('updates')
    update_logger.setLevel(logging.INFO)
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('paramiko').setLevel(logging.WARNING)
    
    print(f"[LOGGING] Enhanced logging configured - Level: {log_level}")
    print(f"[LOGGING] Log files: {log_dir.absolute()}")
    
    return {
        'file_handler': file_handler,
        'error_handler': error_handler,
        'console_handler': console_handler,
        'security_logger': security_logger,
        'server_logger': server_logger,
        'update_logger': update_logger
    }

def get_logger(name):
    """Get a configured logger by name"""
    return logging.getLogger(name)

def log_startup_info():
    """Log system startup information"""
    logger = logging.getLogger('startup')
    logger.info("="*50)
    logger.info("The Originals - Minecraft Server Manager v2.0.0")
    logger.info("="*50)
    logger.info(f"Startup time: {datetime.now().isoformat()}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Log level: {logging.getLogger().level}")
    logger.info("System ready for operation")
    logger.info("="*50)

def log_security_event(event_type, user, details="", level="INFO"):
    """Log security-related events"""
    security_logger = logging.getLogger('security')
    
    message = f"SECURITY_EVENT: {event_type} | User: {user} | Details: {details}"
    
    if level.upper() == "WARNING":
        security_logger.warning(message)
    elif level.upper() == "ERROR":
        security_logger.error(message)
    elif level.upper() == "CRITICAL":
        security_logger.critical(message)
    else:
        security_logger.info(message)

def log_server_event(event_type, details="", level="INFO"):
    """Log server operation events"""
    server_logger = logging.getLogger('server')
    
    message = f"SERVER_EVENT: {event_type} | Details: {details}"
    
    if level.upper() == "WARNING":
        server_logger.warning(message)
    elif level.upper() == "ERROR":
        server_logger.error(message)
    else:
        server_logger.info(message)

def log_update_event(event_type, version="", details="", level="INFO"):
    """Log update system events"""
    update_logger = logging.getLogger('updates')
    
    message = f"UPDATE_EVENT: {event_type} | Version: {version} | Details: {details}"
    
    if level.upper() == "WARNING":
        update_logger.warning(message)
    elif level.upper() == "ERROR":
        update_logger.error(message)
    else:
        update_logger.info(message) 