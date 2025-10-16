"""
-----------------------------------------------------------------
PyProjectManagementSim 1.0
Modelo computacional de gestión de proyectos en Python.
Autores: Manuel Castañón–Puga, Fernando Rosales Quiñones
Correo electrónico: {puga, fernando.rosales59}@uabc.edu.mx
Universidad Autónoma de Baja California
http://www.uabc.edu.mx
PyProjectManagementSim/core/interfaces.py
-----------------------------------------------------------------
"""

"""
Base interfaces for the PyProjectManagementSim framework.
"""

from abc import ABC, abstractmethod
# Import the classes that the interfaces need to know
from core.entities import Task, Resource, Team
from core.exceptions import SimulatorException
from typing import List, Dict, Any, Optional, Protocol, runtime_checkable
from dataclasses import dataclass

@runtime_checkable
class ITaskProgressCalculator(Protocol):
    """
    Protocol for task progress calculators.
    
    Defines the interface that must be implemented by components
    responsible for calculating task progress.
    """
    
    def calculate_progress_increment(
        self, 
        task: Task, 
        assigned_resource: Optional[Resource] = None,
        assigned_team: Optional[Team] = None,
        **context
    ) -> float:
        """
        Calculate progress increment for a task.
        
        Args:
            task: Task for which to calculate progress
            assigned_resource: Assigned resource (optional)
            assigned_team: Assigned team (optional)
            **context: Additional context
            
        Returns:
            Progress increment (0.0 to 1.0)
        """
        ...


@runtime_checkable
class IResourceAllocator(Protocol):
    """
    Protocol for resource allocators.
    
    Defines the interface that must be implemented by components
    responsible for assigning resources to tasks.
    """
    
    def allocate_resource(
        self, 
        task: Task, 
        available_resources: List[Resource],
        **context
    ) -> Optional[Resource]:
        """
        Assigns a resource to a task.
        
        Args:
            task: Task to assign resource to
            available_resources: List of available resources
            **context: Additional context
            
        Returns:
            Assigned resource or None if not assigned
        """
        ...


@runtime_checkable
class IMetricsCollector(Protocol):
    """
    Protocol for metric collectors.
    
    Defines the interface that components responsible for
    collecting project metrics must implement.
    """
    
    def collect_metrics(
        self, 
        tasks: List[Task], 
        resources: List[Resource],
        teams: List[Team],
        **context
    ) -> Dict[str, Any]:
        """
        Collects project metrics.
        
        Args:
            tasks: List of project tasks
            resources: List of project resources
            teams: List of project teams
            **context: Additional context
            
        Returns:
            Dictionary with collected metrics
        """
        ...


@runtime_checkable
class IEventManager(Protocol):
    """
    Protocol for event managers.
    
    Defines the interface that must be implemented by components
    responsible for managing random events.
    """
    
    def should_trigger_event(self, **context) -> bool:
        """
        Determines if an event should be triggered.
        
        Args:
            **context: Simulation context
            
        Returns:
            True if an event should be triggered
        """
        ...
    
    def trigger_event(self, **context) -> Dict[str, Any]:
        """
        Triggers a random event.
        
        Args:
            **context: Simulation context
            
        Returns:
            Information about the triggered event
        """
        ...


@runtime_checkable
class IDependencyResolver(Protocol):
    """
    Protocol for dependency resolvers.
    
    Defines the interface that must be implemented by components
    responsible for resolving dependencies between tasks.
    """
    
    def can_task_start(self, task: Task) -> bool:
        """
        Checks if a task can be started.
        
        Args:
            task: Task to check
            
        Returns:
            True if the task can be started
        """
        ...
    
    def get_ready_tasks(self, tasks: List[Task]) -> List[Task]:
        """
        Gets tasks that are ready to start.
        
        Args:
            tasks: Tasks to check
            
        Returns:
            Tasks that are ready to start
        """
        ...


class IProjectReader(ABC):
    """
    Base interface for project readers.
    
    Defines the contract that must be implemented by all project readers
    de archivos de proyecto (MPP, XML, etc.).
    """
    
    @abstractmethod
    def load(self, file_path: str) -> 'ProjectData':
        """
        Loads a project from a file.
        
        Args:
            file_path: Path to the project file
            
        Returns:
            Loaded project data
            
        Raises:
            ReaderError: If there are problems loading the file
        """
        pass
    
    @abstractmethod
    def validate_data(self, data: 'ProjectData') -> bool:
        """
        Validates the project data.
        
        Args:
            data: Project data to validate
            
        Returns:
            True if data is valid
            
        Raises:
            ValidationError: If data is not valid
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Gets the supported file extensions.
        
        Returns:
            List of supported extensions
        """
        pass


