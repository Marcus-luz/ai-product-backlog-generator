from app.extensions import db
from datetime import datetime

class UserStory(db.Model):
    __tablename__ = 'user_stories'

    id = db.Column(db.Integer, primary_key=True)
    as_a = db.Column(db.String(255)) # Como um...
    i_want = db.Column(db.Text)      # Eu quero...
    so_that = db.Column(db.Text)     # Para que...
    priority = db.Column(db.String(50), default='medium') # Ex: 'low', 'medium', 'high', 'critical'
    status = db.Column(db.String(50), default='draft') # Ex: 'draft', 'in_review', 'approved', 'rejected'
    generated_by_llm = db.Column(db.Boolean, default=False) # Indica se foi gerado por LLM
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Chave estrangeira para o épico pai (pode ser nulo se for uma história "solta")
    epic_id = db.Column(db.Integer, db.ForeignKey('epics.id'), nullable=True)
    # Chave estrangeira para o produto (redundante, mas facilita consultas diretas)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)


    # Relacionamento com requisitos funcionais
    requirements = db.relationship('Requirement', back_populates='user_story', lazy='dynamic')

    # Relacionamento com histórico de revisões (aspecto transversal)
    revisions = db.relationship('Revision', 
                                foreign_keys='Revision.artifact_id', 
                                primaryjoin="and_(Revision.artifact_id==UserStory.id, Revision.artifact_type=='user_story')", 
                                #backref='user_story_revision', lazy='dynamic',
                                back_populates = 'user_story_revision',
                                overlaps = 'revisions')
    epic = db.relationship('Epic', back_populates='user_stories')
    
    def __repr__(self):
        return f'<UserStory {self.id}>'