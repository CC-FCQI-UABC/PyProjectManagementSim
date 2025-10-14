import os
import sys
import random
from dataclasses import dataclass
from typing import Dict, List, Any
import numpy as np
import pandas as pd
from datetime import datetime
import argparse

# Add project root to path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(CURRENT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Lazy-import core simulator modules inside functions to avoid import-time errors


# Optional Plotly import for visualization mode
try:
    import plotly.graph_objects as go
    import plotly.io as pio
    PLOTLY_AVAILABLE = True
except Exception:
    PLOTLY_AVAILABLE = False

# Optional Dash import for live foreground visualization
try:
    from dash import Dash, dcc, html, Output, Input, no_update
    DASH_AVAILABLE = True
except Exception:
    DASH_AVAILABLE = False

# Optional Mesa visualization imports for interactive server mode
# We separate core Mesa and visualization to be robust across versions.
MESA_CORE_AVAILABLE = False
MESA_VIS_AVAILABLE = False
TEXT_ELEMENT_AVAILABLE = False
_MESA_VIS_IMPORT_ERROR = None
try:
    from mesa import Agent as MesaAgent, Model as MesaModel
    from mesa.time import RandomActivation
    from mesa.space import MultiGrid
    from mesa.datacollection import DataCollector
    MESA_CORE_AVAILABLE = True
    try:
        # Prefer classic mesa.visualization if available
        from mesa.visualization.modules import CanvasGrid, ChartModule
        try:
            from mesa.visualization.modules import TextElement
            TEXT_ELEMENT_AVAILABLE = True
        except Exception:
            TEXT_ELEMENT_AVAILABLE = False
        from mesa.visualization.ModularVisualization import ModularServer
        MESA_VIS_AVAILABLE = True
    except Exception as _e1:
        # Fallback to the external package 'mesa-visualization' (newer split)
        try:
            from mesa_visualization.modules import CanvasGrid, ChartModule
            try:
                from mesa_visualization.modules import TextElement
                TEXT_ELEMENT_AVAILABLE = True
            except Exception:
                TEXT_ELEMENT_AVAILABLE = False
            from mesa_visualization.ModularVisualization import ModularServer
            MESA_VIS_AVAILABLE = True
        except Exception as _e2:
            _MESA_VIS_IMPORT_ERROR = f"mesa.visualization error: {_e1}; mesa_visualization error: {_e2}"
            MESA_VIS_AVAILABLE = False
except Exception as _e:
    _MESA_VIS_IMPORT_ERROR = f"Mesa core import error: {_e}"
    MESA_CORE_AVAILABLE = False
    MESA_VIS_AVAILABLE = False # If core fails, visualization is also unavailable


# Disable Solara to keep compatibility with Mesa < 2 (core depends on mesa.time)
SOLARA_AVAILABLE = False
SOLARA_MSG = "Solara disabled (using Mesa < 2 for core compatibility)"


# ------------------------------
# Mesa Interactive Simulation
# ------------------------------

if MESA_CORE_AVAILABLE:

    class TeamAgent(MesaAgent):
        """
        Visual agent that spawns individually, forms teams with nearby agents, and moves as a team
        toward a target zone to complete a shared task.
        """
        def __init__(self, unique_id, model):
            super().__init__(unique_id, model)
            self.team_id = None
            self.color = "#1f77b4"  # default color
            self.in_team = False
            self.task_done = False

        def step(self):
            # If not in a team, try to form a team with nearby agents
            if not self.in_team:
                neighbors = self.model.grid.get_neighbors(self.pos, moore=True, include_center=False, radius=1)
                candidate_ids = [a.unique_id for a in neighbors if isinstance(a, TeamAgent) and not a.in_team]
                candidate_ids.append(self.unique_id)
                candidate_ids = sorted(set(candidate_ids))
                if len(candidate_ids) >= self.model.team_threshold:
                    # Form a new team
                    new_team_id = self.unique_id  # simple seed as team id
                    for aid in candidate_ids:
                        agent = self.model.agent_by_id[aid]
                        agent.in_team = True
                        agent.team_id = new_team_id
                        agent.color = self.model.team_color_map.setdefault(new_team_id, self.model.random_color())

            # If in a team and task not done, move towards target zone as a group
            if self.in_team and not self.task_done:
                tx, ty = self.model.target_pos
                x, y = self.pos
                dx = 1 if tx > x else -1 if tx < x else 0
                dy = 1 if ty > y else -1 if ty < y else 0
                new_pos = (x + dx, y + dy)
                if self.model.grid.is_cell_empty(new_pos) or new_pos == self.model.target_pos:
                    self.model.grid.move_agent(self, new_pos)
                # Check if team reached target
                if new_pos == self.model.target_pos:
                    self.task_done = True
                    self.color = "#2ca02c"  # green when task done


    class TeamFormationModel(MesaModel):
        """
        Model that spawns agents gradually, lets them form teams via proximity,
        and complete a task by reaching a target zone. Includes metrics for UI.
        """
        def __init__(self, width=20, height=20, num_agents=25, team_threshold=3):
            super().__init__()
            self.width = width
            self.height = height
            self.grid = MultiGrid(width, height, torus=False)
            self.schedule = RandomActivation(self)
            self.num_agents_target = num_agents
            self.spawned_agents = 0
            self.team_threshold = team_threshold
            self.agent_by_id: Dict[int, TeamAgent] = {}
            self.team_color_map: Dict[int, str] = {}
            self.target_pos = (width - 2, height - 2)

            self.datacollector = DataCollector(model_reporters={
                "AgentsCreated": lambda m: m.spawned_agents,
                "TeamsFormed": lambda m: m.count_teams(),
                "TasksCompleted": lambda m: m.count_completed(),
            })

            # Spawn an initial agent to start
            self.spawn_one_agent()

        def random_color(self) -> str:
            return "#%06x" % self.random.randrange(0x1000000)

        def spawn_one_agent(self):
            if self.spawned_agents >= self.num_agents_target:
                return
            aid = self.spawned_agents + 1
            agent = TeamAgent(aid, self)
            self.agent_by_id[aid] = agent
            self.schedule.add(agent)
            # Place at random empty position
            placed = False
            for _ in range(50):
                x = self.random.randrange(self.width)
                y = self.random.randrange(self.height)
                if self.grid.is_cell_empty((x, y)):
                    self.grid.place_agent(agent, (x, y))
                    placed = True
                    break
            if not placed:
                # fallback: place anyway
                self.grid.place_agent(agent, (self.random.randrange(self.width), self.random.randrange(self.height)))
            self.spawned_agents += 1

        def step(self):
            # Gradually create agents one-by-one
            if self.spawned_agents < self.num_agents_target:
                self.spawn_one_agent()
            self.schedule.step()
            self.datacollector.collect(self)

        def count_teams(self) -> int:
            team_ids = set()
            for a in self.agent_by_id.values():
                if a.in_team and a.team_id is not None:
                    team_ids.add(a.team_id)
            return len(team_ids)

        def count_completed(self) -> int:
            return sum(1 for a in self.agent_by_id.values() if a.task_done)


    def agent_portrayal(agent: "TeamAgent"):
        # Visual encoding for each agent on the grid
        portrayal = {
            "Shape": "circle",
            "Filled": "true",
            "Color": agent.color,
            "Layer": 1,
            "r": 0.7,
        }
        return portrayal


    if TEXT_ELEMENT_AVAILABLE:
        class MetricsText(TextElement):
            # Side panel showing simple metrics
            def render(self, model: "TeamFormationModel"):
                return (
                    f"Agents created: {model.spawned_agents}\n"
                    f"Teams formed: {model.count_teams()}\n"
                    f"Tasks completed: {model.count_completed()}\n"
                    f"Team threshold: {model.team_threshold}\n"
                )


    def start_mesa_interactive(grid_w: int, grid_h: int, num_agents: int, team_threshold: int) -> None:
        if not MESA_VIS_AVAILABLE:
            msg = _MESA_VIS_IMPORT_ERROR or "Unknown visualization import error"
            print(f"Mesa visualization modules not available. Install/update mesa or mesa's viz extras. Details: {msg}")
            return
        grid = CanvasGrid(agent_portrayal, grid_w, grid_h, 600, 600)
        chart = ChartModule([
            {"Label": "AgentsCreated", "Color": "#1f77b4"},
            {"Label": "TeamsFormed", "Color": "#ff7f0e"},
            {"Label": "TasksCompleted", "Color": "#2ca02c"},
        ], data_collector_name='datacollector')
        elements = [grid, chart]
        if TEXT_ELEMENT_AVAILABLE:
            elements.append(MetricsText())

        server = ModularServer(
            TeamFormationModel,
            elements,
            "Team Formation & Task Simulation",
            {"width": grid_w, "height": grid_h, "num_agents": num_agents, "team_threshold": team_threshold}
        )
        server.port = 8521
        server.launch()
