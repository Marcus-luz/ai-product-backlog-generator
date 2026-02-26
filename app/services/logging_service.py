

import logging
import json
import os
import traceback # Importa para formatar tracebacks
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from functools import wraps

from app.extensions import db
from app.models.revision import Revision


class LogLevel(Enum):
    """Níveis de log customizados para o sistema"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    LLM_CALL = "LLM_CALL"
    USER_ACTION = "USER_ACTION"
    ARTIFACT_GENERATION = "ARTIFACT_GENERATION"
    SYSTEM_PERFORMANCE = "SYSTEM_PERFORMANCE"


class LogType(Enum):
    """Tipos específicos de eventos para categorização"""
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    LLM_ERROR = "llm_error"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_UPDATED = "artifact_updated"
    ARTIFACT_DELETED = "artifact_deleted"
    EPIC_GENERATED = "epic_generated"
    USER_STORY_GENERATED = "user_story_generated"
    REQUIREMENT_GENERATED = "requirement_generated"
    BACKLOG_UPDATED = "backlog_updated"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_METRIC = "performance_metric"


class LoggingService:
    """
    Serviço centralizado de logging para o sistema de geração de artefatos ágeis.
    Integrado com arquivos (system.log, llm_interactions.jsonl) e sistema de revisões (PostgreSQL).
    """
    
    _instance = None # Implementa o padrão Singleton
    _initialized = False # Flag para garantir que __init__ rode apenas uma vez

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggingService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if LoggingService._initialized: # Verifica se já foi inicializado
            return
        
        self.logger = self._setup_logger()
        self._setup_log_directory()
        LoggingService._initialized = True # Marca como inicializado
    
    def _setup_logger(self) -> logging.Logger:
        """Configura o sistema de logging do Python para arquivos."""
        logger = logging.getLogger('agile_artifacts_system')
        logger.setLevel(logging.DEBUG)
        
        if not logger.handlers: # Evita adicionar handlers múltiplos em recargas (em Flask reloader)
            # Formatter estruturado
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            # Handler para console
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # Handler para arquivo
            try:
                file_handler = logging.FileHandler('logs/system.log', encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                print(f"Aviso: Não foi possível criar arquivo de log system.log: {e}")
        
        return logger
    
    def _setup_log_directory(self):
        """Cria o diretório de logs se não existir"""
        os.makedirs('logs', exist_ok=True)
    
    def _create_log_entry(self, 
                          level: LogLevel, 
                          log_type: LogType, 
                          message: str, 
                          details: Optional[Dict[str, Any]] = None,
                          user_id: Optional[int] = None,
                          artifact_id: Optional[int] = None,
                          artifact_type: Optional[str] = None) -> Dict[str, Any]:
        """Cria uma entrada de log estruturada"""
        
        log_entry = {
            'timestamp': datetime.utcnow(), # Usar objeto datetime
            'level': level.value,
            'type': log_type.value,
            'message': message,
            'user_id': user_id,
            'artifact_id': artifact_id,
            'artifact_type': artifact_type,
            'details': details or {}
        }
        
        return log_entry
    
    # --- MÉTODO log_info ---
    def log_info(self, message: str, operation: str = "info", details: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None) -> None:
        """
        Registra mensagens informativas no sistema.
        """
        log_entry = self._create_log_entry(
            level=LogLevel.INFO,
            log_type=LogType.USER_ACTION if user_id else LogType.ARTIFACT_UPDATED, # Um tipo de log mais genérico, você pode refinar
            message=message,
            details=details,
            user_id=user_id
        )
        self._write_log(log_entry)
    # --- FIM DO MÉTODO log_info ---

    # --- MÉTODO log_warning ---
    def log_warning(self, message: str, operation: str = "warning", details: Optional[Dict[str, Any]] = None, user_id: Optional[int] = None) -> None:
        """
        Registra mensagens de aviso no sistema.
        """
        log_entry = self._create_log_entry(
            level=LogLevel.WARNING,
            log_type=LogType.ERROR_OCCURRED, # Pode ser um tipo mais específico de aviso se criado
            message=message,
            details=details,
            user_id=user_id
        )
        self._write_log(log_entry)
    # --- FIM DO MÉTODO log_warning ---


    def log_llm_interaction(self, 
                            operation: str,
                            model: str,
                            prompt_type: str,
                            input_data: Dict[str, Any],
                            response: Optional[str] = None,
                            error: Optional[str] = None,
                            execution_time: Optional[float] = None,
                            user_id: Optional[int] = None) -> None:
        """
        Registra interações com LLMs de forma detalhada, persistindo em arquivo JSONL.
        """
        
        details = {
            'operation': operation,
            'model': model,
            'prompt_type': prompt_type,
            'input_data': input_data,
            'execution_time_seconds': execution_time,
            'input_tokens_estimated': len(str(input_data)) // 4,
            'output_tokens_estimated': len(response or '') // 4 if response else 0
        }
        
        if error:
            log_type = LogType.LLM_ERROR
            level = LogLevel.ERROR
            message = f"Erro na operação LLM '{operation}': {error}"
            details['error'] = error
        else:
            log_type = LogType.LLM_RESPONSE if response else LogType.LLM_REQUEST
            level = LogLevel.LLM_CALL
            message = f"Operação LLM '{operation}' executada com sucesso"
            if response:
                details['response_preview'] = response[:200] + "..." if len(response) > 200 else response
                details['full_response'] = response # Armazenar a resposta completa aqui
        
        log_entry = self._create_log_entry(
            level=level,
            log_type=log_type,
            message=message,
            details=details,
            user_id=user_id
        )
        
        self._write_log(log_entry) # Escreve para o logger padrão (console/system.log)
        self._save_llm_log_to_file(log_entry) # Salva em arquivo JSONL separado

    def log_user_action(self, 
                        action: str, 
                        user_id: int,
                        details: Optional[Dict[str, Any]] = None,
                        artifact_id: Optional[int] = None,
                        artifact_type: Optional[str] = None) -> None:
        """Registra ações de usuários."""
        
        log_entry = self._create_log_entry(
            level=LogLevel.USER_ACTION,
            log_type=LogType.USER_LOGIN if 'login' in action.lower() else LogType.USER_LOGOUT if 'logout' in action.lower() else LogType.ARTIFACT_UPDATED, # Simplificado
            message=f"Usuário {user_id}: {action}",
            details=details,
            user_id=user_id,
            artifact_id=artifact_id,
            artifact_type=artifact_type
        )
        
        self._write_log(log_entry)
    
    def log_artifact_generation(self,
                                artifact_type: str,
                                artifact_id: int,
                                operation: str,
                                user_id: Optional[int] = None,
                                parent_artifact_id: Optional[int] = None,
                                generation_method: str = "llm",
                                details: Optional[Dict[str, Any]] = None) -> None:
        """Registra geração ou modificação de artefatos."""
        
        enhanced_details = details or {}
        enhanced_details.update({
            'generation_method': generation_method,
            'parent_artifact_id': parent_artifact_id,
            'operation': operation
        })
        
        log_type_map = {
            'created': LogType.ARTIFACT_CREATED,
            'updated': LogType.ARTIFACT_UPDATED,
            'deleted': LogType.ARTIFACT_DELETED
        }
        
        log_entry = self._create_log_entry(
            level=LogLevel.ARTIFACT_GENERATION,
            log_type=log_type_map.get(operation, LogType.ARTIFACT_UPDATED),
            message=f"{artifact_type.title()} {artifact_id} foi {operation}",
            details=enhanced_details,
            user_id=user_id,
            artifact_id=artifact_id,
            artifact_type=artifact_type
        )
        
        self._write_log(log_entry)
        
        # Cria entrada no sistema de revisões (PostgreSQL)
        if operation in ['created', 'updated'] and user_id is not None:
            self._create_revision_entry(artifact_id, artifact_type, operation, user_id, enhanced_details)
        
    def log_performance_metric(self,
                               metric_name: str,
                               value: float,
                               unit: str,
                               operation: Optional[str] = None,
                               user_id: Optional[int] = None) -> None:
        """Registra métricas de performance em arquivo de log padrão."""
        
        details = {
            'metric_name': metric_name,
            'value': value,
            'unit': unit,
            'operation': operation
        }
        
        log_entry = self._create_log_entry(
            level=LogLevel.SYSTEM_PERFORMANCE,
            log_type=LogType.PERFORMANCE_METRIC,
            message=f"Métrica {metric_name}: {value} {unit}",
            details=details,
            user_id=user_id
        )
        
        self._write_log(log_entry)

    def log_error(self,
                  error_message: str,
                  exception: Optional[Exception] = None,
                  user_id: Optional[int] = None,
                  operation: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None) -> None:
        """Registra erros do sistema em arquivo de log padrão."""
        
        enhanced_details = details or {}
        if exception:
            enhanced_details.update({
                'exception_type': type(exception).__name__,
                'exception_args': str(exception.args) if exception.args else None,
                'operation': operation,
                'traceback': self._format_traceback(exception) # Adiciona traceback
            })
        
        log_entry = self._create_log_entry(
            level=LogLevel.ERROR,
            log_type=LogType.ERROR_OCCURRED,
            message=error_message,
            details=enhanced_details,
            user_id=user_id
        )
        
        self._write_log(log_entry)
    
    # --- MÉTODO _format_traceback (PRESENTE) ---
    def _format_traceback(self, exc: Exception) -> str:
        """Formata o traceback de uma exceção como string."""
        return traceback.format_exc()
    # --- FIM DO MÉTODO _format_traceback ---

    def _write_log(self, log_entry: Dict[str, Any]) -> None:
        """Escreve entrada de log usando o logger do Python (para console e arquivo system.log)"""
        
        log_level_map = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
            LogLevel.LLM_CALL: logging.INFO, # Mapeia para INFO no logger geral
            LogLevel.USER_ACTION: logging.INFO,
            LogLevel.ARTIFACT_GENERATION: logging.INFO,
            LogLevel.SYSTEM_PERFORMANCE: logging.DEBUG
        }
        
        level = log_level_map.get(LogLevel(log_entry['level']), logging.INFO)
        
        # Mensagem estruturada para o log
        # Remove a chave 'timestamp' do details para não duplicar no json.dumps
        details_for_display = log_entry['details'].copy()
        details_for_display.pop('timestamp', None) 
        
        structured_message = f"[{log_entry['type']}] {log_entry['message']}"
        # Garante que objetos datetime e outros tipos não serializáveis sejam convertidos para string
        def json_serial(obj):
            if isinstance(obj, (datetime, Enum)):
                return str(obj)
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

        if details_for_display:
            structured_message += f" | Details: {json.dumps(details_for_display, ensure_ascii=False, default=json_serial)}"
        
        self.logger.log(level, structured_message)
    
    def _save_llm_log_to_file(self, log_entry: Dict[str, Any]) -> None:
        """Salva logs detalhados de LLM em arquivo JSON separado."""
        try:
            llm_log_file = os.path.join('logs', f"llm_interactions_{datetime.now().strftime('%Y-%m')}.jsonl")
            with open(llm_log_file, 'a', encoding='utf-8') as f:
                # Garante que objetos datetime e outros tipos não serializáveis sejam convertidos para string
                def json_serial(obj):
                    if isinstance(obj, (datetime, Enum)):
                        return str(obj)
                    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

                f.write(json.dumps(log_entry, ensure_ascii=False, default=json_serial) + '\n')
        except Exception as e:
            self.logger.error(f"Erro ao salvar log LLM em arquivo: {e}")
    
    def _create_revision_entry(self,
                               artifact_id: int,
                               artifact_type: str,
                               operation: str,
                               user_id: int,
                               details: Dict[str, Any]) -> None:
        """Cria entrada no sistema de revisões (PostgreSQL)."""
        try:
            # Garante que o content seja um JSON válido, convertendo datetimes/Enums
            def json_serial(obj):
                if isinstance(obj, (datetime, Enum)):
                    return str(obj)
                raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

            revision_content = json.dumps(details, ensure_ascii=False, default=json_serial)
            
            revision = Revision(
                artifact_id=artifact_id,
                artifact_type=artifact_type,
                content=revision_content,
                change_description=f"{operation.title()} via {details.get('generation_method', 'unknown')}",
                user_id=user_id
            )
            
            db.session.add(revision)
            db.session.commit()
            self.logger.info(f"Revisão criada para {artifact_type} {artifact_id} - Operação: {operation}")
            
        except Exception as e:
            self.logger.error(f"Erro ao criar revisão no PostgreSQL: {e}")
            db.session.rollback() # Rollback em caso de erro na revisão
    
    def get_logs_by_criteria(self,
                             user_id: Optional[int] = None,
                             artifact_type: Optional[str] = None,
                             log_type: Optional[LogType] = None,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None,
                             limit: int = 100) -> List[Dict[str, Any]]:
        """
        Recupera logs baseado em critérios específicos (atualmente, uma implementação stub).
        """
        self.logger.warning("get_logs_by_criteria é um stub e não recupera dados persistidos.")
        return []


def log_execution_time(operation_name: str):
    """Decorator para medir e logar tempo de execução de operações."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.utcnow()
            
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                logging_service.log_performance_metric( # Usa a instância global
                    metric_name="execution_time",
                    value=execution_time,
                    unit="seconds",
                    operation=operation_name
                )
                
                return result
                
            except Exception as e:
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                logging_service.log_error( # Usa a instância global
                    error_message=f"Erro em {operation_name}: {str(e)}",
                    exception=e,
                    operation=operation_name,
                    details={'execution_time_seconds': execution_time}
                )
                
                raise e # Re-lança a exceção para que ela continue sendo tratada no fluxo normal
                    
        return wrapper
    return decorator


# Instância global do serviço de logging (Singleton)
logging_service = LoggingService()