"""
-----------------------------------------------------------------
PyProjectManagementSim 1.0
Modelo computacional de gestión de proyectos en Python.
Autores: Manuel Castañón–Puga, Fernando Rosales Quiñones
Correo electrónico: {puga, fernando.rosales59}@uabc.edu.mx
Universidad Autónoma de Baja California
http://www.uabc.edu.mx
PyProjectManagementSim/core/exceptions.py
-----------------------------------------------------------------
"""

"""
Custom exception system for the PyProjectManagementSim simulator.

This module defines a hierarchy of specific exceptions for the simulator,
allowing for more granular and consistent error handling.
"""

from typing import Any, Optional


class SimulatorException(Exception):
    """
    Base exception for all PyProjectManagementSim simulator exceptions.
    
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
            parts.append(f"Field: {self.field}")
        
        if self.value is not None:
            parts.append(f"Value: {self.value}")
        
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Context: {context_str}")
        
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
    
    Raised when there are problems loading or processing project
    files (MPP, XML, etc.).
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
    
    Raised when there are problems saving results,
    generating reports or exporting data.
    """
    pass


# Utility functions for exception handling
def handle_exception(exc: Exception, context: Optional[dict] = None) -> SimulatorException:
    """
    Convert a generic exception into a simulator exception.
    
    Args:
        exc: Original exception
        context: Additional context
        
    Returns:
        Appropriate simulator exception
    """
    if isinstance(exc, SimulatorException):
        return exc
    
    # Mapping of common exceptions to specific exceptions
    if isinstance(exc, FileNotFoundError):
        return ReaderError(
            f"File not found: {exc}",
            context=context
        )
    elif isinstance(exc, PermissionError):
        return ReaderError(
            f"No permissions to access the file: {exc}",
            context=context
        )
    elif isinstance(exc, ValueError):
        return ValidationError(
            f"Invalid value: {exc}",
            context=context
        )
    elif isinstance(exc, KeyError):
        return ConfigurationError(
            f"Required key not found: {exc}",
            context=context
        )
    else:
        return SimulatorException(
            f"Unexpected error: {exc}",
            context=context
        )


def validate_not_none(value: Any, field_name: str) -> None:
    """
    Validate that a value is not None.
    
    Args:
        value: Value to validate
        field_name: Field name for the error message
        
    Raises:
        ValidationError: If the value is None
    """
    if value is None:
        raise ValidationError(
            f"{field_name} cannot be None",
            field=field_name,
            value=value
        )


def validate_positive_number(value: Any, field_name: str) -> None:
    """
    Validate that a value is a positive number.
    
    Args:
        value: Value to validate
        field_name: Field name for the error message
        
    Raises:
        ValidationError: If the value is not a positive number
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"{field_name} must be a positive number",
            field=field_name,
            value=value
        )
    
    if value < 0:
        raise ValidationError(
            f"{field_name} must be a number",
            field=field_name,
            value=value
        )


def validate_non_empty_string(value: Any, field_name: str) -> None:
    """
    Validate that a value is a non-empty string.
    
    Args:
        value: Value to validate
        field_name: Field name for the error message
        
    Raises:
        ValidationError: If the value is not a non-empty string
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"{field_name} must be a non-empty string",
            field=field_name,
            value=value
        )
    
    if not value.strip():
        raise ValidationError(
            f"{field_name} cannot be empty",
            field=field_name,
            value=value
        )