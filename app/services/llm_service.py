
"""
Serviço para integração com APIs de Large Language Models (LLM).

Responsável por gerenciar as chamadas para a API Groq e outros provedores de LLM,
incluindo geração de épicos, histórias de usuário, requisitos e sugestões de prioridade.
"""

import os
import time
from datetime import datetime
from groq import Groq
import json
import re

from app.utils.prompt_templates import (
    EPIC_GENERATION_SYSTEM_PROMPT, EPIC_GENERATION_USER_PROMPT,
    USER_STORY_GENERATION_SYSTEM_PROMPT, USER_STORY_GENERATION_USER_PROMPT,
    REQUIREMENT_GENERATION_SYSTEM_PROMPT, REQUIREMENT_GENERATION_USER_PROMPT,
    PRIORITY_SUGGESTION_SYSTEM_PROMPT, PRIORITY_SUGGESTION_USER_PROMPT
)
from app.services.logging_service import logging_service


class LLMService:
    """
    Serviço para interação com modelos de linguagem via API Groq.
    
    Fornece métodos para geração de diferentes tipos de artefatos ágeis
    como épicos, histórias de usuário e requisitos.
    """
    
    def __init__(self):
        """
        Inicializa o cliente da Groq.
        
        Raises:
            ValueError: Se a chave de API não foi encontrada
        """
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("A variável de ambiente GROQ_API_KEY não foi definida.")
        
        self.client = Groq(api_key=api_key)
        self.model = os.getenv("GROQ_MODEL", 'llama3-8b-8192')

    def _call_llm(self, system_prompt, user_prompt, operation="generic_llm_call", user_id=None):
        """
        Método auxiliar para chamar a API Groq com sistema e prompts do usuário.
        
        Args:
            system_prompt (str): Prompt do sistema para contexto
            user_prompt (str): Prompt do usuário com a solicitação específica
            operation (str): Nome da operação para logging
            user_id (int): ID do usuário para logging
            
        Returns:
            str: Resposta do modelo de linguagem
            
        Raises:
            Exception: Se houver erro na chamada da API
        """
        start_time = time.time()
        
        input_data = {
            'system_prompt_preview': system_prompt[:200] + "..." if len(system_prompt) > 200 else system_prompt,
            'user_prompt_preview': user_prompt[:200] + "..." if len(user_prompt) > 200 else user_prompt,
            'model': self.model,
            'full_prompt_length': len(system_prompt) + len(user_prompt)
        }
        
        print(f"--- CHAMANDO API DA GROQ COM O MODELO: {self.model} ---")
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
                model=self.model,
                temperature=0.6,
                max_tokens=4096, # <--- AJUSTADO: Usado 'max_tokens' em vez de 'max_completion_tokens'
                top_p=0.95,
                stop=None,
            )
            
            execution_time = time.time() - start_time
            response_content = chat_completion.choices[0].message.content
            
            # Log de sucesso
            logging_service.log_llm_interaction(
                operation=operation,
                model=self.model,
                prompt_type=operation.replace("_", " ").title(),
                input_data=input_data,
                response=response_content,
                execution_time=execution_time,
                user_id=user_id
            )
            
            return response_content
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)
            
            print(f"Ocorreu um erro ao chamar a API da Groq: {e}")
            
            # Log de erro
            logging_service.log_llm_interaction(
                operation=operation,
                model=self.model,
                prompt_type=operation.replace("_", " ").title(),
                input_data=input_data,
                error=error_message,
                execution_time=execution_time,
                user_id=user_id
            )
            
            # Re-lança a exceção para a camada superior tratar
            raise e 

    def generate_epics_for_product(self, product, user_id=None, custom_prompt_instruction=None):
        """
        Gera épicos para um determinado produto usando a API da Groq
        e os templates de prompt centralizados.
        """
        # Garante que personas e canais sejam strings, mesmo se forem None no objeto Product
        # AJUSTADO: Usando verificação explícita para None em vez de getattr para clareza
        personas_str = product.personas if product.personas else 'Nenhuma persona definida.'
        channels_str = product.channels_platforms if product.channels_platforms else 'Nenhum canal/plataforma definido.'

        user_prompt_content = EPIC_GENERATION_USER_PROMPT.format(
            product_name=product.name,
            product_description=product.description,
            personas=personas_str, # <--- AJUSTADO
            value_proposition=product.value_proposition,
            channels=channels_str # <--- AJUSTADO
        )

        # Adiciona a instrução customizada ao prompt do usuário se fornecida
        if custom_prompt_instruction:
            user_prompt_content += f"\n\nInstrução Adicional: {custom_prompt_instruction}"

        generated_text = self._call_llm(
            EPIC_GENERATION_SYSTEM_PROMPT, 
            user_prompt_content,
            operation="generate_epics_for_product",
            user_id=user_id
        )
        return generated_text
        
        # Processa a resposta para retornar dados estruturados
        if not isinstance(generated_text, str):
            logging_service.log_error("LLM retornou resposta não-string para geração de épicos.", operation="generate_epics_processing", user_id=user_id)
            return [] # Retorna lista vazia se a resposta não for string
        
        # Remove reasoning tags se presente (comum em modelos de reasoning)
        clean_text = generated_text
        if '<think>' in generated_text and '</think>' in generated_text:
            think_end = generated_text.find('</think>')
            if think_end != -1:
                # <--- AJUSTADO: Removendo a tag de fechamento corretamente
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
                # <--- AJUSTADO: Usando logging_service.log_warning (precisa existir no logging_service)
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
                # <--- AJUSTADO: Usando logging_service.log_warning
                logging_service.log_warning(f"LLM não retornou JSON válido para épicos. Tentando fallback de linhas.", operation="generate_epics_fallback", user_id=user_id)
                lines = [line.strip() for line in clean_text.strip().split('\n') if line.strip()]
                
                for i, line in enumerate(lines, 1):
                    if line and len(line) > 5 and len(line) <= 200:
                        clean_line = re.sub(r'^\d+\.\s*', '', line)
                        epics_list.append({
                            'title': clean_line[:100],
                            'description': f"Épico gerado automaticamente: {clean_line[:150]}"
                        })
        
        return epics_list

    def generate_user_stories_for_epic(self, product_name, product_description, personas, epic_name, user_id=None,custom_prompt_instruction=None):
        """
        Gera histórias de usuário para um épico específico.
        """
        user_prompt_content = USER_STORY_GENERATION_USER_PROMPT.format(
            product_name=product_name,
            product_description=product_description,
            personas=personas,
            epic_name=epic_name
        )
        if custom_prompt_instruction:
            user_prompt_content += f"\n\nAdditional Instruction: {custom_prompt_instruction}"
            
        generated_text = self._call_llm(
            USER_STORY_GENERATION_SYSTEM_PROMPT, 
            user_prompt_content,
            operation="generate_user_stories_for_epic",
            user_id=user_id
        )
        return generated_text
        if not isinstance(generated_text, str):
            logging_service.log_error("LLM retornou resposta não-string para geração de histórias.", operation="generate_stories_processing", user_id=user_id)
            return []
        
        try:
            # Tenta parsear como JSON primeiro
            parsed_data = json.loads(generated_text)
            if 'user_stories' in parsed_data and isinstance(parsed_data['user_stories'], list):
                return parsed_data['user_stories']
            elif isinstance(parsed_data, list):
                return parsed_data
            else:
                # <--- AJUSTADO: Usando logging_service.log_warning
                logging_service.log_warning(f"Formato JSON inesperado da LLM para histórias: {generated_text[:500]}", operation="generate_stories_json_parse", user_id=user_id)
                raise ValueError("Formato JSON inesperado da LLM.")
        except json.JSONDecodeError:
            # <--- AJUSTADO: Usando logging_service.log_warning
            logging_service.log_warning(f"LLM não retornou JSON válido para histórias. Tentando fallback de linhas.", operation="generate_stories_fallback", user_id=user_id)
            # Fallback: trata como lista de linhas de texto
            stories_list = []
            lines = [line.strip() for line in generated_text.strip().split('\n') if line.strip()]
            
            for i, line in enumerate(lines, 1):
                if line and len(line) > 10:
                    clean_line = re.sub(r'^\d+\.\s*', '', line)
                    stories_list.append({
                        'id': i,
                        'story': clean_line,
                        'persona': 'usuário', # Placeholder, idealmente LLM deveria inferir
                        'priority': 'medium' # Placeholder
                    })
            
            return stories_list

    def generate_requirements_for_user_story(self, user_story_text, user_id=None,custom_prompt_instruction=None):
        """
        Gera requisitos funcionais e critérios de aceite para uma história de usuário.
        """
        user_prompt_content = REQUIREMENT_GENERATION_USER_PROMPT.format(
            user_story_text=user_story_text
        )
        
        generated_text = self._call_llm(
            REQUIREMENT_GENERATION_SYSTEM_PROMPT, 
            user_prompt_content,
            operation="generate_requirements_for_user_story",
            user_id=user_id
        )
        return generated_text
        # Processa a resposta para retornar dados estruturados
        if not isinstance(generated_text, str):
            logging_service.log_error("LLM retornou resposta não-string para geração de requisitos.", operation="generate_requirements_processing", user_id=user_id)
            return []
        
        try:
            parsed_data = json.loads(generated_text)
            if 'functional_requirements' in parsed_data and 'acceptance_criteria' in parsed_data:
                return parsed_data # Retorna o objeto completo com ambas as chaves
            else:
                # <--- AJUSTADO: Usando logging_service.log_warning
                logging_service.log_warning(f"Formato JSON inesperado da LLM para requisitos: {generated_text[:500]}", operation="generate_requirements_json_parse", user_id=user_id)
                raise ValueError("Formato JSON inesperado da LLM.")
        except json.JSONDecodeError:
            # <--- AJUSTADO: Usando logging_service.log_warning
            logging_service.log_warning(f"LLM não retornou JSON válido para requisitos. Retornando vazio.", operation="generate_requirements_fallback", user_id=user_id)
            return [] # Retorna vazio se não for JSON válido

    def suggest_priority_for_user_story(self, value_proposition, user_story_text, user_id=None):
        """
        Sugere prioridade para uma história de usuário usando o método MoSCoW.
        """
        user_prompt_content = PRIORITY_SUGGESTION_USER_PROMPT.format(
            value_proposition=value_proposition,
            user_story_text=user_story_text
        )
        
        generated_text = self._call_llm(
            PRIORITY_SUGGESTION_SYSTEM_PROMPT, 
            user_prompt_content,
            operation="suggest_priority_for_user_story",
            user_id=user_id
        )
        return generated_text
        if not isinstance(generated_text, str):
            logging_service.log_error("LLM retornou resposta não-string para sugestão de prioridade.", operation="suggest_priority_processing", user_id=user_id)
            return "medium" # Fallback
        
        try:
            parsed_data = json.loads(generated_text)
            if 'priority_analysis' in parsed_data and 'priority' in parsed_data['priority_analysis']:
                return parsed_data['priority_analysis']['priority']
            else:
                # <--- AJUSTADO: Usando logging_service.log_warning
                logging_service.log_warning(f"Formato JSON inesperado da LLM para prioridade: {generated_text[:500]}", operation="suggest_priority_json_parse", user_id=user_id)
                raise ValueError("Formato JSON inesperado da LLM.")
        except json.JSONDecodeError:
            # <--- AJUSTADO: Usando logging_service.log_warning
            logging_service.log_warning(f"LLM não retornou JSON válido para prioridade. Tentando parsear texto puro.", operation="suggest_priority_fallback", user_id=user_id)
            # Fallback: tenta extrair a prioridade do texto puro
            priority_words = ["must-have", "should-have", "could-have", "won't-have", "must", "should", "could", "won't"]
            for p_word in priority_words:
                if p_word in generated_text.lower():
                    return p_word.replace("-have", "") # Retorna 'must', 'should', etc.
            return "medium" # Fallback final
