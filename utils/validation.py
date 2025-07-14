"""
Input validation utilities for The Originals.
Provides comprehensive validation for user inputs and configuration.
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass
import ipaddress


@dataclass
class ValidationRule:
    """Defines a validation rule for input fields."""
    required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    data_type: Optional[type] = None
    custom_validator: Optional[Callable[[Any], bool]] = None


class InputValidator:
    """Comprehensive input validation system."""
    
    # Common validation patterns
    PATTERNS = {
        'username': r'^[a-zA-Z0-9_]{3,20}$',
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'port': r'^\d{1,5}$',
        'ip_address': r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
        'minecraft_version': r'^\d+\.\d+(?:\.\d+)?$',
        'filename': r'^[a-zA-Z0-9_\-\.]{1,255}$',
        'server_name': r'^[a-zA-Z0-9_\-\s]{3,50}$',
        'password': r'^.{8,128}$',  # Basic length check, more rules in validator
        'hex_color': r'^#[0-9A-Fa-f]{6}$',
        'uuid': r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    }
    
    # Server configuration validation rules
    SERVER_CONFIG_RULES = {
        'server-port': ValidationRule(
            required=True,
            pattern=PATTERNS['port'],
            custom_validator=lambda x: 1024 <= int(x) <= 65535
        ),
        'rcon.port': ValidationRule(
            required=False,
            pattern=PATTERNS['port'],
            custom_validator=lambda x: 1024 <= int(x) <= 65535
        ),
        'max-players': ValidationRule(
            required=True,
            pattern=r'^\d{1,3}$',
            custom_validator=lambda x: 1 <= int(x) <= 999
        ),
        'motd': ValidationRule(
            required=False,
            max_length=100,
            pattern=r'^[^§]*$'  # No section signs (Minecraft formatting)
        ),
        'difficulty': ValidationRule(
            required=False,
            allowed_values=['peaceful', 'easy', 'normal', 'hard', '0', '1', '2', '3']
        ),
        'gamemode': ValidationRule(
            required=False,
            allowed_values=['survival', 'creative', 'adventure', 'spectator', '0', '1', '2', '3']
        ),
        'level-name': ValidationRule(
            required=False,
            pattern=r'^[a-zA-Z0-9_\-]{1,50}$'
        ),
        'seed': ValidationRule(
            required=False,
            pattern=r'^-?\d{1,19}$'  # Long integer range
        ),
        'view-distance': ValidationRule(
            required=False,
            pattern=r'^\d{1,2}$',
            custom_validator=lambda x: 3 <= int(x) <= 32
        ),
        'simulation-distance': ValidationRule(
            required=False,
            pattern=r'^\d{1,2}$',
            custom_validator=lambda x: 3 <= int(x) <= 32
        ),
        'spawn-protection': ValidationRule(
            required=False,
            pattern=r'^\d{1,3}$',
            custom_validator=lambda x: 0 <= int(x) <= 999
        )
    }
    
    # User registration/profile validation rules
    USER_RULES = {
        'username': ValidationRule(
            required=True,
            pattern=PATTERNS['username'],
            min_length=3,
            max_length=20
        ),
        'email': ValidationRule(
            required=True,
            pattern=PATTERNS['email'],
            max_length=120
        ),
        'password': ValidationRule(
            required=True,
            min_length=8,
            max_length=128,
            custom_validator=lambda x: _validate_password_strength(x)
        ),
        'display_name': ValidationRule(
            required=False,
            pattern=r'^[a-zA-Z0-9_\-\s]{3,50}$',
            max_length=50
        ),
        'role': ValidationRule(
            required=False,
            allowed_values=['admin', 'moderator', 'user']
        )
    }
    
    # Node management validation rules
    NODE_RULES = {
        'name': ValidationRule(
            required=True,
            pattern=PATTERNS['server_name'],
            min_length=3,
            max_length=50
        ),
        'ip_address': ValidationRule(
            required=True,
            custom_validator=lambda x: _validate_ip_address(x)
        ),
        'port': ValidationRule(
            required=True,
            pattern=PATTERNS['port'],
            custom_validator=lambda x: 1024 <= int(x) <= 65535
        ),
        'ssh_port': ValidationRule(
            required=False,
            pattern=PATTERNS['port'],
            custom_validator=lambda x: 1 <= int(x) <= 65535
        ),
        'ssh_username': ValidationRule(
            required=False,
            pattern=r'^[a-zA-Z0-9_\-]{1,32}$'
        )
    }
    
    def __init__(self):
        """Initialize the validator."""
        pass
    
    def validate_data(self, data: Dict[str, Any], rules: Dict[str, ValidationRule]) -> Tuple[bool, Dict[str, str]]:
        """
        Validate data against a set of rules.
        
        Args:
            data: Dictionary of data to validate
            rules: Dictionary of validation rules
            
        Returns:
            Tuple of (is_valid, errors_dict)
        """
        errors = {}
        
        for field, rule in rules.items():
            value = data.get(field)
            error = self._validate_field(field, value, rule)
            if error:
                errors[field] = error
        
        return len(errors) == 0, errors
    
    def _validate_field(self, field: str, value: Any, rule: ValidationRule) -> Optional[str]:
        """Validate a single field against its rule."""
        
        # Check if required
        if rule.required and (value is None or value == ''):
            return f"{field} is required"
        
        # Skip validation if field is not provided and not required
        if value is None or value == '':
            return None
        
        # Convert to string for string-based validations
        str_value = str(value)
        
        # Check data type
        if rule.data_type and not isinstance(value, rule.data_type):
            return f"{field} must be of type {rule.data_type.__name__}"
        
        # Check length constraints
        if rule.min_length and len(str_value) < rule.min_length:
            return f"{field} must be at least {rule.min_length} characters"
        
        if rule.max_length and len(str_value) > rule.max_length:
            return f"{field} must be no more than {rule.max_length} characters"
        
        # Check pattern
        if rule.pattern and not re.match(rule.pattern, str_value):
            return f"{field} format is invalid"
        
        # Check allowed values
        if rule.allowed_values and value not in rule.allowed_values:
            return f"{field} must be one of: {', '.join(map(str, rule.allowed_values))}"
        
        # Check custom validator
        if rule.custom_validator:
            try:
                if not rule.custom_validator(value):
                    return f"{field} failed custom validation"
            except Exception as e:
                return f"{field} validation error: {str(e)}"
        
        return None
    
    def validate_server_config(self, config: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        """Validate server configuration."""
        return self.validate_data(config, self.SERVER_CONFIG_RULES)
    
    def validate_user_data(self, user_data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        """Validate user registration/profile data."""
        return self.validate_data(user_data, self.USER_RULES)
    
    def validate_node_data(self, node_data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        """Validate node configuration data."""
        return self.validate_data(node_data, self.NODE_RULES)


def _validate_password_strength(password: str) -> bool:
    """
    Validate password strength.
    
    Requirements:
    - At least 8 characters
    - Contains uppercase and lowercase letters
    - Contains at least one number
    - Contains at least one special character
    """
    if len(password) < 8:
        return False
    
    has_upper = re.search(r'[A-Z]', password)
    has_lower = re.search(r'[a-z]', password)
    has_digit = re.search(r'\d', password)
    has_special = re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
    
    return bool(has_upper and has_lower and has_digit and has_special)


def _validate_ip_address(ip: str) -> bool:
    """Validate IP address format."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_minecraft_command(command: str) -> Tuple[bool, str]:
    """
    Validate a Minecraft server command.
    This is a wrapper around the security module's validation.
    """
    from .security import validate_server_command
    return validate_server_command(command)


