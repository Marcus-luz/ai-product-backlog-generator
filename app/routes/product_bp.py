from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from app.services.product_service import ProductService
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.services.logging_service import logging_service

product_bp = Blueprint('product_bp', __name__, url_prefix='/products')

@product_bp.route('/', methods=['POST'])
@jwt_required()
def create_product():
    """
    Cria um novo produto.
    Requer autenticação JWT. O ID do PO é obtido do token.
    """
    current_user_id = get_jwt_identity() # Obtém o ID do usuário do token JWT
    
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')
    value_proposition = data.get('value_proposition')
    channels_platforms = data.get('channels_platforms')

    try:
        new_product = ProductService.create_product(
            name=name,
            description=description,
            value_proposition=value_proposition,
            channels_platforms=channels_platforms,
            owner_id=int(current_user_id) # Garante que owner_id seja um inteiro
        )
        return jsonify({
            "message": "Produto criado com sucesso",
            "product_id": new_product.id,
            "name": new_product.name
        }), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        # Erro genérico para outros problemas no servidor/banco
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500


@product_bp.route('/', methods=['GET'])
@jwt_required()
def get_products():
    """
    Lista todos os produtos do usuário logado.
    Requer autenticação JWT.
    """
    current_user_id = get_jwt_identity()
    
    products = ProductService.get_all_products(owner_id=int(current_user_id))
    
    products_data = [{
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "value_proposition": p.value_proposition,
        "channels_platforms": p.channels_platforms,
        "owner_id": p.owner_id,
        "created_at": p.created_at.isoformat(),
        "updated_at": p.updated_at.isoformat()
    } for p in products]

    return jsonify(products_data), 200

