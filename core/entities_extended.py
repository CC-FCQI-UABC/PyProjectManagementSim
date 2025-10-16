"""
-----------------------------------------------------------------
PyProjectManagementSim 1.0
Modelo computacional de gestión de proyectos en Python.
Autores: Manuel Castañón–Puga, Fernando Rosales Quiñones
Correo electrónico: {puga, fernando.rosales59}@uabc.edu.mx
Universidad Autónoma de Baja California
http://www.uabc.edu.mx
PyProjectManagementSim/core/entities_extended.py
-----------------------------------------------------------------
"""

from __future__ import annotations

"""
Extended entities of the ABP simulator.

This module contains the Resource and Team classes, refactored
following SOLID principles with robust validations and complete documentation.
It also contains the ResourceMetrics class, which is used to store the metrics of a resource.
"""

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
    """Available resource types."""
    HUMAN = "human"
    EQUIPMENT = "equipment"
    MATERIAL = "material"
    VIRTUAL = "virtual"


class ResourceStatus(Enum):
    """Resource states."""
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
        """Update the average efficiency."""
        if self.total_tasks_completed > 0:
            self.average_efficiency = (
                (self.average_efficiency * self.total_tasks_completed + new_efficiency) /
                (self.total_tasks_completed + 1)
            )
        else:
            self.average_efficiency = new_efficiency