def validate_file_upload(filename: str, allowed_extensions: set, max_size: int) -> Tuple[bool, str]:
    """
    Validate file upload parameters.
    
    Args:
        filename: Name of the uploaded file
        allowed_extensions: Set of allowed file extensions
        max_size: Maximum file size in bytes
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    from .security import sanitize_filename
    
    # Basic filename validation
    is_valid, error = sanitize_filename(filename, allowed_extensions)
    if not is_valid:
        return False, error
    
    # Additional checks can be added here (file size, etc.)
    return True, filename


def create_validation_schema(field_rules: Dict[str, Dict[str, Any]]) -> Dict[str, ValidationRule]:
    """
    Create a validation schema from a dictionary of field rules.
    
    Args:
        field_rules: Dictionary mapping field names to rule dictionaries
        
    Returns:
        Dictionary mapping field names to ValidationRule objects
    """
    schema = {}
    
    for field, rules in field_rules.items():
        schema[field] = ValidationRule(**rules)
    
    return schema


# Pre-defined validation schemas for common use cases
SCHEMAS = {
    'server_config': InputValidator.SERVER_CONFIG_RULES,
    'user_registration': InputValidator.USER_RULES,
    'node_config': InputValidator.NODE_RULES,
    
    # Simplified schemas for specific endpoints
    'login': {
        'username': ValidationRule(required=True, pattern=InputValidator.PATTERNS['username']),
        'password': ValidationRule(required=True, min_length=1)  # Don't validate existing passwords
    },
    
    'server_command': {
        'command': ValidationRule(
            required=True,
            min_length=1,
            max_length=200,
            custom_validator=lambda x: validate_minecraft_command(x)[0]
        )
    },
    
    'mod_search': {
        'query': ValidationRule(
            required=True,
            min_length=2,
            max_length=100,
            pattern=r'^[a-zA-Z0-9_\-\s]+$'
        )
    },
    
    'share_link': {
        'share_id': ValidationRule(
            required=True,
            pattern=r'^[a-zA-Z0-9]{8}$'
        )
    }
} 