# app/models/persona.py

from app.extensions import db
from datetime import datetime

class Persona(db.Model):
    __tablename__ = 'personas'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    demographics = db.Column(db.Text) # Ex: idade, profissão, localização
    goals = db.Column(db.Text)        # Ex: o que a persona quer alcançar
    pain_points = db.Column(db.Text)  # Ex: problemas que a persona enfrenta
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Chave estrangeira para o produto ao qual a persona pertence
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    def __repr__(self):
        return f'<Persona {self.name}>'