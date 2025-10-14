"""
Base interfaces for the ABP simulator.

This module defines the main interfaces that must be implemented
by different simulator components, following the dependency
inversion principle.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Protocol, runtime_checkable
from dataclasses import dataclass

from core.entities import Task, Resource, Team, TaskStatus
from core.exceptions import SimulatorException


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
    Protocolo para asignadores de recursos.
    
    Define la interfaz que deben implementar los componentes
    responsables de asignar recursos a tareas.
    """
    
    def allocate_resource(
        self, 
        task: Task, 
        available_resources: List[Resource],
        **context
    ) -> Optional[Resource]:
        """
        Asigna un recurso a una tarea.
        
        Args:
            task: Tarea a la cual asignar recurso
            available_resources: Lista de recursos disponibles
            **context: Contexto adicional
            
        Returns:
            Recurso asignado o None si no se puede asignar
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
    Protocolo para gestores de eventos.
    
    Define la interfaz que deben implementar los componentes
    responsables de gestionar eventos aleatorios.
    """
    
    def should_trigger_event(self, **context) -> bool:
        """
        Determina si debe activarse un evento.
        
        Args:
            **context: Simulation context
            
        Returns:
            True si debe activarse un evento
        """
        ...
    
    def trigger_event(self, **context) -> Dict[str, Any]:
        """
        Activa un evento aleatorio.
        
        Args:
            **context: Simulation context
            
        Returns:
            Information about the triggered event
        """
        ...


@runtime_checkable
class IDependencyResolver(Protocol):
    """
    Protocolo para resolutores de dependencias.
    
    Define la interfaz que deben implementar los componentes
    responsables de resolver dependencias entre tareas.
    """
    
    def can_task_start(self, task: Task) -> bool:
        """
        Verifica si una tarea puede iniciarse.
        
        Args:
            task: Tarea a verificar
            
        Returns:
            True si la tarea puede iniciarse
        """
        ...
    
    def get_ready_tasks(self, tasks: List[Task]) -> List[Task]:
        """
        Gets tasks that are ready to start.
        
        Args:
            tasks: Lista de tareas a verificar
            
        Returns:
            Lista de tareas listas para iniciarse
        """
        ...


class IProjectReader(ABC):
    """
    Interfaz base para lectores de proyectos.
    
    Define el contrato que deben implementar todos los lectores
    de archivos de proyecto (MPP, XML, etc.).
    """
    
    @abstractmethod
    def load(self, file_path: str) -> 'ProjectData':
        """
        Carga un proyecto desde archivo.
        
        Args:
            file_path: Ruta al archivo del proyecto
            
        Returns:
            Datos del proyecto cargados
            
        Raises:
            ReaderError: Si hay problemas cargando el archivo
        """
        pass
    
    @abstractmethod
    def validate_data(self, data: 'ProjectData') -> bool:
        """
        Valida los datos del proyecto.
        
        Args:
            data: Datos del proyecto a validar
            
        Returns:
            True if data is valid
            
        Raises:
            ValidationError: If data is not valid
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Obtiene las extensiones de archivo soportadas.
        
        Returns:
            Lista de extensiones soportadas
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
        Asigna tareas a recursos.
        
        Args:
            tasks: Lista de tareas a asignar
            resources: Lista de recursos disponibles
            
        Returns:
            Diccionario mapeando task_id -> resource_id
            
        Raises:
            StrategyError: If there are problems with assignment
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """
        Obtiene el nombre de la estrategia.
        
        Returns:
            Nombre de la estrategia
        """
        pass
    
    @abstractmethod
    def get_strategy_description(self) -> str:
        """
        Gets the strategy description.
        
        Returns:
            Strategy description
        """
        pass


class IOutputManager(ABC):
    """
    Interfaz base para gestores de salida.
    
    Define el contrato que deben implementar los componentes
    responsables de generar y guardar resultados.
    """
    
    @abstractmethod
    def save_results(self, data: Any, output_path: str, **options) -> None:
        """
        Guarda resultados en archivo.
        
        Args:
            data: Datos a guardar
            output_path: Ruta donde guardar
            **options: Opciones adicionales
            
        Raises:
            OutputError: Si hay problemas guardando
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """
        Obtiene los formatos de salida soportados.
        
        Returns:
            Lista de formatos soportados
        """
        pass


class IPlugin(ABC):
    """
    Interfaz base para plugins del simulador.
    
    Define el contrato que deben implementar todos los plugins
    del sistema.
    """
    
    @abstractmethod
    def initialize(self, **config) -> None:
        """
        Inicializa el plugin.
        
        Args:
            **config: Plugin configuration
            
        Raises:
            PluginError: Si hay problemas inicializando
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """
        Limpia recursos del plugin.
        
        Raises:
            PluginError: Si hay problemas limpiando
        """
        pass
    
    @abstractmethod
    def get_plugin_name(self) -> str:
        """
        Obtiene el nombre del plugin.
        
        Returns:
            Nombre del plugin
        """
        pass
    
    @abstractmethod
    def get_plugin_version(self) -> str:
        """
        Gets the plugin version.
        
        Returns:
            Plugin version
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
            data: Datos a validar
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
        Obtiene el mensaje de error de la regla.
        
        Returns:
            Mensaje de error
        """
        pass


class IDataProcessor(ABC):
    """
    Interfaz base para procesadores de datos.
    
    Define el contrato que deben implementar los componentes
    responsables de procesar datos del proyecto.
    """
    
    @abstractmethod
    def process(self, data: Any, **options) -> Any:
        """
        Procesa los datos.
        
        Args:
            data: Datos a procesar
            **options: Opciones de procesamiento
            
        Returns:
            Datos procesados
            
        Raises:
            SimulatorException: Si hay problemas procesando
        """
        pass
    
    @abstractmethod
    def get_processor_name(self) -> str:
        """
        Obtiene el nombre del procesador.
        
        Returns:
            Nombre del procesador
        """
        pass


# Clases de datos para las interfaces
@dataclass
class ProjectData:
    """
    Datos de un proyecto cargado desde archivo.
    
    Contains all the information needed to create
    un proyecto en el simulador.
    """
    
    tasks: List[Task]
    resources: List[Resource]
    teams: List[Team]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        """Post-initialization validation."""
        if not self.tasks:
            raise ValueError("El proyecto debe tener al menos una tarea")
        
        if not self.resources:
            raise ValueError("El proyecto debe tener al menos un recurso")


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
            raise ValueError("simulation_id debe ser >= 0")
        
        if not 0 <= self.completion_percentage <= 100:
            raise ValueError("completion_percentage debe estar entre 0 y 100")


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
            raise ValueError("timestamp debe ser >= 0")
        
        if not self.description.strip():
            raise ValueError("description cannot be empty")