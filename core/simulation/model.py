# Contenido completo, final y definitivo de core/simulation/model.py

from mesa import Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from typing import Dict, List
import random
import numpy as np

# Se importan las clases que el modelo necesita conocer
from core.entities import Task, Resource, Team
from core.agents import TaskAgent
from core.simulation.parameters import SimulationParameters
from core.simulation.assignment import BaseAssignmentStrategy, STRATEGY_MAP


class ProjectManagementModel(Model):
    """
    El modelo principal de la simulación. Orquesta a los agentes,
    el avance de las tareas y la recolección de datos.
    """

    # MODIFICADO: La firma del constructor ahora es compatible con el Runner.
    # Acepta listas de tareas y recursos, no el objeto Project completo.
    def __init__(self, tasks: List[Task], resources: List[Resource], params: SimulationParameters):
        super().__init__()
        self.params = params
        self.schedule = RandomActivation(self)

        # El modelo ahora trabaja con su propia copia de las tareas y recursos
        self.task_map: Dict[int, Task] = {task.id: task for task in tasks}

        self.teams: List[Team] = []
        self.team_map: Dict[int, Team] = {}

        self.project_agents: List[TaskAgent] = []
        self.agents_by_resource_id: Dict[int, TaskAgent] = {}
        self.agent_to_team_map: Dict[int, Team] = {}

        for resource in resources:
            # Se crea un agente por cada recurso, usando el constructor moderno
            agent = TaskAgent(unique_id=resource.id, model=self, resource=resource)
            self.project_agents.append(agent)
            self.schedule.add(agent)
            self.agents_by_resource_id[resource.id] = agent

        self._create_teams_from_config()

        # Se selecciona e instancia la estrategia de asignación desde la configuración
        strategy_class = STRATEGY_MAP.get(params.assignment_strategy)
        if not strategy_class:
            raise ValueError(f"Estrategia de asignación desconocida: '{params.assignment_strategy}'")
        self.assignment_strategy: BaseAssignmentStrategy = strategy_class(self)
        print(f"Info (Model): Usando estrategia: {strategy_class.__name__}")

        # El colector de datos con todas las métricas, incluyendo las de equipo
        self.datacollector = DataCollector(
            model_reporters={
                "Time": lambda m: m.schedule.time,
                "Completion": lambda m: m.project_completion_percentage(),
                "ActualCost": lambda m: m.total_actual_cost(),
                "EarnedValue": lambda m: m.total_earned_value(),
                "CPI": lambda m: m.cost_performance_index(),
                "SPI": lambda m: m.schedule_performance_index(),
                "ActiveAgents": lambda m: sum(1 for a in self.schedule.agents if not a.is_available()),
                "AvgTeamMorale": lambda m: self.get_average_team_morale(),
                "AvgTeamCohesion": lambda m: self.get_average_team_cohesion()
            }
        )
        self.running = True

    def _create_teams_from_config(self):
        team_definitions = self.params.team_definitions
        if not team_definitions: return
        print("\nCreando equipos desde la configuración...")
        for team_def in team_definitions:
            team_id, name, member_ids = team_def.get("id"), team_def.get("name"), team_def.get("member_resource_ids",
                                                                                               [])
            team_members = [self.agents_by_resource_id[res_id] for res_id in member_ids if
                            res_id in self.agents_by_resource_id]
            if team_members:
                team = Team(team_id, name, team_members)
                self.teams.append(team)
                self.team_map[team_id] = team
                for member_agent in team_members:
                    member_agent.team = team
                    self.agent_to_team_map[member_agent.unique_id] = team
                print(f" -> Equipo Creado: {team}")
        print("-" * 20)

    def _update_task_progress(self):
        for task in self.task_map.values():
            if task.status == "done": continue
            work_increment = 0.0
            if task.assigned_team:
                team = task.assigned_team
                if not team.is_busy() or team.current_task.id != task.id: continue
                team_base_work = len(team.members)
                team_efficiency = team.cohesion_factor
                work_increment = team_base_work * team_efficiency
            elif task.assigned_resource:
                agent = self.agents_by_resource_id.get(task.required_resource_id)
                if agent and not agent.is_available() and agent.current_task.id == task.id:
                    work_increment = 1.0 * agent.efficiency
            if work_increment > 0:
                error = random.uniform(-self.params.error_margin, self.params.error_margin)
                total_work = work_increment * (1 + error)
                progress_increment = total_work / task.duration if task.duration > 0 else 1.0
                task.update_progress(progress_increment)
                task.real_duration += 1
            if task.progress >= 1.0:
                if task.assigned_team:
                    task.assigned_team.boost_morale()
                    for agent in task.assigned_team.members: agent.release()
                    task.assigned_team.release_task()
                elif task.assigned_resource:
                    agent = self.agents_by_resource_id.get(task.required_resource_id)
                    if agent: agent.release()

    def _update_team_social_dynamics(self):
        for team in self.teams:
            team.regress_to_mean()
            if team.is_busy():
                team.time_on_current_task += 1
                task_duration = team.current_task.duration
                if task_duration > 0 and team.time_on_current_task > (task_duration * 1.5):
                    team.decay_morale(amount=0.02)

    def _introduce_random_events(self):
        if self.random.random() < 0.02 and self.teams:
            team_afectado = self.random.choice(self.teams)
            if self.random.random() < 0.5:
                team_afectado.decay_morale(amount=0.4)
                print(
                    f"** EVENTO (t={self.schedule.time}): ¡Problema técnico! La moral del {team_afectado.name} se resiente.")
            else:
                team_afectado.boost_morale(amount=0.3)
                print(f"** EVENTO (t={self.schedule.time}): ¡Gran avance! El {team_afectado.name} está motivado.")

    def _are_dependencies_met(self, task: Task) -> bool:
        return all(dep.status == "done" for dep in task.dependencies)

    def step(self):
        if all(t.status == "done" for t in self.task_map.values()):
            if self.running:
                self.datacollector.collect(self)
                self.running = False
            return

        self.assignment_strategy.assign_tasks()
        self.schedule.step()
        self._update_task_progress()
        self._update_team_social_dynamics()
        self._introduce_random_events()
        self.datacollector.collect(self)

    def run_model(self):
        for i in range(self.params.max_steps):
            if not self.running: break
            self.step()

    # --- Métodos para el DataCollector ---
    def get_average_team_morale(self) -> float:
        if not self.teams: return 0.0
        return float(np.mean([team.morale for team in self.teams]))

    def get_average_team_cohesion(self) -> float:
        if not self.teams: return 0.0
        return float(np.mean([team.cohesion_factor for team in self.teams]))

    def project_completion_percentage(self) -> float:
        total_duration = sum(t.duration for t in self.task_map.values() if t.duration > 0)
        if total_duration == 0: return 100.0
        completed_duration = sum(t.duration * t.progress for t in self.task_map.values())
        return (completed_duration / total_duration) * 100

    def total_actual_cost(self) -> float:
        return sum(agent.worked_hours * agent.resource.cost_per_hour for agent in self.project_agents)

    def total_earned_value(self) -> float:
        return sum(task.estimated_cost * task.progress for task in self.task_map.values())

    def total_planned_value(self) -> float:
        current_time = self.schedule.time
        return sum(t.estimated_cost for t in self.task_map.values() if self._is_task_planned_to_start(t, current_time))

    def _is_task_planned_to_start(self, task: Task, current_time: int) -> bool:
        return all(self.task_map[dep.id].status == "done" for dep in task.dependencies)

    def cost_performance_index(self) -> float:
        ac = self.total_actual_cost()
        ev = self.total_earned_value()
        return ev / ac if ac > 0 else 1.0

    def schedule_performance_index(self) -> float:
        pv = self.total_planned_value()
        ev = self.total_earned_value()
        return ev / pv if pv > 0 else 1.0