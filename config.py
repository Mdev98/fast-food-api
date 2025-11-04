"""
Configuration centralisée pour l'application Flask Fast-Food API
"""
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()


class Config:
    """Configuration de base pour l'application"""
    
    # Flask
    FLASK_APP = os.getenv('FLASK_APP', 'app.py')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Base de données
    database_url = os.getenv('DATABASE_URL', 'sqlite:///fastfood.db')
    # Render utilise postgres://, mais SQLAlchemy 1.4+ requiert postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Sécurité
    ADMIN_API_KEY = os.getenv('ADMIN_API_KEY', 'your_secret_key_here')
    
    # SMS Configuration (IntechSMS API)
    MANAGER_MOBILE = os.getenv('MANAGER_MOBILE', '+221777293282')
    INTECH_API_KEY = os.getenv('INTECH_API_KEY', 'your_intech_app_key')
    INTECH_SENDER_ID = os.getenv('INTECH_SENDER_ID', 'FastFood')
    SMS_MOCK_MODE = os.getenv('SMS_MOCK_MODE', 'true').lower() == 'true'
    
    # Cache
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'SimpleCache')  # SimpleCache ou RedisCache
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_TTL', '600'))
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    
    # Rate Limiting
    RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'false').lower() == 'true'
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '100/hour')
    
    @staticmethod
    def init_app(app):
        """Initialisation spécifique de l'application"""
        pass


class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = True


class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Configuration pour les tests"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    ADMIN_API_KEY = 'test_api_key'


# Dictionnaire de configurations
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
