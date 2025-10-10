"""
Sistema de excepciones personalizado para el simulador ABP.

Este módulo define una jerarquía de excepciones específicas para el simulador,
permitiendo un manejo de errores más granular y consistente.
"""

from typing import Any, Optional


class SimulatorException(Exception):
    """
    Excepción base para todas las excepciones del simulador ABP.
    
    Proporciona funcionalidad común para todas las excepciones específicas,
    incluyendo información contextual y campos adicionales.
    """
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None, 
        value: Optional[Any] = None,
        context: Optional[dict] = None
    ):
        """
        Inicializa la excepción.
        
        Args:
            message: Mensaje descriptivo del error
            field: Campo que causó el error (opcional)
            value: Valor que causó el error (opcional)
            context: Información contextual adicional (opcional)
        """
        super().__init__(message)
        self.message = message
        self.field = field
        self.value = value
        self.context = context or {}
    
    def __str__(self) -> str:
        """Representación textual de la excepción."""
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
    Excepción para errores de configuración.
    
    Se lanza cuando hay problemas con la configuración del simulador,
    parámetros inválidos o configuraciones incompletas.
    """
    pass


class ValidationError(SimulatorException):
    """
    Excepción para errores de validación de datos.
    
    Se lanza cuando los datos de entrada no cumplen con las reglas
    de validación establecidas.
    """
    pass


class ReaderError(SimulatorException):
    """
    Excepción para errores en la lectura de archivos de proyecto.
    
    Se lanza cuando hay problemas al cargar o procesar archivos
    de proyecto (MPP, XML, etc.).
    """
    pass


class SimulationError(SimulatorException):
    """
    Excepción para errores durante la simulación.
    
    Se lanza cuando ocurren problemas durante la ejecución
    de la simulación que no pueden ser recuperados.
    """
    pass


class TaskError(SimulatorException):
    """
    Excepción específica para errores relacionados con tareas.
    
    Se lanza cuando hay problemas con la creación, modificación
    o procesamiento de tareas.
    """
    pass


class ResourceError(SimulatorException):
    """
    Excepción específica para errores relacionados con recursos.
    
    Se lanza cuando hay problemas con la gestión de recursos,
    asignaciones o disponibilidad.
    """
    pass


class TeamError(SimulatorException):
    """
    Excepción específica para errores relacionados con equipos.
    
    Se lanza cuando hay problemas con la gestión de equipos,
    dinámicas sociales o asignaciones de equipo.
    """
    pass


class StrategyError(SimulatorException):
    """
    Excepción para errores en estrategias de asignación.
    
    Se lanza cuando hay problemas con la ejecución de estrategias
    de asignación de tareas.
    """
    pass


class MetricsError(SimulatorException):
    """
    Excepción para errores en el cálculo de métricas.
    
    Se lanza cuando hay problemas al calcular métricas del proyecto
    o cuando los datos necesarios no están disponibles.
    """
    pass


class DependencyError(SimulatorException):
    """
    Excepción para errores relacionados con dependencias.
    
    Se lanza cuando hay problemas con las dependencias entre tareas,
    como dependencias cíclicas o dependencias inválidas.
    """
    pass


class PluginError(SimulatorException):
    """
    Excepción para errores relacionados con plugins.
    
    Se lanza cuando hay problemas con la carga, inicialización
    o ejecución de plugins.
    """
    pass


class OutputError(SimulatorException):
    """
    Excepción para errores en la generación de salidas.
    
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
    
    # Mapeo de excepciones comunes a excepciones específicas
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
            f"Valor inválido: {exc}",
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
            f"{field_name} debe ser un número",
            field=field_name,
            value=value
        )
    
    if value < 0:
        raise ValidationError(
            f"{field_name} debe ser un número positivo",
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
            f"{field_name} no puede estar vacío",
            field=field_name,
            value=value
        )