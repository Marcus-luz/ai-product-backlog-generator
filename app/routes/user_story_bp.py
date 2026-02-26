
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from app.services.user_story_service import UserStoryService
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

from app.services.logging_service import logging_service
from app.models.epic import Epic # Importar Epic para buscar dados para LLM
from app.models.user_story import UserStory # Importar UserStory para a página de histórias

user_story_bp = Blueprint('user_story_bp', __name__, url_prefix='/user-stories')

# --- Rotas da API para gerenciamento de Histórias de Usuário ---

@user_story_bp.route('/', methods=['POST'])
@jwt_required()
def create_user_story():
    """
    Cria uma nova história de usuário manualmente.
    Requer autenticação JWT.
    """
    current_user_id = get_jwt_identity()
    
    data = request.get_json()
    as_a = data.get('as_a')
    i_want = data.get('i_want')
    so_that = data.get('so_that')
    epic_id = data.get('epic_id')
    product_id = data.get('product_id') # Pode ser inferido do épico se não fornecido
    priority = data.get('priority', 'medium')

    try:
        new_story = UserStoryService.create_user_story(
            as_a=as_a,
            i_want=i_want,
            so_that=so_that,
            epic_id=epic_id,
            product_id=product_id,
            priority=priority,
            generated_by_llm=False, # Marcado como não gerado por LLM
            user_id=int(current_user_id)
        )
        return jsonify({
            "message": "História de usuário criada com sucesso",
            "user_story_id": new_story.id,
            "story_text": f"Como um {new_story.as_a}, eu quero {new_story.i_want}, para que {new_story.so_that}"
        }), 201
    except ValueError as e:
        logging_service.log_error(f"Erro de validação ao criar história: {str(e)}", operation="create_user_story_validation", user_id=int(current_user_id))
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logging_service.log_error(f"Um erro ocorreu: {str(e)}", operation="create_user_story_manual", exception=e, user_id=int(current_user_id))
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500


