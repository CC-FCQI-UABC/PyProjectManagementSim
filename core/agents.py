# Contenido completo, final y definitivo de core/agents.py

from mesa import Agent as MesaAgent
from typing import Optional

try:
    from .entities import Task, Resource, Team
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from core.simulation.model import ProjectManagementModel
except ImportError:
    from entities import Task, Resource, Team
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from model import ProjectManagementModel


class TaskAgent(MesaAgent):
    """
    Agente que representa un Recurso y ejecuta Tareas.
    """

    def __init__(self, unique_id: int, model: 'ProjectManagementModel', resource: Resource, efficiency: float = 1.0):
        # --- MODIFICACIÓN CLAVE Y DEFINITIVA ---
        # No llamamos a super().__init__() para evitar los conflictos de versiones de Mesa.
        # En su lugar, asignamos manualmente los atributos que la clase base necesita.
        # Esto hace que nuestro código sea inmune a cómo Mesa maneje su constructor.
        self.unique_id = unique_id
        self.model = model

        if not isinstance(resource, Resource):
            raise TypeError("TaskAgent requiere una instancia válida de Resource.")

        # Atributos propios del agente
        self.resource = resource
        self.efficiency = max(0.1, efficiency)
        self.current_task: Optional[Task] = None
        self.total_tasks_completed: int = 0
        self.worked_hours: float = 0.0
        self.team: Optional[Team] = None
        self.agent_log_id = f"Agent_{self.resource.id}_{self.resource.name}"

    def is_available(self) -> bool:
        """Verifica si el agente está libre (sin tarea asignada)."""
        return self.current_task is None

    def assign_task(self, task: Task):
        """Asigna una tarea al agente. Es llamado por el Modelo."""
        if self.is_available() and isinstance(task, Task):
            self.current_task = task

    def release(self):
        """Libera al agente de su tarea actual."""
        self.current_task = None

    def reset(self):
        """Resetea el estado del agente para una nueva simulación."""
        self.release()
        self.total_tasks_completed = 0
        self.worked_hours = 0.0

    def step(self):
        """Acción del TaskAgent en cada paso: trabajar si tiene una tarea asignada."""
        if not self.is_available():
            self.worked_hours += 1.0

    def __repr__(self):
        """Representación textual mejorada del TaskAgent."""
        task_id = self.current_task.id if self.current_task else "Idle"
        team_str = f", team={self.team.id}" if self.team else ""
        return f"TaskAgent(uid={self.unique_id}, res='{self.resource.name}', task={task_id}{team_str})"