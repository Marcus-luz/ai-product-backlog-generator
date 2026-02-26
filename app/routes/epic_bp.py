from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from app.services.epic_service import EpicService
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

from app.services.logging_service import logging_service
from app.models.product import Product # Importar Product para pegar dados para LLM
from app.models.epic import Epic 

epic_bp = Blueprint('epic_bp', __name__, url_prefix='/epics')

# --- Rotas da API para gerenciamento de Épicos ---

@epic_bp.route('/', methods=['POST'])
@jwt_required()
def create_epic():
    """
    Cria um novo épico manualmente.
    Requer autenticação JWT.
    """
    current_user_id = get_jwt_identity()
    
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    product_id = data.get('product_id')

    try:
        new_epic = EpicService.create_epic(
            title=title,
            description=description,
            product_id=product_id,
            generated_by_llm=False, # Marcado como não gerado por LLM
            user_id=int(current_user_id)
        )
        return jsonify({
            "message": "Épico criado com sucesso",
            "epic_id": new_epic.id,
            "title": new_epic.title
        }), 201
    except ValueError as e:
        logging_service.log_error(f"Erro de validação ao criar épico: {str(e)}", operation="create_epic_validation", user_id=int(current_user_id))
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logging_service.log_error(f"Erro ao criar épico: {str(e)}", operation="create_epic_manual", exception=e, user_id=int(current_user_id))
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500


