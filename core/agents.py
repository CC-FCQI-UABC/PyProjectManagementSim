"""
-----------------------------------------------------------------
PyProjectManagementSim 1.0
Modelo computacional de gestión de proyectos en Python.
Autores: Manuel Castañón–Puga, Fernando Rosales Quiñones
Correo electrónico: {puga, fernando.rosales59}@uabc.edu.mx
Universidad Autónoma de Baja California
http://www.uabc.edu.mx
PyProjectManagementSim/core/agents.py
-----------------------------------------------------------------
"""

"""
Task agent class.
"""

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

    def __init__(self, unique_id: int, model: 'ProjectManagementModel', resource: Resource,
                 efficiency: Optional[float] = None):
        if not isinstance(resource, Resource):
            raise TypeError("TaskAgent requires a valid Resource instance.")

        # Mesa 3 registers the agent with the model (model.agents) and assigns a
        # sequential unique_id; keep the resource id as the agent id instead.
        super().__init__(model)
        self.unique_id = unique_id

        # Attributes specific to the agent
        self.resource = resource
        # Default to the resource's own efficiency factor
        self.efficiency = max(0.1, resource.efficiency if efficiency is None else efficiency)
        self.current_task: Optional[Task] = None
        self.total_tasks_completed: int = 0
        self.worked_hours: float = 0.0
        self.team: Optional[Team] = None
        self.agent_log_id = f"Agent_{self.resource.id}_{self.resource.name}"

    def is_available(self) -> bool:
        """Check if the agent is free (no assigned task)."""
        return self.current_task is None

    def assign_task(self, task: Task):
        """Assign a task to the agent. It is called by the Model."""
        if self.is_available() and isinstance(task, Task):
            self.current_task = task

    def release(self):
        """Release the agent from its current task."""
        self.current_task = None

    def reset(self):
        """Reset agent state for a new simulation."""
        self.release()
        self.total_tasks_completed = 0
        self.worked_hours = 0.0

    def step(self):
        """TaskAgent action in each step: work if it has an assigned task."""
        if not self.is_available():
            self.worked_hours += 1.0

    def __repr__(self):
        """Improved textual representation of TaskAgent."""
        task_id = self.current_task.id if self.current_task else "Idle"
        team_str = f", team={self.team.id}" if self.team else ""
        return f"TaskAgent(uid={self.unique_id}, res='{self.resource.name}', task={task_id}{team_str})"