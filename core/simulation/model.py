"""
-----------------------------------------------------------------
PyProjectManagementSim 1.0
Modelo computacional de gestión de proyectos en Python.
Autores: Manuel Castañón–Puga, Fernando Rosales Quiñones
Correo electrónico: {puga, fernando.rosales59}@uabc.edu.mx
Universidad Autónoma de Baja California
http://www.uabc.edu.mx
PyProjectManagementSim/core/simulation/model.py
-----------------------------------------------------------------
"""

"""
Main model class for the ABP simulator.
"""

from mesa import Model
from mesa.datacollection import DataCollector
from typing import Dict, List
import numpy as np

# Import the classes that the model needs to know
from core.entities import Task, Resource, Team, TaskStatus
from core.agents import TaskAgent
from core.simulation.parameters import SimulationParameters
from core.simulation.assignment import BaseAssignmentStrategy, STRATEGY_MAP


class ProjectManagementModel(Model):
    """
    The main model class for the ABP simulator. Orchestrates the agents,
    the progress of tasks and data collection.
    """

    # The constructor now is compatible with the Runner.
    # Accepts lists of tasks and resources, not the complete Project object.
    def __init__(self, tasks: List[Task], resources: List[Resource], params: SimulationParameters):
        # rng seeds both self.random and self.rng, so a given seed reproduces a run exactly
        super().__init__(rng=params.seed)
        self.params = params
        if params.reassignment_frequency:
            print(f"Warning (Model): reassignment_frequency={params.reassignment_frequency} is not "
                  f"implemented and has no effect.")

        # The model now works with its own copy of the tasks and resources
        self.task_map: Dict[int, Task] = {task.id: task for task in tasks}

        self.teams: List[Team] = []
        self.team_map: Dict[int, Team] = {}

        self.project_agents: List[TaskAgent] = []
        self.agents_by_resource_id: Dict[int, TaskAgent] = {}
        self.agent_to_team_map: Dict[int, Team] = {}

        for resource in resources:
            # Create an agent for each resource (Mesa registers it in self.agents)
            agent = TaskAgent(unique_id=resource.id, model=self, resource=resource)
            self.project_agents.append(agent)
            self.agents_by_resource_id[resource.id] = agent

        self._create_teams_from_config()

        # Planned (baseline) schedule used for PV/SPI
        self.planned_start: Dict[int, float] = self._compute_planned_schedule()

        # Assignment strategy is selected and instantiated from the configuration
        strategy_class = STRATEGY_MAP.get(params.assignment_strategy)
        if not strategy_class:
            raise ValueError(f"Unknown assignment strategy: '{params.assignment_strategy}'")
        self.assignment_strategy: BaseAssignmentStrategy = strategy_class(self)
        print(f"Info (Model): Using strategy: {strategy_class.__name__}")

        # Data collector with all metrics, including team metrics (morale and cohesion)
        self.datacollector = DataCollector(
            model_reporters={
                "Time": lambda m: m.steps,
                "Completion": lambda m: m.project_completion_percentage(),
                "ActualCost": lambda m: m.total_actual_cost(),
                "EarnedValue": lambda m: m.total_earned_value(),
                "CPI": lambda m: m.cost_performance_index(),
                "SPI": lambda m: m.schedule_performance_index(),
                "ActiveAgents": lambda m: sum(1 for a in m.project_agents if not a.is_available()),
                "AvgTeamMorale": lambda m: self.get_average_team_morale(),
                "AvgTeamCohesion": lambda m: self.get_average_team_cohesion()
            }
        )
        self.running = True

    def _create_teams_from_config(self):
        team_definitions = self.params.team_definitions
        if not team_definitions: return
        print("\nCreating teams from configuration...")
        for team_def in team_definitions:
            team_id, name, member_ids = team_def.get("id"), team_def.get("name"), team_def.get("member_resource_ids",
                                                                                               [])
            unknown_ids = [res_id for res_id in member_ids if res_id not in self.agents_by_resource_id]
            if unknown_ids:
                raise ValueError(f"Team '{name}' (id={team_id}) references unknown resource IDs {unknown_ids}. "
                                 f"Known IDs: {sorted(self.agents_by_resource_id)}")
            already_in_team = [res_id for res_id in member_ids if res_id in self.agent_to_team_map]
            if already_in_team:
                raise ValueError(f"Team '{name}' (id={team_id}) reuses resources {already_in_team} "
                                 f"that already belong to another team")
            team_members = [self.agents_by_resource_id[res_id] for res_id in member_ids]
            if team_members:
                # Extract Resource objects from TaskAgents for Team constructor
                team_resources = [agent.resource for agent in team_members]
                team = Team(team_id, name, team_resources)
                self.teams.append(team)
                self.team_map[team_id] = team
                for member_agent in team_members:
                    member_agent.team = team
                    self.agent_to_team_map[member_agent.resource.id] = team
                print(f" -> Team Created: {team}")
        print("-" * 20)

    def _update_task_progress(self):
        for task in self.task_map.values():
            if task.status == TaskStatus.DONE: continue
            work_increment = 0.0
            working_agents = []
            if task.assigned_team:
                team = task.assigned_team
                # Only process if team IS busy AND working on this specific task
                if team.is_busy() and team.current_task and team.current_task.id == task.id:
                    team_base_work = sum(self.agents_by_resource_id[m.id].efficiency for m in team.members)
                    team_efficiency = team.cohesion_factor
                    
                    # Apply cross-training penalty if team doesn't have required resource
                    cross_training_penalty = 1.0
                    if task.required_resource_id is not None:
                        team_member_ids = [member.id for member in team.members]
                        if task.required_resource_id not in team_member_ids:
                            cross_training_penalty = 0.5  # 50% efficiency penalty for cross-training
                    
                    work_increment = team_base_work * team_efficiency * cross_training_penalty
                    working_agents = [a for a in (self.agents_by_resource_id.get(m.id) for m in team.members)
                                      if a and a.current_task is task]
                    
                    # Debug logging for tasks that are taking too long (removed for cleaner output)
            elif task.assigned_resource:
                # Task is assigned to an individual agent
                agent = self.agents_by_resource_id.get(task.assigned_resource.id)
                if agent and not agent.is_available() and agent.current_task and agent.current_task.id == task.id:
                    work_increment = 1.0 * agent.efficiency
                    working_agents = [agent]
            if work_increment > 0:
                error = self.random.uniform(-self.params.error_margin, self.params.error_margin)
                total_work = work_increment * (1 + error)
                # Calculate progress as percentage of task completion per step
                # Each step is one hour of effort, so one worker completes 1/work of the task per step
                base_progress_per_step = 1.0 / task.work if task.work > 0 else 1.0
                # Apply work efficiency multiplier
                progress_increment = base_progress_per_step * total_work
                # If the task finishes mid-step, only charge the fraction of the hour actually used
                remaining = 1.0 - task.progress
                if progress_increment > remaining:
                    unused_hours = 1.0 - remaining / progress_increment
                    for agent in working_agents:
                        agent.worked_hours -= unused_hours
                task.update_progress(progress_increment)
                task.real_duration += 1
            if task.progress >= 1.0:
                task.status = TaskStatus.DONE
                if task.assigned_team:
                    task.assigned_team.boost_morale()
                    # Get TaskAgent objects for team members
                    for resource in task.assigned_team.members:
                        agent = self.agents_by_resource_id.get(resource.id)
                        if agent:
                            agent.release()
                    task.assigned_team.release_task()
                elif task.assigned_resource:
                    agent = self.agents_by_resource_id.get(task.assigned_resource.id)
                    if agent: agent.release()

    def _update_team_social_dynamics(self):
        for team in self.teams:
            team.regress_to_mean()
            if team.is_busy():
                team.time_on_current_task += 1
                task_work = team.current_task.work
                if task_work > 0 and team.time_on_current_task > (task_work * 1.5):
                    team.decay_morale(amount=0.02)

    def _introduce_random_events(self):
        if self.random.random() < 0.02 and self.teams:
            team_afectado = self.random.choice(self.teams)
            if self.random.random() < 0.5:
                team_afectado.decay_morale(amount=0.4)
                print(f"Event (t={self.steps}): Technical issue - {team_afectado.name} morale decreased")
            else:
                team_afectado.boost_morale(amount=0.3)
                print(f"Event (t={self.steps}): Breakthrough - {team_afectado.name} morale increased")

    def _are_dependencies_met(self, task: Task) -> bool:
        return all(dep.status == TaskStatus.DONE for dep in task.dependencies)

    def _complete_ready_milestones(self):
        """Zero-work tasks (e.g. milestones) need no effort: finish them once their dependencies are met."""
        changed = True
        while changed:
            changed = False
            for task in self.task_map.values():
                if task.status == TaskStatus.TO_DO and task.work == 0 and self._are_dependencies_met(task):
                    task.status = TaskStatus.DONE
                    changed = True

    def _all_tasks_done(self) -> bool:
        return all(t.status == TaskStatus.DONE for t in self.task_map.values())

    def step(self):
        # Mesa 3 advances self.steps before calling step(), so self.steps is the current step number.
        if self._all_tasks_done():
            self.running = False
            return

        self._complete_ready_milestones()
        self.assignment_strategy.assign_tasks()
        self.agents.shuffle_do("step")
        self._update_task_progress()
        self._complete_ready_milestones()
        self._update_team_social_dynamics()
        self._introduce_random_events()
        self.datacollector.collect(self)

        # Finish in the step where the last task completes, so Time equals the real duration.
        if self._all_tasks_done():
            self.running = False
            print(f"SIMULATION COMPLETED! All {len(self.task_map)} tasks finished!")

    def run_model(self):
        step_count = 0
        while self.running and step_count < self.params.max_steps:
            self.step()
            step_count += 1
        
        # Log completion status
        if not self.running:
            completed_tasks = sum(1 for t in self.task_map.values() if t.status == TaskStatus.DONE)
            total_tasks = len(self.task_map)
            print(f"Simulation completed naturally: {completed_tasks}/{total_tasks} tasks done")
        else:
            print(f"Simulation stopped at max_steps limit: {self.params.max_steps}")

    # --- Methods for DataCollector ---
    def get_average_team_morale(self) -> float:
        if not self.teams: return 0.0
        return float(np.mean([team.morale for team in self.teams]))

    def get_average_team_cohesion(self) -> float:
        if not self.teams: return 0.0
        return float(np.mean([team.cohesion_factor for team in self.teams]))

    def project_completion_percentage(self) -> float:
        total_work = sum(t.work for t in self.task_map.values())
        if total_work == 0: return 100.0
        completed_work = sum(t.work * t.progress for t in self.task_map.values())
        return (completed_work / total_work) * 100

    def total_actual_cost(self) -> float:
        return sum(agent.worked_hours * agent.resource.cost_per_hour for agent in self.project_agents)

    def total_earned_value(self) -> float:
        return sum(task.estimated_cost * task.progress for task in self.task_map.values())

    def _compute_planned_schedule(self) -> Dict[int, float]:
        """
        Early-start (CPM forward pass) schedule from task work and dependencies.
        One hour of work equals one simulation step. Returns planned start per task id.
        """
        planned_start: Dict[int, float] = {}
        visiting = set()

        def start_of(task: Task) -> float:
            if task.id in planned_start:
                return planned_start[task.id]
            if task.id in visiting:
                raise ValueError(f"Dependency cycle detected at task {task.id}")
            visiting.add(task.id)
            start = 0.0
            for dep in task.dependencies:
                dep_task = self.task_map.get(dep.id)
                if dep_task is not None:
                    start = max(start, start_of(dep_task) + dep_task.work)
            visiting.discard(task.id)
            planned_start[task.id] = start
            return start

        for task in self.task_map.values():
            start_of(task)
        return planned_start

    def total_planned_value(self) -> float:
        """PV: budgeted cost of the work scheduled to be done by the current time."""
        current_time = self.steps
        pv = 0.0
        for task in self.task_map.values():
            elapsed = current_time - self.planned_start[task.id]
            if elapsed <= 0:
                continue
            planned_fraction = min(1.0, elapsed / task.work) if task.work > 0 else 1.0
            pv += task.estimated_cost * planned_fraction
        return pv

    def cost_performance_index(self) -> float:
        ac = self.total_actual_cost()
        ev = self.total_earned_value()
        return ev / ac if ac > 0 else 1.0

    def schedule_performance_index(self) -> float:
        pv = self.total_planned_value()
        ev = self.total_earned_value()
        return ev / pv if pv > 0 else 1.0