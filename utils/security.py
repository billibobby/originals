"""
Security utilities for The Originals.
Provides secure command validation, input sanitization, and security helpers.
"""

import re
import shlex
import os
import secrets
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from functools import wraps
from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)

# Whitelist of allowed Minecraft server commands
ALLOWED_SERVER_COMMANDS = {
    'list', 'tps', 'help', 'say', 'tell', 'gamemode', 'tp', 'give', 'time',
    'stop', 'save-all', 'save-on', 'save-off', 'reload', 'weather', 'seed',
    'difficulty', 'gamerule', 'effect', 'enchant', 'experience', 'xp',
    'summon', 'kill', 'teleport', 'setblock', 'fill', 'clone'
}

# Valid gamemode values
VALID_GAMEMODES = {
    'survival', 'creative', 'adventure', 'spectator', 
    '0', '1', '2', '3'
}

# Valid difficulty values  
VALID_DIFFICULTIES = {
    'peaceful', 'easy', 'normal', 'hard',
    '0', '1', '2', '3'
}


def validate_server_command(command: str) -> Tuple[bool, str]:
    """
    Validate and sanitize a Minecraft server command.
    
    Args:
        command: Raw command string from user input
        
    Returns:
        Tuple of (is_valid, error_message_or_sanitized_command)
    """
    if not command or not isinstance(command, str):
        return False, "Empty or invalid command"
    
    command = command.strip()
    if not command:
        return False, "Empty command"
    
    # Split command safely using shlex
    try:
        parts = shlex.split(command)
    except ValueError as e:
        logger.warning(f"Invalid command format: {command} - {e}")
        return False, f"Invalid command format: {str(e)}"
    
    if not parts:
        return False, "Empty command"
    
    base_command = parts[0].lower()
    
    # Check if command is allowed
    if base_command not in ALLOWED_SERVER_COMMANDS:
        logger.warning(f"Unauthorized command attempted: {base_command}")
        return False, f"Command '{base_command}' is not allowed"
    
    # Validate specific command arguments
    validation_result = _validate_command_arguments(base_command, parts[1:])
    if not validation_result[0]:
        return validation_result
    
    # Return the sanitized command
    safe_command = ' '.join(parts)
    return True, safe_command


def _validate_command_arguments(command: str, args: list) -> Tuple[bool, str]:
    """Validate arguments for specific commands."""
    
    if command == 'gamemode':
        if len(args) < 1:
            return False, "gamemode requires a mode argument"
        if args[0].lower() not in VALID_GAMEMODES:
            return False, f"Invalid gamemode: {args[0]}"
    
    elif command == 'difficulty':
        if len(args) >= 1 and args[0].lower() not in VALID_DIFFICULTIES:
            return False, f"Invalid difficulty: {args[0]}"
    
    elif command == 'tell':
        if len(args) < 2:
            return False, "tell requires a player and message"
        # Validate player name (basic alphanumeric + underscore)
        if not re.match(r'^[a-zA-Z0-9_]{1,16}$', args[0]):
            return False, "Invalid player name"
    
    elif command == 'give':
        if len(args) < 2:
            return False, "give requires a player and item"
        # Validate player name
        if not re.match(r'^[a-zA-Z0-9_]{1,16}$', args[0]):
            return False, "Invalid player name"
        # Validate item (basic minecraft item format)
        if not re.match(r'^[a-zA-Z0-9_:]{1,50}$', args[1]):
            return False, "Invalid item name"
    
    elif command in ['tp', 'teleport']:
        if len(args) < 1:
            return False, f"{command} requires at least a target"
        # Validate player names
        for arg in args[:2]:  # First two args are usually players
            if not re.match(r'^[a-zA-Z0-9_~@]{1,16}$', arg):
                return False, f"Invalid target: {arg}"
    
    return True, "Valid command"


def sanitize_filename(filename: str, allowed_extensions: Optional[set] = None) -> Tuple[bool, str]:
    """
    Sanitize a filename for safe file operations.
    
    Args:
        filename: The filename to sanitize
        allowed_extensions: Set of allowed file extensions (e.g., {'.jar', '.zip'})
        
    Returns:
        Tuple of (is_valid, error_message_or_sanitized_filename)
    """
    if not filename or not isinstance(filename, str):
        return False, "Invalid filename"
    
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        logger.warning(f"Path traversal attempt detected: {filename}")
        return False, "Invalid filename: path traversal detected"
    
    # Check for null bytes and other dangerous characters
    if '\x00' in filename or any(c in filename for c in '<>:"|?*'):
        return False, "Invalid filename: contains dangerous characters"
    
    # Validate file extension if specified
    if allowed_extensions:
        file_path = Path(filename)
        if file_path.suffix.lower() not in allowed_extensions:
            return False, f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}"
    
    # Basic filename validation
    if not re.match(r'^[a-zA-Z0-9_\-\.]{1,255}$', filename):
        return False, "Invalid filename format"
    
    return True, filename


