
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
        self.model = os.getenv("GROQ_MODEL", 'llama-3.3-70b-versatile')

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
         # Fallback final
