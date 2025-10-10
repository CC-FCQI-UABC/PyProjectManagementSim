# Contenido completo y actualizado de core/simulation/assignment.py

from abc import ABC, abstractmethod
from typing import List

from core.entities import Task, TaskStatus
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .model import ProjectManagementModel


class BaseAssignmentStrategy(ABC):
    """
    Clase base abstracta para todas las estrategias de asignación de tareas.
    Define la interfaz que todas las estrategias deben seguir.
    """
    def __init__(self, model: 'ProjectManagementModel'):
        self.model = model

    @abstractmethod
    def assign_tasks(self):
        """
        El método principal que implementa la lógica de asignación.
        Este método será llamado por el modelo en cada paso.
        """
        raise NotImplementedError("El método assign_tasks debe ser implementado en la subclase.")

    def _get_available_tasks(self) -> List[Task]:
        """Método de ayuda para obtener tareas listas para ser asignadas."""
        return [t for t in self.model.task_map.values() if
                t.status == TaskStatus.TO_DO and self.model._are_dependencies_met(t)]


class GreedyAssignmentStrategy(BaseAssignmentStrategy):
    """
    Estrategia de asignación "voraz". Asigna la primera tarea disponible
    al primer equipo o agente disponible que pueda realizarla.
    """
    def assign_tasks(self):
        available_tasks = self._get_available_tasks()

        for task in available_tasks:
            res_id = task.required_resource_id
            if res_id is None:
                continue

            if res_id in self.model.agent_to_team_map:
                team = self.model.agent_to_team_map[res_id]
                if not team.is_busy():
                    team.assign_task(task)
                    task.assigned_team = team
                    task.status = TaskStatus.IN_PROGRESS  # Change status when assigned
                    # Get TaskAgent objects for team members
                    for resource in team.members:
                        agent = self.model.agents_by_resource_id.get(resource.id)
                        if agent:
                            agent.assign_task(task)
            else:
                agent = self.model.agents_by_resource_id.get(res_id)
                if agent and agent.is_available():
                    agent.assign_task(task)
                    task.status = TaskStatus.IN_PROGRESS  # Change status when assigned


# NUEVO: Segunda estrategia de asignación
class ShortestTaskFirstStrategy(BaseAssignmentStrategy):
    """
    Estrategia que prioriza las tareas con la menor duración.
    """
    def assign_tasks(self):
        # 1. Obtiene las tareas que se pueden empezar
        available_tasks = self._get_available_tasks()

        # 2. Ordena las tareas por duración, de menor a mayor
        sorted_tasks = sorted(available_tasks, key=lambda t: t.duration)

        # 3. Itera sobre la lista ordenada y asigna de la misma forma que la estrategia voraz
        for task in sorted_tasks:
            res_id = task.required_resource_id
            if res_id is None:
                continue

            if res_id in self.model.agent_to_team_map:
                team = self.model.agent_to_team_map[res_id]
                if not team.is_busy():
                    team.assign_task(task)
                    task.assigned_team = team
                    task.status = TaskStatus.IN_PROGRESS  # Change status when assigned
                    # Get TaskAgent objects for team members
                    for resource in team.members:
                        agent = self.model.agents_by_resource_id.get(resource.id)
                        if agent:
                            agent.assign_task(task)
            else:
                agent = self.model.agents_by_resource_id.get(res_id)
                if agent and agent.is_available():
                    agent.assign_task(task)
                    task.status = TaskStatus.IN_PROGRESS  # Change status when assigned


# MODIFICADO: Añadimos la nueva estrategia al mapa
STRATEGY_MAP = {
    "greedy": GreedyAssignmentStrategy,
    "shortest_first": ShortestTaskFirstStrategy,
}