def validate_file_path(file_path: str, base_directory: str) -> Tuple[bool, str]:
    """
    Validate that a file path is within the allowed base directory.
    
    Args:
        file_path: The file path to validate
        base_directory: The base directory that files must be within
        
    Returns:
        Tuple of (is_valid, error_message_or_resolved_path)
    """
    try:
        # Resolve paths to absolute paths
        base_path = Path(base_directory).resolve()
        target_path = (base_path / file_path).resolve()
        
        # Check if target path is within base directory
        if not str(target_path).startswith(str(base_path)):
            logger.warning(f"Path traversal attempt: {file_path} outside {base_directory}")
            return False, "Path is outside allowed directory"
        
        return True, str(target_path)
    
    except (OSError, ValueError) as e:
        logger.error(f"Path validation error: {e}")
        return False, "Invalid path"


def generate_secure_secret() -> str:
    """Generate a cryptographically secure secret key."""
    return secrets.token_urlsafe(32)


def validate_input(schema: Dict[str, Dict[str, Any]]):
    """
    Decorator to validate request input against a schema.
    
    Args:
        schema: Dictionary defining validation rules for each field
        
    Example:
        @validate_input({
            'username': {'type': str, 'pattern': r'^[a-zA-Z0-9_]{3,20}$', 'required': True},
            'port': {'type': str, 'pattern': r'^\d{1,5}$', 'required': True}
        })
        def my_endpoint():
            pass
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if request.is_json:
                data = request.get_json() or {}
            else:
                data = request.form.to_dict()
            
            # Validate each field in schema
            for field, rules in schema.items():
                value = data.get(field)
                
                # Check if required
                if rules.get('required', False) and not value:
                    return jsonify({'success': False, 'error': f'{field} is required'}), 400
                
                # Skip validation if field is not provided and not required
                if value is None:
                    continue
                
                # Check type
                expected_type = rules.get('type')
                if expected_type and not isinstance(value, expected_type):
                    return jsonify({
                        'success': False, 
                        'error': f'{field} must be {expected_type.__name__}'
                    }), 400
                
                # Check length
                max_length = rules.get('max_length')
                if max_length and len(str(value)) > max_length:
                    return jsonify({
                        'success': False,
                        'error': f'{field} too long (max {max_length} characters)'
                    }), 400
                
                min_length = rules.get('min_length')
                if min_length and len(str(value)) < min_length:
                    return jsonify({
                        'success': False,
                        'error': f'{field} too short (min {min_length} characters)'
                    }), 400
                
                # Check pattern
                pattern = rules.get('pattern')
                if pattern and not re.match(pattern, str(value)):
                    return jsonify({
                        'success': False,
                        'error': f'{field} format is invalid'
                    }), 400
                
                # Check allowed values
                allowed_values = rules.get('allowed_values')
                if allowed_values and value not in allowed_values:
                    return jsonify({
                        'success': False,
                        'error': f'{field} must be one of: {", ".join(map(str, allowed_values))}'
                    }), 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


def check_rate_limit(requests_per_minute: int = 60):
    """
    Simple rate limiting decorator.
    
    Args:
        requests_per_minute: Maximum requests per minute per IP
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # This is a placeholder - in production, use Redis or similar
            # For now, we'll rely on Flask-Limiter which is configured in the main app
            return f(*args, **kwargs)
        return wrapper
    return decorator


def log_security_event(event_type: str, details: Dict[str, Any], user_id: Optional[int] = None):
    """
    Log security-related events for monitoring.
    
    Args:
        event_type: Type of security event (e.g., 'failed_login', 'command_injection_attempt')
        details: Additional details about the event
        user_id: User ID if applicable
    """
    from flask import request, g
    
    from datetime import datetime
    
    log_data = {
        'event_type': event_type,
        'timestamp': datetime.now().isoformat(),
        'ip_address': request.remote_addr if request else 'unknown',
        'user_agent': request.headers.get('User-Agent') if request else 'unknown',
        'user_id': user_id or getattr(g, 'user_id', None),
        'details': details
    }
    
    logger.warning(f"SECURITY EVENT: {event_type} - {log_data}") 