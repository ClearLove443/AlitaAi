import toml
from dataclasses import dataclass


with open('config.toml', 'r') as f:
    config = toml.load(f)

@dataclass
class LLMConfig:
    model: str
    api_key: str
    base_url: str


llm_config = LLMConfig(
    model=config['llm']['model'],
    api_key=config['llm']['api_key'],
    base_url=config['llm']['base_url'],
)

