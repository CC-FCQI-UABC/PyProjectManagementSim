"""
Lector base mejorado para proyectos.

Este módulo contiene la implementación base mejorada
para lectores de proyectos con validación automática.
"""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from pathlib import Path

from core.interfaces import IProjectReader, ProjectData
from core.exceptions import ReaderError, ValidationError
from core.config.logging_config import get_logger, log_with_context
from .validator import project_data_validator, ValidationResult

logger = get_logger(__name__)


class BaseProjectReader(IProjectReader):
    """
    Lector base mejorado para proyectos.
    
    Proporciona funcionalidad común para todos los lectores
    incluyendo validación automática y manejo de errores.
    """
    
    def __init__(self, **config):
        """
        Inicializa el lector base.
        
        Args:
            **config: Configuración del lector
        """
        self.config = config
        self._validation_enabled = config.get('validation_enabled', True)
        self._strict_validation = config.get('strict_validation', True)
        
        logger.info(f"{self.__class__.__name__} inicializado")
    
    def load(self, file_path: str) -> ProjectData:
        """
        Carga un proyecto desde archivo con validación automática.
        
        Args:
            file_path: Ruta al archivo del proyecto
            
        Returns:
            Datos del proyecto cargados
            
        Raises:
            ReaderError: Si hay problemas cargando el archivo
        """
        try:
            # Validar archivo
            self._validate_file_path(file_path)
            
            # Cargar datos específicos del lector
            project_data = self._load_specific(file_path)
            
            # Validar datos si está habilitado
            if self._validation_enabled:
                validation_result = self._validate_loaded_data(project_data)
                
                if not validation_result.is_valid:
                    error_msg = f"Datos del proyecto no válidos: {validation_result.errors}"
                    
                    if self._strict_validation:
                        raise ValidationError(error_msg)
                    else:
                        logger.warning(f"Advertencias de validación: {validation_result.warnings}")
            
            log_with_context(
                logger,
                logger.info,
                f"Proyecto cargado exitosamente",
                context={
                    'file_path': file_path,
                    'tasks_count': len(project_data.tasks),
                    'resources_count': len(project_data.resources),
                    'teams_count': len(project_data.teams),
                    'validation_enabled': self._validation_enabled
                }
            )
            
            return project_data
            
        except Exception as e:
            raise ReaderError(
                f"Error cargando proyecto desde '{file_path}': {e}",
                context={'file_path': file_path}
            ) from e
    
    def validate_data(self, data: ProjectData) -> bool:
        """
        Valida los datos del proyecto.
        
        Args:
            data: Datos del proyecto a validar
            
        Returns:
            True si los datos son válidos
            
        Raises:
            ValidationError: Si los datos no son válidos
        """
        try:
            validation_result = project_data_validator.validate_project_data(data)
            
            if not validation_result.is_valid:
                raise ValidationError(
                    f"Datos del proyecto no válidos: {validation_result.errors}"
                )
            
            return True
            
        except Exception as e:
            raise ValidationError(
                f"Error validando datos del proyecto: {e}"
            ) from e
    
    def get_supported_extensions(self) -> List[str]:
        """
        Obtiene las extensiones de archivo soportadas.
        
        Returns:
            Lista de extensiones soportadas
        """
        return self._get_supported_extensions()
    
    def _validate_file_path(self, file_path: str) -> None:
        """
        Valida la ruta del archivo.
        
        Args:
            file_path: Ruta al archivo
            
        Raises:
            ReaderError: Si la ruta no es válida
        """
        if not file_path or not file_path.strip():
            raise ReaderError(
                "Ruta de archivo no puede estar vacía",
                context={'file_path': file_path}
            )
        
        path = Path(file_path)
        
        if not path.exists():
            raise ReaderError(
                f"Archivo no encontrado: {file_path}",
                context={'file_path': file_path}
            )
        
        if not path.is_file():
            raise ReaderError(
                f"La ruta no es un archivo: {file_path}",
                context={'file_path': file_path}
            )
        
        if path.stat().st_size == 0:
            raise ReaderError(
                f"El archivo está vacío: {file_path}",
                context={'file_path': file_path}
            )
    
    def _validate_loaded_data(self, data: ProjectData) -> ValidationResult:
        """
        Valida los datos cargados.
        
        Args:
            data: Datos del proyecto
            
        Returns:
            Resultado de la validación
        """
        return project_data_validator.validate_project_data(data)
    
    def _load_specific(self, file_path: str) -> ProjectData:
        """
        Carga datos específicos del tipo de archivo.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            Datos del proyecto cargados
            
        Raises:
            NotImplementedError: Si no está implementado
        """
        raise NotImplementedError(
            f"Subclase {self.__class__.__name__} debe implementar _load_specific"
        )
    
    @abstractmethod
    def _get_supported_extensions(self) -> List[str]:
        """
        Obtiene las extensiones soportadas específicas del lector.
        
        Returns:
            Lista de extensiones soportadas
        """
        pass
    
    def get_reader_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración del lector.
        
        Returns:
            Diccionario con la configuración
        """
        return self.config.copy()
    
    def update_config(self, **new_config) -> None:
        """
        Actualiza la configuración del lector.
        
        Args:
            **new_config: Nuevos valores de configuración
        """
        self.config.update(new_config)
        
        # Actualizar configuración específica
        if 'validation_enabled' in new_config:
            self._validation_enabled = new_config['validation_enabled']
        
        if 'strict_validation' in new_config:
            self._strict_validation = new_config['strict_validation']
        
        logger.debug(f"Configuración actualizada: {new_config}")
    
    def get_reader_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del lector.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'reader_class': self.__class__.__name__,
            'supported_extensions': self.get_supported_extensions(),
            'config': self.config,
            'validation_enabled': self._validation_enabled,
            'strict_validation': self._strict_validation
        }
