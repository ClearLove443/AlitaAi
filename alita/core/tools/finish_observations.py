from dataclasses import dataclass
from alita.core.tools.files.observation_types import ObservationType
from alita.core.tools.files.observation import Observation



@dataclass
class FinishObservation(Observation):
    task_completed: str

    @property
    def message(self) -> str:
        return f'Finish the task.'

    def __str__(self) -> str:
        return f'[Finish the task: {self.task_completed}. The output is as follows:]\n{self.content}'
