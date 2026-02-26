
from app.extensions import db
from datetime import datetime
import json

class Backlog(db.Model):
    __tablename__ = 'backlogs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # ID do produto ao qual este backlog pertence
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    
    # Conteúdo do backlog: uma lista ordenada de IDs de histórias/requisitos, armazenado como JSON
    # Ex: [{"type": "story", "id": 1}, {"type": "req", "id": 5}, ...]
    content = db.Column(db.Text, nullable=False) 
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamento com o produto
    product = db.relationship('Product', backref='backlogs', lazy=True)

    def set_content(self, items_list):
        """Armazena a lista de itens do backlog como uma string JSON."""
        self.content = json.dumps(items_list)

    def get_content(self):
        """Retorna a lista de itens do backlog do formato JSON."""
        if self.content:
            return json.loads(self.content)
        return []

    def __repr__(self):
        return f'<Backlog {self.name}>'