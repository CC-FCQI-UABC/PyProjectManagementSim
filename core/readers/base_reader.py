# core/readers/base_reader.py
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