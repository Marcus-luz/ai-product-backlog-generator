from flask import Blueprint, render_template, flash, redirect, url_for
from flask_jwt_extended import jwt_required

settings_bp = Blueprint('settings_bp', __name__)

@settings_bp.route('/settings', methods=['GET'])
@jwt_required()
def settings_page():
    flash("Página de Configurações em construção!", "info")
    
    return render_template('dashboard.html', projects=[], total_projects=0, total_epics=0, total_stories=0, total_requirements=0)