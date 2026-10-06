<small>
<strong>PyProjectManagementSim 1.0</strong><br>
<em>Modelo computacional de gestión de proyectos en Python</em><br><br>

<strong>Autores:</strong> Manuel Castañón–Puga, Fernando Rosales Quiñones<br>
<strong>Correo:</strong> {puga, fernando.rosales59}@uabc.edu.mx<br>
<strong>Universidad Autónoma de Baja California</strong><br>
<a href="http://www.uabc.edu.mx">http://www.uabc.edu.mx</a><br>
</small>


# PyProjectManagementSim

Agent-Based Project Management Simulator: a Python framework to simulate project execution with agents (resources/teams), assignment strategies, and real-time EVM-style metrics.

## Highlights

- Agent-based execution of MS Project plans (XML)
- Built-in assignment strategies: greedy, shortest_first, parallel
- Team dynamics: morale and cohesion tracking
- Real-time metrics via Mesa DataCollector (CPI, SPI, EV/AC, completion, active agents)
- Results exported to CSV

## Installation

Recommended: use a virtual environment. On Windows PowerShell:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -U pip; pip install -r requirements.txt
```

Notes
- Python 3.12+ is required (Mesa 3.x, pinned to `mesa>=3.0,<3.5.1` in requirements.txt; Mesa 3.5 needs Python 3.12+).
- Plans are read from MS Project XML. To use a `.mpp` file, save it as XML from MS Project first.

## Quick start

The repository includes a sample Microsoft Project plan at `data/Software Development Plan.xml` and a Jupyter tutorial at `examples/normal_simulations/comprehensive_tutorial.ipynb`.

### Run a minimal simulation from Python (create it in PyProjectManagementSim\examples)

The safest pattern is to avoid passing kwargs to the constructor and assign fields after creating the config. This prevents signature collisions across environments without changing core code.

```python
import core.simulation.runner as runner_mod

# Build config without kwargs (then assign fields)
cfg = runner_mod.ExperimentConfig()

# Project input
cfg.mpp_file_name = "Software Development Plan.xml"  # lives in ./data
cfg.data_folder_relative_path = "data"
cfg.reader_type = "xml"  # XmlProjectReader

# Simulation controls
cfg.num_simulations = 3
cfg.simulation_params = {
  "error_margin": 0.15,
  "reassignment_frequency": 0,
  "max_steps": 1500,
}

# Optional: teams (resource IDs must exist in the XML)
cfg.team_definitions = [
  {"id": 1, "name": "Core Team", "member_resource_ids": [1, 2, 3]},
]

# Optional: resource cost overrides
cfg.resources_definition = [
  # {"resource_id": 1, "cost_per_hour": 120.0},
]

# Outputs
cfg.output_folder_relative_path = "core/generated"
cfg.output_filename_base = "simulation_results_xml"
cfg.add_timestamp_to_filename = True
cfg.print_last_run_summary = True

# Important: set assignment strategy post-construction to avoid constructor kwarg issues
cfg.assignment_strategy = "greedy"  # greedy | shortest_first | parallel

runner = runner_mod.SimulationRunner(cfg)
runner.run()  # CSV will be written under core/generated/
```

### Explore the tutorial notebook

Open `examples/normal_simulations/comprehensive_tutorial.ipynb` in Jupyter/VS Code and run the cells.

## What gets produced

- A CSV file per run (or aggregated across simulations) is saved under `core/generated/` with columns like:
  - Time, Completion, ActualCost, EarnedValue, CPI, SPI, ActiveAgents, AvgTeamMorale, AvgTeamCohesion, simulation_id
- A brief summary of the last simulation’s final state prints to the console when `print_last_run_summary=True`.

## Configuration reference

ExperimentConfig (core.simulation.runner)
- mpp_file_name: str — File name inside `data_folder_relative_path` (e.g., `Software Development Plan.xml`).
- data_folder_relative_path: str — Folder (relative to repo root) containing the plan.
- reader_type: str — A reader registered in `core.readers` (currently `xml`, XmlProjectReader). Unsupported types raise a ValueError.
- resources_definition: List[dict] — Optional overrides, each with `resource_id` and `cost_per_hour` to update loaded resources.
- simulation_params: dict — Keys: `error_margin` (float), `max_steps` (int), `reassignment_frequency` (int; not implemented — a non-zero value only prints a warning).
- team_definitions: List[dict] — Each with `id`, `name`, and `member_resource_ids` (list of resource IDs that form the team).
- assignment_strategy: str — `greedy` | `shortest_first` | `parallel` (see core/simulation/assignment.py).
- num_simulations: int — Number of repeated runs for aggregation.
- output_folder_relative_path: str — Where CSV results are written.
- output_filename_base: str — Base name for CSV.
- add_timestamp_to_filename: bool — If True, append timestamp to the CSV file name.
- print_last_run_summary: bool — If True, print the last simulation’s final metrics row.
- seed: Optional[int] — Base random seed. Simulation i uses `seed + i - 1`, so the whole experiment is reproducible. `None` (default) gives different results each time.
- show_loaded_tasks/show_loaded_resources: bool — Log loaded items to the console.
- display_limit: int — Max items displayed when printing loaded tasks/resources.

Model metrics (core/simulation/model.py)
- Time — simulation step counter
- Completion — percent of total planned work (effort hours) completed
- ActualCost — sum of worked hours × resource cost (one simulation step = one hour of effort)
- EarnedValue — sum of task estimated cost × progress
- CPI — EV/AC (1.0 when AC == 0)
- SPI — EV/PV (1.0 when PV == 0); PV follows an early-start schedule built from task work and dependencies
- ActiveAgents — agents currently working
- AvgTeamMorale, AvgTeamCohesion — simple team dynamics indicators

## Project structure

```
PyProjectManagementSim/
├── cleanup_generated.py
├── requirements.txt
├── core/
│   ├── agents.py
│   ├── entities.py
│   ├── entities_extended.py
│   ├── exceptions.py
│   ├── interfaces.py
│   ├── project.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── logging_config.py
│   ├── generated/           # CSV outputs written here
│   ├── readers/
│   │   ├── __init__.py
│   │   ├── base_reader.py
│   │   └── xml_reader.py    # MS Project XML reader
│   └── simulation/
│       ├── assignment.py    # greedy | shortest_first | parallel
│       ├── model.py
│       ├── parameters.py
│       └── runner.py
├── data/
│   ├── Software Development Plan.mpp
│   └── Software Development Plan.xml
└── examples/
    └── normal_simulations/
        └── comprehensive_tutorial.ipynb
```

## Tips and troubleshooting

- XML files: The default reader expects MS Project XML. Ensure your XML contains:
  - Resources of type "Work" and tasks (non-summary) with UIDs
  - Team `member_resource_ids` must be resource IDs from the XML; unknown IDs, or a resource in two teams, raise a ValueError
  - Task `Work` values: effort is driven by Work, not Duration (tasks without `Work` fall back to Duration; zero-work tasks complete automatically)
  - Optional Assignments to link tasks to required resources (if a task has several, only the resource with the most work is simulated)
  - PredecessorLink elements for dependencies (finish-to-start only; lags are ignored)
  - Invalid values (durations, costs, IDs) raise `ReaderError` naming the task
- No data generated: Check that your XML has valid tasks and resources and that `assignment_strategy` matches available resource IDs.
- Cleaning outputs: Run `cleanup_generated.py` to remove files under `core/generated/` and Python caches. It always works on the project folder and never touches `.venv` or other hidden folders.