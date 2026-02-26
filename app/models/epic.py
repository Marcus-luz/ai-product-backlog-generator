from app.extensions import db
from datetime import datetime

class Epic(db.Model):
    __tablename__ = 'epics'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='draft') # Ex: 'draft', 'in_review', 'approved'
    generated_by_llm = db.Column(db.Boolean, default=False) # Indica se foi gerado por LLM
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Chave estrangeira para o produto ao qual o épico pertence
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    # Relacionamento com histórias de usuário que pertencem a este épico
    user_stories = db.relationship('UserStory', back_populates='epic', lazy='dynamic')
    
    # Relacionamento com histórico de revisões (aspecto transversal)
    revisions = db.relationship('Revision', 
                                foreign_keys='Revision.artifact_id', 
                                primaryjoin="and_(Revision.artifact_id==Epic.id, Revision.artifact_type=='epic')", 
                                #backref='epic_revision', lazy='dynamic',
                                back_populates='epic_revision',
                                overlaps= 'revisions')

    def __repr__(self):
        return f'<Epic {self.title}>'