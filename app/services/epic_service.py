

from app.models.epic import Epic
from app.models.product import Product
from app.models.revision import Revision
from app.extensions import db
from app.services.llm_service import LLMService # Importa o LLMService
from app.services.logging_service import logging_service # Importa o logging_service
from datetime import datetime
import json
import re # Importa re para parsing de resposta da LLM


class EpicService:
    @staticmethod
    def create_epic(title, description, product_id, generated_by_llm=False, user_id=None):
        """
        Cria um novo épico no banco de dados.
        """
        if not all([title, description, product_id]):
            raise ValueError("Título, descrição e ID do produto são obrigatórios.")

        # Verifica se o produto existe
        product = Product.query.get(product_id)
        if not product:
            raise ValueError("Produto não encontrado.")

        new_epic = Epic(
            title=title,
            description=description,
            product_id=product_id,
            status='draft',
            generated_by_llm=generated_by_llm # Garante que este campo é setado
        )
        
        db.session.add(new_epic)
        db.session.commit()
        
        # Cria uma revisão inicial
        EpicService._create_revision(new_epic, "Épico criado", user_id)
        
        # Log da criação
        if user_id:
            logging_service.log_user_action(
                action="Criou épico",
                user_id=user_id,
                artifact_id=new_epic.id,
                artifact_type="epic",
                details={
                    "title": title,
                    "generated_by_llm": generated_by_llm
                }
            )
        
        return new_epic

    @staticmethod
    def generate_epics_for_product(product, user_id=None, custom_prompt_instruction=None):
        """
        Gera épicos usando IA para um produto específico e salva no banco.
        Esta função é responsável por chamar o LLMService e processar sua resposta.
        """
        if not product:
            raise ValueError("Objeto Produto não fornecido.")

        llm_service = LLMService() # Instancia o LLMService
        try:
            # --- CHAMADA AO LLMService E PROCESSAMENTO DA RESPOSTA ---
            # O LLMService.generate_epics_for_product agora retorna a STRING BRUTA da LLM.
            # Este EpicService é responsável por fazer o parsing dessa string.
            generated_text = llm_service.generate_epics_for_product( # <--- CHAMADA CORRETA
                product=product,
                user_id=user_id,
                custom_prompt_instruction=custom_prompt_instruction
            )
            
            # Processa a resposta para retornar dados estruturados
            if not isinstance(generated_text, str):
                logging_service.log_error("LLM retornou resposta não-string para geração de épicos.", operation="generate_epics_processing", user_id=user_id)
                raise ValueError("Resposta inesperada da LLM: não é uma string.")
            
            # Remove reasoning tags se presente (comum em modelos de reasoning)
            clean_text = generated_text
            if '<think>' in generated_text and '</think>' in generated_text:
                think_end = generated_text.find('</think>')
                if think_end != -1:
                    clean_text = generated_text[think_end + len('</think>'):].strip()
            
            epics_list = []
            try:
                # Tenta parsear como JSON primeiro
                parsed_data = json.loads(clean_text)
                if 'epics' in parsed_data and isinstance(parsed_data['epics'], list):
                    epics_list = parsed_data['epics']
                elif isinstance(parsed_data, list): # Se o JSON é uma lista diretamente
                    epics_list = parsed_data
                else:
                    logging_service.log_warning(f"Formato JSON inesperado da LLM para épicos: {clean_text[:500]}", operation="generate_epics_json_parse", user_id=user_id)
                    raise ValueError("Formato JSON inesperado da LLM.")
            except json.JSONDecodeError:
                # Fallback: tenta encontrar JSON válido no texto ou trata como linhas de texto
                json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
                if json_match:
                    try:
                        parsed_data = json.loads(json_match.group())
                        if 'epics' in parsed_data and isinstance(parsed_data['epics'], list):
                            epics_list = parsed_data['epics']
                        elif isinstance(parsed_data, list):
                            epics_list = parsed_data
                    except json.JSONDecodeError:
                        pass # Continua para o fallback de linha por linha
                
                if not epics_list: # Se ainda não parseou, tenta linha por linha como último recurso
                    logging_service.log_warning(f"LLM não retornou JSON válido para épicos. Tentando fallback de linhas.", operation="generate_epics_fallback", user_id=user_id)
                    lines = [line.strip() for line in clean_text.strip().split('\n') if line.strip()]
                    
                    for i, line in enumerate(lines, 1):
                        if line and len(line) > 5 and len(line) <= 200:
                            clean_line = re.sub(r'^\d+\.\s*', '', line)
                            epics_list.append({
                                'title': clean_line[:100],
                                'description': f"Épico gerado automaticamente: {clean_line[:150]}"
                            })
            # --- FIM DO PROCESSAMENTO ---
            
            created_epics = []
            for epic_data in epics_list:
                title = epic_data.get('name', epic_data.get('title', ''))
                description = epic_data.get('description', '')

                if title:
                    title = title[:250] 
                    description = description[:1000] if description else ""
                    
                    epic = EpicService.create_epic(
                        title=title,
                        description=description,
                        product_id=product.id,
                        generated_by_llm=True,
                        user_id=user_id
                    )
                    created_epics.append(epic)

            return created_epics

        except Exception as e:
            # Garante que o log de erro da LLM interaction use o modelo correto do LLMService
            logging_service.log_llm_interaction(
                operation="generate_epics_for_product",
                model=llm_service.model, # Usa o modelo do LLMService
                prompt_type="Epic Generation",
                input_data={"product_id": product.id, "custom_prompt": custom_prompt_instruction},
                error=str(e),
                user_id=user_id
            )
            raise e 

    @staticmethod
    def get_epic_by_id(epic_id):
        """Busca um épico pelo ID."""
        return Epic.query.get(epic_id)

    @staticmethod
    def get_epics_by_product(product_id):
        """Retorna todos os épicos de um produto."""
        return Epic.query.filter_by(product_id=product_id).all()

    @staticmethod
    def get_epics_by_user(user_id):
        """Retorna todos os épicos de um usuário."""
        return Epic.query.join(Product).filter(Product.owner_id == user_id).all()

    @staticmethod
    def update_epic(epic_id, title=None, description=None, status=None, user_id=None):
        """Atualiza as informações de um épico existente."""
        epic = Epic.query.get(epic_id)
        if not epic:
            raise ValueError("Épico não encontrado.")

        changes = {}
        if title and title != epic.title:
            changes['title'] = {'old': epic.title, 'new': title}
            epic.title = title
        if description and description != epic.description:
            changes['description'] = {'old': epic.description, 'new': description}
            epic.description = description
        if status and status != epic.status:
            changes['status'] = {'old': epic.status, 'new': status}
            epic.status = status

        epic.updated_at = datetime.utcnow()
        db.session.commit()

        if changes:
            change_description = f"Épico atualizado: {', '.join(changes.keys())}"
            EpicService._create_revision(epic, change_description, user_id)

        return epic

    @staticmethod
    def delete_epic(epic_id, user_id=None):
        """
        Deleta um épico pelo ID, incluindo todas as histórias e requisitos associados.
        """
        from app.models.user_story import UserStory
        from app.models.requirement import Requirement
        from app.models.revision import Revision
        
        epic = Epic.query.get(epic_id)
        if not epic:
            raise ValueError("Épico não encontrado.")

        if user_id:
            logging_service.log_user_action(
                action="Deletou épico",
                user_id=user_id,
                artifact_id=epic.id,
                artifact_type="epic",
                details={"title": epic.title}
            )

        # 1. Buscar todas as histórias do épico
        stories = UserStory.query.filter_by(epic_id=epic_id).all()
        
        for story in stories:
            # 2. Para cada história, deletar seus requisitos e revisões
            requirements = Requirement.query.filter_by(user_story_id=story.id).all()
            for requirement in requirements:
                # Deletar revisões do requisito
                Revision.query.filter_by(artifact_id=requirement.id, artifact_type='requirement').delete()
                db.session.delete(requirement)
            
            # 3. Deletar revisões da história
            Revision.query.filter_by(artifact_id=story.id, artifact_type='user_story').delete()
            # 4. Deletar a história
            db.session.delete(story)
        
        # 5. Deletar revisões do épico
        Revision.query.filter_by(artifact_id=epic_id, artifact_type='epic').delete()
        # 6. Deletar o épico
        db.session.delete(epic)
        db.session.commit()
        return True

    @staticmethod
    def _create_revision(epic, change_description, user_id=None):
        """
        Cria uma revisão para o épico.
        """
        content = {
            'id': epic.id,
            'title': epic.title,
            'description': epic.description,
            'status': epic.status,
            'product_id': epic.product_id,
            'created_at': epic.created_at.isoformat() if epic.created_at else None,
            'updated_at': epic.updated_at.isoformat() if epic.updated_at else None
        }

        revision = Revision(
            artifact_id=epic.id,
            artifact_type='epic',
            content=json.dumps(content),
            change_description=change_description,
            user_id=user_id
        )
        
        db.session.add(revision)
        db.session.commit()
        return revision
