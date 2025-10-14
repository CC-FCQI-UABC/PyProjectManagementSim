"""
Continuación de entidades principales del simulador ABP.

Este módulo contiene las clases Resource y Team, refactorizadas
siguiendo principios SOLID con validaciones robustas y documentación completa.
"""

from __future__ import annotations
from typing import List, Dict, Optional, Set, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
import logging

from core.exceptions import ResourceError, TeamError, ValidationError
from core.config.logging_config import get_logger

if TYPE_CHECKING:
    from core.entities import Task, TaskStatus

logger = get_logger(__name__)


class ResourceType(Enum):
    """Tipos de recursos disponibles."""
    HUMAN = "human"
    EQUIPMENT = "equipment"
    MATERIAL = "material"
    VIRTUAL = "virtual"


class ResourceStatus(Enum):
    """Estados de un recurso."""
    AVAILABLE = "available"
    BUSY = "busy"
    UNAVAILABLE = "unavailable"
    MAINTENANCE = "maintenance"


@dataclass
class ResourceMetrics:
    """Metrics associated with a resource."""
    total_hours_worked: float = 0.0
    total_tasks_completed: int = 0
    average_efficiency: float = 1.0
    utilization_rate: float = 0.0
    cost_performance: float = 1.0
    
    def update_efficiency(self, new_efficiency: float) -> None:
        """Actualiza la eficiencia promedio."""
        if self.total_tasks_completed > 0:
            self.average_efficiency = (
                (self.average_efficiency * self.total_tasks_completed + new_efficiency) /
                (self.total_tasks_completed + 1)
            )
        else:
            self.average_efficiency = new_efficiency


