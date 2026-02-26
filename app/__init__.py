"""
Inicialização da aplicação Flask.

Configura extensões, blueprints, logging e handlers de erro.
"""

import logging
import os
from dotenv import load_dotenv
from flask import Flask, redirect, url_for, flash, request, jsonify
from config import config_by_name
from app.extensions import db, login_manager, jwt, migrate
from app.models.user import User
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, exceptions as jwt_exceptions

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

from app.routes.auth import auth_bp
from app.routes.product_bp import product_bp
from app.routes.dashboard_bp import dashboard_bp
from app.routes.epic_bp import epic_bp
from app.routes.user_story_bp import user_story_bp
from app.routes.requirement_bp import requirement_bp
from app.routes.backlog_bp import backlog_bp 
from app.routes.settings_bp import settings_bp

from app.services.logging_service import logging_service


def setup_application_logging(app, config_name):
    """
    Configura o sistema de logging padrão do Flask para console e arquivo.
    
    Args:
        app (Flask): Instância da aplicação Flask
        config_name (str): Nome da configuração sendo usada
    """
    os.makedirs('logs', exist_ok=True)
    
    if not app.logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        file_handler = logging.FileHandler('logs/app.log', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        app.logger.addHandler(console_handler)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)


def create_app(config_name='default'):
    """
    Factory para criar e configurar a aplicação Flask.
    
    Args:
        config_name (str): Nome da configuração a ser usada
        
    Returns:
        Flask: Instância configurada da aplicação
    """
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    if app.config.get('LOGGING_ENABLED', True):
        setup_application_logging(app, config_name)
        app.logger.info(f"Aplicação iniciada com configuração: {config_name}")

    # Inicializa extensões
    db.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Importa modelos para o Alembic
    from app.models import user, product, epic, user_story, requirement, persona, revision, backlog
    
    @login_manager.user_loader
    def load_user(user_id):
        """Carrega usuário para o Flask-Login."""
        return User.query.get(int(user_id))

    # Registra blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(epic_bp)
    app.register_blueprint(user_story_bp)
    app.register_blueprint(requirement_bp)
    app.register_blueprint(backlog_bp)
    app.register_blueprint(settings_bp)
    
    register_error_handlers(app)
    register_jwt_handlers(app)

    @app.route('/')
    def index():
        """Redireciona para a página de login."""
        return redirect(url_for('auth_bp.login_page'))

    return app


def register_error_handlers(app):
    """
    Registra handlers personalizados para diferentes tipos de erro.
    
    Args:
        app (Flask): Instância da aplicação Flask
    """
    def get_current_user_id_from_jwt():
        """
        Função auxiliar para tentar obter o user_id de forma segura em error handlers.
        
        Returns:
            int or None: ID do usuário se JWT válido, None caso contrário
        """
        try:
            if verify_jwt_in_request(optional=True):
                return get_jwt_identity()
        except Exception:
            pass
        return None

    @app.errorhandler(404)
    def not_found_error(error):
        """Handler para erro 404 - Página não encontrada."""
        requested_url = request.path if request else 'unknown'
        user_id = get_current_user_id_from_jwt()
        logging_service.log_error(
            error_message=f"Página não encontrada: {requested_url}",
            operation="route_access",
            details={
                'status_code': 404,
                'requested_url': requested_url
            },
            user_id=user_id
        )
        return jsonify({'error': 'Página não encontrada'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handler para erro 500 - Erro interno do servidor."""
        original_exception = getattr(error, 'original_exception', None)
        user_id = get_current_user_id_from_jwt()
        logging_service.log_error(
            error_message=f"Erro interno do servidor: {error}",
            exception=original_exception,
            operation="internal_server_error",
            details={'status_code': 500},
            user_id=user_id
        )
        return jsonify({'error': 'Erro interno do servidor'}), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handler para exceções gerais não tratadas."""
        user_id = get_current_user_id_from_jwt()
        logging_service.log_error(
            error_message=f"Ocorreu um erro inesperado: {error}",
            exception=error,
            operation="unhandled_exception",
            user_id=user_id
        )
        return jsonify({'error': 'Ocorreu um erro inesperado'}), 500


def register_jwt_handlers(app):
    """
    Registra handlers personalizados para erros de JWT.
    
    Args:
        app (Flask): Instância da aplicação Flask
    """
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handler para token expirado."""
        return jsonify({
            'message': 'Token expirou. Faça login novamente.',
            'error': 'token_expired'
        }), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Handler para token inválido."""
        return jsonify({
            'message': 'Token inválido. Faça login novamente.',
            'error': 'invalid_token'
        }), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Handler para token ausente."""
        return jsonify({
            'message': 'Token de acesso requerido. Faça login.',
            'error': 'authorization_required'
        }), 401

    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        """Handler para token que precisa ser atualizado."""
        return jsonify({
            'message': 'Token precisa ser atualizado.',
            'error': 'fresh_token_required'
        }), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Handler para token revogado."""
        return jsonify({
            'message': 'Token foi revogado.',
            'error': 'token_revoked'
        }), 401