else:
    def start_mesa_interactive(grid_w: int, grid_h: int, num_agents: int, team_threshold: int) -> None:
        msg = _MESA_VIS_IMPORT_ERROR or "Mesa not importable"
        print(f"Mesa is not installed or not importable. Please: pip install mesa. Details: {msg}")

@dataclass
class RLTrainingConfig:
    project_filename: str = "Software Development Plan.xml"
    data_folder: str = "data"
    episodes: int = 20
    max_steps: int = 1500
    epsilon_start: float = 0.3
    epsilon_end: float = 0.05
    epsilon_decay_episodes: int = 15
    efficiency_step: float = 0.05  # how much to adjust efficiency per update
    efficiency_min: float = 0.5
    efficiency_max: float = 1.5
    assignment_strategy: str = "parallel"
    error_margin: float = 0.15
    output_dir: str = os.path.join("core", "generated")
    output_filename: str = "rl_training_metrics.csv"


def linear_decay(start: float, end: float, step_idx: int, total_steps: int) -> float:
    if total_steps <= 1:
        return end
    ratio = min(1.0, max(0.0, step_idx / (total_steps - 1)))
    return start + (end - start) * ratio


def run_episode(project: "Project", config: RLTrainingConfig) -> Dict[str, float]:
    from core.simulation.parameters import SimulationParameters
    from core.simulation.model import ProjectManagementModel
    params = SimulationParameters(
        error_margin=config.error_margin,
        reassignment_frequency=0,
        max_steps=config.max_steps,
        team_definitions=[],
        assignment_strategy=config.assignment_strategy,
    )

    model = ProjectManagementModel(
        tasks=project.get_tasks_for_simulation(),
        resources=project.get_resources_for_simulation(),
        params=params,
    )

    # Run until completion or max_steps
    model.run_model()

    # Metrics from this episode
    completion = model.project_completion_percentage()
    steps = model.schedule.time
    ev = model.total_earned_value()
    ac = model.total_actual_cost()
    pv = model.total_planned_value()
    cpi = ev / ac if ac > 0 else 1.0
    spi = ev / pv if pv > 0 else 1.0

    return {
        "completion": completion,
        "steps": steps,
        "EV": ev,
        "AC": ac,
        "PV": pv,
        "CPI": cpi,
        "SPI": spi,
    }


def apply_bandit_update(model: "ProjectManagementModel", reward: float, epsilon: float, cfg: RLTrainingConfig) -> None:
    # Simple per-agent epsilon-greedy: with probability epsilon, explore by random +/- step; otherwise exploit towards global reward signal
    for agent in model.project_agents:
        if random.random() < epsilon:
            delta = cfg.efficiency_step if random.random() < 0.5 else -cfg.efficiency_step
        else:
            # Exploit: if reward is good, increase slightly; if bad, decrease
            delta = cfg.efficiency_step if reward >= 1.0 else -cfg.efficiency_step
        new_eff = max(cfg.efficiency_min, min(cfg.efficiency_max, agent.efficiency + delta))
        agent.efficiency = new_eff


