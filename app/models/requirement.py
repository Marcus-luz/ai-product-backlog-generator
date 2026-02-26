"""
Modelo para requisitos funcionais e critérios de aceite.

Este modelo representa os requisitos extraídos das histórias de usuário,
podendo ser gerados automaticamente por IA ou criados manualmente.
"""

from app.extensions import db
from datetime import datetime


class Requirement(db.Model):
    """
    Modelo para requisitos funcionais do sistema.
    
    Attributes:
        id (int): Identificador único do requisito
        description (str): Descrição textual do requisito
        priority (str): Prioridade do requisito (low, medium, high, critical)
        status (str): Status atual (draft, approved, implemented)
        generated_by_llm (bool): Se foi gerado por IA
        created_at (datetime): Data de criação
        updated_at (datetime): Data da última atualização
        user_story_id (int): ID da história de usuário associada
    """
    
    __tablename__ = 'requirements'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(50), default='medium')
    status = db.Column(db.String(50), default='draft')
    generated_by_llm = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_story_id = db.Column(db.Integer, db.ForeignKey('user_stories.id'), nullable=False)

    # Relacionamentos
    revisions = db.relationship('Revision', 
                                foreign_keys='Revision.artifact_id', 
                                primaryjoin="and_(Revision.artifact_id==Requirement.id, Revision.artifact_type=='requirement')", 
                                lazy='dynamic',
                                overlaps="epic_revision,user_story_revision")

    user_story = db.relationship('UserStory', back_populates='requirements', viewonly=True)

    def __repr__(self):
        return f'<Requirement {self.id}>'