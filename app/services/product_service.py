from app.models.product import Product
from app.models.user import User 
from app.extensions import db
from datetime import datetime

class ProductService:
    @staticmethod
    def create_product(name, description, value_proposition, channels_platforms, owner_id):
        """
        Cria um novo produto no banco de dados.
        """
        if not all([name, description, value_proposition, channels_platforms, owner_id]):
            raise ValueError("Todos os campos do produto são obrigatórios.")

        # Opcional: Verificar se o owner_id corresponde a um usuário existente
        # user = User.query.get(owner_id)
        # if not user:
        #     raise ValueError("Usuário (owner) não encontrado.")

        new_product = Product(
            name=name,
            description=description,
            value_proposition=value_proposition,
            channels_platforms=channels_platforms,
            owner_id=owner_id
        )
        db.session.add(new_product)
        db.session.commit()
        return new_product

    @staticmethod
    def get_product_by_id(product_id):
        """
        Busca um produto pelo ID.
        """
        return Product.query.get(product_id)

    @staticmethod
    def get_all_products(owner_id=None):
        """
        Retorna todos os produtos, opcionalmente filtrando por owner_id.
        """
        query = Product.query
        if owner_id:
            query = query.filter_by(owner_id=owner_id)
        return query.all()

    @staticmethod
    def update_product(product_id, name=None, description=None, value_proposition=None, channels_platforms=None):
        """
        Atualiza as informações de um produto existente.
        """
        product = Product.query.get(product_id)
        if not product:
            raise ValueError("Produto não encontrado.")

        if name:
            product.name = name
        if description:
            product.description = description
        if value_proposition:
            product.value_proposition = value_proposition
        if channels_platforms:
            product.channels_platforms = channels_platforms
        
        product.updated_at = datetime.utcnow() # Atualiza o timestamp

        db.session.commit()
        return product

    @staticmethod
    def delete_product(product_id):
        """
        Deleta um produto pelo ID, incluindo todos os épicos, histórias, requisitos, personas e backlogs associados.
        """
        from app.models.epic import Epic
        from app.models.user_story import UserStory
        from app.models.requirement import Requirement
        from app.models.revision import Revision
        from app.models.persona import Persona
        from app.models.backlog import Backlog
        
        product = Product.query.get(product_id)
        if not product:
            raise ValueError("Produto não encontrado.")
        
        try:
            # 1. Deletar personas do produto
            Persona.query.filter_by(product_id=product_id).delete()
            
            # 2. Deletar backlogs do produto
            Backlog.query.filter_by(product_id=product_id).delete()
            
            # 3. Buscar todos os épicos do produto
            epics = Epic.query.filter_by(product_id=product_id).all()
            epic_ids = [epic.id for epic in epics]
            
            # 4. Buscar todas as histórias dos épicos
            all_stories = UserStory.query.filter_by(product_id=product_id).all()
            story_ids = [story.id for story in all_stories]
            
            # 5. Buscar todos os requisitos das histórias
            if story_ids:
                all_requirements = Requirement.query.filter(Requirement.user_story_id.in_(story_ids)).all()
                requirement_ids = [req.id for req in all_requirements]
                
                # 6. Deletar revisões dos requisitos em lote
                if requirement_ids:
                    Revision.query.filter(
                        Revision.artifact_id.in_(requirement_ids),
                        Revision.artifact_type == 'requirement'
                    ).delete(synchronize_session=False)
                
                # 7. Deletar requisitos em lote
                Requirement.query.filter(Requirement.user_story_id.in_(story_ids)).delete(synchronize_session=False)
            
            # 8. Deletar revisões das histórias em lote
            if story_ids:
                Revision.query.filter(
                    Revision.artifact_id.in_(story_ids),
                    Revision.artifact_type == 'user_story'
                ).delete(synchronize_session=False)
            
            # 9. Deletar histórias em lote
            UserStory.query.filter_by(product_id=product_id).delete()
            
            # 10. Deletar revisões dos épicos em lote
            if epic_ids:
                Revision.query.filter(
                    Revision.artifact_id.in_(epic_ids),
                    Revision.artifact_type == 'epic'
                ).delete(synchronize_session=False)
            
            # 11. Deletar épicos em lote
            Epic.query.filter_by(product_id=product_id).delete()
            
            # 12. Finalmente, deletar o produto
            db.session.delete(product)
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            raise e