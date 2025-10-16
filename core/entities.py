"""
-----------------------------------------------------------------
PyProjectManagementSim 1.0
Modelo computacional de gestión de proyectos en Python.
Autores: Manuel Castañón–Puga, Fernando Rosales Quiñones
Correo electrónico: {puga, fernando.rosales59}@uabc.edu.mx
Universidad Autónoma de Baja California
http://www.uabc.edu.mx
PyProjectManagementSim/core/entities.py
-----------------------------------------------------------------
"""

from __future__ import annotations

"""
Core entities of the ABP simulator.

This module contains the fundamental entities of the simulator:
Task, Resource and Team, refactored following SOLID principles
with robust validations, properties and complete documentation.
"""

from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

from core.exceptions import TaskError, ResourceError, TeamError, ValidationError
from core.config.logging_config import get_logger

# Import Resource and Team from entities_extended
from core.entities_extended import Resource, Team

logger = get_logger(__name__)


class TaskStatus(Enum):
    """Possible task states."""
    TO_DO = "to-do"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priorities."""
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
        """Cost variance (positive = overcost)."""
        return self.actual_cost - self.planned_cost
    
    @property
    def schedule_performance_index(self) -> float:
        """Schedule performance index."""
        if self.actual_duration == 0:
            return 1.0
        return self.planned_duration / self.actual_duration
    
    @property
    def cost_performance_index(self) -> float:
        """Cost performance index."""
        if self.actual_cost == 0:
            return 1.0
        return self.planned_cost / self.actual_cost


class Task:
    """
    Represents a task in the project.
    
    A task is the basic unit of work in the simulator,
    with properties like duration, cost, dependencies and status.
    
    Attributes:
        id: Unique task identifier
        name: Descriptive task name
        duration: Estimated duration in hours
        estimated_cost: Estimated cost of the task
        status: Current status of the task
        progress: Current progress (0.0 to 1.0)
        priority: Task priority
        metrics: Task performance metrics
        dependencies: List of tasks that depend on this task
        assigned_resource: Resource assigned to the task
        required_resource_id: ID of the required resource
        assigned_team: Team assigned to the task
        tags: Tags for categorization
        metadata: Additional custom information
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
        Initialize a new task.
        
        Args:
            task_id: Unique task identifier
            name: Descriptive task name
            duration: Estimated duration in hours (must be > 0)
            estimated_cost: Estimated cost (must be >= 0)
            priority: Task priority
            tags: List of tags for categorization
            metadata: Additional custom information
            
        Raises:
            ValidationError: If parameters are not valid
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
        
        # Relationships
        self._dependencies: List[Task] = []
        self._assigned_resource: Optional[Resource] = None
        self._required_resource_id: Optional[int] = None
        self._assigned_team: Optional[Team] = None
        
        # Metrics
        self._metrics = TaskMetrics(
            planned_duration=self._duration,
            planned_cost=self._estimated_cost
        )
        
        logger.debug(f"Task created: {self}")
    
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
                f"task_id must be a positive integer, received: {task_id}",
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
        """Task name."""
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        """Set the task name."""
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(
                f"name must be a non-empty string, received: '{value}'",
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
        """Set the estimated duration."""
        if not isinstance(value, (int, float)) or value < 0:
            raise ValidationError(
                f"duration must be a number >= 0, received: {value}",
                field="duration",
                value=value
            )
        self._duration = value
        self._metrics.planned_duration = value
    
    @property
    def real_duration(self) -> float:
        """Real duration accumulated in hours."""
        return self._real_duration
    
    @real_duration.setter
    def real_duration(self, value: float) -> None:
        """Set the real duration accumulated."""
        if not isinstance(value, (int, float)) or value < 0:
            raise ValidationError(
                f"real_duration must be a number >= 0, received: {value}",
                field="real_duration",
                value=value
            )
        self._real_duration = value
    
    @property
    def estimated_cost(self) -> float:
        """Estimated cost of the task."""
        return self._estimated_cost
    
    @estimated_cost.setter
    def estimated_cost(self, value: float) -> None:
        """Set the estimated cost."""
        if not isinstance(value, (int, float)) or value < 0:
            raise ValidationError(
                f"estimated_cost must be a number >= 0, received: {value}",
                field="estimated_cost",
                value=value
            )
        self._estimated_cost = value
        self._metrics.planned_cost = value
    
    @property
    def status(self) -> TaskStatus:
        """Current status of the task."""
        return self._status
    
    @status.setter
    def status(self, value: TaskStatus) -> None:
        """Set the status of the task."""
        self._status = value
    
    @property
    def progress(self) -> float:
        """Current progress (0.0 to 1.0)."""
        return self._progress
    
    @property
    def priority(self) -> TaskPriority:
        """Task priority."""
        return self._priority
    
    @priority.setter
    def priority(self, value: TaskPriority) -> None:
        """Set the task priority."""
        if not isinstance(value, TaskPriority):
            raise ValidationError(
                f"priority must be an instance of TaskPriority, received: {type(value)}",
                field="priority",
                value=value
            )
        self._priority = value
    
    @property
    def dependencies(self) -> List[Task]:
        """List of tasks that depend on this task."""
        return self._dependencies.copy()
    
    @dependencies.setter
    def dependencies(self, value: List[Task]) -> None:
        """Set the dependencies of the task."""
        if not isinstance(value, list):
            raise TypeError("dependencies must be a list of Task")
        self._dependencies = value.copy()
    
    @property
    def assigned_resource(self) -> Optional[Resource]:
        """Resource assigned to the task."""
        return self._assigned_resource
    
    @property
    def required_resource_id(self) -> Optional[int]:
        """Required resource ID."""
        return self._required_resource_id
    
    @required_resource_id.setter
    def required_resource_id(self, value: Optional[int]) -> None:
        """Set the required resource ID."""
        if value is not None and (not isinstance(value, int) or value <= 0):
            raise ValidationError(
                f"required_resource_id must be a positive integer or None, received: {value}",
                field="required_resource_id",
                value=value
            )
        self._required_resource_id = value
    
    @property
    def assigned_team(self) -> Optional[Team]:
        """Team assigned to the task."""
        return self._assigned_team
    
    @assigned_team.setter
    def assigned_team(self, value: Optional[Team]) -> None:
        """Set the team assigned to the task."""
        self._assigned_team = value
    
    @property
    def tags(self) -> List[str]:
        """Tags of the task."""
        return self._tags.copy()
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Metadata of the task."""
        return self._metadata.copy()

    @property
    def metrics(self) -> TaskMetrics:
        """Metrics of the task."""
        return self._metrics
    
    # Business methods
    def update_progress(self, increment: float) -> None:
        """
        Update the progress of the task.
        
        Args:
            increment: Progress increment (can be negative)
            
        Raises:
            ValidationError: If the increment is not valid
        """
        if not isinstance(increment, (int, float)):
            raise ValidationError(
                f"increment must be a number, received: {type(increment)}",
                field="increment",
                value=increment
            )
        
        if self._status == TaskStatus.DONE:
            logger.warning(f"Attempting to update progress of completed task: {self.id}")
            return
        
        # Update state according to progress
        if self._status == TaskStatus.TO_DO and increment > 0:
            self._status = TaskStatus.IN_PROGRESS
            logger.debug(f"Task {self.id} started")
        
        # Update progress
        old_progress = self._progress
        self._progress = max(0.0, min(1.0, self._progress + increment))
        
        # Complete task if progress reaches 100%
        if self._progress >= 1.0:
            self._status = TaskStatus.DONE
            self._progress = 1.0
            logger.info(f"Task {self.id} completed")
        
        # Update metrics
        if increment > 0:
            self._metrics.actual_duration += increment
        
        logger.debug(f"Progress updated: {old_progress:.2f} -> {self._progress:.2f}")
    
    def add_dependency(self, task: Task) -> None:
        """
        Add a dependency to the task.
        
        Args:
            task: Task that depends on this task
            
        Raises:
            ValidationError: If the dependency is not valid
        """
        if not isinstance(task, Task):
            raise ValidationError(
                f"dependency must be an instance of Task, received: {type(task)}",
                field="dependency",
                value=task
            )
        
        if task.id == self.id:
            raise ValidationError(
                "A task cannot depend on itself",
                field="dependency",
                value=task
            )
        
        if task not in self._dependencies:
            self._dependencies.append(task)
            logger.debug(f"Dependency added: {task.id} -> {self.id}")
    
    def remove_dependency(self, task: Task) -> None:
        """
        Remove a dependency from the task.
        
        Args:
            task: Task that is no longer dependent on this task
        """
        if task in self._dependencies:
            self._dependencies.remove(task)
            logger.debug(f"Dependency removed: {task.id} -> {self.id}")
    
    def can_start(self) -> bool:
        """
        Check if the task can be started.
        
        Returns:
            True if all dependencies are completed
        """
        if self._status != TaskStatus.TO_DO:
            return False
        
        return all(dep.status == TaskStatus.DONE for dep in self._dependencies)
    
    def assign_resource(self, resource: Resource) -> None:
        """
        Assign a resource to the task.
        
        Args:
            resource: Resource to assign
            
        Raises:
            ValidationError: If the resource is not valid
        """
        if not isinstance(resource, Resource):
            raise ValidationError(
                f"resource must be an instance of Resource, received: {type(resource)}",
                field="resource",
                value=resource
            )
        
        self._assigned_resource = resource
        logger.debug(f"Resource {resource.id} assigned to task {self.id}")
    
    def assign_team(self, team: Team) -> None:
        """
        Assign a team to the task.
        
        Args:
            team: Team to assign
            
        Raises:
            ValidationError: If the team is not valid
        """
        if not isinstance(team, Team):
            raise ValidationError(
                f"team must be an instance of Team, received: {type(team)}",
                field="team",
                value=team
            )
        
        self._assigned_team = team
        logger.debug(f"Team {team.id} assigned to task {self.id}")
    
    def release_assignment(self) -> None:
        """Release the resource or team assignment."""
        if self._assigned_resource:
            logger.debug(f"Resource released from task {self.id}")
            self._assigned_resource = None
        
        if self._assigned_team:
            logger.debug(f"Team released from task {self.id}")
            self._assigned_team = None
    
    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the task.
        
        Args:
            tag: Tag to add
        """
        if isinstance(tag, str) and tag.strip() and tag not in self._tags:
            self._tags.append(tag.strip())
            logger.debug(f"Tag '{tag}' added to task {self.id}")
    
    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the task.
        
        Args:
            tag: Tag to remove
        """
        if tag in self._tags:
            self._tags.remove(tag)
            logger.debug(f"Tag '{tag}' removed from task {self.id}")
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set a metadata of the task.
        
        Args:
            key: Key of the metadata
            value: Value of the metadata
        """
        self._metadata[key] = value
        logger.debug(f"Metadata '{key}' set for task {self.id}")
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get a metadata of the task.
        
        Args:
            key: Key of the metadata
            default: Default value if not exists
            
        Returns:
            Value of the metadata or default value
        """
        return self._metadata.get(key, default)
    
    # Special methods
    def __eq__(self, other: object) -> bool:
        """Equality comparison based on ID."""
        if not isinstance(other, Task):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self._id)
    
    def __lt__(self, other: Task) -> bool:
        """Comparison less than based on priority."""
        if not isinstance(other, Task):
            return NotImplemented
        return self._priority.value < other._priority.value
    
    def __repr__(self) -> str:
        """Textual representation of the task."""
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
        """Readable representation of the task."""
        return f"Task {self._id}: {self._name} ({self._status.value})"