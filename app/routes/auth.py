"""
Rotas para autenticação de usuários.

Este módulo contém as rotas para registro, login, logout e páginas de autenticação.
Utiliza JWT para autenticação stateless.
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, make_response
from app.models.user import User
from app.extensions import db, jwt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, unset_jwt_cookies, set_access_cookies
from datetime import timedelta

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Registra um novo usuário no sistema.
    
    Returns:
        JSON com mensagem de sucesso/erro e status HTTP
    """
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"message": "Username, email e senha são requeridos"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username ja existe"}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email ja existe"}), 409

    new_user = User(username=username, email=email)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registrado com sucesso", "user_id": new_user.id}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Autentica um usuário e retorna um token JWT.
    
    Returns:
        JSON com token de acesso e informações do usuário
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username e senha requeridos"}), 400

    user = User.query.filter_by(username=username).first()

    if user and user.check_password(password):
        access_token = create_access_token(identity=str(user.id), expires_delta=timedelta(days=1))
        return jsonify(access_token=access_token, user_id=user.id, message="Login bem-sucedido"), 200

    else:
        return jsonify({"message": "Credenciais inválidas"}), 401

@auth_bp.route('/protected', methods=['GET'])
@jwt_required() # Protege esta rota com JWT
def protected():
    # Acessa a identidade do usuário a partir do token
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify({"message": f"Olá, {user.username}! Você está autenticado."}), 200

@auth_bp.route('/login_page', methods=['GET'])
def login_page():
    """Renderiza a página de login."""
    return render_template('auth/login.html')

@auth_bp.route('/register_page', methods=['GET'])
def register_page():
    """Renderiza a página de registro."""
    return render_template('auth/register.html')

@auth_bp.route('/user/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    """
    Retorna as informações do usuário logado.
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({"message": "Usuário não encontrado"}), 404
        
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }), 200
    except Exception as e:
        return jsonify({"message": f"Erro ao buscar perfil do usuário: {str(e)}"}), 500

@auth_bp.route('/logout', methods=['GET'])
def logout():
    response = redirect(url_for('auth_bp.login_page'))
    #unset_jwt_cookies(response) # <--- Remove o cookie JWT do navegador
    flash('Você foi desconectado.', 'info')
    return response