class Resource:
    """
    Representa un recurso en el proyecto.
    
    Un recurso puede ser una persona, equipo, material o cualquier
    elemento necesario para completar tareas del proyecto.
    
    Attributes:
        id: Identificador único del recurso
        name: Nombre descriptivo del recurso
        resource_type: Tipo de recurso
        cost_per_hour: Costo por hora de uso del recurso
        efficiency: Factor de eficiencia (1.0 = normal)
        availability: Factor de disponibilidad (0.0-1.0)
        status: Estado actual del recurso
        skills: Habilidades o capacidades del recurso
        metadata: Información adicional personalizada
        metrics: Métricas de rendimiento del recurso
    """
    
    def __init__(
        self,
        resource_id: int,
        name: str,
        cost_per_hour: float,
        resource_type: ResourceType = ResourceType.HUMAN,
        efficiency: float = 1.0,
        availability: float = 1.0,
        skills: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa un nuevo recurso.
        
        Args:
            resource_id: Identificador único del recurso
            name: Nombre descriptivo del recurso
            cost_per_hour: Costo por hora (debe ser >= 0)
            resource_type: Tipo de recurso
            efficiency: Factor de eficiencia (debe ser > 0)
            availability: Factor de disponibilidad (0.0-1.0)
            skills: Lista de habilidades del recurso
            metadata: Información adicional personalizada
            
        Raises:
            ValidationError: Si los parámetros no son válidos
        """
        self._validate_constructor_params(
            resource_id, name, cost_per_hour, efficiency, availability
        )
        
        self._id = resource_id
        self._name = name
        self._resource_type = resource_type
        self._cost_per_hour = max(0.0, cost_per_hour)
        self._efficiency = max(0.1, efficiency)
        self._availability = max(0.0, min(1.0, availability))
        self._status = ResourceStatus.AVAILABLE
        self._skills = skills or []
        self._metadata = metadata or {}
        
        # Metrics
        self._metrics = ResourceMetrics()
        
        logger.debug(f"Resource created: {self}")
    
    def _validate_constructor_params(
        self,
        resource_id: int,
        name: str,
        cost_per_hour: float,
        efficiency: float,
        availability: float
    ) -> None:
        """Validate constructor parameters."""
        if not isinstance(resource_id, int) or resource_id <= 0:
            raise ValidationError(
                f"resource_id debe ser un entero positivo, recibido: {resource_id}",
                field="resource_id",
                value=resource_id
            )
        
        if not isinstance(name, str) or not name.strip():
            raise ValidationError(
                f"name must be a non-empty string, received: '{name}'",
                field="name",
                value=name
            )
        
        if not isinstance(cost_per_hour, (int, float)) or cost_per_hour < 0:
            raise ValidationError(
                f"cost_per_hour must be a number >= 0, received: {cost_per_hour}",
                field="cost_per_hour",
                value=cost_per_hour
            )
        
        if not isinstance(efficiency, (int, float)) or efficiency <= 0:
            raise ValidationError(
                f"efficiency must be a number > 0, received: {efficiency}",
                field="efficiency",
                value=efficiency
            )
        
        if not isinstance(availability, (int, float)) or not (0.0 <= availability <= 1.0):
            raise ValidationError(
                f"availability debe estar entre 0.0 y 1.0, recibido: {availability}",
                field="availability",
                value=availability
            )
    
    # Properties
    @property
    def id(self) -> int:
        """Unique resource ID."""
        return self._id
    
    @property
    def name(self) -> str:
        """Nombre del recurso."""
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        """Establece el nombre del recurso."""
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(
                f"name must be a non-empty string, received: '{value}'",
                field="name",
                value=value
            )
        self._name = value
    
    @property
    def resource_type(self) -> ResourceType:
        """Tipo de recurso."""
        return self._resource_type
    
    @property
    def cost_per_hour(self) -> float:
        """Costo por hora del recurso."""
        return self._cost_per_hour
    
    @cost_per_hour.setter
    def cost_per_hour(self, value: float) -> None:
        """Establece el costo por hora."""
        if not isinstance(value, (int, float)) or value < 0:
            raise ValidationError(
                f"cost_per_hour must be a number >= 0, received: {value}",
                field="cost_per_hour",
                value=value
            )
        self._cost_per_hour = value
    
    @property
    def efficiency(self) -> float:
        """Factor de eficiencia del recurso."""
        return self._efficiency
    
    @efficiency.setter
    def efficiency(self, value: float) -> None:
        """Establece el factor de eficiencia."""
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValidationError(
                f"efficiency must be a number > 0, received: {value}",
                field="efficiency",
                value=value
            )
        self._efficiency = value
    
    @property
    def availability(self) -> float:
        """Factor de disponibilidad del recurso."""
        return self._availability
    
    @availability.setter
    def availability(self, value: float) -> None:
        """Establece el factor de disponibilidad."""
        if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
            raise ValidationError(
                f"availability debe estar entre 0.0 y 1.0, recibido: {value}",
                field="availability",
                value=value
            )
        self._availability = value
    
    @property
    def status(self) -> ResourceStatus:
        """Estado actual del recurso."""
        return self._status
    
    @property
    def skills(self) -> List[str]:
        """Habilidades del recurso."""
        return self._skills.copy()
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Metadatos del recurso."""
        return self._metadata.copy()
    
    @property
    def metrics(self) -> ResourceMetrics:
        """Resource metrics."""
        return self._metrics
    
    # Business methods
    def is_available(self) -> bool:
        """
        Verifica si el recurso está disponible.
        
        Returns:
            True si el recurso está disponible y no está ocupado
        """
        return (
            self._status == ResourceStatus.AVAILABLE and 
            self._availability > 0.0
        )
    
    def set_status(self, status: ResourceStatus) -> None:
        """
        Establece el estado del recurso.
        
        Args:
            status: Nuevo estado del recurso
        """
        if not isinstance(status, ResourceStatus):
            raise ValidationError(
                f"status debe ser una instancia de ResourceStatus, recibido: {type(status)}",
                field="status",
                value=status
            )
        
        old_status = self._status
        self._status = status
        logger.debug(f"Resource {self.id} status changed: {old_status.value} -> {status.value}")
    
    def add_skill(self, skill: str) -> None:
        """
        Añade una habilidad al recurso.
        
        Args:
            skill: Habilidad a añadir
        """
        if isinstance(skill, str) and skill.strip() and skill not in self._skills:
            self._skills.append(skill.strip())
            logger.debug(f"Skill '{skill}' added to resource {self.id}")
    
    def remove_skill(self, skill: str) -> None:
        """
        Elimina una habilidad del recurso.
        
        Args:
            skill: Habilidad a eliminar
        """
        if skill in self._skills:
            self._skills.remove(skill)
            logger.debug(f"Habilidad '{skill}' eliminada del recurso {self.id}")
    
    def has_skill(self, skill: str) -> bool:
        """
        Verifica si el recurso tiene una habilidad específica.
        
        Args:
            skill: Habilidad a verificar
            
        Returns:
            True si el recurso tiene la habilidad
        """
        return skill in self._skills
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Establece un metadato del recurso.
        
        Args:
            key: Clave del metadato
            value: Valor del metadato
        """
        self._metadata[key] = value
        logger.debug(f"Metadato '{key}' establecido para recurso {self.id}")
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un metadato del recurso.
        
        Args:
            key: Clave del metadato
            default: Valor por defecto si no existe
            
        Returns:
            Valor del metadato o valor por defecto
        """
        return self._metadata.get(key, default)
    
    def update_metrics(self, hours_worked: float, efficiency: float) -> None:
        """
        Actualiza las métricas del recurso.
        
        Args:
            hours_worked: Horas trabajadas en el último período
            efficiency: Eficiencia observada en el último período
        """
        self._metrics.total_hours_worked += hours_worked
        self._metrics.total_tasks_completed += 1
        self._metrics.update_efficiency(efficiency)
        
        logger.debug(f"Metrics updated for resource {self.id}")
    
    def get_effective_cost_per_hour(self) -> float:
        """
        Calcula el costo efectivo por hora considerando eficiencia y disponibilidad.
        
        Returns:
            Costo efectivo por hora
        """
        return self._cost_per_hour / (self._efficiency * self._availability)
    
    # Special methods
    def __eq__(self, other: object) -> bool:
        """Equality comparison based on ID."""
        if not isinstance(other, Resource):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        """Hash basado en ID."""
        return hash(self._id)
    
    def __repr__(self) -> str:
        """Textual representation of the resource."""
        return (
            f"Resource(id={self._id}, name='{self._name}', "
            f"type={self._resource_type.value}, cost={self._cost_per_hour:.2f}/h, "
            f"efficiency={self._efficiency:.2f}, availability={self._availability:.2f}, "
            f"status={self._status.value})"
        )
    
    def __str__(self) -> str:
        """Readable representation of the resource."""
        return f"Recurso {self._id}: {self._name} ({self._resource_type.value})"


class Team:
    """
    Representa un equipo de trabajo en el proyecto.
    
    Un equipo es un grupo de recursos que trabajan juntos
    en tareas colaborativas, con dinámica social propia.
    
    Attributes:
        id: Identificador único del equipo
        name: Nombre descriptivo del equipo
        members: Lista de recursos que forman el equipo
        morale: Nivel de moral del equipo (0.0-2.0)
        current_task: Tarea actualmente asignada al equipo
        time_on_current_task: Tiempo trabajando en la tarea actual
        cohesion_factor: Factor de cohesión calculado
        metadata: Información adicional personalizada
    """
    
    def __init__(
        self,
        team_id: int,
        name: str,
        members: List[Resource],
        initial_morale: float = 0.8,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa un nuevo equipo.
        
        Args:
            team_id: Identificador único del equipo
            name: Nombre descriptivo del equipo
            members: Lista de recursos que forman el equipo
            initial_morale: Moral inicial del equipo (0.0-2.0)
            metadata: Información adicional personalizada
            
        Raises:
            ValidationError: Si los parámetros no son válidos
        """
        self._validate_constructor_params(team_id, name, members, initial_morale)
        
        self._id = team_id
        self._name = name
        self._members = members.copy()
        self._morale = max(0.0, min(2.0, initial_morale))
        self._current_task: Optional[Task] = None
        self._time_on_current_task = 0
        self._metadata = metadata or {}
        
        logger.debug(f"Team created: {self}")
    
    def _validate_constructor_params(
        self,
        team_id: int,
        name: str,
        members: List[Resource],
        initial_morale: float
    ) -> None:
        """Validate constructor parameters."""
        if not isinstance(team_id, int) or team_id <= 0:
            raise ValidationError(
                f"team_id debe ser un entero positivo, recibido: {team_id}",
                field="team_id",
                value=team_id
            )
        
        if not isinstance(name, str) or not name.strip():
            raise ValidationError(
                f"name must be a non-empty string, received: '{name}'",
                field="name",
                value=name
            )
        
        if not isinstance(members, list) or not members:
            raise ValidationError(
                f"members must be a non-empty list of Resource, received: {type(members)}",
                field="members",
                value=members
            )
        
        for i, member in enumerate(members):
            if not isinstance(member, Resource):
                raise ValidationError(
                    f"member[{i}] debe ser una instancia de Resource, recibido: {type(member)}",
                    field=f"members[{i}]",
                    value=member
                )
        
        if not isinstance(initial_morale, (int, float)) or not (0.0 <= initial_morale <= 2.0):
            raise ValidationError(
                f"initial_morale debe estar entre 0.0 y 2.0, recibido: {initial_morale}",
                field="initial_morale",
                value=initial_morale
            )
    
    # Properties
    @property
    def id(self) -> int:
        """Unique team ID."""
        return self._id
    
    @property
    def name(self) -> str:
        """Nombre del equipo."""
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        """Establece el nombre del equipo."""
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(
                f"name must be a non-empty string, received: '{value}'",
                field="name",
                value=value
            )
        self._name = value
    
    @property
    def members(self) -> List[Resource]:
        """Miembros del equipo."""
        return self._members.copy()
    
    @property
    def morale(self) -> float:
        """Nivel de moral del equipo."""
        return self._morale
    
    @property
    def current_task(self) -> Optional[Task]:
        """Tarea actualmente asignada al equipo."""
        return self._current_task
    
    @property
    def time_on_current_task(self) -> int:
        """Tiempo trabajando en la tarea actual."""
        return self._time_on_current_task
    
    @time_on_current_task.setter
    def time_on_current_task(self, value: int) -> None:
        """Establece el tiempo trabajando en la tarea actual."""
        if not isinstance(value, int) or value < 0:
            raise ValidationError(
                f"time_on_current_task debe ser un entero >= 0, recibido: {value}",
                field="time_on_current_task",
                value=value
            )
        self._time_on_current_task = value
    
    @property
    def cohesion_factor(self) -> float:
        """
        Factor de cohesión del equipo basado en la moral.
        
        Returns:
            Factor de cohesión (0.6 + morale)
        """
        return 0.6 + self._morale
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Metadatos del equipo."""
        return self._metadata.copy()
    
    # Business methods
    def add_member(self, member: Resource) -> None:
        """
        Añade un miembro al equipo.
        
        Args:
            member: Recurso a añadir al equipo
            
        Raises:
            ValidationError: Si el miembro no es válido
        """
        if not isinstance(member, Resource):
            raise ValidationError(
                f"member debe ser una instancia de Resource, recibido: {type(member)}",
                field="member",
                value=member
            )
        
        if member not in self._members:
            self._members.append(member)
            logger.debug(f"Member {member.id} added to team {self.id}")
    
    def remove_member(self, member: Resource) -> None:
        """
        Elimina un miembro del equipo.
        
        Args:
            member: Recurso a eliminar del equipo
        """
        if member in self._members:
            self._members.remove(member)
            logger.debug(f"Miembro {member.id} eliminado del equipo {self.id}")
    
    def boost_morale(self, amount: float = 0.25) -> None:
        """
        Aumenta la moral del equipo.
        
        Args:
            amount: Cantidad a aumentar (debe ser > 0)
        """
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValidationError(
                f"amount must be a number > 0, received: {amount}",
                field="amount",
                value=amount
            )
        
        old_morale = self._morale
        self._morale = min(2.0, self._morale + amount)
        logger.debug(f"Team {self.id} morale increased: {old_morale:.2f} -> {self._morale:.2f}")
    
    def decay_morale(self, amount: float = 0.05) -> None:
        """
        Disminuye la moral del equipo.
        
        Args:
            amount: Cantidad a disminuir (debe ser > 0)
        """
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValidationError(
                f"amount must be a number > 0, received: {amount}",
                field="amount",
                value=amount
            )
        
        old_morale = self._morale
        self._morale = max(0.0, self._morale - amount)
        logger.debug(f"Team {self.id} morale decreased: {old_morale:.2f} -> {self._morale:.2f}")
    
    def regress_to_mean(self, baseline: float = 0.75, rate: float = 0.02) -> None:
        """
        La moral tiende a volver a un estado base neutral con el tiempo.
        
        Args:
            baseline: Nivel base de moral hacia el cual regresar
            rate: Velocidad de regresión (0.0-1.0)
        """
        if not isinstance(baseline, (int, float)) or not (0.0 <= baseline <= 2.0):
            raise ValidationError(
                f"baseline debe estar entre 0.0 y 2.0, recibido: {baseline}",
                field="baseline",
                value=baseline
            )
        
        if not isinstance(rate, (int, float)) or not (0.0 <= rate <= 1.0):
            raise ValidationError(
                f"rate debe estar entre 0.0 y 1.0, recibido: {rate}",
                field="rate",
                value=rate
            )
        
        if self._morale > baseline:
            self._morale -= rate * (self._morale - baseline)
        elif self._morale < baseline:
            self._morale += rate * (baseline - self._morale)
    
    def assign_task(self, task: Task) -> None:
        """
        Asigna una tarea al equipo.
        
        Args:
            task: Tarea a asignar
            
        Raises:
            ValidationError: Si la tarea no es válida
        """
        # Validate task parameter using duck typing instead of isinstance
        if not hasattr(task, 'id') or not hasattr(task, 'name') or not hasattr(task, 'duration'):
            raise ValidationError(
                f"task debe tener atributos 'id', 'name' y 'duration', recibido: {type(task)}",
                field="task",
                value=type(task)
            )
        
        self._current_task = task
        self._time_on_current_task = 0
        logger.debug(f"Tarea {task.id} asignada al equipo {self.id}")
    
    def release_task(self) -> None:
        """Libera la tarea actual del equipo."""
        if self._current_task:
            logger.debug(f"Tarea {self._current_task.id} liberada del equipo {self.id}")
            self._current_task = None
            self._time_on_current_task = 0
    
    def is_busy(self) -> bool:
        """
        Verifica si el equipo está ocupado.
        
        Returns:
            True si el equipo tiene una tarea asignada y no está completada
        """
        return (
            self._current_task is not None and 
            self._current_task.status.value != "done"
        )
    
    def get_team_size(self) -> int:
        """
        Obtiene el número de miembros del equipo.
        
        Returns:
            Número de miembros
        """
        return len(self._members)
    
    def get_available_members(self) -> List[Resource]:
        """
        Obtiene los miembros disponibles del equipo.
        
        Returns:
            Lista de miembros disponibles
        """
        return [member for member in self._members if member.is_available()]
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Establece un metadato del equipo.
        
        Args:
            key: Clave del metadato
            value: Valor del metadato
        """
        self._metadata[key] = value
        logger.debug(f"Metadato '{key}' establecido para equipo {self.id}")
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un metadato del equipo.
        
        Args:
            key: Clave del metadato
            default: Valor por defecto si no existe
            
        Returns:
            Valor del metadato o valor por defecto
        """
        return self._metadata.get(key, default)
    
    # Special methods
    def __eq__(self, other: object) -> bool:
        """Equality comparison based on ID."""
        if not isinstance(other, Team):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        """Hash basado en ID."""
        return hash(self._id)
    
    def __len__(self) -> int:
        """Number of team members."""
        return len(self._members)
    
    def __contains__(self, member: Resource) -> bool:
        """Verifica si un recurso es miembro del equipo."""
        return member in self._members
    
    def __repr__(self) -> str:
        """Textual representation of the team."""
        member_ids = [member.id for member in self._members]
        task_id = self._current_task.id if self._current_task else None
        
        return (
            f"Team(id={self._id}, name='{self._name}', "
            f"members={member_ids}, morale={self._morale:.2f}, "
            f"current_task={task_id}, cohesion={self.cohesion_factor:.2f})"
        )
    
    def __str__(self) -> str:
        """Readable representation of the team."""
        return f"Equipo {self._id}: {self._name} ({len(self._members)} miembros)"
