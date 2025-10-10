"""
Módulo de lectores de proyectos mejorado.

Este módulo contiene el sistema mejorado de lectores
con Factory pattern y validación post-carga.
"""

from .factory import (
    ReaderFactory,
    reader_factory,
    create_reader,
    register_reader,
    get_supported_extensions,
    get_reader_types,
    get_reader_info,
    validate_reader,
    get_factory_stats
)

from .validator import (
    ProjectDataValidator,
    ValidationResult,
    project_data_validator,
    validate_project_data,
    add_validation_rule,
    add_custom_validator,
    get_validation_stats
)

from .base_reader_improved import BaseProjectReader

# Importar lectores existentes para registro automático
from .xml_reader import XmlProjectReader
from .mpxj_reader import MpxjProjectReader
from .aspose_reader import AsposeProjectReader

__all__ = [
    # Factory
    'ReaderFactory',
    'reader_factory',
    'create_reader',
    'register_reader',
    'get_supported_extensions',
    'get_reader_types',
    'get_reader_info',
    'validate_reader',
    'get_factory_stats',
    
    # Validator
    'ProjectDataValidator',
    'ValidationResult',
    'project_data_validator',
    'validate_project_data',
    'add_validation_rule',
    'add_custom_validator',
    'get_validation_stats',
    
    # Base Reader
    'BaseProjectReader',
    
    # Specific Readers
    'XmlProjectReader',
    'MpxjProjectReader',
    'AsposeProjectReader'
]
