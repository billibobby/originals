"""
User model for The Originals.
Handles user authentication, authorization, and profile management.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import CheckConstraint, Index
from sqlalchemy.orm import validates
import re

# Import db from main app (will be initialized properly)
db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model with enhanced security and validation."""
    
    __tablename__ = 'users'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    
    # Role and permissions
    role = db.Column(db.Enum('admin', 'moderator', 'user', name='user_roles'), 
                    default='user', nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # Security fields
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    last_failed_login = db.Column(db.DateTime)
    password_changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Preferences (JSON stored as text)
    preferences = db.Column(db.Text)  # JSON string for user preferences
    
    # Relationships
    created_servers = db.relationship('ServerInstance', backref='creator', lazy='dynamic')
    
    # Database constraints
    __table_args__ = (
        CheckConstraint('length(username) >= 3', name='username_min_length'),
        CheckConstraint('length(username) <= 20', name='username_max_length'),
        CheckConstraint('length(display_name) >= 1', name='display_name_min_length'),
        CheckConstraint('length(password_hash) >= 60', name='password_hash_min_length'),
        CheckConstraint('failed_login_attempts >= 0', name='failed_login_attempts_positive'),
        Index('idx_user_role_active', 'role', 'is_active'),
        Index('idx_user_created_at', 'created_at'),
    )
    
    def __init__(self, **kwargs):
        """Initialize user with default values."""
        super().__init__(**kwargs)
        if not self.display_name and self.username:
            self.display_name = self.username
    
    def __repr__(self):
        """String representation of user."""
        return f'<User {self.username}>'
    
    @validates('username')
    def validate_username(self, key, username):
        """Validate username format."""
        if not username:
            raise ValueError('Username is required')
        
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            raise ValueError('Username must be 3-20 characters, alphanumeric and underscores only')
        
        return username.lower()  # Store usernames in lowercase
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format."""
        if not email:
            raise ValueError('Email is required')
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError('Invalid email address format')
        
        return email.lower()  # Store emails in lowercase
    
    @validates('role')
    def validate_role(self, key, role):
        """Validate user role."""
        valid_roles = ['admin', 'moderator', 'user']
        if role not in valid_roles:
            raise ValueError(f'Role must be one of: {", ".join(valid_roles)}')
        return role
    
    def set_password(self, password: str) -> None:
        """
        Set user password with strength validation.
        
        Args:
            password: Plain text password
            
        Raises:
            ValueError: If password doesn't meet strength requirements
        """
        if not self._validate_password_strength(password):
            raise ValueError(
                'Password must be at least 8 characters and contain: '
                'uppercase letter, lowercase letter, number, and special character'
            )
        
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()
        self.failed_login_attempts = 0  # Reset failed attempts on password change
    
    def check_password(self, password: str) -> bool:
        """
        Check if provided password matches user's password.
        
        Args:
            password: Plain text password to check
            
        Returns:
            True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def _validate_password_strength(self, password: str) -> bool:
        """
        Validate password strength requirements.
        
        Args:
            password: Password to validate
            
        Returns:
            True if password meets requirements, False otherwise
        """
        if len(password) < 8:
            return False
        
        has_upper = re.search(r'[A-Z]', password)
        has_lower = re.search(r'[a-z]', password)
        has_digit = re.search(r'\d', password)
        has_special = re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
        
        return bool(has_upper and has_lower and has_digit and has_special)
    
    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            permission: Permission name to check
            
        Returns:
            True if user has permission, False otherwise
        """
        if not self.is_active:
            return False
        
        permissions = {
            'admin': [
                'server_control', 'user_management', 'node_management', 
                'config_edit', 'system_admin', 'view_logs', 'manage_updates'
            ],
            'moderator': [
                'server_control', 'config_edit', 'node_management', 'view_logs'
            ],
            'user': [
                'server_view', 'profile_edit'
            ]
        }
        
        user_permissions = permissions.get(self.role, [])
        return permission in user_permissions
    
    def record_login_attempt(self, success: bool) -> None:
        """
        Record a login attempt (success or failure).
        
        Args:
            success: True if login was successful, False if failed
        """
        if success:
            self.last_login = datetime.utcnow()
            self.failed_login_attempts = 0
            self.last_failed_login = None
        else:
            self.failed_login_attempts += 1
            self.last_failed_login = datetime.utcnow()
    
    def is_account_locked(self) -> bool:
        """
        Check if account is locked due to too many failed login attempts.
        
        Returns:
            True if account is locked, False otherwise
        """
        max_attempts = 5
        lockout_duration = 30  # minutes
        
        if self.failed_login_attempts < max_attempts:
            return False
        
        if not self.last_failed_login:
            return False
        
        # Check if lockout period has expired
        lockout_expires = self.last_failed_login + timedelta(minutes=lockout_duration)
        return datetime.utcnow() < lockout_expires
    
    def can_manage_user(self, target_user: 'User') -> bool:
        """
        Check if this user can manage another user.
        
        Args:
            target_user: User to check management permissions for
            
        Returns:
            True if can manage, False otherwise
        """
        if not self.has_permission('user_management'):
            return False
        
        # Admins can manage everyone except other admins (unless they're the same person)
        if self.role == 'admin':
            return target_user.role != 'admin' or self.id == target_user.id
        
        # Moderators can only manage regular users
        if self.role == 'moderator':
            return target_user.role == 'user'
        
        return False
    
    def get_preferences(self) -> dict:
        """
        Get user preferences as dictionary.
        
        Returns:
            Dictionary of user preferences
        """
        if not self.preferences:
            return {}
        
        try:
            import json
            return json.loads(self.preferences)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_preferences(self, preferences: dict) -> None:
        """
        Set user preferences from dictionary.
        
        Args:
            preferences: Dictionary of preferences to set
        """
        import json
        self.preferences = json.dumps(preferences)
    
    def update_preference(self, key: str, value) -> None:
        """
        Update a single preference.
        
        Args:
            key: Preference key
            value: Preference value
        """
        prefs = self.get_preferences()
        prefs[key] = value
        self.set_preferences(prefs)
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert user to dictionary representation.
        
        Args:
            include_sensitive: Whether to include sensitive information
            
        Returns:
            Dictionary representation of user
        """
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email if include_sensitive else self.email.split('@')[0] + '@***',
            'display_name': self.display_name,
            'role': self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'preferences': self.get_preferences()
        }
        
        if include_sensitive:
            data.update({
                'failed_login_attempts': self.failed_login_attempts,
                'last_failed_login': self.last_failed_login.isoformat() if self.last_failed_login else None,
                'password_changed_at': self.password_changed_at.isoformat() if self.password_changed_at else None,
                'is_locked': self.is_account_locked()
            })
        
        return data
    
    @staticmethod
    def get_admin_users() -> List['User']:
        """Get all admin users."""
        return User.query.filter_by(role='admin', is_active=True).all()
    
    @staticmethod
    def get_user_by_username_or_email(identifier: str) -> Optional['User']:
        """
        Get user by username or email.
        
        Args:
            identifier: Username or email to search for
            
        Returns:
            User if found, None otherwise
        """
        return User.query.filter(
            db.or_(
                User.username == identifier.lower(),
                User.email == identifier.lower()
            )
        ).first()
    
    @staticmethod
    def create_default_admin() -> 'User':
        """
        Create default admin user if none exists.
        
        Returns:
            Created admin user
        """
        # Check if any admin users exist
        existing_admin = User.query.filter_by(role='admin').first()
        if existing_admin:
            return existing_admin
        
        # Create default admin
        admin = User(
            username='admin',
            email='admin@theoriginals.local',
            display_name='Administrator',
            role='admin',
            is_verified=True
        )
        admin.set_password('admin123')  # Should be changed immediately
        
        db.session.add(admin)
        db.session.commit()
        
        return admin 