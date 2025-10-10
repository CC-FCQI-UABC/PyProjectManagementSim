"""
Factory para la creación de lectores de proyectos.

Este módulo implementa el patrón Factory para la creación
automática de lectores basándose en el tipo de archivo.
"""

from typing import Dict, Type, Optional, List, Any
from abc import ABC, abstractmethod
from pathlib import Path
import importlib
import inspect

from core.interfaces import IProjectReader, ProjectData
from core.exceptions import ReaderError, ValidationError
from core.config.logging_config import get_logger, log_with_context

logger = get_logger(__name__)


class ReaderFactory:
    """
    Factory para la creación de lectores de proyectos.
    
    Implementa el patrón Factory para crear lectores
    automáticamente basándose en el tipo de archivo.
    """
    
    def __init__(self):
        """Inicializa el factory de lectores."""
        self._readers: Dict[str, Type[IProjectReader]] = {}
        self._file_extensions: Dict[str, str] = {}
        self._reader_configs: Dict[str, Dict[str, Any]] = {}
        
        logger.info("ReaderFactory inicializado")
    
    def register_reader(
        self,
        reader_type: str,
        reader_class: Type[IProjectReader],
        supported_extensions: List[str],
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra un nuevo tipo de lector.
        
        Args:
            reader_type: Tipo de lector (ej: 'xml', 'mpxj')
            reader_class: Clase del lector
            supported_extensions: Extensiones de archivo soportadas
            config: Configuración del lector
            
        Raises:
            ValidationError: Si los parámetros no son válidos
        """
        if not issubclass(reader_class, IProjectReader):
            raise ValidationError(
                f"reader_class debe implementar IProjectReader, recibido: {reader_class}",
                field="reader_class",
                value=reader_class
            )
        
        if not supported_extensions:
            raise ValidationError(
                "supported_extensions no puede estar vacío",
                field="supported_extensions",
                value=supported_extensions
            )
        
        # Registrar lector
        self._readers[reader_type] = reader_class
        self._reader_configs[reader_type] = config or {}
        
        # Registrar extensiones
        for ext in supported_extensions:
            ext = ext.lower().lstrip('.')
            self._file_extensions[ext] = reader_type
        
        log_with_context(
            logger,
            logger.info,
            f"Lector registrado: {reader_type}",
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
        Crea un lector para un archivo específico.
        
        Args:
            file_path: Ruta al archivo del proyecto
            reader_type: Tipo de lector (opcional, se infiere del archivo)
            **kwargs: Parámetros adicionales
            
        Returns:
            Instancia del lector
            
        Raises:
            ReaderError: Si hay problemas creando el lector
        """
        try:
            # Determinar tipo de lector
            if reader_type is None:
                reader_type = self._get_reader_type_from_file(file_path)
            
            if reader_type not in self._readers:
                raise ReaderError(
                    f"Tipo de lector '{reader_type}' no soportado",
                    context={
                        'file_path': file_path,
                        'reader_type': reader_type,
                        'available_readers': list(self._readers.keys())
                    }
                )
            
            # Obtener clase del lector
            reader_class = self._readers[reader_type]
            
            # Obtener configuración
            config = self._reader_configs.get(reader_type, {})
            
            # Combinar configuración con kwargs
            all_params = {**config, **kwargs}
            
            # Crear instancia
            reader = reader_class(**all_params)
            
            log_with_context(
                logger,
                logger.debug,
                f"Lector creado: {reader_type}",
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
                f"Error creando lector para '{file_path}': {e}",
                context={'file_path': file_path, 'reader_type': reader_type}
            ) from e
    
    def _get_reader_type_from_file(self, file_path: str) -> str:
        """
        Determina el tipo de lector basándose en la extensión del archivo.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Tipo de lector
            
        Raises:
            ReaderError: Si no se puede determinar el tipo
        """
        try:
            file_path = Path(file_path)
            extension = file_path.suffix.lower().lstrip('.')
            
            if extension not in self._file_extensions:
                raise ReaderError(
                    f"Extensión de archivo '{extension}' no soportada",
                    context={
                        'file_path': file_path,
                        'extension': extension,
                        'supported_extensions': list(self._file_extensions.keys())
                    }
                )
            
            return self._file_extensions[extension]
            
        except Exception as e:
            raise ReaderError(
                f"Error determinando tipo de lector: {e}",
                context={'file_path': file_path}
            ) from e
    
    def get_supported_extensions(self) -> List[str]:
        """
        Obtiene todas las extensiones soportadas.
        
        Returns:
            Lista de extensiones soportadas
        """
        return list(self._file_extensions.keys())
    
    def get_reader_types(self) -> List[str]:
        """
        Obtiene todos los tipos de lectores registrados.
        
        Returns:
            Lista de tipos de lectores
        """
        return list(self._readers.keys())
    
    def get_reader_info(self, reader_type: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información sobre un tipo de lector.
        
        Args:
            reader_type: Tipo de lector
            
        Returns:
            Información del lector o None
        """
        if reader_type not in self._readers:
            return None
        
        reader_class = self._readers[reader_type]
        config = self._reader_configs.get(reader_type, {})
        
        # Obtener extensiones soportadas
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
        Valida un tipo de lector registrado.
        
        Args:
            reader_type: Tipo de lector
            
        Returns:
            Lista de errores de validación
        """
        errors = []
        
        if reader_type not in self._readers:
            errors.append(f"Tipo de lector '{reader_type}' no encontrado")
            return errors
        
        try:
            reader_class = self._readers[reader_type]
            
            # Verificar métodos requeridos
            required_methods = ['load', 'validate_data', 'get_supported_extensions']
            for method_name in required_methods:
                if not hasattr(reader_class, method_name):
                    errors.append(f"Método '{method_name}' no encontrado en {reader_class.__name__}")
            
            # Verificar parámetros de constructor
            sig = inspect.signature(reader_class.__init__)
            for param_name, param in sig.parameters.items():
                if param_name != 'self' and param.default == inspect.Parameter.empty:
                    if param_name not in self._reader_configs.get(reader_type, {}):
                        errors.append(f"Parámetro requerido '{param_name}' no especificado")
            
        except Exception as e:
            errors.append(f"Error validando lector: {e}")
        
        return errors
    
    def get_factory_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del factory.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'total_readers': len(self._readers),
            'total_extensions': len(self._file_extensions),
            'reader_types': list(self._readers.keys()),
            'supported_extensions': list(self._file_extensions.keys()),
            'extension_mapping': self._file_extensions.copy()
        }
    
    def clear_registry(self) -> None:
        """Limpia el registro de lectores."""
        self._readers.clear()
        self._file_extensions.clear()
        self._reader_configs.clear()
        logger.info("Registro de lectores limpiado")


# Instancia global del factory
reader_factory = ReaderFactory()


# Funciones de conveniencia
def create_reader(file_path: str, reader_type: Optional[str] = None, **kwargs) -> IProjectReader:
    """Crea un lector para un archivo específico."""
    return reader_factory.create_reader(file_path, reader_type, **kwargs)


def register_reader(
    reader_type: str,
    reader_class: Type[IProjectReader],
    supported_extensions: List[str],
    config: Optional[Dict[str, Any]] = None
) -> None:
    """Registra un nuevo tipo de lector."""
    reader_factory.register_reader(reader_type, reader_class, supported_extensions, config)


def get_supported_extensions() -> List[str]:
    """Obtiene todas las extensiones soportadas."""
    return reader_factory.get_supported_extensions()


def get_reader_types() -> List[str]:
    """Obtiene todos los tipos de lectores registrados."""
    return reader_factory.get_reader_types()


def get_reader_info(reader_type: str) -> Optional[Dict[str, Any]]:
    """Obtiene información sobre un tipo de lector."""
    return reader_factory.get_reader_info(reader_type)


def validate_reader(reader_type: str) -> List[str]:
    """Valida un tipo de lector registrado."""
    return reader_factory.validate_reader(reader_type)


def get_factory_stats() -> Dict[str, Any]:
    """Obtiene estadísticas del factory."""
    return reader_factory.get_factory_stats()