@user_story_bp.route('/generate/<int:epic_id>', methods=['POST'])
@jwt_required()
def generate_user_stories_for_epic_api(epic_id): # Renomeado para evitar conflito com método de serviço
    """
    Gera histórias de usuário usando IA para um épico específico e salva no banco.
    Requer autenticação JWT.
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    custom_prompt = data.get('custom_prompt') # Pega o prompt customizado do frontend

    try:
        # Buscar o objeto Epic completo para passar ao serviço
        epic = Epic.query.get(epic_id)
        if not epic:
            return jsonify({"message": "Épico não encontrado para gerar histórias."}), 404

        # Chama o serviço de histórias para gerar e salvar as histórias
        generated_stories = UserStoryService.generate_user_stories_for_epic(
            epic_id=epic.id, # Passa o ID do épico
            user_id=int(current_user_id),
            custom_prompt_instruction=custom_prompt # Passa a instrução customizada
        )
        
        stories_data = [{
            "id": story.id,
            "as_a": story.as_a,
            "i_want": story.i_want,
            "so_that": story.so_that,
            "priority": story.priority,
            "status": story.status,
            "epic_id": story.epic_id,
            "product_id": story.product_id,
            "generated_by_llm": story.generated_by_llm,
            "created_at": story.created_at.isoformat(),
            "updated_at": story.updated_at.isoformat(),
            "story_text": f"Como um {story.as_a}, eu quero {story.i_want}, para que {story.so_that}"
        } for story in generated_stories]

        return jsonify({
            "message": f"{len(generated_stories)} histórias de usuário geradas com sucesso",
            "user_stories": stories_data
        }), 201
    except ValueError as e:
        logging_service.log_error(f"Erro de validação ao gerar histórias: {str(e)}", operation="generate_user_stories_validation", user_id=int(current_user_id))
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logging_service.log_error(f"Um erro ocorreu ao gerar histórias: {str(e)}", operation="generate_user_stories_llm_call", exception=e, user_id=int(current_user_id))
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500


@user_story_bp.route('/epic/<int:epic_id>', methods=['GET'])
@jwt_required()
def get_user_stories_by_epic_api(epic_id): # Renomeado para evitar conflito com método de serviço
    """
    Lista todas as histórias de usuário de um épico (API).
    Requer autenticação JWT.
    """
    try:
        stories = UserStoryService.get_user_stories_by_epic(epic_id)
        
        stories_data = []
        for story in stories:
            epic_title = "Épico Desconhecido"
            if story.epic: # Verifica se a relação epic foi carregada
                epic_title = story.epic.title

            stories_data.append({
                "id": story.id,
                "as_a": story.as_a,
                "i_want": story.i_want,
                "so_that": story.so_that,
                "priority": story.priority,
                "status": story.status,
                "epic_id": story.epic_id,
                "epic_title": epic_title, # Adiciona o título do épico
                "product_id": story.product_id,
                "generated_by_llm": story.generated_by_llm,
                "created_at": story.created_at.isoformat(),
                "updated_at": story.updated_at.isoformat(),
                "story_text": f"Como um {story.as_a}, eu quero {story.i_want}, para que {story.so_that}"
            })

        return jsonify(stories_data), 200
    except Exception as e:
        logging_service.log_error(f"Erro ao listar histórias por épico: {str(e)}", operation="get_user_stories_by_epic_api", exception=e)
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500


@user_story_bp.route('/product/<int:product_id>', methods=['GET'])
@jwt_required()
def get_user_stories_by_product_api(product_id): # Renomeado para evitar conflito com método de serviço
    """
    Lista todas as histórias de usuário de um produto (API).
    Requer autenticação JWT.
    """
    try:
        stories = UserStoryService.get_user_stories_by_product(product_id)
        
        stories_data = []
        for story in stories:
            epic_title = "Épico Desconhecido"
            if story.epic:
                epic_title = story.epic.title

            stories_data.append({
                "id": story.id,
                "as_a": story.as_a,
                "i_want": story.i_want,
                "so_that": story.so_that,
                "priority": story.priority,
                "status": story.status,
                "epic_id": story.epic_id,
                "epic_title": epic_title, # Adiciona o título do épico
                "product_id": story.product_id,
                "generated_by_llm": story.generated_by_llm,
                "created_at": story.created_at.isoformat(),
                "updated_at": story.updated_at.isoformat(),
                "story_text": f"Como um {story.as_a}, eu quero {story.i_want}, para que {story.so_that}"
            })

        return jsonify(stories_data), 200
    except Exception as e:
        logging_service.log_error(f"Erro ao listar histórias por produto: {str(e)}", operation="get_user_stories_by_product_api", exception=e)
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500
@user_story_bp.route('/api/user', methods=['GET']) # <--- NOVA ROTA DE API
@jwt_required()
def get_user_stories_by_user_api():
    """
    Lista todas as histórias de usuário do usuário logado (API).
    Requer autenticação JWT.
    """
    current_user_id = get_jwt_identity()
    try:
        stories = UserStoryService.get_user_stories_by_user(int(current_user_id))
        
        stories_data = []
        for story in stories:
            epic_title = "Épico Desconhecido"
            if story.epic: # Verifica se a relação epic foi carregada
                epic_title = story.epic.title

            stories_data.append({
                "id": story.id,
                "as_a": story.as_a,
                "i_want": story.i_want,
                "so_that": story.so_that,
                "priority": story.priority,
                "status": story.status,
                "epic_id": story.epic_id,
                "epic_title": epic_title, # Adiciona o título do épico
                "product_id": story.product_id,
                "generated_by_llm": story.generated_by_llm,
                "created_at": story.created_at.isoformat(),
                "updated_at": story.updated_at.isoformat(),
                "story_text": f"Como um {story.as_a}, eu quero {story.i_want}, para que {story.so_that}"
            })
        return jsonify(stories_data), 200
    except Exception as e:
        logging_service.log_error(f"Erro ao listar histórias por usuário (API): {str(e)}", operation="get_user_stories_by_user_api", exception=e, user_id=int(current_user_id))
        return jsonify({"message": f"Um erro ocorreu ao listar histórias: {str(e)}"}), 500


@user_story_bp.route('/<int:story_id>', methods=['GET'])
@jwt_required()
def get_user_story_api(story_id): # Renomeado para evitar conflito com método de serviço
    """
    Busca uma história de usuário específica pelo ID (API).
    Requer autenticação JWT.
    """
    try:
        story = UserStoryService.get_user_story_by_id(story_id)
        
        if not story:
            return jsonify({"message": "História de usuário não encontrada"}), 404

        epic_title = "Épico Desconhecido"
        if story.epic:
            epic_title = story.epic.title

        return jsonify({
            "id": story.id,
            "as_a": story.as_a,
            "i_want": story.i_want,
            "so_that": story.so_that,
            "priority": story.priority,
            "status": story.status,
            "epic_id": story.epic_id,
            "epic_title": epic_title,
            "product_id": story.product_id,
            "generated_by_llm": story.generated_by_llm,
            "created_at": story.created_at.isoformat(),
            "updated_at": story.updated_at.isoformat(),
            "story_text": f"Como um {story.as_a}, eu quero {story.i_want}, para que {story.so_that}"
        }), 200
    except Exception as e:
        logging_service.log_error(f"Erro ao buscar história por ID: {str(e)}", operation="get_user_story_by_id_api", exception=e)
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500


@user_story_bp.route('/<int:story_id>', methods=['PUT'])
@jwt_required()
def update_user_story(story_id):
    """
    Atualiza uma história de usuário existente.
    Requer autenticação JWT.
    """
    current_user_id = get_jwt_identity()
    
    data = request.get_json()
    try:
        updated_story = UserStoryService.update_user_story(
            story_id=story_id,
            as_a=data.get('as_a'),
            i_want=data.get('i_want'),
            so_that=data.get('so_that'),
            priority=data.get('priority'),
            status=data.get('status'),
            user_id=int(current_user_id)
        )
        return jsonify({
            "message": "História de usuário atualizada com sucesso",
            "user_story_id": updated_story.id,
            "story_text": f"Como um {updated_story.as_a}, eu quero {updated_story.i_want}, para que {updated_story.so_that}"
        }), 200
    except ValueError as e:
        logging_service.log_error(f"Erro de validação ao atualizar história: {str(e)}", operation="update_user_story_validation", user_id=int(current_user_id))
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logging_service.log_error(f"Um erro ocorreu ao atualizar história: {str(e)}", operation="update_user_story_api", exception=e, user_id=int(current_user_id))
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500


@user_story_bp.route('/<int:story_id>', methods=['DELETE'])
@jwt_required()
def delete_user_story(story_id):
    """
    Deleta uma história de usuário existente.
    Requer autenticação JWT.
    """
    current_user_id = get_jwt_identity()

    try:
        UserStoryService.delete_user_story(story_id, user_id=int(current_user_id))
        return jsonify({"message": "História de usuário deletada com sucesso"}), 204
    except ValueError as e:
        logging_service.log_error(f"Erro de validação ao deletar história: {str(e)}", operation="delete_user_story_validation", user_id=int(current_user_id))
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logging_service.log_error(f"Um erro ocorreu ao deletar história: {str(e)}", operation="delete_user_story_api", exception=e, user_id=int(current_user_id))
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500

# --- Rota para renderizar a página HTML de Histórias de Usuário ---
@user_story_bp.route('/', methods=['GET'])
def stories_page():
    user_id = None
    try:
        # Tentar token na query string primeiro (navegação via JS)
        token_from_url = request.args.get('token')
        if token_from_url:
            # Importar e usar a verificação manual do token
            import jwt as pyjwt
            from flask import current_app
            try:
                decoded = pyjwt.decode(token_from_url, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
                user_id = decoded['sub']
                logging_service.log_info(f"Token da URL validado para usuário {user_id}", operation="stories_page_token_url")
            except Exception as token_error:
                logging_service.log_info(f"Token da URL inválido: {token_error}", operation="stories_page_token_url")
        
        # Se não tem token na URL, tentar JWT no header
        if not user_id:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        
    except Exception as e:
        logging_service.log_info(f"JWT inválido/ausente para acesso à página de histórias: {e}", operation="stories_page_access_attempt")
        user_id = None

    if not user_id:
        flash('Sua sessão expirou ou você não está logado. Por favor, faça login.', 'info')
        return redirect(url_for('auth_bp.login_page'))

    try:
        # Obter parâmetros de filtro da query string
        epic_id_filter = request.args.get('epic_id', type=int)
        epic_title_filter = request.args.get('epic_title', '')
        
        # Log para debugging
        logging_service.log_info(f"Carregando histórias para usuário {user_id}, filtro épico: {epic_id_filter}", operation="stories_page_load")
        
        # Carregar todas as histórias de usuário do usuário para exibição inicial na página
        stories = UserStoryService.get_user_stories_by_user(int(user_id))
        
        # Log para debugging
        logging_service.log_info(f"Encontradas {len(stories)} histórias antes do filtro", operation="stories_page_load")
        for story in stories[:3]:  # Log das primeiras 3 histórias
            logging_service.log_info(f"História {story.id}: epic_id={story.epic_id}, product_id={story.product_id}", operation="stories_page_load")
        
        # Se há filtro por épico, aplicar filtro
        if epic_id_filter:
            original_count = len(stories)
            stories = [story for story in stories if story.epic_id == epic_id_filter]
            logging_service.log_info(f"Após filtro por épico {epic_id_filter}: {len(stories)} histórias (antes: {original_count})", operation="stories_page_load")
            
            # Log das histórias que passaram no filtro
            for story in stories:
                logging_service.log_info(f"História filtrada {story.id}: epic_id={story.epic_id}", operation="stories_page_load")
        
        stories_data = []
        for story in stories:
            epic_title = "Épico Desconhecido"
            if story.epic: # Verifica se a relação epic foi carregada
                epic_title = story.epic.title

            stories_data.append({
                "id": story.id,
                "as_a": story.as_a,
                "i_want": story.i_want,
                "so_that": story.so_that,
                "priority": story.priority,
                "status": story.status,
                "epic_id": story.epic_id,
                "epic_title": epic_title, # Adiciona o título do épico
                "product_id": story.product_id,
                "generated_by_llm": story.generated_by_llm,
                "created_at": story.created_at.isoformat(),
                "updated_at": story.updated_at.isoformat(),
                "story_text": f"Como um {story.as_a}, eu quero {story.i_want}, para que {story.so_that}"
            })

        # Preparar dados de contexto para o template
        context_data = {
            'stories_data': stories_data,
            'filtered_by_epic': epic_id_filter is not None,
            'epic_id_filter': epic_id_filter,
            'epic_title_filter': epic_title_filter
        }

        return render_template('stories.html', **context_data)

    except Exception as e:
        logging_service.log_error(f"Erro ao carregar a página de histórias: {str(e)}", operation="stories_page_load", exception=e, user_id=int(user_id))
        flash('Ocorreu um erro interno ao carregar a página de histórias.', 'error')
        return redirect(url_for('auth_bp.login_page'))


@user_story_bp.route('/<int:story_id>/requirements-count', methods=['GET'])
@jwt_required()
def get_requirements_count(story_id):
    """
    Retorna a contagem de requisitos vinculados a uma história de usuário específica.
    """
    current_user_id = get_jwt_identity()
    
    try:
        # Importar Requirement aqui para evitar import circular
        from app.models.requirement import Requirement
        from app.models.product import Product
        
        # Verificar se a história existe e pertence ao usuário através do produto
        story = UserStory.query.join(Product).filter(
            UserStory.id == story_id,
            Product.owner_id == int(current_user_id)
        ).first()
        
        if not story:
            return jsonify({"message": "História não encontrada"}), 404
        
        # Contar requisitos vinculados a esta história
        requirements_count = Requirement.query.filter_by(user_story_id=story_id).count()
        
        return jsonify({
            "story_id": story_id,
            "count": requirements_count
        }), 200
        
    except Exception as e:
        logging_service.log_error(f"Erro ao buscar contagem de requisitos para história {story_id}: {str(e)}", 
                                operation="get_requirements_count", exception=e, user_id=int(current_user_id))
        return jsonify({"message": "Erro interno do servidor"}), 500
