"""
Configuration settings for The Originals.
Provides secure configuration management with environment variable support.
"""

import os
import secrets
from pathlib import Path
from typing import Dict, Any


class Config:
    """Base configuration class."""
    
    # Flask core settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(32)
    DEBUG = False
    TESTING = False
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + str(Path(__file__).parent / 'instance' / 'the_originals.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Server configuration
    SERVER_PORT = int(os.environ.get('SERVER_PORT', 3000))
    SERVER_HOST = os.environ.get('SERVER_HOST', '0.0.0.0')
    
    # Security settings
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    SESSION_COOKIE_SECURE = os.environ.get('HTTPS_ENABLED', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"
    RATELIMIT_HEADERS_ENABLED = True
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
    ALLOWED_EXTENSIONS = {'.jar', '.zip'}
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/app.log')
    
    # Minecraft server settings
    MINECRAFT_SERVER_DIR = Path(__file__).parent / 'minecraft_server'
    MINECRAFT_VERSION = os.environ.get('MINECRAFT_VERSION', '1.20.1')
    SERVER_MEMORY = os.environ.get('SERVER_MEMORY', '2G')
    
    # Node discovery and networking
    NODE_DISCOVERY_ENABLED = os.environ.get('NODE_DISCOVERY', 'True').lower() == 'true'
    NODE_DISCOVERY_INTERVAL = int(os.environ.get('NODE_DISCOVERY_INTERVAL', 30))
    NETWORK_TIMEOUT = int(os.environ.get('NETWORK_TIMEOUT', 10))
    
    # Auto-update settings
    AUTO_UPDATE_ENABLED = os.environ.get('AUTO_UPDATE', 'True').lower() == 'true'
    UPDATE_CHECK_INTERVAL = int(os.environ.get('UPDATE_CHECK_INTERVAL', 3600))
    GITHUB_REPO = os.environ.get('GITHUB_REPO', 'haloj/the-originals')
    
    # Tunnel settings
    TUNNEL_ENABLED = os.environ.get('TUNNEL_ENABLED', 'True').lower() == 'true'
    CLOUDFLARED_PATH = os.environ.get('CLOUDFLARED_PATH', 'cloudflared')
    
    # Performance settings
    ENABLE_PROFILING = os.environ.get('ENABLE_PROFILING', 'False').lower() == 'true'
    DATABASE_QUERY_TIMEOUT = int(os.environ.get('DB_QUERY_TIMEOUT', 30))
    
    # System tray
    SYSTEM_TRAY_ENABLED = os.environ.get('SYSTEM_TRAY', 'True').lower() == 'true'
    
    @staticmethod
    def init_app(app):
        """Initialize application with this configuration."""
        pass


class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    TESTING = False
    
    # Less strict security for development
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    
    # More verbose logging
    LOG_LEVEL = 'DEBUG'
    SQLALCHEMY_ECHO = True
    
    # Faster development cycles
    AUTO_UPDATE_ENABLED = False
    NODE_DISCOVERY_INTERVAL = 10
    
    @staticmethod
    def init_app(app):
        """Initialize development-specific settings."""
        Config.init_app(app)
        
        # Development-specific initialization
        import logging
        logging.basicConfig(level=logging.DEBUG)


class TestingConfig(Config):
    """Testing configuration."""
    
    TESTING = True
    DEBUG = True
    
    # Use in-memory database for tests
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable security features that interfere with testing
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    
    # Disable external services for testing
    AUTO_UPDATE_ENABLED = False
    NODE_DISCOVERY_ENABLED = False
    TUNNEL_ENABLED = False
    SYSTEM_TRAY_ENABLED = False
    
    # Fast timeouts for testing
    NETWORK_TIMEOUT = 1
    DATABASE_QUERY_TIMEOUT = 5
    
    @staticmethod
    def init_app(app):
        """Initialize testing-specific settings."""
        Config.init_app(app)
        
        # Testing-specific initialization
        import logging
        logging.disable(logging.CRITICAL)


class ProductionConfig(Config):
    """Production configuration."""
    
    DEBUG = False
    TESTING = False
    
    # Strict security for production
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    SQLALCHEMY_ECHO = False
    
    # Production performance settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'pool_size': 10,
        'max_overflow': 20
    }
    
    @staticmethod
    def init_app(app):
        """Initialize production-specific settings."""
        Config.init_app(app)
        
        # Production-specific initialization
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Set up file logging
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/the_originals.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.WARNING)
        app.logger.info('The Originals startup (Production)')


