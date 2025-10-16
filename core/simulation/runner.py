"""
-----------------------------------------------------------------
PyProjectManagementSim 1.0
Modelo computacional de gestión de proyectos en Python.
Autores: Manuel Castañón–Puga, Fernando Rosales Quiñones
Correo electrónico: {puga, fernando.rosales59}@uabc.edu.mx
Universidad Autónoma de Baja California
http://www.uabc.edu.mx
PyProjectManagementSim/core/simulation/runner.py
-----------------------------------------------------------------
"""

"""
Simulation runner class.
"""

import os
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import traceback
import jpype

from core.project import Project, ProjectData
from core.entities import Resource, Task
from core.simulation.model import ProjectManagementModel
from core.simulation.parameters import SimulationParameters
from core.readers.base_reader import ProjectReader
from core.readers.xml_reader import XmlProjectReader


# from core.readers.mpxj_reader import MpxjProjectReader
# from core.readers.aspose_reader import AsposeProjectReader


def get_reader(reader_type: str) -> ProjectReader:
    if reader_type.lower() == "xml":
        return XmlProjectReader()
    else:
        raise ValueError(f"Lector de tipo '{reader_type}' no soportado.")


@dataclass
class ExperimentConfig:
    mpp_file_name: str = "project.xml"
    data_folder_relative_path: str = "data"
    reader_type: str = "xml"
    resources_definition: List[Dict[str, Any]] = field(default_factory=list)
    simulation_params: Dict[str, Any] = field(default_factory=lambda: {
        "error_margin": 0.15, "reassignment_frequency": 0, "max_steps": 1500
    })
    team_definitions: List[Dict[str, Any]] = field(default_factory=list)
    assignment_strategy: str = "greedy"
    num_simulations: int = 5
    output_folder_relative_path: str = "core/generated"
    output_filename_base: str = "simulation_results_xml"
    add_timestamp_to_filename: bool = True
    print_last_run_summary: bool = True
    show_loaded_tasks: bool = False
    show_loaded_resources: bool = False
    display_limit: int = 20


class SimulationRunner:
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.aggregated_results = pd.DataFrame()
        self._project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))
        self.project_file_path = os.path.join(self._project_root, config.data_folder_relative_path,
                                              config.mpp_file_name)
        self.output_dir = os.path.join(self._project_root, config.output_folder_relative_path)
        os.makedirs(self.output_dir, exist_ok=True)

    def _prepare_project(self) -> Project:
        print(f"Info (Runner): Preparing project from '{self.project_file_path}'...")
        reader = get_reader(self.config.reader_type)
        project_data = reader.load(self.project_file_path)
        project = Project(project_data)
        project.override_resource_costs(self.config.resources_definition)
        if self.config.show_loaded_tasks:
            project.display_tasks(self.config.display_limit)
        if self.config.show_loaded_resources:
            project.display_resources(self.config.display_limit)
        return project

    def run(self):
        main_start_time = datetime.now()
        print(f"\n--- Starting {self.config.num_simulations} Simulations ---")

        all_run_dataframes = []  # MODIFICADO: Ahora almacenaremos DataFrames completos

        try:
            project_template = self._prepare_project()
            sim_params = SimulationParameters(
                error_margin=self.config.simulation_params.get('error_margin', 0.1),
                reassignment_frequency=self.config.simulation_params.get('reassignment_frequency', 0),
                max_steps=self.config.simulation_params.get('max_steps', 3000),
                team_definitions=self.config.team_definitions,
                assignment_strategy=self.config.assignment_strategy
            )
            print(f"Info (Runner): Simulation parameters ready: {sim_params}")

            for i in range(1, self.config.num_simulations + 1):
                print(f"--- Simulation {i}/{self.config.num_simulations} ---")
                try:
                    tasks_for_run = project_template.get_tasks_for_simulation()
                    resources_for_run = project_template.get_resources_for_simulation()

                    model = ProjectManagementModel(
                        tasks=tasks_for_run,
                        resources=resources_for_run,
                        params=sim_params
                    )
                    model.run_model()

                    # --- MODIFICACIÓN CLAVE ---
                    # 1. Obtenemos el DataFrame COMPLETO del DataCollector
                    run_df = model.datacollector.get_model_vars_dataframe()
                    # 2. Le añadimos la columna para identificar la simulación
                    run_df['simulation_id'] = i
                    # 3. Añadimos el DataFrame completo a nuestra lista
                    all_run_dataframes.append(run_df)

                    print(f"--- Simulation {i} completed in {model.schedule.time} steps. ---")

                except Exception as sim_exec_e:
                    print(f"  Error during Simulation {i}: {sim_exec_e}")
                    traceback.print_exc()

        except Exception as e:
            print(f"!!! Fatal error in Runner: {e} !!!")
            traceback.print_exc()

        if all_run_dataframes:
            # MODIFIED: Use pd.concat to join the list of DataFrames
            self.aggregated_results = pd.concat(all_run_dataframes, ignore_index=True)
            self.save_results()
            if self.config.print_last_run_summary:
                # Show summary of the last row of the last simulation
                print("\n--- Simulation Summary (Final State of Last Simulation) ---")
                print(all_run_dataframes[-1].iloc[-1].to_string())
        else:
            print("Error: No data generated in any simulation.")

        print(f"\n--- {len(all_run_dataframes)}/{self.config.num_simulations} Simulations Reported ---")
        print(f"Total Execution Time: {datetime.now() - main_start_time}")

    def save_results(self):
        filename = self.config.output_filename_base
        if self.config.add_timestamp_to_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename}_{timestamp}"

        output_path = os.path.join(self.output_dir, f"{filename}.csv")
        self.aggregated_results.to_csv(output_path, index=False, float_format='%.2f')
        print(f"Resultados guardados en: {output_path}")