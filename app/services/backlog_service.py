
from app.models.backlog import Backlog
from app.models.product import Product
from app.models.user_story import UserStory
from app.models.requirement import Requirement
from app.models.revision import Revision # Para criar revisões do backlog
from app.extensions import db
from app.services.logging_service import logging_service
from datetime import datetime
import json


class BacklogService:
    @staticmethod
    def auto_update_product_backlog(product_id, user_id=None):
        """
        Atualiza automaticamente o backlog de um produto quando há mudanças.
        É chamado automaticamente quando histórias/requisitos são criados/alterados.
        """
        try:
            return BacklogService.generate_product_backlog(
                product_id=product_id, 
                user_id=user_id, 
                custom_criteria="Atualização automática do sistema"
            )
        except Exception as e:
            logging_service.log_error(
                f"Erro na atualização automática do backlog para produto {product_id}: {str(e)}", 
                operation="auto_update_backlog", 
                exception=e, 
                user_id=user_id
            )
            # Não levanta exceção para não interromper o fluxo principal
            return None

    @staticmethod
    def generate_product_backlog(product_id, user_id=None, custom_criteria=None):
        """
        Gera um Product Backlog para um produto, baseado em histórias e requisitos aprovados.
        """
        product = Product.query.get(product_id)
        if not product:
            raise ValueError("Produto não encontrado.")

        # Buscar todas as histórias de usuário para este produto (não apenas aprovadas)
        all_stories = UserStory.query.filter_by(
            product_id=product_id
        ).order_by(UserStory.priority.desc(), UserStory.created_at.asc()).all()

        backlog_items = []
        for story in all_stories:
            story_data = {
                "type": "user_story",
                "id": story.id,
                "text": f"Como um {story.as_a}, eu quero {story.i_want}, para que {story.so_that}",
                "priority": story.priority,
                "status": story.status,
                "epic_id": story.epic_id,
                "product_id": story.product_id,
                "created_at": story.created_at.isoformat() if story.created_at else None,
                "updated_at": story.updated_at.isoformat() if story.updated_at else None
            }
            backlog_items.append(story_data)

            # Adicionar todos os requisitos para esta história (não apenas aprovados)
            all_requirements = Requirement.query.filter_by(
                user_story_id=story.id
            ).order_by(Requirement.priority.desc(), Requirement.created_at.asc()).all()

            for req in all_requirements:
                req_data = {
                    "type": "requirement",
                    "id": req.id,
                    "description": req.description,
                    "priority": req.priority,
                    "status": req.status,
                    "user_story_id": req.user_story_id,
                    "created_at": req.created_at.isoformat() if req.created_at else None,
                    "updated_at": req.updated_at.isoformat() if req.updated_at else None
                }
                backlog_items.append(req_data)
        
        # Criar ou atualizar o backlog no banco de dados
        # Podemos ter múltiplas versões de backlog, ou apenas a mais recente
        existing_backlog = Backlog.query.filter_by(product_id=product_id).first()
        if existing_backlog:
            existing_backlog.set_content(backlog_items)
            existing_backlog.updated_at = datetime.utcnow()
            db.session.add(existing_backlog)
            db.session.commit()
            backlog_obj = existing_backlog
            change_description = "Backlog atualizado"
        else:
            new_backlog = Backlog(
                name=f"Backlog do Produto {product.name}",
                description=f"Backlog gerado para o produto {product.name} em {datetime.utcnow().isoformat()}",
                product_id=product_id
            )
            new_backlog.set_content(backlog_items)
            db.session.add(new_backlog)
            db.session.commit()
            backlog_obj = new_backlog
            change_description = "Backlog gerado"

        # Criar revisão para o backlog (aspecto transversal)
        if user_id:
            content_details = {
                "product_id": product_id,
                "total_items": len(backlog_items),
                "custom_criteria": custom_criteria
            }
            BacklogService._create_revision(backlog_obj, change_description, user_id, content_details)

        logging_service.log_user_action(
            action=change_description,
            user_id=user_id,
            artifact_id=backlog_obj.id,
            artifact_type="backlog",
            details={"product_id": product_id, "total_items": len(backlog_items)}
        )

        return backlog_obj

    @staticmethod
    def get_backlog_by_product_id(product_id):
        """
        Retorna o backlog mais recente de um produto.
        """
        backlog = Backlog.query.filter_by(product_id=product_id).order_by(Backlog.updated_at.desc()).first()
        if backlog:
            content = backlog.get_content()
            return {
                "backlog_id": backlog.id,
                "product_id": backlog.product_id,
                "items": content,
                "total_items": len(content),
                "updated_at": backlog.updated_at.isoformat()
            }
        return None

    @staticmethod
    def get_all_backlogs_by_user(user_id):
        """
        Retorna todos os backlogs de produtos de um usuário.
        """
        # Backlog -> Produto -> Usuário
        return Backlog.query.join(Product).filter(Product.owner_id == user_id).all()

    @staticmethod
    def _create_revision(backlog_obj, change_description, user_id=None, details=None):
        """
        Cria uma revisão para o backlog.
        """
        # O conteúdo da revisão será o JSON do próprio backlog
        content = backlog_obj.get_content()
        
        revision = Revision(
            artifact_id=backlog_obj.id,
            artifact_type='backlog',
            content=json.dumps(content), # Salva o conteúdo completo do backlog
            change_description=change_description,
            user_id=user_id
        )
        
        db.session.add(revision)
        db.session.commit()
        return revision

