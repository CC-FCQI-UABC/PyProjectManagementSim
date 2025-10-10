# Complete and updated content of simulation_examples/simulation_experiment_01.py

import sys
import os
import traceback

# --- Environment Configuration ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.normpath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Import Components ---
try:
    from core.simulation.runner import ExperimentConfig, SimulationRunner
except ImportError:
    print("Fatal Error: Could not import 'ExperimentConfig' or 'SimulationRunner'.")
    traceback.print_exc()
    sys.exit(1)

# --- EXPERIMENT CONFIGURATION ---
team_definitions_config = [
    { "id": 101, "name": "Analysis and Design Team", "member_resource_ids": [1, 2] },
    { "id": 102, "name": "Development and Testing Team", "member_resource_ids": [3, 4] }
]

STRATEGY_TO_USE = "greedy"

experiment_settings = ExperimentConfig(
    mpp_file_name="Software Development Plan.xml",
    data_folder_relative_path="data",
    reader_type="xml",
    simulation_params={
        # MODIFIED: Increased error margin for more variability
        "error_margin": 0.35, # Was ~0.1, now tasks can vary up to 35%
        "reassignment_frequency": 0,
        "max_steps": 10000  # Increased limit as safety net, simulation should end naturally
    },
    team_definitions=team_definitions_config,
    assignment_strategy=STRATEGY_TO_USE,
    num_simulations=50,
    output_filename_base=f"sim_sdp_{STRATEGY_TO_USE}_strategy_chaos", # New filename
    add_timestamp_to_filename=True,
    output_folder_relative_path="core/generated",
    show_loaded_tasks=False,
    show_loaded_resources=False,
    display_limit=15,
    print_last_run_summary=True,
    resources_definition=[]
)

# --- EXECUTION ---
print("=" * 70)
print(" Executing Project Management Simulation Experiment ")
print(f" SELECTED STRATEGY: {STRATEGY_TO_USE.upper()}")
print("=" * 70)

runner = SimulationRunner(config=experiment_settings)
runner.run()

print("\n" + "=" * 70)
print(" Simulation Experiment Script Finished. ")
print(f" Check logs and CSV file in: {experiment_settings.output_folder_relative_path} ")
print("=" * 70)