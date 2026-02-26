

from app.models.requirement import Requirement
from app.models.user_story import UserStory
from app.models.epic import Epic
from app.models.product import Product
from app.models.revision import Revision
from app.extensions import db
from app.services.llm_service import LLMService
from app.services.logging_service import logging_service
from datetime import datetime
import json
import re


class RequirementService:
    """
    Serviço para gerenciar requisitos funcionais e critérios de aceite.
    
    Responsável por criar, atualizar, buscar e gerar requisitos usando IA,
    além de manter o histórico de revisões e integração com o backlog.
    """
    
    @staticmethod
    def create_requirement(description, user_story_id, priority='medium', generated_by_llm=False, user_id=None):
        """
        Cria um novo requisito no banco de dados.
        
        Args:
            description (str): Descrição do requisito
            user_story_id (int): ID da história de usuário associada
            priority (str): Prioridade do requisito (low, medium, high)
            generated_by_llm (bool): Se foi gerado por IA
            user_id (int): ID do usuário que criou o requisito
            
        Returns:
            Requirement: O requisito criado
            
        Raises:
            ValueError: Se dados obrigatórios estão ausentes ou inválidos
        """
        if not all([description, user_story_id]):
            raise ValueError("Descrição e ID da história de usuário são obrigatórios.")

        user_story = UserStory.query.get(user_story_id)
        if not user_story:
            raise ValueError("História de usuário não encontrada.")
        
        new_requirement = Requirement(
            description=description,
            user_story_id=user_story_id,
            priority=priority,
            status='draft',
            generated_by_llm=generated_by_llm
        )
        
        db.session.add(new_requirement)
        db.session.commit()
        
        RequirementService._create_revision(new_requirement, "Requisito criado", user_id)
        
        from app.services.backlog_service import BacklogService
        BacklogService.auto_update_product_backlog(user_story.product_id, user_id)
        
        if user_id:
            logging_service.log_user_action(
                action="Criou requisito",
                user_id=user_id,
                artifact_id=new_requirement.id,
                artifact_type="requirement",
                details={
                    "description_preview": description[:100],
                    "user_story_id": user_story_id
                }
            )
        
        return new_requirement

    @staticmethod
    def generate_requirements_for_user_story(user_story_id, user_id=None, custom_prompt_instruction=None):
        """
        Gera requisitos funcionais e critérios de aceite usando IA para uma história de usuário específica.
        
        Args:
            user_story_id (int): ID da história de usuário
            user_id (int): ID do usuário solicitante
            custom_prompt_instruction (str): Instruções customizadas para o prompt
            
        Returns:
            list: Lista de requisitos criados
            
        Raises:
            ValueError: Se a história de usuário não for encontrada ou resposta da IA for inválida
        """
        user_story = UserStory.query.get(user_story_id)
        if not user_story:
            raise ValueError("História de usuário não encontrada.")

        llm_service = LLMService()
        try:
            generated_text = llm_service.generate_requirements_for_user_story(
                user_story_text=f"Como um {user_story.as_a}, eu quero {user_story.i_want}, para que {user_story.so_that}",
                user_id=user_id,
                custom_prompt_instruction=custom_prompt_instruction
            )
            
            if not isinstance(generated_text, str):
                logging_service.log_error("LLM retornou resposta não-string para geração de requisitos.", operation="generate_requirements_processing", user_id=user_id)
                raise ValueError("Resposta inesperada da LLM: não é uma string.")
            
            clean_text = generated_text
            if '<think>' in generated_text and '</think>' in generated_text:
                think_end = generated_text.find('</think>')
                if think_end != -1:
                    clean_text = generated_text[think_end + len('</think>'):].strip()
            
            requirements_data = {"functional_requirements": [], "acceptance_criteria": []}
            try:
                parsed_data = json.loads(clean_text)
                if 'functional_requirements' in parsed_data and 'acceptance_criteria' in parsed_data:
                    requirements_data = parsed_data
                else:
                    logging_service.log_warning(f"Formato JSON inesperado da LLM para requisitos: {clean_text[:500]}", operation="generate_requirements_json_parse", user_id=user_id)
                    raise ValueError("Formato JSON inesperado da LLM.")
            except json.JSONDecodeError:
                logging_service.log_warning(f"LLM não retornou JSON válido para requisitos. Retornando vazio.", operation="generate_requirements_fallback", user_id=user_id)
            
            created_requirements = []
            for req_data in requirements_data.get('functional_requirements', []):
                description = req_data.get('requirement', '')
                if description:
                    requirement = RequirementService.create_requirement(
                        description=description[:1000],
                        user_story_id=user_story.id,
                        priority='medium',
                        generated_by_llm=True,
                        user_id=user_id
                    )
                    created_requirements.append(requirement)
            
            if requirements_data.get('acceptance_criteria'):
                ac_text = "\n\nCritérios de Aceite:\n"
                for ac in requirements_data['acceptance_criteria']:
                    scenario = ac.get('scenario', 'Cenário')
                    given = ac.get('given', '')
                    when = ac.get('when', '')
                    then = ac.get('then', '')
                    ac_text += f"- {scenario}:\n  Dado {given}\n  Quando {when}\n  Então {then}\n"
                
                if created_requirements:
                    created_requirements[-1].description += ac_text
                    db.session.commit()
                else:
                    logging_service.log_info(f"Critérios de Aceite gerados sem requisito associado: {ac_text}", operation="acceptance_criteria_no_req", user_id=user_id, details={"user_story_id": user_story.id})

            return created_requirements
        except Exception as e:
            logging_service.log_llm_interaction(
                operation="generate_requirements_for_user_story",
                model=llm_service.model,
                prompt_type="Requirement Generation",
                input_data={"user_story_id": user_story_id, "custom_prompt": custom_prompt_instruction},
                error=str(e),
                user_id=user_id
            )
            raise e

    @staticmethod
    def get_requirement_by_id(requirement_id):
        """
        Busca um requisito pelo ID.
        
        Args:
            requirement_id (int): ID do requisito
            
        Returns:
            Requirement: O requisito encontrado ou None
        """
        return Requirement.query.get(requirement_id)

    @staticmethod
    def get_requirements_by_user_story(user_story_id):
        """
        Retorna todos os requisitos de uma história de usuário.
        
        Args:
            user_story_id (int): ID da história de usuário
            
        Returns:
            list: Lista de requisitos da história de usuário
        """
        return Requirement.query.filter_by(user_story_id=user_story_id).all()

    @staticmethod
    def get_requirements_by_user(user_id):
        """
        Retorna todos os requisitos de um usuário.
        
        Args:
            user_id (int): ID do usuário
            
        Returns:
            list: Lista de requisitos do usuário
        """
        return Requirement.query.join(UserStory).join(Epic).join(Product).filter(Product.owner_id == user_id).all()

    @staticmethod
    def update_requirement(requirement_id, description=None, priority=None, status=None, user_id=None):
        """
        Atualiza as informações de um requisito existente.
        
        Args:
            requirement_id (int): ID do requisito
            description (str): Nova descrição
            priority (str): Nova prioridade
            status (str): Novo status
            user_id (int): ID do usuário que fez a alteração
            
        Returns:
            Requirement: O requisito atualizado
            
        Raises:
            ValueError: Se o requisito não for encontrado
        """
        requirement = Requirement.query.get(requirement_id)
        if not requirement:
            raise ValueError("Requisito não encontrado.")

        changes = {}
        if description and description != requirement.description:
            changes['description'] = {'old': requirement.description, 'new': description}
            requirement.description = description
        if priority and priority != requirement.priority:
            changes['priority'] = {'old': requirement.priority, 'new': priority}
            requirement.priority = priority
        if status and status != requirement.status:
            changes['status'] = {'old': requirement.status, 'new': status}
            requirement.status = status

        requirement.updated_at = datetime.utcnow()
        db.session.commit()

        if changes:
            change_description = f"Requisito atualizado: {', '.join(changes.keys())}"
            RequirementService._create_revision(requirement, change_description, user_id)
            
            if 'status' in changes or 'priority' in changes:
                from app.services.backlog_service import BacklogService
                user_story = UserStory.query.get(requirement.user_story_id)
                if user_story:
                    BacklogService.auto_update_product_backlog(user_story.product_id, user_id)

        return requirement

    @staticmethod
    def delete_requirement(requirement_id, user_id=None):
        """
        Deleta um requisito pelo ID, incluindo suas revisões.
        
        Args:
            requirement_id (int): ID do requisito
            user_id (int): ID do usuário que deletou
            
        Returns:
            bool: True se deletado com sucesso
            
        Raises:
            ValueError: Se o requisito não for encontrado
        """
        from app.models.revision import Revision
        
        requirement = Requirement.query.get(requirement_id)
        if not requirement:
            raise ValueError("Requisito não encontrado.")

        if user_id:
            logging_service.log_user_action(
                action="Deletou requisito",
                user_id=user_id,
                artifact_id=requirement.id,
                artifact_type="requirement",
                details={
                    "description_preview": requirement.description[:100]
                }
            )

        Revision.query.filter_by(artifact_id=requirement_id, artifact_type='requirement').delete()
        db.session.delete(requirement)
        db.session.commit()
        return True

    @staticmethod
    def _create_revision(requirement, change_description, user_id=None):
        """
        Cria uma revisão para o requisito.
        
        Args:
            requirement (Requirement): O requisito
            change_description (str): Descrição da mudança
            user_id (int): ID do usuário responsável pela mudança
            
        Returns:
            Revision: A revisão criada
        """
        content = {
            'id': requirement.id,
            'description': requirement.description,
            'priority': requirement.priority,
            'status': requirement.status,
            'user_story_id': requirement.user_story_id,
            'created_at': requirement.created_at.isoformat() if requirement.created_at else None,
            'updated_at': requirement.updated_at.isoformat() if requirement.updated_at else None
        }

        revision = Revision(
            artifact_id=requirement.id,
            artifact_type='requirement',
            content=json.dumps(content),
            change_description=change_description,
            user_id=user_id
        )
        
        db.session.add(revision)
        db.session.commit()
        return revision