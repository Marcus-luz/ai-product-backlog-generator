# app/models/product.py

from app.extensions import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    value_proposition = db.Column(db.Text) # Problema que o produto resolve
    channels_platforms = db.Column(db.String(255)) # Ex: 'web, mobile, desktop'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Chave estrangeira para o usuário que criou o produto
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relacionamentos
    personas = db.relationship('Persona', backref='product', lazy='dynamic')
    epics = db.relationship('Epic', backref='product', lazy='dynamic')
    user_stories = db.relationship('UserStory', backref='product', lazy='dynamic') # Histórias diretamente ligadas ao produto (para facilitar consultas)

    def __repr__(self):
        return f'<Product {self.name}>'