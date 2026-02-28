
import pytest
import os
import json
from unittest.mock import patch, MagicMock
from types import SimpleNamespace

# Importa a classe que queremos testar
from app.services.llm_service import LLMService

#region Fixtures
@pytest.fixture
def mock_env_vars(monkeypatch):
    """Fixture to mock environment variables."""
    # Define uma chave de API falsa para que a inicialização do LLMService funcione
    monkeypatch.setenv("GROQ_API_KEY", "DUMMY_API_KEY_FOR_TESTING")
    # Define um modelo padrão para os testes
    monkeypatch.setenv("GROQ_MODEL", "test-model-llama3")

@pytest.fixture
def mock_product():
    """Fixture to create a mock product object for testing."""
    product = SimpleNamespace() # SimpleNamespace é uma forma fácil de criar objetos genéricos
    product.name = "Plataforma de E-commerce"
    product.description = "Uma nova plataforma para vender produtos online."
    product.personas = "Vendedores e Compradores"
    product.value_proposition = "Facilitar o comércio eletrônico para pequenas empresas."
    product.channels_platforms = "Web e Mobile"
    return product

@pytest.fixture
def llm_service(mock_env_vars):
    """Creates an instance of LLMService with mocked environment variables."""
    # O patch aqui garante que não tentaremos nos conectar ao logging_service real
    with patch('app.services.llm_service.logging_service', MagicMock()):
        service = LLMService()
        yield service
#endregion


class TestLLMService:
    """Unit tests for the LLMService."""

    def test_initialization_success(self, mock_env_vars):
        """Tests if the service initializes correctly when the API key is present."""
        service = LLMService()
        assert service.client is not None
        assert service.model == "test-model-llama3"

    def test_initialization_no_api_key(self, monkeypatch):
        """Tests that the service raises a ValueError if the API key is missing."""
        monkeypatch.delenv("GROQ_API_KEY", raising=False) # Garante que a variável não exista
        
        with pytest.raises(ValueError, match="A variável de ambiente GROQ_API_KEY não foi definida."):
            LLMService()
            
    @patch('app.services.llm_service.LLMService._call_llm')
    def test_generate_epics_with_custom_prompt(self, mock_call_llm, llm_service, mock_product):
        """
        Tests that a custom prompt instruction is correctly appended to the user prompt.
        """
        # Arrange
        custom_instruction = "Focar em épicos para o primeiro MVP."
        mock_call_llm.return_value = "[]" # A resposta não importa para este teste

        # Act
        llm_service.generate_epics_for_product(mock_product, custom_prompt_instruction=custom_instruction)

        # Assert
        mock_call_llm.assert_called_once()
        # Pega os argumentos com os quais _call_llm foi chamado
        args, kwargs = mock_call_llm.call_args
        # O user_prompt é o segundo argumento posicional (índice 1)
        user_prompt_sent_to_llm = args[1]
        
        assert custom_instruction in user_prompt_sent_to_llm

    # Este é um teste mais avançado que simula uma falha na API
    # Usamos o patch no cliente real da Groq dentro do serviço
    @patch('app.services.llm_service.Groq')
    @patch('app.services.llm_service.logging_service')
    def test_call_llm_handles_api_exception(self, mock_logging, mock_groq, mock_env_vars, mock_product):
        """
        Tests that _call_llm correctly logs an error and re-raises the exception when the API call fails.
        """
        # Arrange: Configura o mock do cliente para levantar um erro quando for usado
        error_message = "API connection failed"
        # O método que faz a chamada real é o 'create', então o mockamos para levantar um erro
        mock_groq.return_value.chat.completions.create.side_effect = Exception(error_message)
        
        service = LLMService()

        # Act & Assert: Verifica se a exceção é levantada e se o erro foi logado
        with pytest.raises(Exception, match=error_message):
            service.generate_epics_for_product(mock_product)
        
        # Verifica se o nosso logging_service foi chamado para registrar o erro
        mock_logging.log_llm_interaction.assert_called_once()
        # Pega os argumentos da chamada de log
        log_args, log_kwargs = mock_logging.log_llm_interaction.call_args
        assert log_kwargs['error'] == error_message