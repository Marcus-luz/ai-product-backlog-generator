"""
Configurações da aplicação Flask.

Define as configurações para diferentes ambientes (desenvolvimento, produção, teste)
incluindo configurações de banco de dados, JWT, logging e outras variáveis do sistema.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuração base para a aplicação."""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua_chave_secreta_muito_segura'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'postgresql://postgres:Araujo12!@localhost:5432/product_owner_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de Logging
    LOGGING_ENABLED = True
    LOGGING_LEVEL = 'INFO'
    LOG_TO_FILE = True
    LOG_LLM_INTERACTIONS = True
    LOG_PERFORMANCE_METRICS = True
    LOG_MAX_FILE_SIZE_MB = 10
    LOG_BACKUP_COUNT = 5

    # Configurações JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'rp3'
    JWT_TOKEN_LOCATION = ["headers", "cookies", "query_string"]
    JWT_QUERY_STRING_NAME = "token"
    JWT_COOKIE_SECURE = False  # Use True em produção com HTTPS
    JWT_CSRF_ENABLED = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_COOKIE_SAMESITE = "Lax"


class DevelopmentConfig(Config):
    """Configuração para ambiente de desenvolvimento."""
    
    DEBUG = True
    LOGGING_LEVEL = 'DEBUG'
    LOG_PERFORMANCE_METRICS = True


class ProductionConfig(Config):
    """Configuração para ambiente de produção."""
    
    DEBUG = False
    LOGGING_LEVEL = 'INFO'
    LOG_PERFORMANCE_METRICS = False
    LOG_MAX_FILE_SIZE_MB = 50
    LOG_BACKUP_COUNT = 10


class TestingConfig(Config):
    """Configuração para ambiente de testes."""
    
    TESTING = True
    LOGGING_LEVEL = 'WARNING'
    LOG_TO_FILE = False
    LOG_LLM_INTERACTIONS = False
    LOG_PERFORMANCE_METRICS = False


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}