class Resource:
    """
    Represents a resource in the project.
    
    A resource can be a person, equipment, material or any
    element necessary to complete tasks of the project.
    
    Attributes:
        id: Unique identifier of the resource
        name: Descriptive name of the resource
        resource_type: Resource type
        cost_per_hour: Cost per hour of use of the resource
        efficiency: Efficiency factor (1.0 = normal)
        availability: Availability factor (0.0-1.0)
        status: Current state of the resource
        skills: Skills or capabilities of the resource
        metadata: Additional custom information
        metrics: Resource performance metrics
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
        Initializes a new resource.
        
        Args:
            resource_id: Unique identifier of the resource
            name: Descriptive name of the resource
            cost_per_hour: Cost per hour (must be >= 0)
            resource_type: Resource type
            efficiency: Efficiency factor (must be > 0)
            availability: Availability factor (0.0-1.0)
            skills: List of skills of the resource
            metadata: Additional custom information
            
        Raises:
            ValidationError: If the parameters are not valid
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
                f"resource_id must be a positive integer, received: {resource_id}",
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
                f"availability must be between 0.0 and 1.0, received: {availability}",
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
        """Name of the resource."""
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        """Set the name of the resource."""
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(
                f"name must be a non-empty string, received: '{value}'",
                field="name",
                value=value
            )
        self._name = value
    
    @property
    def resource_type(self) -> ResourceType:
        """Resource type."""
        return self._resource_type
    
    @property
    def cost_per_hour(self) -> float:
        """Cost per hour of the resource."""
        return self._cost_per_hour
    
    @cost_per_hour.setter
    def cost_per_hour(self, value: float) -> None:
        """Set the cost per hour."""
        if not isinstance(value, (int, float)) or value < 0:
            raise ValidationError(
                f"cost_per_hour must be a number >= 0, received: {value}",
                field="cost_per_hour",
                value=value
            )
        self._cost_per_hour = value
    
    @property
    def efficiency(self) -> float:
        """Efficiency factor of the resource."""
        return self._efficiency
    
    @efficiency.setter
    def efficiency(self, value: float) -> None:
        """Set the efficiency factor."""
        if not isinstance(value, (int, float)) or value <= 0:
            raise ValidationError(
                f"efficiency must be a number > 0, received: {value}",
                field="efficiency",
                value=value
            )
        self._efficiency = value
    
    @property
    def availability(self) -> float:
        """Availability factor of the resource."""
        return self._availability
    
    @availability.setter
    def availability(self, value: float) -> None:
        """Set the availability factor."""
        if not isinstance(value, (int, float)) or not (0.0 <= value <= 1.0):
            raise ValidationError(
                f"availability must be between 0.0 and 1.0, received: {value}",
                field="availability",
                value=value
            )
        self._availability = value
    
    @property
    def status(self) -> ResourceStatus:
        """Current state of the resource."""
        return self._status
    
    @property
    def skills(self) -> List[str]:
        """Skills of the resource."""
        return self._skills.copy()
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Metadata of the resource."""
        return self._metadata.copy()
    
    @property
    def metrics(self) -> ResourceMetrics:
        """Resource metrics."""
        return self._metrics
    
    # Business methods
    def is_available(self) -> bool:
        """
        Checks if the resource is available.
        
        Returns:
            True if the resource is available and not occupied
        """
        return (
            self._status == ResourceStatus.AVAILABLE and 
            self._availability > 0.0
        )
    
    def set_status(self, status: ResourceStatus) -> None:
        """
        Set the state of the resource.
        
        Args:
            status: New state of the resource
        """
        if not isinstance(status, ResourceStatus):
            raise ValidationError(
                f"status must be an instance of ResourceStatus, received: {type(status)}",
                field="status",
                value=status
            )
        
        old_status = self._status
        self._status = status
        logger.debug(f"Resource {self.id} status changed: {old_status.value} -> {status.value}")
    
    def add_skill(self, skill: str) -> None:
        """
        Add a skill to the resource.
        
        Args:
            skill: Skill to add
        """
        if isinstance(skill, str) and skill.strip() and skill not in self._skills:
            self._skills.append(skill.strip())
            logger.debug(f"Skill '{skill}' added to resource {self.id}")
    
    def remove_skill(self, skill: str) -> None:
        """
        Remove a skill from the resource.
        
        Args:
            skill: Skill to remove
        """
        if skill in self._skills:
            self._skills.remove(skill)
            logger.debug(f"Skill '{skill}' removed from resource {self.id}")
    
    def has_skill(self, skill: str) -> bool:
        """
        Checks if the resource has a specific skill.
        
        Args:
            skill: Skill to check
            
        Returns:
            True if the resource has the skill
        """
        return skill in self._skills
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set a metadata of the resource.
        
        Args:
            key: Key of the metadata
            value: Value of the metadata
        """
        self._metadata[key] = value
        logger.debug(f"Metadata '{key}' set for resource {self.id}")
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get a metadata of the resource.
        
        Args:
            key: Key of the metadata
            default: Default value if not exists
            
        Returns:
            Value of the metadata or default value
        """
        return self._metadata.get(key, default)
    
    def update_metrics(self, hours_worked: float, efficiency: float) -> None:
        """
        Update the metrics of the resource.
        
        Args:
            hours_worked: Hours worked in the last period
            efficiency: Efficiency observed in the last period
        """
        self._metrics.total_hours_worked += hours_worked
        self._metrics.total_tasks_completed += 1
        self._metrics.update_efficiency(efficiency)
        
        logger.debug(f"Metrics updated for resource {self.id}")
    
    def get_effective_cost_per_hour(self) -> float:
        """
        Calculate the effective cost per hour considering efficiency and availability.
        
        Returns:
            Effective cost per hour
        """
        return self._cost_per_hour / (self._efficiency * self._availability)
    
    # Special methods
    def __eq__(self, other: object) -> bool:
        """Equality comparison based on ID."""
        if not isinstance(other, Resource):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        """Hash based on ID."""
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
    Represents a team of workers in the project.
    
    A team is a group of resources that work together
    in collaborative tasks, with its own social dynamics.
    
    Attributes:
        id: Unique identifier of the team
        name: Descriptive name of the team
        members: List of resources that form the team
        morale: Moral level of the team (0.0-2.0)
        current_task: Task currently assigned to the team
        time_on_current_task: Time working on the current task
        cohesion_factor: Calculated cohesion factor
        metadata: Additional custom information
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
        Initializes a new team.
        
        Args:
            team_id: Unique identifier of the team
            name: Descriptive name of the team
            members: List of resources that form the team
            initial_morale: Initial moral of the team (0.0-2.0)
            metadata: Additional custom information
            
        Raises:
            ValidationError: If the parameters are not valid
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
                f"team_id must be a positive integer, received: {team_id}",
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
                    f"member[{i}] must be an instance of Resource, received: {type(member)}",
                    field=f"members[{i}]",
                    value=member
                )
        
        if not isinstance(initial_morale, (int, float)) or not (0.0 <= initial_morale <= 2.0):
            raise ValidationError(
                f"initial_morale must be between 0.0 and 2.0, received: {initial_morale}",
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
        """Name of the team."""
        return self._name
    
    @name.setter
    def name(self, value: str) -> None:
        """Set the name of the team."""
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(
                f"name must be a non-empty string, received: '{value}'",
                field="name",
                value=value
            )
        self._name = value
    
    @property
    def members(self) -> List[Resource]:
        """Members of the team."""
        return self._members.copy()
    
    @property
    def morale(self) -> float:
        """Moral level of the team."""
        return self._morale
    
    @property
    def current_task(self) -> Optional[Task]:
        """Task currently assigned to the team."""
        return self._current_task
    
    @property
    def time_on_current_task(self) -> int:
        """Time working on the current task."""
        return self._time_on_current_task
    
    @time_on_current_task.setter
    def time_on_current_task(self, value: int) -> None:
        """Set the time working on the current task."""
        if not isinstance(value, int) or value < 0:
            raise ValidationError(
                f"time_on_current_task must be an integer >= 0, received: {value}",
                field="time_on_current_task",
                value=value
            )
        self._time_on_current_task = value
    
    @property
    def cohesion_factor(self) -> float:
        """
        Cohesion factor of the team based on the morale.
        
        Returns:
            Cohesion factor (0.6 + morale)
        """
        return 0.6 + self._morale
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Metadata of the team."""
        return self._metadata.copy()
    
    # Business methods
    def add_member(self, member: Resource) -> None:
        """
        Add a member to the team.
        
        Args:
            member: Resource to add to the team
            
        Raises:
            ValidationError: If the member is not valid
        """
        if not isinstance(member, Resource):
            raise ValidationError(
                f"member must be an instance of Resource, received: {type(member)}",
                field="member",
                value=member
            )
        
        if member not in self._members:
            self._members.append(member)
            logger.debug(f"Member {member.id} added to team {self.id}")
    
    def remove_member(self, member: Resource) -> None:
        """
        Remove a member from the team.
        
        Args:
            member: Resource to remove from the team
        """
        if member in self._members:
            self._members.remove(member)
            logger.debug(f"Member {member.id} removed from team {self.id}")
    
    def boost_morale(self, amount: float = 0.25) -> None:
        """
        Increase the morale of the team.
        
        Args:
            amount: Amount to increase (must be > 0)
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
        Decrease the morale of the team.
        
        Args:
            amount: Amount to decrease (must be > 0)
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
        The morale tends to return to a neutral base state over time.
        
        Args:
            baseline: Base moral level to which to return
            rate: Regression rate (0.0-1.0)
        """
        if not isinstance(baseline, (int, float)) or not (0.0 <= baseline <= 2.0):
            raise ValidationError(
                f"baseline must be between 0.0 and 2.0, received: {baseline}",
                field="baseline",
                value=baseline
            )
        
        if not isinstance(rate, (int, float)) or not (0.0 <= rate <= 1.0):
            raise ValidationError(
                f"rate must be between 0.0 and 1.0, received: {rate}",
                field="rate",
                value=rate
            )
        
        if self._morale > baseline:
            self._morale -= rate * (self._morale - baseline)
        elif self._morale < baseline:
            self._morale += rate * (baseline - self._morale)
    
    def assign_task(self, task: Task) -> None:
        """
        Assign a task to the team.
        
        Args:
            task: Task to assign
            
        Raises:
            ValidationError: If the task is not valid
        """
        # Validate task parameter using duck typing instead of isinstance
        if not hasattr(task, 'id') or not hasattr(task, 'name') or not hasattr(task, 'duration'):
            raise ValidationError(
                f"task must have attributes 'id', 'name' and 'duration', received: {type(task)}",
                field="task",
                value=type(task)
            )
        
        self._current_task = task
        self._time_on_current_task = 0
        logger.debug(f"Task {task.id} assigned to team {self.id}")
    
    def release_task(self) -> None:
        """Release the current task from the team."""
        if self._current_task:
            logger.debug(f"Task {self._current_task.id} released from team {self.id}")
            self._current_task = None
            self._time_on_current_task = 0
    
    def is_busy(self) -> bool:
        """
        Check if the team is busy.
        
        Returns:
            True if the team has a task assigned and is not completed
        """
        return (
            self._current_task is not None and 
            self._current_task.status.value != "done"
        )
    
    def get_team_size(self) -> int:
        """
        Get the number of members of the team.
        
        Returns:
            Number of members
        """
        return len(self._members)
    
    def get_available_members(self) -> List[Resource]:
        """
        Get the available members of the team.
        
        Returns:
            List of available members
        """
        return [member for member in self._members if member.is_available()]
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set a metadata of the team.
        
        Args:
            key: Key of the metadata
            value: Value of the metadata
        """
        self._metadata[key] = value
        logger.debug(f"Metadata '{key}' set for team {self.id}")
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get a metadata of the team.

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
        if not isinstance(other, Team):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self._id)
    
    def __len__(self) -> int:
        """Number of members of the team."""
        return len(self._members)
    
    def __contains__(self, member: Resource) -> bool:
        """Check if a resource is a member of the team."""
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
        return f"Team {self._id}: {self._name} ({len(self._members)} members)"