class IAssignmentStrategy(ABC):
    """
    Base interface for assignment strategies.
    
    Defines the contract that all task assignment strategies
    must implement.
    """
    
    @abstractmethod
    def assign_tasks(self, tasks: List[Task], resources: List[Resource]) -> Dict[int, int]:
        """
        Assigns tasks to resources.
        
        Args:
            tasks: Tasks to assign
            resources: Available resources
            
        Returns:
            Dictionary mapping task_id -> resource_id
            
        Raises:
            StrategyError: If there are problems assigning tasks
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """
        Gets the name of the strategy.
        
        Returns:
            Name of the strategy
        """
        pass
    
    @abstractmethod
    def get_strategy_description(self) -> str:
        """
        Get the strategy description.
        
        Returns:
            Description of the strategy
        """
        pass


class IOutputManager(ABC):
    """
    Base interface for output managers.
    
    Defines the contract that must be implemented by components
    responsible for generating and saving results.
    """
    
    @abstractmethod
    def save_results(self, data: Any, output_path: str, **options) -> None:
        """
        Saves results to a file.
        
        Args:
            data: Data to save
            output_path: Path to save the results
            **options: Additional options
            
        Raises:
            OutputError: If there are problems saving the results
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """
        Gets the supported output formats.
        
        Returns:
            List of supported formats
        """
        pass


class IPlugin(ABC):
    """
    Base interface for plugins.
    
    Defines the contract that must be implemented by all plugins
    for the system.
    """
    
    @abstractmethod
    def initialize(self, **config) -> None:
        """
        Initializes the plugin.
        
        Args:
            **config: Plugin configuration
            
        Raises:
            PluginError: If there are problems initializing the plugin
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """
        Cleans up resources of the plugin.
        
        Raises:
            PluginError: If there are problems cleaning up the plugin
        """
        pass
    
    @abstractmethod
    def get_plugin_name(self) -> str:
        """
        Gets the name of the plugin.
        
        Returns:
            Name of the plugin
        """
        pass
    
    @abstractmethod
    def get_plugin_version(self) -> str:
        """
        Get the plugin version.
        
        Returns:
            Version of the plugin
        """
        pass


class IValidationRule(ABC):
    """
    Base interface for validation rules.
    
    Defines the contract that validation rules must implement.
    """
    
    @abstractmethod
    def validate(self, data: Any, **context) -> bool:
        """
        Validates data according to the rule.
        
        Args:
            data: Data to validate
            **context: Validation context
            
        Returns:
            True if data is valid
            
        Raises:
            ValidationError: If data is not valid
        """
        pass
    
    @abstractmethod
    def get_error_message(self) -> str:
        """
        Gets the error message of the rule.
        
        Returns:
            Error message
        """
        pass


class IDataProcessor(ABC):
    """
    Base interface for data processors.
    
    Defines the contract that must be implemented by components
    responsible for processing project data.
    """
    
    @abstractmethod
    def process(self, data: Any, **options) -> Any:
        """
        Processes the data.
        
        Args:
            data: Data to process
            **options: Processing options
            
        Returns:
            Processed data
            
        Raises:
            SimulatorException: If there are problems processing the data
        """
        pass
    
    @abstractmethod
    def get_processor_name(self) -> str:
        """
        Gets the name of the processor.
        
        Returns:
            Name of the processor
        """
        pass


# Data classes for the interfaces
@dataclass
class ProjectData:
    """
    Data of a project loaded from a file.
    
    Contains all the information needed to create
    a project in the simulator.
    """
    
    tasks: List[Task]
    resources: List[Resource]
    teams: List[Team]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.tasks:
            raise ValueError("The project must have at least one task")
        
        if not self.resources:
            raise ValueError("The project must have at least one resource")


@dataclass
class SimulationResult:
    """
    Simulation result.
    
    Contains metrics and data generated during
    simulation execution.
    """
    
    simulation_id: int
    total_steps: int
    completion_percentage: float
    total_cost: float
    total_duration: float
    metrics: Dict[str, Any]
    task_results: List[Dict[str, Any]]
    resource_utilization: Dict[int, float]
    
    def __post_init__(self):
        """Post-initialization validation."""
        if self.simulation_id < 0:
            raise ValueError("simulation_id must be >= 0")
        
        if not 0 <= self.completion_percentage <= 100:
            raise ValueError("completion_percentage must be between 0 and 100")


@dataclass
class EventInfo:
    """
    Information about an event.
    
    Contains details of an event that occurred
    during simulation.
    """
    
    event_type: str
    timestamp: int
    description: str
    impact: Dict[str, Any]
    affected_entities: List[str]
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.event_type.strip():
            raise ValueError("event_type cannot be empty")
        
        if self.timestamp < 0:
            raise ValueError("timestamp must be >= 0")
        
        if not self.description.strip():
            raise ValueError("description cannot be empty")