@epic_bp.route('/generate/<int:product_id>', methods=['POST'])
@jwt_required()
def generate_epics_for_product_api(product_id):
    """
    Gera épicos usando IA para um produto específico e salva no banco.
    Requer autenticação JWT.
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    custom_prompt = data.get('custom_prompt')

    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"message": "Produto não encontrado para gerar épicos."}), 404

        generated_epics = EpicService.generate_epics_for_product(
            product=product,
            user_id=int(current_user_id),
            custom_prompt_instruction=custom_prompt
        )
        
        epics_data = [{
            "id": epic.id,
            "title": epic.title,
            "description": epic.description,
            "status": epic.status,
            "product_id": epic.product_id,
            "created_at": epic.created_at.isoformat(),
            "updated_at": epic.updated_at.isoformat()
        } for epic in generated_epics]

        return jsonify({
            "message": f"{len(generated_epics)} épicos gerados com sucesso",
            "epics": epics_data
        }), 201
    except ValueError as e:
        logging_service.log_error(f"Erro de validação ao gerar épicos: {str(e)}", operation="generate_epics_validation", user_id=int(current_user_id))
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logging_service.log_error(f"Erro ao gerar épicos: {str(e)}", operation="generate_epics_llm_call", exception=e, user_id=int(current_user_id))
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500


@epic_bp.route('/product/<int:product_id>', methods=['GET'])
@jwt_required()
def get_epics_by_product(product_id):
    """
    Lista todos os épicos de um produto específico (API).
    Requer autenticação JWT.
    """
    try:
        epics = EpicService.get_epics_by_product(product_id)
        
        epics_data = [{
            "id": epic.id,
            "title": epic.title,
            "description": epic.description,
            "status": epic.status,
            "product_id": epic.product_id,
            "created_at": epic.created_at.isoformat(),
            "updated_at": epic.updated_at.isoformat()
        } for epic in epics]

        return jsonify(epics_data), 200
    except Exception as e:
        logging_service.log_error(f"Erro ao listar épicos por produto: {str(e)}", operation="get_epics_by_product_api", exception=e)
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500


@epic_bp.route('/<int:epic_id>', methods=['GET'])
@jwt_required()
def get_epic_api(epic_id):
    """
    Busca um épico específico pelo ID (API).
    Requer autenticação JWT.
    """
    try:
        epic = EpicService.get_epic_by_id(epic_id)
        
        if not epic:
            return jsonify({"message": "Épico não encontrado"}), 404

        return jsonify({
            "id": epic.id,
            "title": epic.title,
            "description": epic.description,
            "status": epic.status,
            "product_id": epic.product_id,
            "created_at": epic.created_at.isoformat(),
            "updated_at": epic.updated_at.isoformat()
        }), 200
    except Exception as e:
        logging_service.log_error(f"Erro ao buscar épico por ID: {str(e)}", operation="get_epic_by_id_api", exception=e)
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500


@epic_bp.route('/<int:epic_id>', methods=['PUT'])
@jwt_required()
def update_epic(epic_id):
    """
    Atualiza um épico existente.
    Requer autenticação JWT.
    """
    current_user_id = get_jwt_identity()
    
    data = request.get_json()
    try:
        updated_epic = EpicService.update_epic(
            epic_id=epic_id,
            title=data.get('title'),
            description=data.get('description'),
            status=data.get('status'),
            user_id=int(current_user_id)
        )
        return jsonify({
            "message": "Épico atualizado com sucesso",
            "epic_id": updated_epic.id,
            "title": updated_epic.title
        }), 200
    except ValueError as e:
        logging_service.log_error(f"Erro de validação ao atualizar épico: {str(e)}", operation="update_epic_validation", user_id=int(current_user_id))
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logging_service.log_error(f"Erro ao atualizar épico: {str(e)}", operation="update_epic_api", exception=e, user_id=int(current_user_id))
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500


@epic_bp.route('/<int:epic_id>', methods=['DELETE'])
@jwt_required()
def delete_epic(epic_id):
    """
    Deleta um épico existente.
    Requer autenticação JWT.
    """
    current_user_id = get_jwt_identity()

    try:
        EpicService.delete_epic(epic_id, user_id=int(current_user_id))
        return jsonify({"message": "Épico deletado com sucesso"}), 204
    except ValueError as e:
        logging_service.log_error(f"Erro de validação ao deletar épico: {str(e)}", operation="delete_epic_validation", user_id=int(current_user_id))
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logging_service.log_error(f"Erro ao deletar épico: {str(e)}", operation="delete_epic_api", exception=e, user_id=int(current_user_id))
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500

# --- NOVA ROTA DE API PARA LISTAR ÉPICOS DO USUÁRIO LOGADO ---
@epic_bp.route('/api/user', methods=['GET'])
@jwt_required()
def get_epics_by_user_api():
    """
    Lista todos os épicos do usuário logado (API).
    Requer autenticação JWT.
    """
    current_user_id = get_jwt_identity()
    try:
        epics = EpicService.get_epics_by_user(int(current_user_id))
        
        epics_data = []
        for epic in epics:
            product_name = "Produto Desconhecido"
            # Otimização: para evitar N+1 queries aqui, considere usar eager loading (ex: joinedload)
            if epic.product: 
                product_name = epic.product.name
            
            epics_data.append({
                "id": epic.id,
                "title": epic.title,
                "description": epic.description,
                "status": epic.status,
                "product_id": epic.product_id,
                "product_name": product_name,
                "created_at": epic.created_at.isoformat(),
                "updated_at": epic.updated_at.isoformat()
            })
        return jsonify(epics_data), 200
    except Exception as e:
        # Garante que o retorno é SEMPRE JSON, mesmo em caso de erro
        logging_service.log_error(f"Erro ao listar épicos por usuário (API): {str(e)}", operation="get_epics_by_user_api", exception=e, user_id=int(current_user_id))
        return jsonify({"message": f"Um erro ocorreu ao listar épicos: {str(e)}"}), 500

# --- Rota para renderizar a página HTML de Épicos ---
@epic_bp.route('/', methods=['GET'])
def epics_page():
    """
    Renderiza a página de épicos com todos os épicos do usuário.
    Aceita JWT via headers, cookies ou query string.
    """
    user_id = None
    try:
        # Verificar JWT obrigatório (não opcional)
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        logging_service.log_info(f"Usuário {user_id} acessou página de épicos", operation="epics_page_access")
    except Exception as e:
        logging_service.log_warning(f"Falha na autenticação para página de épicos: {e}", operation="epics_page_auth_failed")
        flash('Sua sessão expirou ou você não está logado. Por favor, faça login.', 'warning')
        return redirect(url_for('auth_bp.login_page'))

    try:
        # Carregar todos os épicos do usuário para exibição inicial na página
        epics = EpicService.get_epics_by_user(int(user_id))
        
        epics_data = []
        for epic in epics:
            # Para cada épico, buscar o nome do produto associado
            product_name = "Produto Desconhecido"
            if epic.product: # Verifica se a relação product foi carregada
                product_name = epic.product.name
            
            # Formatar data de criação de forma amigável
            created_at_formatted = epic.created_at.strftime('%d/%m/%Y às %H:%M') if epic.created_at else 'N/A'
            
            # Calcular estatísticas do épico
            total_stories = epic.user_stories.count() if epic.user_stories else 0
            
            # Calcular total de requisitos associados às histórias do épico
            total_requirements = 0
            if epic.user_stories:
                for story in epic.user_stories:
                    total_requirements += story.requirements.count()
            
            # Calcular progresso baseado no status das histórias
            progress = 0
            if total_stories > 0:
                completed_stories = epic.user_stories.filter_by(status='approved').count()
                progress = round((completed_stories / total_stories) * 100)
            
            
            epics_data.append({
                "id": epic.id,
                "title": epic.title,
                "description": epic.description,
                "status": epic.status,
                "product_id": epic.product_id,
                "product_name": product_name, # Adiciona o nome do produto
                "created_at": created_at_formatted,
                "created_at_raw": epic.created_at.isoformat() if epic.created_at else None,  # Para ordenação
                "updated_at": epic.updated_at.isoformat() if epic.updated_at else None,
                # Estatísticas do card
                "totalStories": total_stories,
                "totalRequirements": total_requirements,
                "progress": progress
            })

        return render_template('epics.html', epics_data=epics_data)

    except Exception as e:
        logging_service.log_error(f"Erro ao carregar a página de épicos: {str(e)}", operation="epics_page_load", exception=e, user_id=int(user_id))
        flash('Ocorreu um erro interno ao carregar a página de épicos.', 'error')
        return redirect(url_for('auth_bp.login_page'))


@epic_bp.route('/<int:epic_id>/stats', methods=['GET'])
@jwt_required()
def get_epic_stats_api(epic_id):
    """
    Retorna as estatísticas atualizadas de um épico específico.
    """
    current_user_id = get_jwt_identity()
    
    try:
        # Buscar o épico através do produto (para verificar ownership)
        epic = Epic.query.join(Product).filter(
            Epic.id == epic_id,
            Product.owner_id == int(current_user_id)
        ).first()
        
        if not epic:
            return jsonify({"message": "Épico não encontrado"}), 404
        
        # Calcular estatísticas atualizadas
        total_stories = epic.user_stories.count() if epic.user_stories else 0
        
        # Calcular total de requisitos associados às histórias do épico
        total_requirements = 0
        completed_requirements = 0
        if epic.user_stories:
            for story in epic.user_stories:
                story_requirements = story.requirements.all()
                total_requirements += len(story_requirements)
                # Contar requisitos com status 'done' (concluído)
                completed_requirements += len([req for req in story_requirements if req.status == 'done'])
        
        # Calcular progresso baseado nos requisitos concluídos
        progress = 0
        if total_requirements > 0:
            progress = round((completed_requirements / total_requirements) * 100)
        
        return jsonify({
            "totalStories": total_stories,
            "totalRequirements": total_requirements,
            "progress": progress
        }), 200
        
    except Exception as e:
        logging_service.log_error(f"Erro ao buscar estatísticas do épico: {str(e)}", operation="epic_stats_api", exception=e, user_id=int(current_user_id))
        return jsonify({"message": "Erro interno do servidor"}), 500
