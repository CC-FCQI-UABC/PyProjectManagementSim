"""
Centralized configuration system for the ABP simulator.

This module provides well-typed configuration classes
with automatic validation using dataclasses and type hints.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import json
import yaml
from enum import Enum

from core.exceptions import ConfigurationError, ValidationError
from core.config.logging_config import get_logger

logger = get_logger(__name__)


class LogLevel(Enum):
    """Niveles de logging disponibles."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AssignmentStrategy(Enum):
    """Available assignment strategies."""
    GREEDY = "greedy"
    ROUND_ROBIN = "round_robin"
    PRIORITY_BASED = "priority_based"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    CRITICAL_PATH = "critical_path"


class ReaderType(Enum):
    """Tipos de lectores disponibles."""
    XML = "xml"
    MPXJ = "mpxj"
    ASPOSE = "aspose"


@dataclass
class CoreConfig:
    """
    Global framework configuration.
    
    Contains configurations that affect the entire simulator.
    """
    
    # Logging configuration
    log_level: LogLevel = LogLevel.INFO
    log_file: Optional[str] = None
    structured_logging: bool = False
    colored_logging: bool = True
    
    # Performance configuration
    max_concurrent_simulations: int = 4
    memory_limit_mb: int = 1024
    
    # Validation configuration
    strict_validation: bool = True
    validate_dependencies: bool = True
    validate_resources: bool = True
    
    # Plugin configuration
    plugins_enabled: bool = True
    plugins_directory: str = "plugins"
    
    def __post_init__(self):
        """Post-initialization validation."""
        if self.max_concurrent_simulations < 1:
            raise ValidationError(
                "max_concurrent_simulations debe ser >= 1",
                field="max_concurrent_simulations",
                value=self.max_concurrent_simulations
            )
        
        if self.memory_limit_mb < 100:
            raise ValidationError(
                "memory_limit_mb debe ser >= 100",
                field="memory_limit_mb",
                value=self.memory_limit_mb
            )


@dataclass
class SimulationConfig:
    """
    Simulation-specific configuration.
    
    Contains parameters that affect simulation behavior.
    """
    
    # Basic parameters
    max_steps: int = 3000
    error_margin: float = 0.15
    reassignment_frequency: int = 0
    
    # Team configuration
    team_morale_decay_rate: float = 0.02
    team_cohesion_regression_rate: float = 0.01
    team_morale_boost_on_completion: float = 0.1
    
    # Random event configuration
    random_events_enabled: bool = True
    random_event_probability: float = 0.02
    random_event_morale_impact: float = 0.3
    
    # Metrics configuration
    collect_detailed_metrics: bool = True
    metrics_collection_interval: int = 1
    
    def __post_init__(self):
        """Post-initialization validation."""
        if self.max_steps < 1:
            raise ValidationError(
                "max_steps debe ser >= 1",
                field="max_steps",
                value=self.max_steps
            )
        
        if not 0 <= self.error_margin <= 1:
            raise ValidationError(
                "error_margin debe estar entre 0 y 1",
                field="error_margin",
                value=self.error_margin
            )
        
        if self.reassignment_frequency < 0:
            raise ValidationError(
                "reassignment_frequency debe ser >= 0",
                field="reassignment_frequency",
                value=self.reassignment_frequency
            )


@dataclass
class ExperimentConfig:
    """
    Experiment configuration.
    
    Contains specific parameters for running experiments
    with multiple simulations.
    """
    
    # Files and data
    project_file: str = "project.xml"
    data_directory: str = "data"
    output_directory: str = "results"
    
    # Reader configuration
    reader_type: ReaderType = ReaderType.XML
    
    # Resource configuration
    resources_definition: List[Dict[str, Any]] = field(default_factory=list)
    
    # Team configuration
    team_definitions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Simulation configuration
    simulation_config: SimulationConfig = field(default_factory=SimulationConfig)
    
    # Experiment configuration
    num_simulations: int = 5
    assignment_strategy: AssignmentStrategy = AssignmentStrategy.GREEDY
    
    # Output configuration
    output_filename_base: str = "simulation_results"
    add_timestamp_to_filename: bool = True
    output_formats: List[str] = field(default_factory=lambda: ["csv"])
    
    # Visualization configuration
    show_loaded_tasks: bool = False
    show_loaded_resources: bool = False
    display_limit: int = 20
    print_summary: bool = True
    
    def __post_init__(self):
        """Post-initialization validation."""
        if self.num_simulations < 1:
            raise ValidationError(
                "num_simulations debe ser >= 1",
                field="num_simulations",
                value=self.num_simulations
            )
        
        if self.display_limit < 1:
            raise ValidationError(
                "display_limit debe ser >= 1",
                field="display_limit",
                value=self.display_limit
            )
        
        # Validar formatos de salida
        valid_formats = ["csv", "json", "excel", "parquet"]
        for fmt in self.output_formats:
            if fmt not in valid_formats:
                raise ValidationError(
                    f"Formato de salida no válido: {fmt}",
                    field="output_formats",
                    value=fmt
                )


