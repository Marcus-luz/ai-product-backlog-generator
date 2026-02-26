

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


class UserStoryService:
    @staticmethod
    def create_user_story(as_a, i_want, so_that, epic_id=None, product_id=None, 
                            priority='medium', generated_by_llm=False, user_id=None):
        """
        Cria uma nova história de usuário no banco de dados.
        """
        if not all([as_a, i_want, so_that]):
            raise ValueError("Todos os campos da história de usuário (Como, Eu quero, Para que) são obrigatórios.")

        # Se epic_id é fornecido mas product_id não, tenta inferir product_id do épico
        if epic_id and not product_id:
            epic = Epic.query.get(epic_id)
            if epic:
                product_id = epic.product_id
            else:
                raise ValueError("Épico não encontrado para inferir o produto.")
        
        if not product_id:
            raise ValueError("ID do produto é obrigatório para criar a história de usuário.")

        # Verifica se o produto existe
        product = Product.query.get(product_id)
        if not product:
            raise ValueError("Produto não encontrado.")

        new_user_story = UserStory(
            as_a=as_a,
            i_want=i_want,
            so_that=so_that,
            epic_id=epic_id,
            product_id=product_id,
            priority=priority,
            status='draft',
            generated_by_llm=generated_by_llm
        )
        
        db.session.add(new_user_story)
        db.session.commit()
        
        # Cria uma revisão inicial
        UserStoryService._create_revision(new_user_story, "História de usuário criada", user_id)
        
        # Atualização automática do backlog do produto
        from app.services.backlog_service import BacklogService
        BacklogService.auto_update_product_backlog(product_id, user_id)
        
        # Log da criação
        if user_id:
            logging_service.log_user_action(
                action="Criou história de usuário",
                user_id=user_id,
                artifact_id=new_user_story.id,
                artifact_type="user_story",
                details={
                    "as_a": as_a,
                    "i_want": i_want,
                    "so_that": so_that,
                    "generated_by_llm": generated_by_llm,
                    "epic_id": epic_id,
                    "product_id": product_id
                }
            )
        
        return new_user_story

    @staticmethod
    def generate_user_stories_for_epic(epic_id, user_id=None, custom_prompt_instruction=None):
        """
        Gera histórias de usuário usando IA para um épico específico e salva no banco.
        """
        epic = Epic.query.get(epic_id)
        if not epic:
            raise ValueError("Épico não encontrado.")
        
        product = Product.query.get(epic.product_id)
        if not product:
            raise ValueError("Produto associado ao épico não encontrado.")

        llm_service = LLMService()
        try:
            # --- CORREÇÃO AQUI: Formatar personas para string legível pela LLM ---
            # product.personas é uma relação. Precisamos extrair os nomes.
            # Se a relação estiver vazia ou não carregada, será uma lista vazia.
            personas_list = [p.name for p in product.personas.all()] 
            personas_str = ", ".join(personas_list) if personas_list else 'Nenhuma persona definida.'
            # --- FIM DA CORREÇÃO ---

            # Chama LLMService para gerar o texto bruto (string)
            generated_text = llm_service.generate_user_stories_for_epic(
                product_name=product.name,
                product_description=product.description,
                personas=personas_str, # Passa a string formatada
                epic_name=epic.title,
                user_id=user_id,
                custom_prompt_instruction=custom_prompt_instruction
            )
            
            # Processa a resposta para retornar dados estruturados
            if not isinstance(generated_text, str):
                logging_service.log_error("LLM retornou resposta não-string para geração de histórias.", operation="generate_stories_processing", user_id=user_id)
                raise ValueError("Resposta inesperada da LLM: não é uma string.")
            
            # Remove reasoning tags se presente (comum em modelos de reasoning)
            clean_text = generated_text
            if '<think>' in generated_text and '</think>' in generated_text:
                think_end = generated_text.find('</think>')
                if think_end != -1:
                    clean_text = generated_text[think_end + len('</think>'):].strip()
            
            stories_list = []
            try:
                # Tenta parsear como JSON primeiro
                parsed_data = json.loads(clean_text)
                if 'user_stories' in parsed_data and isinstance(parsed_data['user_stories'], list):
                    stories_list = parsed_data['user_stories']
                elif isinstance(parsed_data, list): # Se o JSON é uma lista diretamente
                    stories_list = parsed_data
                else:
                    logging_service.log_warning(f"Formato JSON inesperado da LLM para histórias: {clean_text[:500]}", operation="generate_stories_json_parse", user_id=user_id)
                    raise ValueError("Formato JSON inesperado da LLM.")
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
                if json_match:
                    try:
                        parsed_data = json.loads(json_match.group())
                        if 'user_stories' in parsed_data and isinstance(parsed_data['user_stories'], list):
                            stories_list = parsed_data['user_stories']
                        elif isinstance(parsed_data, list):
                            stories_list = parsed_data
                    except json.JSONDecodeError:
                        pass
                
                if not stories_list:
                    logging_service.log_warning(f"LLM não retornou JSON válido para histórias. Tentando fallback de linhas.", operation="generate_stories_fallback", user_id=user_id)
                    lines = [line.strip() for line in clean_text.strip().split('\n') if line.strip()]
                    
                    for i, line in enumerate(lines, 1):
                        if line and len(line) > 10:
                            clean_line = re.sub(r'^\d+\.\s*', '', line)
                            stories_list.append({
                                'as_a': 'Usuário',
                                'i_want': clean_line,
                                'so_that': 'para que eu possa usar a funcionalidade.'
                            })
            
            created_stories = []
            for story_data in stories_list:
                # Check if we have separate fields or a full story text
                if story_data.get('story'):
                    # Parse the full story text
                    story_text = story_data.get('story', '')
                    parsed_as_a, parsed_i_want, parsed_so_that = UserStoryService._parse_user_story_text(story_text)
                    
                    if parsed_as_a and parsed_i_want and parsed_so_that:
                        as_a = parsed_as_a
                        i_want = parsed_i_want
                        so_that = parsed_so_that
                    else:
                        # If parsing failed, skip this story
                        logging_service.log_warning(f"Não foi possível fazer parsing da história: {story_text}", operation="generate_stories_parse_failed", user_id=user_id)
                        continue
                else:
                    # Use separate fields
                    as_a = story_data.get('as_a', 'Usuário')
                    i_want = story_data.get('i_want', '')
                    so_that = story_data.get('so_that', '')
                
                priority = story_data.get('priority', 'medium')

                if i_want and as_a and so_that:
                    final_as_a = as_a[:100] if as_a else 'usuário'
                    final_i_want = i_want[:500] if i_want else 'realizar uma ação'
                    final_so_that = so_that[:500] if so_that else 'obter valor'
                    
                    if (UserStoryService._is_valid_field(final_as_a) and 
                        UserStoryService._is_valid_field(final_i_want) and 
                        UserStoryService._is_valid_field(final_so_that)):
                        
                        story = UserStoryService.create_user_story(
                            as_a=final_as_a,
                            i_want=final_i_want,
                            so_that=final_so_that,
                            epic_id=epic.id,
                            product_id=product.id,
                            priority=priority.lower() if priority else 'medium',
                            generated_by_llm=True,
                            user_id=user_id
                        )
                        created_stories.append(story)
                    else:
                        logging_service.log_warning(f"História gerada pela LLM contém texto inválido após parsing: {story_data}", operation="generate_stories_invalid_field", user_id=user_id)
                else:
                    logging_service.log_warning(f"História gerada pela LLM não tem campos obrigatórios preenchidos: {story_data}", operation="generate_stories_missing_fields", user_id=user_id)

            return created_stories

        except Exception as e:
            logging_service.log_llm_interaction(
                operation="generate_user_stories_for_epic",
                model=llm_service.model,
                prompt_type="User Story Generation",
                input_data={"epic_id": epic_id, "custom_prompt": custom_prompt_instruction},
                error=str(e),
                user_id=user_id
            )
            raise e

    @staticmethod
    def get_user_story_by_id(story_id):
        """
        Busca uma história de usuário pelo ID.
        """
        return UserStory.query.get(story_id)

    @staticmethod
    def get_user_stories_by_epic(epic_id):
        """
        Retorna todas as histórias de usuário de um épico.
        """
        return UserStory.query.filter_by(epic_id=epic_id).all()

    @staticmethod
    def get_user_stories_by_product(product_id):
        """
        Retorna todas as histórias de usuário de um produto.
        """
        return UserStory.query.filter_by(product_id=product_id).all()

    @staticmethod
    def get_user_stories_by_user(user_id):
        """
        Retorna todas as histórias de usuário de um usuário.
        """
        # Simplificar a consulta - buscar todas as histórias do usuário
        # através dos produtos que ele possui
        from sqlalchemy.orm import joinedload
        
        # Primeiro buscar todos os produtos do usuário
        user_products = Product.query.filter_by(owner_id=user_id).all()
        product_ids = [p.id for p in user_products]
        
        if not product_ids:
            return []
        
        # Buscar histórias desses produtos com join eager loading
        return UserStory.query.options(
            joinedload(UserStory.epic)
        ).filter(
            UserStory.product_id.in_(product_ids)
        ).all()

    @staticmethod
    def update_user_story(story_id, as_a=None, i_want=None, so_that=None, 
                            priority=None, status=None, user_id=None):
        """
        Atualiza as informações de uma história de usuário existente.
        """
        story = UserStory.query.get(story_id)
        if not story:
            raise ValueError("História de usuário não encontrada.")

        changes = {}
        if as_a and as_a != story.as_a:
            changes['as_a'] = {'old': story.as_a, 'new': as_a}
            story.as_a = as_a
        if i_want and i_want != story.i_want:
            changes['i_want'] = {'old': story.i_want, 'new': i_want}
            story.i_want = i_want
        if so_that and so_that != story.so_that:
            changes['so_that'] = {'old': story.so_that, 'new': so_that}
            story.so_that = so_that
        if priority and priority != story.priority:
            changes['priority'] = {'old': story.priority, 'new': priority}
            story.priority = priority
        if status and status != story.status:
            changes['status'] = {'old': story.status, 'new': status}
            story.status = status

        story.updated_at = datetime.utcnow()
        db.session.commit()

        # Cria revisão se houve mudanças
        if changes:
            change_description = f"História atualizada: {', '.join(changes.keys())}"
            UserStoryService._create_revision(story, change_description, user_id)
            
            # Atualização automática do backlog do produto se status ou prioridade mudaram
            if 'status' in changes or 'priority' in changes:
                from app.services.backlog_service import BacklogService
                BacklogService.auto_update_product_backlog(story.product_id, user_id)

        return story

    @staticmethod
    def delete_user_story(story_id, user_id=None):
        """
        Deleta uma história de usuário pelo ID, incluindo todos os requisitos associados.
        """
        from app.models.requirement import Requirement
        from app.models.revision import Revision
        
        story = UserStory.query.get(story_id)
        if not story:
            raise ValueError("História de usuário não encontrada.")

        # Log antes de deletar
        if user_id:
            logging_service.log_user_action(
                action="Deletou história de usuário",
                user_id=user_id,
                artifact_id=story.id,
                artifact_type="user_story",
                details={
                    "as_a": story.as_a,
                    "i_want": story.i_want
                }
            )

        # 1. Buscar todos os requisitos da história
        requirements = Requirement.query.filter_by(user_story_id=story_id).all()
        
        # 2. Deletar todos os requisitos e suas revisões
        for requirement in requirements:
            # Deletar revisões do requisito
            Revision.query.filter_by(artifact_id=requirement.id, artifact_type='requirement').delete()
            db.session.delete(requirement)
        
        # 3. Deletar revisões da história
        Revision.query.filter_by(artifact_id=story_id, artifact_type='user_story').delete()
        # 4. Deletar a história
        db.session.delete(story)
        db.session.commit()
        return True

    @staticmethod
    def _create_revision(story, change_description, user_id=None):
        """
        Cria uma revisão para a história de usuário.
        """
        content = {
            'id': story.id,
            'as_a': story.as_a,
            'i_want': story.i_want,
            'so_that': story.so_that,
            'priority': story.priority,
            'status': story.status,
            'epic_id': story.epic_id,
            'product_id': story.product_id,
            'generated_by_llm': story.generated_by_llm,
            'created_at': story.created_at.isoformat() if story.created_at else None,
            'updated_at': story.updated_at.isoformat() if story.updated_at else None
        }

        revision = Revision(
            artifact_id=story.id,
            artifact_type='user_story',
            content=json.dumps(content),
            change_description=change_description,
            user_id=user_id
        )
        
        db.session.add(revision)
        db.session.commit()
        return revision

    @staticmethod
    def _parse_user_story_text(story_text):
        """
        Parse de uma história de usuário no formato padrão "Como um [X], eu quero [Y], para que [Z]".
        Retorna (as_a, i_want, so_that) ou (None, None, None) se não conseguir parsear.
        """
        pattern = r'Como um\s+(.+?),\s*eu quero\s+(.+?),\s*para que\s+(.+?)(?:\.|$)'
        match = re.search(pattern, story_text, re.IGNORECASE)
        
        if match:
            return match.group(1).strip(), match.group(2).strip(), match.group(3).strip()
        
        return None, None, None # Retorna None se não conseguir parsear

    @staticmethod 
    def _is_valid_story_format(story_data):
        """
        Verifica se os dados de uma história (geralmente do JSON da LLM) têm os campos esperados.
        """
        if isinstance(story_data, dict):
            # Verifica se tem pelo menos um dos campos principais
            if story_data.get('story') or (story_data.get('as_a') and story_data.get('i_want')):
                return True
        return False

    @staticmethod 
    def _is_valid_field(field_text):
        """
        Verifica se um campo específico está válido (não contém texto de debugging da IA).
        """
        if not field_text or len(field_text) < 2:
            return False
            
        field_lower = field_text.lower()
        
        # Rejeita campos que contêm texto de debugging ou JSON incompleto
        invalid_patterns = [
            '```json', '```', '<think>', '</think>', '{{', '}}',
            'let me think', 'okay, so', 'first, let me', 'here are',
            '"user_stories":', '"id":', '"story":', '"priority":', '"persona":',
            'json.loads', 'json.dumps', 'parse_json', 'api_response'
        ]
        
        for pattern in invalid_patterns:
            if pattern in field_lower:
                return False
                
        return True