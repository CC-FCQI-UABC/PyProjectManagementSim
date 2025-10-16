"""
-----------------------------------------------------------------
PyProjectManagementSim 1.0
Modelo computacional de gestión de proyectos en Python.
Autores: Manuel Castañón–Puga, Fernando Rosales Quiñones
Correo electrónico: {puga, fernando.rosales59}@uabc.edu.mx
Universidad Autónoma de Baja California
http://www.uabc.edu.mx
PyProjectManagementSim/core/readers/__init__.py
-----------------------------------------------------------------
"""

"""
Project readers module.

This module contains the improved reader system
with Factory pattern and post-load validation.
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

# Import existing readers for automatic registration
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
    
    # Specific Readers
    'XmlProjectReader',
    'MpxjProjectReader',
    'AsposeProjectReader'
]