@dataclass
class ResourceConfig:
    """
    Resource configuration.
    
    Defines the properties of an individual resource.
    """
    
    resource_id: int
    name: str
    cost_per_hour: float
    efficiency: float = 1.0
    availability: float = 1.0
    skills: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation."""
        if self.resource_id <= 0:
            raise ValidationError(
                "resource_id debe ser > 0",
                field="resource_id",
                value=self.resource_id
            )
        
        if not self.name.strip():
            raise ValidationError(
                "name cannot be empty",
                field="name",
                value=self.name
            )
        
        if self.cost_per_hour < 0:
            raise ValidationError(
                "cost_per_hour debe ser >= 0",
                field="cost_per_hour",
                value=self.cost_per_hour
            )
        
        if not 0 <= self.efficiency <= 2:
            raise ValidationError(
                "efficiency debe estar entre 0 y 2",
                field="efficiency",
                value=self.efficiency
            )
        
        if not 0 <= self.availability <= 1:
            raise ValidationError(
                "availability debe estar entre 0 y 1",
                field="availability",
                value=self.availability
            )


@dataclass
class TeamConfig:
    """
    Team configuration.
    
    Defines the properties of a work team.
    """
    
    team_id: int
    name: str
    member_resource_ids: List[int]
    initial_morale: float = 0.8
    initial_cohesion: float = 0.7
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation."""
        if self.team_id <= 0:
            raise ValidationError(
                "team_id debe ser > 0",
                field="team_id",
                value=self.team_id
            )
        
        if not self.name.strip():
            raise ValidationError(
                "name cannot be empty",
                field="name",
                value=self.name
            )
        
        if not self.member_resource_ids:
            raise ValidationError(
                "member_resource_ids cannot be empty",
                field="member_resource_ids",
                value=self.member_resource_ids
            )
        
        if not 0 <= self.initial_morale <= 1:
            raise ValidationError(
                "initial_morale debe estar entre 0 y 1",
                field="initial_morale",
                value=self.initial_morale
            )
        
        if not 0 <= self.initial_cohesion <= 1:
            raise ValidationError(
                "initial_cohesion debe estar entre 0 y 1",
                field="initial_cohesion",
                value=self.initial_cohesion
            )


