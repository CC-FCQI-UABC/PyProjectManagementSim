"""
Validador de datos de proyecto.

Este módulo contiene la lógica para validar los datos
del proyecto después de cargarlos desde archivo.
"""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from collections import defaultdict

from core.entities import Task, TaskStatus
from core.entities_extended import Resource, Team
from core.interfaces import ProjectData, IValidationRule
from core.exceptions import ValidationError, ReaderError
from core.config.logging_config import get_logger, log_with_context

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """
    Resultado de una validación.
    
    Contiene información sobre el resultado
    de una validación de datos.
    """
    
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    validated_entities: Dict[str, int]
    
    def __post_init__(self):
        """Validación post-inicialización."""
        if not isinstance(self.errors, list):
            self.errors = []
        if not isinstance(self.warnings, list):
            self.warnings = []
        if not isinstance(self.validated_entities, dict):
            self.validated_entities = {}


class ProjectDataValidator:
    """
    Validador de datos de proyecto.
    
    Implementa la lógica para validar la integridad
    y consistencia de los datos del proyecto.
    """
    
    def __init__(self):
        """Inicializa el validador de datos."""
        self._validation_rules: List[IValidationRule] = []
        self._custom_validators: List[callable] = []
        
        logger.info("ProjectDataValidator inicializado")
    
    def validate_project_data(self, data: ProjectData) -> ValidationResult:
        """
        Valida los datos del proyecto.
        
        Args:
            data: Datos del proyecto a validar
            
        Returns:
            Resultado de la validación
            
        Raises:
            ValidationError: Si hay problemas con la validación
        """
        try:
            errors = []
            warnings = []
            validated_entities = {
                'tasks': 0,
                'resources': 0,
                'teams': 0
            }
            
            # Validar entidades básicas
            self._validate_basic_entities(data, errors, warnings, validated_entities)
            
            # Validar integridad referencial
            self._validate_referential_integrity(data, errors, warnings)
            
            # Validar dependencias
            self._validate_dependencies(data, errors, warnings)
            
            # Validar recursos
            self._validate_resources(data, errors, warnings)
            
            # Validar equipos
            self._validate_teams(data, errors, warnings)
            
            # Validar reglas personalizadas
            self._validate_custom_rules(data, errors, warnings)
            
            # Validar validadores personalizados
            self._validate_custom_validators(data, errors, warnings)
            
            # Crear resultado
            result = ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                validated_entities=validated_entities
            )
            
            log_with_context(
                logger,
                logger.info,
                f"Validación de datos completada",
                context={
                    'is_valid': result.is_valid,
                    'errors_count': len(errors),
                    'warnings_count': len(warnings),
                    'validated_entities': validated_entities
                }
            )
            
            return result
            
        except Exception as e:
            raise ValidationError(
                f"Error validando datos del proyecto: {e}",
                context={'data': str(data)}
            ) from e
    
    def _validate_basic_entities(
        self,
        data: ProjectData,
        errors: List[str],
        warnings: List[str],
        validated_entities: Dict[str, int]
    ) -> None:
        """Valida las entidades básicas del proyecto."""
        # Validar tareas
        if not data.tasks:
            errors.append("El proyecto debe tener al menos una tarea")
        else:
            validated_entities['tasks'] = len(data.tasks)
            
            # Validar tareas individuales
            for i, task in enumerate(data.tasks):
                if not isinstance(task, Task):
                    errors.append(f"Tarea {i} no es una instancia válida de Task")
                elif task.id <= 0:
                    errors.append(f"Tarea {i} tiene ID inválido: {task.id}")
                elif not task.name.strip():
                    errors.append(f"Tarea {i} no tiene nombre")
                elif task.duration < 0:
                    errors.append(f"Tarea {i} tiene duración negativa: {task.duration}")
                elif task.estimated_cost < 0:
                    errors.append(f"Tarea {i} tiene costo negativo: {task.estimated_cost}")
        
        # Validar recursos
        if not data.resources:
            errors.append("El proyecto debe tener al menos un recurso")
        else:
            validated_entities['resources'] = len(data.resources)
            
            # Validar recursos individuales
            for i, resource in enumerate(data.resources):
                if not isinstance(resource, Resource):
                    errors.append(f"Recurso {i} no es una instancia válida de Resource")
                elif resource.id <= 0:
                    errors.append(f"Recurso {i} tiene ID inválido: {resource.id}")
                elif not resource.name.strip():
                    errors.append(f"Recurso {i} no tiene nombre")
                elif resource.cost_per_hour < 0:
                    errors.append(f"Recurso {i} tiene costo por hora negativo: {resource.cost_per_hour}")
                elif resource.efficiency <= 0:
                    errors.append(f"Recurso {i} tiene eficiencia inválida: {resource.efficiency}")
        
        # Validar equipos
        validated_entities['teams'] = len(data.teams)
        
        for i, team in enumerate(data.teams):
            if not isinstance(team, Team):
                errors.append(f"Equipo {i} no es una instancia válida de Team")
            elif team.id <= 0:
                errors.append(f"Equipo {i} tiene ID inválido: {team.id}")
            elif not team.name.strip():
                errors.append(f"Equipo {i} no tiene nombre")
            elif not team.members:
                errors.append(f"Equipo {i} no tiene miembros")
    
    def _validate_referential_integrity(
        self,
        data: ProjectData,
        errors: List[str],
        warnings: List[str]
    ) -> None:
        """Valida la integridad referencial del proyecto."""
        # Crear mapas de entidades
        task_map = {task.id: task for task in data.tasks}
        resource_map = {resource.id: resource for resource in data.resources}
        team_map = {team.id: team for team in data.teams}
        
        # Validar referencias de tareas
        for task in data.tasks:
            # Validar dependencias
            for dependency in task.dependencies:
                if dependency.id not in task_map:
                    errors.append(f"Tarea {task.id} depende de tarea inexistente {dependency.id}")
            
            # Validar recurso asignado
            if task.assigned_resource:
                if task.assigned_resource.id not in resource_map:
                    errors.append(f"Tarea {task.id} tiene recurso asignado inexistente {task.assigned_resource.id}")
            
            # Validar equipo asignado
            if task.assigned_team:
                if task.assigned_team.id not in team_map:
                    errors.append(f"Tarea {task.id} tiene equipo asignado inexistente {task.assigned_team.id}")
            
            # Validar recurso requerido
            if task.required_resource_id:
                if task.required_resource_id not in resource_map:
                    errors.append(f"Tarea {task.id} requiere recurso inexistente {task.required_resource_id}")
        
        # Validar referencias de equipos
        for team in data.teams:
            for member in team.members:
                if member.id not in resource_map:
                    errors.append(f"Equipo {team.id} tiene miembro inexistente {member.id}")
    
    def _validate_dependencies(
        self,
        data: ProjectData,
        errors: List[str],
        warnings: List[str]
    ) -> None:
        """Valida las dependencias entre tareas."""
        # Crear grafo de dependencias
        dependency_graph = defaultdict(set)
        task_map = {task.id: task for task in data.tasks}
        
        for task in data.tasks:
            for dependency in task.dependencies:
                dependency_graph[dependency.id].add(task.id)
        
        # Detectar ciclos
        visited = set()
        rec_stack = set()
        
        def dfs(node: int, path: List[int]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in dependency_graph[node]:
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Ciclo detectado
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    errors.append(f"Ciclo detectado en dependencias: {cycle}")
            
            rec_stack.remove(node)
        
        for task in data.tasks:
            if task.id not in visited:
                dfs(task.id, [])
        
        # Validar auto-dependencias
        for task in data.tasks:
            if task.id in [dep.id for dep in task.dependencies]:
                errors.append(f"Tarea {task.id} depende de sí misma")
    
    def _validate_resources(
        self,
        data: ProjectData,
        errors: List[str],
        warnings: List[str]
    ) -> None:
        """Valida los recursos del proyecto."""
        # Verificar IDs únicos
        resource_ids = [resource.id for resource in data.resources]
        if len(resource_ids) != len(set(resource_ids)):
            errors.append("Los recursos tienen IDs duplicados")
        
        # Verificar nombres únicos
        resource_names = [resource.name for resource in data.resources]
        if len(resource_names) != len(set(resource_names)):
            warnings.append("Los recursos tienen nombres duplicados")
        
        # Validar rangos de valores
        for resource in data.resources:
            if resource.efficiency > 2.0:
                warnings.append(f"Recurso {resource.id} tiene eficiencia muy alta: {resource.efficiency}")
            
            if resource.availability < 0.5:
                warnings.append(f"Recurso {resource.id} tiene disponibilidad muy baja: {resource.availability}")
            
            if resource.cost_per_hour > 1000:
                warnings.append(f"Recurso {resource.id} tiene costo por hora muy alto: {resource.cost_per_hour}")
    
    def _validate_teams(
        self,
        data: ProjectData,
        errors: List[str],
        warnings: List[str]
    ) -> None:
        """Valida los equipos del proyecto."""
        # Verificar IDs únicos
        team_ids = [team.id for team in data.teams]
        if len(team_ids) != len(set(team_ids)):
            errors.append("Los equipos tienen IDs duplicados")
        
        # Verificar nombres únicos
        team_names = [team.name for team in data.teams]
        if len(team_names) != len(set(team_names)):
            warnings.append("Los equipos tienen nombres duplicados")
        
        # Validar miembros de equipos
        resource_map = {resource.id: resource for resource in data.resources}
        
        for team in data.teams:
            if len(team.members) < 2:
                warnings.append(f"Equipo {team.id} tiene menos de 2 miembros")
            
            if len(team.members) > 10:
                warnings.append(f"Equipo {team.id} tiene más de 10 miembros")
            
            # Verificar que los miembros sean recursos válidos
            for member in team.members:
                if member.id not in resource_map:
                    errors.append(f"Equipo {team.id} tiene miembro inexistente {member.id}")
    
    def _validate_custom_rules(
        self,
        data: ProjectData,
        errors: List[str],
        warnings: List[str]
    ) -> None:
        """Valida usando reglas personalizadas."""
        for rule in self._validation_rules:
            try:
                if not rule.validate(data):
                    errors.append(rule.get_error_message())
            except Exception as e:
                errors.append(f"Error en regla de validación: {e}")
    
    def _validate_custom_validators(
        self,
        data: ProjectData,
        errors: List[str],
        warnings: List[str]
    ) -> None:
        """Valida usando validadores personalizados."""
        for validator in self._custom_validators:
            try:
                result = validator(data)
                if isinstance(result, list):
                    errors.extend(result)
                elif isinstance(result, str):
                    errors.append(result)
            except Exception as e:
                errors.append(f"Error en validador personalizado: {e}")
    
    def add_validation_rule(self, rule: IValidationRule) -> None:
        """
        Añade una regla de validación personalizada.
        
        Args:
            rule: Regla de validación a añadir
        """
        self._validation_rules.append(rule)
        logger.debug(f"Regla de validación añadida: {rule.__class__.__name__}")
    
    def add_custom_validator(self, validator: callable) -> None:
        """
        Añade un validador personalizado.
        
        Args:
            validator: Función validadora a añadir
        """
        self._custom_validators.append(validator)
        logger.debug(f"Validador personalizado añadido: {validator.__name__}")
    
    def remove_validation_rule(self, rule: IValidationRule) -> None:
        """
        Elimina una regla de validación.
        
        Args:
            rule: Regla de validación a eliminar
        """
        if rule in self._validation_rules:
            self._validation_rules.remove(rule)
            logger.debug(f"Regla de validación eliminada: {rule.__class__.__name__}")
    
    def remove_custom_validator(self, validator: callable) -> None:
        """
        Elimina un validador personalizado.
        
        Args:
            validator: Validador a eliminar
        """
        if validator in self._custom_validators:
            self._custom_validators.remove(validator)
            logger.debug(f"Validador personalizado eliminado: {validator.__name__}")
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del validador.
        
        Returns:
            Diccionario con estadísticas
        """
        return {
            'validation_rules_count': len(self._validation_rules),
            'custom_validators_count': len(self._custom_validators),
            'validation_rules': [rule.__class__.__name__ for rule in self._validation_rules],
            'custom_validators': [validator.__name__ for validator in self._custom_validators]
        }
    
    def clear_validation_rules(self) -> None:
        """Limpia todas las reglas de validación."""
        self._validation_rules.clear()
        self._custom_validators.clear()
        logger.info("Reglas de validación limpiadas")


# Instancia global del validador
project_data_validator = ProjectDataValidator()


# Funciones de conveniencia
def validate_project_data(data: ProjectData) -> ValidationResult:
    """Valida los datos del proyecto."""
    return project_data_validator.validate_project_data(data)


def add_validation_rule(rule: IValidationRule) -> None:
    """Añade una regla de validación personalizada."""
    project_data_validator.add_validation_rule(rule)


def add_custom_validator(validator: callable) -> None:
    """Añade un validador personalizado."""
    project_data_validator.add_custom_validator(validator)


def get_validation_stats() -> Dict[str, Any]:
    """Obtiene estadísticas del validador."""
    return project_data_validator.get_validation_stats()
