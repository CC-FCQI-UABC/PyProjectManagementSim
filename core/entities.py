# Contenido completo y final de core/entities.py

from __future__ import annotations
from typing import List, Dict, Optional


class Task:
    def __init__(self, task_id: int, name: str, duration: float, estimated_cost: float):
        self.id = task_id;
        self.name = name;
        self.duration = max(0.0, duration)
        self.estimated_cost = max(0.0, estimated_cost);
        self.status: str = "to-do"
        self.progress: float = 0.0;
        self.real_duration: float = 0.0
        self.dependencies: List[Task] = [];
        self.assigned_resource: Optional['Resource'] = None
        self.required_resource_id: Optional[int] = None;
        self.assigned_team: Optional['Team'] = None

    def update_progress(self, increment: float):
        if self.status == "done": return
        if self.status == "to-do" and increment > 0: self.status = "in_progress"
        self.progress = min(1.0, max(0.0, self.progress + increment))
        if self.progress >= 1.0: self.status = "done"

    def __repr__(self):
        deps_str = f" deps={[d.id for d in self.dependencies]}" if self.dependencies else ""
        req_res_str = f" req_res={self.required_resource_id}" if self.required_resource_id is not None else ""
        assigned_res_str = f" assigned={self.assigned_resource.id}" if self.assigned_resource else ""
        assigned_team_str = f" assigned_team={self.assigned_team.id}" if self.assigned_team else ""
        return (f"Task(id={self.id}, '{self.name}', dur={self.duration:.1f}h, "
                f"cost={self.estimated_cost:.2f}, status='{self.status}', "
                f"prog={self.progress * 100:.0f}%, real_dur={self.real_duration:.1f}h"
                f"{req_res_str}{assigned_res_str}{assigned_team_str}{deps_str})")


class Resource:
    def __init__(self, resource_id: int, name: str, cost_per_hour: float):
        self.id = resource_id;
        self.name = name;
        self.cost_per_hour = max(0.0, cost_per_hour)

    def __repr__(self):
        return f"Resource(id={self.id}, name='{self.name}')"


class Team:
    """Representa a un grupo de agentes que trabajan juntos."""

    def __init__(self, team_id: int, name: str, members: List['TaskAgent']):
        self.id = team_id
        self.name = name
        self.members = members
        self.morale: float = 0.8
        self.current_task: Optional[Task] = None
        self.time_on_current_task: int = 0

    @property
    def cohesion_factor(self) -> float:
        """La cohesión (eficiencia) del equipo depende de su moral."""
        return 0.6 + self.morale

    def boost_morale(self, amount: float = 0.25):
        """Aumenta la moral del equipo."""
        self.morale = min(1.2, self.morale + amount)

    def decay_morale(self, amount: float = 0.05):
        """Disminuye la moral del equipo."""
        self.morale = max(0.0, self.morale - amount)

    def regress_to_mean(self, baseline: float = 0.75, rate: float = 0.02):
        """La moral tiende a volver a un estado base neutral con el tiempo."""
        if self.morale > baseline:
            self.morale -= rate * (self.morale - baseline)
        elif self.morale < baseline:
            self.morale += rate * (baseline - self.morale)

    def assign_task(self, task: Task):
        self.current_task = task
        self.time_on_current_task = 0

    def release_task(self):
        self.current_task = None
        self.time_on_current_task = 0

    def is_busy(self) -> bool:
        return self.current_task is not None and self.current_task.status != "done"

    def __repr__(self):
        member_ids = [agent.resource.id for agent in self.members]
        return f"Team(id={self.id}, name='{self.name}', members={member_ids})"