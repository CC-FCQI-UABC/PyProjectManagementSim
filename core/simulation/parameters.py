# Contenido completo y actualizado de core/simulation/parameters.py

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class SimulationParameters:
    error_margin: float = 0.1
    reassignment_frequency: int = 10
    max_steps: int = 1000
    team_definitions: List[Dict] = field(default_factory=list)

    # NUEVO: Campo para almacenar el nombre de la estrategia de asignación.
    assignment_strategy: str = "greedy"