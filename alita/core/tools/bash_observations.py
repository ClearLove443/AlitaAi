
from dataclasses import dataclass
from alita.core.tools.files.observation_types import ObservationType
from alita.core.tools.files.observation import Observation



@dataclass
class BashObservation(Observation):
    command: str
    exit_code: int
    error: str

    @property
    def message(self) -> str:
        return f'I executed the command {self.command}.'

    def __str__(self) -> str:
        return f'[Executed command {self.command} is successful. The output is as follows:]\n{self.content}'
