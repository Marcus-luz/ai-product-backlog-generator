from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request # Manter jwt_required
from app.services.product_service import ProductService
from app.models.product import Product
from app.models.epic import Epic
from app.models.user_story import UserStory
from app.models.requirement import Requirement
from datetime import datetime, date
from sqlalchemy import extract

from app.services.logging_service import logging_service

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/dashboard', methods=['GET'])
def dashboard_page():
    """
    Dashboard page that handles authentication flexibly.
    Checks for JWT token from query parameter or uses verify_jwt_in_request with optional=True.
    """
    user_id = None
    
    try:
        # Try to verify JWT token (from headers, cookies, or query params)
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except Exception as e:
        logging_service.log_info(f"JWT inválido/ausente para acesso ao dashboard: {e}", operation="dashboard_access_attempt")
        user_id = None

    if not user_id:
        flash('Sua sessão expirou ou você não está logado. Por favor, faça login.', 'info')
        return redirect(url_for('auth_bp.login_page'))

    # Se chegou até aqui, user_id é válido
    try:
        products = ProductService.get_all_products(owner_id=int(user_id))
        
        # Obter data atual para filtros do mês
        current_date = datetime.now()
        current_month = current_date.month
        current_year = current_date.year
        
        total_projects = len(products)
        total_epics = 0
        total_stories = 0
        total_requirements = 0
        
        # Métricas do mês atual
        projects_this_month = 0
        stories_this_month = 0
        
        projects_data_for_template = []
        for p in products:
            # Contar se o projeto foi criado neste mês
            if (p.created_at.month == current_month and 
                p.created_at.year == current_year):
                projects_this_month += 1
            
            num_epics = p.epics.count()
            num_stories = p.user_stories.count()
            
            # Contar histórias criadas neste mês
            stories_this_month += p.user_stories.filter(
                extract('month', UserStory.created_at) == current_month,
                extract('year', UserStory.created_at) == current_year
            ).count()
            
            num_reqs = 0
            for us in p.user_stories.all():
                num_reqs += us.requirements.count()

            total_epics += num_epics
            total_stories += num_stories
            total_requirements += num_reqs

            projects_data_for_template.append({
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "status": "active",
                "epics": num_epics,
                "stories": num_stories,
                "requirements": num_reqs,
                "lastUpdated": p.updated_at.strftime('%d/%m/%Y %H:%M')
            })

        return render_template('dashboard.html', 
                               projects=projects_data_for_template,
                               total_projects=total_projects,
                               total_epics=total_epics,
                               total_stories=total_stories,
                               total_requirements=total_requirements,
                               projects_this_month=projects_this_month,
                               stories_this_month=stories_this_month)
    
    except Exception as e:
        logging_service.log_error(
            error_message=f"Erro ao carregar o dashboard: {str(e)}",
            operation="dashboard_load",
            exception=e,
            user_id=int(user_id)
        )
        flash('Ocorreu um erro interno ao carregar o dashboard. Tente novamente mais tarde.', 'error')
        return redirect(url_for('auth_bp.login_page'))