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
- Python 3.9–3.11 is recommended (Mesa 1.x and numpy < 2 are required by requirements.txt).
- Only the XML reader is enabled by default. Aspose reader exists but is optional and may require additional setup.

## Quick start

The repository includes a sample Microsoft Project plan at `data/Software Development Plan.xml` and a Jupyter tutorial at `examples/normal_simulations/comprehensive_tutorial.ipynb`.

### Run a minimal simulation from Python

```python
from core.simulation.runner import ExperimentConfig, SimulationRunner

config = ExperimentConfig(
    mpp_file_name="Software Development Plan.xml",    # file in ./data
    data_folder_relative_path="data",
    reader_type="xml",                                # xml reader enabled
    assignment_strategy="greedy",                     # greedy | shortest_first | parallel
    num_simulations=3,
    simulation_params={
        "error_margin": 0.15,
        "reassignment_frequency": 0,
        "max_steps": 1500,
    },
    team_definitions=[
        # Example: create a team that can work together (resource IDs must exist in the XML)
        {"id": 1, "name": "Core Team", "member_resource_ids": [1, 2, 3]}
    ],
    output_folder_relative_path="core/generated",
    output_filename_base="simulation_results_xml",
    add_timestamp_to_filename=True,
    print_last_run_summary=True,
    show_loaded_tasks=False,
    show_loaded_resources=False,
)

runner = SimulationRunner(config)
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
- reader_type: str — Currently `xml` is supported (XmlProjectReader). Unsupported types raise a ValueError.
- resources_definition: List[dict] — Optional overrides, each with `resource_id` and `cost_per_hour` to update loaded resources.
- simulation_params: dict — Keys: `error_margin` (float), `reassignment_frequency` (int), `max_steps` (int).
- team_definitions: List[dict] — Each with `id`, `name`, and `member_resource_ids` (list of resource IDs that form the team).
- assignment_strategy: str — `greedy` | `shortest_first` | `parallel` (see core/simulation/assignment.py).
- num_simulations: int — Number of repeated runs for aggregation.
- output_folder_relative_path: str — Where CSV results are written.
- output_filename_base: str — Base name for CSV.
- add_timestamp_to_filename: bool — If True, append timestamp to the CSV file name.
- print_last_run_summary: bool — If True, print the last simulation’s final metrics row.
- show_loaded_tasks/show_loaded_resources: bool — Log loaded items to the console.
- display_limit: int — Max items displayed when printing loaded tasks/resources.

Model metrics (core/simulation/model.py)
- Time — simulation step counter
- Completion — percent complete based on task durations and progress
- ActualCost — sum of worked hours × resource cost
- EarnedValue — sum of task estimated cost × progress
- CPI — EV/AC (1.0 when AC == 0)
- SPI — EV/PV (1.0 when PV == 0)
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
│   │   ├── xml_reader.py    # default reader (enabled)
│   │   └── aspose_reader.py # optional (not wired by default)
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
  - Optional Assignments to link tasks to required resources
  - PredecessorLink elements for dependencies
- Aspose reader: Present but not enabled by default in `get_reader`. If you plan to use it, additional setup may be needed and you must wire it in `core/simulation/runner.get_reader`.
- No data generated: Check that your XML has valid tasks and resources and that `assignment_strategy` matches available resource IDs.
- Cleaning outputs: Run `cleanup_generated.py` to remove files under `core/generated/`.