# Contenido completo y actualizado de simulation_examples/simulation_experiment_01.py

import sys
import os
import traceback

# --- Configuración del Entorno ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.normpath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Importar Componentes ---
try:
    from core.simulation.runner import ExperimentConfig, SimulationRunner
except ImportError:
    print("Error Fatal: No se pudo importar 'ExperimentConfig' o 'SimulationRunner'.")
    traceback.print_exc()
    sys.exit(1)

# --- CONFIGURACIÓN DEL EXPERIMENTO ---
team_definitions_config = [
    { "id": 101, "name": "Equipo de Análisis y Diseño", "member_resource_ids": [1, 2] },
    { "id": 102, "name": "Equipo de Desarrollo y Pruebas", "member_resource_ids": [3, 4] }
]

STRATEGY_TO_USE = "greedy"

experiment_settings = ExperimentConfig(
    mpp_file_name="Software Development Plan.xml",
    data_folder_relative_path="data",
    reader_type="xml",
    simulation_params={
        # MODIFICADO: Aumentamos el margen de error para más variabilidad
        "error_margin": 0.35, # Antes era ~0.1, ahora las tareas pueden variar hasta un 35%
        "reassignment_frequency": 0,
        "max_steps": 3000
    },
    team_definitions=team_definitions_config,
    assignment_strategy=STRATEGY_TO_USE,
    num_simulations=50,
    output_filename_base=f"sim_sdp_{STRATEGY_TO_USE}_strategy_chaos", # Nuevo nombre de archivo
    add_timestamp_to_filename=True,
    output_folder_relative_path="core/generated",
    show_loaded_tasks=False,
    show_loaded_resources=False,
    display_limit=15,
    print_last_run_summary=True,
    resources_definition=[]
)

# --- EJECUCIÓN ---
print("=" * 70)
print(" Ejecutando Experimento de Simulación de Gestión de Proyectos ")
print(f" ESTRATEGIA SELECCIONADA: {STRATEGY_TO_USE.upper()}")
print("=" * 70)

runner = SimulationRunner(config=experiment_settings)
runner.run()

print("\n" + "=" * 70)
print(" Script de Experimento Finalizado. ")
print(f" Revisa los logs y el archivo CSV en: {experiment_settings.output_folder_relative_path} ")
print("=" * 70)