from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from app.services.backlog_service import BacklogService
from app.services.product_service import ProductService # Para carregar produtos no modal
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request

from app.services.logging_service import logging_service
from app.models.product import Product # Importar Product para a página de backlog


backlog_bp = Blueprint('backlog_bp', __name__, url_prefix='/backlog')

# --- Rotas da API para gerenciamento de Backlog ---

@backlog_bp.route('/generate/<int:product_id>', methods=['POST'])
@jwt_required()
def generate_backlog_for_product_api(product_id):
    """
    Gera um Product Backlog para um produto específico.
    Requer autenticação JWT.
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()
    custom_criteria = data.get('custom_criteria') # Critérios customizados para a geração

    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"message": "Produto não encontrado para gerar o backlog."}), 404

        backlog_obj = BacklogService.generate_product_backlog(
            product_id=product.id,
            user_id=int(current_user_id),
            custom_criteria=custom_criteria
        )
        
        # Retorna o conteúdo do backlog gerado/atualizado
        return jsonify({
            "message": f"Backlog do produto '{product.name}' gerado/atualizado com sucesso!",
            "backlog_id": backlog_obj.id,
            "product_id": backlog_obj.product_id,
            "total_items": len(backlog_obj.get_content())
        }), 201
    except ValueError as e:
        logging_service.log_error(f"Erro de validação ao gerar backlog: {str(e)}", operation="generate_backlog_validation", user_id=int(current_user_id))
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        logging_service.log_error(f"Um erro ocorreu ao gerar backlog: {str(e)}", operation="generate_backlog_api", exception=e, user_id=int(current_user_id))
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500


@backlog_bp.route('/product/<int:product_id>', methods=['GET'])
@jwt_required()
def get_backlog_by_product_api(product_id):
    """
    Retorna o backlog mais recente de um produto específico (API).
    Requer autenticação JWT.
    """
    try:
        backlog_content = BacklogService.get_backlog_by_product_id(product_id)
        
        if not backlog_content:
            return jsonify({"message": "Nenhum backlog encontrado para este produto."}), 404

        return jsonify(backlog_content), 200
    except Exception as e:
        logging_service.log_error(f"Erro ao buscar backlog por produto (API): {str(e)}", operation="get_backlog_by_product_api", exception=e)
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500


@backlog_bp.route('/api/user', methods=['GET'])
@jwt_required()
def get_all_backlogs_by_user_api():
    """
    Lista todos os backlogs de produtos do usuário logado (API).
    Retorna apenas metadados dos backlogs (não o conteúdo completo).
    Requer autenticação JWT.
    """
    current_user_id = get_jwt_identity()
    try:
        backlogs = BacklogService.get_all_backlogs_by_user(int(current_user_id))
        
        backlogs_data = []
        for backlog in backlogs:
            product_name = "Produto Desconhecido"
            if backlog.product: # Verifica se a relação product foi carregada
                product_name = backlog.product.name
            
            backlogs_data.append({
                "id": backlog.id,
                "name": backlog.name,
                "description": backlog.description,
                "product_id": backlog.product_id,
                "product_name": product_name,
                "total_items": len(backlog.get_content()), # Obtém o número de itens
                "created_at": backlog.created_at.isoformat(),
                "updated_at": backlog.updated_at.isoformat()
            })
        return jsonify(backlogs_data), 200
    except Exception as e:
        logging_service.log_error(f"Erro ao listar todos os backlogs por usuário (API): {str(e)}", operation="get_all_backlogs_by_user_api", exception=e, user_id=int(current_user_id))
        return jsonify({"message": f"Um erro ocorreu ao listar backlogs: {str(e)}"}), 500


# --- Rota para renderizar a página HTML de Backlog ---
@backlog_bp.route('/', methods=['GET'])
def backlog_page():
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except Exception as e:
        logging_service.log_info(f"JWT inválido/ausente para acesso à página de backlog: {e}", operation="backlog_page_access_attempt")
        user_id = None

    if not user_id:
        flash('Sua sessão expirou ou você não está logado. Por favor, faça login.', 'info')
        return redirect(url_for('auth_bp.login_page'))

    try:
        # Carregar todos os backlogs de produtos do usuário para exibição inicial na página
        backlogs = BacklogService.get_all_backlogs_by_user(int(user_id))
        
        backlogs_data = []
        for backlog in backlogs:
            product_name = "Produto Desconhecido"
            if backlog.product:
                product_name = backlog.product.name
            
            backlogs_data.append({
                "id": backlog.id,
                "name": backlog.name,
                "description": backlog.description,
                "product_id": backlog.product_id,
                "product_name": product_name,
                "total_items": len(backlog.get_content()),
                "created_at": backlog.created_at.isoformat(),
                "updated_at": backlog.updated_at.isoformat()
            })

        return render_template('backlog.html', backlogs_data=backlogs_data)

    except Exception as e:
        logging_service.log_error(f"Erro ao carregar a página de backlog: {str(e)}", operation="backlog_page_load", exception=e, user_id=int(user_id))
        flash('Ocorreu um erro interno ao carregar a página de backlog.', 'error')
        return redirect(url_for('auth_bp.login_page'))


@backlog_bp.route('/details/<int:product_id>', methods=['GET'])
def backlog_details_page(product_id):
    """
    Página de detalhes do backlog de um produto específico em formato de lista.
    """
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except Exception as e:
        logging_service.log_info(f"JWT inválido/ausente para acesso aos detalhes do backlog: {e}", operation="backlog_details_access_attempt")
        user_id = None

    if not user_id:
        flash('Sua sessão expirou ou você não está logado. Por favor, faça login.', 'info')
        return redirect(url_for('auth_bp.login_page'))

    try:
        # Verificar se o produto pertence ao usuário
        product = Product.query.filter_by(id=product_id, owner_id=int(user_id)).first()
        if not product:
            flash('Produto não encontrado ou você não tem permissão para acessá-lo.', 'error')
            return redirect(url_for('backlog_bp.backlog_page'))

        # Gerar/atualizar o backlog automaticamente
        backlog_obj = BacklogService.auto_update_product_backlog(product_id, int(user_id))
        
        # Buscar o backlog mais recente
        backlog_content = BacklogService.get_backlog_by_product_id(product_id)
        
        if not backlog_content:
            backlog_items = []
        else:
            backlog_items = backlog_content.get('items', [])

        return render_template('backlog_details.html', 
                             product=product, 
                             backlog_items=backlog_items,
                             total_items=len(backlog_items))

    except Exception as e:
        logging_service.log_error(f"Erro ao carregar detalhes do backlog: {str(e)}", operation="backlog_details_load", exception=e, user_id=int(user_id))
        flash('Ocorreu um erro interno ao carregar os detalhes do backlog.', 'error')
        return redirect(url_for('backlog_bp.backlog_page'))
