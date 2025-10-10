# Complete and updated content of core/project.py

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from copy import deepcopy

# Use relative import within the same 'core' package
from .entities import Task, Resource


@dataclass
class ProjectData:
    """
    A simple data structure to pass raw data from the reader to the project.
    """
    project_name: str
    tasks: Dict[int, Task]
    resources: Dict[int, Resource]
    baseline_cost: float


class Project:
    """
    Represents the project, containing the already processed tasks and resources.
    Its main responsibility is to load data and resolve dependencies between tasks.
    """

    def __init__(self, data: ProjectData):
        """
        Initialize the project from a ProjectData object that comes from the reader.
        """
        if not isinstance(data, ProjectData):
            raise TypeError("Project must be initialized with a ProjectData instance.")

        self.name: str = data.project_name
        self.tasks: Dict[int, Task] = data.tasks
        self.resources: Dict[int, Resource] = data.resources
        self.baseline_cost: float = data.baseline_cost

        # Crucial step that executes when creating the project
        self._resolve_dependencies()
        print(f"Info (Project): Dependencies resolved for {len(self.tasks)} tasks.")

    def _resolve_dependencies(self):
        """
        Converts dependency IDs into references to real Task objects.
        This is fundamental for the model to verify if a task can start.
        """
        for task in self.tasks.values():
            if not hasattr(task, 'dependencies') or not isinstance(task.dependencies, list):
                continue

            resolved_deps = []
            # task.dependencies contains IDs at this point (e.g. [1, 5, 12])
            for dep_id in task.dependencies:
                # Search for the task corresponding to that ID in our dictionary
                dependency_task_object = self.tasks.get(int(dep_id))
                if dependency_task_object:
                    resolved_deps.append(dependency_task_object)

            # Replace the list of IDs with the list of Task objects
            task.dependencies = resolved_deps

    def get_tasks_for_simulation(self) -> List[Task]:
        """
        Returns a DEEP COPY of the task list.
        It is CRUCIAL to use a copy so that each simulation is independent.
        """
        return deepcopy(list(self.tasks.values()))

    def get_resources_for_simulation(self) -> List[Resource]:
        """
        Returns a DEEP COPY of the resource list.
        """
        return deepcopy(list(self.resources.values()))

    def get_all_resources(self) -> List[Resource]:
        """Returns a list of all Resource objects in the project."""
        return list(self.resources.values())

    def get_all_tasks(self) -> List[Task]:
        """Returns a list of all Task objects in the project."""
        return list(self.tasks.values())

    def override_resource_costs(self, resources_definition: List[Dict[str, Any]]):
        """Allows overriding resource costs from configuration."""
        if not resources_definition:
            return

        print(f"Info (Project): Attempting to update costs from configuration...")
        updated_count = 0
        for res_data in resources_definition:
            res_id = res_data.get('resource_id')
            cost = res_data.get('cost_per_hour')
            if res_id is not None and cost is not None and res_id in self.resources:
                self.resources[res_id].cost_per_hour = float(cost)
                updated_count += 1
        print(f"Info (Project): {updated_count} resource costs updated.")

    def display_tasks(self, limit: int = 20):
        """Shows a list of loaded tasks in the console."""
        print(f"\n--- Loaded Tasks List (max {limit}) ---")
        if not self.tasks:
            print("  (No work tasks loaded)")
            return

        for i, task in enumerate(self.get_all_tasks()):
            if i >= limit:
                print(f"  ... and {len(self.tasks) - limit} more tasks.")
                break
            res_id_str = f"Req. Res: {task.required_resource_id}" if task.required_resource_id is not None else "Req. Res: N/A"
            dep_str = f"Deps: {len(task.dependencies)}"
            print(
                f"  - ID: {task.id:<5} | Name: {task.name[:35]:<35} | Dur: {task.duration:<6.1f}h | Cost: {task.estimated_cost:<7.2f} | {res_id_str:<15} | {dep_str}")
        print("-" * (35 + 40))

    def display_resources(self, limit: int = 20):
        """Shows a list of loaded resources in the console."""
        print(f"\n--- Loaded Resources Sample (max {limit}) ---")
        if not self.resources:
            print("  (No work resources loaded)")
            return

        for i, resource in enumerate(self.get_all_resources()):
            if i >= limit:
                print(f"  ... and {len(self.resources) - limit} more resources.")
                break
            print(
                f"  - ID: {resource.id:<5} | Name: {resource.name[:40]:<40} | Cost/h: {resource.cost_per_hour:<7.2f}")
        print("-" * (40 + 25))

    def __repr__(self):
        """Textual representation of the Project object."""
        return (f"Project(name='{self.name}', tasks={len(self.tasks)}, "
                f"resources={len(self.resources)}, baseline_cost={self.baseline_cost:.2f})")