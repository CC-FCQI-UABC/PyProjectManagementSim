"""
-----------------------------------------------------------------
PyProjectManagementSim 1.0
Modelo computacional de gestión de proyectos en Python.
Autores: Manuel Castañón–Puga, Fernando Rosales Quiñones
Correo electrónico: {puga, fernando.rosales59}@uabc.edu.mx
Universidad Autónoma de Baja California
http://www.uabc.edu.mx
PyProjectManagementSim/core/readers/base_reader.py
-----------------------------------------------------------------
"""

"""
Base reader class for project files.
"""

from abc import ABC, abstractmethod
# Import Project using absolute path from core
from core.project import Project

class ProjectReader(ABC):
    """Abstract interface for project file readers."""

    @abstractmethod
    def load(self, file_path: str) -> Project:
        """
        Load project data from a file.

        Args:
            file_path: Path to the project file.

        Returns:
            A Project instance populated with tasks, (optionally) resources,
            and dependencies.

        Raises:
            FileNotFoundError: If the file is not found.
            ValueError: If the file cannot be read or processed.
            Exception: Other unexpected errors.
        """
        pass