class DockerConfig(ProductionConfig):
    """Docker container configuration."""
    
    # Docker-specific settings
    SERVER_HOST = '0.0.0.0'
    
    # Use environment variables for all critical settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://postgres:password@db:5432/the_originals'
    
    # Redis for session storage and rate limiting
    SESSION_TYPE = 'redis'
    SESSION_REDIS = os.environ.get('REDIS_URL', 'redis://redis:6379')
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'redis://redis:6379')
    
    @staticmethod
    def init_app(app):
        """Initialize Docker-specific settings."""
        ProductionConfig.init_app(app)
        
        # Docker-specific logging to stdout
        import logging
        
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
        app.logger.setLevel(logging.INFO)


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


def get_config() -> Config:
    """
    Get configuration based on environment.
    
    Returns:
        Configuration class instance
    """
    config_name = os.environ.get('FLASK_ENV', 'default')
    return config.get(config_name, config['default'])


def validate_config(config_obj: Config) -> Dict[str, Any]:
    """
    Validate configuration settings.
    
    Args:
        config_obj: Configuration object to validate
        
    Returns:
        Dictionary with validation results
    """
    issues = []
    warnings = []
    
    # Check secret key security
    if config_obj.SECRET_KEY == 'dev' or len(config_obj.SECRET_KEY) < 16:
        issues.append("SECRET_KEY is insecure - use a strong random key")
    
    # Check database configuration
    if 'sqlite' in config_obj.SQLALCHEMY_DATABASE_URI and not config_obj.TESTING:
        warnings.append("SQLite database not recommended for production")
    
    # Check HTTPS configuration
    if config_obj.SESSION_COOKIE_SECURE and not os.environ.get('HTTPS_ENABLED'):
        warnings.append("HTTPS not configured but secure cookies enabled")
    
    # Check file permissions
    upload_dir = getattr(config_obj, 'UPLOAD_FOLDER', None)
    if upload_dir and upload_dir.exists():
        stat = upload_dir.stat()
        if stat.st_mode & 0o077:  # World or group writable
            issues.append(f"Upload directory {upload_dir} has insecure permissions")
    
    # Check logging configuration
    log_file = getattr(config_obj, 'LOG_FILE', None)
    if log_file:
        log_path = Path(log_file)
        if not log_path.parent.exists():
            warnings.append(f"Log directory {log_path.parent} does not exist")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings
    }


def create_required_directories(config_obj: Config) -> None:
    """
    Create required directories based on configuration.
    
    Args:
        config_obj: Configuration object
    """
    directories = [
        'logs',
        'instance',
        getattr(config_obj, 'UPLOAD_FOLDER', None),
        getattr(config_obj, 'MINECRAFT_SERVER_DIR', None)
    ]
    
    for directory in directories:
        if directory:
            Path(directory).mkdir(parents=True, exist_ok=True)


def load_env_file(env_file: str = '.env') -> None:
    """
    Load environment variables from file.
    
    Args:
        env_file: Path to environment file
    """
    env_path = Path(env_file)
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)


# Security configuration helpers
def get_security_headers() -> Dict[str, str]:
    """
    Get security headers for HTTP responses.
    
    Returns:
        Dictionary of security headers
    """
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdnjs.cloudflare.com cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "font-src 'self' cdnjs.cloudflare.com; "
            "connect-src 'self' ws: wss:;"
        ),
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'
    }


# Environment validation
def check_environment() -> None:
    """Check and validate environment setup."""
    required_vars = []
    recommended_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'LOG_LEVEL'
    ]
    
    missing_required = [var for var in required_vars if not os.environ.get(var)]
    missing_recommended = [var for var in recommended_vars if not os.environ.get(var)]
    
    if missing_required:
        raise RuntimeError(f"Missing required environment variables: {missing_required}")
    
    if missing_recommended:
        print(f"Warning: Missing recommended environment variables: {missing_recommended}")


if __name__ == "__main__":
    # Configuration validation script
    import sys
    
    config_name = sys.argv[1] if len(sys.argv) > 1 else 'development'
    config_class = config.get(config_name)
    
    if not config_class:
        print(f"Unknown configuration: {config_name}")
        print(f"Available configurations: {list(config.keys())}")
        sys.exit(1)
    
    config_obj = config_class()
    validation = validate_config(config_obj)
    
    print(f"Configuration: {config_name}")
    print(f"Valid: {validation['valid']}")
    
    if validation['issues']:
        print("\nIssues:")
        for issue in validation['issues']:
            print(f"  - {issue}")
    
    if validation['warnings']:
        print("\nWarnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    if not validation['valid']:
        sys.exit(1) 