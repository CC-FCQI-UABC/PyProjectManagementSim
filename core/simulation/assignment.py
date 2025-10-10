# Complete and updated content of core/simulation/assignment.py

from abc import ABC, abstractmethod
from typing import List

from core.entities import Task, TaskStatus
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .model import ProjectManagementModel


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


class GreedyAssignmentStrategy(BaseAssignmentStrategy):
    """
    "Greedy" assignment strategy. Assigns the first available task
    to the first available team or agent that can perform it.
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


# NEW: Second assignment strategy
class ShortestTaskFirstStrategy(BaseAssignmentStrategy):
    """
    Strategy that prioritizes tasks with the shortest duration.
    """
    def assign_tasks(self):
        # 1. Get tasks that can be started
        available_tasks = self._get_available_tasks()

        # 2. Sort tasks by duration, shortest first
        sorted_tasks = sorted(available_tasks, key=lambda t: t.duration)

        # 3. Iterate over the sorted list and assign the same way as the greedy strategy
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


# MODIFIED: Add the new strategy to the map
STRATEGY_MAP = {
    "greedy": GreedyAssignmentStrategy,
    "shortest_first": ShortestTaskFirstStrategy,
}