def run_episode_with_traces(project: "Project", config: RLTrainingConfig) -> Dict[str, Any]:
    from core.simulation.parameters import SimulationParameters
    from core.simulation.model import ProjectManagementModel
    params = SimulationParameters(
        error_margin=config.error_margin,
        reassignment_frequency=0,
        max_steps=config.max_steps,
        team_definitions=[],
        assignment_strategy=config.assignment_strategy,
    )

    model = ProjectManagementModel(
        tasks=project.get_tasks_for_simulation(),
        resources=project.get_resources_for_simulation(),
        params=params,
    )

    # Pre-allocate traces
    times: List[int] = []
    completion: List[float] = []
    pv_list: List[float] = []
    ev_list: List[float] = []
    ac_list: List[float] = []
    cpi_list: List[float] = []
    spi_list: List[float] = []

    agent_ids = [a.unique_id for a in model.project_agents]
    agent_id_to_index = {aid: idx for idx, aid in enumerate(agent_ids)}
    busy_matrix: List[List[int]] = []  # time x agents

    step_counter = 0
    while model.running and step_counter < config.max_steps:
        # Record before step
        t = model.schedule.time
        times.append(t)
        pv = model.total_planned_value()
        ev = model.total_earned_value()
        ac = model.total_actual_cost()
        cpi = ev / ac if ac > 0 else 1.0
        spi = ev / pv if pv > 0 else 0.0
        total = len(model.task_map)
        done = sum(1 for task in model.task_map.values() if task.status.value == "done")
        comp = (done / total) * 100 if total > 0 else 0.0

        completion.append(comp)
        pv_list.append(pv)
        ev_list.append(ev)
        ac_list.append(ac)
        cpi_list.append(cpi)
        spi_list.append(spi)

        # Agent activity snapshot (1 busy, 0 idle)
        busy_row = [0] * len(agent_ids)
        for agent in model.project_agents:
            busy_row[agent_id_to_index[agent.unique_id]] = 0 if agent.is_available() else 1
        busy_matrix.append(busy_row)

        # Advance one step
        model.step()
        step_counter += 1

    return {
        "times": times,
        "completion": completion,
        "pv": pv_list,
        "ev": ev_list,
        "ac": ac_list,
        "cpi": cpi_list,
        "spi": spi_list,
        "agent_ids": agent_ids,
        "busy_matrix": busy_matrix,
        "total_steps": step_counter,
    }


def build_plotly_visualization(traces: Dict[str, Any], output_path: str) -> None:
    if not PLOTLY_AVAILABLE:
        print("Plotly is not installed. Please: pip install plotly")
        return

    times = traces["times"]
    # Line charts for Progress, CPI, SPI
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=times, y=traces["completion"], mode="lines", name="Completion %"))
    fig1.add_trace(go.Scatter(x=times, y=traces["cpi"], mode="lines", name="CPI"))
    fig1.add_trace(go.Scatter(x=times, y=traces["spi"], mode="lines", name="SPI"))
    fig1.update_layout(title="Progress and Performance Indices", xaxis_title="Time", yaxis_title="Value")

    # Line charts for EVM values
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=times, y=traces["pv"], mode="lines", name="PV"))
    fig2.add_trace(go.Scatter(x=times, y=traces["ev"], mode="lines", name="EV"))
    fig2.add_trace(go.Scatter(x=times, y=traces["ac"], mode="lines", name="AC"))
    fig2.update_layout(title="EVM Values", xaxis_title="Time", yaxis_title="Cost ($)")

    # Agent activity heatmap (agents x time)
    z = np.array(traces["busy_matrix"]).T if traces["busy_matrix"] else np.zeros((0, 0))
    fig3 = go.Figure(data=go.Heatmap(z=z, x=times, y=[str(aid) for aid in traces["agent_ids"]], colorscale=[[0, "#e0f3ff"], [1, "#1f77b4"]]))
    fig3.update_layout(title="Agent Activity (1=busy, 0=idle)", xaxis_title="Time", yaxis_title="Agent ID")

    # Write a single HTML with all figures stacked
    html_parts = [
        pio.to_html(fig1, include_plotlyjs="cdn", full_html=False),
        pio.to_html(fig2, include_plotlyjs=False, full_html=False),
        pio.to_html(fig3, include_plotlyjs=False, full_html=False),
    ]
    html = "\n<hr/>\n".join(html_parts)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("<html><head><meta charset='utf-8'><title>RL Visualization</title></head><body>\n")
        f.write("<h2>Reinforcement Learning Episode Visualization</h2>\n")
        f.write(html)
        f.write("\n</body></html>")
    print(f"Visualization saved to: {output_path}")


