from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from app.services.requirement_service import RequirementService
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

from app.services.logging_service import logging_service
from app.models.user_story import UserStory # Importar UserStory para buscar dados para LLM


requirement_bp = Blueprint('requirement_bp', __name__, url_prefix='/requirements')

# --- Rotas da API para gerenciamento de Requisitos ---

@requirement_bp.route('/', methods=['POST'])
@jwt_required()
def create_requirement():
    """
    Cria um novo requisito manualmente.
    Requer autenticação JWT.
    """
    current_user_id = get_jwt_identity()
    
    data = request.get_json()
    description = data.get('description')
    user_story_id = data.get('user_story_id')
    priority = data.get('priority', 'medium')

    try:
        new_requirement = RequirementService.create_requirement(
            description=description,
            user_story_id=user_story_id,
            priority=priority,
            generated_by_llm=False, # Marcado como não gerado por LLM
            user_id=int(current_user_id)
        )
        return jsonify({
            "message": "Requisito criado com sucesso",
            "requirement_id": new_requirement.id,
            "description": new_requirement.description
        }), 201
    except ValueError as e:
        logging_service.log_error(f"Erro de validação ao criar requisito: {str(e)}", operation="create_requirement_validation", user_id=int(current_user_id))
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logging_service.log_error(f"Um erro ocorreu: {str(e)}", operation="create_requirement_manual", exception=e, user_id=int(current_user_id))
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500