@product_bp.route('/<int:product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    """
    Busca um produto específico pelo ID.
    Requer autenticação JWT.
    """
    product = ProductService.get_product_by_id(product_id)
    
    if not product:
        return jsonify({"message": "Produto não encontrado"}), 404

    # Opcional: Garantir que o usuário logado é o dono do produto
    current_user_id = get_jwt_identity()
    if product.owner_id != int(current_user_id):
        return jsonify({"message": "Sem permissão para acessar esse produto"}), 403 # Forbidden

    return jsonify({
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "value_proposition": product.value_proposition,
        "channels_platforms": product.channels_platforms,
        "owner_id": product.owner_id,
        "created_at": product.created_at.isoformat(),
        "updated_at": product.updated_at.isoformat()
    }), 200

@product_bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    """
    Atualiza um produto existente.
    Requer autenticação JWT. O usuário deve ser o dono do produto.
    """
    current_user_id = get_jwt_identity()
    product = ProductService.get_product_by_id(product_id)

    if not product:
        return jsonify({"message": "Produto não encontrado"}), 404
    
    if product.owner_id != int(current_user_id):
        return jsonify({"message": "Sem permissão para alterar"}), 403 # Forbidden

    data = request.get_json()
    try:
        updated_product = ProductService.update_product(
            product_id,
            name=data.get('name'),
            description=data.get('description'),
            value_proposition=data.get('value_proposition'),
            channels_platforms=data.get('channels_platforms')
        )
        return jsonify({
            "message": "Produto atualizado com sucesso",
            "product_id": updated_product.id,
            "name": updated_product.name
        }), 200
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500

@product_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    """
    Deleta um produto existente.
    Requer autenticação JWT. O usuário deve ser o dono do produto.
    """
    current_user_id = get_jwt_identity()
    product = ProductService.get_product_by_id(product_id)

    if not product:
        return jsonify({"message": "Produto não encontrado"}), 404
    
    if product.owner_id != int(current_user_id):
        return jsonify({"message": "Não autorizado para exclusão"}), 403 # Forbidden

    try:
        ProductService.delete_product(product_id)
        return jsonify({"message": "Produto deletado com sucesso"}), 204 # No Content
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"Um erro ocorreu: {str(e)}"}), 500

@product_bp.route('/page', methods=['GET']) # <--- Rota para a página HTML
def products_page():
    """
    Renderiza a página de produtos com todos os produtos do usuário.
    Aceita JWT via headers, cookies ou query string.
    """
    user_id = None
    try:
        # Verificar JWT obrigatório (não opcional)
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        logging_service.log_info(f"Usuário {user_id} acessou página de produtos", operation="products_page_access")
    except Exception as e:
        logging_service.log_warning(f"Falha na autenticação para página de produtos: {e}", operation="products_page_auth_failed")
        flash('Sua sessão expirou ou você não está logado. Por favor, faça login.', 'warning')
        return redirect(url_for('auth_bp.login_page'))

    try:
        # Carregar todos os produtos do usuário para exibição inicial na página
        products = ProductService.get_all_products(owner_id=int(user_id))
        
        products_data = []
        for p in products:
            # Formatar data de criação de forma amigável
            created_at_formatted = p.created_at.strftime('%d/%m/%Y às %H:%M') if p.created_at else 'N/A'
            updated_at_formatted = p.updated_at.strftime('%d/%m/%Y às %H:%M') if p.updated_at else 'N/A'
            
            products_data.append({
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "value_proposition": p.value_proposition,
                "channels_platforms": p.channels_platforms,
                "owner_id": p.owner_id,
                "created_at": created_at_formatted,
                "created_at_raw": p.created_at.isoformat() if p.created_at else None,  # Para ordenação
                "updated_at": updated_at_formatted
            })

        return render_template('products.html', products_data=products_data)

    except Exception as e:
        logging_service.log_error(f"Erro ao carregar a página de produtos: {str(e)}", operation="products_page_load", exception=e, user_id=int(user_id))
        flash('Ocorreu um erro interno ao carregar a página de produtos.', 'error')
        return redirect(url_for('auth_bp.login_page'))

@product_bp.route('/<int:product_id>/detail', methods=['GET'])
def product_detail(product_id):
    """
    Página de detalhes de um produto específico com épicos, histórias e requisitos.
    """
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except Exception as e:
        logging_service.log_info(f"JWT inválido/ausente para acesso aos detalhes do produto: {e}", operation="product_detail_access_attempt")
        user_id = None

    if not user_id:
        flash('Sua sessão expirou ou você não está logado. Por favor, faça login.', 'info')
        return redirect(url_for('auth_bp.login_page'))

    try:
        # Buscar o produto
        product = ProductService.get_product_by_id(product_id)
        
        if not product:
            flash('Produto não encontrado.', 'error')
            return redirect(url_for('dashboard_bp.dashboard_page'))

        # Verificar se o usuário é o dono do produto
        if product.owner_id != int(user_id):
            flash('Você não tem permissão para acessar este produto.', 'error')
            return redirect(url_for('dashboard_bp.dashboard_page'))

        # Buscar épicos, histórias e requisitos do produto
        from app.services.epic_service import EpicService
        from app.services.user_story_service import UserStoryService
        from app.services.requirement_service import RequirementService
        
        epics = EpicService.get_epics_by_product(product_id)
        epics_data = []
        total_user_stories = 0
        total_requirements = 0
        
        for epic in epics:
            user_stories = UserStoryService.get_user_stories_by_epic(epic.id)
            stories_data = []
            epic_requirements = 0
            
            for story in user_stories:
                requirements = RequirementService.get_requirements_by_user_story(story.id)
                epic_requirements += len(requirements)
                
                # Construir a história completa a partir dos campos separados
                full_story = f"Como um {story.as_a}, eu quero {story.i_want}, para que {story.so_that}"
                
                stories_data.append({
                    'id': story.id,
                    'story': full_story,
                    'as_a': story.as_a,
                    'i_want': story.i_want,
                    'so_that': story.so_that,
                    'persona': story.as_a,  # Using as_a as persona for display
                    'priority': story.priority,
                    'status': story.status,
                    'requirements_count': len(requirements),
                    'requirements': [{'id': req.id, 'description': req.description, 'priority': req.priority, 'status': req.status} for req in requirements]
                })
            
            total_user_stories += len(user_stories)
            total_requirements += epic_requirements
            
            epics_data.append({
                'id': epic.id,
                'title': epic.title,
                'description': epic.description,
                'status': epic.status,
                'user_stories': stories_data,
                'user_stories_count': len(user_stories),
                'requirements_count': epic_requirements
            })

        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'value_proposition': product.value_proposition,
            'channels_platforms': product.channels_platforms,
            'status': 'active',  # Default status since Product model doesn't have status field
            'created_at': product.created_at.strftime('%d/%m/%Y'),
            'updated_at': product.updated_at.strftime('%d/%m/%Y')
        }

        return render_template('product_detail.html', 
                             product=product_data, 
                             epics=epics_data,
                             total_epics=len(epics_data),
                             total_user_stories=total_user_stories,
                             total_requirements=total_requirements)

    except Exception as e:
        logging_service.log_error(f"Erro ao carregar detalhes do produto {product_id}: {str(e)}", operation="product_detail_load", exception=e, user_id=int(user_id))
        flash('Ocorreu um erro interno ao carregar os detalhes do produto.', 'error')
        return redirect(url_for('dashboard_bp.dashboard_page'))