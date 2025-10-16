"""
-----------------------------------------------------------------
PyProjectManagementSim 1.0
Modelo computacional de gestión de proyectos en Python.
Autores: Manuel Castañón–Puga, Fernando Rosales Quiñones
Correo electrónico: {puga, fernando.rosales59}@uabc.edu.mx
Universidad Autónoma de Baja California
http://www.uabc.edu.mx
PyProjectManagementSim/core/config/logging_config.py
-----------------------------------------------------------------

"""

"""
Professional logging system for the ABP simulator.

This module provides centralized logging configuration
with different levels per module and structured logs.
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
    jSon Formatte
    
    Useful for automated analysis and integration with monitoring systems.
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
        
        # Add exception information if it exists
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add additional context fields
        if hasattr(record, 'context'):
            log_data['context'] = record.context
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """
    Formateador con colores para terminal.
    
    Mejora la legibilidad de los logs en desarrollo.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
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
        # Apply color according to level
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Create base message
        message = super().format(record)
        
        # Apply color only if we are in terminal
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
    Configures the logging system of the simulator.
    
    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Archivo donde guardar los logs (opcional)
        structured: Si usar formato JSON estructurado
        colored: Si usar colores en terminal
    """
    
    # Base configuration
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
    
    # Configure handlers
    handlers = []
    
    # Console handler
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
    
    # File handler if specified
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
    
    # Assign handlers to loggers
    for logger_name in config['loggers']:
        config['loggers'][logger_name]['handlers'] = handlers.copy()
    
    config['root']['handlers'] = handlers.copy()
    
    # Apply configuration
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    Gets a configured logger for the specified module.

    Args:
        name: Name of the module (usually __name__)
        
    Returns:
        Configured logger
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
    Logs a message with additional context.
    
    Args:
        logger: Logger to use
        level: Level of logging
        message: Message to log
        context: Additional context
        **kwargs: Additional context fields
    """

    if context is None:
        context = {}
    
    # Combine context with kwargs
    full_context = {**context, **kwargs}
    
    # Create record with context
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

    Logs performance metrics for an operation.

    Args:
        logger: Logger to use
        operation: Name of the operation
        duration: Duration in seconds
        **metrics: Additional metrics
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

    Logs information about a simulation step.
    Args:
        logger: Logger to use
        step: Number of the step
        completion: Completion percentage
        active_agents: Number of active agents
        **metrics: Additional metrics
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
    Logs the assignment of a task.
    Args:
        logger: Logger to use
        task_id: ID of the task
        resource_id: ID of the resource
        strategy: Strategy used
        **context: Additional context
    """

    log_with_context(
        logger,
        logging.INFO,
        f"Task {task_id} assigned to resource {resource_id}",
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
    Logs an error with detailed context.
    Args:
        logger: Logger to use
        message: Error message
        exception: Associated exception (optional)
        **context: Additional context
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


# Default configuration
def setup_default_logging() -> None:
    """
    Configures the logging with default values appropriate for development.
    """
    setup_logging(
        level="INFO",
        structured=False,
        colored=True
    )


# Production configuration
def setup_production_logging(log_file: str) -> None:
    """
    Configures the logging for production.
    
    Args:
        log_file: File where to save the logs
    """
    setup_logging(
        level="WARNING",
        log_file=log_file,
        structured=True,
        colored=False
    )


# Debugging configuration
def setup_debug_logging(log_file: Optional[str] = None) -> None:
    """
    Configures the logging for detailed debugging.
    
    Args:
        log_file: File where to save the logs (optional)
    """
    setup_logging(
        level="DEBUG",
        log_file=log_file,
        structured=False,
        colored=True
    )