@requirement_bp.route('/generate/<int:user_story_id>', methods=['POST'])
@jwt_required()
def generate_requirements_for_user_story_api(user_story_id): # Renomeado para evitar conflito com método de serviço
    """
    Gera requisitos usando IA para uma história de usuário específica e salva no banco.
    Requer autenticação JWT.
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    custom_prompt = data.get('custom_prompt') # Pega o prompt customizado do frontend

    try:
        # Buscar o objeto UserStory completo para passar ao serviço
        user_story = UserStory.query.get(user_story_id)
        if not user_story:
            return jsonify({"message": "História de usuário não encontrada para gerar requisitos."}), 404

        # Chama o serviço de requisitos para gerar e salvar os requisitos
        generated_requirements = RequirementService.generate_requirements_for_user_story(
            user_story_id=user_story.id, # Passa o ID da história de usuário
            user_id=int(current_user_id),
            custom_prompt_instruction=custom_prompt # Passa a instrução customizada
        )
        
        requirements_data = [{
            "id": req.id,
            "description": req.description,
            "priority": req.priority,
            "status": req.status,
            "user_story_id": req.user_story_id,
            "created_at": req.created_at.isoformat(),
            "updated_at": req.updated_at.isoformat()
        } for req in generated_requirements]

        return jsonify({
            "message": f"{len(generated_requirements)} requisitos gerados com sucesso",
            "requirements": requirements_data
        }), 201
    except ValueError as e:
        logging_service.log_error(f"Erro de validação ao gerar requisitos: {str(e)}", operation="generate_requirements_validation", user_id=int(current_user_id))
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logging_service.log_error(f"Um erro ocorreu ao gerar requisitos: {str(e)}", operation="generate_requirements_llm_call", exception=e, user_id=int(current_user_id))
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500


@requirement_bp.route('/user-story/<int:user_story_id>', methods=['GET'])
@jwt_required()
def get_requirements_by_user_story_api(user_story_id): # Renomeado para evitar conflito com método de serviço
    """
    Lista todos os requisitos de uma história de usuário (API).
    Requer autenticação JWT.
    """
    try:
        requirements = RequirementService.get_requirements_by_user_story(user_story_id)
        
        requirements_data = []
        for req in requirements:
            user_story_text = "História de Usuário Desconhecida"
            if req.user_story: # Verifica se a relação user_story foi carregada
                user_story_text = f"Como um {req.user_story.as_a}, eu quero {req.user_story.i_want}, para que {req.user_story.so_that}"

            requirements_data.append({
                "id": req.id,
                "description": req.description,
                "priority": req.priority,
                "status": req.status,
                "user_story_id": req.user_story_id,
                "user_story_text": user_story_text, # Adiciona o texto da história de usuário
                "created_at": req.created_at.isoformat(),
                "updated_at": req.updated_at.isoformat()
            })

        return jsonify(requirements_data), 200
    except Exception as e:
        logging_service.log_error(f"Erro ao listar requisitos por história de usuário (API): {str(e)}", operation="get_requirements_by_user_story_api", exception=e)
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500


@requirement_bp.route('/<int:requirement_id>', methods=['GET'])
@jwt_required()
def get_requirement_api(requirement_id): # Renomeado para evitar conflito com método de serviço
    """
    Busca um requisito específico pelo ID (API).
    Requer autenticação JWT.
    """
    try:
        requirement = RequirementService.get_requirement_by_id(requirement_id)
        
        if not requirement:
            return jsonify({"message": "Requisito não encontrado"}), 404

        user_story_text = "História de Usuário Desconhecida"
        if requirement.user_story:
            user_story_text = f"Como um {requirement.user_story.as_a}, eu quero {requirement.user_story.i_want}, para que {requirement.user_story.so_that}"

        return jsonify({
            "id": requirement.id,
            "description": requirement.description,
            "priority": requirement.priority,
            "status": requirement.status,
            "user_story_id": requirement.user_story_id,
            "user_story_text": user_story_text,
            "created_at": requirement.created_at.isoformat(),
            "updated_at": requirement.updated_at.isoformat()
        }), 200
    except Exception as e:
        logging_service.log_error(f"Erro ao buscar requisito por ID: {str(e)}", operation="get_requirement_by_id_api", exception=e)
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500


@requirement_bp.route('/<int:requirement_id>', methods=['PUT'])
@jwt_required()
def update_requirement(requirement_id):
    """
    Atualiza um requisito existente.
    Requer autenticação JWT.
    """
    current_user_id = get_jwt_identity()
    
    data = request.get_json()
    try:
        updated_requirement = RequirementService.update_requirement(
            requirement_id=requirement_id,
            description=data.get('description'),
            priority=data.get('priority'),
            status=data.get('status'),
            user_id=int(current_user_id)
        )
        return jsonify({
            "message": "Requisito atualizado com sucesso",
            "requirement_id": updated_requirement.id,
            "description": updated_requirement.description
        }), 200
    except ValueError as e:
        logging_service.log_error(f"Erro de validação ao atualizar requisito: {str(e)}", operation="update_requirement_validation", user_id=int(current_user_id))
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logging_service.log_error(f"Um erro ocorreu ao atualizar requisito: {str(e)}", operation="update_requirement_api", exception=e, user_id=int(current_user_id))
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500


@requirement_bp.route('/<int:requirement_id>', methods=['DELETE'])
@jwt_required()
def delete_requirement(requirement_id):
    """
    Deleta um requisito existente.
    Requer autenticação JWT.
    """
    current_user_id = get_jwt_identity()

    try:
        RequirementService.delete_requirement(requirement_id, user_id=int(current_user_id))
        return jsonify({"message": "Requisito deletado com sucesso"}), 204
    except ValueError as e:
        logging_service.log_error(f"Erro de validação ao deletar requisito: {str(e)}", operation="delete_requirement_validation", user_id=int(current_user_id))
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logging_service.log_error(f"Um erro ocorreu ao deletar requisito: {str(e)}", operation="delete_requirement_api", exception=e, user_id=int(current_user_id))
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500

# --- NOVA ROTA DE API PARA LISTAR REQUISITOS DO USUÁRIO LOGADO ---
@requirement_bp.route('/api/user', methods=['GET']) # <--- NOVA ROTA DE API
@jwt_required()
def get_requirements_by_user_api():
    """
    Lista todos os requisitos do usuário logado (API).
    Requer autenticação JWT.
    """
    current_user_id = get_jwt_identity()
    try:
        requirements = RequirementService.get_requirements_by_user(int(current_user_id))
        
        requirements_data = []
        for req in requirements:
            user_story_text = "História de Usuário Desconhecida"
            if req.user_story: # Verifica se a relação user_story foi carregada
                user_story_text = f"Como um {req.user_story.as_a}, eu quero {req.user_story.i_want}, para que {req.user_story.so_that}"

            requirements_data.append({
                "id": req.id,
                "description": req.description,
                "priority": req.priority,
                "status": req.status,
                "user_story_id": req.user_story_id,
                "user_story_text": user_story_text, # Adiciona o texto da história de usuário
                "created_at": req.created_at.isoformat(),
                "updated_at": req.updated_at.isoformat()
            })
        return jsonify(requirements_data), 200
    except Exception as e:
        logging_service.log_error(f"Erro ao listar requisitos por usuário (API): {str(e)}", operation="get_requirements_by_user_api", exception=e, user_id=int(current_user_id))
        return jsonify({"message": f"Um erro ocorreu ao listar requisitos: {str(e)}"}), 500


# --- Rota para renderizar a página HTML de Requisitos ---
@requirement_bp.route('/', methods=['GET'])
def requirements_page():
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except Exception as e:
        logging_service.log_info(f"JWT inválido/ausente para acesso à página de requisitos: {e}", operation="requirements_page_access_attempt")
        user_id = None

    # Se não há user_id do header, tentar obter do token da URL
    if not user_id:
        from flask_jwt_extended import decode_token
        import jwt
        
        token_from_url = request.args.get('token')
        if token_from_url:
            try:
                # Decodificar o token manualmente usando PyJWT
                from app import app
                decoded_token = jwt.decode(token_from_url, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
                user_id = decoded_token.get('sub')  # 'sub' é onde o JWT armazena o user_id
                logging_service.log_info(f"Token da URL decodificado com sucesso para user_id: {user_id}", operation="requirements_page_token_auth")
            except jwt.ExpiredSignatureError:
                logging_service.log_info("Token da URL expirado", operation="requirements_page_token_expired")
            except jwt.InvalidTokenError as e:
                logging_service.log_info(f"Token da URL inválido: {e}", operation="requirements_page_token_invalid")
            except Exception as e:
                logging_service.log_error(f"Erro ao decodificar token da URL: {e}", operation="requirements_page_token_decode_error")

    if not user_id:
        flash('Sua sessão expirou ou você não está logado. Por favor, faça login.', 'info')
        return redirect(url_for('auth_bp.login_page'))

    try:
        # Verificar se há filtro por história de usuário
        story_id_filter = request.args.get('story_id')
        story_title_filter = None
        filtered_by_story = False
        
        if story_id_filter:
            try:
                story_id_filter = int(story_id_filter)
                # Buscar o título da história para exibição
                user_story = UserStory.query.get(story_id_filter)
                if user_story:
                    story_title_filter = f"Como um {user_story.as_a}, eu quero {user_story.i_want[:50]}{'...' if len(user_story.i_want) > 50 else ''}"
                    filtered_by_story = True
                    # Carregar apenas requisitos da história específica
                    requirements = RequirementService.get_requirements_by_user_story(story_id_filter)
                else:
                    # Se a história não existe, carregar todos os requisitos
                    requirements = RequirementService.get_requirements_by_user(int(user_id))
                    story_id_filter = None
            except (ValueError, TypeError):
                # Se o story_id não é um número válido, carregar todos os requisitos
                requirements = RequirementService.get_requirements_by_user(int(user_id))
                story_id_filter = None
        else:
            # Carregar todos os requisitos do usuário para exibição inicial na página
            requirements = RequirementService.get_requirements_by_user(int(user_id))
        
        requirements_data = []
        for req in requirements:
            user_story_text = "História de Usuário Desconhecida"
            if req.user_story: # Verifica se a relação user_story foi carregada
                user_story_text = f"Como um {req.user_story.as_a}, eu quero {req.user_story.i_want}, para que {req.user_story.so_that}"

            requirements_data.append({
                "id": req.id,
                "description": req.description,
                "priority": req.priority,
                "status": req.status,
                "user_story_id": req.user_story_id,
                "user_story_text": user_story_text, # Adiciona o texto da história de usuário
                "created_at": req.created_at.isoformat(),
                "updated_at": req.updated_at.isoformat()
            })

        return render_template('requirements.html', 
                             requirements_data=requirements_data,
                             filtered_by_story=filtered_by_story,
                             story_id_filter=story_id_filter,
                             story_title_filter=story_title_filter)

    except Exception as e:
        logging_service.log_error(f"Erro ao carregar a página de requisitos: {str(e)}", operation="requirements_page_load", exception=e, user_id=int(user_id))
        flash('Ocorreu um erro interno ao carregar a página de requisitos.', 'error')
        return redirect(url_for('auth_bp.login_page'))
