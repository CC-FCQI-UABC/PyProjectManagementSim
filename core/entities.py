"""
Entidades principales del simulador ABP.

Este módulo contiene las clases fundamentales del simulador:
Task, Resource y Team, refactorizadas siguiendo principios SOLID
con validaciones robustas, properties y documentación completa.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

from core.exceptions import TaskError, ResourceError, TeamError, ValidationError
from core.config.logging_config import get_logger

# Importar Resource y Team desde entities_extended
from core.entities_extended import Resource, Team

logger = get_logger(__name__)


class TaskStatus(Enum):
    """Estados posibles de una tarea."""
    TO_DO = "to-do"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Prioridades de tarea."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TaskMetrics:
    """Metrics associated with a task."""
    planned_duration: float
    planned_cost: float
    actual_duration: float = 0.0
    actual_cost: float = 0.0
    efficiency: float = 1.0
    
    @property
    def duration_variance(self) -> float:
        """Variance in duration (positive = delay)."""
        return self.actual_duration - self.planned_duration
    
    @property
    def cost_variance(self) -> float:
        """Varianza en el costo (positiva = sobrecosto)."""
        return self.actual_cost - self.planned_cost
    
    @property
    def schedule_performance_index(self) -> float:
        """Índice de rendimiento del cronograma."""
        if self.actual_duration == 0:
            return 1.0
        return self.planned_duration / self.actual_duration
    
    @property
    def cost_performance_index(self) -> float:
        """Índice de rendimiento del costo."""
        if self.actual_cost == 0:
            return 1.0
        return self.planned_cost / self.actual_cost


class Task:
    """
    Representa una tarea en el proyecto.
    
    Una tarea es la unidad básica de trabajo en el simulador,
    con propiedades como duración, costo, dependencias y estado.
    
    Attributes:
        id: Identificador único de la tarea
        name: Nombre descriptivo de la tarea
        duration: Duración estimada en horas
        estimated_cost: Costo estimado de la tarea
        status: Estado actual de la tarea
        progress: Progreso actual (0.0 a 1.0)
        priority: Prioridad de la tarea
        metrics: Métricas de rendimiento de la tarea
        dependencies: Lista de tareas de las que depende
        assigned_resource: Recurso asignado a la tarea
        required_resource_id: ID del recurso requerido
        assigned_team: Equipo asignado a la tarea
        tags: Etiquetas para categorización
        metadata: Información adicional personalizada
    """
    
    def __init__(
        self,
        task_id: int,
        name: str,
        duration: float,
        estimated_cost: float,
        priority: TaskPriority = TaskPriority.MEDIUM,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa una nueva tarea.
        
        Args:
            task_id: Identificador único de la tarea
            name: Nombre descriptivo de la tarea
            duration: Duración estimada en horas (debe ser > 0)
            estimated_cost: Costo estimado (debe ser >= 0)
            priority: Prioridad de la tarea
            tags: Lista de etiquetas para categorización
            metadata: Información adicional personalizada
            
        Raises:
            ValidationError: Si los parámetros no son válidos
        """
        self._validate_constructor_params(task_id, name, duration, estimated_cost)
        
        self._id = task_id
        self._name = name
        self._duration = max(0.0, duration)
        self._real_duration = 0.0  # Real accumulated duration
        self._estimated_cost = max(0.0, estimated_cost)
        self._status = TaskStatus.TO_DO
        self._progress = 0.0
        self._priority = priority
        self._tags = tags or []
        self._metadata = metadata or {}
        
        # Relaciones
        self._dependencies: List[Task] = []
        self._assigned_resource: Optional[Resource] = None
        self._required_resource_id: Optional[int] = None
        self._assigned_team: Optional[Team] = None
        
        # Metrics
        self._metrics = TaskMetrics(
            planned_duration=self._duration,
            planned_cost=self._estimated_cost
        )
        
        logger.debug(f"Tarea creada: {self}")
    
    def _validate_constructor_params(
        self, 
        task_id: int, 
        name: str, 
        duration: float, 
        estimated_cost: float
    ) -> None:
        """Validate constructor parameters."""
        if not isinstance(task_id, int) or task_id <= 0:
            raise ValidationError(
                f"task_id debe ser un entero positivo, recibido: {task_id}",
                field="task_id",
                value=task_id
            )
        
        if not isinstance(name, str) or not name.strip():
            raise ValidationError(
                f"name must be a non-empty string, received: '{name}'",
                field="name",
                value=name
            )
        
        if not isinstance(duration, (int, float)) or duration < 0:
            raise ValidationError(
                f"duration must be a number >= 0, received: {duration}",
                field="duration",
                value=duration
            )
        
        if not isinstance(estimated_cost, (int, float)) or estimated_cost < 0:
            raise ValidationError(
                f"estimated_cost must be a number >= 0, received: {estimated_cost}",
                field="estimated_cost",
                value=estimated_cost
            )
    
    # Properties
    @property
    def id(self) -> int:
        """Unique task ID."""
        return self._id
    
    @property
    def name(self) -> str:
        """Nombre de la tarea."""
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        """Establece el nombre de la tarea."""
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(
                f"name debe ser una cadena no vacía, recibido: '{value}'",
                field="name",
                value=value
            )
        self._name = value
    
    @property
    def duration(self) -> float:
        """Estimated duration in hours."""
        return self._duration
    
    @duration.setter
    def duration(self, value: float) -> None:
        """Establece la duración estimada."""
        if not isinstance(value, (int, float)) or value < 0:
            raise ValidationError(
                f"duration debe ser un número >= 0, recibido: {value}",
                field="duration",
                value=value
            )
        self._duration = value
        self._metrics.planned_duration = value
    
    @property
    def real_duration(self) -> float:
        """Duración real acumulada en horas."""
        return self._real_duration
    
    @real_duration.setter
    def real_duration(self, value: float) -> None:
        """Establece la duración real acumulada."""
        if not isinstance(value, (int, float)) or value < 0:
            raise ValidationError(
                f"real_duration debe ser un número >= 0, recibido: {value}",
                field="real_duration",
                value=value
            )
        self._real_duration = value
    
    @property
    def estimated_cost(self) -> float:
        """Costo estimado de la tarea."""
        return self._estimated_cost
    
    @estimated_cost.setter
    def estimated_cost(self, value: float) -> None:
        """Establece el costo estimado."""
        if not isinstance(value, (int, float)) or value < 0:
            raise ValidationError(
                f"estimated_cost debe ser un número >= 0, recibido: {value}",
                field="estimated_cost",
                value=value
            )
        self._estimated_cost = value
        self._metrics.planned_cost = value
    
    @property
    def status(self) -> TaskStatus:
        """Estado actual de la tarea."""
        return self._status
    
    @status.setter
    def status(self, value: TaskStatus) -> None:
        """Establece el estado de la tarea."""
        self._status = value
    
    @property
    def progress(self) -> float:
        """Progreso actual (0.0 a 1.0)."""
        return self._progress
    
    @property
    def priority(self) -> TaskPriority:
        """Prioridad de la tarea."""
        return self._priority
    
    @priority.setter
    def priority(self, value: TaskPriority) -> None:
        """Establece la prioridad de la tarea."""
        if not isinstance(value, TaskPriority):
            raise ValidationError(
                f"priority debe ser una instancia de TaskPriority, recibido: {type(value)}",
                field="priority",
                value=value
            )
        self._priority = value
    
    @property
    def dependencies(self) -> List[Task]:
        """Lista de tareas de las que depende."""
        return self._dependencies.copy()
    
    @dependencies.setter
    def dependencies(self, value: List[Task]) -> None:
        """Establece las dependencias de la tarea."""
        if not isinstance(value, list):
            raise TypeError("dependencies debe ser una lista de Task")
        self._dependencies = value.copy()
    
    @property
    def assigned_resource(self) -> Optional[Resource]:
        """Recurso asignado a la tarea."""
        return self._assigned_resource
    
    @property
    def required_resource_id(self) -> Optional[int]:
        """ID del recurso requerido."""
        return self._required_resource_id
    
    @required_resource_id.setter
    def required_resource_id(self, value: Optional[int]) -> None:
        """Establece el ID del recurso requerido."""
        if value is not None and (not isinstance(value, int) or value <= 0):
            raise ValidationError(
                f"required_resource_id debe ser un entero positivo o None, recibido: {value}",
                field="required_resource_id",
                value=value
            )
        self._required_resource_id = value
    
    @property
    def assigned_team(self) -> Optional[Team]:
        """Equipo asignado a la tarea."""
        return self._assigned_team
    
    @assigned_team.setter
    def assigned_team(self, value: Optional[Team]) -> None:
        """Establece el equipo asignado a la tarea."""
        self._assigned_team = value
    
    @property
    def tags(self) -> List[str]:
        """Etiquetas de la tarea."""
        return self._tags.copy()
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Metadatos de la tarea."""
        return self._metadata.copy()

    @property
    def metrics(self) -> TaskMetrics:
        """Métricas de la tarea."""
        return self._metrics
    
    # Business methods
    def update_progress(self, increment: float) -> None:
        """
        Actualiza el progreso de la tarea.
        
        Args:
            increment: Incremento de progreso (puede ser negativo)
            
        Raises:
            ValidationError: Si el incremento no es válido
        """
        if not isinstance(increment, (int, float)):
            raise ValidationError(
                f"increment debe ser un número, recibido: {type(increment)}",
                field="increment",
                value=increment
            )
        
        if self._status == TaskStatus.DONE:
            logger.warning(f"Intentando actualizar progreso de tarea completada: {self.id}")
            return
        
        # Update state according to progress
        if self._status == TaskStatus.TO_DO and increment > 0:
            self._status = TaskStatus.IN_PROGRESS
            logger.debug(f"Tarea {self.id} iniciada")
        
        # Actualizar progreso
        old_progress = self._progress
        self._progress = max(0.0, min(1.0, self._progress + increment))
        
        # Completar tarea si progreso llega al 100%
        if self._progress >= 1.0:
            self._status = TaskStatus.DONE
            self._progress = 1.0
            logger.info(f"Tarea {self.id} completada")
        
        # Update metrics
        if increment > 0:
            self._metrics.actual_duration += increment
        
        logger.debug(f"Progreso actualizado: {old_progress:.2f} -> {self._progress:.2f}")
    
    def add_dependency(self, task: Task) -> None:
        """
        Añade una dependencia a la tarea.
        
        Args:
            task: Tarea de la que depende
            
        Raises:
            ValidationError: Si la dependencia no es válida
        """
        if not isinstance(task, Task):
            raise ValidationError(
                f"dependency debe ser una instancia de Task, recibido: {type(task)}",
                field="dependency",
                value=task
            )
        
        if task.id == self.id:
            raise ValidationError(
                "Una tarea no puede depender de sí misma",
                field="dependency",
                value=task
            )
        
        if task not in self._dependencies:
            self._dependencies.append(task)
            logger.debug(f"Dependencia añadida: {task.id} -> {self.id}")
    
    def remove_dependency(self, task: Task) -> None:
        """
        Elimina una dependencia de la tarea.
        
        Args:
            task: Tarea de la que ya no depende
        """
        if task in self._dependencies:
            self._dependencies.remove(task)
            logger.debug(f"Dependencia eliminada: {task.id} -> {self.id}")
    
    def can_start(self) -> bool:
        """
        Verifica si la tarea puede iniciarse.
        
        Returns:
            True si todas las dependencias están completadas
        """
        if self._status != TaskStatus.TO_DO:
            return False
        
        return all(dep.status == TaskStatus.DONE for dep in self._dependencies)
    
    def assign_resource(self, resource: Resource) -> None:
        """
        Asigna un recurso a la tarea.
        
        Args:
            resource: Recurso a asignar
            
        Raises:
            ValidationError: Si el recurso no es válido
        """
        if not isinstance(resource, Resource):
            raise ValidationError(
                f"resource debe ser una instancia de Resource, recibido: {type(resource)}",
                field="resource",
                value=resource
            )
        
        self._assigned_resource = resource
        logger.debug(f"Recurso {resource.id} asignado a tarea {self.id}")
    
    def assign_team(self, team: Team) -> None:
        """
        Asigna un equipo a la tarea.
        
        Args:
            team: Equipo a asignar
            
        Raises:
            ValidationError: Si el equipo no es válido
        """
        if not isinstance(team, Team):
            raise ValidationError(
                f"team debe ser una instancia de Team, recibido: {type(team)}",
                field="team",
                value=team
            )
        
        self._assigned_team = team
        logger.debug(f"Equipo {team.id} asignado a tarea {self.id}")
    
    def release_assignment(self) -> None:
        """Libera la asignación de recurso o equipo."""
        if self._assigned_resource:
            logger.debug(f"Recurso liberado de tarea {self.id}")
            self._assigned_resource = None
        
        if self._assigned_team:
            logger.debug(f"Equipo liberado de tarea {self.id}")
            self._assigned_team = None
    
    def add_tag(self, tag: str) -> None:
        """
        Añade una etiqueta a la tarea.
        
        Args:
            tag: Etiqueta a añadir
        """
        if isinstance(tag, str) and tag.strip() and tag not in self._tags:
            self._tags.append(tag.strip())
            logger.debug(f"Etiqueta '{tag}' añadida a tarea {self.id}")
    
    def remove_tag(self, tag: str) -> None:
        """
        Elimina una etiqueta de la tarea.
        
        Args:
            tag: Etiqueta a eliminar
        """
        if tag in self._tags:
            self._tags.remove(tag)
            logger.debug(f"Etiqueta '{tag}' eliminada de tarea {self.id}")
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Establece un metadato de la tarea.
        
        Args:
            key: Clave del metadato
            value: Valor del metadato
        """
        self._metadata[key] = value
        logger.debug(f"Metadato '{key}' establecido para tarea {self.id}")
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un metadato de la tarea.
        
        Args:
            key: Clave del metadato
            default: Valor por defecto si no existe
            
        Returns:
            Valor del metadato o valor por defecto
        """
        return self._metadata.get(key, default)
    
    # Special methods
    def __eq__(self, other: object) -> bool:
        """Comparación de igualdad basada en ID."""
        if not isinstance(other, Task):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        """Hash basado en ID."""
        return hash(self._id)
    
    def __lt__(self, other: Task) -> bool:
        """Comparación menor que basada en prioridad."""
        if not isinstance(other, Task):
            return NotImplemented
        return self._priority.value < other._priority.value
    
    def __repr__(self) -> str:
        """Representación textual de la tarea."""
        deps_str = f", deps={[d.id for d in self._dependencies]}" if self._dependencies else ""
        res_str = f", res={self._assigned_resource.id}" if self._assigned_resource else ""
        team_str = f", team={self._assigned_team.id}" if self._assigned_team else ""
        req_res_str = f", req_res={self._required_resource_id}" if self._required_resource_id else ""
        
        return (
            f"Task(id={self._id}, name='{self._name}', "
            f"dur={self._duration:.1f}h, cost={self._estimated_cost:.2f}, "
            f"status={self._status.value}, progress={self._progress:.2f}, "
            f"priority={self._priority.name}{req_res_str}{res_str}{team_str}{deps_str})"
        )
    
    def __str__(self) -> str:
        """Representación legible de la tarea."""
        return f"Tarea {self._id}: {self._name} ({self._status.value})"