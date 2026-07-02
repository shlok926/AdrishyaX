import os

class Config:
    VERSION = '4.0.0'
    DEBUG = os.getenv('FLASK_ENV', 'production') == 'development'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-super-secret-key-sf-v4')
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_PASSWORD_LENGTH = 256
    MAX_MESSAGE_LENGTH = 10000
    RATE_LIMIT_PER_MINUTE = 30
    REQUEST_TIMEOUT = 300  # 5 minutes

class DevConfig(Config):
    DEBUG = True
    # SQLITE URIs etc later
    
class ProdConfig(Config):
    DEBUG = False
