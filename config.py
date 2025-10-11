import os
from datetime import timedelta

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Application settings
    APP_NAME = 'SIEMSpeak Enterprise'
    APP_VERSION = '2.1.0'
    
    # Data settings
    SAMPLE_DATA_SIZE = 10000
    MAX_RESULTS = 1000
    DEFAULT_TIME_RANGE = '24h'
    
    # AI/NLP settings
    NLP_CONFIDENCE_THRESHOLD = 0.7
    MAX_QUERY_LENGTH = 500
    
    # Chart settings
    DEFAULT_CHART_THEME = 'dark'
    CHART_COLORS = {
        'primary': ['#4dc9f6', '#f67019', '#f53794', '#537bc4', '#acc236'],
        'success': ['#28a745', '#20c997', '#00ca8e'],
        'warning': ['#ffc107', '#fd7e14', '#e83e8c'],
        'danger': ['#dc3545', '#c82333', '#a71e2a']
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}