def start_live_dashboard(project: "Project", cfg: RLTrainingConfig) -> None:
    from core.simulation.parameters import SimulationParameters
    from core.simulation.model import ProjectManagementModel
    if not DASH_AVAILABLE:
        print("Dash is not installed. Please: pip install dash")
        return

    params = SimulationParameters(
        error_margin=cfg.error_margin,
        reassignment_frequency=0,
        max_steps=cfg.max_steps,
        team_definitions=[],
        assignment_strategy=cfg.assignment_strategy,
    )

    # Create a persistent model instance for live stepping
    live_model = ProjectManagementModel(
        tasks=project.get_tasks_for_simulation(),
        resources=project.get_resources_for_simulation(),
        params=params,
    )

    # Live data buffers
    live_times: List[int] = []
    live_completion: List[float] = []
    live_cpi: List[float] = []
    live_spi: List[float] = []
    live_agent_ids = [a.unique_id for a in live_model.project_agents]
    agent_id_to_index = {aid: idx for idx, aid in enumerate(live_agent_ids)}
    live_busy_matrix: List[List[int]] = []

    app = Dash(__name__)
    app.title = "ABP RL Live"

    app.layout = html.Div([
        html.H2("ABP Simulator - Live RL Episode"),
        html.Div(id="status-text", style={"marginBottom": "10px"}),
        html.Div(id="agents-teams-summary", style={"marginBottom": "10px", "whiteSpace": "pre-wrap", "fontFamily": "monospace"}),
        dcc.Graph(id="progress-graph"),
        dcc.Graph(id="agents-heatmap"),
        dcc.Graph(id="gantt-graph"),
        dcc.Interval(id="tick", interval=500, n_intervals=0),
    ], style={"maxWidth": "1100px", "margin": "0 auto", "fontFamily": "Arial, sans-serif"})

    # Track task start/end times for Gantt-like view
    task_start_time: Dict[int, int] = {}
    task_end_time: Dict[int, int] = {}

    @app.callback(
        [Output("progress-graph", "figure"),
         Output("agents-heatmap", "figure"),
         Output("gantt-graph", "figure"),
         Output("status-text", "children"),
         Output("agents-teams-summary", "children")],
        Input("tick", "n_intervals")
    )
    def on_tick(_):
        nonlocal live_model, live_times, live_completion, live_cpi, live_spi, live_busy_matrix, task_start_time, task_end_time

        # Stop stepping if completed
        if not live_model.running:
            status = f"Completed at step {live_model.schedule.time}."
            # Build agents/teams summary
            busy_agents = sum(1 for a in live_model.project_agents if not a.is_available())
            summary_lines = [
                f"Agents: {len(live_model.project_agents)} (busy: {busy_agents})",
                f"Teams: {len(live_model.teams)}",
                "",
            ]
            for team in live_model.teams:
                members = ", ".join(f"{m.id}" for m in team.members)
                current = team.current_task.id if getattr(team, 'current_task', None) else "-"
                summary_lines.append(f"Team {team.id} [{members}] -> Task {current}")
            summary = "\n".join(summary_lines)

            prog_fig = go.Figure()
            prog_fig.add_trace(go.Scatter(x=live_times, y=live_completion, mode="lines", name="Completion %"))
            prog_fig.add_trace(go.Scatter(x=live_times, y=live_cpi, mode="lines", name="CPI"))
            prog_fig.add_trace(go.Scatter(x=live_times, y=live_spi, mode="lines", name="SPI"))
            prog_fig.update_layout(title="Progress / CPI / SPI", xaxis_title="Time", yaxis_title="Value")

            z = np.array(live_busy_matrix).T if live_busy_matrix else np.zeros((0, 0))
            heat = go.Figure(data=go.Heatmap(z=z, x=live_times, y=[str(a) for a in live_agent_ids], colorscale=[[0, "#e0f3ff"], [1, "#1f77b4"]]))
            heat.update_layout(title="Agent Activity (1=busy, 0=idle)", xaxis_title="Time", yaxis_title="Agent ID")

            # Build Gantt-like figure from recorded start/end times
            gantt_fig = go.Figure()
            for task in live_model.task_map.values():
                tid = task.id
                if tid in task_start_time:
                    start = task_start_time[tid]
                    end = task_end_time.get(tid, live_times[-1] if live_times else 0)
                    gantt_fig.add_trace(go.Bar(x=[max(0, end - start)], y=[str(tid)], base=[start], orientation='h', name=f"Task {tid}", hovertext=f"Task {tid}"))
            gantt_fig.update_layout(barmode='overlay', title="Task Schedule (Gantt-like)", xaxis_title="Time", yaxis_title="Task ID", showlegend=False)

            return prog_fig, heat, gantt_fig, status, summary

        # Record before this step
        t = live_model.schedule.time
        pv = live_model.total_planned_value()
        ev = live_model.total_earned_value()
        ac = live_model.total_actual_cost()
        cpi = ev / ac if ac > 0 else 1.0
        spi = ev / pv if pv > 0 else 0.0
        total = len(live_model.task_map)
        done = sum(1 for task in live_model.task_map.values() if task.status.value == "done")
        comp = (done / total) * 100 if total > 0 else 0.0

        live_times.append(t)
        live_completion.append(comp)
        live_cpi.append(cpi)
        live_spi.append(spi)

        # Busy row snapshot
        busy_row = [0] * len(live_agent_ids)
        for agent in live_model.project_agents:
            busy_row[agent_id_to_index[agent.unique_id]] = 0 if agent.is_available() else 1
        live_busy_matrix.append(busy_row)

        # Track task start/end times
        for task in live_model.task_map.values():
            tid = task.id
            if task.progress > 0 and tid not in task_start_time:
                task_start_time[tid] = t
            if task.status.value == "done" and tid not in task_end_time:
                task_end_time[tid] = t

        # Advance simulation one step
        live_model.step()

        status = f"Step {t} | Completion {comp:.1f}% | CPI {cpi:.2f} | SPI {spi:.2f}"
        busy_agents = sum(1 for a in live_model.project_agents if not a.is_available())
        summary_lines = [
            f"Agents: {len(live_model.project_agents)} (busy: {busy_agents})",
            f"Teams: {len(live_model.teams)}",
            "",
        ]
        for team in live_model.teams:
            members = ", ".join(f"{m.id}" for m in team.members)
            current = team.current_task.id if getattr(team, 'current_task', None) else "-"
            summary_lines.append(f"Team {team.id} [{members}] -> Task {current}")
        summary = "\n".join(summary_lines)

        # Build figures
        prog_fig = go.Figure()
        prog_fig.add_trace(go.Scatter(x=live_times, y=live_completion, mode="lines", name="Completion %"))
        prog_fig.add_trace(go.Scatter(x=live_times, y=live_cpi, mode="lines", name="CPI"))
        prog_fig.add_trace(go.Scatter(x=live_times, y=live_spi, mode="lines", name="SPI"))
        prog_fig.update_layout(title="Progress / CPI / SPI", xaxis_title="Time", yaxis_title="Value")

        z = np.array(live_busy_matrix).T if live_busy_matrix else np.zeros((0, 0))
        heat = go.Figure(data=go.Heatmap(z=z, x=live_times, y=[str(a) for a in live_agent_ids], colorscale=[[0, "#e0f3ff"], [1, "#1f77b4"]]))
        heat.update_layout(title="Agent Activity (1=busy, 0=idle)", xaxis_title="Time", yaxis_title="Agent ID")

        # Gantt-like figure using start/end times so far; if running, extend to current t
        gantt_fig = go.Figure()
        for task in live_model.task_map.values():
            tid = task.id
            if tid in task_start_time:
                start = task_start_time[tid]
                end = task_end_time.get(tid, t)
                gantt_fig.add_trace(go.Bar(x=[max(0, end - start)], y=[str(tid)], base=[start], orientation='h', name=f"Task {tid}", hovertext=f"Task {tid}"))
        gantt_fig.update_layout(barmode='overlay', title="Task Schedule (Gantt-like)", xaxis_title="Time", yaxis_title="Task ID", showlegend=False)

        return prog_fig, heat, gantt_fig, status, summary

    app.run(debug=False, port=8050)


