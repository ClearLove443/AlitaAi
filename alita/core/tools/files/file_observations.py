from dataclasses import dataclass
from .observation_types import ObservationType, FileEditSource, FileReadSource
from .observation import Observation
from typing import Optional

@dataclass
class FileReadObservation(Observation):
    path: str
    observation: str = ObservationType.READ
    impl_source: FileReadSource = FileReadSource.DEFAULT

    @property
    def message(self) -> str:
        return f'I read the file {self.path}.'

    def __str__(self) -> str:
        return f'[Read from {self.path} is successful.]\n{self.content}'

@dataclass
class FileWriteObservation(Observation):
    path: str
    observation: str = ObservationType.WRITE

    @property
    def message(self) -> str:
        return f'I wrote to the file {self.path}.'

    def __str__(self) -> str:
        return f'[Write to {self.path} is successful.]\n{self.content}'

@dataclass
class FileEditObservation(Observation):
    path: str = ''
    prev_exist: bool = False
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    observation: str = ObservationType.EDIT
    impl_source: FileEditSource = FileEditSource.LLM_BASED_EDIT
    diff: Optional[str] = None
    _diff_cache: Optional[str] = None

    @property
    def message(self) -> str:
        return f'I edited the file {self.path}.'

    def get_edit_groups(self, n_context_lines: int = 2) -> list:
        # Placeholder for diff logic, implement as needed
        return []
