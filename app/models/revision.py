"""
Modelo para controle de versões de artefatos ágeis.

Este modelo mantém um histórico de todas as alterações feitas em épicos,
histórias de usuário e requisitos, permitindo auditoria e rastreabilidade.
"""

from app.extensions import db
from datetime import datetime


class Revision(db.Model):
    """
    Modelo para histórico de revisões de artefatos.
    
    Mantém um registro de todas as mudanças feitas em épicos, user stories
    e requisitos, incluindo o estado completo do artefato em cada revisão.
    
    Attributes:
        id (int): Identificador único da revisão
        artifact_id (int): ID do artefato revisado
        artifact_type (str): Tipo do artefato (epic, user_story, requirement)
        content (str): Estado completo do artefato como JSON
        change_description (str): Descrição da mudança realizada
        user_id (int): ID do usuário que fez a mudança (nullable para mudanças automáticas)
        timestamp (datetime): Data e hora da revisão
    """
    
    __tablename__ = 'revisions'

    id = db.Column(db.Integer, primary_key=True)
    artifact_id = db.Column(db.Integer, nullable=False)
    artifact_type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    change_description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    reviser = db.relationship('User', backref='revisions', lazy=True)

    epic_revision = db.relationship(
        'Epic',
        primaryjoin="and_(Revision.artifact_id==Epic.id, Revision.artifact_type=='epic')",
        foreign_keys='Revision.artifact_id',
        viewonly=True,
        back_populates='revisions'
    )
    
    user_story_revision = db.relationship(
        'UserStory',
        primaryjoin="and_(Revision.artifact_id==UserStory.id, Revision.artifact_type=='user_story')",
        foreign_keys='Revision.artifact_id',
        viewonly=True,
        back_populates='revisions'
    )
    
    requirement_revision = db.relationship(
        'Requirement',
        primaryjoin="and_(Revision.artifact_id==Requirement.id, Revision.artifact_type=='requirement')",
        foreign_keys='Revision.artifact_id',
        viewonly=True,
        back_populates='revisions'
    )

    def __repr__(self):
        return f'<Revision {self.artifact_type}:{self.artifact_id} at {self.timestamp}>'