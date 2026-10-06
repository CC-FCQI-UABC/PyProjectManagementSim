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

from abc import abstractmethod
from typing import List

from core.exceptions import ValidationError
from core.interfaces import IProjectReader
from core.project import ProjectData


class ProjectReader(IProjectReader):
    """Base class for project file readers (registered through core.readers.factory)."""

    # File extensions this reader handles, without the dot (e.g. ['xml'])
    supported_extensions: List[str] = []

    @abstractmethod
    def load(self, file_path: str) -> ProjectData:
        """
        Load project data from a file.

        Args:
            file_path: Path to the project file.

        Returns:
            ProjectData with tasks (dependencies as task IDs), resources and baseline cost.

        Raises:
            FileNotFoundError: If the file is not found.
            ReaderError: If the file cannot be read or processed.
        """

    def validate_data(self, data: ProjectData) -> bool:
        """Check that loaded data is usable; raises ValidationError otherwise."""
        if not isinstance(data, ProjectData):
            raise ValidationError(f"Expected ProjectData, received: {type(data)}", field="data")
        if not data.tasks:
            raise ValidationError("The project has no work tasks", field="tasks")
        return True

    def get_supported_extensions(self) -> List[str]:
        return list(self.supported_extensions)