class ConfigManager:
    """
    Simulator configuration manager.
    
    Provides methods to load, validate and manage
    configurations from different sources.
    """
    
    def __init__(self):
        """Initializes the configuration manager."""
        self._core_config: Optional[CoreConfig] = None
        self._simulation_config: Optional[SimulationConfig] = None
        self._experiment_config: Optional[ExperimentConfig] = None
    
    @property
    def core_config(self) -> CoreConfig:
        """Gets the core configuration."""
        if self._core_config is None:
            self._core_config = CoreConfig()
        return self._core_config
    
    @property
    def simulation_config(self) -> SimulationConfig:
        """Gets the simulation configuration."""
        if self._simulation_config is None:
            self._simulation_config = SimulationConfig()
        return self._simulation_config
    
    @property
    def experiment_config(self) -> ExperimentConfig:
        """Gets the experiment configuration."""
        if self._experiment_config is None:
            self._experiment_config = ExperimentConfig()
        return self._experiment_config
    
    def load_core_config(self, config_path: Union[str, Path]) -> CoreConfig:
        """
        Loads core configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Loaded core configuration
            
        Raises:
            ConfigurationError: If there are problems loading the configuration
        """
        try:
            config_path = Path(config_path)
            
            if not config_path.exists():
                raise ConfigurationError(
                    f"Configuration file not found: {config_path}",
                    field="config_path",
                    value=str(config_path)
                )
            
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.json':
                    data = json.load(f)
                elif config_path.suffix.lower() in ['.yml', '.yaml']:
                    data = yaml.safe_load(f)
                else:
                    raise ConfigurationError(
                        f"Formato de archivo no soportado: {config_path.suffix}",
                        field="config_path",
                        value=str(config_path)
                    )
            
            self._core_config = CoreConfig(**data)
            logger.info(f"Configuración del core cargada desde {config_path}")
            return self._core_config
            
        except Exception as e:
            raise ConfigurationError(
                f"Error cargando configuración del core: {e}",
                field="config_path",
                value=str(config_path)
            ) from e
    
    def load_experiment_config(self, config_path: Union[str, Path]) -> ExperimentConfig:
        """
        Carga la configuración de experimento desde archivo.
        
        Args:
            config_path: Ruta al archivo de configuración
            
        Returns:
            Configuración de experimento cargada
            
        Raises:
            ConfigurationError: Si hay problemas cargando la configuración
        """
        try:
            config_path = Path(config_path)
            
            if not config_path.exists():
                raise ConfigurationError(
                    f"Configuration file not found: {config_path}",
                    field="config_path",
                    value=str(config_path)
                )
            
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.json':
                    data = json.load(f)
                elif config_path.suffix.lower() in ['.yml', '.yaml']:
                    data = yaml.safe_load(f)
                else:
                    raise ConfigurationError(
                        f"Formato de archivo no soportado: {config_path.suffix}",
                        field="config_path",
                        value=str(config_path)
                    )
            
            # Procesar configuración de simulación anidada
            if 'simulation_config' in data:
                sim_data = data['simulation_config']
                data['simulation_config'] = SimulationConfig(**sim_data)
            
            self._experiment_config = ExperimentConfig(**data)
            logger.info(f"Configuración de experimento cargada desde {config_path}")
            return self._experiment_config
            
        except Exception as e:
            raise ConfigurationError(
                f"Error cargando configuración de experimento: {e}",
                field="config_path",
                value=str(config_path)
            ) from e
    
    def save_config(self, config: Union[CoreConfig, SimulationConfig, ExperimentConfig], 
                   config_path: Union[str, Path]) -> None:
        """
        Guarda una configuración en archivo.
        
        Args:
            config: Configuración a guardar
            config_path: Ruta donde guardar la configuración
            
        Raises:
            ConfigurationError: Si hay problemas guardando la configuración
        """
        try:
            config_path = Path(config_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convertir dataclass a diccionario
            data = self._dataclass_to_dict(config)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.json':
                    json.dump(data, f, indent=2, ensure_ascii=False)
                elif config_path.suffix.lower() in ['.yml', '.yaml']:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
                else:
                    raise ConfigurationError(
                        f"Formato de archivo no soportado: {config_path.suffix}",
                        field="config_path",
                        value=str(config_path)
                    )
            
            logger.info(f"Configuración guardada en {config_path}")
            
        except Exception as e:
            raise ConfigurationError(
                f"Error guardando configuración: {e}",
                field="config_path",
                value=str(config_path)
            ) from e
    
    def _dataclass_to_dict(self, obj: Any) -> Dict[str, Any]:
        """
        Convierte un dataclass a diccionario recursivamente.
        
        Args:
            obj: Objeto dataclass a convertir
            
        Returns:
            Diccionario con los datos del objeto
        """
        if hasattr(obj, '__dataclass_fields__'):
            result = {}
            for field_name, field_info in obj.__dataclass_fields__.items():
                value = getattr(obj, field_name)
                if hasattr(value, '__dataclass_fields__'):
                    result[field_name] = self._dataclass_to_dict(value)
                elif isinstance(value, Enum):
                    result[field_name] = value.value
                elif isinstance(value, list):
                    result[field_name] = [
                        self._dataclass_to_dict(item) if hasattr(item, '__dataclass_fields__') else item
                        for item in value
                    ]
                else:
                    result[field_name] = value
            return result
        else:
            return obj
    
    def validate_config(self, config: Union[CoreConfig, SimulationConfig, ExperimentConfig]) -> bool:
        """
        Valida una configuración.
        
        Args:
            config: Configuración a validar
            
        Returns:
            True si la configuración es válida
            
        Raises:
            ValidationError: Si la configuración no es válida
        """
        try:
            # La validación se hace en __post_init__ de cada dataclass
            # Solo verificamos que se pueda crear una nueva instancia
            config_type = type(config)
            config_type(**self._dataclass_to_dict(config))
            return True
        except Exception as e:
            raise ValidationError(
                f"Configuración inválida: {e}",
                field="config",
                value=str(config)
            ) from e


# Instancia global del gestor de configuración
config_manager = ConfigManager()


def get_core_config() -> CoreConfig:
    """Obtiene la configuración del core."""
    return config_manager.core_config


def get_simulation_config() -> SimulationConfig:
    """Obtiene la configuración de simulación."""
    return config_manager.simulation_config


def get_experiment_config() -> ExperimentConfig:
    """Obtiene la configuración de experimento."""
    return config_manager.experiment_config