def main():
    parser = argparse.ArgumentParser(description="RL Training and Visualization for ABP Simulator")
    parser.add_argument("--mode", choices=["train", "visual", "live", "mesa", "pygame", "pygame_core"], default="live", help="Run training, offline visual, live dashboard, Mesa sim, Pygame toy, or Pygame tied to core")
    parser.add_argument("--episodes", type=int, default=None, help="Number of training episodes")
    parser.add_argument("--grid", type=str, default=None, help="Grid size WxH for Mesa mode, e.g. 20x20")
    parser.add_argument("--agents", type=int, default=None, help="Num agents for Mesa mode")
    parser.add_argument("--team", type=int, default=None, help="Team size threshold for Mesa mode")
    args = parser.parse_args()

    cfg = RLTrainingConfig()
    if args.episodes is not None:
        cfg.episodes = args.episodes

    # Load project template once
    from core.readers.xml_reader import XmlProjectReader
    from core.project import Project
    reader = XmlProjectReader()
    project_path = os.path.join(PROJECT_ROOT, cfg.data_folder, cfg.project_filename)
    project_data = reader.load(project_path)
    project_template = Project(project_data)

    os.makedirs(os.path.join(PROJECT_ROOT, cfg.output_dir), exist_ok=True)

    if args.mode == "visual":
        # Single episode with per-step traces and Plotly HTML output
        episode_project = Project(project_template.get_project_data_copy()) if hasattr(project_template, "get_project_data_copy") else Project(project_data)
        traces = run_episode_with_traces(episode_project, cfg)
        html_path = os.path.join(PROJECT_ROOT, cfg.output_dir, "rl_visualization.html")
        build_plotly_visualization(traces, html_path)
        return

    if args.mode == "live":
        episode_project = Project(project_template.get_project_data_copy()) if hasattr(project_template, "get_project_data_copy") else Project(project_data)
        start_live_dashboard(episode_project, cfg)
        return

    if args.mode == "pygame_core":
        # Real-time core-driven pygame: step the real model each frame and visualize agents and tasks
        try:
            import pygame
        except Exception:
            print("Pygame is not installed. Please: pip install pygame")
            return

        from core.simulation.parameters import SimulationParameters
        from core.simulation.model import ProjectManagementModel

        # Hardcoded teams like plot_simulation_experiment.py
        team_definitions_config = [
            { "id": 101, "name": "Analysis and Design Team", "member_resource_ids": [1, 2] },
            { "id": 102, "name": "Development and Testing Team", "member_resource_ids": [3, 4] }
        ]

        params = SimulationParameters(
            error_margin=cfg.error_margin,
            reassignment_frequency=0,
            max_steps=cfg.max_steps,
            team_definitions=team_definitions_config,
            assignment_strategy=cfg.assignment_strategy,
        )
        model = ProjectManagementModel(
            tasks=project_template.get_tasks_for_simulation(),
            resources=project_template.get_resources_for_simulation(),
            params=params,
        )

        pygame.init()
        width, height = 1200, 720
        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Core-driven Pygame - Teams & Tasks")
        clock = pygame.time.Clock()

        rng = random.Random(123)
        agent_positions = {}
        for agent in model.project_agents:
            agent_positions[agent.unique_id] = [rng.randint(40, width - 380), rng.randint(60, height - 60)]

        # Build visual rects for tasks (right panel grid)
        tasks_cols, tasks_rows = 4, 8
        MAX_RENDER = tasks_cols * tasks_rows
        task_ids = sorted([t.id for t in model.task_map.values()])[:MAX_RENDER]
        task_rects = {}
        margin_left, margin_top = width - 360, 60
        tw, th, gx, gy = 72, 16, 90, 52
        for idx, tid in enumerate(task_ids):
            row, col = idx // tasks_cols, idx % tasks_cols
            x = margin_left + col * gx
            y = margin_top + row * gy
            task_rects[tid] = pygame.Rect(x, y, tw, th)

        # Epsilon for online learning (decays over time)
        online_epsilon = 0.2
        epsilon_decay = 0.995

        def draw(pv: float, ev: float, ac: float, cpi: float, spi: float):
            screen.fill((20, 20, 30))
            # Draw tasks with real progress from the core
            for tid in task_ids:
                rect = task_rects[tid]
                task = model.task_map.get(tid)
                if not task:
                    continue
                done = (task.status.value == "done")
                # available if all deps done
                avail = all(model.task_map[d.id].status.value == "done" for d in task.dependencies)
                base_color = (100, 100, 120) if not done else (80, 160, 100)
                if not avail and not done:
                    base_color = (70, 70, 80)
                pygame.draw.rect(screen, base_color, rect, border_radius=4)
                # progress bar from core progress
                pr = getattr(task, "progress", 0.0)
                if pr > 0:
                    pr_w = int(rect.width * pr)
                    pygame.draw.rect(screen, (60, 200, 120), pygame.Rect(rect.x, rect.y, pr_w, rect.height), border_radius=4)
                pygame.draw.rect(screen, (180, 180, 200), rect, width=1, border_radius=4)
                font = pygame.font.SysFont("Arial", 14)
                label = font.render(f"HW {tid}", True, (220, 220, 235))
                screen.blit(label, (rect.x, rect.y - 18))

            # Draw agents, colored by team membership
            team_ids = set([team.id for team in model.teams])
            for agent in model.project_agents:
                ax, ay = agent_positions[agent.unique_id]
                in_team = (agent.team is not None)
                color = (78, 205, 196) if not in_team else (255, 107, 107)
                pygame.draw.circle(screen, color, (int(ax), int(ay)), 6)

            # Draw assignment lines (from team centroid to their current task, if any)
            for team in model.teams:
                if team.current_task is not None:
                    # team centroid from member positions
                    members = team.members
                    if members:
                        sx = sy = 0
                        for res in members:
                            pos = agent_positions.get(res.id)
                            if pos:
                                sx += pos[0]
                                sy += pos[1]
                        cx, cy = sx / len(members), sy / len(members)
                        rect = task_rects.get(team.current_task.id)
                        if rect:
                            pygame.draw.line(screen, (120, 120, 220), (int(cx), int(cy)), rect.center, 1)

            # HUD
            font = pygame.font.SysFont("Arial", 16)
            completed = sum(1 for t in model.task_map.values() if t.status.value == "done")
            text = font.render(f"Agents: {len(model.project_agents)}  Teams: {len(model.teams)}  Tasks: {len(model.task_map)}  Completed: {completed}", True, (200, 200, 220))
            screen.blit(text, (12, 10))
            # EVM line
            evm_text = font.render(f"PV ${pv:,.0f}  EV ${ev:,.0f}  AC ${ac:,.0f}  CPI {cpi:.2f}  SPI {spi:.2f}", True, (200, 200, 220))
            screen.blit(evm_text, (12, 32))

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Step the real model once
            if model.running:
                model.step()

            # Online RL tweak: every 50 ticks, adjust efficiencies via epsilon-greedy on CPI/SPI + completion
            if model.schedule.time % 50 == 0 and model.schedule.time > 0:
                # Reward similar to training loop
                pv = model.total_planned_value()
                ev = model.total_earned_value()
                ac = model.total_actual_cost()
                cpi = ev / ac if ac > 0 else 1.0
                spi = ev / pv if pv > 0 else 1.0
                completion = model.project_completion_percentage() / 100.0
                reward = max(0.0, (completion + (1 - abs(1.0 - cpi)) + (1 - abs(1.0 - spi))) / 3.0)
                apply_bandit_update(model, reward, online_epsilon, cfg)
                online_epsilon = max(0.05, online_epsilon * epsilon_decay)

            # Move agent sprites slightly to visualize activity (cosmetic only)
            for agent in model.project_agents:
                ax, ay = agent_positions[agent.unique_id]
                ax += rng.choice([-1, 0, 1])
                ay += rng.choice([-1, 0, 1])
                ax = min(max(20, ax), width - 380)
                ay = min(max(40, ay), height - 40)
                agent_positions[agent.unique_id] = [ax, ay]

            # Compute EVM for display
            pv = model.total_planned_value()
            ev = model.total_earned_value()
            ac = model.total_actual_cost()
            cpi = ev / ac if ac > 0 else 1.0
            spi = ev / pv if pv > 0 else 1.0

            draw(pv, ev, ac, cpi, spi)
            pygame.display.flip()
            clock.tick(30)

        pygame.quit()
        return
    if args.mode == "pygame":
        # Lightweight Pygame visualization of agents moving and forming teams
        try:
            import pygame
        except Exception:
            print("Pygame is not installed. Please: pip install pygame")
            return

        # Minimal sim state using resources count to set agent count
        try:
            n_from_xml = len(project_template.get_resources_for_simulation())
        except Exception:
            n_from_xml = 20
        num_agents = max(5, n_from_xml)

        # Build full task graph from XML with dependencies (successors/predecessors)
        try:
            tasks_from_xml = project_template.get_tasks_for_simulation()
        except Exception:
            tasks_from_xml = []
        # Task graph state: id -> {deps: [ids], progress, done, assigned_team}
        task_graph: Dict[int, Dict[str, Any]] = {}
        for t in tasks_from_xml:
            dep_ids = [d.id for d in getattr(t, "dependencies", [])] if hasattr(t, "dependencies") else []
            task_graph[t.id] = {"deps": dep_ids, "progress": 0.0, "done": False, "assigned_team": None}
        # If no tasks, synthesize some
        if not task_graph:
            for fake_id in range(1, 11):
                task_graph[fake_id] = {"deps": [], "progress": 0.0, "done": False, "assigned_team": None}

        # Visual settings
        width, height = 1100, 700
        bg_color = (20, 20, 30)
        idle_color = (78, 205, 196)
        team_color = (255, 107, 107)
        done_color = (60, 179, 113)
        # Tasks will be placed on the right side; remove single target zone

        pygame.init()
        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("ABP Agents - Pygame Live View (Teams & Homeworks)")
        clock = pygame.time.Clock()

        # Generate agents with random positions
        rng = random.Random(42)
        agents = []
        for i in range(num_agents):
            agents.append({
                "id": i + 1,
                "x": rng.randint(40, width - 360),
                "y": rng.randint(60, height - 60),
                "vx": rng.choice([-2, -1, 1, 2]),
                "vy": rng.choice([-2, -1, 1, 2]),
                "in_team": False,
                "team_id": None,
                "done": False,  # not used for task mode, kept for compatibility
            })

        # Paging for tasks (right panel)
        tasks_cols = 4
        tasks_rows = 6
        MAX_RENDER = tasks_cols * tasks_rows  # tasks per page
        sorted_task_ids = sorted(task_graph.keys())
        total_pages = max(1, (len(sorted_task_ids) + MAX_RENDER - 1) // MAX_RENDER)
        page_index = 0
        tasks_margin_left = width - 320
        tasks_margin_top = 60
        task_w, task_h = 72, 16
        gap_x, gap_y = 90, 52

        def get_render_ids() -> List[int]:
            start = page_index * MAX_RENDER
            end = start + MAX_RENDER
            return sorted_task_ids[start:end]

        def get_task_rects_for_page(render_ids: List[int]) -> Dict[int, pygame.Rect]:
            rects = {}
            for idx, tid in enumerate(render_ids):
                row = idx // tasks_cols
                col = idx % tasks_cols
                x = tasks_margin_left + col * gap_x
                y = tasks_margin_top + row * gap_y
                rects[tid] = pygame.Rect(x, y, task_w, task_h)
            return rects

        def form_teams():
            # Simple proximity-based team formation
            team_counter = 100
            for a in agents:
                if a["in_team"]:
                    continue
                near = [b for b in agents if not b["in_team"] and (a["x"]-b["x"])**2 + (a["y"]-b["y"])**2 <= 55**2]
                if len(near) >= 3:
                    team_counter += 1
                    for b in near:
                        b["in_team"] = True
                        b["team_id"] = team_counter

        def get_teams():
            teams = {}
            for a in agents:
                if a["in_team"] and a["team_id"] is not None:
                    teams.setdefault(a["team_id"], []).append(a)
            return teams

        def team_centroid(members):
            if not members:
                return (0, 0)
            sx = sum(m["x"] for m in members)
            sy = sum(m["y"] for m in members)
            n = len(members)
            return (sx / n, sy / n)

        def is_task_available(tid: int) -> bool:
            state = task_graph.get(tid)
            if not state or state["done"] or state["assigned_team"] is not None:
                return False
            # All predecessors must be done; if a predecessor id is not present (not rendered), treat based on full graph
            for dep_id in state["deps"]:
                dep_state = task_graph.get(dep_id)
                if dep_state and not dep_state["done"]:
                    return False
            return True

        def assign_tasks_to_teams():
            # Greedy: for each team without a current assignment, pick nearest available task
            teams = get_teams()
            for team_id, members in teams.items():
                # skip if any task already assigned to this team
                if any(state.get("assigned_team") == team_id and not state.get("done") for state in task_graph.values()):
                    continue
                cx, cy = team_centroid(members)
                best = None
                best_d2 = None
                for tid, state in task_graph.items():
                    if not is_task_available(tid):
                        continue
                    rect = current_task_rects.get(tid)
                    if rect is None:
                        # If not rendered, compute based on centroid only; deprioritize non-rendered by adding bias
                        tx, ty = (width - 200, 50)
                        bias = 1.3
                    else:
                        tx, ty = rect.center
                        bias = 1.0
                    d2 = (tx - cx)**2 + (ty - cy)**2
                    score = d2 * bias
                    if best is None or score < best_d2:
                        best = tid
                        best_d2 = score
                if best is not None:
                    task_graph[best]["assigned_team"] = team_id

        def move_agents():
            teams = get_teams()
            # Movement: in_team agents move toward their team's assigned task (if any)
            for a in agents:
                if a["in_team"] and a["team_id"] is not None:
                    # Find this team's task target if any
                    target = None
                    for tid, state in task_graph.items():
                        if state.get("assigned_team") == a["team_id"] and not state.get("done"):
                            target = tid
                            break
                    if target is not None:
                        rect = current_task_rects.get(target)
                        if rect is not None:
                            tx, ty = rect.center
                        else:
                            tx, ty = (width - 200, 50)
                        cx, cy = a["x"], a["y"]
                        if tx > cx: a["x"] += 2
                        if tx < cx: a["x"] -= 2
                        if ty > cy: a["y"] += 2
                        if ty < cy: a["y"] -= 2
                    else:
                        # idle small drift
                        a["x"] += a["vx"] * 0.3
                        a["y"] += a["vy"] * 0.3
                else:
                    # Random wander
                    a["x"] += a["vx"]
                    a["y"] += a["vy"]
                    if a["x"] < 20 or a["x"] > width - 360:
                        a["vx"] *= -1
                    if a["y"] < 20 or a["y"] > height - 20:
                        a["vy"] *= -1

            # Apply work on tasks: progress increases if team centroid near task and all predecessors done
            for tid, state in task_graph.items():
                if state["done"] or state["assigned_team"] is None:
                    continue
                if not is_task_available(tid):
                    continue
                members = get_teams().get(state["assigned_team"], [])
                if not members:
                    continue
                cx, cy = team_centroid(members)
                rect = current_task_rects.get(tid)
                if rect is not None:
                    tx, ty = rect.center
                else:
                    tx, ty = (width - 200, 50)
                d2 = (tx - cx)**2 + (ty - cy)**2
                if d2 <= (40**2):
                    # Progress rate scales with team size
                    rate = 0.004 * len(members)
                    state["progress"] = min(1.0, state["progress"] + rate)
                    if state["progress"] >= 1.0:
                        state["done"] = True

        running = True
        step_counter = 0
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        page_index = (page_index + 1) % total_pages
                    elif event.key == pygame.K_LEFT:
                        page_index = (page_index - 1 + total_pages) % total_pages

            screen.fill(bg_color)

            if step_counter % 15 == 0:
                form_teams()
                assign_tasks_to_teams()
            move_agents()

            # Compute current page rects and ids
            render_ids = get_render_ids()
            current_task_rects = get_task_rects_for_page(render_ids)

            # Draw agents
            for a in agents:
                color = done_color if a["done"] else (team_color if a["in_team"] else idle_color)
                pygame.draw.circle(screen, color, (int(a["x"]), int(a["y"])), 6)

            # Draw task panel separator
            pygame.draw.line(screen, (70, 70, 90), (width - 340, 40), (width - 340, height - 40), 2)
            # Draw tasks with progress bars, respecting dependency gating for current page
            for tid in render_ids:
                rect = current_task_rects[tid]
                state = task_graph.get(tid, {"progress": 0.0, "done": False})
                available = is_task_available(tid)
                base_color = (100, 100, 120) if not state["done"] else (80, 160, 100)
                if not available and not state["done"]:
                    base_color = (70, 70, 80)
                pygame.draw.rect(screen, base_color, rect, border_radius=4)
                # progress bar overlay
                pr = state["progress"]
                if pr > 0:
                    pr_w = int(rect.width * pr)
                    pr_rect = pygame.Rect(rect.x, rect.y, pr_w, rect.height)
                    pygame.draw.rect(screen, (60, 200, 120), pr_rect, border_radius=4)
                # outline and id
                pygame.draw.rect(screen, (180, 180, 200), rect, width=1, border_radius=4)
                font = pygame.font.SysFont("Arial", 14)
                label = font.render(f"HW {tid}", True, (220, 220, 235))
                screen.blit(label, (rect.x, rect.y - 18))

            # Draw team-to-task lines
            teams = get_teams()
            for tid, state in task_graph.items():
                if state.get("assigned_team") and not state.get("done"):
                    members = teams.get(state["assigned_team"], [])
                    if members:
                        cx, cy = team_centroid(members)
                        rect = current_task_rects.get(tid)
                        if rect is not None:
                            pygame.draw.line(screen, (120, 120, 220), (int(cx), int(cy)), rect.center, 1)

            # HUD
            font = pygame.font.SysFont("Arial", 16)
            teams_count = len(set([ag['team_id'] for ag in agents if ag['in_team']]))
            tasks_done = sum(1 for state in task_graph.values() if state['done'])
            available_count = sum(1 for tid in task_graph.keys() if is_task_available(tid))
            text = font.render(f"Agents: {num_agents}  Teams: {teams_count}  Homeworks: {len(task_graph)}  Available: {available_count}  Completed: {tasks_done}", True, (200, 200, 220))
            screen.blit(text, (12, 10))
            # Page indicator and hint
            page_text = font.render(f"Page {page_index+1}/{total_pages}  (Left/Right to change)", True, (180, 180, 200))
            screen.blit(page_text, (width - 330, 20))

            pygame.display.flip()
            clock.tick(30)
            step_counter += 1

        pygame.quit()
        return

    if args.mode == "mesa":
        # If Solara stack is available (Mesa 3.x), run that; otherwise use classic viz server
        if SOLARA_AVAILABLE:
            # Determine agent count from XML resources if available
            try:
                project_for_count = Project(project_data)
                n_from_xml = len(project_for_count.get_resources_for_simulation())
            except Exception:
                n_from_xml = None
            n = args.agents if isinstance(args.agents, int) and args.agents > 0 else (n_from_xml or 25)
            grid_w, grid_h = 20, 20
            if args.grid and "x" in args.grid:
                parts = args.grid.lower().split("x")
                try:
                    grid_w, grid_h = int(parts[0]), int(parts[1])
                except Exception:
                    pass
            # Hardcoded teams (for display/reference) similar to plot_simulation_experiment.py
            team_definitions_config = [
                { "id": 101, "name": "Analysis and Design Team", "member_resource_ids": [1, 2] },
                { "id": 102, "name": "Development and Testing Team", "member_resource_ids": [3, 4] }
            ]

            # Build the model and the SpaceRenderer
            tfm = TeamFormationModel(width=grid_w, height=grid_h, num_agents=n, team_threshold=(args.team or 3))
            renderer = SpaceRenderer(model=tfm, backend="matplotlib").render(
                agent_portrayal=lambda a: AgentPortrayalStyle(size=80, color=("#2ca02c" if getattr(a, "task_done", False) else a.color))
            )
            TeamsPlot = make_plot_component("TeamsFormed")
            AgentsPlot = make_plot_component("AgentsCreated")
            TasksPlot = make_plot_component("TasksCompleted")
            viz = SolaraViz(
                tfm,
                renderer,
                components=[TeamsPlot, AgentsPlot, TasksPlot],
                model_params={
                    "num_agents": {"type": "SliderInt", "value": n, "label": "Agents", "min": 5, "max": 200, "step": 5},
                    "width": grid_w,
                    "height": grid_h,
                    "team_threshold": (args.team or 3),
                },
                name="Team Formation & Task Simulation (Solara)",
            )
            # Attach team definitions to the page state for visibility (printed to console for now)
            print("Using hardcoded teams:")
            for t in team_definitions_config:
                print(f" - {t['id']}: {t['name']} members={t['member_resource_ids']}")
            # Print clear CLI instructions to run with Solara server (more reliable)
            print("\nTo launch Solara dashboard, run:")
            print("  solara run simulation_examples/rl_training_example.py")
            print("Then open the provided local URL.")
            return
        else:
            # Fallback to classic server
            grid_w, grid_h = 20, 20
            if args.grid and "x" in args.grid:
                parts = args.grid.lower().split("x")
                try:
                    grid_w, grid_h = int(parts[0]), int(parts[1])
                except Exception:
                    pass
            num_agents = args.agents if isinstance(args.agents, int) and args.agents > 0 else 25
            team_threshold = args.team if isinstance(args.team, int) and args.team > 0 else 3
            start_mesa_interactive(grid_w, grid_h, num_agents, team_threshold)
            return

    # Training mode
    rows: List[Dict[str, float]] = []
    for ep in range(cfg.episodes):
        epsilon = linear_decay(cfg.epsilon_start, cfg.epsilon_end, ep, cfg.epsilon_decay_episodes)

        # Create a fresh project for each episode (deep copies via API)
        episode_project = Project(project_template.get_project_data_copy()) if hasattr(project_template, "get_project_data_copy") else Project(project_data)

        # Run episode
        metrics = run_episode(episode_project, cfg)

        # Define a simple reward: CPI and SPI near 1 and completion 100
        reward = 0.0
        reward += min(1.0, metrics["completion"] / 100.0)
        reward += 1.0 - abs(1.0 - metrics["CPI"])
        reward += 1.0 - abs(1.0 - metrics["SPI"])
        reward = max(0.0, reward / 3.0)

        # Minimal model instance to access agents for efficiency updates
        params_for_update = SimulationParameters(
            error_margin=cfg.error_margin,
            reassignment_frequency=0,
            max_steps=1,
            team_definitions=[],
            assignment_strategy=cfg.assignment_strategy,
        )
        update_model = ProjectManagementModel(
            tasks=episode_project.get_tasks_for_simulation(),
            resources=episode_project.get_resources_for_simulation(),
            params=params_for_update,
        )
        apply_bandit_update(update_model, reward, epsilon, cfg)

        row = {
            "episode": ep + 1,
            "epsilon": round(epsilon, 4),
            "reward": round(reward, 4),
            **{k: (round(v, 4) if isinstance(v, (int, float)) else v) for k, v in metrics.items()},
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        rows.append(row)

        print(f"Episode {ep+1}/{cfg.episodes} | completion={metrics['completion']:.1f}% steps={metrics['steps']} CPI={metrics['CPI']:.2f} SPI={metrics['SPI']:.2f} reward={reward:.3f} epsilon={epsilon:.3f}")

    df = pd.DataFrame(rows)
    out_path = os.path.join(PROJECT_ROOT, cfg.output_dir, cfg.output_filename)
    df.to_csv(out_path, index=False)
    print(f"Training metrics saved to: {out_path}")


if __name__ == "__main__":
    main()