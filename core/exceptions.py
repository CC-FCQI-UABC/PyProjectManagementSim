"""
Custom exception system for the ABP simulator.

This module defines a hierarchy of specific exceptions for the simulator,
allowing for more granular and consistent error handling.
"""

from typing import Any, Optional


class SimulatorException(Exception):
    """
    Base exception for all ABP simulator exceptions.
    
    Provides common functionality for all specific exceptions,
    including contextual information and additional fields.
    """
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None, 
        value: Optional[Any] = None,
        context: Optional[dict] = None
    ):
        """
        Initializes the exception.
        
        Args:
            message: Descriptive error message
            field: Field that caused the error (optional)
            value: Value that caused the error (optional)
            context: Additional contextual information (optional)
        """
        super().__init__(message)
        self.message = message
        self.field = field
        self.value = value
        self.context = context or {}
    
    def __str__(self) -> str:
        """Textual representation of the exception."""
        parts = [self.message]
        
        if self.field:
            parts.append(f"Campo: {self.field}")
        
        if self.value is not None:
            parts.append(f"Valor: {self.value}")
        
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Contexto: {context_str}")
        
        return " | ".join(parts)


class ConfigurationError(SimulatorException):
    """
    Exception for configuration errors.
    
    Raised when there are problems with simulator configuration,
    invalid parameters or incomplete configurations.
    """
    pass


class ValidationError(SimulatorException):
    """
    Exception for data validation errors.
    
    Raised when input data does not meet the established
    validation rules.
    """
    pass


class ReaderError(SimulatorException):
    """
    Exception for project file reading errors.
    
    Se lanza cuando hay problemas al cargar o procesar archivos
    de proyecto (MPP, XML, etc.).
    """
    pass


class SimulationError(SimulatorException):
    """
    Exception for simulation errors.
    
    Raised when problems occur during simulation execution
    that cannot be recovered.
    """
    pass


class TaskError(SimulatorException):
    """
    Specific exception for task-related errors.
    
    Raised when there are problems with task creation, modification
    or task processing.
    """
    pass


class ResourceError(SimulatorException):
    """
    Specific exception for resource-related errors.
    
    Raised when there are problems with resource management,
    assignments or availability.
    """
    pass


class TeamError(SimulatorException):
    """
    Specific exception for team-related errors.
    
    Raised when there are problems with team management,
    social dynamics or team assignments.
    """
    pass


class StrategyError(SimulatorException):
    """
    Exception for assignment strategy errors.
    
    Raised when there are problems with strategy execution
    for task assignment.
    """
    pass


class MetricsError(SimulatorException):
    """
    Exception for metric calculation errors.
    
    Raised when there are problems calculating project metrics
    or when necessary data is not available.
    """
    pass


class DependencyError(SimulatorException):
    """
    Exception for dependency-related errors.
    
    Raised when there are problems with task dependencies,
    such as cyclic dependencies or invalid dependencies.
    """
    pass


class PluginError(SimulatorException):
    """
    Exception for plugin-related errors.
    
    Raised when there are problems with plugin loading, initialization
    or plugin execution.
    """
    pass


class OutputError(SimulatorException):
    """
    Exception for output generation errors.
    
    Se lanza cuando hay problemas al guardar resultados,
    generar reportes o exportar datos.
    """
    pass


# Funciones de utilidad para manejo de excepciones
def handle_exception(exc: Exception, context: Optional[dict] = None) -> SimulatorException:
    """
    Convierte una excepción genérica en una excepción del simulador.
    
    Args:
        exc: Excepción original
        context: Contexto adicional
        
    Returns:
        Excepción del simulador apropiada
    """
    if isinstance(exc, SimulatorException):
        return exc
    
    # Mapping of common exceptions to specific exceptions
    if isinstance(exc, FileNotFoundError):
        return ReaderError(
            f"Archivo no encontrado: {exc}",
            context=context
        )
    elif isinstance(exc, PermissionError):
        return ReaderError(
            f"Sin permisos para acceder al archivo: {exc}",
            context=context
        )
    elif isinstance(exc, ValueError):
        return ValidationError(
            f"Invalid value: {exc}",
            context=context
        )
    elif isinstance(exc, KeyError):
        return ConfigurationError(
            f"Clave requerida no encontrada: {exc}",
            context=context
        )
    else:
        return SimulatorException(
            f"Error inesperado: {exc}",
            context=context
        )


def validate_not_none(value: Any, field_name: str) -> None:
    """
    Valida que un valor no sea None.
    
    Args:
        value: Valor a validar
        field_name: Nombre del campo para el mensaje de error
        
    Raises:
        ValidationError: Si el valor es None
    """
    if value is None:
        raise ValidationError(
            f"{field_name} no puede ser None",
            field=field_name,
            value=value
        )


def validate_positive_number(value: Any, field_name: str) -> None:
    """
    Valida que un valor sea un número positivo.
    
    Args:
        value: Valor a validar
        field_name: Nombre del campo para el mensaje de error
        
    Raises:
        ValidationError: Si el valor no es un número positivo
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"{field_name} must be a number",
            field=field_name,
            value=value
        )
    
    if value < 0:
        raise ValidationError(
            f"{field_name} must be a positive number",
            field=field_name,
            value=value
        )


def validate_non_empty_string(value: Any, field_name: str) -> None:
    """
    Valida que un valor sea una cadena no vacía.
    
    Args:
        value: Valor a validar
        field_name: Nombre del campo para el mensaje de error
        
    Raises:
        ValidationError: Si el valor no es una cadena no vacía
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"{field_name} debe ser una cadena",
            field=field_name,
            value=value
        )
    
    if not value.strip():
        raise ValidationError(
            f"{field_name} cannot be empty",
            field=field_name,
            value=value
        )