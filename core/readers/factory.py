"""
-----------------------------------------------------------------
PyProjectManagementSim 1.0
Modelo computacional de gestión de proyectos en Python.
Autores: Manuel Castañón–Puga, Fernando Rosales Quiñones
Correo electrónico: {puga, fernando.rosales59}@uabc.edu.mx
Universidad Autónoma de Baja California
http://www.uabc.edu.mx
PyProjectManagementSim/core/readers/factory.py
-----------------------------------------------------------------
"""

"""
Factory for project reader creation.

This module implements the Factory pattern for automatic
reader creation based on file type.
"""

from typing import Dict, Type, Optional, List, Any
from abc import ABC, abstractmethod
from pathlib import Path
import importlib
import logging
import inspect

from core.interfaces import IProjectReader, ProjectData
from core.exceptions import ReaderError, ValidationError
from core.config.logging_config import get_logger, log_with_context

logger = get_logger(__name__)


class ReaderFactory:
    """
    Factory for project reader creation.
    
    Implements the Factory pattern to create readers
    automatically based on file type.
    """
    
    def __init__(self):
        """Initialize the reader factory."""
        self._readers: Dict[str, Type[IProjectReader]] = {}
        self._file_extensions: Dict[str, str] = {}
        self._reader_configs: Dict[str, Dict[str, Any]] = {}
        
        logger.info("ReaderFactory initialized")
    
    def register_reader(
        self,
        reader_type: str,
        reader_class: Type[IProjectReader],
        supported_extensions: List[str],
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a new reader type.
        
        Args:
            reader_type: Reader type (e.g.: 'xml', 'mpxj')
            reader_class: Reader class
            supported_extensions: Supported file extensions
            config: Reader configuration
            
        Raises:
            ValidationError: If parameters are not valid
        """
        if not issubclass(reader_class, IProjectReader):
            raise ValidationError(
                f"reader_class must implement IProjectReader, received: {reader_class}",
                field="reader_class",
                value=reader_class
            )
        
        if not supported_extensions:
            raise ValidationError(
                "supported_extensions cannot be empty",
                field="supported_extensions",
                value=supported_extensions
            )
        
        # Register reader
        self._readers[reader_type] = reader_class
        self._reader_configs[reader_type] = config or {}
        
        # Register extensions
        for ext in supported_extensions:
            ext = ext.lower().lstrip('.')
            self._file_extensions[ext] = reader_type
        
        log_with_context(
            logger,
            logging.INFO,
            f"Reader registered: {reader_type}",
            context={
                'reader_type': reader_type,
                'reader_class': reader_class.__name__,
                'supported_extensions': supported_extensions,
                'config': config
            }
        )
    
    def create_reader(
        self,
        file_path: str,
        reader_type: Optional[str] = None,
        **kwargs
    ) -> IProjectReader:
        """
        Create a reader for a specific file.
        
        Args:
            file_path: Path to the project file
            reader_type: Reader type (optional, inferred from file)
            **kwargs: Additional parameters
            
        Returns:
            Reader instance
            
        Raises:
            ReaderError: If there are problems creating the reader
        """
        try:
            # Determine reader type
            if reader_type is None:
                reader_type = self._get_reader_type_from_file(file_path)
            
            if reader_type not in self._readers:
                raise ReaderError(
                    f"Reader type '{reader_type}' not supported",
                    context={
                        'file_path': file_path,
                        'reader_type': reader_type,
                        'available_readers': list(self._readers.keys())
                    }
                )
            
            # Get reader class
            reader_class = self._readers[reader_type]
            
            # Get configuration
            config = self._reader_configs.get(reader_type, {})
            
            # Combine configuration with kwargs
            all_params = {**config, **kwargs}
            
            # Create instance
            reader = reader_class(**all_params)
            
            log_with_context(
                logger,
                logging.DEBUG,
                f"Reader created: {reader_type}",
                context={
                    'file_path': file_path,
                    'reader_type': reader_type,
                    'reader_class': reader_class.__name__,
                    'parameters': all_params
                }
            )
            
            return reader
            
        except Exception as e:
            raise ReaderError(
                f"Error creating reader for '{file_path}': {e}",
                context={'file_path': file_path, 'reader_type': reader_type}
            ) from e
    
    def _get_reader_type_from_file(self, file_path: str) -> str:
        """
        Determine reader type based on file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Reader type
            
        Raises:
            ReaderError: If type cannot be determined
        """
        try:
            file_path = Path(file_path)
            extension = file_path.suffix.lower().lstrip('.')
            
            if extension not in self._file_extensions:
                raise ReaderError(
                    f"File extension '{extension}' not supported",
                    context={
                        'file_path': file_path,
                        'extension': extension,
                        'supported_extensions': list(self._file_extensions.keys())
                    }
                )
            
            return self._file_extensions[extension]
            
        except Exception as e:
            raise ReaderError(
                f"Error determining reader type: {e}",
                context={'file_path': file_path}
            ) from e
    
    def get_supported_extensions(self) -> List[str]:
        """
        Get all supported extensions.
        
        Returns:
            List of supported extensions
        """
        return list(self._file_extensions.keys())
    
    def get_reader_types(self) -> List[str]:
        """
        Get all registered reader types.
        
        Returns:
            List of reader types
        """
        return list(self._readers.keys())
    
    def get_reader_info(self, reader_type: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a reader type.
        
        Args:
            reader_type: Reader type
            
        Returns:
            Reader information or None
        """
        if reader_type not in self._readers:
            return None
        
        reader_class = self._readers[reader_type]
        config = self._reader_configs.get(reader_type, {})
        
        # Get supported extensions
        supported_extensions = [
            ext for ext, rt in self._file_extensions.items() 
            if rt == reader_type
        ]
        
        return {
            'reader_type': reader_type,
            'reader_class': reader_class.__name__,
            'supported_extensions': supported_extensions,
            'config': config,
            'description': getattr(reader_class, '__doc__', 'No description available')
        }
    
    def validate_reader(self, reader_type: str) -> List[str]:
        """
        Validate a registered reader type.
        
        Args:
            reader_type: Reader type
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if reader_type not in self._readers:
            errors.append(f"Reader type '{reader_type}' not found")
            return errors
        
        try:
            reader_class = self._readers[reader_type]
            
            # Check required methods
            required_methods = ['load', 'validate_data', 'get_supported_extensions']
            for method_name in required_methods:
                if not hasattr(reader_class, method_name):
                    errors.append(f"Method '{method_name}' not found in {reader_class.__name__}")
            
            # Check constructor parameters
            sig = inspect.signature(reader_class.__init__)
            for param_name, param in sig.parameters.items():
                if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                    continue
                if param_name != 'self' and param.default == inspect.Parameter.empty:
                    if param_name not in self._reader_configs.get(reader_type, {}):
                        errors.append(f"Required parameter '{param_name}' not specified")
            
        except Exception as e:
            errors.append(f"Error validating reader: {e}")
        
        return errors
    
    def get_factory_stats(self) -> Dict[str, Any]:
        """
        Get factory statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'total_readers': len(self._readers),
            'total_extensions': len(self._file_extensions),
            'reader_types': list(self._readers.keys()),
            'supported_extensions': list(self._file_extensions.keys()),
            'extension_mapping': self._file_extensions.copy()
        }
    
    def clear_registry(self) -> None:
        """Clear the reader registry."""
        self._readers.clear()
        self._file_extensions.clear()
        self._reader_configs.clear()
        logger.info("Reader registry cleared")


# Global factory instance
reader_factory = ReaderFactory()


# Convenience functions
def create_reader(file_path: str, reader_type: Optional[str] = None, **kwargs) -> IProjectReader:
    """Create a reader for a specific file."""
    return reader_factory.create_reader(file_path, reader_type, **kwargs)


def register_reader(
    reader_type: str,
    reader_class: Type[IProjectReader],
    supported_extensions: List[str],
    config: Optional[Dict[str, Any]] = None
) -> None:
    """Register a new reader type."""
    reader_factory.register_reader(reader_type, reader_class, supported_extensions, config)


def get_supported_extensions() -> List[str]:
    """Get all supported extensions."""
    return reader_factory.get_supported_extensions()


def get_reader_types() -> List[str]:
    """Get all registered reader types."""
    return reader_factory.get_reader_types()


def get_reader_info(reader_type: str) -> Optional[Dict[str, Any]]:
    """Get information about a reader type."""
    return reader_factory.get_reader_info(reader_type)


def validate_reader(reader_type: str) -> List[str]:
    """Validate a registered reader type."""
    return reader_factory.validate_reader(reader_type)


def get_factory_stats() -> Dict[str, Any]:
    """Get factory statistics."""
    return reader_factory.get_factory_stats()