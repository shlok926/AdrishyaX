"""
StegoForge Configuration Management
Environment-based settings for development, testing, and production
"""

import os
from datetime import timedelta

class BaseConfig:
    """Base configuration."""
    APP_NAME = 'StegoForge'
    VERSION = '4.0.0'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = False
    TESTING = False
    JSON_SORT_KEYS = False
    
    # API Configuration
    API_VERSION = 'v1'
    RATE_LIMIT_PER_MINUTE = 1000
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_PASSWORD_LENGTH = 256
    MAX_MESSAGE_LENGTH = 10000
    REQUEST_TIMEOUT = 300  # 5 minutes
    
    # Security
    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000']
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'stegoforge.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'
    SESSION_COOKIE_SECURE = False
    CORS_ORIGINS = ['*']  # Allow all origins in dev


class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    # CORS_ORIGINS should be set via environment variable
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://yourdomain.com').split(',')
    
    # Enforce TLS in production
    PREFERRED_URL_SCHEME = 'https'
    
    # Stricter rate limiting in production
    RATE_LIMIT_PER_MINUTE = 20


class TestingConfig(BaseConfig):
    """Testing configuration."""
    DEBUG = False
    TESTING = True
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB for tests
    RATE_LIMIT_PER_MINUTE = 1000  # Disable rate limiting


def get_config():
    """Get configuration based on FLASK_ENV."""
    env = os.getenv('FLASK_ENV', 'development').lower()
    
    if env == 'production':
        return ProductionConfig()
    elif env == 'testing':
        return TestingConfig()
    else:
        return DevelopmentConfig()
