"""
-----------------------------------------------------------------
PyProjectManagementSim 1.0
Modelo computacional de gestión de proyectos en Python.
Autores: Manuel Castañón–Puga, Fernando Rosales Quiñones
Correo electrónico: {puga, fernando.rosales59}@uabc.edu.mx
Universidad Autónoma de Baja California
http://www.uabc.edu.mx
PyProjectManagementSim/core/config/__init__.py
-----------------------------------------------------------------

"""

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
    """ Available logging levels """
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
    """ Available reader types """
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
                "max_steps must be >= 1",
                field="max_steps",
                value=self.max_steps
            )
        
        if not 0 <= self.error_margin <= 1:
            raise ValidationError(
                "error_margin must be between 0 and 1",
                field="error_margin",
                value=self.error_margin
            )
        
        if self.reassignment_frequency < 0:
            raise ValidationError(
                "reassignment_frequency must be >= 0",
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
                "num_simulations must be >= 1",
                field="num_simulations",
                value=self.num_simulations
            )
        
        if self.display_limit < 1:
            raise ValidationError(
                "display_limit must be >= 1",
                field="display_limit",
                value=self.display_limit
            )
        
        # Validate output formats
        valid_formats = ["csv", "json", "excel", "parquet"]
        for fmt in self.output_formats:
            if fmt not in valid_formats:
                raise ValidationError(
                    f"Invalid output format: {fmt}",
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
                "resource_id must be > 0",
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
                "cost_per_hour must be >= 0",
                field="cost_per_hour",
                value=self.cost_per_hour
            )
        
        if not 0 <= self.efficiency <= 2:
            raise ValidationError(
                "efficiency must be between 0 and 2",
                field="efficiency",
                value=self.efficiency
            )
        
        if not 0 <= self.availability <= 1:
            raise ValidationError(
                "availability must be between 0 and 1",
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
                "team_id must be > 0",
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
                "initial_morale must be between 0 and 1",
                field="initial_morale",
                value=self.initial_morale
            )
        
        if not 0 <= self.initial_cohesion <= 1:
            raise ValidationError(
                "initial_cohesion must be between 0 and 1",
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
                        f"Unsupported file format: {config_path.suffix}",
                        field="config_path",
                        value=str(config_path)
                    )
            
            self._core_config = CoreConfig(**data)
            logger.info(f"Core configuration loaded from {config_path}")
            return self._core_config
            
        except Exception as e:
            raise ConfigurationError(
                f"Error loading core configuration: {e}",
                field="config_path",
                value=str(config_path)
            ) from e
    
    def load_experiment_config(self, config_path: Union[str, Path]) -> ExperimentConfig:
        """
        Loads experiment configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Loaded experiment configuration
            
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
                        f"Unsupported file format: {config_path.suffix}",
                        field="config_path",
                        value=str(config_path)
                    )
            
            # Process nested simulation configuration
            if 'simulation_config' in data:
                sim_data = data['simulation_config']
                data['simulation_config'] = SimulationConfig(**sim_data)
            
            self._experiment_config = ExperimentConfig(**data)
            logger.info(f"Experiment configuration loaded from {config_path}")
            return self._experiment_config
            
        except Exception as e:
            raise ConfigurationError(
                f"Error loading experiment configuration: {e}",
                field="config_path",
                value=str(config_path)
            ) from e
    
    def save_config(self, config: Union[CoreConfig, SimulationConfig, ExperimentConfig], 
                   config_path: Union[str, Path]) -> None:
        """
        Saves a configuration to file.
        
        Args:
            config: Configuration to save
            config_path: Path to save the configuration
            
        Raises:
            ConfigurationError: If there are problems saving the configuration
        """
        try:
            config_path = Path(config_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert dataclass to dictionary
            data = self._dataclass_to_dict(config)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.json':
                    json.dump(data, f, indent=2, ensure_ascii=False)
                elif config_path.suffix.lower() in ['.yml', '.yaml']:
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
                else:
                    raise ConfigurationError(
                        f"Unsupported file format: {config_path.suffix}",
                        field="config_path",
                        value=str(config_path)
                    )
            
            logger.info(f"Configuration saved to {config_path}")
            
        except Exception as e:
            raise ConfigurationError(
                f"Error saving configuration: {e}",
                field="config_path",
                value=str(config_path)
            ) from e
    
    def _dataclass_to_dict(self, obj: Any) -> Dict[str, Any]:
        """
        Converts a dataclass to a dictionary recursively.
        
        Args:
            obj: dataclass object to convert
            
        Returns:
            Dictionary with the object data
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
        Validates a configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if the configuration is valid
            
        Raises:
            ValidationError: If the configuration is not valid
        """
        try:
            # The validation is done in __post_init__ of each dataclass
            # We only verify that a new instance can be created
            config_type = type(config)
            config_type(**self._dataclass_to_dict(config))
            return True
        except Exception as e:
            raise ValidationError(
                f"Invalid configuration: {e}",
                field="config",
                value=str(config)
            ) from e


# Global instance of the configuration manager
config_manager = ConfigManager()


def get_core_config() -> CoreConfig:
    """Gets the core configuration."""
    return config_manager.core_config


def get_simulation_config() -> SimulationConfig:
    """Gets the simulation configuration."""
    return config_manager.simulation_config


def get_experiment_config() -> ExperimentConfig:
    """Gets the experiment configuration."""
    return config_manager.experiment_config