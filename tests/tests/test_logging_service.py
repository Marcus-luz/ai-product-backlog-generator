# tests/test_logging_service.py

import pytest
import os
import json
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch, MagicMock
from pathlib import Path
import logging

# Importa as classes e a instância global do serviço
from app.services.logging_service import (
    LoggingService,
    LogLevel,
    LogType,
    log_execution_time,
    logging_service as global_logging_service # Damos um apelido para a instância global
)

#region Fixtures
@pytest.fixture
def temp_log_dir():
    """Cria um diretório temporário para logs e o retorna como um objeto Path."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_db_session():
    """Mock para a sessão do banco de dados para evitar escritas reais no DB."""
    with patch('app.services.logging_service.db.session') as mock_session:
        yield mock_session
#endregion


class TestLoggingService:
    """Testes unitários para os métodos da classe LoggingService."""

    def test_singleton_pattern(self):
        """Testa se o padrão Singleton está funcionando (a mesma instância é sempre retornada)."""
        instance1 = LoggingService()
        instance2 = LoggingService()
        assert instance1 is instance2

    

    def test_log_llm_interaction_writes_to_files(self, temp_log_dir):
        """Testa se a interação com LLM é logada no system.log e no arquivo JSONL."""
        LoggingService._initialized = False
        # Para este teste, vamos mockar os métodos de escrita para não escrever em disco
        # e sim verificar os dados que seriam escritos.
        with patch.object(LoggingService, '_write_log') as mock_write_log, \
             patch.object(LoggingService, '_save_llm_log_to_file') as mock_save_llm:
            
            service = LoggingService()
            
            # Act
            service.log_llm_interaction(
                operation="test_op", model="test_model", prompt_type="test_prompt",
                input_data={"data": "test"}, response="test_response"
            )

            # Assert
            mock_write_log.assert_called_once()
            mock_save_llm.assert_called_once()
            # Verifica o conteúdo da chamada
            log_entry = mock_write_log.call_args[0][0]
            assert log_entry['level'] == LogLevel.LLM_CALL.value
            assert log_entry['type'] == LogType.LLM_RESPONSE.value
            assert log_entry['details']['operation'] == "test_op"


    def test_log_artifact_creates_revision(self, mock_db_session):
        """Testa se logar a geração de um artefato também chama a criação de uma revisão no DB."""
        with patch('app.services.logging_service.Revision') as mock_revision_class:
            # Arrange
            LoggingService._initialized = False
            service = LoggingService()
            # Mock para o método de escrita em log para isolar o teste
            service._write_log = MagicMock()

            # Act
            service.log_artifact_generation(
                artifact_type="epic", artifact_id=1, operation="created", user_id=1
            )

            # Assert
            mock_revision_class.assert_called_once()
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()


class TestLogExecutionTimeDecorator:
    """Testes para o decorator @log_execution_time."""

    # Usamos patch para substituir a *instância global* `logging_service` usada pelo decorator.
    # `autospec=True` garante que o mock tenha a mesma "assinatura" do objeto real.
    @patch('app.services.logging_service.logging_service', autospec=True)
    def test_decorator_logs_performance_on_success(self, mock_global_logging_service):
        """Testa se o decorator loga a performance em caso de sucesso."""
        # Arrange
        @log_execution_time("successful_operation")
        def sample_function():
            return "all good"
        
        # Act
        result = sample_function()
        
        # Assert
        assert result == "all good"
        mock_global_logging_service.log_performance_metric.assert_called_once()
        
        # Verifica os argumentos passados para o mock
        kwargs = mock_global_logging_service.log_performance_metric.call_args.kwargs
        assert kwargs['metric_name'] == "execution_time"
        assert kwargs['operation'] == "successful_operation"
        assert isinstance(kwargs['value'], float)

    @patch('app.services.logging_service.logging_service', autospec=True)
    def test_decorator_logs_error_on_exception(self, mock_global_logging_service):
        """Testa se o decorator loga o erro em caso de uma exceção."""
        # Arrange
        error_message = "it failed"
        @log_execution_time("failing_operation")
        def sample_function_that_fails():
            raise ValueError(error_message)
        
        # Act & Assert
        # Verifica se a exceção original ainda é levantada após o log
        with pytest.raises(ValueError, match=error_message):
            sample_function_that_fails()
        
        # Verifica se o método de log de ERRO foi chamado
        mock_global_logging_service.log_error.assert_called_once()
        kwargs = mock_global_logging_service.log_error.call_args.kwargs
        assert kwargs['operation'] == "failing_operation"
        assert error_message in kwargs['error_message']