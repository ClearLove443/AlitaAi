from dataclasses import dataclass

@dataclass
class Observation:
    content: str
    
    @property
    def message(self) -> str:
        return "Observation: " + str(self.content)
