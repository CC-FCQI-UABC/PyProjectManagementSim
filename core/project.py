# Contenido completo y actualizado de core/project.py

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from copy import deepcopy

# Usar importación relativa dentro del mismo paquete 'core'
from .entities import Task, Resource


@dataclass
class ProjectData:
    """
    Una estructura de datos simple para pasar los datos crudos del lector al proyecto.
    """
    project_name: str
    tasks: Dict[int, Task]
    resources: Dict[int, Resource]
    baseline_cost: float


class Project:
    """
    Representa el proyecto, conteniendo las tareas y recursos ya procesados.
    Su principal responsabilidad es cargar los datos y resolver las dependencias entre tareas.
    """

    def __init__(self, data: ProjectData):
        """
        Inicializa el proyecto a partir de un objeto ProjectData que viene del lector.
        """
        if not isinstance(data, ProjectData):
            raise TypeError("Project debe inicializarse con una instancia de ProjectData.")

        self.name: str = data.project_name
        self.tasks: Dict[int, Task] = data.tasks
        self.resources: Dict[int, Resource] = data.resources
        self.baseline_cost: float = data.baseline_cost

        # Paso crucial que se ejecuta al crear el proyecto
        self._resolve_dependencies()
        print(f"Info (Project): Dependencias resueltas para {len(self.tasks)} tareas.")

    def _resolve_dependencies(self):
        """
        Convierte los IDs de las dependencias en referencias a los objetos Task reales.
        Esto es fundamental para que el modelo pueda verificar si una tarea puede empezar.
        """
        for task in self.tasks.values():
            if not hasattr(task, 'dependencies') or not isinstance(task.dependencies, list):
                continue

            resolved_deps = []
            # task.dependencies contiene IDs en este punto (ej. [1, 5, 12])
            for dep_id in task.dependencies:
                # Buscamos la tarea correspondiente a ese ID en nuestro diccionario
                dependency_task_object = self.tasks.get(int(dep_id))
                if dependency_task_object:
                    resolved_deps.append(dependency_task_object)

            # Reemplazamos la lista de IDs por la lista de objetos Task
            task.dependencies = resolved_deps

    def get_tasks_for_simulation(self) -> List[Task]:
        """
        Devuelve una COPIA PROFUNDA de la lista de tareas.
        Es CRUCIAL usar una copia para que cada simulación sea independiente.
        """
        return deepcopy(list(self.tasks.values()))

    def get_resources_for_simulation(self) -> List[Resource]:
        """
        Devuelve una COPIA PROFUNDA de la lista de recursos.
        """
        return deepcopy(list(self.resources.values()))

    def get_all_resources(self) -> List[Resource]:
        """Devuelve una lista de todos los objetos Resource del proyecto."""
        return list(self.resources.values())

    def get_all_tasks(self) -> List[Task]:
        """Devuelve una lista de todos los objetos Task del proyecto."""
        return list(self.tasks.values())

    def override_resource_costs(self, resources_definition: List[Dict[str, Any]]):
        """Permite sobreescribir los costos de los recursos desde la configuración."""
        if not resources_definition:
            return

        print(f"Info (Project): Intentando actualizar costos desde la configuración...")
        updated_count = 0
        for res_data in resources_definition:
            res_id = res_data.get('resource_id')
            cost = res_data.get('cost_per_hour')
            if res_id is not None and cost is not None and res_id in self.resources:
                self.resources[res_id].cost_per_hour = float(cost)
                updated_count += 1
        print(f"Info (Project): {updated_count} costos de recursos actualizados.")

    def display_tasks(self, limit: int = 20):
        """Muestra una lista de las tareas cargadas en la consola."""
        print(f"\n--- Lista de Tareas Cargadas (max {limit}) ---")
        if not self.tasks:
            print("  (No hay tareas de trabajo cargadas)")
            return

        for i, task in enumerate(self.get_all_tasks()):
            if i >= limit:
                print(f"  ... y {len(self.tasks) - limit} tareas más.")
                break
            res_id_str = f"Req. Res: {task.required_resource_id}" if task.required_resource_id is not None else "Req. Res: N/A"
            dep_str = f"Deps: {len(task.dependencies)}"
            print(
                f"  - ID: {task.id:<5} | Nombre: {task.name[:35]:<35} | Dur: {task.duration:<6.1f}h | Costo: {task.estimated_cost:<7.2f} | {res_id_str:<15} | {dep_str}")
        print("-" * (35 + 40))

    def display_resources(self, limit: int = 20):
        """Muestra una lista de los recursos cargados en la consola."""
        print(f"\n--- Muestra de Recursos Cargados (max {limit}) ---")
        if not self.resources:
            print("  (No hay recursos de trabajo cargados)")
            return

        for i, resource in enumerate(self.get_all_resources()):
            if i >= limit:
                print(f"  ... y {len(self.resources) - limit} recursos más.")
                break
            print(
                f"  - ID: {resource.id:<5} | Nombre: {resource.name[:40]:<40} | Costo/h: {resource.cost_per_hour:<7.2f}")
        print("-" * (40 + 25))

    def __repr__(self):
        """Representación textual del objeto Project."""
        return (f"Project(name='{self.name}', tasks={len(self.tasks)}, "
                f"resources={len(self.resources)}, baseline_cost={self.baseline_cost:.2f})")