"""
Sistema de logging profesional para el simulador ABP.

Este módulo proporciona configuración centralizada de logging
con diferentes niveles por módulo y logs estructurados.
"""

import logging
import logging.config
import sys
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import json


class StructuredFormatter(logging.Formatter):
    """
    Formateador que produce logs estructurados en formato JSON.
    
    Útil para análisis automatizado y integración con sistemas de monitoreo.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formatea el registro de log como JSON estructurado.
        
        Args:
            record: Registro de log a formatear
            
        Returns:
            Cadena JSON con la información del log
        """
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Agregar información de excepción si existe
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Agregar campos adicionales del contexto
        if hasattr(record, 'context'):
            log_data['context'] = record.context
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """
    Formateador con colores para terminal.
    
    Mejora la legibilidad de los logs en desarrollo.
    """
    
    # Códigos de color ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Amarillo
        'ERROR': '\033[31m',      # Rojo
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formatea el registro con colores.
        
        Args:
            record: Registro de log a formatear
            
        Returns:
            Cadena formateada con colores
        """
        # Aplicar color según el nivel
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Crear el mensaje base
        message = super().format(record)
        
        # Aplicar color solo si estamos en terminal
        if sys.stdout.isatty():
            return f"{color}{message}{reset}"
        else:
            return message


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    structured: bool = False,
    colored: bool = True
) -> None:
    """
    Configura el sistema de logging del simulador.
    
    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Archivo donde guardar los logs (opcional)
        structured: Si usar formato JSON estructurado
        colored: Si usar colores en terminal
    """
    
    # Configuración base
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            }
        },
        'handlers': {},
        'loggers': {
            'core': {
                'level': level,
                'handlers': [],
                'propagate': False
            },
            'core.entities': {
                'level': 'DEBUG' if level == 'DEBUG' else 'INFO',
                'handlers': [],
                'propagate': False
            },
            'core.simulation': {
                'level': 'DEBUG' if level == 'DEBUG' else 'INFO',
                'handlers': [],
                'propagate': False
            },
            'core.readers': {
                'level': 'DEBUG' if level == 'DEBUG' else 'INFO',
                'handlers': [],
                'propagate': False
            }
        },
        'root': {
            'level': level,
            'handlers': []
        }
    }
    
    # Configurar handlers
    handlers = []
    
    # Handler para consola
    console_handler = 'console'
    if structured:
        config['formatters']['structured'] = {
            '()': StructuredFormatter
        }
        config['handlers'][console_handler] = {
            'class': 'logging.StreamHandler',
            'level': level,
            'formatter': 'structured',
            'stream': 'ext://sys.stdout'
        }
    elif colored:
        config['formatters']['colored'] = {
            '()': ColoredFormatter,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
        config['handlers'][console_handler] = {
            'class': 'logging.StreamHandler',
            'level': level,
            'formatter': 'colored',
            'stream': 'ext://sys.stdout'
        }
    else:
        config['handlers'][console_handler] = {
            'class': 'logging.StreamHandler',
            'level': level,
            'formatter': 'detailed',
            'stream': 'ext://sys.stdout'
        }
    
    handlers.append(console_handler)
    
    # Handler para archivo si se especifica
    if log_file:
        file_handler = 'file'
        config['handlers'][file_handler] = {
            'class': 'logging.FileHandler',
            'level': level,
            'formatter': 'detailed',
            'filename': log_file,
            'mode': 'a',
            'encoding': 'utf-8'
        }
        handlers.append(file_handler)
    
    # Asignar handlers a loggers
    for logger_name in config['loggers']:
        config['loggers'][logger_name]['handlers'] = handlers.copy()
    
    config['root']['handlers'] = handlers.copy()
    
    # Aplicar configuración
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para el módulo especificado.
    
    Args:
        name: Nombre del módulo (usualmente __name__)
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """
    Registra un mensaje con contexto adicional.
    
    Args:
        logger: Logger a usar
        level: Nivel de logging
        message: Mensaje a registrar
        context: Contexto adicional
        **kwargs: Campos adicionales del contexto
    """
    if context is None:
        context = {}
    
    # Combinar contexto con kwargs
    full_context = {**context, **kwargs}
    
    # Crear registro con contexto
    record = logger.makeRecord(
        logger.name, level, "", 0, message, (), None
    )
    record.context = full_context
    
    logger.handle(record)


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration: float,
    **metrics
) -> None:
    """
    Registra métricas de rendimiento de una operación.
    
    Args:
        logger: Logger a usar
        operation: Nombre de la operación
        duration: Duración en segundos
        **metrics: Métricas adicionales
    """
    log_with_context(
        logger,
        logging.INFO,
        f"Operación completada: {operation}",
        context={
            'operation': operation,
            'duration_seconds': duration,
            'performance_metrics': metrics
        }
    )


def log_simulation_step(
    logger: logging.Logger,
    step: int,
    completion: float,
    active_agents: int,
    **metrics
) -> None:
    """
    Registra información de un paso de simulación.
    
    Args:
        logger: Logger a usar
        step: Número del paso
        completion: Porcentaje de completitud
        active_agents: Número de agentes activos
        **metrics: Métricas adicionales
    """
    log_with_context(
        logger,
        logging.DEBUG,
        f"Paso de simulación {step}",
        context={
            'simulation_step': step,
            'completion_percentage': completion,
            'active_agents': active_agents,
            'step_metrics': metrics
        }
    )


def log_task_assignment(
    logger: logging.Logger,
    task_id: int,
    resource_id: int,
    strategy: str,
    **context
) -> None:
    """
    Registra la asignación de una tarea.
    
    Args:
        logger: Logger a usar
        task_id: ID de la tarea
        resource_id: ID del recurso
        strategy: Estrategia usada
        **context: Contexto adicional
    """
    log_with_context(
        logger,
        logging.INFO,
        f"Tarea {task_id} asignada a recurso {resource_id}",
        context={
            'task_id': task_id,
            'resource_id': resource_id,
            'assignment_strategy': strategy,
            **context
        }
    )


def log_error_with_context(
    logger: logging.Logger,
    message: str,
    exception: Optional[Exception] = None,
    **context
) -> None:
    """
    Registra un error con contexto detallado.
    
    Args:
        logger: Logger a usar
        message: Mensaje de error
        exception: Excepción asociada (opcional)
        **context: Contexto adicional
    """
    log_with_context(
        logger,
        logging.ERROR,
        message,
        context={
            'error_context': context,
            'exception_type': type(exception).__name__ if exception else None,
            'exception_message': str(exception) if exception else None
        }
    )


# Configuración por defecto
def setup_default_logging() -> None:
    """
    Configura el logging con valores por defecto apropiados para desarrollo.
    """
    setup_logging(
        level="INFO",
        structured=False,
        colored=True
    )


# Configuración para producción
def setup_production_logging(log_file: str) -> None:
    """
    Configura el logging para producción.
    
    Args:
        log_file: Archivo donde guardar los logs
    """
    setup_logging(
        level="WARNING",
        log_file=log_file,
        structured=True,
        colored=False
    )


# Configuración para debugging
def setup_debug_logging(log_file: Optional[str] = None) -> None:
    """
    Configura el logging para debugging detallado.
    
    Args:
        log_file: Archivo donde guardar los logs (opcional)
    """
    setup_logging(
        level="DEBUG",
        log_file=log_file,
        structured=False,
        colored=True
    )