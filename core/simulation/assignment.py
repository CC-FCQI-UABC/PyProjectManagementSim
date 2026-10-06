"""
-----------------------------------------------------------------
PyProjectManagementSim 1.0
Modelo computacional de gestión de proyectos en Python.
Autores: Manuel Castañón–Puga, Fernando Rosales Quiñones
Correo electrónico: {puga, fernando.rosales59}@uabc.edu.mx
Universidad Autónoma de Baja California
http://www.uabc.edu.mx
PyProjectManagementSim/core/simulation/assignment.py
-----------------------------------------------------------------
"""

"""
Assignment strategies for the ABP simulator.
"""

from abc import ABC, abstractmethod
from typing import List

from core.entities import Task, TaskStatus
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .model import ProjectManagementModel
    from core.agents import TaskAgent
    from core.entities import Team


class BaseAssignmentStrategy(ABC):
    """
    Abstract base class for all task assignment strategies.
    Defines the interface that all strategies must follow.
    """
    def __init__(self, model: 'ProjectManagementModel'):
        self.model = model

    @abstractmethod
    def assign_tasks(self):
        """
        The main method that implements the assignment logic.
        This method will be called by the model in each step.
        """
        raise NotImplementedError("The assign_tasks method must be implemented in the subclass.")

    def _get_available_tasks(self) -> List[Task]:
        """Helper method to get tasks ready to be assigned."""
        return [t for t in self.model.task_map.values() if
                t.status == TaskStatus.TO_DO and self.model._are_dependencies_met(t)]

    def _assign_to_team(self, task: Task, team: 'Team'):
        """Assign a task to a team and to every member's agent."""
        team.assign_task(task)
        task.assigned_team = team
        task.status = TaskStatus.IN_PROGRESS
        for resource in team.members:
            agent = self.model.agents_by_resource_id.get(resource.id)
            if agent:
                agent.assign_task(task)

    def _assign_to_agent(self, task: Task, agent: 'TaskAgent'):
        """Assign a task to an individual agent, recording the resource on the task."""
        agent.assign_task(task)
        task.assign_resource(agent.resource)
        task.status = TaskStatus.IN_PROGRESS

    def _assign_to_any_idle(self, task: Task) -> bool:
        """Assign a task with no required resource to the first idle team or unteamed agent."""
        team = next((t for t in self.model.teams if not t.is_busy()), None)
        if team:
            self._assign_to_team(task, team)
            return True
        agent = next((a for a in self.model.project_agents
                      if a.is_available() and a.resource.id not in self.model.agent_to_team_map), None)
        if agent:
            self._assign_to_agent(task, agent)
            return True
        return False

    def _assign_by_required_resource(self, tasks: List[Task]):
        """Assign each task to the team or agent owning its required resource, if free."""
        for task in tasks:
            res_id = task.required_resource_id
            if res_id is None:
                self._assign_to_any_idle(task)
                continue

            if res_id in self.model.agent_to_team_map:
                team = self.model.agent_to_team_map[res_id]
                if not team.is_busy():
                    self._assign_to_team(task, team)
            else:
                agent = self.model.agents_by_resource_id.get(res_id)
                if agent and agent.is_available():
                    self._assign_to_agent(task, agent)


class GreedyAssignmentStrategy(BaseAssignmentStrategy):
    """
    "Greedy" assignment strategy. Assigns the first available task
    to the first available team or agent that can perform it.
    """
    def assign_tasks(self):
        self._assign_by_required_resource(self._get_available_tasks())


# Second assignment strategy
class ShortestTaskFirstStrategy(BaseAssignmentStrategy):
    """
    Strategy that prioritizes tasks with the least work (effort).
    """
    def assign_tasks(self):
        available_tasks = sorted(self._get_available_tasks(), key=lambda t: t.work)
        self._assign_by_required_resource(available_tasks)


# Parallel assignment strategy
class ParallelAssignmentStrategy(BaseAssignmentStrategy):
    """
    Strategy that assigns multiple tasks in parallel to all available teams.
    This allows true parallel execution of tasks by different teams.

    Assignment order each step:
      1. Idle teams take a task that needs one of their members (or no specific resource).
      2. Idle individual agents take a task that needs them (or no specific resource).
      3. Teams still idle take any remaining task as cross-training (efficiency penalty
         applied in the model).
    """
    def assign_tasks(self):
        available_tasks = self._get_available_tasks()
        if not available_tasks:
            return

        def pending():
            return [t for t in available_tasks if t.status == TaskStatus.TO_DO]

        idle_teams = [team for team in self.model.teams if not team.is_busy()]
        idle_agents = [agent for agent in self.model.project_agents
                       if agent.is_available() and agent.resource.id not in self.model.agent_to_team_map]

        # 1. Teams take tasks matching their skills
        for team in list(idle_teams):
            member_ids = {member.id for member in team.members}
            task = next((t for t in pending()
                         if t.required_resource_id is None or t.required_resource_id in member_ids), None)
            if task:
                self._assign_to_team(task, team)
                idle_teams.remove(team)

        # 2. Individual agents take their own tasks
        for agent in idle_agents:
            task = next((t for t in pending()
                         if t.required_resource_id is None or t.required_resource_id == agent.resource.id), None)
            if task:
                self._assign_to_agent(task, agent)

        # 3. Remaining idle teams cross-train on leftover tasks
        for team in idle_teams:
            remaining = pending()
            if not remaining:
                break
            self._assign_to_team(remaining[0], team)


# Add the new strategy to the map
STRATEGY_MAP = {
    "greedy": GreedyAssignmentStrategy,
    "shortest_first": ShortestTaskFirstStrategy,
    "parallel": ParallelAssignmentStrategy
}