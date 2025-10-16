"""
-----------------------------------------------------------------
PyProjectManagementSim 1.0
Modelo computacional de gestión de proyectos en Python.
Autores: Manuel Castañón–Puga, Fernando Rosales Quiñones
Correo electrónico: {puga, fernando.rosales59}@uabc.edu.mx
Universidad Autónoma de Baja California
http://www.uabc.edu.mx
PyProjectManagementSim/core/simulation/parameters.py
-----------------------------------------------------------------
"""

"""
Simulation parameters class.
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class SimulationParameters:
    error_margin: float = 0.1
    reassignment_frequency: int = 10
    max_steps: int = 1000
    team_definitions: List[Dict] = field(default_factory=list)

    # NEW: Field to store the assignment strategy name.
    assignment_strategy: str = "greedy"